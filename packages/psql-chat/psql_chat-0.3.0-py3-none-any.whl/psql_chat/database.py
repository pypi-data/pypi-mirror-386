import subprocess
import sys
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import psycopg2
from psycopg2 import extensions
from psycopg2.extras import RealDictCursor


class DatabaseError(Exception):
    """Database operation error."""

    pass


def gather_context(dsn: Optional[str]) -> Tuple[Dict[str, Any], str]:
    """Gather database schema context for SQL generation.

    Args:
        dsn: Database connection string, or None to use PostgreSQL environment variables

    Returns:
        Tuple of (context_dict, source_mode)
    """
    # If no DSN provided, try to use PostgreSQL environment variables
    if not dsn:
        # Check if PostgreSQL environment variables are available
        import os

        pg_vars = {
            "PGHOST": os.getenv("PGHOST"),
            "PGPORT": os.getenv("PGPORT"),
            "PGDATABASE": os.getenv("PGDATABASE"),
            "PGUSER": os.getenv("PGUSER"),
            "PGPASSWORD": os.getenv("PGPASSWORD"),
        }

        # If we have at least database info, try to construct a DSN or use environment variables directly
        if pg_vars["PGDATABASE"] or any(pg_vars.values()):
            # Try connecting using environment variables (psycopg2 supports this)
            try:
                # psycopg2.connect() without arguments uses PostgreSQL environment variables
                with psycopg2.connect() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        tables_with_columns = _get_table_info(cur)
                        context = {
                            "tables": [
                                {
                                    "schema_name": t["schema_name"],
                                    "table_name": t["table_name"],
                                    "owner": t["owner"],
                                }
                                for t in tables_with_columns
                            ],
                            "columns": _flatten_columns(tables_with_columns),
                            "views": _get_view_info(cur),
                            "functions": _get_function_info(cur),
                            "database_name": pg_vars.get("PGDATABASE", "unknown"),
                        }
                        return context, "env_vars"
            except psycopg2.Error as e:
                # Fall back to psql-based context gathering with environment variables
                try:
                    return _gather_context_via_psql(None), "psql_env_fallback"
                except Exception as fallback_error:
                    return {
                        "error": f"Database connection failed: {e}. Fallback also failed: {fallback_error}",
                        "tables": [],
                        "views": [],
                        "functions": [],
                    }, "error"
        else:
            return {"error": "No database connection provided"}, "none"

    try:
        # Try to connect and get schema info
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                tables_with_columns = _get_table_info(cur)
                context = {
                    "tables": [
                        {
                            "schema_name": t["schema_name"],
                            "table_name": t["table_name"],
                            "owner": t["owner"],
                        }
                        for t in tables_with_columns
                    ],
                    "columns": _flatten_columns(tables_with_columns),
                    "views": _get_view_info(cur),
                    "functions": _get_function_info(cur),
                    "database_name": _get_database_name(dsn),
                }
                return context, "direct_connection"

    except psycopg2.Error as e:
        # Fall back to psql-based context gathering
        try:
            return _gather_context_via_psql(dsn), "psql_fallback"
        except Exception as fallback_error:
            return {
                "error": f"Database connection failed: {e}. Fallback also failed: {fallback_error}",
                "tables": [],
                "views": [],
                "functions": [],
            }, "error"


def explain_sql(sql: str, dsn: Optional[str]) -> Tuple[bool, str]:
    """Get execution plan for SQL statement.

    Args:
        sql: SQL statement to explain
        dsn: Database connection string, or None to use PostgreSQL environment variables

    Returns:
        Tuple of (success, explanation_text)
    """
    explain_query = f"EXPLAIN (ANALYZE false, VERBOSE true, BUFFERS false) {sql}"

    try:
        if dsn:
            # Use provided DSN
            with psycopg2.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(explain_query)
                    rows = cur.fetchall()
                    return True, "\n".join(row[0] for row in rows)
        else:
            # Try using environment variables like gather_context does
            import os

            pg_vars = {
                "PGHOST": os.getenv("PGHOST"),
                "PGPORT": os.getenv("PGPORT"),
                "PGDATABASE": os.getenv("PGDATABASE"),
                "PGUSER": os.getenv("PGUSER"),
                "PGPASSWORD": os.getenv("PGPASSWORD"),
            }

            if pg_vars["PGDATABASE"] or any(pg_vars.values()):
                # psycopg2.connect() without arguments uses PostgreSQL environment variables
                with psycopg2.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute(explain_query)
                        rows = cur.fetchall()
                        return True, "\n".join(row[0] for row in rows)
            else:
                return False, "No database connection available for EXPLAIN"

    except psycopg2.Error as e:
        return False, f"EXPLAIN failed: {e}"


