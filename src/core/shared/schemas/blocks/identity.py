"""Who the company is."""

from pydantic import HttpUrl

from shared.schemas.common.base import Base, CountryCode


class Identity(Base):
    """The fields the dedupe works from.

    `domain` is the identifier when there is no LEI or registration number, so it is stored
    bare and lower case (no scheme, no `www.`) to be comparable across sources; `website`
    keeps the full URL for a human to click.
    """

    name: str
    country: CountryCode | None = None
    domain: str | None = None
    website: HttpUrl | None = None
    hq_city: str | None = None
