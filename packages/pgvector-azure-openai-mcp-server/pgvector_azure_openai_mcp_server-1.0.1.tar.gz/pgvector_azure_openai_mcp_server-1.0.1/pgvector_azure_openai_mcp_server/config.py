"""Simplified configuration management for pgvector MCP server."""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Simplified application settings - only essential configuration required from MCP client environment."""

    def __init__(self):
        # Essential configuration - must be provided by MCP client environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Please configure it in your MCP client environment (e.g., Claude Desktop)."
            )
        self.database_url: str = database_url

        azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not azure_openai_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT environment variable is required. "
                "Please configure your Azure OpenAI endpoint in your MCP client environment."
            )
        self.azure_openai_endpoint: str = azure_openai_endpoint

        azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not azure_openai_api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY environment variable is required. "
                "Please configure your Azure OpenAI API key in your MCP client environment."
            )
        self.azure_openai_api_key: str = azure_openai_api_key

        self.azure_openai_model: str = os.getenv("AZURE_OPENAI_MODEL", "text-embedding-3-small")

        # Optional configuration with sensible defaults
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
