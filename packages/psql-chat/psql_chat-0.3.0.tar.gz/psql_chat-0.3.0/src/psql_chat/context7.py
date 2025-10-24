"""Context7 integration for PostgreSQL documentation retrieval."""

import urllib.parse
import urllib.request
from typing import Optional


class Context7Error(Exception):
    """Context7 operation error."""

    pass


def fetch_context7_docs(topic: str, max_chars: int = 8000) -> Optional[str]:
    """Fetch PostgreSQL documentation from Context7.

    Args:
        topic: The PostgreSQL topic to search for
        max_chars: Maximum number of characters to retrieve

    Returns:
        Documentation text or None if fetch fails
    """
    try:
        # URL encode the topic
        encoded_topic = urllib.parse.quote(topic)
        url = f"https://context7.com/websites/postgresql/llms.txt?topic={encoded_topic}"

        # Make the request
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.getcode() == 200:
                content = response.read().decode("utf-8")

                # Truncate if too long
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n[... truncated for length ...]"

                return content
            else:
                return None

    except Exception:
        # Silently fail - we'll continue without context
        return None
