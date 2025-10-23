"""Nexus CLI - Command-line interface for Nexus filesystem operations.

Beautiful CLI with Click and Rich for file operations, discovery, and management.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, cast

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

import nexus
from nexus import NexusFilesystem
from nexus.core.exceptions import NexusError, NexusFileNotFoundError, ValidationError
from nexus.core.nexus_fs import NexusFS

console = Console()

# Global options
BACKEND_OPTION = click.option(
    "--backend",
    type=click.Choice(["local", "gcs"]),
    default="local",
    help="Backend type: local (default) or gcs (Google Cloud Storage)",
    show_default=True,
)

DATA_DIR_OPTION = click.option(
    "--data-dir",
    type=click.Path(),
    default=lambda: os.getenv("NEXUS_DATA_DIR", "./nexus-data"),
    help="Path to Nexus data directory (for local backend and metadata DB). Can also be set via NEXUS_DATA_DIR environment variable.",
    show_default=True,
)

GCS_BUCKET_OPTION = click.option(
    "--gcs-bucket",
    type=str,
    default=None,
    help="GCS bucket name (required when backend=gcs)",
)

GCS_PROJECT_OPTION = click.option(
    "--gcs-project",
    type=str,
    default=None,
    help="GCP project ID (optional for GCS backend)",
)

GCS_CREDENTIALS_OPTION = click.option(
    "--gcs-credentials",
    type=click.Path(exists=True),
    default=None,
    help="Path to GCS service account credentials JSON file",
)

CONFIG_OPTION = click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to Nexus config file (nexus.yaml)",
)


class BackendConfig:
    """Configuration for backend connection."""

    def __init__(
        self,
        backend: str = "local",
        data_dir: str = "./nexus-data",
        config_path: str | None = None,
        gcs_bucket: str | None = None,
        gcs_project: str | None = None,
        gcs_credentials: str | None = None,
    ):
        self.backend = backend
        self.data_dir = data_dir
        self.config_path = config_path
        self.gcs_bucket = gcs_bucket
        self.gcs_project = gcs_project
        self.gcs_credentials = gcs_credentials


def add_backend_options(func: Any) -> Any:
    """Decorator to add all backend-related options to a command and pass them via context."""
    import functools

    @CONFIG_OPTION
    @BACKEND_OPTION
    @DATA_DIR_OPTION
    @GCS_BUCKET_OPTION
    @GCS_PROJECT_OPTION
    @GCS_CREDENTIALS_OPTION
    @functools.wraps(func)
    def wrapper(
        config: str | None,
        backend: str,
        data_dir: str,
        gcs_bucket: str | None,
        gcs_project: str | None,
        gcs_credentials: str | None,
        **kwargs: Any,
    ) -> Any:
        # Create backend config and pass to function
        backend_config = BackendConfig(
            backend=backend,
            data_dir=data_dir,
            config_path=config,
            gcs_bucket=gcs_bucket,
            gcs_project=gcs_project,
            gcs_credentials=gcs_credentials,
        )
        return func(backend_config=backend_config, **kwargs)

    return wrapper


def get_filesystem(
    backend_config: BackendConfig, enforce_permissions: bool = True
) -> NexusFilesystem:
    """Get Nexus filesystem instance from backend configuration.

    Args:
        backend_config: Backend configuration
        enforce_permissions: Whether to enforce permissions (default: True)

    Returns:
        NexusFilesystem instance
    """
    try:
        if backend_config.config_path:
            # Use explicit config file
            return nexus.connect(config=backend_config.config_path)
        elif backend_config.backend == "gcs":
            # Use GCS backend via nexus.connect()
            if not backend_config.gcs_bucket:
                console.print("[red]Error:[/red] --gcs-bucket is required when using --backend=gcs")
                sys.exit(1)
            config = {
                "backend": "gcs",
                "gcs_bucket_name": backend_config.gcs_bucket,
                "gcs_project_id": backend_config.gcs_project,
                "gcs_credentials_path": backend_config.gcs_credentials,
                "db_path": str(Path(backend_config.data_dir) / "nexus-gcs-metadata.db"),
                "enforce_permissions": enforce_permissions,
            }
            return nexus.connect(config=config)
        else:
            # Use local backend (default)
            return nexus.connect(
                config={
                    "data_dir": backend_config.data_dir,
                    "enforce_permissions": enforce_permissions,
                }
            )
    except Exception as e:
        console.print(f"[red]Error connecting to Nexus:[/red] {e}")
        sys.exit(1)


def handle_error(e: Exception) -> None:
    """Handle errors with beautiful output."""
    if isinstance(e, PermissionError):
        console.print(f"[red]Permission Denied:[/red] {e}")
    elif isinstance(e, NexusFileNotFoundError):
        console.print(f"[red]Error:[/red] File not found: {e}")
    elif isinstance(e, ValidationError):
        console.print(f"[red]Validation Error:[/red] {e}")
    elif isinstance(e, NexusError):
        console.print(f"[red]Nexus Error:[/red] {e}")
    else:
        console.print(f"[red]Unexpected error:[/red] {e}")
    sys.exit(1)


@click.group()
@click.version_option(version=nexus.__version__, prog_name="nexus")
def main() -> None:
    """
    Nexus - AI-Native Distributed Filesystem

    Beautiful command-line interface for file operations, discovery, and management.
    """
    pass


@main.command()
@click.argument("path", default="./nexus-workspace", type=click.Path())
def init(path: str) -> None:
    """Initialize a new Nexus workspace.

    Creates a new Nexus workspace with the following structure:
    - nexus-data/    # Metadata and content storage
    - workspace/     # Agent-specific scratch space
    - shared/        # Shared data between agents

    Example:
        nexus init ./my-workspace
    """
    workspace_path = Path(path)
    data_dir = workspace_path / "nexus-data"

    try:
        # Create workspace structure
        workspace_path.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Nexus
        nx = nexus.connect(config={"data_dir": str(data_dir)})

        # Create default directories
        nx.mkdir("/workspace", exist_ok=True)
        nx.mkdir("/shared", exist_ok=True)

        nx.close()

        console.print(
            f"[green]✓[/green] Initialized Nexus workspace at [cyan]{workspace_path}[/cyan]"
        )
        console.print(f"  Data directory: [cyan]{data_dir}[/cyan]")
        console.print(f"  Workspace: [cyan]{workspace_path / 'workspace'}[/cyan]")
        console.print(f"  Shared: [cyan]{workspace_path / 'shared'}[/cyan]")
    except Exception as e:
        handle_error(e)


@main.command(name="ls")
@click.argument("path", default="/", type=str)
@click.option("-r", "--recursive", is_flag=True, help="List files recursively")
@click.option("-l", "--long", is_flag=True, help="Show detailed information")
@add_backend_options
def list_files(
    path: str,
    recursive: bool,
    long: bool,
    backend_config: BackendConfig,
) -> None:
    """List files in a directory.

    Examples:
        nexus ls /workspace
        nexus ls /workspace --recursive
        nexus ls /workspace -l
        nexus ls /workspace --backend=gcs --gcs-bucket=my-bucket
    """
    try:
        nx = get_filesystem(backend_config)

        if long:
            # Detailed listing
            files_raw = nx.list(path, recursive=recursive, details=True)
            files = cast(list[dict[str, Any]], files_raw)

            if not files:
                console.print(f"[yellow]No files found in {path}[/yellow]")
                nx.close()
                return

            table = Table(title=f"Files in {path}")
            table.add_column("Permissions", style="magenta")
            table.add_column("Owner", style="blue")
            table.add_column("Group", style="blue")
            table.add_column("Path", style="cyan")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Modified", style="yellow")

            # Get metadata with permissions
            if isinstance(nx, NexusFS):
                for file in files:
                    meta = nx.metadata.get(file["path"])

                    # Format permissions
                    if meta and meta.mode is not None:
                        from nexus.core.permissions import FileMode

                        mode_obj = FileMode(meta.mode)
                        perms_str = str(mode_obj)
                    else:
                        perms_str = "---------"

                    owner_str = meta.owner if meta and meta.owner else "-"
                    group_str = meta.group if meta and meta.group else "-"
                    size_str = f"{file['size']:,} bytes"
                    modified_str = (
                        file["modified_at"].strftime("%Y-%m-%d %H:%M:%S")
                        if file["modified_at"]
                        else "N/A"
                    )

                    table.add_row(
                        perms_str, owner_str, group_str, file["path"], size_str, modified_str
                    )
            else:
                # Remote FS - no permission support yet
                for file in files:
                    size_str = f"{file['size']:,} bytes"
                    modified_str = (
                        file["modified_at"].strftime("%Y-%m-%d %H:%M:%S")
                        if file["modified_at"]
                        else "N/A"
                    )
                    table.add_row("---------", "-", "-", file["path"], size_str, modified_str)

            console.print(table)
        else:
            # Simple listing
            files_raw = nx.list(path, recursive=recursive)
            file_paths = cast(list[str], files_raw)

            if not file_paths:
                console.print(f"[yellow]No files found in {path}[/yellow]")
                nx.close()
                return

            for file_path in file_paths:
                console.print(f"  {file_path}")

        nx.close()
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("path", type=str)
@add_backend_options
def cat(
    path: str,
    backend_config: BackendConfig,
) -> None:
    """Display file contents.

    Examples:
        nexus cat /workspace/data.txt
        nexus cat /workspace/code.py
    """
    try:
        nx = get_filesystem(backend_config)
        content = nx.read(path)
        nx.close()

        # Try to detect file type for syntax highlighting
        try:
            text = content.decode("utf-8")

            # Simple syntax highlighting based on extension
            if path.endswith(".py"):
                syntax = Syntax(text, "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            elif path.endswith(".json"):
                syntax = Syntax(text, "json", theme="monokai", line_numbers=True)
                console.print(syntax)
            elif path.endswith((".md", ".markdown")):
                syntax = Syntax(text, "markdown", theme="monokai")
                console.print(syntax)
            else:
                console.print(text)
        except UnicodeDecodeError:
            console.print(f"[yellow]Binary file ({len(content)} bytes)[/yellow]")
            console.print(f"[dim]{content[:100]!r}...[/dim]")
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("path", type=str)
@click.argument("content", type=str, required=False)
@click.option("-i", "--input", "input_file", type=click.File("rb"), help="Read from file or stdin")
@add_backend_options
def write(
    path: str,
    content: str | None,
    input_file: Any,
    backend_config: BackendConfig,
) -> None:
    """Write content to a file.

    Examples:
        nexus write /workspace/data.txt "Hello World"
        echo "Hello World" | nexus write /workspace/data.txt --input -
        nexus write /workspace/data.txt --input local_file.txt
    """
    try:
        nx = get_filesystem(backend_config)

        # Determine content source
        if input_file:
            file_content = input_file.read()
        elif content == "-":
            # Read from stdin
            file_content = sys.stdin.buffer.read()
        elif content:
            file_content = content.encode("utf-8")
        else:
            console.print("[red]Error:[/red] Must provide content or use --input")
            sys.exit(1)

        nx.write(path, file_content)
        nx.close()

        console.print(f"[green]✓[/green] Wrote {len(file_content)} bytes to [cyan]{path}[/cyan]")
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("source", type=str)
@click.argument("dest", type=str)
@add_backend_options
def cp(
    source: str,
    dest: str,
    backend_config: BackendConfig,
) -> None:
    """Copy a file (simple copy - for recursive copy use 'copy' command).

    Examples:
        nexus cp /workspace/source.txt /workspace/dest.txt
    """
    try:
        nx = get_filesystem(backend_config)

        # Read source
        content = nx.read(source)

        # Write to destination
        nx.write(dest, content)

        nx.close()

        console.print(f"[green]✓[/green] Copied [cyan]{source}[/cyan] → [cyan]{dest}[/cyan]")
    except Exception as e:
        handle_error(e)


@main.command(name="copy")
@click.argument("source", type=str)
@click.argument("dest", type=str)
@click.option("-r", "--recursive", is_flag=True, help="Copy directories recursively")
@click.option("--checksum", is_flag=True, help="Skip identical files (hash-based)", default=True)
@click.option("--no-checksum", is_flag=True, help="Disable checksum verification")
@add_backend_options
def copy_cmd(
    source: str,
    dest: str,
    recursive: bool,
    checksum: bool,
    no_checksum: bool,
    backend_config: BackendConfig,
) -> None:
    """Smart copy with deduplication.

    Copy files from source to destination with automatic deduplication.
    Uses content hashing to skip identical files.

    Supports both local filesystem paths and Nexus paths:
    - /path/in/nexus - Nexus virtual path
    - ./local/path or /local/path - Local filesystem path

    Examples:
        # Copy local directory to Nexus
        nexus copy ./local/data/ /workspace/data/ --recursive

        # Copy within Nexus
        nexus copy /workspace/source/ /workspace/dest/ --recursive

        # Copy Nexus to local
        nexus copy /workspace/data/ ./backup/ --recursive

        # Copy single file
        nexus copy /workspace/file.txt /workspace/copy.txt
    """
    try:
        from nexus.sync import copy_file, copy_recursive, is_local_path

        nx = get_filesystem(backend_config)

        # Handle --no-checksum flag
        use_checksum = checksum and not no_checksum

        if recursive:
            # Use progress bar from sync module (tqdm)
            stats = copy_recursive(nx, source, dest, checksum=use_checksum, progress=True)
            nx.close()

            # Display results
            console.print("[bold green]✓ Copy Complete![/bold green]")
            console.print(f"  Files checked: [cyan]{stats.files_checked}[/cyan]")
            console.print(f"  Files copied: [green]{stats.files_copied}[/green]")
            console.print(f"  Files skipped: [yellow]{stats.files_skipped}[/yellow] (identical)")
            console.print(f"  Bytes transferred: [cyan]{stats.bytes_transferred:,}[/cyan]")

            if stats.errors:
                console.print(f"\n[bold red]Errors:[/bold red] {len(stats.errors)}")
                for error in stats.errors[:10]:  # Show first 10 errors
                    console.print(f"  [red]•[/red] {error}")

        else:
            # Single file copy
            is_source_local = is_local_path(source)
            is_dest_local = is_local_path(dest)

            bytes_copied = copy_file(nx, source, dest, is_source_local, is_dest_local, use_checksum)

            nx.close()

            if bytes_copied > 0:
                console.print(
                    f"[green]✓[/green] Copied [cyan]{source}[/cyan] → [cyan]{dest}[/cyan] "
                    f"({bytes_copied:,} bytes)"
                )
            else:
                console.print(
                    f"[yellow]⊘[/yellow] Skipped [cyan]{source}[/cyan] (identical content)"
                )

    except Exception as e:
        handle_error(e)


@main.command(name="move")
@click.argument("source", type=str)
@click.argument("dest", type=str)
@click.option("-f", "--force", is_flag=True, help="Don't ask for confirmation")
@add_backend_options
def move_cmd(
    source: str,
    dest: str,
    force: bool,
    backend_config: BackendConfig,
) -> None:
    """Move files or directories.

    Move files from source to destination. This is an efficient rename
    when possible, otherwise copy + delete.

    Examples:
        nexus move /workspace/old.txt /workspace/new.txt
        nexus move /workspace/old_dir/ /workspace/new_dir/ --force
    """
    try:
        from nexus.sync import move_file

        nx = get_filesystem(backend_config)

        # Confirm unless --force
        if not force and not click.confirm(f"Move {source} to {dest}?"):
            console.print("[yellow]Cancelled[/yellow]")
            nx.close()
            return

        with console.status(f"[yellow]Moving {source} to {dest}...[/yellow]", spinner="dots"):
            success = move_file(nx, source, dest)

        nx.close()

        if success:
            console.print(f"[green]✓[/green] Moved [cyan]{source}[/cyan] → [cyan]{dest}[/cyan]")
        else:
            console.print(f"[red]Error:[/red] Failed to move {source}")
            sys.exit(1)

    except Exception as e:
        handle_error(e)


@main.command(name="sync")
@click.argument("source", type=str)
@click.argument("dest", type=str)
@click.option("--delete", is_flag=True, help="Delete files in dest that don't exist in source")
@click.option("--dry-run", is_flag=True, help="Preview changes without making them")
@click.option("--no-checksum", is_flag=True, help="Disable hash-based comparison")
@add_backend_options
def sync_cmd(
    source: str,
    dest: str,
    delete: bool,
    dry_run: bool,
    no_checksum: bool,
    backend_config: BackendConfig,
) -> None:
    """One-way sync from source to destination.

    Efficiently synchronizes files from source to destination using
    hash-based change detection. Only copies changed files.

    Supports both local filesystem paths and Nexus paths.

    Examples:
        # Sync local to Nexus
        nexus sync ./local/dataset/ /workspace/training/

        # Preview changes (dry run)
        nexus sync ./local/data/ /workspace/data/ --dry-run

        # Sync with deletion (mirror)
        nexus sync /workspace/source/ /workspace/dest/ --delete

        # Disable checksum (copy all files)
        nexus sync ./data/ /workspace/ --no-checksum
    """
    try:
        from nexus.sync import sync_directories

        nx = get_filesystem(backend_config)

        use_checksum = not no_checksum

        # Display sync configuration
        console.print(f"[cyan]Syncing:[/cyan] {source} → {dest}")
        if delete:
            console.print("  [yellow]⚠ Delete mode enabled[/yellow]")
        if dry_run:
            console.print("  [yellow]DRY RUN - No changes will be made[/yellow]")
        if not use_checksum:
            console.print("  [yellow]Checksum disabled - copying all files[/yellow]")
        console.print()

        # Use progress bar from sync module (tqdm)
        stats = sync_directories(
            nx, source, dest, delete=delete, dry_run=dry_run, checksum=use_checksum, progress=True
        )

        nx.close()

        # Display results
        if dry_run:
            console.print("[bold yellow]DRY RUN RESULTS:[/bold yellow]")
        else:
            console.print("[bold green]✓ Sync Complete![/bold green]")

        console.print(f"  Files checked: [cyan]{stats.files_checked}[/cyan]")
        console.print(f"  Files copied: [green]{stats.files_copied}[/green]")
        console.print(f"  Files skipped: [yellow]{stats.files_skipped}[/yellow] (identical)")

        if delete:
            console.print(f"  Files deleted: [red]{stats.files_deleted}[/red]")

        if not dry_run:
            console.print(f"  Bytes transferred: [cyan]{stats.bytes_transferred:,}[/cyan]")

        if stats.errors:
            console.print(f"\n[bold red]Errors:[/bold red] {len(stats.errors)}")
            for error in stats.errors[:10]:  # Show first 10 errors
                console.print(f"  [red]•[/red] {error}")

    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("path", type=str)
@click.option("-f", "--force", is_flag=True, help="Don't ask for confirmation")
@add_backend_options
def rm(
    path: str,
    force: bool,
    backend_config: BackendConfig,
) -> None:
    """Delete a file.

    Examples:
        nexus rm /workspace/data.txt
        nexus rm /workspace/data.txt --force
    """
    try:
        nx = get_filesystem(backend_config)

        # Check if file exists
        if not nx.exists(path):
            console.print(f"[yellow]File does not exist:[/yellow] {path}")
            nx.close()
            return

        # Confirm deletion unless --force
        if not force and not click.confirm(f"Delete {path}?"):
            console.print("[yellow]Cancelled[/yellow]")
            nx.close()
            return

        nx.delete(path)
        nx.close()

        console.print(f"[green]✓[/green] Deleted [cyan]{path}[/cyan]")
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("pattern", type=str)
@click.option("-p", "--path", default="/", help="Base path to search from")
@add_backend_options
def glob(
    pattern: str,
    path: str,
    backend_config: BackendConfig,
) -> None:
    """Find files matching a glob pattern.

    Supports:
    - * (matches any characters except /)
    - ** (matches any characters including /)
    - ? (matches single character)
    - [...] (character classes)

    Examples:
        nexus glob "**/*.py"
        nexus glob "*.txt" --path /workspace
        nexus glob "test_*.py"
    """
    try:
        nx = get_filesystem(backend_config)
        matches = nx.glob(pattern, path)
        nx.close()

        if not matches:
            console.print(f"[yellow]No files match pattern:[/yellow] {pattern}")
            return

        console.print(f"[green]Found {len(matches)} files matching[/green] [cyan]{pattern}[/cyan]:")
        for match in matches:
            console.print(f"  {match}")
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("pattern", type=str)
@click.option("-p", "--path", default="/", help="Base path to search from")
@click.option("-f", "--file-pattern", help="Filter files by glob pattern (e.g., *.py)")
@click.option("-i", "--ignore-case", is_flag=True, help="Case-insensitive search")
@click.option("-n", "--max-results", default=100, help="Maximum results to show")
@click.option(
    "--search-mode",
    type=click.Choice(["auto", "parsed", "raw"]),
    default="auto",
    help="Search mode: auto (try parsed, fallback to raw), parsed (only parsed), raw (only raw)",
    show_default=True,
)
@add_backend_options
def grep(
    pattern: str,
    path: str,
    file_pattern: str | None,
    ignore_case: bool,
    max_results: int,
    search_mode: str,
    backend_config: BackendConfig,
) -> None:
    """Search file contents using regex patterns.

    Search Modes:
    - auto: Try parsed text first, fallback to raw (default)
    - parsed: Only search parsed text (great for PDFs/docs)
    - raw: Only search raw file content (skip parsing)

    Examples:
        # Search all files (auto mode - tries parsed first)
        nexus grep "TODO"

        # Search only parsed content from PDFs
        nexus grep "revenue" --file-pattern "**/*.pdf" --search-mode=parsed

        # Search only raw content (skip parsing)
        nexus grep "TODO" --search-mode=raw

        # Other options
        nexus grep "def \\w+" --file-pattern "**/*.py"
        nexus grep "error" --ignore-case
        nexus grep "TODO" --path /workspace
    """
    try:
        nx = get_filesystem(backend_config)
        matches = nx.grep(
            pattern,
            path=path,
            file_pattern=file_pattern,
            ignore_case=ignore_case,
            max_results=max_results,
            search_mode=search_mode,
        )
        nx.close()

        if not matches:
            console.print(f"[yellow]No matches found for:[/yellow] {pattern}")
            return

        console.print(f"[green]Found {len(matches)} matches[/green] for [cyan]{pattern}[/cyan]")
        console.print(f"[dim]Search mode: {search_mode}[/dim]\n")

        current_file = None
        for match in matches:
            if match["file"] != current_file:
                current_file = match["file"]
                console.print(f"[bold cyan]{current_file}[/bold cyan]")

            # Display source type
            source = match.get("source", "raw")
            source_color = "magenta" if source == "parsed" else "dim"
            console.print(f"  [yellow]{match['line']}:[/yellow] {match['content']}")
            console.print(
                f"      [dim]Match: [green]{match['match']}[/green] "
                f"[{source_color}]({source})[/{source_color}][/dim]"
            )
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("path", type=str)
@click.option("-p", "--parents", is_flag=True, help="Create parent directories as needed")
@add_backend_options
def mkdir(
    path: str,
    parents: bool,
    backend_config: BackendConfig,
) -> None:
    """Create a directory.

    Examples:
        nexus mkdir /workspace/data
        nexus mkdir /workspace/deep/nested/dir --parents
    """
    try:
        nx = get_filesystem(backend_config)
        nx.mkdir(path, parents=parents, exist_ok=True)
        nx.close()

        console.print(f"[green]✓[/green] Created directory [cyan]{path}[/cyan]")
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("path", type=str)
@click.option("-r", "--recursive", is_flag=True, help="Remove directory and contents")
@click.option("-f", "--force", is_flag=True, help="Don't ask for confirmation")
@add_backend_options
def rmdir(
    path: str,
    recursive: bool,
    force: bool,
    backend_config: BackendConfig,
) -> None:
    """Remove a directory.

    Examples:
        nexus rmdir /workspace/data
        nexus rmdir /workspace/data --recursive --force
    """
    try:
        nx = get_filesystem(backend_config)

        # Confirm deletion unless --force
        if not force and not click.confirm(f"Remove directory {path}?"):
            console.print("[yellow]Cancelled[/yellow]")
            nx.close()
            return

        nx.rmdir(path, recursive=recursive)
        nx.close()

        console.print(f"[green]✓[/green] Removed directory [cyan]{path}[/cyan]")
    except Exception as e:
        handle_error(e)


@main.command()
@click.argument("path", type=str)
@add_backend_options
def info(
    path: str,
    backend_config: BackendConfig,
) -> None:
    """Show detailed file information.

    Examples:
        nexus info /workspace/data.txt
    """
    try:
        nx = get_filesystem(backend_config)

        # Check if file exists first
        if not nx.exists(path):
            console.print(f"[yellow]File not found:[/yellow] {path}")
            nx.close()
            return

        # Get file metadata from metadata store
        # Note: Only NexusFS mode has direct metadata access
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] File info is only available for NexusFS instances")
            nx.close()
            return

        file_meta = nx.metadata.get(path)
        nx.close()

        if not file_meta:
            console.print(f"[yellow]File not found:[/yellow] {path}")
            return

        table = Table(title=f"File Information: {path}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        created_str = (
            file_meta.created_at.strftime("%Y-%m-%d %H:%M:%S") if file_meta.created_at else "N/A"
        )
        modified_str = (
            file_meta.modified_at.strftime("%Y-%m-%d %H:%M:%S") if file_meta.modified_at else "N/A"
        )

        table.add_row("Path", file_meta.path)
        table.add_row("Size", f"{file_meta.size:,} bytes")
        table.add_row("Created", created_str)
        table.add_row("Modified", modified_str)
        table.add_row("ETag", file_meta.etag or "N/A")
        table.add_row("MIME Type", file_meta.mime_type or "N/A")

        # Show permissions if available
        if file_meta.owner or file_meta.group or file_meta.mode is not None:
            table.add_row("Owner", file_meta.owner or "N/A")
            table.add_row("Group", file_meta.group or "N/A")

            if file_meta.mode is not None:
                from nexus.core.permissions import FileMode

                mode_obj = FileMode(file_meta.mode)
                table.add_row("Permissions", f"{oct(file_meta.mode)} ({mode_obj})")

        console.print(table)
    except Exception as e:
        handle_error(e)


@main.command()
@add_backend_options
def version(
    backend_config: BackendConfig,
) -> None:  # noqa: ARG001
    """Show Nexus version information."""
    console.print(f"[cyan]Nexus[/cyan] version [green]{nexus.__version__}[/green]")
    console.print(f"Data directory: [cyan]{backend_config.data_dir}[/cyan]")


@main.command(name="export")
@click.argument("output", type=click.Path())
@click.option("-p", "--prefix", default="", help="Export only files with this prefix")
@click.option("--tenant-id", default=None, help="Filter by tenant ID")
@click.option(
    "--after",
    default=None,
    help="Export only files modified after this time (ISO format: 2024-01-01T00:00:00)",
)
@click.option("--include-deleted", is_flag=True, help="Include soft-deleted files in export")
@add_backend_options
def export_metadata(
    output: str,
    prefix: str,
    tenant_id: str | None,
    after: str | None,
    include_deleted: bool,
    backend_config: BackendConfig,
) -> None:
    """Export metadata to JSONL file for backup and migration.

    Exports all file metadata (paths, sizes, timestamps, hashes, custom metadata)
    to a JSONL file. Each line is a JSON object representing one file.

    Output is sorted by path for clean git diffs.

    IMPORTANT: This exports metadata only, not file content. The content remains
    in the CAS storage. To restore, you need both the metadata JSONL file AND
    the CAS storage directory.

    Examples:
        nexus export metadata-backup.jsonl
        nexus export workspace-backup.jsonl --prefix /workspace
        nexus export recent.jsonl --after 2024-01-01T00:00:00
        nexus export tenant.jsonl --tenant-id acme-corp
    """
    try:
        from nexus.core.export_import import ExportFilter

        nx = get_filesystem(backend_config)

        # Note: Only Embedded mode supports metadata export
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] Metadata export is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Parse after time if provided
        after_time = None
        if after:
            from datetime import datetime

            try:
                after_time = datetime.fromisoformat(after)
            except ValueError:
                console.print(
                    f"[red]Error:[/red] Invalid date format: {after}. Use ISO format (2024-01-01T00:00:00)"
                )
                nx.close()
                sys.exit(1)

        # Create export filter
        export_filter = ExportFilter(
            tenant_id=tenant_id,
            path_prefix=prefix,
            after_time=after_time,
            include_deleted=include_deleted,
        )

        # Display filter options
        console.print(f"[cyan]Exporting metadata to:[/cyan] {output}")
        if prefix:
            console.print(f"  Path prefix: [cyan]{prefix}[/cyan]")
        if tenant_id:
            console.print(f"  Tenant ID: [cyan]{tenant_id}[/cyan]")
        if after_time:
            console.print(f"  After time: [cyan]{after_time.isoformat()}[/cyan]")
        if include_deleted:
            console.print("  [yellow]Including deleted files[/yellow]")

        with console.status("[yellow]Exporting metadata...[/yellow]", spinner="dots"):
            count = nx.export_metadata(output, filter=export_filter)

        nx.close()

        console.print(f"[green]✓[/green] Exported [cyan]{count}[/cyan] file metadata records")
        console.print(f"  Output: [cyan]{output}[/cyan]")
    except Exception as e:
        handle_error(e)


@main.command(name="import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--conflict-mode",
    type=click.Choice(["skip", "overwrite", "remap", "auto"]),
    default="skip",
    help="How to handle path collisions (default: skip)",
)
@click.option("--dry-run", is_flag=True, help="Simulate import without making changes")
@click.option(
    "--no-preserve-ids",
    is_flag=True,
    help="Don't preserve original UUIDs from export (default: preserve)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    hidden=True,
    help="(Deprecated) Use --conflict-mode=overwrite instead",
)
@click.option(
    "--no-skip-existing",
    is_flag=True,
    hidden=True,
    help="(Deprecated) Use --conflict-mode option instead",
)
@add_backend_options
def import_metadata(
    input_file: str,
    conflict_mode: str,
    dry_run: bool,
    no_preserve_ids: bool,
    overwrite: bool,
    no_skip_existing: bool,
    backend_config: BackendConfig,
) -> None:
    """Import metadata from JSONL file.

    IMPORTANT: This imports metadata only, not file content. The content must
    already exist in the CAS storage (matched by content hash). This is useful for:
    - Restoring metadata after database corruption
    - Migrating metadata between instances (with same CAS content)
    - Creating alternative path mappings to existing content

    Conflict Resolution Modes:
    - skip: Keep existing files, skip imports (default)
    - overwrite: Replace existing files with imported data
    - remap: Rename imported files to avoid collisions (adds _imported suffix)
    - auto: Smart resolution - newer file wins based on timestamps

    Examples:
        nexus import metadata-backup.jsonl
        nexus import metadata-backup.jsonl --conflict-mode=overwrite
        nexus import metadata-backup.jsonl --conflict-mode=auto --dry-run
        nexus import metadata-backup.jsonl --conflict-mode=remap
    """
    try:
        from nexus.core.export_import import ImportOptions

        nx = get_filesystem(backend_config)

        # Note: Only Embedded mode supports metadata import
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] Metadata import is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Handle deprecated options for backward compatibility
        _ = no_skip_existing  # Deprecated parameter, kept for backward compatibility

        if overwrite:
            console.print(
                "[yellow]Warning:[/yellow] --overwrite is deprecated, use --conflict-mode=overwrite"
            )
            conflict_mode = "overwrite"

        # Create import options
        import_options = ImportOptions(
            dry_run=dry_run,
            conflict_mode=conflict_mode,  # type: ignore
            preserve_ids=not no_preserve_ids,
        )

        # Display import configuration
        console.print(f"[cyan]Importing metadata from:[/cyan] {input_file}")
        console.print(f"  Conflict mode: [yellow]{conflict_mode}[/yellow]")
        if dry_run:
            console.print("  [yellow]DRY RUN - No changes will be made[/yellow]")
        if no_preserve_ids:
            console.print("  [yellow]Not preserving original IDs[/yellow]")

        with console.status("[yellow]Importing metadata...[/yellow]", spinner="dots"):
            result = nx.import_metadata(input_file, options=import_options)

        nx.close()

        # Display results
        if dry_run:
            console.print("[bold yellow]DRY RUN RESULTS:[/bold yellow]")
        else:
            console.print("[bold green]✓ Import Complete![/bold green]")

        console.print(f"  Created: [green]{result.created}[/green]")
        console.print(f"  Updated: [cyan]{result.updated}[/cyan]")
        console.print(f"  Skipped: [yellow]{result.skipped}[/yellow]")
        if result.remapped > 0:
            console.print(f"  Remapped: [magenta]{result.remapped}[/magenta]")
        console.print(f"  Total: [bold]{result.total_processed}[/bold]")

        # Display collisions if any
        if result.collisions:
            console.print(f"\n[bold yellow]Collisions:[/bold yellow] {len(result.collisions)}")
            console.print()

            # Group collisions by resolution type
            from collections import defaultdict

            by_resolution = defaultdict(list)
            for collision in result.collisions:
                by_resolution[collision.resolution].append(collision)

            # Show summary by resolution type
            for resolution, collisions in sorted(by_resolution.items()):
                console.print(f"  [cyan]{resolution}:[/cyan] {len(collisions)} files")

            # Show detailed collision list (limit to first 10 for readability)
            if len(result.collisions) <= 10:
                console.print("\n[bold]Collision Details:[/bold]")
                for collision in result.collisions:
                    console.print(f"  • {collision.path}")
                    console.print(f"    [dim]{collision.message}[/dim]")
            else:
                console.print("\n[dim]Use --dry-run to see all collision details[/dim]")

    except Exception as e:
        handle_error(e)


@main.command(name="work")
@click.argument(
    "view_type",
    type=click.Choice(["ready", "pending", "blocked", "in-progress", "status"]),
)
@click.option("-l", "--limit", type=int, default=None, help="Maximum number of results to show")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@add_backend_options
def work_command(
    view_type: str,
    limit: int | None,
    json_output: bool,
    backend_config: BackendConfig,
) -> None:
    """Query work items using SQL views.

    View Types:
    - ready: Files ready for processing (status='ready', no blockers)
    - pending: Files waiting to be processed (status='pending')
    - blocked: Files blocked by dependencies
    - in-progress: Files currently being processed
    - status: Show aggregate statistics of all work queues

    Examples:
        nexus work ready --limit 10
        nexus work blocked
        nexus work status
        nexus work ready --json
    """
    try:
        nx = get_filesystem(backend_config)

        # Only Embedded mode has metadata store with work views
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] Work views are only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Handle status view (aggregate statistics)
        if view_type == "status":
            if json_output:
                import json

                ready_count = len(nx.metadata.get_ready_work())
                pending_count = len(nx.metadata.get_pending_work())
                blocked_count = len(nx.metadata.get_blocked_work())
                in_progress_count = len(nx.metadata.get_in_progress_work())

                status_data = {
                    "ready": ready_count,
                    "pending": pending_count,
                    "blocked": blocked_count,
                    "in_progress": in_progress_count,
                    "total": ready_count + pending_count + blocked_count + in_progress_count,
                }
                console.print(json.dumps(status_data, indent=2))
            else:
                ready_count = len(nx.metadata.get_ready_work())
                pending_count = len(nx.metadata.get_pending_work())
                blocked_count = len(nx.metadata.get_blocked_work())
                in_progress_count = len(nx.metadata.get_in_progress_work())
                total_count = ready_count + pending_count + blocked_count + in_progress_count

                table = Table(title="Work Queue Status")
                table.add_column("Queue", style="cyan")
                table.add_column("Count", justify="right", style="green")

                table.add_row("Ready", str(ready_count))
                table.add_row("Pending", str(pending_count))
                table.add_row("Blocked", str(blocked_count))
                table.add_row("In Progress", str(in_progress_count))
                table.add_row("[bold]Total[/bold]", f"[bold]{total_count}[/bold]")

                console.print(table)

            nx.close()
            return

        # Get work items based on view type
        if view_type == "ready":
            items = nx.metadata.get_ready_work(limit=limit)
            title = "Ready Work Items"
            description = "Files ready for processing"
        elif view_type == "pending":
            items = nx.metadata.get_pending_work(limit=limit)
            title = "Pending Work Items"
            description = "Files waiting to be processed"
        elif view_type == "blocked":
            items = nx.metadata.get_blocked_work(limit=limit)
            title = "Blocked Work Items"
            description = "Files blocked by dependencies"
        elif view_type == "in-progress":
            items = nx.metadata.get_in_progress_work(limit=limit)
            title = "In-Progress Work Items"
            description = "Files currently being processed"
        else:
            console.print(f"[red]Error:[/red] Unknown view type: {view_type}")
            nx.close()
            sys.exit(1)

        nx.close()

        # Output results
        if not items:
            console.print(f"[yellow]No {view_type} work items found[/yellow]")
            return

        if json_output:
            import json

            console.print(json.dumps(items, indent=2, default=str))
        else:
            console.print(f"[green]{description}[/green] ([cyan]{len(items)}[/cyan] items)\n")

            table = Table(title=title)
            table.add_column("Path", style="cyan", no_wrap=False)
            table.add_column("Status", style="yellow")
            table.add_column("Priority", justify="right", style="green")

            # Add blocker_count column for blocked view
            if view_type == "blocked":
                table.add_column("Blockers", justify="right", style="red")

            # Add worker info for in-progress view
            if view_type == "in-progress":
                table.add_column("Worker ID", style="magenta")
                table.add_column("Started At", style="dim")

            for item in items:
                import json as json_lib

                # Extract status and priority
                status_value = "N/A"
                if item.get("status"):
                    try:
                        status_value = json_lib.loads(item["status"])
                    except (json_lib.JSONDecodeError, TypeError):
                        status_value = str(item["status"])

                priority_value = "N/A"
                if item.get("priority"):
                    try:
                        priority_value = str(json_lib.loads(item["priority"]))
                    except (json_lib.JSONDecodeError, TypeError):
                        priority_value = str(item["priority"])

                # Build row data
                row_data = [
                    item["virtual_path"],
                    status_value,
                    priority_value,
                ]

                # Add blocker count for blocked view
                if view_type == "blocked":
                    blocker_count = item.get("blocker_count", 0)
                    row_data.append(str(blocker_count))

                # Add worker info for in-progress view
                if view_type == "in-progress":
                    worker_id = "N/A"
                    if item.get("worker_id"):
                        try:
                            worker_id = json_lib.loads(item["worker_id"])
                        except (json_lib.JSONDecodeError, TypeError):
                            worker_id = str(item["worker_id"])

                    started_at = "N/A"
                    if item.get("started_at"):
                        try:
                            started_at = json_lib.loads(item["started_at"])
                        except (json_lib.JSONDecodeError, TypeError):
                            started_at = str(item["started_at"])

                    row_data.extend([worker_id, started_at])

                table.add_row(*row_data)

            console.print(table)

    except Exception as e:
        handle_error(e)


@main.command(name="find-duplicates")
@click.option("-p", "--path", default="/", help="Base path to search from")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@add_backend_options
def find_duplicates(path: str, json_output: bool, backend_config: BackendConfig) -> None:
    """Find duplicate files using content hashes.

    Uses batch_get_content_ids() for efficient deduplication detection.
    Groups files by their content hash to find duplicates.

    Examples:
        nexus find-duplicates
        nexus find-duplicates --path /workspace
        nexus find-duplicates --json
    """
    try:
        nx = get_filesystem(backend_config)

        # Only Embedded mode supports batch_get_content_ids
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] find-duplicates is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Get all files under path
        with console.status(f"[yellow]Scanning files in {path}...[/yellow]", spinner="dots"):
            all_files_raw = nx.list(path, recursive=True)

            # Check if we got detailed results (list of dicts) or simple paths (list of strings)
            if all_files_raw and isinstance(all_files_raw[0], dict):
                # details=True was used
                all_files_detailed = cast(list[dict[str, Any]], all_files_raw)
                file_paths = [f["path"] for f in all_files_detailed]
            else:
                # Simple list of paths
                file_paths = cast(list[str], all_files_raw)

        if not file_paths:
            console.print(f"[yellow]No files found in {path}[/yellow]")
            nx.close()
            return

        # Get content hashes in batch (single query)
        with console.status(
            f"[yellow]Analyzing {len(file_paths)} files for duplicates...[/yellow]",
            spinner="dots",
        ):
            content_ids = nx.batch_get_content_ids(file_paths)

            # Group by hash
            from collections import defaultdict

            by_hash = defaultdict(list)
            for file_path, content_hash in content_ids.items():
                if content_hash:
                    by_hash[content_hash].append(file_path)

            # Find duplicate groups (hash with >1 file)
            duplicates = {h: paths for h, paths in by_hash.items() if len(paths) > 1}

        nx.close()

        # Calculate statistics
        total_files = len(file_paths)
        unique_hashes = len(by_hash)
        duplicate_groups = len(duplicates)
        duplicate_files = sum(len(paths) for paths in duplicates.values())

        if json_output:
            import json

            result = {
                "total_files": total_files,
                "unique_hashes": unique_hashes,
                "duplicate_groups": duplicate_groups,
                "duplicate_files": duplicate_files,
                "duplicates": [
                    {"content_hash": h, "paths": paths} for h, paths in duplicates.items()
                ],
            }
            console.print(json.dumps(result, indent=2))
        else:
            # Display summary
            console.print("\n[bold cyan]Duplicate File Analysis[/bold cyan]")
            console.print(f"Total files scanned: [green]{total_files}[/green]")
            console.print(f"Unique content hashes: [green]{unique_hashes}[/green]")
            console.print(f"Duplicate groups: [yellow]{duplicate_groups}[/yellow]")
            console.print(f"Duplicate files: [yellow]{duplicate_files}[/yellow]")

            if not duplicates:
                console.print("\n[green]✓ No duplicate files found![/green]")
                return

            # Display duplicate groups
            console.print("\n[bold yellow]Duplicate Groups:[/bold yellow]\n")

            for i, (content_hash, paths) in enumerate(duplicates.items(), 1):
                console.print(f"[bold]Group {i}[/bold] (hash: [dim]{content_hash[:16]}...[/dim])")
                console.print(f"  [yellow]{len(paths)} files with identical content:[/yellow]")
                for path in sorted(paths):
                    console.print(f"    • {path}")
                console.print()

            # Calculate potential space savings
            # Each duplicate group can save (n-1) copies
            console.print("[bold cyan]Storage Impact:[/bold cyan]")
            console.print(
                f"  Files that could be deduplicated: [yellow]{duplicate_files - duplicate_groups}[/yellow]"
            )
            console.print("  (CAS automatically deduplicates - no action needed!)")

    except Exception as e:
        handle_error(e)


@main.command(name="tree")
@click.argument("path", default="/", type=str)
@click.option("-L", "--level", type=int, default=None, help="Max depth to display")
@click.option("--show-size", is_flag=True, help="Show file sizes")
@add_backend_options
def tree(
    path: str,
    level: int | None,
    show_size: bool,
    backend_config: BackendConfig,
) -> None:
    """Display directory tree structure.

    Shows an ASCII tree view of files and directories with optional
    size information and depth limiting.

    Examples:
        nexus tree /workspace
        nexus tree /workspace -L 2
        nexus tree /workspace --show-size
    """
    try:
        nx = get_filesystem(backend_config)

        # Get all files recursively
        files_raw = nx.list(path, recursive=True, details=show_size)
        nx.close()

        if not files_raw:
            console.print(f"[yellow]No files found in {path}[/yellow]")
            return

        # Build tree structure
        from collections import defaultdict
        from pathlib import PurePosixPath

        tree_dict: dict[str, Any] = defaultdict(dict)

        if show_size:
            files = cast(list[dict[str, Any]], files_raw)
            for file in files:
                file_path = file["path"]
                parts = PurePosixPath(file_path).parts
                current = tree_dict
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Leaf node (file)
                        current[part] = file["size"]
                    else:  # Directory
                        if part not in current or not isinstance(current[part], dict):
                            current[part] = {}
                        current = current[part]
        else:
            file_paths = cast(list[str], files_raw)
            for file_path in file_paths:
                parts = PurePosixPath(file_path).parts
                current = tree_dict
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Leaf node (file)
                        current[part] = None
                    else:  # Directory
                        if part not in current or not isinstance(current[part], dict):
                            current[part] = {}
                        current = current[part]

        # Display tree
        def format_size(size: int) -> str:
            """Format size in human-readable format."""
            size_float = float(size)
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_float < 1024.0:
                    return f"{size_float:.1f} {unit}"
                size_float /= 1024.0
            return f"{size_float:.1f} PB"

        def print_tree(
            node: dict[str, Any],
            prefix: str = "",
            current_level: int = 0,
        ) -> tuple[int, int]:
            """Recursively print tree structure. Returns (file_count, total_size)."""
            if level is not None and current_level >= level:
                return 0, 0

            items = sorted(node.items())
            total_files = 0
            total_size = 0

            for i, (name, value) in enumerate(items):
                is_last_item = i == len(items) - 1
                connector = "└── " if is_last_item else "├── "
                extension = "    " if is_last_item else "│   "

                if isinstance(value, dict):
                    # Directory
                    console.print(f"{prefix}{connector}[bold cyan]{name}/[/bold cyan]")
                    files, size = print_tree(
                        value,
                        prefix + extension,
                        current_level + 1,
                    )
                    total_files += files
                    total_size += size
                else:
                    # File
                    total_files += 1
                    if show_size and value is not None:
                        size_str = format_size(value)
                        console.print(f"{prefix}{connector}{name} [dim]({size_str})[/dim]")
                        total_size += value
                    else:
                        console.print(f"{prefix}{connector}{name}")

            return total_files, total_size

        # Print header
        console.print(f"[bold green]{path}[/bold green]")

        # Print tree
        file_count, total_size = print_tree(tree_dict)

        # Print summary
        console.print()
        if show_size:
            console.print(f"[dim]{file_count} files, {format_size(total_size)} total[/dim]")
        else:
            console.print(f"[dim]{file_count} files[/dim]")

    except Exception as e:
        handle_error(e)


@main.command(name="size")
@click.argument("path", default="/", type=str)
@click.option("--human", "-h", is_flag=True, help="Human-readable output")
@click.option("--details", is_flag=True, help="Show per-file breakdown")
@add_backend_options
def size(
    path: str,
    human: bool,
    details: bool,
    backend_config: BackendConfig,
) -> None:
    """Calculate total size of files in a path.

    Recursively calculates the total size of all files under a given path.

    Examples:
        nexus size /workspace
        nexus size /workspace --human
        nexus size /workspace --details
    """
    try:
        nx = get_filesystem(backend_config)

        # Get all files with details
        with console.status(f"[yellow]Calculating size of {path}...[/yellow]", spinner="dots"):
            files_raw = nx.list(path, recursive=True, details=True)

        nx.close()

        if not files_raw:
            console.print(f"[yellow]No files found in {path}[/yellow]")
            return

        files = cast(list[dict[str, Any]], files_raw)

        # Calculate total size
        total_size = sum(f["size"] for f in files)
        file_count = len(files)

        def format_size(size: int) -> str:
            """Format size in human-readable format."""
            if not human:
                return f"{size:,} bytes"

            size_float = float(size)
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_float < 1024.0:
                    return f"{size_float:.1f} {unit}"
                size_float /= 1024.0
            return f"{size_float:.1f} PB"

        # Display summary
        console.print(f"[bold cyan]Size of {path}:[/bold cyan]")
        console.print(f"  Total size: [green]{format_size(total_size)}[/green]")
        console.print(f"  File count: [cyan]{file_count:,}[/cyan]")

        if details:
            console.print()
            console.print("[bold]Top 10 largest files:[/bold]")

            # Sort by size and show top 10
            sorted_files = sorted(files, key=lambda f: f["size"], reverse=True)[:10]

            table = Table()
            table.add_column("Size", justify="right", style="green")
            table.add_column("Path", style="cyan")

            for file in sorted_files:
                table.add_row(format_size(file["size"]), file["path"])

            console.print(table)

    except Exception as e:
        handle_error(e)


@main.command(name="mount")
@click.argument("mount_point", type=click.Path())
@click.option(
    "--mode",
    type=click.Choice(["binary", "text", "smart"]),
    default="smart",
    help="Mount mode: binary (raw), text (parsed), smart (auto-detect)",
    show_default=True,
)
@click.option(
    "--auto-parse",
    is_flag=True,
    help="Auto-parse binary files (PDFs, Office docs) as text by default. "
    "Eliminates need for .txt suffix on parsed files.",
)
@click.option(
    "--daemon",
    is_flag=True,
    help="Run in background (daemon mode)",
)
@click.option(
    "--allow-other",
    is_flag=True,
    help="Allow other users to access the mount",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable FUSE debug output",
)
@click.option(
    "--remote-url",
    type=str,
    default=None,
    help="Remote Nexus RPC server URL (e.g., http://localhost:8080)",
)
@click.option(
    "--remote-api-key",
    type=str,
    default=None,
    help="API key for remote server authentication (optional)",
)
@add_backend_options
def mount(
    mount_point: str,
    mode: str,
    auto_parse: bool,
    daemon: bool,
    allow_other: bool,
    debug: bool,
    remote_url: str | None,
    remote_api_key: str | None,
    backend_config: BackendConfig,
) -> None:
    """Mount Nexus filesystem to a local path.

    Mounts the Nexus filesystem using FUSE, allowing standard Unix tools
    to work seamlessly with Nexus files.

    Mount Modes:
    - binary: Return raw file content (no parsing)
    - text: Parse all files and return text representation
    - smart (default): Auto-detect file type and return appropriate format

    Virtual File Views:
    - .raw/ directory: Access original binary content
    - .txt suffix: View parsed text representation
    - .md suffix: View formatted markdown representation

    Examples:
        # Mount in smart mode (default)
        nexus mount /mnt/nexus

        # Mount in binary mode (raw files only)
        nexus mount /mnt/nexus --mode=binary

        # Mount in background
        nexus mount /mnt/nexus --daemon

        # Mount with debug output
        nexus mount /mnt/nexus --debug

        # Use standard Unix tools
        ls /mnt/nexus
        cat /mnt/nexus/workspace/document.pdf.txt
        grep "TODO" /mnt/nexus/workspace/**/*.py
        vim /mnt/nexus/workspace/file.txt
    """
    try:
        from nexus.fuse import mount_nexus

        # Get filesystem instance
        nx: NexusFilesystem
        if remote_url:
            # Use remote NexusFS
            from nexus.remote import RemoteNexusFS

            nx = RemoteNexusFS(
                server_url=remote_url,
                api_key=remote_api_key,
            )
        else:
            # Use local or GCS backend
            nx = get_filesystem(backend_config)

        # Create mount point if it doesn't exist
        mount_path = Path(mount_point)
        mount_path.mkdir(parents=True, exist_ok=True)

        # Display mount info
        console.print("[green]Mounting Nexus filesystem...[/green]")
        console.print(f"  Mount point: [cyan]{mount_point}[/cyan]")
        console.print(f"  Mode: [cyan]{mode}[/cyan]")
        if remote_url:
            console.print(f"  Remote URL: [cyan]{remote_url}[/cyan]")
        else:
            console.print(f"  Backend: [cyan]{backend_config.backend}[/cyan]")
        if daemon:
            console.print("  [yellow]Running in background (daemon mode)[/yellow]")

        console.print()
        console.print("[bold cyan]Virtual File Views:[/bold cyan]")
        console.print("  • [cyan].raw/[/cyan] - Access original binary content")
        console.print("  • [cyan]file.txt[/cyan] - View parsed text representation")
        console.print("  • [cyan]file.md[/cyan] - View formatted markdown")
        console.print()

        # Create log file path for daemon mode (before forking)
        log_file = None
        if daemon:
            log_file = f"/tmp/nexus-mount-{int(time.time())}.log"
            console.print(f"  Logs: [cyan]{log_file}[/cyan]")
            console.print()

        if daemon:
            # Daemon mode: double-fork BEFORE mounting
            import os
            import sys

            # First fork
            pid = os.fork()

            if pid > 0:
                # Parent process - wait for intermediate child to exit, then return
                os.waitpid(pid, 0)  # Reap intermediate child to avoid zombies
                console.print(f"[green]✓[/green] Mounted Nexus to [cyan]{mount_point}[/cyan]")
                console.print()
                console.print("[yellow]To unmount:[/yellow]")
                console.print(f"  nexus unmount {mount_point}")
                console.print()
                console.print("[yellow]To view logs:[/yellow]")
                console.print(f"  tail -f {log_file}")
                return

            # Intermediate child - detach and fork again
            os.setsid()  # Create new session and become session leader

            # Second fork
            pid2 = os.fork()

            if pid2 > 0:
                # Intermediate child exits immediately
                # This makes the grandchild process be adopted by init (PID 1)
                os._exit(0)

            # Grandchild (daemon process) - set up logging and redirect I/O
            sys.stdin.close()

            # log_file must be set when daemon=True
            assert log_file is not None, "log_file must be set in daemon mode"

            # Configure logging to file
            logging.basicConfig(
                filename=log_file,
                level=logging.DEBUG if debug else logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

            # Redirect stdout/stderr to log file (for any print statements or uncaught errors)
            sys.stdout = open(log_file, "a")  # noqa: SIM115
            sys.stderr = open(log_file, "a")  # noqa: SIM115

            # Log daemon startup
            logging.info(f"Nexus FUSE daemon starting (PID: {os.getpid()})")
            logging.info(f"Mount point: {mount_point}")
            logging.info(f"Mode: {mode}")
            if remote_url:
                logging.info(f"Remote URL: {remote_url}")
            else:
                logging.info(f"Backend: {backend_config.backend}")

            # Now mount the filesystem in the daemon process (foreground mode to block)
            try:
                fuse = mount_nexus(
                    nx,
                    mount_point,
                    mode=mode,
                    auto_parse=auto_parse,
                    foreground=True,  # Run in foreground to keep daemon process alive
                    allow_other=allow_other,
                    debug=debug,
                )
                logging.info("Mount completed, waiting for unmount signal...")
            except Exception as e:
                logging.error(f"Failed to mount: {e}", exc_info=True)
                os._exit(1)

            # Exit cleanly when unmounted
            logging.info("Daemon shutting down")
            os._exit(0)

        # Non-daemon mode: mount in background thread
        fuse = mount_nexus(
            nx,
            mount_point,
            mode=mode,
            foreground=False,  # Run in background thread
            allow_other=allow_other,
            debug=debug,
        )

        console.print(f"[green]Mounted Nexus to [cyan]{mount_point}[/cyan][/green]")
        console.print("[yellow]Press Ctrl+C to unmount[/yellow]")

        # Wait for signal (foreground mode)
        try:
            fuse.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]Unmounting...[/yellow]")
            fuse.unmount()
            console.print("[green]✓[/green] Unmounted")

    except ImportError:
        console.print(
            "[red]Error:[/red] FUSE support not available. "
            "Install with: pip install 'nexus-ai-fs[fuse]'"
        )
        sys.exit(1)
    except Exception as e:
        handle_error(e)


@main.command(name="unmount")
@click.argument("mount_point", type=click.Path(exists=True))
def unmount(mount_point: str) -> None:
    """Unmount a Nexus filesystem.

    Examples:
        nexus unmount /mnt/nexus
    """
    try:
        import platform
        import subprocess

        system = platform.system()

        console.print(f"[yellow]Unmounting {mount_point}...[/yellow]")

        try:
            if system == "Darwin":  # macOS
                subprocess.run(
                    ["umount", mount_point],
                    check=True,
                    capture_output=True,
                )
            elif system == "Linux":
                subprocess.run(
                    ["fusermount", "-u", mount_point],
                    check=True,
                    capture_output=True,
                )
            else:
                console.print(f"[red]Error:[/red] Unsupported platform: {system}")
                sys.exit(1)

            console.print(f"[green]✓[/green] Unmounted [cyan]{mount_point}[/cyan]")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            console.print(f"[red]Error:[/red] Failed to unmount: {error_msg}")
            sys.exit(1)

    except Exception as e:
        handle_error(e)


@main.command(name="serve")
@click.option("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
@click.option("--port", default=8080, type=int, help="Server port (default: 8080)")
@click.option("--api-key", default=None, help="API key for authentication (optional)")
@add_backend_options
def serve(
    host: str,
    port: int,
    api_key: str | None,
    backend_config: BackendConfig,
) -> None:
    """Start Nexus RPC server.

    Exposes all NexusFileSystem operations through a JSON-RPC API over HTTP.
    This allows remote clients (including FUSE mounts) to access Nexus over the network.

    The server provides direct endpoints for all NFS methods:
    - read, write, delete, exists
    - list, glob, grep
    - mkdir, rmdir, is_directory

    Examples:
        # Start server with local backend (no authentication)
        nexus serve

        # Start server with API key authentication
        nexus serve --api-key mysecretkey

        # Start server with GCS backend
        nexus serve --backend=gcs --gcs-bucket=my-bucket --api-key mysecretkey

        # Connect from Python
        from nexus.remote import RemoteNexusFS
        nx = RemoteNexusFS("http://localhost:8080", api_key="mysecretkey")
        nx.write("/workspace/file.txt", b"Hello, World!")

        # Mount with FUSE
        from nexus.fuse import mount_nexus
        mount_nexus(nx, "/mnt/nexus")
    """
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Import server components
        from nexus.server.rpc_server import NexusRPCServer

        # Get filesystem instance
        nx = get_filesystem(backend_config)

        # Create and start server
        console.print("[green]Starting Nexus RPC server...[/green]")
        console.print(f"  Host: [cyan]{host}[/cyan]")
        console.print(f"  Port: [cyan]{port}[/cyan]")
        console.print(f"  Backend: [cyan]{backend_config.backend}[/cyan]")
        if backend_config.backend == "gcs":
            console.print(f"  GCS Bucket: [cyan]{backend_config.gcs_bucket}[/cyan]")
        else:
            console.print(f"  Data Dir: [cyan]{backend_config.data_dir}[/cyan]")

        if api_key:
            console.print("  Authentication: [yellow]API key required[/yellow]")
        else:
            console.print("  Authentication: [yellow]None (open access)[/yellow]")

        console.print()
        console.print("[bold cyan]Endpoints:[/bold cyan]")
        console.print(f"  Health check: [cyan]http://{host}:{port}/health[/cyan]")
        console.print(f"  RPC methods: [cyan]http://{host}:{port}/api/nfs/{{method}}[/cyan]")
        console.print()
        console.print("[yellow]Connect from Python:[/yellow]")
        console.print("  from nexus.remote import RemoteNexusFS")
        console.print(f'  nx = RemoteNexusFS("http://{host}:{port}"', end="")
        if api_key:
            console.print(f', api_key="{api_key}")')
        else:
            console.print(")")
        console.print("  nx.write('/workspace/file.txt', b'Hello!')")
        console.print()
        console.print("[green]Press Ctrl+C to stop server[/green]")

        server = NexusRPCServer(
            nexus_fs=nx,
            host=host,
            port=port,
            api_key=api_key,
        )

        server.serve_forever()

    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        handle_error(e)


@main.command(name="chmod")
@click.argument("mode", type=str)
@click.argument("path", type=str)
@add_backend_options
def chmod_cmd(
    mode: str,
    path: str,
    backend_config: BackendConfig,
) -> None:
    """Change file mode (permissions).

    Mode can be specified as octal (e.g., '755', '0o644') or
    symbolic (e.g., 'rwxr-xr-x').

    Examples:
        nexus chmod 755 /workspace/script.sh
        nexus chmod 0o644 /workspace/data.txt
        nexus chmod rwxr-xr-x /workspace/file.txt
    """
    try:
        nx = get_filesystem(backend_config)

        # Note: Only Embedded mode supports permissions
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] chmod is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Check if file exists
        if not nx.exists(path):
            console.print(f"[red]Error:[/red] File not found: {path}")
            nx.close()
            sys.exit(1)

        # Use chmod method with permission checks
        nx.chmod(path, mode)
        nx.close()

        from nexus.core.permissions import FileMode, parse_mode

        mode_int = parse_mode(mode) if isinstance(mode, str) else mode
        mode_obj = FileMode(mode_int)
        console.print(
            f"[green]✓[/green] Changed mode of [cyan]{path}[/cyan] to [yellow]{mode_obj}[/yellow]"
        )
    except Exception as e:
        handle_error(e)


@main.command(name="chown")
@click.argument("owner", type=str)
@click.argument("path", type=str)
@add_backend_options
def chown_cmd(
    owner: str,
    path: str,
    backend_config: BackendConfig,
) -> None:
    """Change file owner.

    Examples:
        nexus chown alice /workspace/file.txt
        nexus chown bob /workspace/data/
    """
    try:
        nx = get_filesystem(backend_config)

        # Note: Only Embedded mode supports permissions
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] chown is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Check if file exists
        if not nx.exists(path):
            console.print(f"[red]Error:[/red] File not found: {path}")
            nx.close()
            sys.exit(1)

        # Use chown method with permission checks
        nx.chown(path, owner)
        nx.close()

        console.print(
            f"[green]✓[/green] Changed owner of [cyan]{path}[/cyan] to [yellow]{owner}[/yellow]"
        )
    except Exception as e:
        handle_error(e)


@main.command(name="chgrp")
@click.argument("group", type=str)
@click.argument("path", type=str)
@add_backend_options
def chgrp_cmd(
    group: str,
    path: str,
    backend_config: BackendConfig,
) -> None:
    """Change file group.

    Examples:
        nexus chgrp developers /workspace/code/
        nexus chgrp admins /workspace/config.yaml
    """
    try:
        nx = get_filesystem(backend_config)

        # Note: Only Embedded mode supports permissions
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] chgrp is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Check if file exists
        if not nx.exists(path):
            console.print(f"[red]Error:[/red] File not found: {path}")
            nx.close()
            sys.exit(1)

        # Use chgrp method with permission checks
        nx.chgrp(path, group)
        nx.close()

        console.print(
            f"[green]✓[/green] Changed group of [cyan]{path}[/cyan] to [yellow]{group}[/yellow]"
        )
    except Exception as e:
        handle_error(e)


@main.command(name="getfacl")
@click.argument("path", type=str)
@add_backend_options
def getfacl_cmd(
    path: str,
    backend_config: BackendConfig,
) -> None:
    """Display Access Control List (ACL) for a file.

    Examples:
        nexus getfacl /workspace/file.txt
        nexus getfacl /workspace/data/
    """
    try:
        nx = get_filesystem(backend_config)

        # Note: Only Embedded mode supports ACLs
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] getfacl is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Check if file exists
        if not nx.exists(path):
            console.print(f"[red]Error:[/red] File not found: {path}")
            nx.close()
            sys.exit(1)

        # Get file metadata
        file_meta = nx.metadata.get(path)
        if not file_meta:
            console.print(f"[red]Error:[/red] File not found: {path}")
            nx.close()
            sys.exit(1)

        # Display file info
        console.print(f"[bold]# file: {path}[/bold]")
        console.print(f"# owner: {file_meta.owner or 'N/A'}")
        console.print(f"# group: {file_meta.group or 'N/A'}")

        if file_meta.mode is not None:
            from nexus.core.permissions import FileMode

            mode_obj = FileMode(file_meta.mode)
            console.print(f"# mode: {oct(file_meta.mode)} ({mode_obj})")
        else:
            console.print("# mode: N/A")

        # Get ACL entries from database
        from sqlalchemy import select

        from nexus.storage.models import ACLEntryModel

        # Get path_id using public API
        path_id = nx.metadata.get_path_id(path)
        if path_id:
            with nx.metadata.SessionLocal() as session:
                stmt = select(ACLEntryModel).where(ACLEntryModel.path_id == path_id)
                acl_entries = session.scalars(stmt).all()

                if acl_entries:
                    console.print()
                    console.print("[bold]# ACL entries:[/bold]")
                    for entry in acl_entries:
                        deny_prefix = "deny:" if entry.deny else ""
                        if entry.identifier:
                            console.print(
                                f"{deny_prefix}{entry.entry_type}:{entry.identifier}:{entry.permissions}"
                            )
                        else:
                            console.print(f"{deny_prefix}{entry.entry_type}:{entry.permissions}")
                else:
                    console.print()
                    console.print("[dim]# No ACL entries[/dim]")

        nx.close()

    except Exception as e:
        handle_error(e)


@main.command(name="setfacl")
@click.argument("acl_entry", type=str)
@click.argument("path", type=str)
@click.option("--remove", "-x", is_flag=True, help="Remove ACL entry")
@add_backend_options
def setfacl_cmd(
    acl_entry: str,
    path: str,
    remove: bool,
    backend_config: BackendConfig,
) -> None:
    """Set or remove Access Control List (ACL) entry.

    ACL Entry Format:
        user:<username>:rwx    - Grant user permissions
        group:<groupname>:r-x  - Grant group permissions
        deny:user:<username>   - Deny user access

    Examples:
        # Grant alice read+write
        nexus setfacl user:alice:rw- /workspace/file.txt

        # Grant developers group read+execute
        nexus setfacl group:developers:r-x /workspace/code/

        # Deny bob access
        nexus setfacl deny:user:bob /workspace/secret.txt

        # Remove ACL entry
        nexus setfacl user:alice:rwx /workspace/file.txt --remove
    """
    try:
        from nexus.core.acl import ACLEntry

        nx = get_filesystem(backend_config)

        # Note: Only Embedded mode supports ACLs
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] setfacl is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Check if file exists
        if not nx.exists(path):
            console.print(f"[red]Error:[/red] File not found: {path}")
            nx.close()
            sys.exit(1)

        # Parse ACL entry
        try:
            entry = ACLEntry.from_string(acl_entry)
        except ValueError as e:
            console.print(f"[red]Error:[/red] Invalid ACL entry: {e}")
            nx.close()
            sys.exit(1)

        # Get file metadata to find path_id
        file_meta = nx.metadata.get(path)
        if not file_meta:
            console.print(f"[red]Error:[/red] File not found: {path}")
            nx.close()
            sys.exit(1)

        # Get path_id using public API
        path_id = nx.metadata.get_path_id(path)
        if path_id:
            from sqlalchemy import delete

            from nexus.storage.models import ACLEntryModel

            with nx.metadata.SessionLocal() as session:
                if remove:
                    # Remove ACL entry
                    stmt = delete(ACLEntryModel).where(
                        ACLEntryModel.path_id == path_id,
                        ACLEntryModel.entry_type == entry.entry_type.value,
                        ACLEntryModel.identifier == entry.identifier,
                    )
                    result = session.execute(stmt)
                    session.commit()

                    if result.rowcount > 0:  # type: ignore[attr-defined]
                        console.print(
                            f"[green]✓[/green] Removed ACL entry [yellow]{acl_entry}[/yellow] "
                            f"from [cyan]{path}[/cyan]"
                        )
                    else:
                        console.print("[yellow]No matching ACL entry found to remove[/yellow]")
                else:
                    # Add ACL entry
                    # First remove existing entry for same type+identifier
                    stmt = delete(ACLEntryModel).where(
                        ACLEntryModel.path_id == path_id,
                        ACLEntryModel.entry_type == entry.entry_type.value,
                        ACLEntryModel.identifier == entry.identifier,
                    )
                    session.execute(stmt)

                    # Create new entry
                    acl_model = ACLEntryModel(
                        path_id=path_id,
                        entry_type=entry.entry_type.value,
                        identifier=entry.identifier,
                        permissions=entry.to_string().split(":")[-1],  # Get rwx part
                        deny=entry.deny,
                    )
                    session.add(acl_model)
                    session.commit()

                    console.print(
                        f"[green]✓[/green] Added ACL entry [yellow]{acl_entry}[/yellow] "
                        f"to [cyan]{path}[/cyan]"
                    )

        nx.close()

    except Exception as e:
        handle_error(e)


# ReBAC Commands (Relationship-Based Access Control)
@main.group(name="rebac")
def rebac() -> None:
    """Relationship-Based Access Control (ReBAC) commands.

    Manage authorization relationships using Zanzibar-style ReBAC.
    Enables team-based permissions, hierarchical access, and dynamic inheritance.

    Examples:
        nexus rebac create agent alice member-of group eng-team
        nexus rebac check agent alice read file file123
        nexus rebac expand read file file123
        nexus rebac delete <tuple-id>
    """
    pass


@rebac.command(name="create")
@click.argument("subject_type", type=str)
@click.argument("subject_id", type=str)
@click.argument("relation", type=str)
@click.argument("object_type", type=str)
@click.argument("object_id", type=str)
@click.option("--expires", type=str, default=None, help="Expiration time (ISO format)")
@add_backend_options
def rebac_create(
    subject_type: str,
    subject_id: str,
    relation: str,
    object_type: str,
    object_id: str,
    expires: str | None,
    backend_config: BackendConfig,
) -> None:
    """Create a relationship tuple.

    Creates a (subject, relation, object) tuple representing a relationship.

    Examples:
        # Alice is member of eng-team
        nexus rebac create agent alice member-of group eng-team

        # Eng-team owns file123
        nexus rebac create group eng-team owner-of file file123

        # Parent folder has child folder
        nexus rebac create file parent-folder parent-of file child-folder

        # Temporary access (expires in 1 hour)
        nexus rebac create agent bob viewer-of file secret --expires 2025-12-31T23:59:59
    """
    try:
        from pathlib import Path

        from nexus.core.rebac_manager import ReBACManager

        nx = get_filesystem(backend_config)

        # Only Embedded mode supports ReBAC
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] ReBAC is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Get database path
        db_path = Path(backend_config.data_dir) / "metadata.db"
        rebac_mgr = ReBACManager(db_path=str(db_path))

        # Parse expiration time if provided
        expires_at = None
        if expires:
            from datetime import datetime

            try:
                expires_at = datetime.fromisoformat(expires)
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid date format: {expires}")
                console.print("Use ISO format: 2025-12-31T23:59:59")
                nx.close()
                sys.exit(1)

        # Create tuple
        tuple_id = rebac_mgr.rebac_write(
            subject=(subject_type, subject_id),
            relation=relation,
            object=(object_type, object_id),
            expires_at=expires_at,
        )

        rebac_mgr.close()
        nx.close()

        console.print("[green]✓[/green] Created relationship tuple")
        console.print(f"  Tuple ID: [cyan]{tuple_id}[/cyan]")
        console.print(f"  Subject: [yellow]{subject_type}:{subject_id}[/yellow]")
        console.print(f"  Relation: [magenta]{relation}[/magenta]")
        console.print(f"  Object: [yellow]{object_type}:{object_id}[/yellow]")
        if expires_at:
            console.print(f"  Expires: [dim]{expires_at.isoformat()}[/dim]")

    except Exception as e:
        handle_error(e)


@rebac.command(name="delete")
@click.argument("tuple_id", type=str)
@add_backend_options
def rebac_delete_cmd(
    tuple_id: str,
    backend_config: BackendConfig,
) -> None:
    """Delete a relationship tuple.

    Examples:
        nexus rebac delete 550e8400-e29b-41d4-a716-446655440000
    """
    try:
        from pathlib import Path

        from nexus.core.rebac_manager import ReBACManager

        nx = get_filesystem(backend_config)

        # Only Embedded mode supports ReBAC
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] ReBAC is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Get database path
        db_path = Path(backend_config.data_dir) / "metadata.db"
        rebac_mgr = ReBACManager(db_path=str(db_path))

        # Delete tuple
        deleted = rebac_mgr.rebac_delete(tuple_id)

        rebac_mgr.close()
        nx.close()

        if deleted:
            console.print(f"[green]✓[/green] Deleted relationship tuple [cyan]{tuple_id}[/cyan]")
        else:
            console.print(f"[yellow]Tuple not found:[/yellow] {tuple_id}")

    except Exception as e:
        handle_error(e)


@rebac.command(name="check")
@click.argument("subject_type", type=str)
@click.argument("subject_id", type=str)
@click.argument("permission", type=str)
@click.argument("object_type", type=str)
@click.argument("object_id", type=str)
@add_backend_options
def rebac_check_cmd(
    subject_type: str,
    subject_id: str,
    permission: str,
    object_type: str,
    object_id: str,
    backend_config: BackendConfig,
) -> None:
    """Check if subject has permission on object.

    Uses graph traversal and caching to determine if permission is granted.

    Examples:
        # Does alice have read permission on file123?
        nexus rebac check agent alice read file file123

        # Does bob have write permission on workspace?
        nexus rebac check agent bob write workspace main

        # Does eng-team have owner permission on project?
        nexus rebac check group eng-team owner file project-folder
    """
    try:
        from pathlib import Path

        from nexus.core.rebac_manager import ReBACManager

        nx = get_filesystem(backend_config)

        # Only Embedded mode supports ReBAC
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] ReBAC is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Get database path
        db_path = Path(backend_config.data_dir) / "metadata.db"
        rebac_mgr = ReBACManager(db_path=str(db_path))

        # Check permission
        granted = rebac_mgr.rebac_check(
            subject=(subject_type, subject_id),
            permission=permission,
            object=(object_type, object_id),
        )

        rebac_mgr.close()
        nx.close()

        # Display result
        if granted:
            console.print("[green]✓ GRANTED[/green]")
            console.print(
                f"  [yellow]{subject_type}:{subject_id}[/yellow] has [magenta]{permission}[/magenta] on [yellow]{object_type}:{object_id}[/yellow]"
            )
        else:
            console.print("[red]✗ DENIED[/red]")
            console.print(
                f"  [yellow]{subject_type}:{subject_id}[/yellow] does NOT have [magenta]{permission}[/magenta] on [yellow]{object_type}:{object_id}[/yellow]"
            )

    except Exception as e:
        handle_error(e)


@rebac.command(name="expand")
@click.argument("permission", type=str)
@click.argument("object_type", type=str)
@click.argument("object_id", type=str)
@add_backend_options
def rebac_expand_cmd(
    permission: str,
    object_type: str,
    object_id: str,
    backend_config: BackendConfig,
) -> None:
    """Find all subjects with a given permission on an object.

    Uses recursive graph traversal to find all subjects.

    Examples:
        # Who has read permission on file123?
        nexus rebac expand read file file123

        # Who has write permission on workspace?
        nexus rebac expand write workspace main

        # Who owns the project folder?
        nexus rebac expand owner file project-folder
    """
    try:
        from pathlib import Path

        from nexus.core.rebac_manager import ReBACManager

        nx = get_filesystem(backend_config)

        # Only Embedded mode supports ReBAC
        if not isinstance(nx, NexusFS):
            console.print("[red]Error:[/red] ReBAC is only available in embedded mode")
            nx.close()
            sys.exit(1)

        # Get database path
        db_path = Path(backend_config.data_dir) / "metadata.db"
        rebac_mgr = ReBACManager(db_path=str(db_path))

        # Expand permission
        subjects = rebac_mgr.rebac_expand(
            permission=permission,
            object=(object_type, object_id),
        )

        rebac_mgr.close()
        nx.close()

        # Display results
        if not subjects:
            console.print(
                f"[yellow]No subjects found with[/yellow] [magenta]{permission}[/magenta] [yellow]on[/yellow] [cyan]{object_type}:{object_id}[/cyan]"
            )
            return

        console.print(
            f"[green]Found {len(subjects)} subjects[/green] with [magenta]{permission}[/magenta] on [cyan]{object_type}:{object_id}[/cyan]"
        )
        console.print()

        table = Table(title=f"Subjects with '{permission}' permission")
        table.add_column("Subject Type", style="yellow")
        table.add_column("Subject ID", style="cyan")

        for subj_type, subj_id in sorted(subjects):
            table.add_row(subj_type, subj_id)

        console.print(table)

    except Exception as e:
        handle_error(e)


# Skills System Commands (v0.3.0)
@main.group(name="skills")
def skills() -> None:
    """Skills System - Manage reusable AI agent skills.

    The Skills System provides vendor-neutral skill management with:
    - SKILL.md format with YAML frontmatter
    - Three-tier hierarchy (agent > tenant > system)
    - Dependency resolution with DAG and cycle detection
    - Vendor-neutral export to .zip packages
    - Skill lifecycle management (create, fork, publish)
    - Usage analytics and governance

    Examples:
        nexus skills list
        nexus skills create my-skill --description "My custom skill"
        nexus skills fork analyze-code my-analyzer
        nexus skills publish my-skill
        nexus skills export my-skill --output ./my-skill.zip --format claude
    """
    pass


@skills.command(name="list")
@click.option("--tenant", is_flag=True, help="Show tenant-wide skills")
@click.option("--system", is_flag=True, help="Show system skills")
@click.option("--tier", type=click.Choice(["agent", "tenant", "system"]), help="Filter by tier")
@add_backend_options
def skills_list(
    tenant: bool,
    system: bool,
    tier: str | None,
    backend_config: BackendConfig,
) -> None:
    """List all skills.

    Examples:
        nexus skills list
        nexus skills list --tenant
        nexus skills list --system
        nexus skills list --tier agent
    """
    try:
        import asyncio

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)

        # Determine tier filter
        if tier:
            tier_filter = tier
        elif tenant:
            tier_filter = "tenant"
        elif system:
            tier_filter = "system"
        else:
            tier_filter = None

        registry = SkillRegistry(nx)

        async def list_skills_async() -> None:
            # Discover skills
            await registry.discover()

            # Get skills list with metadata
            skills_metadata_raw = registry.list_skills(tier=tier_filter, include_metadata=True)

            # Type hint the return value
            from nexus.skills.models import SkillMetadata

            skills_metadata: list[SkillMetadata] = skills_metadata_raw  # type: ignore[assignment]

            if not skills_metadata:
                console.print("[yellow]No skills found[/yellow]")
                return

            # Display skills in table
            table = Table(title=f"Skills ({len(skills_metadata)} found)")
            table.add_column("Name", style="cyan", no_wrap=False)
            table.add_column("Description", style="green")
            table.add_column("Version", style="yellow")
            table.add_column("Tier", style="magenta")

            for metadata in skills_metadata:
                table.add_row(
                    metadata.name,
                    metadata.description or "N/A",
                    metadata.version or "N/A",
                    metadata.tier or "N/A",
                )

            console.print(table)

        asyncio.run(list_skills_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="create")
@click.argument("name", type=str)
@click.option("--description", required=True, help="Skill description")
@click.option("--template", default="basic", help="Template to use (basic, data-analysis, etc.)")
@click.option(
    "--tier", type=click.Choice(["agent", "tenant", "system"]), default="agent", help="Target tier"
)
@click.option("--author", help="Author name")
@add_backend_options
def skills_create(
    name: str,
    description: str,
    template: str,
    tier: str,
    author: str | None,
    backend_config: BackendConfig,
) -> None:
    """Create a new skill from template.

    Examples:
        nexus skills create my-skill --description "My custom skill"
        nexus skills create data-viz --description "Data visualization" --template data-analysis
        nexus skills create analyzer --description "Code analyzer" --author Alice
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        # Get filesystem with permission enforcement disabled for skills operations
        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def create_skill_async() -> None:
            skill_path = await manager.create_skill(
                name=name,
                description=description,
                template=template,
                tier=tier,
                author=author,
            )

            console.print(f"[green]✓[/green] Created skill [cyan]{name}[/cyan]")
            console.print(f"  Path: [dim]{skill_path}[/dim]")
            console.print(f"  Tier: [yellow]{tier}[/yellow]")
            console.print(f"  Template: [yellow]{template}[/yellow]")

        asyncio.run(create_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="fork")
