from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1678() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.Component.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("Component", string_type), ("ArcComponent", string_type), ("component_name", string_type), ("component_type", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    Component: str
    ArcComponent: str
    component_name: str
    component_type: str

IContext_reflection = _expr1678

def _arrow1688(__unit: None=None) -> IEncodable:
    class ObjectExpr1679(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1680(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:PropertyValue")

    class ObjectExpr1681(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:name")

    class ObjectExpr1682(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:propertyID")

    class ObjectExpr1683(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("sdo:value")

    class ObjectExpr1684(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("sdo:valueReference")

    class ObjectExpr1685(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            return helpers_6.encode_string("sdo:unitText")

    class ObjectExpr1686(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
            return helpers_7.encode_string("sdo:unitCode")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1679()), ("Component", ObjectExpr1680()), ("category", ObjectExpr1681()), ("categoryCode", ObjectExpr1682()), ("value", ObjectExpr1683()), ("valueCode", ObjectExpr1684()), ("unit", ObjectExpr1685()), ("unitCode", ObjectExpr1686())])
    class ObjectExpr1687(IEncodable):
        def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_8))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_8.encode_object(arg)

    return ObjectExpr1687()


context_jsonvalue: IEncodable = _arrow1688()

context_str: str = "\r\n{\r\n  \"@context\": {\r\n    \"sdo\": \"http://schema.org/\",\r\n    \r\n    \"Component\": \"sdo:PropertyValue\",\r\n\r\n    \"componentName\": \"sdo\",\r\n    \"componentType\": \"arc:ARC#ARC_00000102\"\r\n  }\r\n}\r\n    "

__all__ = ["IContext_reflection", "context_jsonvalue", "context_str"]

