"""Test session execution application"""

from __future__ import annotations

import asyncio
import base64
import plistlib
from pathlib import Path
from types import MappingProxyType

import structlog.contextvars

from noqa_runner.application.services.mobile_service import MobileService
from noqa_runner.config import settings
from noqa_runner.domain.exceptions import AgentAPIError, AppiumError, BuildNotFoundError
from noqa_runner.domain.models.test_info import RunnerTestInfo
from noqa_runner.infrastructure.adapters.http.agent_api import AgentApiAdapter
from noqa_runner.infrastructure.adapters.mobile.appium_adapter import AppiumClient
from shared.infrastructure.adapters.http.generic import generic_adapter
from shared.infrastructure.adapters.storage.local_storage_adapter import (
    LocalStorageAdapter,
)
from shared.logging_config import get_logger
from shared.models.actions.stop import Stop
from shared.models.state.screen import Screen
from shared.models.state.step import Step
from shared.models.state.test_state import TestState, TestStatus
from shared.utils.graceful_shutdown import register_task

logger = get_logger(__name__)


# Default Appium capabilities (immutable)
DEFAULT_APPIUM_CAPABILITIES = MappingProxyType(
    {
        "platformName": "iOS",
        "appium:automationName": "XCUITest",
        "appium:disableWindowAnimation": True,
        "appium:waitForQuiescence": True,
        "appium:waitForIdleTimeout": 2,
    }
)

MAX_STEPS = 50