@click.argument("source_skill", type=str)
@click.argument("target_skill", type=str)
@click.option(
    "--tier", type=click.Choice(["agent", "tenant", "system"]), default="agent", help="Target tier"
)
@click.option("--author", help="Author name for the fork")
@add_backend_options
def skills_fork(
    source_skill: str,
    target_skill: str,
    tier: str,
    author: str | None,
    backend_config: BackendConfig,
) -> None:
    """Fork an existing skill.

    Examples:
        nexus skills fork analyze-code my-analyzer
        nexus skills fork data-analysis custom-analysis --author Bob
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def fork_skill_async() -> None:
            await registry.discover()

            forked_path = await manager.fork_skill(
                source_name=source_skill,
                target_name=target_skill,
                tier=tier,
                author=author,
            )

            console.print(
                f"[green]✓[/green] Forked skill [cyan]{source_skill}[/cyan] → [cyan]{target_skill}[/cyan]"
            )
            console.print(f"  Path: [dim]{forked_path}[/dim]")
            console.print(f"  Tier: [yellow]{tier}[/yellow]")

        asyncio.run(fork_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="publish")
@click.argument("skill_name", type=str)
@click.option(
    "--from-tier",
    type=click.Choice(["agent", "tenant", "system"]),
    default="agent",
    help="Source tier",
)
@click.option(
    "--to-tier",
    type=click.Choice(["agent", "tenant", "system"]),
    default="tenant",
    help="Target tier",
)
@add_backend_options
def skills_publish(
    skill_name: str,
    from_tier: str,
    to_tier: str,
    backend_config: BackendConfig,
) -> None:
    """Publish skill to tenant or system library.

    Examples:
        nexus skills publish my-skill
        nexus skills publish shared-skill --from-tier tenant --to-tier system
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def publish_skill_async() -> None:
            published_path = await manager.publish_skill(
                name=skill_name,
                source_tier=from_tier,
                target_tier=to_tier,
            )

            console.print(f"[green]✓[/green] Published skill [cyan]{skill_name}[/cyan]")
            console.print(f"  From: [yellow]{from_tier}[/yellow] → To: [yellow]{to_tier}[/yellow]")
            console.print(f"  Path: [dim]{published_path}[/dim]")

        asyncio.run(publish_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="search")
