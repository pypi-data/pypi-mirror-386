from __future__ import annotations
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ..fable_modules.fable_library.option import map
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IRequiredGetter, string, IOptionalGetter, resize_array, IGetters)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.arc_types import (ArcWorkflow__get_Identifier, ArcWorkflow__get_WorkflowType, ArcWorkflow__get_Title, ArcWorkflow__get_URI, ArcWorkflow__get_Description, ArcWorkflow__get_Version, ArcWorkflow__get_DataMap, ArcWorkflow__get_SubWorkflowIdentifiers, ArcWorkflow__get_Parameters, ArcWorkflow__get_Components, ArcWorkflow__get_Contacts, ArcWorkflow__get_Comments, ArcWorkflow, ArcWorkflow_create_Z3BB02240)
from ..Core.comment import Comment
from ..Core.data_map import DataMap
from ..Core.ontology_annotation import OntologyAnnotation
from ..Core.person import Person
from ..Core.Process.component import Component
from ..Core.Process.protocol_parameter import ProtocolParameter
from ..Core.Table.composite_cell import CompositeCell
from .comment import (encoder as encoder_5, decoder as decoder_5)
from .DataMap.data_map import (encoder as encoder_1, decoder as decoder_3, encoder_compressed as encoder_compressed_1, decoder_compressed as decoder_compressed_1)
from .encode import (try_include, try_include_seq)
from .ontology_annotation import (OntologyAnnotation_encoder, OntologyAnnotation_decoder)
from .person import (encoder as encoder_4, decoder as decoder_4)
from .Process.component import (encoder as encoder_3, decoder as decoder_2)
from .Process.protocol_parameter import (encoder as encoder_2, decoder as decoder_1)

__A_ = TypeVar("__A_")

