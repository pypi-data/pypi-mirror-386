import base64
import io
import os
import random
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import cast

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rich.console import Console

from arcade_cli.secret import load_env_file
from arcade_cli.utils import compute_base_url, validate_and_get_config

console = Console()

# Models


class MCPClientInfo(BaseModel):
    """MCP client information for initialize request."""

    name: str
    version: str


class MCPInitializeParams(BaseModel):
    """Parameters for MCP initialize request."""

    capabilities: dict = Field(default_factory=dict)
    clientInfo: MCPClientInfo
    protocolVersion: str


class MCPInitializeRequest(BaseModel):
    """MCP initialize request payload."""

    id: int
    jsonrpc: str = "2.0"
    method: str = "initialize"
    params: MCPInitializeParams


class ToolkitBundle(BaseModel):
    """A toolkit bundle for deployment."""

    name: str
    version: str
    bytes: str
    type: str = "mcp"
    entrypoint: str


class DeploymentToolkits(BaseModel):
    """Toolkits section of deployment request."""

    bundles: list[ToolkitBundle]
    packages: list[str] = Field(default_factory=list)


class DeploymentRequest(BaseModel):
    """Deployment request payload for /v1/deployments endpoint."""

    name: str
    description: str
    toolkits: DeploymentToolkits


# Functions


def create_package_archive(package_dir: Path) -> str:
    """
    Create a tar.gz archive of the package directory.

    Args:
        package_dir: Path to the package directory to archive

    Returns:
        Base64-encoded string of the tar.gz archive bytes

    Raises:
        ValueError: If package_dir doesn't exist or is not a directory
    """
    if not package_dir.exists():
        raise ValueError(f"Package directory not found: {package_dir}")

    if not package_dir.is_dir():
        raise ValueError(f"Package path must be a directory: {package_dir}")

    def exclude_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
        """Filter for files/directories to exclude from the archive.

        Filters out:
        - Hidden files and directories
        - __pycache__ directories
        - .egg-info directories
        - dist and build directories
        - files ending with .lock
        """
        name = tarinfo.name

        parts = Path(name).parts
        if any(part.startswith(".") for part in parts):
            return None

        if "__pycache__" in parts:
            return None

        if any(part.endswith(".egg-info") for part in parts):
            return None

        if "dist" in parts or "build" in parts:
            return None

        if name.endswith(".lock"):
            return None

        return tarinfo

    # Create tar.gz archive in memory
    byte_stream = io.BytesIO()
    with tarfile.open(fileobj=byte_stream, mode="w:gz") as tar:
        tar.add(package_dir, arcname=package_dir.name, filter=exclude_filter)

    # Get bytes and encode to base64
    byte_stream.seek(0)
    package_bytes = byte_stream.read()
    package_bytes_b64 = base64.b64encode(package_bytes).decode("utf-8")

    return package_bytes_b64


def start_server_process(entrypoint: str, debug: bool = False) -> tuple[subprocess.Popen, int]:
    """
    Start the MCP server process on a random port.

    Args:
        entrypoint: Path to the entrypoint file that runs the MCPApp instance
        debug: Whether to show debug information

    Returns:
        Tuple of (process, port)

    Raises:
        ValueError: If the server process exits immediately
    """
    port = random.randint(8000, 9000)  # noqa: S311

    # override app.run() settings
    env = {
        **os.environ,
        "ARCADE_SERVER_HOST": "localhost",
        "ARCADE_SERVER_PORT": str(port),
        "ARCADE_SERVER_TRANSPORT": "http",
        "ARCADE_AUTH_DISABLED": "true",
    }

    cmd = [sys.executable, entrypoint]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    # Check for immediate failure on start up
    time.sleep(0.5)
    if process.poll() is not None:
        _, stderr = process.communicate()
        error_msg = stderr.strip() if stderr else "Unknown error"
        raise ValueError(f"Server process exited immediately: {error_msg}")

    return process, port