@click.argument("query", type=str)
@click.option("--tier", type=click.Choice(["agent", "tenant", "system"]), help="Filter by tier")
@click.option("--limit", default=10, type=int, help="Maximum results")
@add_backend_options
def skills_search(
    query: str,
    tier: str | None,
    limit: int,
    backend_config: BackendConfig,
) -> None:
    """Search skills by description.

    Examples:
        nexus skills search "data analysis"
        nexus skills search "code" --tier tenant --limit 5
    """
    try:
        import asyncio

        from nexus.skills import SkillManager, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        manager = SkillManager(nx, registry)

        async def search_skills_async() -> None:
            results = await manager.search_skills(query=query, tier=tier, limit=limit)

            if not results:
                console.print(f"[yellow]No skills match query:[/yellow] {query}")
                return

            console.print(
                f"[green]Found {len(results)} skills matching[/green] [cyan]{query}[/cyan]\n"
            )

            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Skill Name", style="cyan")
            table.add_column("Relevance Score", justify="right", style="yellow")

            for skill_name, score in results:
                table.add_row(skill_name, f"{score:.2f}")

            console.print(table)

        asyncio.run(search_skills_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="info")
@click.argument("skill_name", type=str)
@add_backend_options
def skills_info(
    skill_name: str,
    backend_config: BackendConfig,
) -> None:
    """Show detailed skill information.

    Examples:
        nexus skills info analyze-code
        nexus skills info data-analysis
    """
    try:
        import asyncio

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)

        async def show_info_async() -> None:
            await registry.discover()

            # Get metadata first
            metadata = registry.get_metadata(skill_name)

            # Load full skill to ensure it exists and cache it
            await registry.get_skill(skill_name)

            # Display skill information
            table = Table(title=f"Skill Information: {skill_name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Name", metadata.name)
            table.add_row("Description", metadata.description or "N/A")
            table.add_row("Version", metadata.version or "N/A")
            table.add_row("Author", metadata.author or "N/A")
            table.add_row("Tier", metadata.tier or "N/A")
            table.add_row("File Path", metadata.file_path or "N/A")

            if metadata.created_at:
                table.add_row("Created", metadata.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            if metadata.modified_at:
                table.add_row("Modified", metadata.modified_at.strftime("%Y-%m-%d %H:%M:%S"))

            # Show dependencies
            if metadata.requires:
                deps_str = ", ".join(metadata.requires)
                table.add_row("Dependencies", deps_str)

            console.print(table)

            # Show dependencies resolved
            if metadata.requires:
                console.print("\n[bold]Dependency Resolution:[/bold]")
                resolved = await registry.resolve_dependencies(skill_name)
                console.print(f"  Resolved order: [cyan]{' → '.join(resolved)}[/cyan]")

        asyncio.run(show_info_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="export")
@click.argument("skill_name", type=str)
@click.option("--output", "-o", type=click.Path(), required=True, help="Output .zip file path")
@click.option(
    "--format",
    type=click.Choice(["generic", "claude", "openai"]),
    default="generic",
    help="Export format",
)
@click.option("--no-deps", is_flag=True, help="Exclude dependencies from export")
@add_backend_options
def skills_export(
    skill_name: str,
    output: str,
    format: str,
    no_deps: bool,
    backend_config: BackendConfig,
) -> None:
    """Export skill to .zip package.

    Examples:
        nexus skills export my-skill --output ./my-skill.zip
        nexus skills export analyze-code --output ./export.zip --format claude
        nexus skills export my-skill --output ./export.zip --no-deps
    """
    try:
        import asyncio

        from nexus.skills import SkillExporter, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        exporter = SkillExporter(registry)

        async def export_skill_async() -> None:
            await registry.discover()

            include_deps = not no_deps

            with console.status(
                f"[yellow]Exporting skill {skill_name}...[/yellow]", spinner="dots"
            ):
                await exporter.export_skill(
                    name=skill_name,
                    output_path=output,
                    format=format,
                    include_dependencies=include_deps,
                )

            console.print(f"[green]✓[/green] Exported skill [cyan]{skill_name}[/cyan]")
            console.print(f"  Output: [cyan]{output}[/cyan]")
            console.print(f"  Format: [yellow]{format}[/yellow]")
            console.print(
                f"  Dependencies: [yellow]{'Included' if include_deps else 'Excluded'}[/yellow]"
            )

        asyncio.run(export_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="validate")
@click.argument("skill_name", type=str)
@click.option(
    "--format",
    type=click.Choice(["generic", "claude", "openai"]),
    default="generic",
    help="Validation format",
)
@add_backend_options
def skills_validate(
    skill_name: str,
    format: str,
    backend_config: BackendConfig,
) -> None:
    """Validate skill format and size limits.

    Examples:
        nexus skills validate my-skill
        nexus skills validate analyze-code --format claude
    """
    try:
        import asyncio

        from nexus.skills import SkillExporter, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        exporter = SkillExporter(registry)

        async def validate_skill_async() -> None:
            await registry.discover()

            valid, message, size_bytes = await exporter.validate_export(
                name=skill_name,
                format=format,
                include_dependencies=True,
            )

            def format_size(size: int) -> str:
                """Format size in human-readable format."""
                size_float = float(size)
                for unit in ["B", "KB", "MB", "GB"]:
                    if size_float < 1024.0:
                        return f"{size_float:.2f} {unit}"
                    size_float /= 1024.0
                return f"{size_float:.2f} TB"

            if valid:
                console.print(
                    f"[green]✓[/green] Skill [cyan]{skill_name}[/cyan] is valid for export"
                )
                console.print(f"  Format: [yellow]{format}[/yellow]")
                console.print(f"  Total size: [cyan]{format_size(size_bytes)}[/cyan]")
                console.print(f"  Message: [dim]{message}[/dim]")
            else:
                console.print(f"[red]✗[/red] Skill [cyan]{skill_name}[/cyan] validation failed")
                console.print(f"  Format: [yellow]{format}[/yellow]")
                console.print(f"  Total size: [cyan]{format_size(size_bytes)}[/cyan]")
                console.print(f"  Error: [red]{message}[/red]")
                sys.exit(1)

        asyncio.run(validate_skill_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="size")
@click.argument("skill_name", type=str)
@click.option("--human", "-h", is_flag=True, help="Human-readable output")
@add_backend_options
def skills_size(
    skill_name: str,
    human: bool,
    backend_config: BackendConfig,
) -> None:
    """Calculate total size of skill and dependencies.

    Examples:
        nexus skills size my-skill
        nexus skills size analyze-code --human
    """
    try:
        import asyncio

        from nexus.skills import SkillExporter, SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)
        exporter = SkillExporter(registry)

        async def calculate_size_async() -> None:
            await registry.discover()

            _, _, size_bytes = await exporter.validate_export(
                name=skill_name,
                format="generic",
                include_dependencies=True,
            )

            def format_size(size: int) -> str:
                """Format size in human-readable format."""
                if not human:
                    return f"{size:,} bytes"

                size_float = float(size)
                for unit in ["B", "KB", "MB", "GB"]:
                    if size_float < 1024.0:
                        return f"{size_float:.2f} {unit}"
                    size_float /= 1024.0
                return f"{size_float:.2f} TB"

            console.print(f"[bold cyan]Size of {skill_name} (with dependencies):[/bold cyan]")
            console.print(f"  Total size: [green]{format_size(size_bytes)}[/green]")

        asyncio.run(calculate_size_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="deps")