def encoder(workflow: ArcWorkflow) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], workflow: Any=workflow) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3052(__unit: None=None, workflow: Any=workflow) -> IEncodable:
        value: str = ArcWorkflow__get_Identifier(workflow)
        class ObjectExpr3051(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3051()

    def _arrow3053(oa: OntologyAnnotation, workflow: Any=workflow) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def _arrow3055(value_1: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3054(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3054()

    def _arrow3057(value_3: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3056(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3056()

    def _arrow3059(value_5: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3058(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3058()

    def _arrow3061(value_7: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3060(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_7)

        return ObjectExpr3060()

    def _arrow3062(dm: DataMap, workflow: Any=workflow) -> IEncodable:
        return encoder_1(dm)

    def _arrow3064(value_9: str, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3063(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_9)

        return ObjectExpr3063()

    def _arrow3065(value_11: ProtocolParameter, workflow: Any=workflow) -> IEncodable:
        return encoder_2(value_11)

    def _arrow3066(value_12: Component, workflow: Any=workflow) -> IEncodable:
        return encoder_3(value_12)

    def _arrow3067(person: Person, workflow: Any=workflow) -> IEncodable:
        return encoder_4(person)

    def _arrow3068(comment: Comment, workflow: Any=workflow) -> IEncodable:
        return encoder_5(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3052()), try_include("WorkflowType", _arrow3053, ArcWorkflow__get_WorkflowType(workflow)), try_include("Title", _arrow3055, ArcWorkflow__get_Title(workflow)), try_include("URI", _arrow3057, ArcWorkflow__get_URI(workflow)), try_include("Description", _arrow3059, ArcWorkflow__get_Description(workflow)), try_include("Version", _arrow3061, ArcWorkflow__get_Version(workflow)), try_include("DataMap", _arrow3062, ArcWorkflow__get_DataMap(workflow)), try_include_seq("SubWorkflowIdentifiers", _arrow3064, ArcWorkflow__get_SubWorkflowIdentifiers(workflow)), try_include_seq("Parameters", _arrow3065, ArcWorkflow__get_Parameters(workflow)), try_include_seq("Components", _arrow3066, ArcWorkflow__get_Components(workflow)), try_include_seq("Contacts", _arrow3067, ArcWorkflow__get_Contacts(workflow)), try_include_seq("Comments", _arrow3068, ArcWorkflow__get_Comments(workflow))]))
    class ObjectExpr3069(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], workflow: Any=workflow) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr3069()


def _arrow3082(get: IGetters) -> ArcWorkflow:
    def _arrow3070(__unit: None=None) -> str:
        object_arg: IRequiredGetter = get.Required
        return object_arg.Field("Identifier", string)

    def _arrow3071(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("Title", string)

    def _arrow3072(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("Description", string)

    def _arrow3073(__unit: None=None) -> OntologyAnnotation | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("WorkflowType", OntologyAnnotation_decoder)

    def _arrow3074(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("URI", string)

    def _arrow3075(__unit: None=None) -> str | None:
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("Version", string)

    def _arrow3076(__unit: None=None) -> Array[str] | None:
        arg_13: Decoder_1[Array[str]] = resize_array(string)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("SubWorkflowIdentifiers", arg_13)

    def _arrow3077(__unit: None=None) -> Array[ProtocolParameter] | None:
        arg_15: Decoder_1[Array[ProtocolParameter]] = resize_array(decoder_1)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("Parameters", arg_15)

    def _arrow3078(__unit: None=None) -> Array[Component] | None:
        arg_17: Decoder_1[Array[Component]] = resize_array(decoder_2)
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("Components", arg_17)

    def _arrow3079(__unit: None=None) -> DataMap | None:
        object_arg_9: IOptionalGetter = get.Optional
        return object_arg_9.Field("DataMap", decoder_3)

    def _arrow3080(__unit: None=None) -> Array[Person] | None:
        arg_21: Decoder_1[Array[Person]] = resize_array(decoder_4)
        object_arg_10: IOptionalGetter = get.Optional
        return object_arg_10.Field("Contacts", arg_21)

    def _arrow3081(__unit: None=None) -> Array[Comment] | None:
        arg_23: Decoder_1[Array[Comment]] = resize_array(decoder_5)
        object_arg_11: IOptionalGetter = get.Optional
        return object_arg_11.Field("Comments", arg_23)

    return ArcWorkflow_create_Z3BB02240(_arrow3070(), _arrow3071(), _arrow3072(), _arrow3073(), _arrow3074(), _arrow3075(), _arrow3076(), _arrow3077(), _arrow3078(), _arrow3079(), _arrow3080(), _arrow3081())


decoder: Decoder_1[ArcWorkflow] = object(_arrow3082)

def encoder_compressed(string_table: Any, oa_table: Any, cell_table: Any, workflow: ArcWorkflow) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3086(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        value: str = ArcWorkflow__get_Identifier(workflow)
        class ObjectExpr3085(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3085()

    def _arrow3087(oa: OntologyAnnotation, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return OntologyAnnotation_encoder(oa)

    def _arrow3089(value_1: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3088(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3088()

    def _arrow3091(value_3: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3090(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3090()

    def _arrow3093(value_5: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3092(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3092()

    def _arrow3095(value_7: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3094(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_7)

        return ObjectExpr3094()

    def _arrow3096(dm: DataMap, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_compressed_1(string_table, oa_table, cell_table, dm)

    def _arrow3098(value_9: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        class ObjectExpr3097(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_9)

        return ObjectExpr3097()

    def _arrow3101(value_11: ProtocolParameter, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_2(value_11)

    def _arrow3102(value_12: Component, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_3(value_12)

    def _arrow3105(person: Person, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_4(person)

    def _arrow3108(comment: Comment, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> IEncodable:
        return encoder_5(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3086()), try_include("WorkflowType", _arrow3087, ArcWorkflow__get_WorkflowType(workflow)), try_include("Title", _arrow3089, ArcWorkflow__get_Title(workflow)), try_include("URI", _arrow3091, ArcWorkflow__get_URI(workflow)), try_include("Description", _arrow3093, ArcWorkflow__get_Description(workflow)), try_include("Version", _arrow3095, ArcWorkflow__get_Version(workflow)), try_include("DataMap", _arrow3096, ArcWorkflow__get_DataMap(workflow)), try_include_seq("SubWorkflowIdentifiers", _arrow3098, ArcWorkflow__get_SubWorkflowIdentifiers(workflow)), try_include_seq("Parameters", _arrow3101, ArcWorkflow__get_Parameters(workflow)), try_include_seq("Components", _arrow3102, ArcWorkflow__get_Components(workflow)), try_include_seq("Contacts", _arrow3105, ArcWorkflow__get_Contacts(workflow)), try_include_seq("Comments", _arrow3108, ArcWorkflow__get_Comments(workflow))]))
    class ObjectExpr3113(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, workflow: Any=workflow) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr3113()


def decoder_compressed(string_table: Array[str], oa_table: Array[OntologyAnnotation], cell_table: Array[CompositeCell]) -> Decoder_1[ArcWorkflow]:
    def _arrow3137(get: IGetters, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ArcWorkflow:
        def _arrow3120(__unit: None=None) -> str:
            object_arg: IRequiredGetter = get.Required
            return object_arg.Field("Identifier", string)

        def _arrow3122(__unit: None=None) -> str | None:
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("Title", string)

        def _arrow3123(__unit: None=None) -> str | None:
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("Description", string)

        def _arrow3124(__unit: None=None) -> OntologyAnnotation | None:
            object_arg_3: IOptionalGetter = get.Optional
            return object_arg_3.Field("WorkflowType", OntologyAnnotation_decoder)

        def _arrow3125(__unit: None=None) -> str | None:
            object_arg_4: IOptionalGetter = get.Optional
            return object_arg_4.Field("URI", string)

        def _arrow3126(__unit: None=None) -> str | None:
            object_arg_5: IOptionalGetter = get.Optional
            return object_arg_5.Field("Version", string)

        def _arrow3128(__unit: None=None) -> Array[str] | None:
            arg_13: Decoder_1[Array[str]] = resize_array(string)
            object_arg_6: IOptionalGetter = get.Optional
            return object_arg_6.Field("SubWorkflowIdentifiers", arg_13)

        def _arrow3129(__unit: None=None) -> Array[ProtocolParameter] | None:
            arg_15: Decoder_1[Array[ProtocolParameter]] = resize_array(decoder_1)
            object_arg_7: IOptionalGetter = get.Optional
            return object_arg_7.Field("Parameters", arg_15)

        def _arrow3130(__unit: None=None) -> Array[Component] | None:
            arg_17: Decoder_1[Array[Component]] = resize_array(decoder_2)
            object_arg_8: IOptionalGetter = get.Optional
            return object_arg_8.Field("Components", arg_17)

        def _arrow3131(__unit: None=None) -> DataMap | None:
            arg_19: Decoder_1[DataMap] = decoder_compressed_1(string_table, oa_table, cell_table)
            object_arg_9: IOptionalGetter = get.Optional
            return object_arg_9.Field("DataMap", arg_19)

        def _arrow3133(__unit: None=None) -> Array[Person] | None:
            arg_21: Decoder_1[Array[Person]] = resize_array(decoder_4)
            object_arg_10: IOptionalGetter = get.Optional
            return object_arg_10.Field("Contacts", arg_21)

        def _arrow3136(__unit: None=None) -> Array[Comment] | None:
            arg_23: Decoder_1[Array[Comment]] = resize_array(decoder_5)
            object_arg_11: IOptionalGetter = get.Optional
            return object_arg_11.Field("Comments", arg_23)

        return ArcWorkflow_create_Z3BB02240(_arrow3120(), _arrow3122(), _arrow3123(), _arrow3124(), _arrow3125(), _arrow3126(), _arrow3128(), _arrow3129(), _arrow3130(), _arrow3131(), _arrow3133(), _arrow3136())

    return object(_arrow3137)


__all__ = ["encoder", "decoder", "encoder_compressed", "decoder_compressed"]