class RunnerSession:
    """Application for running test sessions"""

    async def execute(
        self,
        device_id: str,
        build_path: str,
        noqa_api_token: str,
        tests: list[RunnerTestInfo],
        appium_url: str | None = None,
        agent_api_url: str | None = None,
        app_context: str | None = None,
        apple_developer_team_id: str | None = None,
    ) -> list[TestState]:
        """
        Run multiple tests in a session with shared mobile service

        Args:
            device_id: Device UDID
            appium_url: Appium server URL
            build_path: Path to IPA build
            noqa_api_token: API token for authentication
            tests: List of test cases to execute
            agent_api_url: Agent API base URL
            app_context: Optional application context

        Returns:
            List of final test states
        """
        appium_caps = dict(DEFAULT_APPIUM_CAPABILITIES)

        if not agent_api_url:
            agent_api_url = settings.AGENT_API_URL
        if not appium_url:
            appium_url = settings.DEFAULT_APPIUM_URL
        if apple_developer_team_id:
            appium_caps["appium:xcodeOrgId"] = apple_developer_team_id
            appium_caps["appium:xcodeSigningId"] = "iPhone Developer"

        logger.info("Starting test session", test_count=len(tests), device_id=device_id)

        # Session-level validation: extract bundle_id from build
        try:
            bundle_id = await self._extract_bundle_id_from_build(build_path=build_path)
        except BuildNotFoundError:
            logger.error(
                "Build file not found, cannot start session", build_path=build_path
            )
            raise  # Critical error - stop session immediately

        appium_caps["appium:app"] = build_path
        appium_caps["appium:udid"] = device_id

        results = []

        # Execute tests sequentially, creating new Appium client for each test
        for test_info in tests:
            # Create test state
            state = TestState(
                test_id=test_info.test_id,
                bundle_id=bundle_id,
                case_name=test_info.case_name,
                case_instructions=test_info.case_instructions,
                app_context=app_context,
            )

            # Setup logging context for this test
            structlog.contextvars.bind_contextvars(test_id=str(state.test_id))

            # Use Appium client as async context manager for each test
            try:
                async with AppiumClient(
                    appium_url=appium_url, appium_capabilities=appium_caps
                ) as appium_client:
                    # Create mobile service for this test
                    mobile_service = MobileService(appium_client)

                    # Run test as a task and register it for cancellation
                    task = asyncio.create_task(
                        self._run_single_test(
                            mobile_service=mobile_service,
                            state=state,
                            noqa_api_token=noqa_api_token,
                            agent_api_url=agent_api_url,
                        )
                    )
                    register_task(task)
                    await task
                    results.append(state)
            except asyncio.CancelledError:
                # Shutdown signal - stop session
                self._finalize_test_state(
                    state=state,
                    status=TestStatus.STOPPED,
                    message="Test stopped by shutdown signal",
                )
                results.append(state)
                break
            except (AppiumError, AgentAPIError) as e:
                message = f"Test session execution failed: {str(e)}"
                logger.error(
                    "Test session execution failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                self._finalize_test_state(
                    state=state, status=TestStatus.ERROR, message=message
                )
                results.append(state)
                break
            except Exception as e:
                logger.error(
                    "Test execution failed, continuing with next test",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                self._finalize_test_state(
                    state=state,
                    status=TestStatus.ERROR,
                    message=f"Test execution failed: {str(e)}",
                )
                results.append(state)

            structlog.contextvars.unbind_contextvars("step_number", "test_id")

        return results

    async def _run_single_test(
        self,
        mobile_service: MobileService,
        state: TestState,
        noqa_api_token: str,
        agent_api_url: str,
    ) -> None:
        """Execute single test and mutate state in place"""
        # Use agent API adapter as async context manager
        async with AgentApiAdapter(
            base_url=agent_api_url, api_token=noqa_api_token
        ) as agent_api:
            # Prepare test with agent API (create conditions, fetch app metadata)
            prepared_state = await agent_api.prepare_test(state)
            state.conditions = prepared_state.conditions
            state.action_system_prompt = prepared_state.action_system_prompt
            state.resolution = mobile_service.resolution

            # Log received conditions
            logger.info(
                "Check list", conditions=[x.model_dump() for x in state.conditions]
            )

            # Main test execution loop
            step_count = 0
            while step_count < MAX_STEPS:
                step_count += 1
                step_number = max(state.steps.keys(), default=0) + 1
                # Bind step_number to logging context
                structlog.contextvars.bind_contextvars(step_number=step_number)
                logger.info("Step")

                # Capture screen from device
                xml_source, screenshot_base64 = (
                    await mobile_service.get_appium_screen_data()
                )

                # Upload screenshot and get URLs
                screenshot_url = await self._upload_screenshot(
                    agent_api=agent_api,
                    screenshot_base64=screenshot_base64,
                    test_id=str(state.test_id),
                    step_number=step_number,
                )

                # Create step with screen data
                state.steps[step_number] = Step(
                    number=step_number,
                    screen=Screen(
                        elements_tree=xml_source, screenshot_url=screenshot_url
                    ),
                )
                logger.info("Captured screen")

                # Send to agent API for decision
                step_state = await agent_api.execute_step(state)
                state.steps = step_state.steps
                state.status = step_state.status
                state.result_summary = step_state.result_summary
                state.conditions = step_state.conditions

                logger.info(
                    state.current_step.action_data.action.get_action_description()
                )

                # Check if test is complete
                if isinstance(state.current_step.action_data.action, Stop):
                    logger.info("Agent requested to stop the test")
                    break
                else:
                    # Execute action on device
                    await mobile_service.execute_action(
                        action=state.current_step.action_data.action,
                        screen=state.current_step.screen,
                    )

                structlog.contextvars.unbind_contextvars("step_number")

            # Test completed successfully - finalize state
            self._finalize_test_state(
                state=state,
                status=state.status,
                message=state.result_summary or "Test completed",
            )

    async def _extract_bundle_id_from_build(self, build_path: str) -> str:
        """
        Extract bundle_id from iOS build archive

        Args:
            build_path: Path to the local IPA build file

        Returns:
            Bundle ID (e.g., "com.example.app")

        Raises:
            BuildNotFoundError: If build file not found
            ValueError: If bundle ID cannot be extracted
        """
        # Check if build file exists
        if not Path(build_path).exists():
            raise BuildNotFoundError(build_path)

        # Extract Info.plist from the IPA archive using LocalStorageAdapter
        # Create adapter with the build file's directory as base_dir to allow access
        build_dir = str(Path(build_path).parent)
        file_storage = LocalStorageAdapter(output_dir=build_dir)
        plist_content = await file_storage.extract_file_from_zip(
            zip_path=build_path, filename=".app/Info.plist"
        )

        if not plist_content:
            raise ValueError(f"Info.plist not found in build {build_path}")

        # Parse plist to get bundle_id
        plist_data = plistlib.loads(plist_content)
        bundle_id = plist_data.get("CFBundleIdentifier")

        if not bundle_id:
            raise ValueError(
                f"CFBundleIdentifier not found in Info.plist for build {build_path}"
            )

        return bundle_id

    def _finalize_test_state(
        self, state: TestState, status: TestStatus, message: str
    ) -> None:
        """Update test state with final status and message"""
        structlog.contextvars.unbind_contextvars("step_number")
        state.status = status
        state.result_summary = message
        logger.info("test_result", status=status, test_state=state.export_dict())
        structlog.contextvars.unbind_contextvars("test_id")

    async def _upload_screenshot(
        self,
        agent_api: AgentApiAdapter,
        screenshot_base64: str,
        test_id: str,
        step_number: int,
    ) -> str:
        """Upload screenshot to storage and return download URL"""
        upload_url, download_url = await agent_api.get_screenshot_urls(
            test_id=test_id, step_number=step_number
        )

        # Upload screenshot using generic HTTP adapter singleton
        image_data = base64.b64decode(screenshot_base64)
        await generic_adapter.upload_bytes(
            url=upload_url, data=image_data, content_type="image/png"
        )

        # Return public URL
        return download_url

    async def run_async(
        self,
        device_id: str,
        build_path: str,
        noqa_api_token: str,
        tests: list[RunnerTestInfo],
        agent_api_url: str | None = None,
        appium_url: str | None = None,
        app_context: str | None = None,
        apple_developer_team_id: str | None = None,
    ) -> list[TestState]:
        """
        Async method to run test session.
        This is an alias for execute() method for better API clarity.
        """
        return await self.execute(
            device_id=device_id,
            appium_url=appium_url,
            build_path=build_path,
            noqa_api_token=noqa_api_token,
            tests=tests,
            agent_api_url=agent_api_url,
            app_context=app_context,
            apple_developer_team_id=apple_developer_team_id,
        )

    def run(
        self,
        device_id: str,
        build_path: str,
        noqa_api_token: str,
        tests: list[RunnerTestInfo],
        agent_api_url: str | None = None,
        appium_url: str | None = None,
        app_context: str | None = None,
        apple_developer_team_id: str | None = None,
    ) -> list[TestState]:
        """
        Synchronous method to run test session.

        Runs the async execute() method in a new event loop.
        This is the main API for synchronous code.

        Args:
            device_id: Device UDID
            appium_url: Appium server URL
            build_path: Path to IPA build
            noqa_api_token: API token for authentication
            tests: List of test cases to execute
            agent_api_url: Agent API base URL
            app_context: Optional application context

        Returns:
            List of final test states
        """
        return asyncio.run(
            self.execute(
                device_id=device_id,
                appium_url=appium_url,
                build_path=build_path,
                noqa_api_token=noqa_api_token,
                tests=tests,
                agent_api_url=agent_api_url,
                app_context=app_context,
                apple_developer_team_id=apple_developer_team_id,
            )
        )