@click.argument("skill_name", type=str)
@click.option("--visual/--no-visual", default=True, help="Show visual tree (default: True)")
@add_backend_options
def skills_deps(
    skill_name: str,
    visual: bool,
    backend_config: BackendConfig,
) -> None:
    """Show skill dependencies as a visual tree.

    Examples:
        nexus skills deps my-skill
        nexus skills deps analyze-code --no-visual
    """
    try:
        import asyncio

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)

        async def show_deps_async() -> None:
            await registry.discover()

            # Get the skill to verify it exists
            skill = await registry.get_skill(skill_name)

            if visual:
                # Build visual dependency tree
                from rich.tree import Tree

                tree = Tree(f"[bold cyan]{skill_name}[/bold cyan]", guide_style="dim")

                async def add_dependencies(
                    parent_tree: Tree, skill_name: str, visited: set[str]
                ) -> None:
                    """Recursively add dependencies to tree."""
                    if skill_name in visited:
                        parent_tree.add(f"[dim]{skill_name} (circular reference)[/dim]")
                        return

                    visited.add(skill_name)

                    try:
                        skill_obj = await registry.get_skill(skill_name)
                        deps = skill_obj.metadata.requires or []

                        for dep in deps:
                            dep_metadata = registry.get_metadata(dep)
                            dep_desc = dep_metadata.description or "No description"

                            # Truncate description
                            if len(dep_desc) > 50:
                                dep_desc = dep_desc[:47] + "..."

                            dep_node = parent_tree.add(
                                f"[green]{dep}[/green] - [dim]{dep_desc}[/dim]"
                            )

                            # Recursively add dependencies
                            await add_dependencies(dep_node, dep, visited.copy())
                    except Exception as e:
                        parent_tree.add(f"[red]{skill_name} (error: {e})[/red]")

                # Add dependencies to the tree
                visited: set[str] = set()
                deps = skill.metadata.requires or []

                if not deps:
                    tree.add("[yellow]No dependencies[/yellow]")
                else:
                    for dep in deps:
                        dep_metadata = registry.get_metadata(dep)
                        dep_desc = dep_metadata.description or "No description"

                        if len(dep_desc) > 50:
                            dep_desc = dep_desc[:47] + "..."

                        dep_node = tree.add(f"[green]{dep}[/green] - [dim]{dep_desc}[/dim]")

                        # Recursively add sub-dependencies
                        await add_dependencies(dep_node, dep, visited.copy())

                console.print()
                console.print(tree)
                console.print()

                # Show total dependency count
                all_deps = await registry.resolve_dependencies(skill_name)
                total_deps = len(all_deps) - 1  # Exclude the skill itself
                console.print(f"[dim]Total dependencies: {total_deps}[/dim]")

            else:
                # Simple list format
                deps = await registry.resolve_dependencies(skill_name)

                console.print(f"\n[bold cyan]Dependencies for {skill_name}:[/bold cyan]")

                if len(deps) == 1:
                    console.print("  [yellow]No dependencies[/yellow]")
                else:
                    console.print("  [dim]Resolution order:[/dim]")
                    for i, dep in enumerate(deps):
                        if dep == skill_name:
                            console.print(f"  {i + 1}. [bold cyan]{dep}[/bold cyan] (self)")
                        else:
                            dep_metadata = registry.get_metadata(dep)
                            console.print(f"  {i + 1}. [green]{dep}[/green]")
                            if dep_metadata.description:
                                console.print(f"      [dim]{dep_metadata.description}[/dim]")

        asyncio.run(show_deps_async())
        nx.close()

    except Exception as e:
        handle_error(e)


