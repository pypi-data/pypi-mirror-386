from typing import Any, Dict, Optional

import openai
from openai import OpenAI
from pydantic import BaseModel, Field

from .config import Config


class LLMError(Exception):
    """LLM operation error."""

    pass


class PostgreSQLResponse(BaseModel):
    """Structured response model for PostgreSQL queries and explanations."""

    explanation: str = Field(
        description="Clear, detailed explanation of the PostgreSQL command or concept"
    )
    command: Optional[str] = Field(
        default=None,
        description="The exact PostgreSQL command to run, or null if explanation-only",
    )
    command_type: str = Field(
        description="Type of command: 'sql' for SQL queries, 'bash' for psql meta-commands, 'NONE' for explanation-only"
    )
    warnings: Optional[str] = Field(
        default=None,
        description="Safety warnings or important considerations, or null if none",
    )


class DocumentationNeed(BaseModel):
    """Model for determining if PostgreSQL documentation is needed."""

    needs_context: bool = Field(
        description="True if PostgreSQL documentation context is needed for this request"
    )
    search_topic: Optional[str] = Field(
        default=None,
        description="Specific PostgreSQL topic to search for, or null if no context needed",
    )


def needs_documentation_context(nl_request: str, context: dict) -> bool:
    """Determine if PostgreSQL documentation context is needed for the request.

    Args:
        nl_request: The user's natural language request
        context: Database context (not used currently but kept for compatibility)

    Returns:
        True if documentation context is needed, False otherwise
    """
    config = Config.from_environment()
    client = OpenAI(api_key=config.openai_api_key)

    system_prompt = """You are a PostgreSQL expert assistant. Determine if a user's request requires additional PostgreSQL documentation context beyond basic SQL knowledge.

Examples of requests that NEED context:
- Questions about PostgreSQL-specific features (JSONB, arrays, window functions, CTEs, etc.)
- Performance optimization questions
- Advanced configuration or administration tasks
- PostgreSQL-specific functions or operators
- Backup/restore procedures
- Replication, partitioning, or other advanced topics

Examples of requests that DON'T NEED context:
- Basic SELECT/INSERT/UPDATE/DELETE queries
- Simple table creation
- Basic JOIN operations
- Standard SQL operations that work the same across databases

Be conservative - if in doubt, request context."""

    try:
        response = client.beta.chat.completions.parse(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"User request: {nl_request}\n\nDoes this request need PostgreSQL documentation context?",
                },
            ],
            response_format=DocumentationNeed,
        )

        if response.choices and response.choices[0].message.parsed:
            return response.choices[0].message.parsed.needs_context
        return False

    except Exception:
        # If we can't determine, err on the side of not fetching context
        return False


def generate_postgresql_response(
    nl_request: str,
    context: dict,
    connection_info: dict | None = None,
    docs_context: str | None = None,
) -> tuple[str, str, bool, str]:
    """Generate structured PostgreSQL response using OpenAI's structured outputs.

    Args:
        nl_request: Natural language request
        context: Database context dictionary
        connection_info: PostgreSQL connection information
        docs_context: Optional PostgreSQL documentation context

    Returns:
        Tuple of (command, explanation, is_explanation_only, command_type)
    """
    config = Config.from_environment()
    client = OpenAI(api_key=config.openai_api_key)

    # Build system prompt
    system_prompt = """You are an expert PostgreSQL assistant that helps users with database operations.

You are being called from within a psql session. The user is already connected to PostgreSQL with full database schema context.

Handle these types of requests:
1. **Data queries** ("show me...", "find all...", "get records...", "list users...") - set command_type to "sql" and provide executable SELECT query
2. **Schema queries** ("show tables", "describe table", "list columns") - set command_type to "bash" for meta-commands like \\dt, \\d
3. **General PSQL Commands** ("connect to database", "change user", "set search path") - set command_type to "bash"
4. **Data modifications** (INSERT, UPDATE, DELETE) - set command_type to "sql"
5. **DDL operations** (CREATE, ALTER, DROP) - set command_type to "sql"
6. **Administrative tasks** (BACKUP, RESTORE, VACUUM) - set command_type to "sql"
7. **Educational/conceptual questions only** ("what is a primary key?", "explain ACID properties") - set command_type to "NONE"

CRITICAL RULES:
- If user wants to see data from tables, ALWAYS provide executable SQL (command_type = "sql")
- If user asks about schema structure, use psql meta-commands (command_type = "bash")
- Only use command_type = "NONE" for pure educational questions that don't involve the user's specific database
- Use the provided database schema context to generate accurate table/column names

For SQL commands:
- Generate complete, executable SELECT statements using actual table/column names from the schema
- Use proper JOINs based on foreign key relationships visible in the schema
- Include WHERE clauses if the user specifies conditions
- Always end SQL with semicolon
- Set command_type to "sql"

For psql commands:
- Use standard psql meta-commands
- Include any relevant SQL commands as needed.
- Set command_type to "bash"

For explanations:
- Keep explanations brief and focused on the specific query being generated
- Use **bold** and *italic* markdown formatting for emphasis
- Set command_type to "NONE"

Make sure to only set command_type to sql if you are providing an actual functioning SQL command that can be run against the user's database. Otherwise, use bash or NONE as appropriate.

"""


    # Format database context
    db_context_str = _format_context_for_prompt(context)

    # Build connection info string
    conn_str = ""
    if connection_info:
        conn_str = f"""Current psql session context:
- Database: {connection_info.get("PGDATABASE", "current database")}
- Host: {connection_info.get("PGHOST", "localhost")}
- Port: {connection_info.get("PGPORT", "5432")}
- User: {connection_info.get("PGUSER", "current user")}

"""

    # Build user prompt
    user_prompt = f"""{conn_str}Database Schema Context:
{db_context_str}"""

    if docs_context:
        user_prompt += f"""

PostgreSQL Documentation Context:
{docs_context}"""

    user_prompt += f"""

User Request: {nl_request}

Provide the appropriate PostgreSQL command or detailed explanation."""

    try:
        response = client.beta.chat.completions.parse(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=PostgreSQLResponse,
        )
        if not response.choices or not response.choices[0].message.parsed:
            raise LLMError("Failed to get structured response from OpenAI")

        result = response.choices[0].message.parsed

        # Build final explanation with warnings if present
        final_explanation = result.explanation
        if result.warnings:
            final_explanation += f"\n\n⚠️  **Warning:** {result.warnings}"

        # Determine if explanation only based on command_type
        is_explanation_only = result.command_type == "NONE"

        return (
            result.command or "",
            final_explanation,
            is_explanation_only,
            result.command_type,
        )

    except openai.AuthenticationError:
        raise LLMError("Invalid OpenAI API key")
    except openai.RateLimitError:
        raise LLMError("OpenAI API rate limit exceeded")
    except openai.APIConnectionError:
        raise LLMError("Failed to connect to OpenAI API")
    except openai.APIError as e:
        raise LLMError(f"OpenAI API error: {e}")
    except Exception as e:
        raise LLMError(f"Unexpected error calling OpenAI API: {e}")


