import sys
import subprocess
import pathlib
import yaml
import os
import logging
from typing import List, Tuple, Dict, Any, Optional

# Unified detached execution & VS Code attach flow helpers
from rockerc.core import (
    derive_container_name,
    prepare_launch_plan,
    execute_plan,
)
from .completion import install_all_completions


#############################################
# Coloring / Formatting Helpers
#############################################


class Colorizer:
    """Unified color and formatting helper for consistent styling."""

    ANSI = {
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
        "STRIKE": "\033[9m",
        "CYAN": "\033[36m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "RED": "\033[31m",
        "MAGENTA": "\033[35m",
        "BLUE": "\033[34m",
    }

    def __init__(self):
        self.enabled = os.environ.get("NO_COLOR") is None and sys.stdout.isatty()

    def style(self, text: str, color: str, *, bold: bool = False, strike: bool = False) -> str:
        """Apply color and styling to text."""
        if not self.enabled or not text:
            return text
        parts = [self.ANSI[color]]
        if bold:
            parts.append(self.ANSI["BOLD"])
        if strike:
            parts.append(self.ANSI["STRIKE"])
        parts.append(text)
        parts.append(self.ANSI["RESET"])
        return "".join(parts)

    def header(self, text: str) -> str:
        """Format text as a header (blue, bold)."""
        return self.style(text, "BLUE", bold=True)


# Global instance for backward compatibility
_colorizer = Colorizer()


class _Colors:  # pragma: no cover - trivial container for backward compatibility
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"


def _use_color() -> bool:
    # Respect NO_COLOR (https://no-color.org/) and only colorize when stdout is a TTY
    return _colorizer.enabled


def _c(txt: str, color: str, *, bold: bool = False) -> str:
    if not _use_color():
        return txt
    prefix = color
    if bold:
        prefix += _Colors.BOLD
    return f"{prefix}{txt}{_Colors.RESET}"


def _header(txt: str) -> str:
    return _c(txt, _Colors.BLUE, bold=True)


#############################################
# Simple Table Formatter
#############################################


def _format_table(rows: list[list[str]], headers: list[str]) -> str:
    """Format a simple table with aligned columns.

    Args:
        rows: List of row data (each row is a list of strings)
        headers: List of header strings

    Returns:
        Formatted table string
    """
    if not rows:
        return ""

    # Calculate column widths - need to strip ANSI codes for proper width calculation
    def strip_ansi(text: str) -> str:
        """Strip ANSI escape sequences from text for width calculation."""
        import re

        return re.sub(r"\033\[[0-9;]*m", "", text)

    all_rows = [headers] + rows
    col_count = len(headers)
    col_widths = [0] * col_count

    for row in all_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(strip_ansi(cell)))

    # Format rows
    lines = []
    for i, row in enumerate(all_rows):
        formatted_cells = []
        for j, cell in enumerate(row):
            # Pad with spaces (accounting for ANSI codes)
            visible_len = len(strip_ansi(cell))
            padding = col_widths[j] - visible_len
            formatted_cells.append(cell + " " * padding)
        lines.append("  ".join(formatted_cells))

    return "\n".join(lines)


#############################################
# Extension Table Renderer (new functionality)
#############################################


def _expand_aggregates(ext_list: list[str]) -> list[str]:
    """Normalize aggregated tokens like 'nvidia - x11 - user' into individual extensions."""
    expanded: list[str] = []
    for item in ext_list:
        if " - " in item and not item.strip().startswith("-"):
            parts = [p.strip() for p in item.split(" - ") if p.strip()]
            # Only expand if every part looks like a plausible extension token
            if parts and all(part.replace("-", "").isalnum() for part in parts):
                for p in parts:
                    if p not in expanded:
                        expanded.append(p)
                continue
        # Add non-aggregate items only if not already present
        if item not in expanded:
            expanded.append(item)
    return expanded


def _has_explicit_command_in_args(extra_args: str) -> bool:
    """Check if extra_args contains explicit commands (not just flags).

    This helper function reduces nesting in yaml_dict_to_args by extracting
    the command detection logic.

    Args:
        extra_args: Command line arguments string

    Returns:
        True if explicit commands are found, False otherwise
    """
    if not extra_args:
        return False

    import shlex

    try:
        tokens = shlex.split(extra_args)
        # Find command arguments (non-flag tokens that aren't flag values)
        skip_next = False
        for i, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                continue
            if token.startswith("--"):
                # Check if this flag takes a value (next token doesn't start with --)
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                    skip_next = True
            else:
                # Found a command
                return True
        return False
    except ValueError:
        # If shlex parsing fails, assume no command
        return False