@skills.command(name="diff")
@click.argument("skill1", type=str)
@click.argument("skill2", type=str)
@click.option("--context", "-c", default=3, type=int, help="Context lines (default: 3)")
@add_backend_options
def skills_diff(
    skill1: str,
    skill2: str,
    context: int,
    backend_config: BackendConfig,
) -> None:
    """Show differences between two skills.

    Examples:
        nexus skills diff my-skill-v1 my-skill-v2
        nexus skills diff analyze-code my-analyzer --context 5
    """
    try:
        import asyncio
        import difflib

        from rich.syntax import Syntax

        from nexus.skills import SkillRegistry

        nx = get_filesystem(backend_config, enforce_permissions=False)
        registry = SkillRegistry(nx)

        async def show_diff_async() -> None:
            await registry.discover()

            # Load both skills
            skill_obj1 = await registry.get_skill(skill1)
            skill_obj2 = await registry.get_skill(skill2)

            # Reconstruct SKILL.md content for both
            from nexus.skills.exporter import SkillExporter

            exporter = SkillExporter(registry)

            content1 = exporter._reconstruct_skill_md(skill_obj1)
            content2 = exporter._reconstruct_skill_md(skill_obj2)

            # Generate unified diff
            diff = difflib.unified_diff(
                content1.splitlines(keepends=True),
                content2.splitlines(keepends=True),
                fromfile=f"{skill1}/SKILL.md",
                tofile=f"{skill2}/SKILL.md",
                n=context,
            )

            diff_text = "".join(diff)

            if not diff_text:
                console.print(f"[yellow]No differences between {skill1} and {skill2}[/yellow]")
                return

            # Display diff with syntax highlighting
            console.print(f"\n[bold]Diff: {skill1} vs {skill2}[/bold]\n")

            # Use Syntax for colored diff output
            syntax = Syntax(
                diff_text,
                "diff",
                theme="monokai",
                line_numbers=True,
                word_wrap=False,
            )
            console.print(syntax)

            # Show summary statistics
            lines = diff_text.split("\n")
            additions = sum(
                1 for line in lines if line.startswith("+") and not line.startswith("+++")
            )
            deletions = sum(
                1 for line in lines if line.startswith("-") and not line.startswith("---")
            )

            console.print(
                f"\n[dim]Summary: [green]+{additions}[/green] additions, [red]-{deletions}[/red] deletions[/dim]"
            )

        asyncio.run(show_diff_async())
        nx.close()

    except Exception as e:
        handle_error(e)


