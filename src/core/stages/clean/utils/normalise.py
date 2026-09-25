"""Fixing the values strict structured output cannot constrain.

Strict mode carries no `pattern` and no `format`, so nothing on the wire stops a model
answering "Netherlands" where an alpha-2 code is wanted, or a bare host where a URL is
wanted. Every agent-backed source has the same problem, so the repair lives here rather than
in each connector.
"""

from typing import Any
from urllib.parse import urlparse

# Keys whose values are not held to a format on the wire, wherever they appear: on an
# identity, inside a mandate, on a deal in a track record.
COUNTRY_KEYS = frozenset({"country", "countries_active", "countries_acquired"})
URL_KEYS = frozenset({"website", "url"})


def normalise(node: Any) -> Any:
    """Walk a record and repair every value the schema could not constrain.

    Recursive because these keys are not only at the top: `countries_acquired` sits inside
    the track record and `url` sits on each deal within it.
    """
    if isinstance(node, list):
        return [normalise(item) for item in node]
    if not isinstance(node, dict):
        return node

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key in COUNTRY_KEYS:
            out[key] = [c for c in map(country_code, value) if c] if isinstance(value, list) else country_code(value)
        elif key in URL_KEYS:
            out[key] = url(value)
        elif key == "domain":
            out[key] = domain(value if isinstance(value, str) else None)
        else:
            out[key] = normalise(value)

    # The dedupe leans on the domain, so derive one from the website rather than fall back to
    # name-and-country because the agent left the field empty or omitted it. Keyed off
    # `website` rather than off `domain` being present: strict output always sends every key,
    # but nothing here should depend on that.
    if out.get("website") and not out.get("domain"):
        out["domain"] = domain(out["website"])
    return out


def country_code(value: Any) -> str | None:
    """ISO 3166-1 alpha-2, or nothing. "nl" is salvageable, "Netherlands" is not."""
    if not isinstance(value, str):
        return None
    candidate = value.strip().upper()
    return candidate if len(candidate) == 2 and candidate.isalpha() else None


def url(value: Any) -> str | None:
    """A full URL, or nothing. Bare hosts come back as often as URLs and `HttpUrl` rejects
    them, so a missing scheme is added rather than losing the field."""
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    return candidate if "//" in candidate else f"https://{candidate}"


def domain(website: str | None) -> str | None:
    """Bare, lower case, no scheme and no www: the form the dedupe compares."""
    if not website:
        return None
    host = urlparse(website if "//" in website else f"//{website}").netloc or ""
    host = host.split("@")[-1].split(":")[0].strip().lower().removeprefix("www.")
    return host or None