def render_extension_table(
    final_args: list[str],
    *,
    original_global_args: list[str] | None,
    original_project_args: list[str] | None,
    blacklist: list[str],
    removed_by_blacklist: list[str],
    original_global_blacklist: list[str] | None = None,
    original_project_blacklist: list[str] | None = None,
) -> None:
    """Render a provenance table of extensions.

    Consumes pre-computed metadata – does NOT perform merge/filter logic.
    Columns: Global | Local | Status
    Group order: global-only, shared, local-only (stable original order).
    Blacklisted entries appear with strikethrough & red status in-place.
    """
    col = _colorizer

    # Expand aggregates first
    g_raw = _expand_aggregates(original_global_args or [])
    p_raw = _expand_aggregates(original_project_args or [])
    g_set = set(g_raw)
    p_set = set(p_raw)
    bl_set = set(blacklist)
    removed_set = set(removed_by_blacklist)
    final_set = set(final_args)
    g_bl_set = set(original_global_blacklist or [])
    p_bl_set = set(original_project_blacklist or [])

    # Remember original order for stable sorting (keep first occurrence only)
    raw_index = {}
    for i, n in enumerate(g_raw + p_raw):
        if n not in raw_index:
            raw_index[n] = i

    def group_rank(name: str) -> int:
        """Return group rank: 0=global-only, 1=shared, 2=local-only, 3=unknown."""
        in_g = (name in g_set) or (name in g_bl_set)
        in_p = (name in p_set) or (name in p_bl_set)
        if in_g and not in_p:
            return 0
        if in_g and in_p:
            return 1
        return 2 if in_p and not in_g else 3

    # Collect all unique names and sort by (group_rank, original_index)
    all_names = (
        set(g_raw) | set(p_raw) | g_bl_set | p_bl_set | set(blacklist) | set(removed_by_blacklist)
    )

    def sort_key(name: str):
        return (group_rank(name), raw_index.get(name, float("inf")))

    ordered = sorted(all_names, key=sort_key)

    def extension_status(ext: str) -> str:
        """Return status: loaded, blacklisted, or filtered."""
        if ext in final_set:
            return "loaded"
        if ext in removed_set:
            return "blacklisted"
        return "filtered" if ext in bl_set else "loaded"

    def fmt_cell(ext_name: str, show: bool, status: str, is_blacklisted_here: bool) -> str:
        """Format a table cell with appropriate styling."""
        if not show:
            return ""

        if status == "loaded":
            return col.style(ext_name, "CYAN")
        if status == "blacklisted":
            if is_blacklisted_here:
                return col.style(ext_name, "RED", strike=True)
            # Required here but blacklisted elsewhere
            return col.style(ext_name, "CYAN")
        # filtered
        return col.style(ext_name, "YELLOW")

    # Build rows
    rows = []
    for ext in ordered:
        status = extension_status(ext)

        # Show extension in a column if:
        # - It was in that column's args, OR
        # - It was blacklisted in that column (to show what's being blocked)
        show_in_global = (ext in g_set) or (ext in g_bl_set)
        show_in_local = (ext in p_set) or (ext in p_bl_set)

        # Apply strikethrough only in the column where it's blacklisted
        # NOT in columns where it's just present in args
        is_blacklisted_in_global = ext in g_bl_set
        is_blacklisted_in_local = ext in p_bl_set

        g_cell = fmt_cell(ext, show_in_global, status, is_blacklisted_in_global)
        l_cell = fmt_cell(ext, show_in_local, status, is_blacklisted_in_local)

        if status == "loaded":
            status_txt = col.style(status, "GREEN")
        elif status == "blacklisted":
            status_txt = col.style(status, "RED")
        else:
            status_txt = col.style(status, "YELLOW")

        rows.append([g_cell, l_cell, status_txt])

    # Print table
    if rows:
        headers = ["Global", "Local", "Status"]
        if col.enabled:
            headers = [col.style(h, "CYAN", bold=True) for h in headers]
        print(_format_table(rows, headers))