# Version Tracking Commands (v0.3.5)
@main.group(name="versions")
def version_group() -> None:
    """Version Tracking - Manage file version history.

    CAS-backed version tracking for files and skills with full history.
    Every file write creates a new version, preserving all previous versions.

    Examples:
        nexus versions history /workspace/SKILL.md
        nexus versions diff /workspace/data.txt --v1 1 --v2 3
        nexus versions get /workspace/file.txt --version 2
        nexus versions rollback /workspace/file.txt --version 1
    """
    pass


@version_group.command(name="history")
@click.argument("path")
@click.option("--limit", type=int, default=None, help="Limit number of versions shown")
@add_backend_options
def version_history(path: str, limit: int | None, backend_config: BackendConfig) -> None:
    """Show version history for a file.

    Displays all versions of a file with metadata.

    Example:
        nexus version history /workspace/SKILL.md
        nexus version history /workspace/data.txt --limit 10
    """

    def format_size(size: int) -> str:
        """Format size in human-readable format."""
        size_float = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.1f} PB"

    try:
        nx = get_filesystem(backend_config)
        versions = nx.list_versions(path)

        if not versions:
            console.print(f"[yellow]No version history found for: {path}[/yellow]")
            nx.close()
            return

        # Apply limit
        if limit:
            versions = versions[:limit]

        # Display table
        table = Table(title=f"Version History: {path}")
        table.add_column("Version", style="cyan", justify="right")
        table.add_column("Size", style="green")
        table.add_column("Created At")
        table.add_column("Created By")
        table.add_column("Source", style="yellow")
        table.add_column("Change Reason")

        for v in versions:
            created_at = v["created_at"].strftime("%Y-%m-%d %H:%M:%S") if v["created_at"] else "N/A"
            size = format_size(v["size"])
            table.add_row(
                str(v["version"]),
                size,
                created_at,
                v.get("created_by") or "-",
                v.get("source_type") or "original",
                v.get("change_reason") or "-",
            )

        console.print(table)
        console.print(f"\n[dim]Total versions: {len(versions)}[/dim]")

        nx.close()

    except Exception as e:
        handle_error(e)


