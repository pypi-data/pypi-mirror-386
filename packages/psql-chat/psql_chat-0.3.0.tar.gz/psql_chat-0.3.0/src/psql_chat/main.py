"""Command line entry point for psql-chat implemented with Typer."""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

from psql_chat.context7 import Context7Error, fetch_context7_docs
from psql_chat.database import DatabaseError, explain_sql, gather_context, run_with_psql
from psql_chat.llm import (
    correct_sql_command,
    generate_postgresql_response,
    needs_documentation_context,
)
from psql_chat.rich_formatting import format_explanation_with_syntax
from psql_chat.sql_utils import is_mutating

from .config import Config

VERSION = "0.2.0"

console = Console()
console_err = Console(stderr=True)


def abort(message: str, exit_code: int = 1) -> None:
    """Print an error message and terminate the CLI."""
    console_err.print(f"[red]Error: {message}[/]")
    raise typer.Exit(exit_code)

def confirm(message: str, default: str = "y") -> bool:
    """Prompt user for yes/no confirmation.

    Args:
        message: The confirmation message to display
        default: Default response ('y' or 'n')

    Returns:
        True if user confirms, False otherwise
    """
    valid_yes = {"y", "yes", "true", "1"}
    valid_no = {"n", "no", "false", "0"}

    prompt_suffix = f" [{'Y/n' if default.lower() == 'y' else 'y/N'}]: "

    while True:
        try:
            response = input(message + prompt_suffix).strip().lower()

            if not response:  # Empty input, use default
                return default.lower() in valid_yes

            if response in valid_yes:
                return True
            elif response in valid_no:
                return False
            else:
                print(
                    "Please respond with 'y' or 'n' (or 'yes' or 'no').",
                    file=sys.stderr,
                )

        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.", file=sys.stderr)
            return False



def clean_input(text: str) -> str:
    """Normalize the natural-language request."""
    if not text:
        return ""

    text = text.strip()
    if text.startswith("\"") and text.endswith("\""):
        text = text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]

    return text.strip()


def empty_context() -> Dict[str, Any]:
    """Return a new, empty database context stub."""
    return {"tables": [], "columns": []}


def version_callback(value: bool) -> None:
    """Display the CLI version when requested."""
    if value:
        console.print(f"psql-chat {VERSION}")
        raise typer.Exit()


def load_database_context(dsn: Optional[str], skip: bool, verbose: bool) -> Dict[str, Any]:
    """Gather database schema context unless the user opts out."""
    console_err.print("[cyan]Connecting to database...[/]")

    if skip:
        console_err.print("[cyan]Skipping context gathering (--no-context)[/]")
        return empty_context()

    try:
        context, mode = gather_context(dsn)
        table_count = len(context.get("tables", []))
        label = "psql environment" if mode == "psql" else mode
        console_err.print(f"[green]✓ Connected to: {label} ({table_count} tables)[/]")

        if verbose:
            import json

            console_err.print("\n[cyan]📋 Database Context (Verbose):[/]")
            console_err.print(json.dumps(context, indent=2, default=str))
            console_err.print()

        return context
    except Exception as exc:  # gather_context provides richer detail for logging
        fallback = empty_context()
        console_err.print(f"[yellow]![/] Context gathering failed: {exc}")
        if verbose:
            console_err.print("\n[red]📋 Database Context Error (Verbose):[/]")
            console_err.print(f"Error: {exc}")
            console_err.print(f"Fallback context: {fallback}")
            console_err.print()
        return fallback


def maybe_fetch_docs(
    request: str, context: Dict[str, Any], skip_docs: bool
) -> Optional[str]:
    """Fetch Context7 documentation when it helps the response."""
    if skip_docs:
        console_err.print("[cyan]Documentation context disabled[/]")
        return None

    try:
        console_err.print("[cyan]Analyzing request for documentation needs...[/]")
        if not needs_documentation_context(request, context):
            console_err.print("[cyan]Using standard response (no docs needed)[/]")
            return None

        console_err.print(f"[cyan]Fetching PostgreSQL docs for: {request}[/]")
        docs_context = fetch_context7_docs(request)
        if docs_context:
            console_err.print(
                f"[green]✓ Retrieved documentation context ({len(docs_context)} chars)[/]"
            )
        else:
            console_err.print("[yellow]No relevant docs found[/]")
        return docs_context
    except Exception as exc:
        console_err.print(f"[yellow]![/] Context7 integration failed: {exc}")
        return None


def validate_sql(
    request: str,
    command: str,
    command_type: str,
    context: Dict[str, Any],
    connection_info: Dict[str, str],
    docs_context: Optional[str],
    dsn: Optional[str],
) -> str:
    """Validate SQL using EXPLAIN and attempt corrections via the LLM."""
    if command_type != "sql" or not command:
        return command

    max_attempts = 5
    attempt = 1

    while attempt <= max_attempts:
        console_err.print(
            f"[cyan]Validating SQL (attempt {attempt}/{max_attempts})...[/]"
        )
        success, explain_result = explain_sql(command, dsn)

        if success:
            console_err.print("[green]SQL validation passed[/]")
            return command

        console_err.print(f"[yellow]SQL validation failed: {explain_result}[/]")

        if attempt >= max_attempts:
            console_err.print("[red]Maximum correction attempts reached[/]")
            return command

        console_err.print("[cyan]Attempting to correct SQL...[/]")
        try:
            command, _, _, command_type = correct_sql_command(
                request,
                command,
                explain_result,
                context,
                connection_info,
                docs_context,
            )
            console_err.print("[green]SQL corrected, re-validating...[/]")
            if command_type != "sql":
                # The correction switched to a non-SQL command, so stop validation.
                return command
        except Exception as exc:
            console_err.print(f"[red]Failed to correct SQL: {exc}[/]")
            return command

        attempt += 1

    return command


