import re
from typing import Set

MUTATING_KEYWORDS: Set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "MERGE",
    "REPLACE",
    "GRANT",
    "REVOKE",
}



def is_mutating(sql_statement: str) -> bool:
    """Check if SQL statement modifies data or schema.

    Returns True for INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, etc.
    Returns False for SELECT, SHOW, EXPLAIN, etc.
    """
    if not sql_statement.strip():
        return False

    # Remove comments and normalize whitespace
    cleaned = re.sub(r"--.*$", "", sql_statement, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Check first meaningful word
    words = cleaned.split()
    if not words:
        return False

    first_word = words[0].upper()
    return first_word in MUTATING_KEYWORDS


