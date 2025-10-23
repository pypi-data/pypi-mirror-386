from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1671() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.Comment.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("Comment", string_type), ("name", string_type), ("value", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    Comment: str
    name: str
    value: str

IContext_reflection = _expr1671

def _arrow1677(__unit: None=None) -> IEncodable:
    class ObjectExpr1672(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1673(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:Comment")

    class ObjectExpr1674(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:name")

    class ObjectExpr1675(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:text")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1672()), ("Comment", ObjectExpr1673()), ("name", ObjectExpr1674()), ("value", ObjectExpr1675())])
    class ObjectExpr1676(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr1676()


context_jsonvalue: IEncodable = _arrow1677()

context_str: str = "\r\n{\r\n  \"@context\": {\r\n    \"sdo\": \"http://schema.org/\",\r\n    \r\n    \"Comment\": \"sdo:Comment\",\r\n    \"name\": \"sdo:name\",\r\n    \"value\": \"sdo:text\"\r\n  }\r\n}\r\n    "

__all__ = ["IContext_reflection", "context_jsonvalue", "context_str"]

