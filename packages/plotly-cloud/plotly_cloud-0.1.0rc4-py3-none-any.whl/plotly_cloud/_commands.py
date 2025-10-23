"""Command implementations for Plotly Cloud CLI."""

import asyncio
import importlib
import json
import os
import sys
import tempfile
import time
import webbrowser
from typing import Dict, List, TypedDict, cast

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from plotly_cloud._changes import collect_module_files, until_change
from plotly_cloud._cloud_env import cloud_config
from plotly_cloud._definitions import REVISION_STATUS_MAP, CommandArgument, RevisionStatusInfo
from plotly_cloud._deploy import (
    DeploymentClient,
    create_deployment_zip,
    format_app_url,
    get_config_path,
    load_deployment_config,
    save_deployment_config,
)
from plotly_cloud._oauth import OAuthClient
from plotly_cloud._parser import ParsedArguments

from .exceptions import (
    ApplicationError,
    CredentialError,
    DashAppError,
    ModuleImportError,
    TokenError,
)

console = Console()


class CommandGroup(TypedDict):
    description: str
    commands: Dict[str, "BaseCommand"]


class CommandRegistry(type):
    """Metaclass to automatically register command classes."""

    commands: Dict[str, CommandGroup] = {
        "app": {"description": "", "commands": {}},
        "user": {"description": "", "commands": {}},
    }

    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)
        if name != "BaseCommand" and "name" in attrs:
            CommandRegistry.commands[attrs["group"]]["commands"][attrs["name"]] = new_cls  # type: ignore
        return new_cls


class BaseCommand(metaclass=CommandRegistry):
    """Base class for CLI commands."""

    name: str = ""
    short_description: str = ""
    description: str = ""
    arguments: List[CommandArgument] = []
    group: str = ""

    @classmethod
    async def execute(cls, args: ParsedArguments) -> None:
        """Execute the command."""
        raise NotImplementedError


class LoginCommand(BaseCommand):
    """Handle login to Plotly Cloud using OAuth."""

    name = "login"
    group = "user"
    short_description = "🔐 Login to Plotly Cloud using OAuth"
    description = "Authenticate with Plotly Cloud to publish and manage applications."
    arguments: List[CommandArgument] = [
        {
            "name": "--browser",
            "action": "store_true",
            "help": "Open browser for authentication (default behavior)",
        },
        {
            "name": "--no-browser",
            "action": "store_true",
            "help": "Don't open browser automatically - show URL instead",
        },
    ]

    @classmethod
    async def execute(cls, args: ParsedArguments) -> None:
        """Execute login command."""

        client_id = cloud_config.get_oauth_client_id()

        oauth_client = OAuthClient(client_id)

        # Check if already authenticated
        if await oauth_client.is_authenticated():
            console.print("✓ Already logged in to Plotly Cloud!")
            return

        # Perform OAuth login
        open_browser = not args.no_browser
        await oauth_client.login(open_browser=open_browser)

        console.print("✓ Successfully logged in to Plotly Cloud!")


class LogoutCommand(BaseCommand):
    """Handle logout from Plotly Cloud."""

    name = "logout"
    group = "user"
    short_description = "Logout from Plotly Cloud"
    description = "Clear your authentication credentials and log out from Plotly Cloud."

    @classmethod
    async def execute(cls, args: ParsedArguments) -> None:
        """Execute logout command."""
        console.print("Logging out from Plotly Cloud...")

        client_id = cloud_config.get_oauth_client_id()

        oauth_client = OAuthClient(client_id)

        # Check if authenticated
        if not await oauth_client.is_authenticated():
            console.print("Not currently logged in.")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Clearing credentials...", total=None)
            await oauth_client.logout()

        console.print("✓ Successfully logged out!")


