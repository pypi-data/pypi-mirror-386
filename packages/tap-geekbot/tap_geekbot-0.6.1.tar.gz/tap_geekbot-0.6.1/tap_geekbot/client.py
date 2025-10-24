"""REST client handling, including GeekbotStream base class."""

from __future__ import annotations

import sys

from singer_sdk import RESTStream
from singer_sdk.authenticators import APIKeyAuthenticator

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class GeekbotStream(RESTStream):
    """Geekbot stream class."""

    url_base = "https://api.geekbot.com"
    records_jsonpath = "$[*]"
    primary_keys = ("id",)

    @property
    @override
    def authenticator(self) -> APIKeyAuthenticator:
        return APIKeyAuthenticator(
            key="Authorization",
            value=self.config["api_key"],
            location="header",
        )
