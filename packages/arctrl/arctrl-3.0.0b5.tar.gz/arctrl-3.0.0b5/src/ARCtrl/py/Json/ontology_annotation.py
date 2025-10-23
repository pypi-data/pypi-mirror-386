from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (of_array, choose, FSharpList)
from ..fable_modules.fable_library.option import map as map_1
from ..fable_modules.fable_library.seq import (map as map_2, filter)
from ..fable_modules.fable_library.string_ import replace
from ..fable_modules.fable_library.types import (to_string, Array)
from ..fable_modules.fable_library.util import (int32_to_string, IEnumerable_1)
from ..fable_modules.thoth_json_core.decode import (one_of, map, int_1, float_1, string, object, IOptionalGetter, resize_array, IGetters)
from ..fable_modules.thoth_json_core.types import (Decoder_1, IEncodable, IEncoderHelpers_1)
from ..Core.comment import Comment
from ..Core.ontology_annotation import OntologyAnnotation
from ..Core.Process.column_index import order_name
from ..Core.uri import URIModule_toString
from .comment import (encoder, decoder, ROCrate_encoderDisambiguatingDescription, ROCrate_decoderDisambiguatingDescription)
from .context.rocrate.isa_ontology_annotation_context import context_jsonvalue
from .context.rocrate.property_value_context import context_jsonvalue as context_jsonvalue_1
from .encode import (try_include, try_include_seq)
from .idtable import encode
from .string_table import (encode_string, decode_string)

__A_ = TypeVar("__A_")

AnnotationValue_decoder: Decoder_1[str] = one_of(of_array([map(int32_to_string, int_1), map(to_string, float_1), string]))