def yaml_dict_to_args(d: dict, extra_args: str = "") -> str:
    """Given a dictionary of arguments turn it into an argument string to pass to rocker.

    CRITICAL: This function automatically adds 'tail -f /dev/null' to detached containers
    to ensure they stay running for docker exec attachment. This is a core architectural
    requirement for rockerc/renv container lifecycle consistency.

    Args:
        d (dict): rocker arguments dictionary
        extra_args (str): additional command line arguments to insert before the image

    Returns:
        str: rocker arguments string with automatic keep-alive for detached containers

    Container Lifecycle:
        - When --detach is present: Automatically appends 'tail -f /dev/null' unless
          explicit command is provided in extra_args
        - This ensures ALL detached containers can be attached to via docker exec
        - Prevents "container is not running" errors during attachment

    Historical Context:
        - Before this fix: Each tool manually added keep-alive commands inconsistently
        - This centralized approach ensures no tool can forget the keep-alive requirement
        - See CONTAINER_LIFECYCLE.md for full architectural documentation
    """
    image = d.pop("image", None)
    segments = []

    # explicit flags
    for a in d.pop("args", []):
        segments.append(f"--{a}")

    # Remove extension-blacklist - it's only for internal rockerc filtering
    d.pop("extension-blacklist", None)

    # key/value pairs
    for k, v in d.items():
        segments.extend([f"--{k}", str(v)])

    # any extra CLI pieces - keep as string to preserve complex quoting
    cmd_str = " ".join(segments)
    if extra_args:
        cmd_str += f" {extra_args}"

    # separator + image
    if image:
        cmd_str += f" -- {image}"

        # Add keep-alive command for detached containers only
        if "--detach" in cmd_str and not _has_explicit_command_in_args(extra_args):
            cmd_str += " tail -f /dev/null"

    return cmd_str


def _load_and_validate_config(config_path: pathlib.Path) -> dict:
    """Load and validate a YAML config file.

    Args:
        config_path: Path to the config file

    Returns:
        dict: Parsed and validated configuration dictionary, or empty dict if parsing fails
    """
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            # Validate args format
            if config and "args" in config:
                _validate_args_format(config["args"], str(config_path))
            return config
    except yaml.YAMLError as e:
        logging.warning(f"Failed to parse YAML config at {config_path}: {e}")
        return {}
    except Exception as e:
        logging.warning(f"Error loading config at {config_path}: {e}")
        return {}


def load_global_config() -> dict:
    """Load global rockerc configuration from ~/.rockerc.yaml

    Returns:
        dict: Parsed configuration dictionary, or empty dict if parsing fails.
    """
    config_path = pathlib.Path.home() / ".rockerc.yaml"
    return _load_and_validate_config(config_path)


def deduplicate_extensions(extensions: list) -> list:
    """Remove duplicate extensions while preserving order

    Args:
        extensions (list): List of extension names

    Returns:
        list: Deduplicated list of extensions
    """
    seen = set()
    result = []
    for ext in extensions:
        if ext not in seen:
            seen.add(ext)
            result.append(ext)
    return result


def _validate_args_format(args: Optional[list], config_path: str) -> None:
    """Validate that args list doesn't contain malformed aggregate strings.

    Args:
        args: List of extension arguments or None
        config_path: Path to the config file for error messages

    Raises:
        ValueError: If malformed aggregate strings are detected
    """
    if not args or not isinstance(args, list):
        return

    for arg in args:
        if not isinstance(arg, str):
            continue

        # Detect common YAML indentation issues that create aggregate strings
        # Pattern: "word - word - word" (spaces around dashes)
        if " - " in arg and not arg.strip().startswith("-"):
            parts = [p.strip() for p in arg.split(" - ")]
            # If we have multiple parts that look like extension names, it's likely a formatting issue
            if len(parts) > 1 and all(
                part and part.replace("-", "").replace("_", "").isalnum() for part in parts
            ):
                raise ValueError(
                    f"Malformed args entry in {config_path}: '{arg}'\n"
                    f"  This looks like a YAML indentation issue. Each extension should be a separate list item:\n"
                    f"  \n"
                    f"  ❌ Incorrect (inconsistent indentation):\n"
                    f"  args:\n"
                    f"   - {parts[0]}\n"
                    f"    - {parts[1]}\n"
                    f"  \n"
                    f"  ✅ Correct (consistent indentation):\n"
                    f"  args:\n"
                    f"    - {parts[0]}\n"
                    f"    - {parts[1]}"
                )


