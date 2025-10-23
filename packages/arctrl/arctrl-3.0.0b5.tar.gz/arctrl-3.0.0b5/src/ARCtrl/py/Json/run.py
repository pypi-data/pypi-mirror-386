from __future__ import annotations
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ..fable_modules.fable_library.option import map
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IRequiredGetter, string, IOptionalGetter, resize_array, IGetters)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.arc_types import ArcRun
from ..Core.comment import Comment
from ..Core.data_map import DataMap
from ..Core.ontology_annotation import OntologyAnnotation
from ..Core.person import Person
from ..Core.Table.arc_table import ArcTable
from ..Core.Table.composite_cell import CompositeCell
from .comment import (encoder as encoder_4, decoder as decoder_4)
from .DataMap.data_map import (encoder as encoder_1, decoder as decoder_2, encoder_compressed as encoder_compressed_1, decoder_compressed as decoder_compressed_2)
from .encode import (try_include, try_include_seq)
from .ontology_annotation import (OntologyAnnotation_encoder, OntologyAnnotation_decoder)
from .person import (encoder as encoder_3, decoder as decoder_3)
from .Table.arc_table import (encoder as encoder_2, decoder as decoder_1, encoder_compressed as encoder_compressed_2, decoder_compressed as decoder_compressed_1)

__A_ = TypeVar("__A_")

def encoder(run: ArcRun) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], run: Any=run) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3104(__unit: None=None, run: Any=run) -> IEncodable:
        value: str = run.Identifier
        class ObjectExpr3103(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3103()

    def _arrow3107(value_1: str, run: Any=run) -> IEncodable:
        class ObjectExpr3106(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3106()

    def _arrow3110(value_3: str, run: Any=run) -> IEncodable:
        class ObjectExpr3109(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3109()

    def _arrow3111(oa: OntologyAnnotation, run: Any=run) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def _arrow3112(oa_1: OntologyAnnotation, run: Any=run) -> IEncodable:
        return OntologyAnnotation_encoder(oa_1)

    def _arrow3114(oa_2: OntologyAnnotation, run: Any=run) -> IEncodable:
        return OntologyAnnotation_encoder(oa_2)

    def _arrow3115(dm: DataMap, run: Any=run) -> IEncodable:
        return encoder_1(dm)

    def _arrow3117(value_5: str, run: Any=run) -> IEncodable:
        class ObjectExpr3116(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3116()

    def _arrow3118(table: ArcTable, run: Any=run) -> IEncodable:
        return encoder_2(table)

    def _arrow3119(person: Person, run: Any=run) -> IEncodable:
        return encoder_3(person)

    def _arrow3121(comment: Comment, run: Any=run) -> IEncodable:
        return encoder_4(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3104()), try_include("Title", _arrow3107, run.Title), try_include("Description", _arrow3110, run.Description), try_include("MeasurementType", _arrow3111, run.MeasurementType), try_include("TechnologyType", _arrow3112, run.TechnologyType), try_include("TechnologyPlatform", _arrow3114, run.TechnologyPlatform), try_include("DataMap", _arrow3115, run.DataMap), try_include_seq("WorkflowIdentifiers", _arrow3117, run.WorkflowIdentifiers), try_include_seq("Tables", _arrow3118, run.Tables), try_include_seq("Performers", _arrow3119, run.Performers), try_include_seq("Comments", _arrow3121, run.Comments)]))
    class ObjectExpr3127(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], run: Any=run) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr3127()


