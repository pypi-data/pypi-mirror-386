from datetime import datetime
from typing import Any, ClassVar, Self

import dateparser
from pydantic import ModelWrapValidatorHandler, TypeAdapter, model_serializer, model_validator

from ocsf.events.base_event import BaseEvent
from ocsf.profiles.base_profile import BaseProfile


class Datetime(BaseProfile):
    __datetime_fields__: dict[str, datetime]
    schema_name: ClassVar[str] = "datetime"

    def model_post_init(self, context: Any) -> None:
        self.__datetime_fields__ = dict()
        return super().model_post_init(context)

    @model_serializer(mode="plain")
    def serialize(self):
        return {
            k: TypeAdapter(datetime).dump_python(v)
            for (k, v) in self.__datetime_fields__.items()
            if k.endswith("_dt") and isinstance(v, datetime)
        }

    @model_validator(mode="wrap")
    @classmethod
    def validate_event(cls, event: BaseEvent, _: ModelWrapValidatorHandler) -> Self:
        instance = cls.model_construct()
        extra_data = {}
        for k in event.__class__.model_fields:
            if v := getattr(event, k, None):
                if isinstance(v, datetime):
                    instance.__datetime_fields__[f"{k}_dt"] = v
        if not event.__pydantic_extra__:
            return instance
        data = event.__pydantic_extra__
        for k in data:
            if k.endswith("_dt"):
                value = dateparser.parse(data[k])
                if value is not None:
                    instance.__datetime_fields__[k] = value
            else:
                extra_data[k] = data[k]
        if extra_data:
            instance.__pydantic_extra__ = extra_data
        else:
            instance.__pydantic_extra__ = None
        return instance

    def __getattr__(self, attr: str) -> datetime:
        if not attr.endswith("_dt"):
            raise AttributeError(attr)
        if attr_val := self.__datetime_fields__.get(attr):
            return attr_val
        if attr_val := getattr(self.__event__, attr[:-3], None):
            if isinstance(attr_val, datetime):
                return attr_val
        raise AttributeError(attr)