@version_group.command(name="get")
@click.argument("path")
@click.option("--version", "-v", type=int, required=True, help="Version number to retrieve")
@click.option("--output", "-o", help="Output file path (default: stdout)")
@add_backend_options
def version_get(path: str, version: int, output: str | None, backend_config: BackendConfig) -> None:
    """Get a specific version of a file.

    Retrieves content from a specific version.

    Example:
        nexus version get /workspace/file.txt --version 2
        nexus version get /workspace/file.txt -v 1 -o old_version.txt
    """
    try:
        nx = get_filesystem(backend_config)
        content = nx.get_version(path, version)

        if output:
            # Write to file
            Path(output).write_bytes(content)
            console.print(f"[green]✓[/green] Wrote version {version} to: {output}")
        else:
            # Print to stdout
            try:
                console.print(content.decode("utf-8"))
            except UnicodeDecodeError:
                console.print("[yellow]Binary content (cannot display)[/yellow]")
                console.print("[dim]Use --output to save to file[/dim]")

        nx.close()

    except Exception as e:
        handle_error(e)


@version_group.command(name="diff")
@click.argument("path")
@click.option("--v1", type=int, required=True, help="First version number")
@click.option("--v2", type=int, required=True, help="Second version number")
@click.option(
    "--mode", type=click.Choice(["metadata", "content"]), default="content", help="Diff mode"
)
@add_backend_options
def version_diff(path: str, v1: int, v2: int, mode: str, backend_config: BackendConfig) -> None:
    """Compare two versions of a file.

    Shows differences between two versions.

    Example:
        nexus version diff /workspace/file.txt --v1 1 --v2 3
        nexus version diff /workspace/file.txt --v1 1 --v2 2 --mode metadata
    """

    def format_size(size: int) -> str:
        """Format size in human-readable format."""
        size_float = float(abs(size))
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.1f} PB"

    try:
        nx = get_filesystem(backend_config)
        diff = nx.diff_versions(path, v1, v2, mode=mode)

        if mode == "metadata":
            # diff is a dict in metadata mode
            if not isinstance(diff, dict):
                console.print("[red]Error: Expected metadata dict from diff[/red]")
                nx.close()
                return

            # Display metadata diff as table
            table = Table(title=f"Metadata Diff: v{v1} vs v{v2}")
            table.add_column("Property")
            table.add_column(f"Version {v1}", style="cyan")
            table.add_column(f"Version {v2}", style="green")

            table.add_row(
                "Size",
                format_size(cast(int, diff.get("size_v1", 0))),
                format_size(cast(int, diff.get("size_v2", 0))),
            )
            table.add_row(
                "Size Delta",
                "",
                f"{'+' if cast(int, diff.get('size_delta', 0)) > 0 else ''}{format_size(abs(cast(int, diff.get('size_delta', 0))))}",
            )
            table.add_row(
                "Content Hash",
                str(diff.get("content_hash_v1", ""))[:16] + "...",
                str(diff.get("content_hash_v2", ""))[:16] + "...",
            )
            table.add_row(
                "Content Changed",
                "",
                "[green]Yes[/green]" if diff.get("content_changed") else "[dim]No[/dim]",
            )

            created_at_v1 = diff.get("created_at_v1")
            created_at_v2 = diff.get("created_at_v2")
            table.add_row(
                "Created At",
                created_at_v1.strftime("%Y-%m-%d %H:%M:%S") if created_at_v1 else "N/A",
                created_at_v2.strftime("%Y-%m-%d %H:%M:%S") if created_at_v2 else "N/A",
            )

            console.print(table)
        else:
            # Display content diff (diff is a string in content mode)
            console.print(str(diff))

        nx.close()

    except Exception as e:
        handle_error(e)