def _arrow3146(get: IGetters) -> ArcRun:
    def _arrow3132(__unit: None=None) -> str:
        object_arg: IRequiredGetter = get.Required
        return object_arg.Field("Identifier", string)

    def _arrow3134(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("Title", string)

    def _arrow3135(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("Description", string)

    def _arrow3138(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("MeasurementType", OntologyAnnotation_decoder)

    def _arrow3139(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("TechnologyType", OntologyAnnotation_decoder)

    def _arrow3140(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("TechnologyPlatform", OntologyAnnotation_decoder)

    def _arrow3141(__unit: None=None) -> Array[str] | None:
        arg_13: Decoder_1[Array[str]] = resize_array(string)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("WorkflowIdentifiers", arg_13)

    def _arrow3142(__unit: None=None) -> Array[ArcTable] | None:
        arg_15: Decoder_1[Array[ArcTable]] = resize_array(decoder_1)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("Tables", arg_15)

    def _arrow3143(__unit: None=None) -> DataMap | None:
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("DataMap", decoder_2)

    def _arrow3144(__unit: None=None) -> Array[Person] | None:
        arg_19: Decoder_1[Array[Person]] = resize_array(decoder_3)
        object_arg_9: IOptionalGetter = get.Optional
        return object_arg_9.Field("Performers", arg_19)

    def _arrow3145(__unit: None=None) -> Array[Comment] | None:
        arg_21: Decoder_1[Array[Comment]] = resize_array(decoder_4)
        object_arg_10: IOptionalGetter = get.Optional
        return object_arg_10.Field("Comments", arg_21)

    return ArcRun.create(_arrow3132(), _arrow3134(), _arrow3135(), _arrow3138(), _arrow3139(), _arrow3140(), _arrow3141(), _arrow3142(), _arrow3143(), _arrow3144(), _arrow3145())


decoder: Decoder_1[ArcRun] = object(_arrow3146)

def encoder_compressed(string_table: Any, oa_table: Any, cell_table: Any, run: ArcRun) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3150(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        value: str = run.Identifier
        class ObjectExpr3149(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3149()

    def _arrow3152(value_1: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        class ObjectExpr3151(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3151()

    def _arrow3154(value_3: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        class ObjectExpr3153(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3153()

    def _arrow3155(oa: OntologyAnnotation, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def _arrow3156(oa_1: OntologyAnnotation, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        return OntologyAnnotation_encoder(oa_1)

    def _arrow3157(oa_2: OntologyAnnotation, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        return OntologyAnnotation_encoder(oa_2)

    def _arrow3158(dm: DataMap, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        return encoder_compressed_1(string_table, oa_table, cell_table, dm)

    def _arrow3160(value_5: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        class ObjectExpr3159(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3159()

    def _arrow3161(table: ArcTable, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        return encoder_compressed_2(string_table, oa_table, cell_table, table)

    def _arrow3162(person: Person, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        return encoder_3(person)

    def _arrow3163(comment: Comment, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> IEncodable:
        return encoder_4(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3150()), try_include("Title", _arrow3152, run.Title), try_include("Description", _arrow3154, run.Description), try_include("MeasurementType", _arrow3155, run.MeasurementType), try_include("TechnologyType", _arrow3156, run.TechnologyType), try_include("TechnologyPlatform", _arrow3157, run.TechnologyPlatform), try_include("DataMap", _arrow3158, run.DataMap), try_include_seq("WorkflowIdentifiers", _arrow3160, run.WorkflowIdentifiers), try_include_seq("Tables", _arrow3161, run.Tables), try_include_seq("Performers", _arrow3162, run.Performers), try_include_seq("Comments", _arrow3163, run.Comments)]))
    class ObjectExpr3164(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, run: Any=run) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr3164()


def decoder_compressed(string_table: Array[str], oa_table: Array[OntologyAnnotation], cell_table: Array[CompositeCell]) -> Decoder_1[ArcRun]:
    def _arrow3176(get: IGetters, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ArcRun:
        def _arrow3165(__unit: None=None) -> str:
            object_arg: IRequiredGetter = get.Required
            return object_arg.Field("Identifier", string)

        def _arrow3166(__unit: None=None) -> str | None:
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("Title", string)

        def _arrow3167(__unit: None=None) -> str | None:
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("Description", string)

        def _arrow3168(__unit: None=None) -> OntologyAnnotation | None:
            object_arg_3: IOptionalGetter = get.Optional
            return object_arg_3.Field("MeasurementType", OntologyAnnotation_decoder)

        def _arrow3169(__unit: None=None) -> OntologyAnnotation | None:
            object_arg_4: IOptionalGetter = get.Optional
            return object_arg_4.Field("TechnologyType", OntologyAnnotation_decoder)

        def _arrow3170(__unit: None=None) -> OntologyAnnotation | None:
            object_arg_5: IOptionalGetter = get.Optional
            return object_arg_5.Field("TechnologyPlatform", OntologyAnnotation_decoder)

        def _arrow3171(__unit: None=None) -> Array[str] | None:
            arg_13: Decoder_1[Array[str]] = resize_array(string)
            object_arg_6: IOptionalGetter = get.Optional
            return object_arg_6.Field("WorkflowIdentifiers", arg_13)

        def _arrow3172(__unit: None=None) -> Array[ArcTable] | None:
            arg_15: Decoder_1[Array[ArcTable]] = resize_array(decoder_compressed_1(string_table, oa_table, cell_table))
            object_arg_7: IOptionalGetter = get.Optional
            return object_arg_7.Field("Tables", arg_15)

        def _arrow3173(__unit: None=None) -> DataMap | None:
            arg_17: Decoder_1[DataMap] = decoder_compressed_2(string_table, oa_table, cell_table)
            object_arg_8: IOptionalGetter = get.Optional
            return object_arg_8.Field("DataMap", arg_17)

        def _arrow3174(__unit: None=None) -> Array[Person] | None:
            arg_19: Decoder_1[Array[Person]] = resize_array(decoder_3)
            object_arg_9: IOptionalGetter = get.Optional
            return object_arg_9.Field("Performers", arg_19)

        def _arrow3175(__unit: None=None) -> Array[Comment] | None:
            arg_21: Decoder_1[Array[Comment]] = resize_array(decoder_4)
            object_arg_10: IOptionalGetter = get.Optional
            return object_arg_10.Field("Comments", arg_21)

        return ArcRun.create(_arrow3165(), _arrow3166(), _arrow3167(), _arrow3168(), _arrow3169(), _arrow3170(), _arrow3171(), _arrow3172(), _arrow3173(), _arrow3174(), _arrow3175())

    return object(_arrow3176)


__all__ = ["encoder", "decoder", "encoder_compressed", "decoder_compressed"]

