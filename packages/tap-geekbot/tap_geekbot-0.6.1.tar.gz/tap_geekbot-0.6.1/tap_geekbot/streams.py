"""Stream type classes for tap-geekbot."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from singer_sdk import typing as th

from tap_geekbot.client import GeekbotStream

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from singer_sdk.helpers.types import Context, Record

user = th.ObjectType(
    th.Property("id", th.StringType),
    th.Property("email", th.EmailType),
    th.Property("username", th.StringType),
    th.Property("role", th.StringType),
    th.Property("realname", th.StringType),
    th.Property("profile_img", th.StringType),
)

question = th.ObjectType(
    th.Property("id", th.IntegerType),
    th.Property("color", th.StringType),
    th.Property("text", th.StringType),
    th.Property("schedule", th.StringType),
    th.Property("answer_type", th.StringType),
    th.Property("answer_choices", th.ArrayType(th.StringType)),
    th.Property("hasAnswers", th.BooleanType),
    th.Property("is_random", th.BooleanType),
    th.Property("random_texts", th.ArrayType(th.StringType)),
    th.Property("prefilled_by", th.IntegerType),
    th.Property("text_id", th.IntegerType),
    th.Property("preconditions", th.ArrayType(th.StringType)),
    th.Property("label", th.StringType),
)


class Teams(GeekbotStream):
    """Teams stream."""

    name = "teams"
    path = "/v1/teams"
    records_jsonpath = "$"

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType),
        th.Property("name", th.StringType),
        th.Property("users", th.ArrayType(user)),
    ).to_dict()


class Reports(GeekbotStream):
    """Reports stream."""

    name = "reports"
    path = "/v1/reports"
    replication_key = "_sdc_timestamp"

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType),
        th.Property("slack_ts", th.StringType),
        th.Property("standup_id", th.IntegerType),
        th.Property("timestamp", th.IntegerType),
        th.Property("_sdc_timestamp", th.DateTimeType),
        th.Property("channel", th.StringType),
        th.Property("is_anonymous", th.BooleanType),
        th.Property("is_confidential", th.BooleanType),
        th.Property("members", th.ArrayType(user)),
        th.Property(
            "questions",
            th.ArrayType(
                th.ObjectType(
                    th.Property("id", th.IntegerType),
                    th.Property("question", th.StringType),
                    th.Property("question_id", th.IntegerType),
                    th.Property("color", th.StringType),
                    th.Property("answer", th.StringType),
                    th.Property(
                        "images",
                        th.ArrayType(
                            th.ObjectType(
                                th.Property("title", th.StringType),
                                th.Property("image_url", th.URIType),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ).to_dict()

    @override
    def get_url_params(self, context: Context | None, next_page_token: Any | None) -> dict[str, Any]:
        params: dict[str, Any] = super().get_url_params(context, next_page_token)  # type: ignore[assignment]
        params["limit"] = 100

        if start_time := self.get_starting_timestamp(context):
            params["after"] = start_time.timestamp()

        return params

    @override
    def post_process(self, row: Record, context: Context | None = None) -> Record | None:
        row["_sdc_timestamp"] = datetime.fromtimestamp(row["timestamp"], tz=timezone.utc)
        return row


class StandUps(GeekbotStream):
    """Reports stream."""

    name = "standups"
    path = "/v1/standups"

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType),
        th.Property("name", th.StringType),
        th.Property("time", th.TimeType),
        th.Property(
            "wait_time",
            th.NumberType,
            description=(
                "Minutes to wait after user logs in before asking question. Null value means no automated asking."
            ),
        ),
        th.Property("timezone", th.StringType),
        th.Property("days", th.ArrayType(th.StringType)),
        th.Property("channel", th.StringType),
        th.Property("channel_ready", th.BooleanType),
        th.Property("questions", th.ArrayType(question)),
        th.Property("users", th.ArrayType(user)),
        th.Property("users_total", th.IntegerType),
        th.Property("webhooks", th.ArrayType(th.StringType)),
        th.Property("master", th.StringType),
        th.Property("sync_channel_members", th.BooleanType),
    ).to_dict()
