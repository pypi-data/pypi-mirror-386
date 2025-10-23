"""Command-line interface for Groundhog.

This module implements the `hog` CLI tool for running Python scripts on
Globus Compute endpoints. It handles script execution, harness invocation,
Python version validation, and error reporting.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from packaging.specifiers import SpecifierSet
from packaging.version import Version

import groundhog_hpc
from groundhog_hpc.compute import pre_register_shell_function
from groundhog_hpc.errors import RemoteExecutionError
from groundhog_hpc.function import Function
from groundhog_hpc.harness import Harness
from groundhog_hpc.pep723 import (
    Pep723Metadata,
    insert_or_update_metadata,
    read_pep723,
    write_pep723,
)
from groundhog_hpc.utils import get_groundhog_version_spec

app = typer.Typer()


def _check_and_update_metadata(script_path: Path, contents: str) -> str:
    """Check for missing/incomplete PEP 723 metadata and offer to update.

    Args:
        script_path: Path to the script file
        contents: Current script contents

    Returns:
        Updated script contents (or original if no update made)
    """
    metadata_dict = read_pep723(contents)

    # Check if metadata is missing or incomplete
    needs_update = False
    if metadata_dict is None:
        # No metadata block at all
        needs_update = True
        typer.echo(
            "\nWarning: Script does not contain PEP 723 metadata block.", err=True
        )
    else:
        # Check if expected fields are present
        missing_fields = []
        if "requires-python" not in metadata_dict:
            missing_fields.append("requires-python")
        if "dependencies" not in metadata_dict:
            missing_fields.append("dependencies")

        if missing_fields:
            needs_update = True
            typer.echo(
                f"\nWarning: Script metadata is missing fields: {', '.join(missing_fields)}",
                err=True,
            )

    if not needs_update:
        return contents

    # Create metadata with defaults
    if metadata_dict is None:
        metadata = Pep723Metadata()
    else:
        # Preserve existing metadata, fill in defaults for missing fields
        metadata = Pep723Metadata.model_validate(metadata_dict)

    # Show proposed metadata
    typer.echo("\nProposed metadata block:", err=True)
    typer.echo(write_pep723(metadata), err=True)
    typer.echo()

    # Prompt user
    if typer.confirm("Would you like to update the script with this metadata?"):
        updated_contents = insert_or_update_metadata(contents, metadata)
        script_path.write_text(updated_contents)
        typer.echo(f"✓ Updated {script_path}", err=True)
        typer.echo()
        return updated_contents
    else:
        typer.echo("Continuing without updating metadata...\n", err=True)
        return contents


@app.command(no_args_is_help=True)
def run(
    script: Path = typer.Argument(
        ..., help="Path to script with PEP 723 dependencies to deploy to the endpoint"
    ),
    harness: str = typer.Argument(
        "main", help="Name of harness function to invoke from script (default 'main')"
    ),
    no_fun_allowed: bool = typer.Option(
        False,
        "--no-fun-allowed",
        help="Suppress emoji output\n\n[env: GROUNDHOG_NO_FUN_ALLOWED=]",
    ),
) -> None:
    """Run a Python script on a Globus Compute endpoint."""
    if no_fun_allowed:
        os.environ["GROUNDHOG_NO_FUN_ALLOWED"] = str(no_fun_allowed)

    script_path = script.resolve()
    if not script_path.exists():
        typer.echo(f"Error: Script '{script_path}' not found", err=True)
        raise typer.Exit(1)
    else:
        # used by Function to build callable
        os.environ["GROUNDHOG_SCRIPT_PATH"] = str(script_path)

    contents = script_path.read_text()

    # Check for missing/incomplete metadata and offer to update
    contents = _check_and_update_metadata(script_path, contents)

    metadata = read_pep723(contents)
    if metadata and "requires-python" in metadata:
        requires_python = metadata["requires-python"]
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        if not _python_version_matches(current_version, requires_python):
            groundhog_spec = get_groundhog_version_spec()
            uv_cmd = (
                f"uv run --with {groundhog_spec} "
                f"--python {requires_python} "
                f"hog run {script_path} {harness}"
            )

            typer.echo(
                f"Warning: Script requires Python {requires_python}, "
                f"but current version is {current_version}. This may "
                "cause issues with serialization.",
                err=True,
            )
            typer.echo(
                f"\nTo run with matching Python version, use:\n  {uv_cmd}",
                err=True,
            )

    try:
        # Execute in the actual __main__ module so that classes defined in the script
        # can be properly pickled (pickle requires classes to be importable from their
        # __module__, and for __main__.ClassName to work it must be in sys.modules["__main__"])
        import __main__

        exec(contents, __main__.__dict__, __main__.__dict__)

        if harness not in __main__.__dict__:
            typer.echo(f"Error: Function '{harness}' not found in script")
            raise typer.Exit(1)
        elif not isinstance(__main__.__dict__[harness], Harness):
            typer.echo(
                f"Error: Function '{harness}' must be decorated with `@hog.harness`",
            )
            raise typer.Exit(1)

        # signal to harness obj that invocation is allowed
        os.environ[f"GROUNDHOG_RUN_{harness}".upper()] = str(True)
        result = __main__.__dict__[harness]()
        typer.echo(result)
    except RemoteExecutionError as e:
        typer.echo(f"Remote execution failed (exit code {e.returncode}):", err=True)
        typer.echo(e.stderr, err=True)
        raise typer.Exit(1)
    except Exception as e:
        if not isinstance(e, RemoteExecutionError):
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(no_args_is_help=True, hidden=True)
def register(
    script: Path = typer.Argument(
        ...,
        help="Python script with decorated functions to pre-register with Globus Compute.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Print detailed information about registered functions",
    ),
) -> None:
    """Register all @hog.function decorated functions in a script and print their UUIDs."""

    script_path = script.resolve()
    if not script_path.exists():
        typer.echo(f"Error: Script '{script_path}' not found", err=True)
        raise typer.Exit(1)

    # Set script path for Function instances
    os.environ["GROUNDHOG_SCRIPT_PATH"] = str(script_path)

    contents = script_path.read_text()

    try:
        # Execute in a temporary module namespace
        import __main__

        exec(contents, __main__.__dict__, __main__.__dict__)

        # Find all Function instances
        functions_found = []
        for name, obj in __main__.__dict__.items():
            if isinstance(obj, Function):
                functions_found.append((name, obj))

        if not functions_found:
            typer.echo("No @hog.function decorated functions found in script", err=True)
            raise typer.Exit(1)

        # Register each function
        typer.echo(f"Registering {len(functions_found)} function(s)...")

        for name, func in functions_found:
            function_id = pre_register_shell_function(
                str(script_path), name, walltime=func.walltime
            )
            typer.echo(f"{name}: {function_id}")

            if verbose:
                from pprint import pprint

                import globus_compute_sdk as gc

                client = gc.Client()

                func_info = client.get_function(function_id)
                pprint(func_info)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def _python_version_matches(current: str, spec: str) -> bool:
    """Check if current Python version satisfies the PEP 440 version specifier.

    Args:
        current: Current Python version string (e.g., "3.11.5")
        spec: PEP 440 version specifier (e.g., ">=3.11")

    Returns:
        True if current version matches the specifier, False otherwise
    """
    return Version(current) in SpecifierSet(spec)


def _version_callback(show: bool) -> None:
    """Typer callback to display version and exit.

    Args:
        show: Boolean flag set by --version option
    """
    if show:
        typer.echo(f"{groundhog_hpc.__version__}")
        raise typer.Exit()


@app.callback(no_args_is_help=True)
def main_info(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True
    ),
) -> None:
    f"""
    Hello, Groundhog {"☀️🦫🕳️" if not os.environ.get("GROUNDHOG_NO_FUN_ALLOWED") else ""}
    """
    pass