class RunCommand(BaseCommand):
    """Run a Dash application."""

    name = "run"
    group = "app"
    short_description = "🚀 Run a Dash application locally"
    description = "Start a local development server for your Dash application with debugging tools."
    arguments: List[CommandArgument] = [
        {
            "name": "app",
            "help": "The Dash application to run in 'module:variable' format (e.g., 'app:app')",
        },
        {
            "name": "--host",
            "default": "127.0.0.1",
            "help": "Host IP address to bind to",
        },
        {
            "name": "--port",
            "type": int,
            "default": 8050,
            "help": "Port number to listen on",
        },
        {
            "name": "--proxy",
            "help": "Proxy configuration for the application",
        },
        {
            "name": "--debug",
            "action": "store_true",
            "help": "Enable debug mode with detailed error messages",
        },
        {
            "name": "--dev-tools-ui",
            "action": "store_true",
            "help": "Enable development tools UI",
        },
        {
            "name": "--dev-tools-props-check",
            "action": "store_true",
            "help": "Enable component prop validation",
        },
        {
            "name": "--dev-tools-serve-dev-bundles",
            "action": "store_true",
            "help": "Enable serving development bundles",
        },
        {
            "name": "--dev-tools-hot-reload",
            "action": "store_true",
            "help": "Enable hot reloading for development",
        },
        {
            "name": "--dev-tools-hot-reload-interval",
            "type": float,
            "default": 3.0,
            "help": "Polling interval for hot reload",
        },
        {
            "name": "--dev-tools-hot-reload-watch-interval",
            "type": float,
            "default": 0.5,
            "help": "File watch polling interval",
        },
        {
            "name": "--dev-tools-hot-reload-max-retry",
            "type": int,
            "default": 8,
            "help": "Max failed hot reload requests",
        },
        {
            "name": "--dev-tools-silence-routes-logging",
            "action": "store_true",
            "help": "Silence Werkzeug route logging",
        },
        {
            "name": "--dev-tools-disable-version-check",
            "action": "store_true",
            "help": "Disable Dash version upgrade check",
        },
        {
            "name": "--dev-tools-prune-errors",
            "action": "store_true",
            "help": "Prune tracebacks to user code only",
        },
        {
            "name": "--open",
            "action": "store_true",
            "help": "Automatically open browser with server URL",
        },
    ]

    @classmethod
    async def execute(cls, args: ParsedArguments) -> None:
        """Execute run command."""
        keep_running = True

        # Add current directory to Python path for local module imports
        if "." not in sys.path:
            sys.path.insert(0, ".")

        while keep_running:
            if not args.debug:
                keep_running = False

            try:
                # Parse module and variable
                if ":" in args.app:
                    module_name, variable_name = args.app.split(":", 1)
                else:
                    module_name = args.app
                    variable_name = "app"

                # Handle directory separators - convert to dot notation for import
                original_module_name = module_name

                if module_name.endswith(".py"):
                    module_name = module_name[:-3]
                if "/" in module_name or "\\" in module_name:
                    # Convert directory separators to dots for module import
                    module_name = module_name.replace("/", ".").replace("\\", ".")

                # Import the module
                try:
                    module = importlib.import_module(module_name)
                except ImportError as e:
                    # If no path separators, just raise the original error
                    if not ("/" in original_module_name or "\\" in original_module_name):
                        raise ModuleImportError(f"Could not import module '{module_name}'", str(e)) from e

                    # Get the directory path and module name
                    if "/" in original_module_name:
                        parts = original_module_name.split("/")
                    else:
                        parts = original_module_name.split("\\")

                    # If only one part, no directory to change to
                    if len(parts) <= 1:
                        raise ModuleImportError(f"Could not import module '{original_module_name}'", str(e)) from e

                    dir_path = os.path.join(*parts[:-1])
                    just_module_name = parts[-1]

                    if just_module_name.endswith(".py"):
                        just_module_name = just_module_name[:-3]

                    # Check if the directory exists
                    if not os.path.exists(dir_path):
                        raise ModuleImportError(
                            f"Could not import module '{original_module_name}'"
                            " and directory '{dir_path}' does not exist",
                            str(e),
                        ) from e

                    console.print(f"Trying to import from directory: {dir_path}")

                    # Save current directory
                    original_cwd = os.getcwd()

                    try:
                        # Change to the target directory
                        os.chdir(dir_path)

                        # Add the new directory to Python path
                        if "." not in sys.path:
                            sys.path.insert(0, ".")

                        # Try to import just the module name
                        module = importlib.import_module(just_module_name)
                        console.print(f"✓ Successfully imported {just_module_name} from {dir_path}")

                    except ImportError:
                        # Restore original directory and re-raise original error
                        os.chdir(original_cwd)
                        raise ModuleImportError(f"Could not import module '{original_module_name}'", str(e)) from e

                # Get the app variable
                if hasattr(module, variable_name):
                    app = getattr(module, variable_name)
                else:
                    # Try to find the first Dash app in the module
                    import dash

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, dash.Dash):
                            app = attr
                            console.print(f"Using Dash app: {attr_name}")
                            break
                    else:
                        raise DashAppError(
                            f"Could not find variable '{variable_name}' or any Dash app in module '{module_name}'"  # noqa: E501
                        )

                # Prepare run arguments
                run_kwargs = {
                    "host": args.host,
                    "port": args.port,
                    "debug": args.debug,
                }

                # Add optional arguments if provided
                if args.proxy:
                    run_kwargs["proxy"] = args.proxy
                if args.dev_tools_ui:
                    run_kwargs["dev_tools_ui"] = args.dev_tools_ui
                if args.dev_tools_props_check:
                    run_kwargs["dev_tools_props_check"] = args.dev_tools_props_check
                if args.dev_tools_serve_dev_bundles:
                    run_kwargs["dev_tools_serve_dev_bundles"] = args.dev_tools_serve_dev_bundles
                if args.dev_tools_hot_reload:
                    run_kwargs["dev_tools_hot_reload"] = args.dev_tools_hot_reload
                if args.dev_tools_hot_reload_interval != 3.0:
                    run_kwargs["dev_tools_hot_reload_interval"] = args.dev_tools_hot_reload_interval
                if args.dev_tools_hot_reload_watch_interval != 0.5:
                    run_kwargs["dev_tools_hot_reload_watch_interval"] = args.dev_tools_hot_reload_watch_interval
                if args.dev_tools_hot_reload_max_retry != 8:
                    run_kwargs["dev_tools_hot_reload_max_retry"] = args.dev_tools_hot_reload_max_retry
                if args.dev_tools_silence_routes_logging:
                    run_kwargs["dev_tools_silence_routes_logging"] = args.dev_tools_silence_routes_logging
                if args.dev_tools_disable_version_check:
                    run_kwargs["dev_tools_disable_version_check"] = args.dev_tools_disable_version_check
                if args.dev_tools_prune_errors:
                    run_kwargs["dev_tools_prune_errors"] = args.dev_tools_prune_errors

                # Open browser if requested
                if args.open:
                    server_url = f"http://{args.host}:{args.port}"
                    console.print("Opening browser...")
                    webbrowser.open(server_url)

                app.run(**run_kwargs)

                # The server has been stopped normally, stop running.
                keep_running = False
            except Exception as e:
                if not keep_running or isinstance(e, KeyboardInterrupt):
                    raise ApplicationError("Error running app", str(e)) from e

                console.print_exception()
                console.print("\n\n")

                # Create a progress with spinner for waiting
                progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[cyan]Waiting for changes..."),
                    console=console,
                )
                with Live(progress, console=console, refresh_per_second=10):
                    progress.add_task("waiting", total=None)

                    # Resolve the actual file path for watching
                    module_spec = args.app.split(":")[0] if ":" in args.app else args.app
                    if not module_spec.endswith(".py"):
                        module_spec += ".py"
                    # Handle path separators
                    if "/" in module_spec or "\\" in module_spec:
                        actual_app_file = os.path.abspath(module_spec)
                    else:
                        # Current directory case
                        actual_app_file = os.path.abspath(module_spec)

                    await until_change(collect_module_files, actual_app_file)


