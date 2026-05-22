from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv(override=True)


def get_model():
    provider = os.environ.get("MODEL_PROVIDER", "azure_openai")

    if provider == "azure_openai":
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.azure import AzureProvider

        return OpenAIModel(
            os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            provider=AzureProvider(
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.environ.get("AZURE_OPENAI_API_VERSION") or None,
            ),
        )

    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    raise ValueError(f"Unknown MODEL_PROVIDER {provider!r}. Use 'azure_openai' or 'anthropic'.")
