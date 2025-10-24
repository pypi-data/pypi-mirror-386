"""psql-ai: Natural language to SQL converter for PostgreSQL.
"""

__version__ = "0.3.0"

# Import main functionality for convenience
from .config import Config
from .database import gather_context
from .llm import generate_postgresql_response, needs_documentation_context
from .main import main
from .sql_utils import is_mutating

__all__ = [
    "main",
    "Config",
    "gather_context",
    "generate_postgresql_response",
    "needs_documentation_context",
    "is_mutating",
]
