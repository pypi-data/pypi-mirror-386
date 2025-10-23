"""API type definitions for Plotly Cloud."""

from typing import Any, Dict, List

from typing_extensions import NotRequired, TypedDict


class AppRequest(TypedDict):
    pythonVersion: NotRequired[str]
    entrypointModule: NotRequired[str]
    name: NotRequired[str]
    appUrl: NotRequired[str]
    description: NotRequired[str]
    isViewPrivate: NotRequired[str]
    invitations: NotRequired[List[str]]
    environmentVariables: NotRequired[List[Dict[str, Any]]]

EnvironmentVariables = Dict[str, Any]

class ErrorResponse(TypedDict):
    error: NotRequired[str]
    error_description: NotRequired[str]

class App(TypedDict):
    id: NotRequired[str]
    author_id: NotRequired[str]
    name: NotRequired[str]
    description: NotRequired[str]
    app_url: NotRequired[str]
    is_view_private: NotRequired[bool]
    created_with_desktop: NotRequired[bool]
    desktop_app_version: NotRequired[str]
    environment_variables: NotRequired[EnvironmentVariables]
    invitations: NotRequired[List[str]]
    status: NotRequired[str]
    created_at: NotRequired[str]
    last_published: NotRequired[str]