def collect_arguments(path: str = ".") -> dict:
    """Search for rockerc.yaml files and return a merged dictionary

    Args:
        path (str, optional): path to reach for files. Defaults to ".".

    Returns:
        dict: A dictionary of merged rockerc arguments
    """
    # Load global configuration from ~/.rockerc.yaml
    global_config = {}
    global_config_path = pathlib.Path.home() / ".rockerc.yaml"
    if global_config_path.exists():
        print(f"loading {global_config_path}")
        with open(global_config_path, "r", encoding="utf-8") as f:
            global_config = yaml.safe_load(f) or {}

    # Load project-specific configuration
    search_path = pathlib.Path(path)
    merged_dict = {}
    for p in search_path.glob("rockerc.yaml"):
        print(f"loading {p}")
        config = _load_and_validate_config(p)
        merged_dict |= config

    # Start with global config as base, then override with project-specific settings
    final_dict = global_config | merged_dict

    # Special handling for args - merge and deduplicate instead of overriding
    global_args = global_config.get("args", [])
    project_args = merged_dict.get("args", [])
    if global_args or project_args:
        final_dict["args"] = deduplicate_extensions(global_args + project_args)

    # Special handling for extension-blacklist - merge lists instead of overriding
    global_blacklist = global_config.get("extension-blacklist", [])
    project_blacklist = merged_dict.get("extension-blacklist", [])

    # Ensure they are lists for consistent handling
    if not isinstance(global_blacklist, list):
        global_blacklist = [global_blacklist] if global_blacklist else []
    if not isinstance(project_blacklist, list):
        project_blacklist = [project_blacklist] if project_blacklist else []

    if global_blacklist or project_blacklist:
        final_dict["extension-blacklist"] = deduplicate_extensions(
            global_blacklist + project_blacklist
        )

    # Filter out blacklisted extensions from args
    if "extension-blacklist" in final_dict and "args" in final_dict:
        blacklisted_extensions = set(final_dict["extension-blacklist"])
        filtered_args = [arg for arg in final_dict["args"] if arg not in blacklisted_extensions]
        final_dict["args"] = filtered_args

    return final_dict


def collect_arguments_with_meta(path: str = ".") -> tuple[dict, dict]:
    """Enhanced variant of collect_arguments returning (final_config, metadata).

    Metadata contains:
      original_global_args: list | None
      original_project_args: list | None
      merged_args_before_blacklist: list
      removed_by_blacklist: list
      blacklist: list
      global_config_used: bool
      project_config_used: bool
      source_files: list[str]
    """
    # Load configs to capture metadata
    global_config = load_global_config()

    search_path = pathlib.Path(path)
    project_config: Dict[str, Any] = {}
    project_files: List[str] = []
    for p in search_path.glob("rockerc.yaml"):
        project_files.append(p.as_posix())
        config = _load_and_validate_config(p)
        project_config |= config

    # Extract metadata before merging
    g_args = global_config.get("args", []) or []
    p_args = project_config.get("args", []) or []
    merged_args = deduplicate_extensions(g_args + p_args) if (g_args or p_args) else []

    g_bl = global_config.get("extension-blacklist", []) or []
    p_bl = project_config.get("extension-blacklist", []) or []

    if not isinstance(g_bl, list):
        g_bl = [g_bl] if g_bl else []
    if not isinstance(p_bl, list):
        p_bl = [p_bl] if p_bl else []

    blacklist = deduplicate_extensions(g_bl + p_bl) if (g_bl or p_bl) else []
    removed = [a for a in merged_args if a in set(blacklist)] if (blacklist and merged_args) else []

    # Now use collect_arguments to get the final merged result
    final_dict = collect_arguments(path)

    meta = {
        "original_global_args": g_args or None,
        "original_project_args": p_args or None,
        "merged_args_before_blacklist": merged_args,
        "removed_by_blacklist": removed,
        "blacklist": blacklist,
        "original_global_blacklist": g_bl or None,
        "original_project_blacklist": p_bl or None,
        "global_config_used": bool(global_config),
        "project_config_used": bool(project_config),
        "source_files": project_files,
    }
    return final_dict, meta


def build_docker(dockerfile_path: str = ".") -> str:
    """Build a Docker image from a Dockerfile and return an autogenerated image tag based on where rocker was run.

    Args:
        dockerfile_path (str, optional): Path to the Dockerfile. Defaults to ".".

    Returns:
        str: The tag of the built Docker image.
    """

    tag = f"{pathlib.Path().absolute().name.lower()}:latest"
    dockerfile_dir = pathlib.Path(dockerfile_path).absolute().parent
    # Enable Docker BuildKit for improved build performance
    env = {**os.environ, "DOCKER_BUILDKIT": "1"}
    subprocess.call(["docker", "build", "-t", tag, str(dockerfile_dir)], env=env)
    return tag


