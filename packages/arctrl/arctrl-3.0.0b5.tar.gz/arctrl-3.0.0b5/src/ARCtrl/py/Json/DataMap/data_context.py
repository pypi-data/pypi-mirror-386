from __future__ import annotations
from typing import (Any, TypeVar)
from ...fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ...fable_modules.fable_library.option import map
from ...fable_modules.fable_library.seq import map as map_1
from ...fable_modules.fable_library.util import IEnumerable_1
from ...fable_modules.thoth_json_core.decode import (object, IRequiredGetter, IOptionalGetter, string, IGetters)
from ...fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ...Core.data import Data
from ...Core.data_context import (DataContext__get_Explication, DataContext__get_Unit, DataContext__get_ObjectType, DataContext__get_Description, DataContext__get_GeneratedBy, DataContext__get_Label, DataContext, DataContext__ctor_Z780A8A2A)
from ...Core.ontology_annotation import OntologyAnnotation
from ..data import (encoder as encoder_1, decoder as decoder_1)
from ..encode import try_include
from ..ontology_annotation import (OntologyAnnotation_encoder, OntologyAnnotation_decoder)

__A_ = TypeVar("__A_")

def encoder(dc: DataContext) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], dc: Any=dc) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2921(oa: OntologyAnnotation, dc: Any=dc) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def _arrow2923(oa_1: OntologyAnnotation, dc: Any=dc) -> IEncodable:
        return OntologyAnnotation_encoder(oa_1)

    def _arrow2925(oa_2: OntologyAnnotation, dc: Any=dc) -> IEncodable:
        return OntologyAnnotation_encoder(oa_2)

    def _arrow2927(value: str, dc: Any=dc) -> IEncodable:
        class ObjectExpr2926(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2926()

    def _arrow2929(value_2: str, dc: Any=dc) -> IEncodable:
        class ObjectExpr2928(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr2928()

    def _arrow2931(value_4: str, dc: Any=dc) -> IEncodable:
        class ObjectExpr2930(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_4)

        return ObjectExpr2930()

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("data", encoder_1(dc)), try_include("explication", _arrow2921, DataContext__get_Explication(dc)), try_include("unit", _arrow2923, DataContext__get_Unit(dc)), try_include("objectType", _arrow2925, DataContext__get_ObjectType(dc)), try_include("description", _arrow2927, DataContext__get_Description(dc)), try_include("generatedBy", _arrow2929, DataContext__get_GeneratedBy(dc)), try_include("label", _arrow2931, DataContext__get_Label(dc))]))
    class ObjectExpr2932(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any], dc: Any=dc) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_3))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_3.encode_object(arg)

    return ObjectExpr2932()


def _arrow2939(get: IGetters) -> DataContext:
    data: Data
    object_arg: IRequiredGetter = get.Required
    data = object_arg.Field("data", decoder_1)
    def _arrow2933(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("explication", OntologyAnnotation_decoder)

    def _arrow2934(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("unit", OntologyAnnotation_decoder)

    def _arrow2935(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("objectType", OntologyAnnotation_decoder)

    def _arrow2936(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("label", string)

    def _arrow2937(__unit: None=None) -> str | None:
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("description", string)

    def _arrow2938(__unit: None=None) -> str | None:
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("generatedBy", string)

    return DataContext__ctor_Z780A8A2A(data.ID, data.Name, data.DataType, data.Format, data.SelectorFormat, _arrow2933(), _arrow2934(), _arrow2935(), _arrow2936(), _arrow2937(), _arrow2938(), data.Comments)


decoder: Decoder_1[DataContext] = object(_arrow2939)

__all__ = ["encoder", "decoder"]

