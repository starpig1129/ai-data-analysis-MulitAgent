"""Tests for MCPManager connection setup."""

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest

from src.core.mcp_manager import MCPManager


class _StopConnect(Exception):
    """Raised by the fake transport to end connect() right after stderr setup."""


def test_connect_falls_back_to_stderr_when_log_file_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If logs/mcp_servers.log cannot be created, server stderr goes to sys.stderr."""
    config_path = tmp_path / "mcp.yaml"
    config_path.write_text(
        "servers:\n  demo:\n    command: echo\n    args: []\n", encoding="utf-8"
    )
    manager = MCPManager(config_path=config_path)
    received_errlog: list[Any] = []

    def fail_makedirs(*args: Any, **kwargs: Any) -> None:
        raise PermissionError("logs directory is read-only")

    def fake_stdio_client(server_params: Any, errlog: Any) -> Any:
        received_errlog.append(errlog)
        raise _StopConnect

    monkeypatch.setattr("src.core.mcp_manager.os.makedirs", fail_makedirs)
    monkeypatch.setattr("mcp.client.stdio.stdio_client", fake_stdio_client)

    connected = asyncio.run(manager.connect("demo"))

    assert connected is False
    assert received_errlog == [sys.stderr]
