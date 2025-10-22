# This is free and unencumbered software released into the public domain.

from pydantic import BaseModel, Field
from typing import ClassVar
from typing_extensions import Self


class Thing(BaseModel):
    model_label: ClassVar[str] = "Thing"

    type: str = Field("Thing", alias="@type")
    id: str | None = Field(default=None, alias="@id")

    def __init__(self, id: str | None = None, **kwargs: object):
        super().__init__(**{"@id": id, **kwargs})

    def metadata(self) -> Self:
        return self

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), separators=(",", ":"))

    def to_dict(self) -> dict[str, object]:
        return self.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_computed_fields=True,
            serialize_as_any=True,
        )
