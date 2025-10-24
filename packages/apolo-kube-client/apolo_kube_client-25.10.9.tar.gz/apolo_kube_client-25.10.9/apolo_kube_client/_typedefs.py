from typing import TypeAlias

PrimitiveType: TypeAlias = int | float | str | bytes | bool | None
type JsonType = "PrimitiveType | list[JsonType] | dict[str, JsonType]"

type NestedStrKeyDict = dict[
    str, PrimitiveType | NestedStrKeyDict | list[PrimitiveType | NestedStrKeyDict]
]
