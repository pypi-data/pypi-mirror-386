import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_agent.cli.config import settings
from mcp_agent.cli.core.constants import MCP_SECRETS_FILENAME
from mcp_agent.cli.utils.git_utils import (
    get_git_metadata,
    compute_directory_fingerprint,
    utc_iso_now,
)
from mcp_agent.cli.utils.ux import (
    console,
    print_error,
    print_warning,
    print_info,
    print_verbose,
)
from .bundle_utils import (
    create_pathspec_from_gitignore,
    should_ignore_by_gitignore,
)
from .constants import (
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_EMAIL,
    DEFAULT_DEPLOYMENTS_UPLOAD_API_BASE_URL,
    WRANGLER_SEND_METRICS,
)
from .settings import deployment_settings
from .validation import validate_project

# Pattern to match relative mcp-agent imports like "mcp-agent @ file://../../"
RELATIVE_MCP_AGENT_PATTERN = re.compile(
    r"^mcp-agent\s*@\s*file://[^\n]*$", re.MULTILINE
)


def _needs_requirements_modification(requirements_path: Path) -> bool:
    """Check if requirements.txt contains relative mcp-agent imports that need modification."""
    if not requirements_path.exists():
        return False

    content = requirements_path.read_text()
    return bool(RELATIVE_MCP_AGENT_PATTERN.search(content))


def _modify_requirements_txt(requirements_path: Path) -> None:
    """Modify requirements.txt in place to replace relative mcp-agent imports with absolute ones."""
    content = requirements_path.read_text()
    modified_content = RELATIVE_MCP_AGENT_PATTERN.sub("mcp-agent", content)
    requirements_path.write_text(modified_content)


def _handle_wrangler_error(e: subprocess.CalledProcessError) -> None:
    """Parse and present Wrangler errors in a clean format."""
    error_output = e.stderr or e.stdout or "No error output available"

    # Clean up ANSI escape sequences for better parsing
    clean_output = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", error_output)
    console.print("\n")

    # Check for authentication issues first
    if "Unauthorized 401" in clean_output or "401" in clean_output:
        print_error(
            "Authentication failed: Invalid or expired API key for bundling. Run 'mcp-agent login' or set MCP_API_KEY environment variable with new API key."
        )
        return

    # Extract key error messages
    lines = clean_output.strip().split("\n")

    # Look for the main error message (usually starts with ERROR or has [ERROR] tag)
    main_errors = []
    warnings = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match error patterns
        if re.search(r"^\[ERROR\]|^✘.*\[ERROR\]", line):
            # Extract the actual error message
            error_match = re.search(r"(?:\[ERROR\]|\[97mERROR\[.*?\])\s*(.*)", line)
            if error_match:
                main_errors.append(error_match.group(1).strip())
            else:
                main_errors.append(line)
        elif re.search(r"^\[WARNING\]|^▲.*\[WARNING\]", line):
            # Extract warning message
            warning_match = re.search(
                r"(?:\[WARNING\]|\[30mWARNING\[.*?\])\s*(.*)", line
            )
            if warning_match:
                warnings.append(warning_match.group(1).strip())
        elif line.startswith("ERROR:") or line.startswith("Error:"):
            main_errors.append(line)

    # Present cleaned up errors
    if warnings:
        for warning in warnings:
            print_warning(warning)

    if main_errors:
        for error in main_errors:
            print_error(error)
    else:
        # Fallback to raw output if we can't parse it
        print_error("Bundling failed with error:")
        print_error(clean_output)


