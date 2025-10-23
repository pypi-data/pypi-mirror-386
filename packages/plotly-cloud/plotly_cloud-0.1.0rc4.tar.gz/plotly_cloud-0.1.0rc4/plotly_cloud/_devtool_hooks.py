import asyncio

import dash
import flask
from packaging.version import parse as _parse_version

from plotly_cloud._devtool_publish_rpc import PlotlyCloudPublishRPC

dash_version = _parse_version(dash.__version__)


def _run_sync(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


def install_hook():
    import nest_asyncio

    # Make asyncio stuff runs smoothly.
    # Prevent no loop and existing loop errors.
    nest_asyncio.apply()

    rpc = PlotlyCloudPublishRPC()

    try:
        # The style only works with the position left defined.
        dash.hooks.devtool(  # type: ignore
            "plotly_cloud_publish_component",
            "PlotlyCloudPublishComponent",
            {"id": "_plotly-cloud-publish"},
            position="left",
        )
    except Exception:
        return

    dash.hooks.script(
        [
            {"dev_package_path": "cloud_devtools.js", "namespace": "plotly_cloud", "dev_only": True},
        ]
    )

    dash.hooks.stylesheet(
        [
            {"relative_package_path": "cloud_devtools.css", "namespace": "plotly_cloud"},
        ]
    )

    @dash.hooks.route("_plotly_cloud_publish", methods=["POST"])
    def plotly_cloud_publish_rpc():
        data = flask.request.get_json()
        data = _run_sync(rpc.handle_operation(data))
        return flask.jsonify(data)

    @dash.hooks.setup()
    def plotly_cloud_setup(app):
        rpc._app_setup = app


if hasattr(dash.hooks, "devtool"):
    install_hook()
