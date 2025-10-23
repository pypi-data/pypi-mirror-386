import re
import shutil
from datetime import datetime
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Optional

import typer
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console

from arcade_cli.templates import get_full_template_directory, get_minimal_template_directory

console = Console()

# Retrieve the installed version of arcade-mcp
try:
    ARCADE_MCP_MIN_VERSION = get_version("arcade-mcp")
    ARCADE_MCP_MAX_VERSION = str(int(ARCADE_MCP_MIN_VERSION.split(".")[0]) + 1) + ".0.0"
except Exception as e:
    console.print(f"[red]Failed to get arcade-mcp version: {e}[/red]")
    ARCADE_MCP_MIN_VERSION = "1.3.0"  # Default version if unable to fetch
    ARCADE_MCP_MAX_VERSION = "2.0.0"

ARCADE_TDK_MIN_VERSION = "3.0.0"
ARCADE_TDK_MAX_VERSION = "4.0.0"
ARCADE_SERVE_MIN_VERSION = "3.0.0"
ARCADE_SERVE_MAX_VERSION = "4.0.0"
ARCADE_MCP_SERVER_MIN_VERSION = "1.4.0"
ARCADE_MCP_SERVER_MAX_VERSION = "2.0.0"


def ask_question(question: str, default: Optional[str] = None) -> str:
    """
    Ask a question via input() and return the answer.
    """
    answer = typer.prompt(question, default=default, show_default=False)
    if not answer and default:
        return default
    return str(answer)


def ask_yes_no_question(question: str, default: bool = True) -> bool:
    """
    Ask a yes/no question via input() and return the bool answer.
    """
    default_str = "Y/n" if default else "y/N"
    answer = typer.prompt(
        f"{question} ({default_str})", default="y" if default else "n", show_default=False
    )
    return answer.lower() in [
        "y",
        "y/",
        "yes",
        "true",
        "1",
        "ye",
        "yes",
        "yeah",
        "yep",
        "sure",
        "ok",
        "yup",
    ]


def render_template(env: Environment, template_string: str, context: dict) -> str:
    """Render a template string with the given variables."""
    template = env.from_string(template_string)
    return template.render(context)


def write_template(path: Path, content: str) -> None:
    """Write content to a file."""
    path.write_text(content, encoding="utf-8")


def create_ignore_pattern(
    include_evals: bool, is_community_or_official_toolkit: bool
) -> re.Pattern[str]:
    """Create an ignore pattern based on user preferences."""
    patterns = [
        "__pycache__",
        r"\.DS_Store",
        r"Thumbs\.db",
        r"\.git",
        r"\.svn",
        r"\.hg",
        r"\.vscode",
        r"\.idea",
        "build",
        "dist",
        r".*\.egg-info",
        r".*\.pyc",
        r".*\.pyo",
    ]

    if not include_evals:
        patterns.append("evals")

    if not is_community_or_official_toolkit:
        patterns.extend([".ruff.toml", ".pre-commit-config.yaml", "LICENSE"])
    else:
        patterns.extend(["README.md"])

    return re.compile(f"({'|'.join(patterns)})$")


def create_package(
    env: Environment,
    template_path: Path,
    output_path: Path,
    context: dict,
    ignore_pattern: re.Pattern[str],
) -> None:
    """Recursively create a new toolkit directory structure from jinja2 templates."""
    if ignore_pattern.match(template_path.name):
        return

    try:
        if template_path.is_dir():
            folder_name = render_template(env, template_path.name, context)
            new_dir_path = output_path / folder_name
            new_dir_path.mkdir(parents=True, exist_ok=True)

            for item in template_path.iterdir():
                create_package(env, item, new_dir_path, context, ignore_pattern)

        else:
            # Render the file name
            file_name = render_template(env, template_path.name, context)
            with open(template_path, encoding="utf-8") as f:
                content = f.read()
            # Render the file content
            content = render_template(env, content, context)

            write_template(output_path / file_name, content)
    except Exception as e:
        console.print(f"[red]Failed to create package: {e}[/red]")
        raise


def remove_toolkit(toolkit_directory: Path, toolkit_name: str) -> None:
    """Teardown logic for when creating a new toolkit fails."""
    toolkit_path = toolkit_directory / toolkit_name
    if toolkit_path.exists():
        shutil.rmtree(toolkit_path)


