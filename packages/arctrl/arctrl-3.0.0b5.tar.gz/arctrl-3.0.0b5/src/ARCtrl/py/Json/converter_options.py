from typing import Any
from ..fable_modules.fable_library.reflection import (TypeInfo, union_type)
from ..fable_modules.fable_library.types import (Array, Union)

def _expr1904() -> TypeInfo:
    return union_type("ARCtrl.Json.ConverterOptions", [], ConverterOptions, lambda: [[], [], []])


class ConverterOptions(Union):
    def __init__(self, tag: int, *fields: Any) -> None:
        super().__init__()
        self.tag: int = tag or 0
        self.fields: Array[Any] = list(fields)

    @staticmethod
    def cases() -> list[str]:
        return ["ARCtrl", "ROCrate", "ISAJson"]


ConverterOptions_reflection = _expr1904

__all__ = ["ConverterOptions_reflection"]

