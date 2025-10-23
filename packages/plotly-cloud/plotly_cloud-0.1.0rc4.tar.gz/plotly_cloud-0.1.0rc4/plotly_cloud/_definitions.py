"""Type definitions for Plotly Cloud CLI."""

from typing import Literal, Union

from typing_extensions import NotRequired, TypedDict


class HelpPanelStyle(TypedDict):
    """Style configuration for help panels."""

    border_style: str
    argument_color: str
    description_color: str
    argument_width: int


class CommandArgument(TypedDict):
    """Definition for a command argument."""

    name: str
    help: str
    action: NotRequired[str]
    type: NotRequired[type]
    default: NotRequired[Union[str, int, float, bool]]
    choices: NotRequired[list]
    required: NotRequired[bool]
    nargs: NotRequired[str]
    metavar: NotRequired[str]


class AppDeploymentConfig(TypedDict):
    """Deployed application configuration and metadata."""

    name: NotRequired[str]
    description: NotRequired[str]
    app_id: NotRequired[str]
    app_url: NotRequired[str]


# Revision status enum values
RevisionStatus = Literal[
    "BUILDING",
    "PENDING_ENTITLEMENTS",
    "BUILD_FAILED",
    "BUILD_COMPLETED",
    "STARTING",
    "RUNNING",
    "STOPPING",
    "STOPPED",
    "FAILING",
]


class RevisionStatusInfo(TypedDict):
    """User-friendly information about revision status."""

    label: str
    emoji: str
    color: str


# User-friendly status mappings based on HTML page
REVISION_STATUS_MAP: dict[str, RevisionStatusInfo] = {
    "BUILDING": {
        "label": "Building",
        "emoji": "⚒",
        "color": "yellow",
    },
    "PENDING_ENTITLEMENTS": {
        "label": "Max Deployed Apps Reached",
        "emoji": "⏸",
        "color": "dim white",
    },
    "BUILD_FAILED": {
        "label": "Build Failed",
        "emoji": "✗",
        "color": "red",
    },
    "BUILD_COMPLETED": {
        "label": "Build Completed",
        "emoji": "✓",
        "color": "green",
    },
    "STARTING": {
        "label": "Starting",
        "emoji": "→",
        "color": "dim white",
    },
    "RUNNING": {
        "label": "Running",
        "emoji": "▶",
        "color": "green",
    },
    "STOPPING": {
        "label": "Stopping",
        "emoji": "⏹",
        "color": "yellow",
    },
    "STOPPED": {
        "label": "Stopped",
        "emoji": "⏹",
        "color": "dim white",
    },
    "FAILING": {
        "label": "Failing",
        "emoji": "⚠",
        "color": "red",
    },
}
