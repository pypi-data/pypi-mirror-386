"""
Context variables for global state management.

Uses ContextVar to avoid prop drilling and maintain clean function signatures.
"""

from collections.abc import Callable, Coroutine
from enum import Enum
from pathlib import Path
from typing import Literal

from adbutils import AdbClient
from openai import BaseModel
from pydantic import ConfigDict

from minitap.mobile_use.agents.planner.types import Subgoal
from minitap.mobile_use.clients.device_hardware_client import DeviceHardwareClient
from minitap.mobile_use.clients.screen_api_client import ScreenApiClient
from minitap.mobile_use.config import AgentNode, LLMConfig


class DevicePlatform(str, Enum):
    """Mobile device platform enumeration."""

    ANDROID = "android"
    IOS = "ios"


class DeviceContext(BaseModel):
    host_platform: Literal["WINDOWS", "LINUX"]
    mobile_platform: DevicePlatform
    device_id: str
    device_width: int
    device_height: int

    def to_str(self):
        return (
            f"Host platform: {self.host_platform}\n"
            f"Mobile platform: {self.mobile_platform.value}\n"
            f"Device ID: {self.device_id}\n"
            f"Device width: {self.device_width}\n"
            f"Device height: {self.device_height}\n"
        )


class ExecutionSetup(BaseModel):
    """Execution setup for a task."""

    traces_path: Path
    trace_name: str
    enable_remote_tracing: bool


IsReplan = bool


class MobileUseContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    trace_id: str
    device: DeviceContext
    hw_bridge_client: DeviceHardwareClient
    screen_api_client: ScreenApiClient
    llm_config: LLMConfig
    adb_client: AdbClient | None = None
    execution_setup: ExecutionSetup | None = None
    on_agent_thought: Callable[[AgentNode, str], Coroutine] | None = None
    on_plan_changes: Callable[[list[Subgoal], IsReplan], Coroutine] | None = None
    minitap_api_key: str | None = None

    def get_adb_client(self) -> AdbClient:
        if self.adb_client is None:
            raise ValueError("No ADB client in context.")
        return self.adb_client  # type: ignore
