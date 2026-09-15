"""Tests for the optional Atlas Cloud LLM provider."""

from unittest.mock import patch

import pytest

from src.llm.atlascloud import AtlasCloudChatOpenAI, AtlasCloudProvider
from src.llm.factory import ProviderFactory


def test_factory_creates_atlascloud_provider() -> None:
    """The factory maps "atlascloud" to the Atlas Cloud provider and model class."""
    provider = ProviderFactory().create_provider("atlascloud")

    assert isinstance(provider, AtlasCloudProvider)
    assert provider.get_model_class() is AtlasCloudChatOpenAI


def test_atlascloud_model_uses_compatible_endpoint_with_default_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The model targets Atlas Cloud and keeps ChatOpenAI's default retry policy."""
    monkeypatch.setenv("ATLASCLOUD_API_KEY", "test-key")

    with patch("src.llm.atlascloud.ChatOpenAI.__init__", return_value=None) as init:
        AtlasCloudChatOpenAI(model="openai/gpt-5.4", temperature=1.0)

    init.assert_called_once_with(
        api_key="test-key",
        model="openai/gpt-5.4",
        temperature=1.0,
        base_url="https://api.atlascloud.ai/v1",
    )


def test_atlascloud_model_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing ATLASCLOUD_API_KEY raises instead of silently using another key."""
    monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ATLASCLOUD_API_KEY"):
        AtlasCloudChatOpenAI(model="openai/gpt-5.4")
