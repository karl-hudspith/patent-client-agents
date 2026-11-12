"""Standalone patent-client-agents MCP server entry point.

Run via the ``patent-client-agents-mcp`` console script (installed by the ``[mcp]``
extra of the ``patent-client-agents`` distribution), or directly::

    python -m patent_client_agents.mcp.server

Stdio is the default transport. Use ``--transport http`` for HTTP mode;
HTTP mode requires authentication to be configured.

Auth is env-driven via ``mcp_data_core.mcp.auth.make_auth``. For stdio
and local development, leave the auth env vars unset and the server
runs without authentication. For HTTP deployments, set
``LAW_TOOLS_CORE_PUBLIC_URL`` plus the Google OAuth or static bearer
env vars described in :mod:`mcp_data_core.mcp.auth`. The command-line
entry point refuses to start HTTP mode unless ``make_auth()`` returns
an authentication provider.

Hosted/multi-instance deployments that need persistent OAuth/DCR
client state (Firestore-backed storage, rate limiting, etc.) belong in
a separate deploy package (see ``patent-mcp-deploy``) that builds its
own server from the same ``build_server`` + ``ip_mcp`` building blocks.

Note on naming: the PyPI distribution is ``patent-client-agents``; the import module
stays ``patent_client_agents`` (PyYAML/yaml, scikit-learn/sklearn style decoupling).
"""

from __future__ import annotations

import argparse
import sys

from patent_client_agents import __version__

_mcp_import_error: ModuleNotFoundError | None = None

try:
    from mcp_data_core.mcp import make_auth
    from mcp_data_core.mcp.server_factory import build_server

    from . import ip_mcp
except ModuleNotFoundError as exc:
    if exc.name != "fastmcp":
        raise
    _mcp_import_error = exc
    mcp = None
else:
    _auth = make_auth()
    mcp = build_server(
        name="patent-client-agents",
        instructions=(
            "Patent and IP data connectors: USPTO (ODP, PPUBS, Assignments, "
            "Office Actions, PTAB, Petitions, Bulk Data, TSDR, Trademark "
            "Assignments), EPO OPS, Google Patents, CPC, MPEP, TMEP, CanLII "
            "(Canadian courts, tribunals, and IP statutes), and WIPO Lex "
            "(global IP statute / treaty / judgment database)."
        ),
        auth=_auth,
    )
    mcp.mount(ip_mcp)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``patent-client-agents-mcp`` console script.

    No args ⇒ run the MCP server on stdio (the default behavior MCP
    clients expect). ``--version`` and ``--help`` print and exit.
    """
    parser = argparse.ArgumentParser(
        prog="patent-client-agents-mcp",
        description=(
            "Run the patent-client-agents MCP server. Exposes 136 "
            "default patent/IP tools to any MCP client; local/private deployments "
            "expose up to 234 tools when every env-gated family is configured. "
            "See docs/installation.md for client configuration."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"patent-client-agents {__version__}",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="MCP transport (HTTP requires authentication; default: stdio)",
    )
    args = parser.parse_args(argv)
    if _mcp_import_error is not None:
        raise SystemExit(
            "patent-client-agents-mcp requires the optional MCP dependencies. "
            "Install with: pip install 'patent-client-agents[mcp]'"
        ) from _mcp_import_error
    if args.transport == "http" and _auth is None:
        parser.error(
            "HTTP transport requires authentication. Set LAW_TOOLS_CORE_PUBLIC_URL "
            "and configure Google OAuth or static bearer credentials."
        )
    try:
        assert mcp is not None
        mcp.run(transport=args.transport)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