def wrangler_deploy(
    app_id: str,
    api_key: str,
    project_dir: Path,
    ignore_file: Path | None = None,
) -> None:
    """Bundle the MCP Agent using Wrangler.

    A thin wrapper around the Wrangler CLI to bundle the MCP Agent application code
    and upload it our internal cf storage.

    Some key details here:
    - We copy the user's project to a temporary directory and perform all operations there
    - Secrets file must be excluded from the bundle
    - We must add a temporary `wrangler.toml` to the project directory to set python_workers
      compatibility flag (CLI arg is not sufficient).
    - Python workers with a `requirements.txt` file cannot be published by Wrangler, so we must
      rename any `requirements.txt` file to `requirements.txt.mcpac.py` before bundling
    - Non-python files (e.g. `uv.lock`, `poetry.lock`, `pyproject.toml`) would be excluded by default
    due to no py extension, so they are renamed with a `.mcpac.py` extension.
    - We exclude .venv directories from the copy to avoid bundling issues.

    Args:
        app_id (str): The application ID.
        api_key (str): User MCP Agent Cloud API key.
        project_dir (Path): The directory of the project to deploy.
        ignore_file (Path | None): Optional path to a gitignore-style file for excluding files from the bundle.
    """

    # Copy existing env to avoid overwriting
    env = os.environ.copy()

    env_updates = {
        "CLOUDFLARE_ACCOUNT_ID": CLOUDFLARE_ACCOUNT_ID,
        "CLOUDFLARE_API_TOKEN": api_key,
        "CLOUDFLARE_EMAIL": CLOUDFLARE_EMAIL,
        "WRANGLER_AUTH_DOMAIN": deployment_settings.wrangler_auth_domain,
        "WRANGLER_AUTH_URL": deployment_settings.wrangler_auth_url,
        "WRANGLER_SEND_METRICS": str(WRANGLER_SEND_METRICS).lower(),
        "CLOUDFLARE_API_BASE_URL": deployment_settings.cloudflare_api_base_url,
        "HOME": os.path.expanduser(settings.DEPLOYMENT_CACHE_DIR),
        "XDG_HOME_DIR": os.path.expanduser(settings.DEPLOYMENT_CACHE_DIR),
    }

    if os.name == "nt":
        # On Windows, configure npm to use a safe prefix within our cache directory
        # to avoid issues with missing global npm directories
        npm_prefix = (
            Path(os.path.expanduser(settings.DEPLOYMENT_CACHE_DIR)) / "npm-global"
        )
        npm_prefix.mkdir(parents=True, exist_ok=True)
        env_updates["npm_config_prefix"] = str(npm_prefix)

    if os.environ.get("__MCP_DISABLE_TLS_VALIDATION", "").lower() in ("1", "true", "yes"):
        if deployment_settings.DEPLOYMENTS_UPLOAD_API_BASE_URL == DEFAULT_DEPLOYMENTS_UPLOAD_API_BASE_URL:
            print_error(
                f"Cannot disable TLS validation when using {DEFAULT_DEPLOYMENTS_UPLOAD_API_BASE_URL}. "
                "Set MCP_DEPLOYMENTS_UPLOAD_API_BASE_URL to a custom endpoint."
            )
            raise ValueError(
                f"TLS validation cannot be disabled with {DEFAULT_DEPLOYMENTS_UPLOAD_API_BASE_URL}"
            )

        env_updates["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
        print_warning(
            "TLS certificate validation disabled (__MCP_DISABLE_TLS_VALIDATION is set)."
        )
        if settings.VERBOSE:
            print_info(
                f"Deployment endpoint: {deployment_settings.DEPLOYMENTS_UPLOAD_API_BASE_URL}"
            )

    env.update(env_updates)

    validate_project(project_dir)

    # We require main.py to be present as the entrypoint / app definition
    main_py = "main.py"

    # Create a temporary directory for all operations
    with tempfile.TemporaryDirectory(prefix="mcp-deploy-") as temp_dir_str:
        temp_project_dir = Path(temp_dir_str) / "project"

        # Load ignore rules (gitignore syntax) only if an explicit ignore file is provided
        ignore_spec = (
            create_pathspec_from_gitignore(ignore_file) if ignore_file else None
        )
        if ignore_file:
            if ignore_spec is None:
                print_warning(
                    f"Ignore file '{ignore_file}' not found; applying default excludes only"
                )
            else:
                print_info(f"Using ignore patterns from {ignore_file}")
        else:
            print_verbose("No ignore file provided; applying default excludes only")

        # Copy the entire project to temp directory, excluding unwanted directories and the live secrets file
        def ignore_patterns(path_str, names):
            ignored = set()

            # Keep existing hardcoded exclusions (highest priority)
            for name in names:
                if (name.startswith(".") and name not in {".env"}) or name in {
                    "logs",
                    "__pycache__",
                    "node_modules",
                    "venv",
                    MCP_SECRETS_FILENAME,  # Exclude mcp_agent.secrets.yaml only
                }:
                    ignored.add(name)

            # Apply explicit ignore file patterns (if provided)
            spec_ignored = should_ignore_by_gitignore(
                path_str, names, project_dir, ignore_spec
            )
            ignored.update(spec_ignored)

            return ignored

        shutil.copytree(project_dir, temp_project_dir, ignore=ignore_patterns)

        # Handle requirements.txt modification if needed
        requirements_path = temp_project_dir / "requirements.txt"
        if _needs_requirements_modification(requirements_path):
            _modify_requirements_txt(requirements_path)

        # Process non-Python files to be included in the bundle
        for root, _dirs, files in os.walk(temp_project_dir):
            for filename in files:
                file_path = Path(root) / filename

                # Skip temporary files and hidden files
                if filename.startswith(".") or filename.endswith((".bak", ".tmp")):
                    continue

                # Skip wrangler.toml (we create our own below)
                if filename == "wrangler.toml":
                    continue

                # For Python files, they're already included by Wrangler
                if filename.endswith(".py"):
                    continue

                # For non-Python files, rename with .mcpac.py extension to be included as py files
                py_path = file_path.with_suffix(file_path.suffix + ".mcpac.py")

                # Rename in place
                file_path.rename(py_path)

        # Compute and log which original files are being bundled (skip internal helpers)
        bundled_original_files: list[str] = []
        internal_bundle_files = {"wrangler.toml", "mcp_deploy_breadcrumb.py"}
        for root, _dirs, files in os.walk(temp_project_dir):
            for filename in files:
                rel = Path(root).relative_to(temp_project_dir) / filename
                if filename in internal_bundle_files:
                    continue
                if filename.endswith(".mcpac.py"):
                    orig_rel = str(rel)[: -len(".mcpac.py")]
                    bundled_original_files.append(orig_rel)
                else:
                    bundled_original_files.append(str(rel))

        bundled_original_files.sort()
        if bundled_original_files:
            print_verbose(
                "\n".join(
                    [f"Bundling {len(bundled_original_files)} project file(s):"]
                    + [f" - {p}" for p in bundled_original_files]
                )
            )

        # Collect deployment metadata (git if available, else workspace hash)
        git_meta = get_git_metadata(project_dir)
        deploy_source = "git" if git_meta else "workspace"
        meta_vars = {
            "MCP_DEPLOY_SOURCE": deploy_source,
            "MCP_DEPLOY_TIME_UTC": utc_iso_now(),
        }
        if git_meta:
            meta_vars.update(
                {
                    "MCP_DEPLOY_GIT_COMMIT": git_meta.commit_sha,
                    "MCP_DEPLOY_GIT_SHORT": git_meta.short_sha,
                    "MCP_DEPLOY_GIT_BRANCH": git_meta.branch or "",
                    "MCP_DEPLOY_GIT_DIRTY": "true" if git_meta.dirty else "false",
                }
            )
            # Friendly console hint
            dirty_mark = "*" if git_meta.dirty else ""
            print_info(
                f"Deploying from git commit {git_meta.short_sha}{dirty_mark} on branch {git_meta.branch or '?'}"
            )
        else:
            # Compute a cheap fingerprint (metadata-based) of the prepared project
            bundle_hash = compute_directory_fingerprint(
                temp_project_dir,
                ignore_names={
                    ".git",
                    "logs",
                    "__pycache__",
                    "node_modules",
                    "venv",
                    MCP_SECRETS_FILENAME,
                },
            )
            meta_vars.update({"MCP_DEPLOY_WORKSPACE_HASH": bundle_hash})
            print_verbose(
                f"Deploying from non-git workspace (hash {bundle_hash[:12]}…)"
            )

        # Write a breadcrumb file into the project so it ships with the bundle.
        # Use a Python file for guaranteed inclusion without renaming.
        breadcrumb = {
            "version": 1,
            "app_id": app_id,
            "deploy_time_utc": meta_vars["MCP_DEPLOY_TIME_UTC"],
            "source": meta_vars["MCP_DEPLOY_SOURCE"],
        }
        if git_meta:
            breadcrumb.update(
                {
                    "git": {
                        "commit": git_meta.commit_sha,
                        "short": git_meta.short_sha,
                        "branch": git_meta.branch,
                        "dirty": git_meta.dirty,
                        "tag": git_meta.tag,
                        "message": git_meta.commit_message,
                    }
                }
            )
        else:
            breadcrumb.update(
                {"workspace_fingerprint": meta_vars["MCP_DEPLOY_WORKSPACE_HASH"]}
            )

        breadcrumb_py = textwrap.dedent(
            """
            # Auto-generated by mcp-agent deploy. Do not edit.
            # Contains deployment metadata for traceability.
            import json as _json
            BREADCRUMB = %s
            BREADCRUMB_JSON = _json.dumps(BREADCRUMB, separators=(",", ":"))
            __all__ = ["BREADCRUMB", "BREADCRUMB_JSON"]
            """
        ).strip() % (json.dumps(breadcrumb, indent=2))

        (temp_project_dir / "mcp_deploy_breadcrumb.py").write_text(breadcrumb_py)

        # Create temporary wrangler.toml with [vars] carrying deploy metadata
        # Use TOML strings and keep values simple/escaped; also include a compact JSON blob
        meta_json = json.dumps(meta_vars, separators=(",", ":"))
        vars_lines = ["[vars]"] + [f'{k} = "{v}"' for k, v in meta_vars.items()]
        vars_lines.append(f'MCP_DEPLOY_META = """{meta_json}"""')

        wrangler_toml_content = textwrap.dedent(
            f"""
            name = "{app_id}"
            main = "{main_py}"
            compatibility_flags = ["python_workers"]
            compatibility_date = "2025-06-26"

            {os.linesep.join(vars_lines)}
        """
        ).strip()

        wrangler_toml_path = temp_project_dir / "wrangler.toml"
        wrangler_toml_path.write_text(wrangler_toml_content)

        spinner_column = SpinnerColumn(spinner_name="aesthetic")
        with Progress(
            "",
            spinner_column,
            TextColumn(" [progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task("Bundling MCP Agent...", total=None)

            try:
                cmd = [
                    "npx",
                    "--yes",
                    "wrangler@4.22.0",
                    "deploy",
                    main_py,
                    "--name",
                    app_id,
                    "--no-bundle",
                ]

                subprocess.run(
                    cmd,
                    check=True,
                    env=env,
                    cwd=str(temp_project_dir),
                    capture_output=True,
                    text=True,
                    # On Windows, we need to use shell=True for npx to work correctly
                    shell=(os.name == "nt"),
                    encoding="utf-8",
                    errors="replace",
                )
                spinner_column.spinner.frames = spinner_column.spinner.frames[-2:-1]
                progress.update(task, description="Bundled successfully")
            except subprocess.CalledProcessError as e:
                progress.update(task, description="❌ Bundling failed")
                _handle_wrangler_error(e)
                raise
