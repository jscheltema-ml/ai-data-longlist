"""OAuth login for the Gain MCP server.

Gain's MCP server is guarded by WorkOS AuthKit, not by Entra, so a token minted from our own
app registration is rejected whatever scope it carries: wrong issuer, wrong audience.
Microsoft SSO is only how you authenticate on AuthKit's page.

Authorization code with PKCE, the flow OAuth 2.1 mandates and the one Gain confirmed they
support. It needs a browser and a person, so nothing here can run unattended.

The SDK's `OAuthClientProvider` does the protocol work (discovery, dynamic registration,
PKCE, refresh). What it leaves to us is the three host-specific parts: where to keep the
tokens, how to open a browser, and how to catch the redirect.
"""

import json
import threading
import webbrowser
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from agent_framework import MCPStreamableHTTPTool
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

MCP_URL = "https://gain.ai/mcp"
CALLBACK_PORT = 41573
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}/callback"

# Outside the repo, and holds a refresh token, so it is chmod 600 rather than gitignored.
# The client registration lives here too: registration is dynamic, and re-registering every
# run would leave a trail of dead clients on Gain's authorization server.
CACHE = Path.home() / ".gain_mcp_token.json"


class _FileStorage(TokenStorage):
    """Tokens and client registration in one JSON file."""

    def _read(self) -> dict:
        try:
            return json.loads(CACHE.read_text())
        except (OSError, ValueError):
            return {}

    def _write(self, key: str, value: dict) -> None:
        CACHE.write_text(json.dumps(self._read() | {key: value}))
        CACHE.chmod(0o600)

    async def get_tokens(self) -> OAuthToken | None:
        raw = self._read().get("tokens")
        return OAuthToken.model_validate(raw) if raw else None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._write("tokens", tokens.model_dump(mode="json"))

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        raw = self._read().get("client")
        return OAuthClientInformationFull.model_validate(raw) if raw else None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._write("client", client_info.model_dump(mode="json"))


def _serve_one_callback() -> dict[str, str]:
    """Run a one-request web server and return the query the browser was redirected with."""
    captured: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            captured.update({k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<p>Signed in. You can close this tab.</p>")

        def log_message(self, *args: object) -> None:
            """Silence the default stderr logging, which lands in the notebook."""

    with HTTPServer(("localhost", CALLBACK_PORT), Handler) as server:
        server.handle_request()
    return captured


def gain_auth(mcp_url: str = MCP_URL) -> OAuthClientProvider:
    """The httpx auth flow that signs requests to `mcp_url`, logging in on first use."""

    async def redirect_handler(url: str) -> None:
        print(f"Opening {url}", flush=True)
        webbrowser.open(url)

    async def callback_handler() -> tuple[str, str | None]:
        # The callback server blocks, so it goes on a thread to leave the event loop free.
        result: dict[str, str] = {}
        thread = threading.Thread(target=lambda: result.update(_serve_one_callback()))
        thread.start()
        thread.join()
        if "error" in result:
            raise RuntimeError(f"sign-in failed: {result.get('error_description', result['error'])}")
        return result["code"], result.get("state")

    return OAuthClientProvider(
        server_url=mcp_url,
        client_metadata=OAuthClientMetadata(
            client_name="long-list",
            redirect_uris=[CALLBACK_URL],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="none",
            scope="openid profile email offline_access",
        ),
        storage=_FileStorage(),
        redirect_handler=redirect_handler,
        callback_handler=callback_handler,
    )


def gain_client(mcp_url: str = MCP_URL) -> httpx.AsyncClient:
    """An HTTP client that authenticates itself against `mcp_url`.

    This is what `MCPStreamableHTTPTool(http_client=...)` wants, and what hands the agent
    every tool Gain exposes without any of them being declared here.
    """
    return httpx.AsyncClient(auth=gain_auth(mcp_url), timeout=60, follow_redirects=True)


@asynccontextmanager
async def gain_session(mcp_url: str = MCP_URL) -> AsyncIterator[ClientSession]:
    """An initialised MCP session, for calling Gain by hand rather than through an agent.

        async with gain_session() as session:
            tools = await session.list_tools()
    """
    async with streamable_http_client(mcp_url, http_client=gain_client(mcp_url)) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def gain_mcp_tools(name: str = "gain", mcp_url: str = MCP_URL) -> MCPStreamableHTTPTool:
    """Every tool Gain exposes, as one agent tool.

    Nothing is declared here, so a tool Gain adds becomes available without a change on our
    side. Hand the result to `Agent(tools=...)` and open it around the run:

        gain_tools = gain_mcp_tools()
        async with gain_tools:
            response = await agent.run("...")

    A factory rather than a module-level instance: each tool owns an MCP session, so two
    agents sharing one would share that session and the first to exit would close it out
    from under the second.
    """
    return MCPStreamableHTTPTool(name=name, url=mcp_url, http_client=gain_client(mcp_url))
