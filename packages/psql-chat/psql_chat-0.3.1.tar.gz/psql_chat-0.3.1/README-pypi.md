# psql-chat

psql-chat lets you ask your PostgreSQL database questions in natural language. The tool translates your request into SQL or `psql` shell commands, gives you a syntax-highlighted explanation, and can optionally execute the command after confirmation.

## Features

- **Natural language to SQL** – Converts plain-language prompts into PostgreSQL commands.
- **Database-aware** – Gathers schema context automatically (tables, columns, relationships) unless disabled with `--no-context`.
- **Documentation lookup** – Fetches relevant PostgreSQL docs on demand through Context7.
- **Safety first** – Warns when a query will modify data and asks for confirmation before executing.
- **Rich terminal output** – Uses Rich for colored, syntax-highlighted explanations.
- **Flexible usage** – Explain-only (default), execute with `--execute`, or skip docs with `--no-docs` for faster responses.

## Quick Start

```
uvx psql-chat "how do I list all users?"
uvx psql-chat --dsn "postgresql://user:pass@host:5432/db" "show top 10 customers"
uvx psql-chat "delete inactive users" --execute  # confirmation required
```

You can also call it from inside `psql`:

```
\! psql-chat "count orders by month"
\! psql-chat --no-docs "list tables"
```

## Requirements

- Python 3.11+
- A PostgreSQL connection (either via environment variables/`.pgpass` or `--dsn`)
- An OpenAI API key available as the `OPENAI_API_KEY` environment variable
- `uv` package manager (for `uvx`) or another way to install/run the package

## Installation

```
uv pip install psql-chat
```

On Windows the repository includes a `setup.ps1` helper script that installs dependencies and configures a shell alias so `psql-chat` is available in `psql`.

## Usage Options

```
psql-chat [OPTIONS] "your request"

Options:
  --dsn TEXT          PostgreSQL connection URI.
  --no-context        Skip schema discovery for faster responses.
  --no-docs           Skip fetching PostgreSQL documentation.
  -e, --execute       Execute the generated command after confirmation.
  --verbose           Show gathered schema context for debugging.
  --version           Show the program version and exit.
```

## License

This project is released under the PostgreSQL License (MIT-style).