def correct_sql_command(
    original_request: str,
    failed_sql: str,
    error_message: str,
    context: dict,
    connection_info: dict | None = None,
    docs_context: str | None = None,
) -> tuple[str, str, bool, str]:
    """Correct a failed SQL command based on error feedback.

    Args:
        original_request: Original natural language request
        failed_sql: The SQL command that failed
        error_message: Error message from EXPLAIN
        context: Database context dictionary
        connection_info: PostgreSQL connection information
        docs_context: Optional PostgreSQL documentation context

    Returns:
        Tuple of (command, explanation, is_explanation_only, command_type)
    """
    config = Config.from_environment()
    client = OpenAI(api_key=config.openai_api_key)

    # Build correction prompt
    system_prompt = """You are an expert PostgreSQL assistant fixing SQL errors.

The user requested data, you generated SQL, but it failed validation. Your job is to fix the SQL command.

CRITICAL:
- Always return command_type = "sql" for corrected commands
- Generate working SQL that addresses the original user request
- Fix syntax errors, wrong table/column names, and logical issues
- Use the provided database schema context to ensure correct names"""

    # Format database context
    db_context_str = _format_context_for_prompt(context)

    # Build connection info string
    conn_str = ""
    if connection_info:
        conn_str = f"""Current psql session context:
- Database: {connection_info.get("PGDATABASE", "current database")}
- Host: {connection_info.get("PGHOST", "localhost")}
- Port: {connection_info.get("PGPORT", "5432")}
- User: {connection_info.get("PGUSER", "current user")}

"""

    user_prompt = f"""{conn_str}Database Schema Context:
{db_context_str}

Original User Request: {original_request}

Failed SQL Command:
{failed_sql}

Error Message:
{error_message}

Please fix the SQL command to fulfill the original user request."""

    try:
        response = client.beta.chat.completions.parse(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=PostgreSQLResponse,
        )

        if not response.choices or not response.choices[0].message.parsed:
            raise LLMError("Failed to get structured correction response from OpenAI")

        result = response.choices[0].message.parsed

        # Build final explanation with warnings if present
        final_explanation = f"**Corrected SQL:** {result.explanation}"
        if result.warnings:
            final_explanation += f"\n\n⚠️  **Warning:** {result.warnings}"

        return result.command or "", final_explanation, False, "sql"

    except Exception as e:
        raise LLMError(f"Failed to correct SQL: {e}")


def _format_context_for_prompt(context: Dict[str, Any]) -> str:
    """Format database context for inclusion in prompt.

    Args:
        context: Database context dictionary

    Returns:
        Formatted context string
    """
    if "error" in context:
        return f"Error gathering context: {context['error']}\n\nPlease generate SQL based on standard PostgreSQL syntax."

    # Simply return the full context as JSON for the LLM to parse
    import json

    try:
        return json.dumps(context, indent=2, default=str)
    except Exception as e:
        return f"Error formatting context: {e}\n\nPlease generate SQL based on standard PostgreSQL syntax."