@version_group.command(name="rollback")
@click.argument("path")
@click.option("--version", "-v", type=int, required=True, help="Version to rollback to")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@add_backend_options
def version_rollback(path: str, version: int, yes: bool, backend_config: BackendConfig) -> None:
    """Rollback file to a previous version.

    Reverts file content to an older version.

    Example:
        nexus version rollback /workspace/file.txt --version 2
        nexus version rollback /workspace/file.txt -v 1 --yes
    """
    try:
        nx = get_filesystem(backend_config)

        # Get current version for confirmation
        # Check if file exists
        if not nx.exists(path):
            console.print(f"[red]File not found: {path}[/red]")
            nx.close()
            return

        # Get version history to determine current version
        versions = nx.list_versions(path)
        if not versions:
            console.print(f"[yellow]No version history found for: {path}[/yellow]")
            nx.close()
            return

        current_version = versions[0]["version"]  # First entry is the latest

        if not yes:
            confirmed = click.confirm(f"Rollback {path} from v{current_version} to v{version}?")
            if not confirmed:
                console.print("Cancelled")
                nx.close()
                return

        # Perform rollback
        nx.rollback(path, version)

        console.print(f"[green]✓[/green] Rolled back {path} to version {version}")
        console.print(f"[dim]New version: {current_version + 1}[/dim]")

        nx.close()

    except Exception as e:
        handle_error(e)


# Plugin System Commands (v0.3.5)
@main.group(name="plugins")
def plugins() -> None:
    """Plugin System - Manage Nexus plugins.

    The Plugin System allows extending Nexus with external integrations
    while maintaining vendor neutrality:
    - Entry point-based plugin discovery
    - Custom CLI commands via `nexus <plugin> <command>`
    - Lifecycle hooks (before_write, after_read, etc.)
    - Per-plugin configuration
    - Enable/disable plugins dynamically

    Examples:
        nexus plugins list
        nexus plugins info anthropic
        nexus plugins install anthropic
        nexus plugins enable anthropic
        nexus plugins disable anthropic
        nexus plugins uninstall anthropic
    """
    pass


@plugins.command(name="list")
def plugins_list() -> None:
    """List all installed plugins."""
    try:
        from nexus.plugins.registry import PluginRegistry

        registry = PluginRegistry()
        plugin_names = registry.discover()

        if not plugin_names:
            console.print("[yellow]No plugins installed.[/yellow]")
            console.print("\nInstall plugins with: [cyan]pip install nexus-plugin-<name>[/cyan]")
            return

        table = Table(title="Installed Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Description")
        table.add_column("Status", style="yellow")

        for plugin_name in plugin_names:
            plugin = registry.get_plugin(plugin_name)
            if plugin:
                metadata = plugin.metadata()
                status = "✓ Enabled" if plugin.is_enabled() else "✗ Disabled"
                table.add_row(metadata.name, metadata.version, metadata.description, status)

        console.print(table)

    except Exception as e:
        handle_error(e)


@plugins.command(name="info")
@click.argument("plugin_name")
def plugins_info(plugin_name: str) -> None:
    """Show detailed information about a plugin."""
    try:
        from nexus.plugins.registry import PluginRegistry

        registry = PluginRegistry()
        registry.discover()

        plugin = registry.get_plugin(plugin_name)
        if not plugin:
            console.print(f"[red]Plugin '{plugin_name}' not found.[/red]")
            return

        metadata = plugin.metadata()

        console.print(f"\n[bold cyan]{metadata.name}[/bold cyan] v{metadata.version}")
        console.print(f"{metadata.description}\n")
        console.print(f"[bold]Author:[/bold] {metadata.author}")

        if metadata.homepage:
            console.print(f"[bold]Homepage:[/bold] {metadata.homepage}")

        if metadata.requires:
            console.print(f"[bold]Dependencies:[/bold] {', '.join(metadata.requires)}")

        # Show commands
        commands = plugin.commands()
        if commands:
            console.print("\n[bold]Commands:[/bold]")
            for cmd_name in commands:
                console.print(f"  • nexus {plugin_name} {cmd_name}")

        # Show hooks
        hooks = plugin.hooks()
        if hooks:
            console.print("\n[bold]Hooks:[/bold]")
            for hook_name in hooks:
                console.print(f"  • {hook_name}")

        status = "✓ Enabled" if plugin.is_enabled() else "✗ Disabled"
        console.print(f"\n[bold]Status:[/bold] {status}")

    except Exception as e:
        handle_error(e)


@plugins.command(name="enable")
@click.argument("plugin_name")
def plugins_enable(plugin_name: str) -> None:
    """Enable a plugin."""
    try:
        from nexus.plugins.registry import PluginRegistry

        registry = PluginRegistry()
        registry.discover()

        plugin = registry.get_plugin(plugin_name)
        if not plugin:
            console.print(f"[red]Plugin '{plugin_name}' not found.[/red]")
            return

        if plugin.is_enabled():
            console.print(f"[yellow]Plugin '{plugin_name}' is already enabled.[/yellow]")
            return

        registry.enable_plugin(plugin_name)
        console.print(f"[green]✓ Enabled plugin '{plugin_name}'[/green]")

    except Exception as e:
        handle_error(e)


@plugins.command(name="disable")
@click.argument("plugin_name")
def plugins_disable(plugin_name: str) -> None:
    """Disable a plugin."""
    try:
        from nexus.plugins.registry import PluginRegistry

        registry = PluginRegistry()
        registry.discover()

        plugin = registry.get_plugin(plugin_name)
        if not plugin:
            console.print(f"[red]Plugin '{plugin_name}' not found.[/red]")
            return

        if not plugin.is_enabled():
            console.print(f"[yellow]Plugin '{plugin_name}' is already disabled.[/yellow]")
            return

        registry.disable_plugin(plugin_name)
        console.print(f"[green]✓ Disabled plugin '{plugin_name}'[/green]")

    except Exception as e:
        handle_error(e)


@plugins.command(name="install")
@click.argument("plugin_name")
def plugins_install(plugin_name: str) -> None:
    """Install a plugin from PyPI.

    Example: nexus plugins install anthropic
    This will run: pip install nexus-plugin-anthropic
    """
    import subprocess

    # Convert short name to full package name
    package_name = plugin_name
    if not package_name.startswith("nexus-plugin-"):
        package_name = f"nexus-plugin-{plugin_name}"

    console.print(f"Installing {package_name}...")

    try:
        subprocess.check_call(
            ["pip", "install", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        console.print(f"[green]✓ Successfully installed {package_name}[/green]")
        console.print("\nRun [cyan]'nexus plugins list'[/cyan] to see the installed plugin")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Failed to install {package_name}[/red]")
        console.print(f"Error: {e.stderr.decode() if e.stderr else str(e)}")


@plugins.command(name="uninstall")
@click.argument("plugin_name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def plugins_uninstall(plugin_name: str, yes: bool) -> None:
    """Uninstall a plugin.

    Example: nexus plugins uninstall anthropic
    """
    import subprocess

    # Convert short name to full package name
    package_name = plugin_name
    if not package_name.startswith("nexus-plugin-"):
        package_name = f"nexus-plugin-{plugin_name}"

    if not yes:
        confirmed = click.confirm(f"Uninstall {package_name}?")
        if not confirmed:
            console.print("Cancelled")
            return

    console.print(f"Uninstalling {package_name}...")

    try:
        subprocess.check_call(
            ["pip", "uninstall", "-y", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        console.print(f"[green]✓ Successfully uninstalled {package_name}[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Failed to uninstall {package_name}[/red]")
        console.print(f"Error: {e.stderr.decode() if e.stderr else str(e)}")


# Dynamic plugin command registration
def _register_plugin_commands() -> None:
    """Dynamically register plugin commands at CLI initialization."""
    try:
        import asyncio
        import inspect

        from nexus.plugins.registry import PluginRegistry

        # Discover plugins without NexusFS (for metadata only)
        registry = PluginRegistry()
        plugin_names = registry.discover()

        for plugin_name in plugin_names:
            plugin = registry.get_plugin(plugin_name)
            if not plugin or not plugin.is_enabled():
                continue

            # Get plugin commands
            commands = plugin.commands()
            if not commands:
                continue

            # Get plugin class for later instantiation
            import importlib.metadata

            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, "select"):
                nexus_plugins = entry_points.select(group="nexus.plugins")
            else:
                result = entry_points.get("nexus.plugins")
                nexus_plugins = cast(Any, result if result else [])

            plugin_class = None
            for ep in nexus_plugins:
                if ep.name == plugin_name:
                    plugin_class = ep.load()
                    break

            if not plugin_class:
                continue

            # Create a Click group for this plugin
            @click.group(name=plugin_name)
            def plugin_group() -> None:
                """Plugin commands."""
                pass

            # Update the docstring with plugin description
            metadata = plugin.metadata()
            plugin_group.__doc__ = (
                f"{metadata.description}\n\nPlugin: {metadata.name} v{metadata.version}"
            )

            # Add each command to the plugin group
            for cmd_name, cmd_func in commands.items():
                # Create a wrapper that handles async commands with NexusFS
                def make_command(func: Any, name: str, _p_class: Any, p_name: str) -> Any:
                    # Preserve the original function's signature
                    sig = inspect.signature(func)
                    params: list[Any] = []

                    for param_name, param in sig.parameters.items():
                        if param_name == "self":
                            continue

                        # Create Click option/argument based on parameter
                        if param.default == inspect.Parameter.empty:
                            # Required argument
                            params.append(click.Argument([param_name]))
                        else:
                            # Optional option
                            option_name = f"--{param_name.replace('_', '-')}"
                            params.append(
                                click.Option(
                                    [option_name],
                                    default=param.default,
                                    help=f"{param_name} parameter",
                                )
                            )

                    @click.command(name=name, params=params)
                    @click.pass_context
                    def wrapper(_ctx: Any, **kwargs: Any) -> None:
                        """Execute plugin command."""
                        nx = None
                        try:
                            # Initialize NexusFS for commands that need it
                            from nexus import connect
                            from nexus.plugins.registry import PluginRegistry

                            nx = connect()

                            # Re-instantiate plugin with NexusFS
                            plugin_registry = PluginRegistry(nx)  # type: ignore[arg-type]
                            plugin_registry.discover()
                            plugin_instance = plugin_registry.get_plugin(p_name)

                            if not plugin_instance:
                                console.print(f"[red]Plugin '{p_name}' not found[/red]")
                                return

                            # Get the command method from the plugin instance
                            cmd_method = plugin_instance.commands().get(name)
                            if not cmd_method:
                                console.print(f"[red]Command '{name}' not found[/red]")
                                return

                            # Handle async functions
                            if inspect.iscoroutinefunction(cmd_method):
                                asyncio.run(cmd_method(**kwargs))
                            else:
                                cmd_method(**kwargs)

                        except Exception as e:
                            handle_error(e)
                        finally:
                            # Clean up NexusFS connection
                            if nx:
                                with contextlib.suppress(BaseException):
                                    nx.close()

                    # Preserve docstring
                    wrapper.__doc__ = func.__doc__ or f"{name} command"
                    return wrapper

                cmd = make_command(cmd_func, cmd_name, plugin_class, plugin_name)
                plugin_group.add_command(cmd)

            # Add the plugin group to main CLI
            main.add_command(plugin_group)

    except Exception as e:
        # Silently fail if plugin system is not available
        # This allows the CLI to work even if plugins are broken
        import logging

        logging.debug(f"Failed to register plugin commands: {e}")


# Register plugin commands at module load time
_register_plugin_commands()


if __name__ == "__main__":
    main()
