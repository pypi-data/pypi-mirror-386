from datetime import datetime
from typing import Annotated

from pydantic import PlainSerializer, PlainValidator


def serialize_timestamp_t(value: datetime | int) -> int:
    if isinstance(value, int):
        return value
    return int(value.timestamp() * 1000)


def validate_timestamp_t(value: datetime | int) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromtimestamp(value / 1000)


Timestamp = Annotated[datetime, PlainValidator(validate_timestamp_t), PlainSerializer(serialize_timestamp_t)]
