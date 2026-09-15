from __future__ import annotations

import os
from typing import Any

from langchain_openai import ChatOpenAI

from .base import BaseProvider


class AtlasCloudChatOpenAI(ChatOpenAI):
    """ChatOpenAI client configured for Atlas Cloud's compatible API."""

    def __init__(self, **kwargs: Any) -> None:
        """Initializes the client with Atlas Cloud credentials and endpoint.

        Args:
            **kwargs: ChatOpenAI keyword arguments from the agent model config.
                An explicit ``api_key`` or ``base_url`` overrides the defaults.

        Raises:
            ValueError: If no API key is passed and ``ATLASCLOUD_API_KEY`` is
                unset.
        """
        api_key = kwargs.pop("api_key", None) or os.getenv("ATLASCLOUD_API_KEY")
        if not api_key:
            raise ValueError(
                "ATLASCLOUD_API_KEY is required for the Atlas Cloud provider"
            )

        kwargs.setdefault("base_url", "https://api.atlascloud.ai/v1")
        super().__init__(api_key=api_key, **kwargs)


class AtlasCloudProvider(BaseProvider):
    """Provider for models exposed by Atlas Cloud."""

    def get_model_class(self) -> type[Any]:
        """Returns the Atlas Cloud ChatOpenAI class."""
        return AtlasCloudChatOpenAI
