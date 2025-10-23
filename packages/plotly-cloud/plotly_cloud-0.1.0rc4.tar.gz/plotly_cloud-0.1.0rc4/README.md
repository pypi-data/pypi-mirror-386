# Plotly Cloud CLI

A command-line interface for interacting with Plotly Cloud to publish and manage Dash applications.

## Features

- 🔐 **Authentication**: Login/logout with Plotly Cloud using OAuth
- 🚀 **Local Development**: Run Dash applications locally with comprehensive dev tools
- 📦 **Publish**: Publish Dash applications to Plotly Cloud with metadata management
- ⚙️ **Environment Configuration**: Centralized cloud configuration with staging/production support

## Installation

```bash
pip install plotly-cloud
```

## Quick Start

### 1. Login to Plotly Cloud

```bash
plotly login
```

This will open your browser for OAuth authentication.

### 2. Run a Dash Application

```bash
plotly run app:app
```

This runs your Dash app from the `app` module, using the `app` variable.

### 3. Publish to Plotly Cloud

```bash
# For new applications (first publish)
plotly publish --name "My App" --description "My application description"

# For existing applications (with default polling)
plotly publish

# Publish without polling status
plotly publish --poll-status=false
```

### 4. Logout

```bash
plotly logout
```

## Environment Configuration

The CLI uses a `cloud-env.toml` file for environment-specific configuration (OAuth client IDs, API URLs). This file is gitignored and should be created during development or at packaging time.

## Usage

### Authentication Commands

#### Login
```bash
plotly login [--browser | --no-browser]
```

Options:
- `--browser`: Open browser for authentication (default)
- `--no-browser`: Don't open browser automatically

#### Logout
```bash
plotly logout
```

#### Check Current User
```bash
plotly whoami
```

Show current user information if logged in with a valid token. If the token is invalid, it will automatically clear the credentials.

### Running Applications

#### Basic Usage
```bash
plotly run <module:variable>
```

Examples:
```bash
plotly run app:app          # Run app from app.py
plotly run myapp:dashboard  # Run dashboard from myapp.py
plotly run main             # Run from main.py (looks for first Dash app)
```

#### Advanced Options

```bash
plotly run app:app --host 0.0.0.0 --port 8080 --debug
```

**Server Options:**
- `--host`: Host IP address (default: 127.0.0.1)
- `--port, -p`: Port number (default: 8050)
- `--proxy`: Proxy configuration
- `--debug, -d`: Enable debug mode

**Development Tools:**
- `--dev-tools-ui`: Enable dev tools UI
- `--dev-tools-props-check`: Enable component prop validation
- `--dev-tools-serve-dev-bundles`: Enable serving dev bundles
- `--dev-tools-hot-reload`: Enable hot reloading
- `--dev-tools-hot-reload-interval`: Hot reload polling interval (default: 3.0s)
- `--dev-tools-hot-reload-watch-interval`: File watch interval (default: 0.5s)
- `--dev-tools-hot-reload-max-retry`: Max failed reload attempts (default: 8)
- `--dev-tools-silence-routes-logging`: Silence Werkzeug route logging
- `--dev-tools-disable-version-check`: Disable Dash version upgrade check
- `--dev-tools-prune-errors`: Prune tracebacks to user code only

### Publishing Commands

#### Publish Application
```bash
plotly publish [OPTIONS]
```

Publish your Dash application to Plotly Cloud with automatic status polling.

**Options:**
- `--project-path`: Path to project directory (default: current directory)
- `--config`: Path to configuration file (default: plotly-cloud.toml)
- `--name`: Application name (required for first publish)
- `--description`: Application description (optional)
- `--output`: Output path for publish zip file (default: temporary file)
- `--keep-zip`: Keep the publish zip file after upload
- `--poll-status`: Poll publish status until completion (default: true)
- `--poll-interval`: Polling interval in seconds (default: 1.0)
- `--poll-timeout`: Polling timeout in seconds (default: 180 = 3 minutes)

**Examples:**
```bash
# Publish with default settings (includes status polling)
plotly publish

# Publish new app with custom name and description
plotly publish --name "My Dashboard" --description "Sales analytics dashboard"

# Publish without status polling
plotly publish --poll-status=false

# Publish with custom polling settings
plotly publish --poll-interval=2.0 --poll-timeout=300

# Publish and keep the zip file
plotly publish --output=my-app.zip --keep-zip
```

#### Check Application Status
```bash
plotly status [OPTIONS]
```

Get current status and details of your published application.

**Options:**
- `--project-path`: Path to project directory (default: current directory)
- `--config`: Path to configuration file (default: plotly-cloud.toml)

**Example:**
```bash
plotly status
```

## Requirements

- Python 3.9+

### Python Dependencies

- `httpx>=0.24.0` - HTTP client for API requests
- `dash>=2.0.0` - Dash framework
- `rich>=10.0.0` - Rich terminal formatting

### Development Dependencies

- `pytest>=6.0` - Testing framework
- `ruff>=0.1.0` - Code linting and formatting
- `pyright>=1.1.0` - Type checking

## Development

### Setup

We use [`uv`](https://docs.astral.sh/uv/) to manage dependencies and [Just](https://github.com/casey/just) is used for task automation. Install them and use our Justfile for common development tasks:

1. Clone the repository
2. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` or on windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
3. Install Just: `cargo install just` or see [installation docs](https://github.com/casey/just#installation)
4. Setup the development environment:
   ```bash
   # Install dependencies
   just install
   
   # Setup cloud environment configuration
   just setup-cloud-env "your-staging-client-id" "your-production-client-id"
   
   # Install CLI in development mode
   just install-cli
   ```

### Development Commands

Run `just` or `just --list` to see all available commands:

```bash
# Testing
just test                    # Run all tests
just test-cov               # Run tests with coverage
just test-file tests/test_commands.py  # Run specific test file

# Code Quality
just lint                   # Run linting
just lint-fix              # Run linting with auto-fix
just format                 # Format code
just quality                # Run all quality checks (lint + typecheck + test)

# Cloud Configuration
just setup-cloud-env <staging_id> [production_id]  # Setup cloud config
just show-cloud-config      # Display current configuration

# Publishing
just publish [path]          # Publish to cloud (default: current directory)

# Development
just install-cli            # Install CLI in development mode
just test-cli              # Test CLI after installation
just run-example app:app    # Run example Dash app

# Maintenance
just clean                  # Clean build artifacts
just build                  # Build package
```

### Alternative Setup (without Just)

If you prefer not to use Just:

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

### Project Structure

```
plotly-cloud-cli/
├── plotly_cloud/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Main CLI entry point
│   └── _commands.py         # Command implementations
├── pyproject.toml           # Project configuration
├── uv.lock                  # Dependency lock file
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please open an issue on the GitHub repository.