def wait_for_health(base_url: str, process: subprocess.Popen, timeout: int = 30) -> None:
    """
    Wait for the server to become healthy.

    Args:
        base_url: Base URL of the server
        process: The server process
        timeout: Maximum time to wait in seconds

    Raises:
        ValueError: If the server doesn't become healthy within timeout
    """
    health_url = f"{base_url}/worker/health"
    start_time = time.time()
    is_healthy = False

    while time.time() - start_time < timeout:
        try:
            response = httpx.get(health_url, timeout=2.0)
            if response.status_code == 200:
                is_healthy = True
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        except Exception:
            console.print("  Health check failed. Trying again...", style="dim")
        time.sleep(0.5)

    if not is_healthy:
        process.terminate()
        try:
            _, stderr = process.communicate(timeout=2)
            error_msg = stderr.strip() if stderr else "Server failed to become healthy"
        except subprocess.TimeoutExpired:
            process.kill()
            error_msg = f"Server failed to become healthy within {timeout} seconds"
        raise ValueError(error_msg)

    console.print("✓ Server is healthy", style="green")


def get_server_info(base_url: str) -> tuple[str, str]:
    """
    Extract server name and version via the MCP initialize endpoint.

    Args:
        base_url: Base URL of the server

    Returns:
        Tuple of (server_name, server_version)

    Raises:
        ValueError: If server info extraction fails
    """
    mcp_url = f"{base_url}/mcp"

    initialize_request = MCPInitializeRequest(
        id=1,
        params=MCPInitializeParams(
            clientInfo=MCPClientInfo(name="arcade-deploy-client", version="1.0.0"),
            protocolVersion="2025-06-18",
        ),
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        mcp_response = httpx.post(
            mcp_url, json=initialize_request.model_dump(), headers=headers, timeout=10.0
        )
        mcp_response.raise_for_status()
        mcp_data = mcp_response.json()

        server_name = mcp_data["result"]["serverInfo"]["name"]
        server_version = mcp_data["result"]["serverInfo"]["version"]

        console.print(f"✓ Found server name: {server_name}", style="green")
        console.print(f"✓ Found server version: {server_version}", style="green")

    except Exception as e:
        raise ValueError(f"Failed to extract server info from /mcp endpoint: {e}") from e
    else:
        return server_name, server_version


def get_required_secrets(
    base_url: str, server_name: str, server_version: str, debug: bool = False
) -> set[str]:
    """
    Extract required secrets from the /worker/tools endpoint.

    Args:
        base_url: Base URL of the server
        server_name: Name of the server (for display purposes)
        server_version: Version of the server (for display purposes)
        debug: Whether to show debug information

    Returns:
        Set of required secret keys

    Raises:
        ValueError: If secrets extraction fails
    """
    tools_url = f"{base_url}/worker/tools"

    try:
        tools_response = httpx.get(tools_url, timeout=10.0)
        tools_response.raise_for_status()
        tools_data = tools_response.json()

        required_secrets = set()
        for tool in tools_data:
            if (
                "requirements" in tool
                and tool["requirements"]
                and "secrets" in tool["requirements"]
                and tool["requirements"]["secrets"]
            ):
                for secret in tool["requirements"]["secrets"]:
                    if secret.get("key"):
                        required_secrets.add(secret["key"])

        console.print(f"✓ Found {len(tools_data)} tools", style="green")

    except Exception as e:
        raise ValueError(f"Failed to extract tool secrets from /worker/tools endpoint: {e}") from e
    else:
        return required_secrets


def verify_server_and_get_metadata(
    entrypoint: str, debug: bool = False
) -> tuple[str, str, set[str]]:
    """
    Start the server, verify it's healthy, and extract metadata.

    This function orchestrates:
    1. Starting the server on a random port
    2. Waiting for the server to become healthy
    3. Extracting server name and version via POST /mcp (initialize method)
    4. Extracting required secrets via GET /worker/tools
    5. Stopping the server
    6. Returning the metadata

    Args:
        entrypoint: Path to the entrypoint file that runs the MCPApp instance
        debug: Whether to show debug information

    Returns:
        Tuple of (server_name, server_version, required_secrets_set)

    Raises:
        ValueError: If the server fails to start or metadata extraction fails
    """
    process, port = start_server_process(entrypoint, debug)
    console.print(f"✓ Server started on port {port}", style="green")
    base_url = f"http://127.0.0.1:{port}"

    try:
        wait_for_health(base_url, process)

        server_name, server_version = get_server_info(base_url)

        required_secrets = get_required_secrets(base_url, server_name, server_version, debug)
        console.print(f"✓ Found {len(required_secrets)} required secret(s)", style="green")

        return server_name, server_version, required_secrets

    finally:
        # Always stop the server
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        if debug:
            console.print("✓ Server stopped", style="green")


def upsert_secrets_to_engine(
    engine_url: str, api_key: str, secrets: set[str], debug: bool = False
) -> None:
    """
    Upsert secrets to the Arcade Engine.

    Args:
        engine_url: The base URL of the Arcade Engine
        api_key: The API key for authentication
        secrets: Set of secret keys to upsert
        debug: Whether to show debug information
    """
    if not secrets:
        return

    client = httpx.Client(base_url=engine_url, headers={"Authorization": f"Bearer {api_key}"})

    for secret_key in sorted(secrets):
        secret_value = os.getenv(secret_key)

        if secret_value:
            console.print(
                f"✓ Uploading '{secret_key}' with value ending in ...{secret_value[-4:]}",
                style="green",
            )
        else:
            console.print(
                f"⚠️  Secret '{secret_key}' not found in environment, skipping upload.",
                style="yellow",
            )
            continue

        try:
            # Upsert secret to engine
            response = client.put(
                f"/v1/admin/secrets/{secret_key}",
                json={"description": "Secret set via CLI", "value": secret_value},
                timeout=30,
            )
            response.raise_for_status()
            console.print(f"✓ Secret '{secret_key}' uploaded", style="green")
        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to upload secret '{secret_key}': HTTP {e.response.status_code}"
            if debug:
                console.print(f"❌ {error_msg}: {e.response.text}", style="red")
            else:
                console.print(f"❌ {error_msg}", style="red")
        except Exception as e:
            error_msg = f"Failed to upload secret '{secret_key}': {e}"
            console.print(f"❌ {error_msg}", style="red")

    client.close()


def deploy_server_to_engine(
    engine_url: str, api_key: str, deployment_request: dict, debug: bool = False
) -> dict:
    """
    Deploy the server to Arcade Engine.

    Args:
        engine_url: The base URL of the Arcade Engine
        api_key: The API key for authentication
        deployment_request: The deployment request payload
        debug: Whether to show debug information

    Returns:
        The response JSON from the deployment API

    Raises:
        httpx.HTTPStatusError: If the deployment request fails
        httpx.ConnectError: If connection to the engine fails
    """
    client = httpx.Client(
        base_url=engine_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=360,
    )

    try:
        response = client.post("/v1/deployments", json=deployment_request)
        response.raise_for_status()
        return cast(dict, response.json())
    except httpx.ConnectError as e:
        raise ValueError(f"Failed to connect to Arcade Engine at {engine_url}: {e}") from e
    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_json = e.response.json()
            error_detail = f": {error_json}"
        except Exception:
            error_detail = f": {e.response.text}"

        raise ValueError(
            f"Deployment failed with HTTP {e.response.status_code}{error_detail}"
        ) from e
    finally:
        client.close()


def deploy_server_logic(
    entrypoint: str,
    skip_validate: bool,
    server_name: str | None,
    server_version: str | None,
    secrets: str,
    host: str,
    port: int | None,
    force_tls: bool,
    force_no_tls: bool,
    debug: bool,
) -> None:
    """
    Main logic for deploying an MCP server to Arcade Engine.

    Args:
        entrypoint: Path (relative to project root) to the entrypoint file that runs the MCPApp instance.
                    This file must execute the `run()` method on your `MCPApp` instance when invoked directly.
        skip_validate: Skip running the server locally for health/metadata checks.
        server_name: Explicit server name to use when --skip-validate is set.
        server_version: Explicit server version to use when --skip-validate is set.
        secrets: How to upsert secrets before deploy.
        host: Arcade Engine host
        port: Arcade Engine port (optional)
        force_tls: Force TLS connection
        force_no_tls: Disable TLS connection
        debug: Show debug information
    """
    # Step 1: Validate user is logged in
    console.print("\nValidating user is logged in...", style="dim")
    config = validate_and_get_config()
    engine_url = compute_base_url(force_tls, force_no_tls, host, port)
    console.print(f"✓ {config.user.email} is logged in", style="green")

    # Step 2: Validate pyproject.toml exists in current directory
    console.print("\nValidating pyproject.toml exists in current directory...", style="dim")
    current_dir = Path.cwd()
    pyproject_path = current_dir / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {pyproject_path}\n"
            "Please run this command from the root of your MCP server package."
        )
    console.print(f"✓ pyproject.toml found at {pyproject_path}", style="green")

    # Step 3: Load .env file from current directory if it exists
    console.print("\nLoading .env file from current directory if it exists...", style="dim")
    env_path = current_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
        console.print(f"✓ Loaded environment from {env_path}", style="green")
    else:
        console.print(f"⚠️  No .env file found at {env_path}", style="yellow")

    # Step 4: Verify server and extract metadata (or skip if --skip-validate)
    required_secrets_from_validation: set[str] = set()

    if skip_validate:
        console.print("\n⚠️  Skipping server validation (--skip-validate set)", style="yellow")
        # Use the provided server_name and server_version
        # These are guaranteed to be set due to validation in main.py
        if server_name is None:
            raise ValueError("server_name must be provided when skip_validate is True")
        if server_version is None:
            raise ValueError("server_version must be provided when skip_validate is True")
        console.print(f"✓ Using server name: {server_name}", style="green")
        console.print(f"✓ Using server version: {server_version}", style="green")
    else:
        console.print(
            "\nValidating server is healthy and extracting metadata before deploying...",
            style="dim",
        )
        try:
            server_name, server_version, required_secrets_from_validation = (
                verify_server_and_get_metadata(entrypoint, debug=debug)
            )
        except Exception as e:
            raise ValueError(
                f"Server verification failed: {e}\n"
                "Please ensure your server starts correctly before deploying."
            ) from e

    # Step 5: Determine which secrets to upsert based on --secrets flag
    secrets_to_upsert: set[str] = set()

    if secrets == "skip":
        console.print("\n⚠️  Skipping secret upload (--secrets skip)", style="yellow")
    elif secrets == "all":
        console.print("\nUploading ALL secrets from .env file...", style="dim")
        secrets_to_upsert = set(load_env_file(str(env_path)).keys())
        if secrets_to_upsert:
            console.print(f"✓ Found {len(secrets_to_upsert)} secret(s) in .env file", style="green")
            upsert_secrets_to_engine(engine_url, config.api.key, secrets_to_upsert, debug)
        else:
            console.print("⚠️  No secrets found in .env file", style="yellow")
    elif secrets == "auto":
        # Only upload required secrets discovered during validation
        if required_secrets_from_validation:
            console.print(
                f"\nUploading {len(required_secrets_from_validation)} required secret(s) to Arcade...",
                style="dim",
            )
            upsert_secrets_to_engine(
                engine_url, config.api.key, required_secrets_from_validation, debug
            )
        else:
            console.print("\n✓ No required secrets found", style="green")

    # Step 6: Create tar.gz archive of current directory
    console.print("\nCreating deployment package...", style="dim")
    try:
        archive_base64 = create_package_archive(current_dir)
        archive_size_kb = len(archive_base64) * 3 / 4 / 1024  # base64 is ~4/3 larger
        console.print(f"✓ Package created ({archive_size_kb:.1f} KB)", style="green")
    except Exception as e:
        raise ValueError(f"Failed to create package archive: {e}") from e

    # Step 7: Build deployment request payload
    deployment_request = DeploymentRequest(
        name=server_name,
        description="MCP Server deployed via CLI",
        toolkits=DeploymentToolkits(
            bundles=[
                ToolkitBundle(
                    name=server_name,
                    version=server_version,
                    bytes=archive_base64,
                    type="mcp",
                    entrypoint=entrypoint,
                )
            ],
        ),
    )

    # Step 8: Send deployment request to engine
    console.print("\nDeploying to Arcade Engine...", style="dim")
    try:
        response = deploy_server_to_engine(
            engine_url, config.api.key, deployment_request.model_dump(), debug
        )
    except Exception as e:
        raise ValueError(f"Deployment failed: {e}") from e

    console.print(
        f"✓ Server '{server_name}' v{server_version} deployed successfully", style="bold green"
    )

    deployment_id = response.get("id", "N/A")
    deployment_uri = response.get("http", {}).get("uri", "N/A")
    deployment_secret = response.get("http", {}).get("secret", "N/A").get("value", "N/A")

    console.print("\n[bold]Deployment Details:[/bold]")
    console.print(f"  • Server ID: [cyan]{deployment_id}[/cyan]")
    console.print(f"  • Server URI: [cyan]{deployment_uri}[/cyan]")
    console.print(f"  • Server Secret: [cyan]{deployment_secret}[/cyan]")
    console.print("\n[yellow]⚠ Note:[/yellow] Your server is now starting up...", style="bold")
    console.print(
        "\n  This process may take a few minutes. Your server will be available at the URI above once ready."
    )

    console.print(
        "\nView and manage your servers: [link]https://api.arcade.dev/dashboard/[/link]",
        style="dim",
    )
