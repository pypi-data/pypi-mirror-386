from typing import ClassVar

from pydantic import model_validator

from ocsf.objects.object import Object


class OccurrenceDetails(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "occurrence_details"

    # Optional
    cell_name: str | None = None
    column_name: str | None = None
    column_number: int | None = None
    end_line: int | None = None
    json_path: str | None = None
    page_number: int | None = None
    record_index_in_array: int | None = None
    row_number: int | None = None
    start_line: int | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in [
                "cell_name",
                "column_name",
                "column_number",
                "end_line",
                "json_path",
                "page_number",
                "record_index_in_array",
                "row_number",
                "start_line",
            ]
        ):
            raise ValueError(
                "At least one of `cell_name`, `column_name`, `column_number`, `end_line`, `json_path`, `page_number`, `record_index_in_array`, `row_number`, `start_line` must be provided"
            )
        return self
