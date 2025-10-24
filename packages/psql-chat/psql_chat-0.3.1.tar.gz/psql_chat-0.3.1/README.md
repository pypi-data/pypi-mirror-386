# psql-chat - Natives NL-to-SQL

PostgreSQL has been one of the most popular open source databases for years. However, learning how to query data with SQL is a hurdle for many users.
The AI tool “psql-chat” makes it possible to ask the database questions in natural language. The chatbot then suggests an SQL query or a psql command. After approval, the command can be executed or the prompt can be adjusted. 

This makes database administrators more efficient, while users can perform data analyses without in-depth SQL knowledge

![psql-chat flow diagram](resources/flow-diagram.png)

## Quick Start 

### Windows

1. **Run setup:** `.\setup.ps1` 
2. **Set API key:** `$env:OPENAI_API_KEY = "your-key"`
3. **Configure pgpass:** (optional but recommended) Add the connection details to your `pgpass` file for passwordless access.
4. **Use from psql:** `\! psql-chat "show me all tables"`

## Usage

**From psql (recommended):**
```sql
\! psql-chat "find users who haven't logged in recently"
\! psql-chat "count orders by month" -e               -- execute immediately (after confirmation)
\! psql-chat "explain JSONB indexing strategies"      -- gets docs automatically
```
Note: These usage examples assume `psql-chat` is in your PATH. This is done automatically by the setup script. Otherwise use `uvx psql-chat ...` after installation.


## How It Works

1. Converts natural language to PostgreSQL commands
2. Analyzes database schema for context
3. Fetches PostgreSQL docs automatically when needed
4. Shows syntax-highlighted SQL with explanation
5. Optional execution with safety warnings

## Features

- **Smart context** - Uses your database schema
- **Auto documentation** - Fetches PostgreSQL docs via Context7
- **Safety first** - Warns before data modifications  
- **Rich formatting** - Syntax highlighting and explanations
- **Flexible modes** - Explain-only (default) or execute with `--execute`
- **Fast option** - Skip docs with `--no-docs`

## Options

- `--execute, -e` - Execute the command (default: explain only)
- `--dsn` - Database connection string
- `--no-context` - Skip database schema gathering
- `--no-docs` - Skip PostgreSQL documentation
- `--version, -v` - Show version

## Requirements

- OpenAI API key (set `OPENAI_API_KEY`)
- PostgreSQL connection (via psql environment or `--dsn`)
- uv package manager (auto-installed by setup script)
