import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration settings for the application."""

    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    db_uri: Optional[str] = None


    @classmethod
    def from_environment(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            db_uri=os.getenv("DB_URI"),
        )