def create_new_toolkit(output_directory: str, toolkit_name: str) -> None:
    """Create a new toolkit from a template with user input."""
    toolkit_directory = Path(output_directory)

    # Check for illegal characters in the toolkit name
    if re.match(r"^[a-z0-9_]+$", toolkit_name):
        if (toolkit_directory / toolkit_name).exists():
            console.print(f"[red]Server '{toolkit_name}' already exists.[/red]")
            exit(1)
    else:
        console.print(
            "[red]Server name contains illegal characters. "
            "Only lowercase alphanumeric characters and underscores are allowed. "
            "Please try again.[/red]"
        )
        exit(1)

    toolkit_description = ask_question("Describe what your server will do (optional)", default="")
    toolkit_author_name = ask_question("Your GitHub username (optional)", default="")
    while True:
        toolkit_author_email = ask_question("Your email (optional)", default="")
        if toolkit_author_email == "" or re.match(r"[^@ ]+@[^@ ]+\.[^@ ]+", toolkit_author_email):
            break
        console.print(
            "[red]Invalid email format. Please enter a valid email address or leave it empty.[/red]"
        )
    include_evals = ask_yes_no_question(
        "Do you want an evals directory created for you?", default=True
    )

    cwd = Path.cwd()
    # TODO: this detection mechanism works only for people that didn't change the
    # name of the repo, a better detection method is required here
    is_community_toolkit = False
    if cwd.name == "toolkits" and cwd.parent.name == "arcade-mcp":
        prompt = (
            "Is your server a community contribution (to be merged into "
            "\x1b]8;;https://github.com/ArcadeAI/arcade-mcp\x1b\\ArcadeAI/arcade-mcp\x1b]8;;\x1b\\ repo)?"
        )
        is_community_toolkit = ask_yes_no_question(prompt, default=True)

    is_official_toolkit = cwd.name == "toolkits" and cwd.parent.name == "tools"

    context = {
        "package_name": "arcade_" + toolkit_name if is_community_toolkit else toolkit_name,
        "toolkit_name": toolkit_name,
        "toolkit_description": toolkit_description,
        "toolkit_author_name": toolkit_author_name,
        "toolkit_author_email": toolkit_author_email,
        "arcade_tdk_min_version": ARCADE_TDK_MIN_VERSION,
        "arcade_tdk_max_version": ARCADE_TDK_MAX_VERSION,
        "arcade_serve_min_version": ARCADE_SERVE_MIN_VERSION,
        "arcade_serve_max_version": ARCADE_SERVE_MAX_VERSION,
        "arcade_mcp_min_version": ARCADE_MCP_MIN_VERSION,
        "arcade_mcp_max_version": ARCADE_MCP_MAX_VERSION,
        "creation_year": datetime.now().year,
        "is_community_toolkit": is_community_toolkit,
        "is_official_toolkit": is_official_toolkit,
    }

    template_directory = get_full_template_directory() / "{{ toolkit_name }}"

    env = Environment(
        loader=FileSystemLoader(str(template_directory)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Create dynamic ignore pattern based on user preferences
    ignore_pattern = create_ignore_pattern(
        include_evals, is_community_toolkit or is_official_toolkit
    )

    try:
        create_package(env, template_directory, toolkit_directory, context, ignore_pattern)
        console.print(
            f"[green]Toolkit '{toolkit_name}' created successfully at '{toolkit_directory}'.[/green]"
        )
        create_deployment(toolkit_directory, toolkit_name)
    except Exception:
        remove_toolkit(toolkit_directory, toolkit_name)
        raise


def create_deployment(toolkit_directory: Path, toolkit_name: str) -> None:
    # No longer create worker.toml for MCP servers
    # The server.py file handles all configuration
    pass


def create_new_toolkit_minimal(output_directory: str, toolkit_name: str) -> None:
    """Create a new toolkit from a template with user input."""
    toolkit_directory = Path(output_directory)

    # Check for illegal characters in the toolkit name
    if re.match(r"^[a-z0-9_]+$", toolkit_name):
        if (toolkit_directory / toolkit_name).exists():
            raise FileExistsError(
                f"Server with name '{toolkit_name}' already exists at '{toolkit_directory / toolkit_name}'"
            )
    else:
        raise ValueError(
            f"Server name '{toolkit_name}' contains illegal characters. "
            "Only lowercase alphanumeric characters and underscores are allowed. "
            "Please try again."
        )

    context = {
        "toolkit_name": toolkit_name,
        "arcade_mcp_min_version": ARCADE_MCP_MIN_VERSION,
        "arcade_mcp_max_version": ARCADE_MCP_MAX_VERSION,
        "arcade_mcp_server_min_version": ARCADE_MCP_SERVER_MIN_VERSION,
        "arcade_mcp_server_max_version": ARCADE_MCP_SERVER_MAX_VERSION,
    }
    template_directory = get_minimal_template_directory() / "{{ toolkit_name }}"

    env = Environment(
        loader=FileSystemLoader(str(template_directory)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    ignore_pattern = create_ignore_pattern(False, False)

    try:
        create_package(env, template_directory, toolkit_directory, context, ignore_pattern)
        console.print(
            f"[green]Server '{toolkit_name}' created successfully at '{toolkit_directory}'.[/green]"
        )
    except Exception:
        remove_toolkit(toolkit_directory, toolkit_name)
        raise