def _format_docker_run_script(run_command_section: str) -> str:
    """Format docker run command as a bash script."""
    lines = run_command_section.split()
    formatted_lines = [
        "#!/bin/bash",
        "# This file was autogenerated by rockerc",
        "docker run \\",
    ]

    # Skip 'docker run' which is split in the first two items
    for i, line in enumerate(lines[2:], start=2):
        suffix = " \\" if i < len(lines) - 1 else ""
        formatted_lines.append(f"  {line}{suffix}")

    return "\n".join(formatted_lines)


def _write_dockerfile(dockerfile_content: str) -> None:
    """Write Dockerfile content to Dockerfile.rocker."""
    with open("Dockerfile.rocker", "w", encoding="utf-8") as dockerfile:
        dockerfile.write("#This file was autogenerated by rockerc\n")
        dockerfile.write(dockerfile_content)


def _write_run_script(script_content: str, script_path: str) -> None:
    """Write and make executable the run script."""
    with open(script_path, "w", encoding="utf-8") as bash_script:
        bash_script.write(script_content)
    os.chmod(script_path, 0o755)


def save_rocker_cmd(split_cmd: List[str]) -> str | None:
    dry_run = split_cmd + ["--mode", "dry-run"]
    try:
        s = subprocess.run(dry_run, capture_output=True, text=True, check=True)
        output = s.stdout

        # Split by "vvvvvv" to discard the top section
        _, after_vvvvvv = output.split("vvvvvv", 1)
        # Split by "^^^^^^" to get the second section
        section_to_save, after_caret = after_vvvvvv.split("^^^^^^", 1)

        # Save the Dockerfile section
        dockerfile_content = section_to_save.strip()
        _write_dockerfile(dockerfile_content)

        # Find the "run this command" section
        run_command_section = after_caret.split("Run this command: ", 1)[-1].strip()
        formatted_script_content = _format_docker_run_script(run_command_section)

        bash_script_path = "run_dockerfile.sh"
        _write_run_script(formatted_script_content, bash_script_path)

        logging.info(
            "Saved generated Dockerfile to Dockerfile.rocker and launch script to %s",
            bash_script_path,
        )
        return dockerfile_content
    except subprocess.CalledProcessError as e:
        logging.error("[rockerc] Error: rocker dry-run failed.")
        logging.error(f"[rockerc] Command: {' '.join(dry_run)}")
        logging.error(f"[rockerc] Exit code: {e.returncode}")
        logging.error(f"[rockerc] Output:\n{e.stdout}")
        logging.error(f"[rockerc] Error output:\n{e.stderr}")
        logging.error(
            "[rockerc] This likely means rocker or one of its extensions failed to generate a Dockerfile. Please check your rockerc.yaml and rocker installation."
        )
        sys.exit(e.returncode)
    except ValueError as e:
        logging.error(f"[rockerc] Error processing the output from rocker dry-run: {e}")
        logging.error(
            "[rockerc] The output format may have changed or rocker failed to generate the expected output."
        )
        sys.exit(1)
    return None


def _parse_extra_flags(argv: List[str]) -> Tuple[bool, bool, bool, bool, List[str]]:
    """Parse ad-hoc flags for --vsc, --force, --verbose and --show-dockerfile.

    Returns: (vsc, force, verbose, show_dockerfile, remaining_args)
    """
    vsc = False
    force = False
    verbose = False
    show_dockerfile = False
    remaining: List[str] = []
    for a in argv:
        if a == "--vsc":
            vsc = True
            continue
        if a in ("--force", "-f"):
            force = True
            continue
        if a in ("--verbose", "-v"):
            verbose = True
            continue
        if a == "--show-dockerfile":
            show_dockerfile = True
            continue
        remaining.append(a)
    return vsc, force, verbose, show_dockerfile, remaining


