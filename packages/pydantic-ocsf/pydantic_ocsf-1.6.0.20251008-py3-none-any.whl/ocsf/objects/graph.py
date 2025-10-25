import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.edge import Edge
from ocsf.objects.node import Node


class QueryLanguageId(IntEnum):
    UNKNOWN = 0
    CYPHER = 1
    GRAPHQL = 2
    GREMLIN = 3
    GQL = 4
    G_CORE = 5
    PGQL = 6
    SPARQL = 7
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return QueryLanguageId[obj]
        else:
            return QueryLanguageId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "CYPHER": "Cypher",
            "GRAPHQL": "GraphQL",
            "GREMLIN": "Gremlin",
            "GQL": "GQL",
            "G_CORE": "G-CORE",
            "PGQL": "PGQL",
            "SPARQL": "SPARQL",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Graph(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "graph"

    # Required
    nodes: list[Node]

    # Recommended
    name: str | None = None
    query_language_id: QueryLanguageId | None = None
    uid: str | None = None

    # Optional
    desc: str | None = None
    edges: list[Edge] | None = None
    is_directed: bool | None = None
    type_: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def query_language(self) -> str | None:
        if self.query_language_id is None:
            return None
        return self.query_language_id.name

    @query_language.setter
    def query_language(self, value: str | None) -> None:
        if value is None:
            self.query_language_id = None
        else:
            self.query_language_id = QueryLanguageId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_query_language_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "query_language" in data and "query_language_id" not in data:
            query_language = re.sub(r"\W", "_", data.pop("query_language").upper())
            data["query_language_id"] = QueryLanguageId[query_language]
        return data

    @model_validator(mode="after")
    def validate_query_language_after(self) -> Self:
        if self.__pydantic_extra__ and "query_language" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("query_language")
        return self
