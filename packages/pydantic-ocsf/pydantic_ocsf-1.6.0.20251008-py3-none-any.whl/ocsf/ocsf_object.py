from collections.abc import Callable
from functools import wraps
from typing import Any, ClassVar, Protocol, TypeGuard

from pydantic import BaseModel, ConfigDict
from pydantic._internal._model_construction import ModelMetaclass


class Wrappable[T, **P](Protocol):
    __self__: "OcsfObject"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T: ...


def is_wrappable(f: Any) -> TypeGuard[Wrappable]:
    return callable(f) and hasattr(f, "__self__")


def force_model_rebuild[T, **P](f: Wrappable[T, P]) -> Callable[P, T]:
    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        cls: "OcsfObject" = f.__self__
        if not cls.__pydantic_complete__:
            from ocsf.objects.ldap_person import LdapPerson  # noqa: F401
            from ocsf.objects.network_proxy import NetworkProxy  # noqa: F401
            from ocsf.objects.user import User  # noqa: F401

            if not LdapPerson.__pydantic_complete__:
                LdapPerson.model_rebuild()
            if not NetworkProxy.__pydantic_complete__:
                NetworkProxy.model_rebuild()
            if not User.__pydantic_complete__:
                User.model_rebuild()

            cls.model_rebuild(
                _types_namespace={
                    "LdapPerson": LdapPerson,
                    "NetworkProxy": NetworkProxy,
                    "User": User,
                }
            )
        return f(*args, **kwargs)

    return wrapper


class OcsfModelMetaclass(ModelMetaclass):
    def __getattribute__(self, name: str) -> Any:
        value = super().__getattribute__(name)
        if (name.startswith("model_validate") or name.startswith("model_dump")) and is_wrappable(value):
            value = force_model_rebuild(value)
        return value


class OcsfObject(BaseModel, metaclass=OcsfModelMetaclass):
    schema_name: ClassVar[str]
    allowed_profiles: ClassVar[list[str] | None]
    model_config = ConfigDict(extra="allow")
