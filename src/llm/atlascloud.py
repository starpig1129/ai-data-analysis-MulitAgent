from __future__ import annotations

import os
from typing import Any, Type

from langchain_openai import ChatOpenAI

from .base import BaseProvider

DEFAULT_BASE_URL = "https://api.atlascloud.ai/v1"


class ChatAtlasCloud(ChatOpenAI):
    """ChatOpenAI pointed at the Atlas Cloud gateway.

    Atlas Cloud speaks the OpenAI chat-completions format, so the transport is
    unchanged; only the defaults differ. The base URL falls back to
    ``ATLASCLOUD_BASE_URL`` then to the public gateway, and the key to
    ``ATLASCLOUD_API_KEY``, so an agent entry needs nothing but
    ``provider: atlascloud`` and a model name. Anything passed in
    ``model_config`` still wins.
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("base_url", os.getenv("ATLASCLOUD_BASE_URL", DEFAULT_BASE_URL))
        if not kwargs.get("api_key"):
            api_key = os.getenv("ATLASCLOUD_API_KEY")
            if api_key:
                kwargs["api_key"] = api_key
        super().__init__(**kwargs)


class AtlasCloudProvider(BaseProvider):
    """Provider for Atlas Cloud models."""

    def get_model_class(self) -> Type:
        """Returns the ChatAtlasCloud class."""
        return ChatAtlasCloud