class PublishCommand(BaseCommand):
    """Deploy application to Plotly Cloud."""

    name = "publish"
    group = "app"
    short_description = "📦 Publish application to Plotly Cloud"
    description = "Package and publish your Dash application to Plotly Cloud."
    arguments: List[CommandArgument] = [
        {
            "name": "--project-path",
            "default": ".",
            "help": "Path to project directory to publish (default: current directory)",
        },
        {
            "name": "--config",
            "default": "plotly-cloud.toml",
            "help": "Path to configuration file",
        },
        {
            "name": "--name",
            "help": "Application name (will prompt if not provided first time app is published)",
        },
        {
            "name": "--entrypoint-module",
            "help": "Entrypoint module for the application in 'module:variable' format (e.g., 'app:app')",
        },
        {
            "name": "--output",
            "help": "Output path for zip file of the published app (default: temporary file)",
        },
        {
            "name": "--keep-zip",
            "action": "store_true",
            "help": "Keep the zip file of the published app after upload",
        },
        {
            "name": "--poll-status",
            "type": lambda x: x.lower() in ("true", "1", "yes", "on"),  # type: ignore
            "default": True,
            "help": "Poll publishing status until completion (default: True)",
        },
        {
            "name": "--poll-interval",
            "type": float,
            "default": 1.0,
            "help": "Polling interval in seconds",
        },
        {
            "name": "--poll-timeout",
            "type": int,
            "default": 180,
            "help": "Polling timeout in seconds",
        },
    ]

    @classmethod
    async def _poll_deployment_status(
        cls, deploy_client: "DeploymentClient", app_id: str, poll_interval: float = 1.0, timeout_seconds: int = 180
    ) -> str:
        """Poll deployment status until completion.

        Args:
            deploy_client: The deployment client
            app_id: Application ID to poll
            poll_interval: Polling interval in seconds
            timeout_seconds: Timeout in seconds (default: 180 = 3 minutes)

        Returns:
            Final status
        """
        # Define terminal states
        error_states = {"BUILD_FAILED", "PENDING_ENTITLEMENTS", "FAILING"}
        success_states = {"RUNNING"}
        terminal_states = error_states | success_states

        # Start with STARTING status, wait 0.5 seconds before first poll
        current_status = "STARTING"
        start_time = time.time()

        with Live(cls._create_status_display(current_status), refresh_per_second=4) as live:
            await asyncio.sleep(0.5)

            while current_status not in terminal_states:
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    current_status = "TIMEOUT"
                    live.update(cls._create_status_display(current_status))
                    break

                status_data = await deploy_client.get_app_status(app_id)
                new_status = status_data.get("status", "STARTING")

                if new_status != current_status:
                    current_status = new_status
                    live.update(cls._create_status_display(current_status))

                if current_status in terminal_states:
                    break

                await asyncio.sleep(poll_interval)

        return current_status

    @classmethod
    def _create_status_display(cls, status: str) -> Panel:
        """Create a rich display for the current status.

        Args:
            status: Current deployment status

        Returns:
            Rich Panel with status information
        """
        if status == "TIMEOUT":
            status_text = Text()
            status_text.append("Timeout ", style="bold")
            status_text.append("Timeout", style="bold yellow")
            return Panel(status_text, title="🚀 Publish Status", border_style="yellow", padding=(0, 1))

        status_info = cast(
            RevisionStatusInfo, REVISION_STATUS_MAP.get(status, {"label": status, "emoji": "⏳", "color": "white"})
        )

        status_text = Text()
        status_text.append(f"{status_info['emoji']}  ", style="bold")
        status_text.append(status_info["label"], style=f"bold {status_info['color']}")

        return Panel(status_text, title="🚀 Publish Status", border_style="blue", padding=(0, 1))

    @classmethod
    async def execute(cls, args: ParsedArguments) -> None:
        """Execute deploy command."""
        # Check for user input needs before starting progress
        project_path = os.path.abspath(args.project_path)
        config_path = get_config_path(project_path, args.config)
        config = load_deployment_config(config_path)

        app_id = config.get("app_id")
        is_new_app = app_id is None
        deployment_warning = None  # Track deployment warnings

        if is_new_app:
            app_name = args.name or config.get("name")
            if not app_name:
                # Use folder name as default suggestion
                folder_name = os.path.basename(os.path.abspath(args.project_path))
                console.print("App name is required the first time you publish an app.")

                app_name = Prompt.ask("Enter app name: ", default=folder_name).strip()
                if not app_name:
                    raise ApplicationError("App name cannot be empty.")
                args.name = app_name

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Get OAuth client for authentication
            auth_task = progress.add_task("🔐 Checking authentication...", total=None)

            client_id = cloud_config.get_oauth_client_id()
            oauth_client = OAuthClient(client_id)

            # Check if authenticated, if not, perform login
            if not await oauth_client.is_authenticated():
                progress.update(auth_task, description="🔐 Authentication required - logging in...")
                await oauth_client.login(open_browser=True)
                progress.update(auth_task, description="✓ Successfully authenticated!")
            else:
                progress.update(auth_task, description="✓ Already authenticated!")

            # Get the access token
            auth_token = await oauth_client.get_access_token()
            if not auth_token:
                raise ApplicationError("Unable to retrieve access token. Please try logging in again.")

            progress.remove_task(auth_task)

            # Validate project path
            validate_task = progress.add_task("Validating project...", total=None)
            project_path = os.path.abspath(args.project_path)
            if not os.path.exists(project_path):
                raise ApplicationError(f"Project path does not exist: {project_path}")

            if not os.path.isdir(project_path):
                raise ApplicationError(f"Project path is not a directory: {project_path}")

            # Get configuration file path
            config_path = get_config_path(project_path, args.config)

            # Initialize deployment client
            async with DeploymentClient(oauth_client) as deploy_client:
                if config:
                    progress.update(validate_task, description="Loaded existing configuration")
                else:
                    progress.update(validate_task, description="No existing configuration found")

                # Determine output path for zip file
                if args.output:
                    zip_path = os.path.abspath(args.output)
                else:
                    # Create temporary file
                    temp_file = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
                    zip_path = temp_file.name
                    temp_file.close()

                progress.remove_task(validate_task)

                try:
                    # Create deployment zip
                    package_task = progress.add_task("Creating deployment package...", total=None)
                    zip_size = await create_deployment_zip(project_path, zip_path)
                    progress.update(
                        package_task, description=f"✓ Created deployment package: {zip_size / (1024 * 1024):.1f}MB"
                    )

                    # Determine if this is a new app or existing app
                    app_id = config.get("app_id")
                    is_new_app = app_id is None

                    if is_new_app:
                        # New app - name is required
                        app_name = args.name or config.get("name")
                        assert app_name

                        # Create the app with deployment
                        progress.remove_task(package_task)
                        deploy_task = progress.add_task(f"Creating new app: {app_name}...", total=None)

                        entrypoint_module = getattr(args, "entrypoint_module", None)
                        app_data = await deploy_client.create_app(app_name, zip_path, entrypoint_module)

                        progress.update(
                            deploy_task,
                            description=f"✓ Created new app: {app_name} (ID: {app_data.get('app_id')})",
                        )

                        # Update config with app metadata
                        config.update(
                            {
                                "name": str(app_name),
                                "app_id": app_data.get("id", ""),
                                "app_url": app_data.get("app_url", ""),
                            }
                        )

                        # Save updated config
                        progress.update(deploy_task, description="Saving configuration...")
                        save_deployment_config(config, config_path)
                        progress.update(deploy_task, description="✓ Configuration saved!")
                    else:
                        # Existing app - publish update with deployment
                        assert app_id is not None  # We know this is not None in else branch
                        progress.remove_task(package_task)
                        deploy_task = progress.add_task(f"Updating existing app (ID: {app_id})...", total=None)
                        entrypoint_module = getattr(args, "entrypoint_module", None)
                        app_data = await deploy_client.publish_app(app_id, zip_path, entrypoint_module)
                        progress.update(deploy_task, description=f"✓ Published app update (ID: {app_id})")

                        # Update config with any new data
                        if app_data.get("app_url"):
                            config["app_url"] = app_data.get("app_url", "")
                            progress.update(deploy_task, description="Updating configuration...")
                            save_deployment_config(config, config_path)
                            progress.update(deploy_task, description="✓ Configuration updated!")

                    # Poll for deployment status if enabled (after Progress context ends)
                    if args.poll_status:
                        progress.stop()
                        console.print()
                        final_app_id = config.get("app_id")
                        if final_app_id:
                            final_status = await cls._poll_deployment_status(
                                deploy_client, final_app_id, args.poll_interval, args.poll_timeout
                            )

                            # Set deployment warning based on final status
                            if final_status in {"BUILD_FAILED", "PENDING_ENTITLEMENTS", "FAILING", "TIMEOUT"}:
                                if final_status == "TIMEOUT":
                                    timeout_minutes = args.poll_timeout / 60
                                    deployment_warning = (
                                        f"Deployment status polling timed out after {timeout_minutes:.1f} minutes. "
                                        "Check the Plotly Cloud dashboard for current status."
                                    )
                                else:
                                    status_info = REVISION_STATUS_MAP.get(final_status, {"label": final_status})
                                    deployment_warning = (
                                        f"Publishing app failed with status: {status_info['label']}. "
                                        "Check the Plotly Cloud dashboard for further details."
                                    )

                        progress.start()

                    progress.remove_task(deploy_task)

                finally:
                    # Clean up temporary zip file unless user wants to keep it
                    if not args.keep_zip and (not args.output):
                        try:
                            os.unlink(zip_path)
                        except OSError:
                            pass
                    elif args.keep_zip or args.output:
                        cleanup_task = progress.add_task("Keeping deployment package...", total=None)
                        progress.update(cleanup_task, description=f"Deployment package saved: {zip_path}")
                        progress.remove_task(cleanup_task)

        # Show deployment warning if there was one
        if deployment_warning:
            console.print()
            console.print(
                Panel(
                    f"⚠ {deployment_warning}",
                    title="Warning",
                    border_style="magenta",
                )
            )
        else:
            console.print("🎉 Published app successfully!")

        # Show app URL if available
        app_url = config.get("app_url")
        if app_url and not deployment_warning:
            console.print(f"Your app is available at: {format_app_url(app_url)}")