def run_cli(
    request: str,
    dsn: Optional[str],
    no_context: bool,
    execute: bool,
    no_docs: bool,
    verbose: bool,
) -> None:
    """Execute the core CLI workflow."""
    config = Config.from_environment()
    if not config.openai_api_key:
        abort("OPENAI_API_KEY environment variable is required")

    nl_request = clean_input(request)
    if not nl_request:
        abort("Empty request provided")

    dsn_value = dsn or os.getenv("DB_URI")
    if not dsn_value and not any(
        os.getenv(var) for var in ("PGHOST", "PGDATABASE", "PGUSER")
    ):
        console_err.print(
            "[yellow]Warning: No --dsn, DB_URI, or PostgreSQL environment variables provided.[/]"
        )

    context = load_database_context(dsn_value, no_context, verbose)

    connection_info = {
        "PGHOST": os.getenv("PGHOST", "localhost"),
        "PGPORT": os.getenv("PGPORT", "5432"),
        "PGDATABASE": os.getenv("PGDATABASE", "unknown"),
        "PGUSER": os.getenv("PGUSER", "unknown"),
    }

    docs_context = maybe_fetch_docs(nl_request, context, no_docs)

    command: str = ""
    explanation: str = ""
    explanation_only: bool = False
    command_type: str = ""
    try:
        command, explanation, explanation_only, command_type = (
            generate_postgresql_response(
                nl_request,
                context,
                connection_info,
                docs_context,
            )
        )
    except Exception as exc:
        console_err.print(f"[yellow]![/] Structured generation failed: {exc}")
        abort(f"Failed to generate response: {exc}")

    console.print(f"command_type: {command_type}")

    command = validate_sql(
        nl_request,
        command,
        command_type,
        context,
        connection_info,
        docs_context,
        dsn_value,
    )

    if explanation_only:
        format_explanation_with_syntax(explanation, console)
        raise typer.Exit(0)

    format_explanation_with_syntax(f"{explanation}", console)
    console.print()

    if command_type == "sql":
        console.print(Syntax(command, "sql", theme="monokai", line_numbers=False))
    elif command_type == "bash":
        console.print(Syntax(command, "bash", theme="monokai", line_numbers=False))
    else:
        console.print(command)
    console.print()

    if not execute:
        raise typer.Exit(0)

    try:
        if command_type == "sql" and is_mutating(command):
            console_err.print(
                "[bright_red]WARNING: This will modify your database![/]"
            )

        if confirm("Execute this command?", default="y"):
            if command_type in {"sql", "bash"}:
                console_err.print(
                    f"[cyan]Executing {command_type.upper()} command...[/]"
                )
                exit_code = run_with_psql(command, dsn_value)
                if exit_code == 0:
                    console_err.print("[green]✓ Command executed successfully.[/]")
                else:
                    console_err.print(
                        f"[red]✗ Command failed with exit code {exit_code}.[/]"
                    )
                    raise typer.Exit(exit_code)
            else:
                console_err.print(
                    "[yellow]Please execute this shell command manually in your terminal.[/]"
                )
        else:
            console_err.print("[yellow]Command execution cancelled.[/]")
    except (KeyboardInterrupt, EOFError):
        console_err.print("[yellow]\nCommand execution cancelled.[/]")


def cli(
    request: str = typer.Argument(..., help="Natural language request to convert."),
    dsn: Optional[str] = typer.Option(
        None,
        "--dsn",
        metavar="CONNECTION_STRING",
        help="PostgreSQL connection URI (postgresql://user:pass@host:port/db)",
    ),
    no_context: bool = typer.Option(
        False, "--no-context", help="Skip database context gathering."
    ),
    execute: bool = typer.Option(
        False,
        "-e",
        "--execute",
        help="Execute the generated command after confirmation.",
    ),
    no_docs: bool = typer.Option(
        False, "--no-docs", help="Skip Context7 documentation retrieval."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed database context and debugging information.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_flag=True,
        is_eager=True,
        help="Show the psql-chat version and exit.",
    ),
) -> None:
    del version  # Handled by version_callback

    try:
        run_cli(request, dsn, no_context, execute, no_docs, verbose)
    except Context7Error as exc:
        abort(f"Context7 integration error: {exc}")
    except DatabaseError as exc:
        abort(f"Database error: {exc}")
    except KeyboardInterrupt:
        console_err.print("\nOperation cancelled by user.")
        raise typer.Exit(1)
    except typer.Exit:
        # Exit already handled; just re-raise.
        raise
    except Exception as exc:  # Fallback for unexpected issues
        abort(f"Unexpected error: {exc}")


def main() -> None:
    """Entry point for console_scripts."""
    typer.run(cli)


if __name__ == "__main__":
    main()