def run_with_psql(sql: str, dsn: Optional[str]) -> int:
    """Execute SQL using psql command-line tool.

    Args:
        sql: SQL statement to execute
        dsn: Database connection string

    Returns:
        Exit code from psql
    """
    cmd = ["psql"]

    if dsn:
        cmd.append(dsn)

    cmd.extend(["-c", sql])

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode

    except FileNotFoundError:
        print(
            "Error: psql command not found. Please ensure PostgreSQL client is installed.",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Error running psql: {e}", file=sys.stderr)
        return 1


def _get_table_info(cursor) -> list:
    """Get information about tables in the database."""
    cursor.execute(
        """
        SELECT
            schemaname,
            tablename,
            tableowner
        FROM pg_tables
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename;
    """
    )

    tables = cursor.fetchall()

    # Get column info for each table
    result = []
    for table in tables:
        schema = table["schemaname"]
        name = table["tablename"]

        cursor.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """,
            (schema, name),
        )

        columns = cursor.fetchall()

        result.append(
            {
                "schema_name": schema,
                "table_name": name,
                "owner": table["tableowner"],
                "columns": [dict(col) for col in columns],
            }
        )

    return result


def _flatten_columns(tables_with_columns) -> list:
    """Flatten column information from tables into a flat list."""
    columns = []
    for table in tables_with_columns:
        schema_name = table["schema_name"]
        table_name = table["table_name"]
        for col in table["columns"]:
            column_info = dict(col)
            column_info["schema_name"] = schema_name
            column_info["table_name"] = table_name
            columns.append(column_info)
    return columns


def _get_view_info(cursor) -> list:
    """Get information about views in the database."""
    cursor.execute(
        """
        SELECT
            schemaname,
            viewname,
            viewowner
        FROM pg_views
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, viewname;
    """
    )

    return [dict(row) for row in cursor.fetchall()]


def _get_function_info(cursor) -> list:
    """Get information about functions in the database."""
    cursor.execute(
        """
        SELECT
            n.nspname as schema,
            p.proname as name,
            pg_get_function_result(p.oid) as result_type
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY n.nspname, p.proname;
    """
    )

    return [dict(row) for row in cursor.fetchall()]


def _get_database_name(dsn: str) -> str:
    """Extract database name from connection string."""
    try:
        parsed = extensions.parse_dsn(dsn)
        db_name = parsed.get("dbname")
        if db_name:
            return db_name
    except (psycopg2.ProgrammingError, psycopg2.InterfaceError, ValueError):
        pass

    try:
        parsed_uri = urlparse(dsn)
        return parsed_uri.path.lstrip("/") if parsed_uri.path else "unknown"
    except Exception:
        return "unknown"


def _gather_context_via_psql(dsn: Optional[str]) -> Dict[str, Any]:
    """Fallback method to gather context using psql command."""
    cmd = ["psql"]

    # Add DSN if provided, otherwise psql will use environment variables
    if dsn:
        cmd.append(dsn)

    cmd.extend(
        [
            "-At",
            "-c",
            "SELECT schemaname, tablename, tableowner FROM pg_tables WHERE schemaname NOT IN ('information_schema', 'pg_catalog') ORDER BY schemaname, tablename;",
        ]
    )

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        tables = []
        for line in result.stdout.splitlines():
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 3:
                continue
            schema_name, table_name, owner = parts
            tables.append(
                {
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "owner": owner or "unknown",
                }
            )

        import os

        database_name = (
            _get_database_name(dsn)
            if dsn
            else os.getenv("PGDATABASE")
            or "unknown"
        )

        return {
            "tables": tables,
            "columns": [],
            "views": [],
            "functions": [],
            "database_name": database_name,
        }

    except subprocess.CalledProcessError as e:
        raise DatabaseError(f"Failed to gather context via psql: {e}")
