from __future__ import annotations
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ..fable_modules.fable_library.option import map
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.string_ import replace
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IOptionalGetter, string, resize_array, IGetters)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.comment import Comment
from ..Core.ontology_source_reference import OntologySourceReference
from .comment import (encoder as encoder_1, decoder as decoder_1, ISAJson_encoder as ISAJson_encoder_1)
from .context.rocrate.isa_ontology_source_reference_context import context_jsonvalue
from .decode import Decode_uri
from .encode import (try_include, try_include_seq)

__A_ = TypeVar("__A_")

def encoder(osr: OntologySourceReference) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], osr: Any=osr) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2171(value: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2170(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2170()

    def _arrow2173(value_2: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2172(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr2172()

    def _arrow2175(value_4: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2174(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_4)

        return ObjectExpr2174()

    def _arrow2177(value_6: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2176(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_6)

        return ObjectExpr2176()

    def _arrow2178(comment: Comment, osr: Any=osr) -> IEncodable:
        return encoder_1(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("description", _arrow2171, osr.Description), try_include("file", _arrow2173, osr.File), try_include("name", _arrow2175, osr.Name), try_include("version", _arrow2177, osr.Version), try_include_seq("comments", _arrow2178, osr.Comments)]))
    class ObjectExpr2179(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], osr: Any=osr) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr2179()


def _arrow2185(get: IGetters) -> OntologySourceReference:
    def _arrow2180(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("description", Decode_uri)

    def _arrow2181(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("file", string)

    def _arrow2182(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("name", string)

    def _arrow2183(__unit: None=None) -> str | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("version", string)

    def _arrow2184(__unit: None=None) -> Array[Comment] | None:
        arg_9: Decoder_1[Array[Comment]] = resize_array(decoder_1)
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("comments", arg_9)

    return OntologySourceReference(_arrow2180(), _arrow2181(), _arrow2182(), _arrow2183(), _arrow2184())


decoder: Decoder_1[OntologySourceReference] = object(_arrow2185)

def ROCrate_genID(o: OntologySourceReference) -> str:
    match_value: str | None = o.File
    if match_value is None:
        match_value_1: str | None = o.Name
        if match_value_1 is None:
            return "#DummyOntologySourceRef"

        else: 
            return "#OntologySourceRef_" + replace(match_value_1, " ", "_")


    else: 
        return match_value



def ROCrate_encoder(osr: OntologySourceReference) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], osr: Any=osr) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2189(__unit: None=None, osr: Any=osr) -> IEncodable:
        value: str = ROCrate_genID(osr)
        class ObjectExpr2188(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2188()

    class ObjectExpr2190(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], osr: Any=osr) -> Any:
            return helpers_1.encode_string("OntologySourceReference")

    def _arrow2192(value_2: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2191(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr2191()

    def _arrow2194(value_4: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2193(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_4)

        return ObjectExpr2193()

    def _arrow2196(value_6: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2195(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_6)

        return ObjectExpr2195()

    def _arrow2198(value_8: str, osr: Any=osr) -> IEncodable:
        class ObjectExpr2197(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_8)

        return ObjectExpr2197()

    def _arrow2199(comment: Comment, osr: Any=osr) -> IEncodable:
        return encoder_1(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2189()), ("@type", ObjectExpr2190()), try_include("description", _arrow2192, osr.Description), try_include("file", _arrow2194, osr.File), try_include("name", _arrow2196, osr.Name), try_include("version", _arrow2198, osr.Version), try_include_seq("comments", _arrow2199, osr.Comments), ("@context", context_jsonvalue)]))
    class ObjectExpr2200(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], osr: Any=osr) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr2200()


def _arrow2206(get: IGetters) -> OntologySourceReference:
    def _arrow2201(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("description", Decode_uri)

    def _arrow2202(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("file", string)

    def _arrow2203(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("name", string)

    def _arrow2204(__unit: None=None) -> str | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("version", string)

    def _arrow2205(__unit: None=None) -> Array[Comment] | None:
        arg_9: Decoder_1[Array[Comment]] = resize_array(decoder_1)
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("comments", arg_9)

    return OntologySourceReference(_arrow2201(), _arrow2202(), _arrow2203(), _arrow2204(), _arrow2205())


ROCrate_decoder: Decoder_1[OntologySourceReference] = object(_arrow2206)

def ISAJson_encoder(id_map: Any | None, osr: OntologySourceReference) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], id_map: Any=id_map, osr: Any=osr) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2210(value: str, id_map: Any=id_map, osr: Any=osr) -> IEncodable:
        class ObjectExpr2209(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2209()

    def _arrow2212(value_2: str, id_map: Any=id_map, osr: Any=osr) -> IEncodable:
        class ObjectExpr2211(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr2211()

    def _arrow2214(value_4: str, id_map: Any=id_map, osr: Any=osr) -> IEncodable:
        class ObjectExpr2213(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_4)

        return ObjectExpr2213()

    def _arrow2216(value_6: str, id_map: Any=id_map, osr: Any=osr) -> IEncodable:
        class ObjectExpr2215(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_6)

        return ObjectExpr2215()

    def _arrow2217(comment: Comment, id_map: Any=id_map, osr: Any=osr) -> IEncodable:
        return ISAJson_encoder_1(id_map, comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("description", _arrow2210, osr.Description), try_include("file", _arrow2212, osr.File), try_include("name", _arrow2214, osr.Name), try_include("version", _arrow2216, osr.Version), try_include_seq("comments", _arrow2217, osr.Comments)]))
    class ObjectExpr2218(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], id_map: Any=id_map, osr: Any=osr) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr2218()


ISAJson_decoder: Decoder_1[OntologySourceReference] = decoder

__all__ = ["encoder", "decoder", "ROCrate_genID", "ROCrate_encoder", "ROCrate_decoder", "ISAJson_encoder", "ISAJson_decoder"]

