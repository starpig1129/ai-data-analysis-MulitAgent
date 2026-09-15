from __future__ import annotations

import os
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from .base import BaseProvider

# OrcaRouter is an OpenAI-compatible AI gateway. Model IDs follow the
# "orcarouter/<model>" namespace (e.g. orcarouter/fusion-mini).
ORCAROUTER_BASE_URL = "https://api.orcarouter.ai/v1"


class OrcaRouterChatOpenAI(ChatOpenAI):
    """ChatOpenAI preconfigured for the OrcaRouter gateway."""

    def __init__(self, **kwargs: Any) -> None:
        """Initializes the client with OrcaRouter credentials and endpoint.

        Args:
            **kwargs: ChatOpenAI keyword arguments from the agent model config.
                An explicit ``api_key`` or ``base_url`` overrides the defaults.

        Raises:
            ValueError: If no API key is passed and ``ORCAROUTER_API_KEY`` is
                unset. Passing ``api_key=None`` through would make the OpenAI
                SDK fall back to ``OPENAI_API_KEY`` and send it to OrcaRouter.
        """
        api_key = kwargs.pop("api_key", None) or os.getenv("ORCAROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "ORCAROUTER_API_KEY is required for the OrcaRouter provider"
            )

        kwargs.setdefault("base_url", ORCAROUTER_BASE_URL)
        super().__init__(api_key=SecretStr(api_key), **kwargs)


class OrcaRouterProvider(BaseProvider):
    """Provider for OrcaRouter models."""

    def get_model_class(self) -> type:
        """Returns the OrcaRouterChatOpenAI class."""
        return OrcaRouterChatOpenAI
