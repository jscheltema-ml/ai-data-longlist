"""Device-code login for the Gain MCP server.

Gain's MCP server is guarded by WorkOS AuthKit, not by Entra, so a token minted from our own
app registration is rejected whatever scope it carries: wrong issuer, wrong audience.
Microsoft SSO is how you authenticate on AuthKit's page, not how the token is issued.

Device code rather than the authorization-code flow because it needs no local callback
listener, which makes it usable from a notebook and over SSH.
"""

import json
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

import httpx

MCP_URL = "https://gain.ai/mcp"
SCOPE = "openid profile email offline_access"
DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"

# Outside the repo, and holding a refresh token, so it is chmod 600 rather than gitignored.
# The client_id lives here too: registration is dynamic, and re-registering on every run
# would leave a trail of dead clients on Gain's authorization server.
CACHE = Path.home() / ".gain_mcp_token.json"


def get_token(mcp_url: str = MCP_URL) -> str:
    """Return a bearer token for `mcp_url`, logging in through the browser if needed."""
    cache = _load()
    if cache.get("expires_at", 0) > time.time() + 60:
        return cache["access_token"]

    with httpx.Client(timeout=30, follow_redirects=True) as http:
        meta = _discover(http, mcp_url)

        client_id = cache.get("client_id") or _register(http, meta)
        device = _authorize(http, meta, client_id)
        token = _poll(http, meta, client_id, device)

    _save(
        {
            "client_id": client_id,
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token"),
            "expires_at": time.time() + token.get("expires_in", 3600),
        }
    )
    return token["access_token"]


def _discover(http: httpx.Client, mcp_url: str) -> dict:
    """Follow RFC 9728 from the resource to its authorization server's metadata."""
    origin = f"{urlparse(mcp_url).scheme}://{urlparse(mcp_url).netloc}"
    resource = _json(http.get(f"{origin}/.well-known/oauth-protected-resource"))
    server = resource["authorization_servers"][0].rstrip("/")
    return _json(http.get(f"{server}/.well-known/oauth-authorization-server"))


def _register(http: httpx.Client, meta: dict) -> str:
    """Register a public client on the fly (RFC 7591); no secret, nothing pre-arranged."""
    body = {
        "client_name": "long-list",
        # Required even though the device flow never redirects, and it must be non-empty.
        # localhost is the conventional placeholder for a native client.
        "redirect_uris": ["http://localhost"],
        "grant_types": [DEVICE_GRANT, "refresh_token"],
        "token_endpoint_auth_method": "none",
        "application_type": "native",
    }
    return _json(http.post(meta["registration_endpoint"], json=body))["client_id"]


def _authorize(http: httpx.Client, meta: dict, client_id: str) -> dict:
    device = _json(http.post(meta["device_authorization_endpoint"], data={"client_id": client_id, "scope": SCOPE}))
    url = device.get("verification_uri_complete") or device["verification_uri"]
    # flush because a notebook buffers stdout, and this is the one thing the user has to act
    # on before the poll below can finish.
    print(f"Sign in at {url}", flush=True)
    print(f"Code {device['user_code']}: approve it in the browser, being signed in is not enough.", flush=True)
    webbrowser.open(url)
    return device


def _poll(http: httpx.Client, meta: dict, client_id: str, device: dict) -> dict:
    """Wait for the browser sign-in, backing off when the server says to (RFC 8628)."""
    interval = device.get("interval", 5)
    deadline = time.time() + device.get("expires_in", 600)

    while time.time() < deadline:
        time.sleep(interval)
        response = http.post(
            meta["token_endpoint"],
            data={"grant_type": DEVICE_GRANT, "device_code": device["device_code"], "client_id": client_id},
        )
        if response.status_code == 200:
            print("signed in.", flush=True)
            return response.json()

        error = response.json().get("error")
        if error == "authorization_pending":
            print(f"  waiting for approval, {int(deadline - time.time())}s left", flush=True)
            continue
        if error == "slow_down":
            interval += 5
            continue
        raise RuntimeError(f"device login failed: {error}")

    raise TimeoutError(
        "the code expired before anyone approved it. The browser page needs the confirm button "
        "pressed for this specific code; an existing session only skips the password step."
    )


def _json(response: httpx.Response) -> dict:
    """Return the body, or raise carrying it.

    `raise_for_status()` discards the response body, and for OAuth that body is the only part
    worth reading: a bare 400 says nothing, `error_description` says which field is wrong.
    """
    if response.is_error:
        raise RuntimeError(f"{response.status_code} from {response.request.url}: {response.text[:300]}")
    return response.json()


def _load() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _save(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache))
    CACHE.chmod(0o600)