class StatusCommand(BaseCommand):
    """Get the status of an app published to Plotly Cloud."""

    name = "status"
    group = "app"
    short_description = "📊 Get a published app's current status."
    description = "Retrieve the current status and details of your published app."
    arguments: List[CommandArgument] = [
        {
            "name": "--project-path",
            "default": ".",
            "help": "Path to project directory",
        },
        {
            "name": "--config",
            "default": "plotly-cloud.toml",
            "help": "Path to configuration file",
        },
    ]

    @classmethod
    async def execute(cls, args: ParsedArguments) -> None:
        """Execute status command."""
        # Load configuration
        project_path = os.path.abspath(args.project_path)
        config_path = get_config_path(project_path, args.config)
        config = load_deployment_config(config_path)

        columns_display = ["name", "app_url", "is_view_private", "status", "created_at"]

        # Check if app_id exists
        app_id = config.get("app_id")
        if not app_id:
            raise ApplicationError("No app_id found in configuration. Publish your app first using 'plotly publish'.")

        # Get OAuth client for authentication
        client_id = cloud_config.get_oauth_client_id()
        oauth_client = OAuthClient(client_id)

        # Check if authenticated
        if not await oauth_client.is_authenticated():
            raise ApplicationError("Not authenticated. Please run 'plotly login' first.")

        # Get access token
        auth_token = await oauth_client.get_access_token()
        if not auth_token:
            raise ApplicationError("Unable to retrieve access token. Please try logging in again.")

        # Get app status
        async with DeploymentClient(oauth_client) as deploy_client:
            status_data = await deploy_client.get_app_status(app_id)

        # Create a table for the status information
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Value", style="white")

        # Add rows for each key-value pair
        for key, value in status_data.items():
            if not args.verbose and key not in columns_display:
                continue

            # Format the key to be more readable
            display_key = key.replace("_", " ").title()

            # Handle different value types
            if isinstance(value, bool):
                display_value = "✓ Yes" if value else "✗ No"
            elif value is None:
                display_value = "—"
            elif isinstance(value, (list, dict)):
                display_value = json.dumps(value, indent=2)
            elif key == "app_url":
                # Format the app URL properly if it's just a subdomain
                formatted_url = format_app_url(str(value)) if value else None
                display_value = f"[underline][blue]{formatted_url or config.get('app_url', '—')}[/blue][/underline]"
            elif key == "status" and isinstance(value, str) and value in REVISION_STATUS_MAP:
                # Use revision status mapping for user-friendly display
                status_info = REVISION_STATUS_MAP[value]
                display_value = (
                    f"{status_info['emoji']}  [{status_info['color']}]{status_info['label']}[/{status_info['color']}]"
                )
            else:
                display_value = str(value)

            table.add_row(display_key, display_value)

        console.print()
        console.print(Panel.fit(table, title="📊 Application Status", border_style="bold blue"))
        console.print()


class WhoamiCommand(BaseCommand):
    """Show current user information."""

    name = "whoami"
    group = "user"
    short_description = "👤 Show current user information"
    description = "Display the username if currently logged in with a valid token."
    arguments: List[CommandArgument] = []

    @classmethod
    async def execute(cls, args: ParsedArguments) -> None:
        """Execute the whoami command."""
        client_id = cloud_config.get_oauth_client_id()
        oauth_client = OAuthClient(client_id)

        # Check if authenticated
        if not await oauth_client.is_authenticated():
            console.print("✗ Not logged in")
            return

        # Load credentials to get user info
        credentials = await oauth_client.load_credentials()
        if not credentials:
            console.print("✗ No credentials found")
            return

        # Try to refresh token to validate it
        try:
            await oauth_client.refresh_access_token()

            # Extract user information from credentials
            user_info = credentials.get("user", {})
            email = user_info.get("email") or credentials.get("email")

            if email:
                console.print(f"✓ Logged in as: [bold green]{email}[/bold green]")
            else:
                console.print("✓ Logged in (no email information available)")

        except (TokenError, CredentialError):
            # Token is invalid and cannot be refreshed, clear credentials
            await oauth_client.logout()
            console.print("✗ Invalid token - credentials cleared")
