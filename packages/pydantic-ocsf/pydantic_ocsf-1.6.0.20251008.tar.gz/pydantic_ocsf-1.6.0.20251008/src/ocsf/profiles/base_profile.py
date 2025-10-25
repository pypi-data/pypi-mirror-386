from typing import Any, ClassVar, Self

from pydantic import ModelWrapValidatorHandler, model_validator

from ocsf.events.base_event import BaseEvent
from ocsf.ocsf_object import OcsfObject


class BaseProfile(OcsfObject):
    schema_name: ClassVar[str]
    __event__: BaseEvent

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> Self:
        if not isinstance(obj, BaseEvent):
            raise ValueError("Must validate an OCSF profile from an OCSF event")
        instance = super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            by_alias=by_alias,
            by_name=by_name,
        )
        instance.__event__ = obj
        obj.__pydantic_extra__, instance.__pydantic_extra__ = instance.__pydantic_extra__, None
        return instance

    @model_validator(mode="wrap")
    @classmethod
    def validate_event(cls, event: BaseEvent, handler: ModelWrapValidatorHandler) -> Self:
        data = event.__pydantic_extra__ or {}
        return handler(data)