def parse_cli_extensions_and_image(
    args: List[str],
) -> Tuple[List[str], Optional[str], List[str]]:
    """Parse CLI arguments into extensions, image, and command.

    Args:
        args: List of command-line arguments (after removing --vsc, --force, --verbose)

    Returns:
        Tuple of (extensions, image, command)
        - extensions: List of extension names (without -- prefix)
        - image: Docker image name (first non-flag argument) or None
        - command: Command arguments (all args after image)

    Examples:
        ['--claude', 'ubuntu:22.04'] -> (['claude'], 'ubuntu:22.04', [])
        ['--user', '--git', 'ubuntu:22.04', 'bash'] -> (['user', 'git'], 'ubuntu:22.04', ['bash'])
        ['ubuntu:22.04'] -> ([], 'ubuntu:22.04', [])
        ['--user'] -> (['user'], None, [])
    """
    extensions: List[str] = []
    image: Optional[str] = None
    command: List[str] = []

    image_found = False
    for arg in args:
        if arg.startswith("--"):
            # Extension flag
            ext_name = arg[2:]  # Remove '--' prefix
            extensions.append(ext_name)
        elif not image_found:
            # First non-flag argument is the image
            image = arg
            image_found = True
        else:
            # Remaining arguments are command
            command.append(arg)

    return extensions, image, command


def _configure_logging(verbose: bool):  # pragma: no cover - formatting only
    # Remove any existing handlers (avoid duplicate logs when called multiple times)
    root = logging.getLogger()
    if root.handlers:
        for h in list(root.handlers):
            root.removeHandler(h)

    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler()

    def format_record(record: logging.LogRecord) -> str:
        level_color = {
            "DEBUG": _Colors.MAGENTA,
            "INFO": _Colors.GREEN,
            "WARNING": _Colors.YELLOW,
            "ERROR": _Colors.RED,
            "CRITICAL": _Colors.RED,
        }.get(record.levelname, _Colors.CYAN)
        prefix = _c(record.levelname, level_color, bold=True)
        msg = record.getMessage()
        return f"{prefix}: {msg}"

    class _Formatter(logging.Formatter):  # pragma: no cover - trivial
        def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
            return format_record(record)

    handler.setFormatter(_Formatter())
    root.addHandler(handler)
    root.setLevel(level)


def _print_verbose_metadata(meta: dict) -> None:
    """Print verbose metadata about configuration sources and merging."""
    origins: List[str] = []
    if meta.get("global_config_used"):
        origins.append("global ~/.rockerc.yaml")
    if meta.get("project_config_used"):
        origins.append("project rockerc.yaml")
    if origins:
        print(_c("Sources:", _Colors.DIM, bold=True), _c(", ".join(origins), _Colors.DIM))
    if meta.get("original_global_args"):
        print(
            _c("Global args:", _Colors.DIM, bold=True),
            _c(", ".join(meta["original_global_args"]), _Colors.DIM),
        )
    if meta.get("original_project_args"):
        print(
            _c("Project args:", _Colors.DIM, bold=True),
            _c(", ".join(meta["original_project_args"]), _Colors.DIM),
        )
    if meta.get("merged_args_before_blacklist"):
        print(
            _c("Merged (pre-blacklist):", _Colors.DIM, bold=True),
            _c(", ".join(meta["merged_args_before_blacklist"]), _Colors.DIM),
        )