def OntologyAnnotation_encoder(oa: OntologyAnnotation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map_1(mapping, tupled_arg[1])

    def _arrow2062(value: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2061(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2061()

    def _arrow2064(value_2: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2063(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr2063()

    def _arrow2066(value_4: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2065(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_4)

        return ObjectExpr2065()

    def _arrow2067(comment: Comment, oa: Any=oa) -> IEncodable:
        return encoder(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("annotationValue", _arrow2062, oa.Name), try_include("termSource", _arrow2064, oa.TermSourceREF), try_include("termAccession", _arrow2066, oa.TermAccessionNumber), try_include_seq("comments", _arrow2067, oa.Comments)]))
    class ObjectExpr2068(IEncodable):
        def Encode(self, helpers_3: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_3))

            arg: IEnumerable_1[tuple[str, __A_]] = map_2(mapping_1, values)
            return helpers_3.encode_object(arg)

    return ObjectExpr2068()


def _arrow2073(get: IGetters) -> OntologyAnnotation:
    def _arrow2069(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("annotationValue", AnnotationValue_decoder)

    def _arrow2070(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("termSource", string)

    def _arrow2071(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("termAccession", string)

    def _arrow2072(__unit: None=None) -> Array[Comment] | None:
        arg_7: Decoder_1[Array[Comment]] = resize_array(decoder)
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("comments", arg_7)

    return OntologyAnnotation.create(_arrow2069(), _arrow2070(), _arrow2071(), _arrow2072())


OntologyAnnotation_decoder: Decoder_1[OntologyAnnotation] = object(_arrow2073)

def OntologyAnnotation_compressedEncoder(string_table: Any, oa: OntologyAnnotation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], string_table: Any=string_table, oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map_1(mapping, tupled_arg[1])

    def _arrow2075(s: str, string_table: Any=string_table, oa: Any=oa) -> IEncodable:
        return encode_string(string_table, s)

    def _arrow2076(s_1: str, string_table: Any=string_table, oa: Any=oa) -> IEncodable:
        return encode_string(string_table, s_1)

    def _arrow2077(s_2: str, string_table: Any=string_table, oa: Any=oa) -> IEncodable:
        return encode_string(string_table, s_2)

    def _arrow2078(comment: Comment, string_table: Any=string_table, oa: Any=oa) -> IEncodable:
        return encoder(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("a", _arrow2075, oa.Name), try_include("ts", _arrow2076, oa.TermSourceREF), try_include("ta", _arrow2077, oa.TermAccessionNumber), try_include_seq("comments", _arrow2078, oa.Comments)]))
    class ObjectExpr2079(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any], string_table: Any=string_table, oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers))

            arg: IEnumerable_1[tuple[str, __A_]] = map_2(mapping_1, values)
            return helpers.encode_object(arg)

    return ObjectExpr2079()


def OntologyAnnotation_compressedDecoder(string_table: Array[str]) -> Decoder_1[OntologyAnnotation]:
    def _arrow2084(get: IGetters, string_table: Any=string_table) -> OntologyAnnotation:
        def _arrow2080(__unit: None=None) -> str | None:
            arg_1: Decoder_1[str] = decode_string(string_table)
            object_arg: IOptionalGetter = get.Optional
            return object_arg.Field("a", arg_1)

        def _arrow2081(__unit: None=None) -> str | None:
            arg_3: Decoder_1[str] = decode_string(string_table)
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("ts", arg_3)

        def _arrow2082(__unit: None=None) -> str | None:
            arg_5: Decoder_1[str] = decode_string(string_table)
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("ta", arg_5)

        def _arrow2083(__unit: None=None) -> Array[Comment] | None:
            arg_7: Decoder_1[Array[Comment]] = resize_array(decoder)
            object_arg_3: IOptionalGetter = get.Optional
            return object_arg_3.Field("comments", arg_7)

        return OntologyAnnotation(_arrow2080(), _arrow2081(), _arrow2082(), _arrow2083())

    return object(_arrow2084)


def OntologyAnnotation_ROCrate_genID(o: OntologyAnnotation) -> str:
    match_value: str | None = o.TermAccessionNumber
    if match_value is None:
        match_value_1: str | None = o.TermSourceREF
        if match_value_1 is None:
            match_value_2: str | None = o.Name
            if match_value_2 is None:
                return "#DummyOntologyAnnotation"

            else: 
                return "#UserTerm_" + replace(match_value_2, " ", "_")


        else: 
            return "#" + replace(match_value_1, " ", "_")


    else: 
        return URIModule_toString(match_value)



def OntologyAnnotation_ROCrate_encoderDefinedTerm(oa: OntologyAnnotation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map_1(mapping, tupled_arg[1])

    def _arrow2088(__unit: None=None, oa: Any=oa) -> IEncodable:
        value: str = OntologyAnnotation_ROCrate_genID(oa)
        class ObjectExpr2087(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2087()

    class ObjectExpr2089(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            return helpers_1.encode_string("OntologyAnnotation")

    def _arrow2091(value_2: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2090(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr2090()

    def _arrow2093(value_4: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2092(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_4)

        return ObjectExpr2092()

    def _arrow2095(value_6: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2094(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_6)

        return ObjectExpr2094()

    def _arrow2096(comment: Comment, oa: Any=oa) -> IEncodable:
        return ROCrate_encoderDisambiguatingDescription(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2088()), ("@type", ObjectExpr2089()), try_include("annotationValue", _arrow2091, oa.Name), try_include("termSource", _arrow2093, oa.TermSourceREF), try_include("termAccession", _arrow2095, oa.TermAccessionNumber), try_include_seq("comments", _arrow2096, oa.Comments), ("@context", context_jsonvalue)]))
    class ObjectExpr2097(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_5))

            arg: IEnumerable_1[tuple[str, __A_]] = map_2(mapping_1, values)
            return helpers_5.encode_object(arg)

    return ObjectExpr2097()


def _arrow2102(get: IGetters) -> OntologyAnnotation:
    def _arrow2098(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("annotationValue", AnnotationValue_decoder)

    def _arrow2099(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("termSource", string)

    def _arrow2100(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("termAccession", string)

    def _arrow2101(__unit: None=None) -> Array[Comment] | None:
        arg_7: Decoder_1[Array[Comment]] = resize_array(ROCrate_decoderDisambiguatingDescription)
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("comments", arg_7)

    return OntologyAnnotation.create(_arrow2098(), _arrow2099(), _arrow2100(), _arrow2101())


OntologyAnnotation_ROCrate_decoderDefinedTerm: Decoder_1[OntologyAnnotation] = object(_arrow2102)

def OntologyAnnotation_ROCrate_encoderPropertyValue(oa: OntologyAnnotation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map_1(mapping, tupled_arg[1])

    def _arrow2106(__unit: None=None, oa: Any=oa) -> IEncodable:
        value: str = OntologyAnnotation_ROCrate_genID(oa)
        class ObjectExpr2105(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2105()

    class ObjectExpr2107(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            return helpers_1.encode_string("PropertyValue")

    def _arrow2109(value_2: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2108(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr2108()

    def _arrow2111(value_4: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2110(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_4)

        return ObjectExpr2110()

    def _arrow2112(comment: Comment, oa: Any=oa) -> IEncodable:
        return ROCrate_encoderDisambiguatingDescription(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2106()), ("@type", ObjectExpr2107()), try_include("category", _arrow2109, oa.Name), try_include("categoryCode", _arrow2111, oa.TermAccessionNumber), try_include_seq("comments", _arrow2112, oa.Comments), ("@context", context_jsonvalue_1)]))
    class ObjectExpr2113(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_2(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr2113()


def _arrow2117(get: IGetters) -> OntologyAnnotation:
    def _arrow2114(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("category", string)

    def _arrow2115(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("categoryCode", string)

    def _arrow2116(__unit: None=None) -> Array[Comment] | None:
        arg_5: Decoder_1[Array[Comment]] = resize_array(ROCrate_decoderDisambiguatingDescription)
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("comments", arg_5)

    return OntologyAnnotation.create(_arrow2114(), None, _arrow2115(), _arrow2116())


OntologyAnnotation_ROCrate_decoderPropertyValue: Decoder_1[OntologyAnnotation] = object(_arrow2117)

def OntologyAnnotation_ISAJson_encoder(id_map: Any | None, oa: OntologyAnnotation) -> IEncodable:
    def f(oa_1: OntologyAnnotation, id_map: Any=id_map, oa: Any=oa) -> IEncodable:
        def predicate(c: Comment, oa_1: Any=oa_1) -> bool:
            match_value: str | None = c.Name
            (pattern_matching_result,) = (None,)
            if match_value is not None:
                if match_value == order_name:
                    pattern_matching_result = 0

                else: 
                    pattern_matching_result = 1


            else: 
                pattern_matching_result = 1

            if pattern_matching_result == 0:
                return False

            elif pattern_matching_result == 1:
                return True


        comments: IEnumerable_1[Comment] = filter(predicate, oa_1.Comments)
        def chooser(tupled_arg: tuple[str, IEncodable | None], oa_1: Any=oa_1) -> tuple[str, IEncodable] | None:
            def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
                return (tupled_arg[0], v_1)

            return map_1(mapping, tupled_arg[1])

        def _arrow2121(value: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2120(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                    return helpers.encode_string(value)

            return ObjectExpr2120()

        def _arrow2123(value_2: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2122(IEncodable):
                def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_1.encode_string(value_2)

            return ObjectExpr2122()

        def _arrow2125(value_4: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2124(IEncodable):
                def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_2.encode_string(value_4)

            return ObjectExpr2124()

        def _arrow2127(value_6: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2126(IEncodable):
                def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_3.encode_string(value_6)

            return ObjectExpr2126()

        def _arrow2128(comment: Comment, oa_1: Any=oa_1) -> IEncodable:
            return encoder(comment)

        values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("@id", _arrow2121, OntologyAnnotation_ROCrate_genID(oa_1)), try_include("annotationValue", _arrow2123, oa_1.Name), try_include("termSource", _arrow2125, oa_1.TermSourceREF), try_include("termAccession", _arrow2127, oa_1.TermAccessionNumber), try_include_seq("comments", _arrow2128, comments)]))
        class ObjectExpr2129(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any], oa_1: Any=oa_1) -> Any:
                def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                    return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

                arg: IEnumerable_1[tuple[str, __A_]] = map_2(mapping_1, values)
                return helpers_4.encode_object(arg)

        return ObjectExpr2129()

    if id_map is not None:
        def _arrow2130(o: OntologyAnnotation, id_map: Any=id_map, oa: Any=oa) -> str:
            return OntologyAnnotation_ROCrate_genID(o)

        return encode(_arrow2130, f, oa, id_map)

    else: 
        return f(oa)



OntologyAnnotation_ISAJson_decoder: Decoder_1[OntologyAnnotation] = OntologyAnnotation_decoder

__all__ = ["AnnotationValue_decoder", "OntologyAnnotation_encoder", "OntologyAnnotation_decoder", "OntologyAnnotation_compressedEncoder", "OntologyAnnotation_compressedDecoder", "OntologyAnnotation_ROCrate_genID", "OntologyAnnotation_ROCrate_encoderDefinedTerm", "OntologyAnnotation_ROCrate_decoderDefinedTerm", "OntologyAnnotation_ROCrate_encoderPropertyValue", "OntologyAnnotation_ROCrate_decoderPropertyValue", "OntologyAnnotation_ISAJson_encoder", "OntologyAnnotation_ISAJson_decoder"]

