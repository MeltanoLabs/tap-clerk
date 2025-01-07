"""REST client handling, including ClerkStream base class."""

from __future__ import annotations

import decimal
import typing as t
from importlib import resources

from singer_sdk.authenticators import BearerTokenAuthenticator
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseOffsetPaginator
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context


# TODO: Delete this is if not using json files for schema definition
SCHEMAS_DIR = resources.files(__package__) / "schemas"


class ClerkStream(RESTStream):
    """Clerk stream class."""

    # Update this value if necessary or override `parse_response`.
    records_jsonpath = "$.data[*]"

    # Update this value if necessary or override `get_new_paginator`.
    next_page_token_jsonpath = "$.next_page"  # noqa: S105
    API_LIMIT_PAGE_SIZE = 500

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return "https://api.clerk.com/v1"

    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        return BearerTokenAuthenticator.create_for_stream(
            self,
            token=self.config.get("auth_token", ""),
        )

    def get_new_paginator(self) -> BaseOffsetPaginator:
        return BaseOffsetPaginator(start_value=0, page_size=self.API_LIMIT_PAGE_SIZE)

    def get_url_params(self, context: dict | None, next_page_token: Any | None) -> dict[str, Any]:
        params: dict = {"limit": self.API_LIMIT_PAGE_SIZE}
        if next_page_token:
            params["offset"] = next_page_token
        if self.replication_key:
            params["order_by"] = f'-{self.replication_key}'
        return params


    def parse_response(self, response: requests.Response) -> t.Iterable[dict]:
        """Parse the response and return an iterator of result records.

        Args:
            response: The HTTP ``requests.Response`` object.

        Yields:
            Each record from the source.
        """
        yield from extract_jsonpath(
            self.records_jsonpath,
            input=response.json(parse_float=decimal.Decimal),
        )
