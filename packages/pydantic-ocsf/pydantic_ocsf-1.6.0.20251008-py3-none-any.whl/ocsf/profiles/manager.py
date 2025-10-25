import importlib
import inspect
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocsf.profiles.base_profile import BaseProfile


# TODO: Allow extensions to register modified versions of profiles.


class ProfileManager:
    search_path: dict[str, list[str]] = defaultdict(list, {"": ["ocsf.profiles"]})
    __profiles__: dict[str, type["BaseProfile"]] = dict()

    @classmethod
    def _get_profile_class(cls, profile: str) -> type["BaseProfile"]:
        from ocsf.profiles.base_profile import BaseProfile

        if "/" in profile:
            ns, _, profile = profile.partition("/")
        else:
            ns = ""

        for parent_module in cls.search_path[ns]:
            try:
                m = importlib.import_module(f"{parent_module}.{profile}")
            except ModuleNotFoundError:
                continue
            for _, pcls in inspect.getmembers(m, inspect.isclass):
                if issubclass(pcls, BaseProfile) and getattr(pcls, "schema_name", None) == profile:
                    return pcls
        raise ValueError(profile)

    @classmethod
    def get_profile_class(cls, profile: str):
        if profile not in cls.__profiles__:
            cls.__profiles__[profile] = cls._get_profile_class(profile)
        return cls.__profiles__[profile]

    @classmethod
    def register_profile(cls, profile: type["BaseProfile"], overwrite: bool = False):
        if profile.schema_name in cls.__profiles__:
            if cls.__profiles__[profile.schema_name] is profile:
                return
            if not overwrite:
                raise KeyError(f"'{profile.schema_name}' already registered")
        cls.__profiles__[profile.schema_name] = profile
