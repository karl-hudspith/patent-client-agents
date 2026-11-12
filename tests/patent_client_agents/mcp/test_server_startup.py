from __future__ import annotations

from unittest.mock import Mock

import pytest

pytest.importorskip("fastmcp")
server = pytest.importorskip("patent_client_agents.mcp.server")


def test_http_transport_requires_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "_auth", None)

    with pytest.raises(SystemExit, match="2"):
        server.main(["--transport", "http"])


@pytest.mark.parametrize("transport", ["stdio", "http"])
def test_configured_server_runs_requested_transport(
    monkeypatch: pytest.MonkeyPatch, transport: str
) -> None:
    mcp = Mock()
    monkeypatch.setattr(server, "mcp", mcp)
    monkeypatch.setattr(server, "_auth", object())

    server.main(["--transport", transport])

    mcp.run.assert_called_once_with(transport=transport)


def test_stdio_transport_does_not_require_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mcp = Mock()
    monkeypatch.setattr(server, "mcp", mcp)
    monkeypatch.setattr(server, "_auth", None)

    server.main()

    mcp.run.assert_called_once_with(transport="stdio")
