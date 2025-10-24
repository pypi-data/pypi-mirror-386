"""Geekbot tap class."""

from __future__ import annotations

import sys

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_geekbot.streams import Reports, StandUps, Teams

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class TapGeekbot(Tap):
    """Singer tap for Geekbot."""

    name = "tap-geekbot"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_key",
            th.StringType,
            required=True,
            description="API Key for Geekbot",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="Earliest datetime to get data from",
        ),
    ).to_dict()

    @override
    def discover_streams(self) -> list[Stream]:
        return [
            Teams(tap=self),
            Reports(tap=self),
            StandUps(tap=self),
        ]
