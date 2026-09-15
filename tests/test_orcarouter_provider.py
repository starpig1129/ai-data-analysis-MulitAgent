"""Tests for the optional OrcaRouter LLM provider."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.llm.factory import ProviderFactory
from src.llm.orcarouter import OrcaRouterChatOpenAI, OrcaRouterProvider


def test_factory_creates_orcarouter_provider() -> None:
    """The factory maps "orcarouter" to the OrcaRouter provider and model class."""
    provider = ProviderFactory().create_provider("orcarouter")

    assert isinstance(provider, OrcaRouterProvider)
    assert provider.get_model_class() is OrcaRouterChatOpenAI


def test_orcarouter_model_uses_gateway_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The model sends ORCAROUTER_API_KEY to the OrcaRouter endpoint."""
    monkeypatch.setenv("ORCAROUTER_API_KEY", "test-key")

    with patch("src.llm.orcarouter.ChatOpenAI.__init__", return_value=None) as init:
        OrcaRouterChatOpenAI(model="orcarouter/fusion-mini", temperature=1.0)

    init.assert_called_once_with(
        api_key="test-key",
        model="orcarouter/fusion-mini",
        temperature=1.0,
        base_url="https://api.orcarouter.ai/v1",
    )


def test_orcarouter_model_requires_its_own_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing ORCAROUTER_API_KEY raises instead of falling back to OPENAI_API_KEY.

    Without this guard the OpenAI SDK reads OPENAI_API_KEY and would send the
    user's OpenAI key to the third-party OrcaRouter endpoint.
    """
    monkeypatch.delenv("ORCAROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key-must-not-leak")

    with pytest.raises(ValueError, match="ORCAROUTER_API_KEY"):
        OrcaRouterChatOpenAI(model="orcarouter/fusion-mini")
