from __future__ import annotations
from dataclasses import dataclass
from typing import (Any, TypeVar)
from ....fable_modules.fable_library.reflection import (TypeInfo, string_type, record_type)
from ....fable_modules.fable_library.seq import map
from ....fable_modules.fable_library.types import Record
from ....fable_modules.fable_library.util import (to_enumerable, IEnumerable_1)
from ....fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1)

__A_ = TypeVar("__A_")

def _expr1890() -> TypeInfo:
    return record_type("ARCtrl.Json.ROCrateContext.Study.IContext", [], IContext, lambda: [("sdo", string_type), ("arc", string_type), ("Study", string_type), ("ArcStudy", string_type), ("identifier", string_type), ("title", string_type), ("description", string_type), ("submission_date", string_type), ("public_release_date", string_type), ("publications", string_type), ("people", string_type), ("assays", string_type), ("filename", string_type), ("comments", string_type), ("protocols", string_type), ("materials", string_type), ("other_materials", string_type), ("sources", string_type), ("samples", string_type), ("process_sequence", string_type), ("factors", string_type), ("characteristic_categories", string_type), ("unit_categories", string_type), ("study_design_descriptors", string_type)])


@dataclass(eq = False, repr = False, slots = True)
class IContext(Record):
    sdo: str
    arc: str
    Study: str
    ArcStudy: str
    identifier: str
    title: str
    description: str
    submission_date: str
    public_release_date: str
    publications: str
    people: str
    assays: str
    filename: str
    comments: str
    protocols: str
    materials: str
    other_materials: str
    sources: str
    samples: str
    process_sequence: str
    factors: str
    characteristic_categories: str
    unit_categories: str
    study_design_descriptors: str

IContext_reflection = _expr1890

def _arrow1910(__unit: None=None) -> IEncodable:
    class ObjectExpr1891(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
            return helpers.encode_string("http://schema.org/")

    class ObjectExpr1892(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
            return helpers_1.encode_string("sdo:Dataset")

    class ObjectExpr1893(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
            return helpers_2.encode_string("sdo:identifier")

    class ObjectExpr1894(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
            return helpers_3.encode_string("sdo:headline")

    class ObjectExpr1895(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
            return helpers_4.encode_string("sdo:additionalType")

    class ObjectExpr1896(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
            return helpers_5.encode_string("sdo:description")

    class ObjectExpr1897(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
            return helpers_6.encode_string("sdo:dateCreated")

    class ObjectExpr1898(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
            return helpers_7.encode_string("sdo:datePublished")

    class ObjectExpr1899(IEncodable):
        def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
            return helpers_8.encode_string("sdo:citation")

    class ObjectExpr1900(IEncodable):
        def Encode(self, helpers_9: IEncoderHelpers_1[Any]) -> Any:
            return helpers_9.encode_string("sdo:creator")

    class ObjectExpr1901(IEncodable):
        def Encode(self, helpers_10: IEncoderHelpers_1[Any]) -> Any:
            return helpers_10.encode_string("sdo:hasPart")

    class ObjectExpr1903(IEncodable):
        def Encode(self, helpers_11: IEncoderHelpers_1[Any]) -> Any:
            return helpers_11.encode_string("sdo:hasPart")

    class ObjectExpr1904(IEncodable):
        def Encode(self, helpers_12: IEncoderHelpers_1[Any]) -> Any:
            return helpers_12.encode_string("sdo:alternateName")

    class ObjectExpr1905(IEncodable):
        def Encode(self, helpers_13: IEncoderHelpers_1[Any]) -> Any:
            return helpers_13.encode_string("sdo:comment")

    class ObjectExpr1906(IEncodable):
        def Encode(self, helpers_14: IEncoderHelpers_1[Any]) -> Any:
            return helpers_14.encode_string("sdo:about")

    class ObjectExpr1907(IEncodable):
        def Encode(self, helpers_15: IEncoderHelpers_1[Any]) -> Any:
            return helpers_15.encode_string("arc:ARC#ARC_00000037")

    values: IEnumerable_1[tuple[str, IEncodable]] = to_enumerable([("sdo", ObjectExpr1891()), ("Study", ObjectExpr1892()), ("identifier", ObjectExpr1893()), ("title", ObjectExpr1894()), ("additionalType", ObjectExpr1895()), ("description", ObjectExpr1896()), ("submissionDate", ObjectExpr1897()), ("publicReleaseDate", ObjectExpr1898()), ("publications", ObjectExpr1899()), ("people", ObjectExpr1900()), ("assays", ObjectExpr1901()), ("dataFiles", ObjectExpr1903()), ("filename", ObjectExpr1904()), ("comments", ObjectExpr1905()), ("processSequence", ObjectExpr1906()), ("studyDesignDescriptors", ObjectExpr1907())])
    class ObjectExpr1909(IEncodable):
        def Encode(self, helpers_16: IEncoderHelpers_1[Any]) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_16))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_16.encode_object(arg)

    return ObjectExpr1909()


context_jsonvalue: IEncodable = _arrow1910()

__all__ = ["IContext_reflection", "context_jsonvalue"]