def run_rockerc(path: str = "."):
    """Unified rockerc entry point (always-detached model).

    Behavior:
    1. Collect + merge configuration.
    2. Optionally build Dockerfile if 'dockerfile' key present.
    3. Support --create-dockerfile to emit a generated Dockerfile + run script.
    4. Always ensure container is (or becomes) detached so we can exec a shell.
    5. Optional VS Code attach with --vsc.
    6. Reuse existing container unless --force provided.
    """

    cli_args = sys.argv[1:]
    if "--install" in cli_args:
        rc_path: Optional[pathlib.Path] = None
        if "--rc-file" in cli_args:
            rc_index = cli_args.index("--rc-file")
            try:
                rc_arg = cli_args[rc_index + 1]
            except IndexError:
                logging.error("--rc-file requires a path argument when used with --install")
                sys.exit(1)
            rc_path = pathlib.Path(rc_arg)
        if len([arg for arg in cli_args if not arg.startswith("--")]) > (1 if rc_path else 0):
            logging.warning(
                "Ignoring unexpected arguments while installing completions: %s", cli_args
            )
        sys.exit(install_all_completions(rc_path))

    # --- Begin fix for auto extension workspace path handling ---
    vsc, force, verbose, show_dockerfile, filtered_cli = _parse_extra_flags(cli_args)
    _configure_logging(verbose)

    # Detect --auto and workspace path
    auto_idx = None
    auto_path = None
    auto_flag = False
    if "--auto" in filtered_cli:
        auto_idx = filtered_cli.index("--auto")
        auto_flag = True
        # If next argument exists and does not start with --, treat as workspace path
        if auto_idx + 1 < len(filtered_cli) and not filtered_cli[auto_idx + 1].startswith("--"):
            auto_path = filtered_cli[auto_idx + 1]
            # Remove workspace path from CLI so it is not treated as image or extension
            filtered_cli.pop(auto_idx + 1)
        else:
            auto_path = os.getcwd()
    # Remove --auto from CLI args for extension parsing
    if auto_idx is not None:
        filtered_cli.pop(auto_idx)

    # Use auto_path for config merging if present
    config_path = auto_path if auto_path else path
    merged_dict, meta = collect_arguments_with_meta(config_path)

    # Ensure auto extension is present in args if --auto was passed
    if auto_flag:
        if "auto" not in merged_dict.get("args", []):
            merged_dict["args"] = ["auto"] + merged_dict.get("args", [])

    if not merged_dict:
        logging.error(
            "No rockerc.yaml found in the specified directory. Please create a rockerc.yaml file with rocker arguments. See 'rocker -h' for help."
        )
        sys.exit(1)

    if "args" not in merged_dict:
        logging.error(
            "No 'args' key found in rockerc.yaml. Please add an 'args' list with rocker arguments. See 'rocker -h' for help."
        )
        sys.exit(1)

    # Dockerfile build handling
    if "dockerfile" in merged_dict:
        logging.info("Dockerfile specified -> building image locally")
        merged_dict["image"] = build_docker(merged_dict["dockerfile"])
        logging.info("Disabling 'pull' extension because a local Dockerfile was used")
        if "pull" in merged_dict["args"]:
            merged_dict["args"].remove("pull")
        merged_dict.pop("dockerfile")

    # create-dockerfile mode
    create_dockerfile = False
    if "create-dockerfile" in merged_dict["args"]:
        merged_dict["args"].remove("create-dockerfile")
        create_dockerfile = True

    # Parse CLI arguments to extract extensions, image, and command
    cli_extensions, cli_image, cli_command = parse_cli_extensions_and_image(filtered_cli)

    # Merge CLI extensions with config extensions
    if cli_extensions:
        merged_dict["args"] = deduplicate_extensions(merged_dict.get("args", []) + cli_extensions)

    # Override image if provided via CLI
    if cli_image:
        # Only set image if it is not a workspace path
        if not (auto_path and cli_image == auto_path):
            merged_dict["image"] = cli_image

    # Detect explicit container name in user filtered args (very naive: look for --name <value>)
    explicit_name = None
    if "--name" in filtered_cli:
        try:
            idx = filtered_cli.index("--name")
            explicit_name = filtered_cli[idx + 1]
        except (ValueError, IndexError):  # pragma: no cover - defensive
            pass

    container_name = derive_container_name(explicit_name)

    # Command arguments (space-preserved) for injection pass
    extra_cli = " ".join(cli_command)

    plan = prepare_launch_plan(
        merged_dict,
        extra_cli,
        container_name,
        vsc,
        force,
        pathlib.Path(config_path).absolute(),
    )

    # Render new provenance table (replaces prior summary block)
    render_extension_table(
        merged_dict.get("args", []),
        original_global_args=meta.get("original_global_args"),
        original_project_args=meta.get("original_project_args"),
        blacklist=meta.get("blacklist", []),
        removed_by_blacklist=meta.get("removed_by_blacklist", []),
        original_global_blacklist=meta.get("original_global_blacklist"),
        original_project_blacklist=meta.get("original_project_blacklist"),
    )

    # Show origin info (only if verbose to reduce noise)
    if verbose:
        _print_verbose_metadata(meta)

    if create_dockerfile and plan.rocker_cmd:
        dockerfile_content = save_rocker_cmd(plan.rocker_cmd)
        if show_dockerfile and dockerfile_content:
            print(_header("Generated Dockerfile (Dockerfile.rocker):"))
            print(_c(dockerfile_content, _Colors.DIM))
            print(_c("(End Dockerfile)", _Colors.DIM))

    exit_code = execute_plan(plan)
    sys.exit(exit_code)
    # --- End fix ---


if __name__ == "__main__":
    run_rockerc()
