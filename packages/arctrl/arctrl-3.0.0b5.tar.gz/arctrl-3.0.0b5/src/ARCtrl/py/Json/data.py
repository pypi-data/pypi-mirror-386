from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList, singleton)
from ..fable_modules.fable_library.option import map
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.string_ import replace
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IOptionalGetter, string, resize_array, IGetters)
from ..fable_modules.thoth_json_core.encode import list_1 as list_1_1
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.comment import Comment
from ..Core.data import Data
from ..Core.data_file import DataFile
from ..Core.uri import URIModule_toString
from .comment import (encoder as encoder_1, decoder as decoder_1, ROCrate_encoder as ROCrate_encoder_2, ROCrate_decoder as ROCrate_decoder_2, ISAJson_encoder as ISAJson_encoder_2, ISAJson_decoder as ISAJson_decoder_2)
from .context.rocrate.isa_data_context import context_jsonvalue
from .data_file import (ISAJson_encoder as ISAJson_encoder_1, ISAJson_decoder as ISAJson_decoder_1, ROCrate_encoder as ROCrate_encoder_1, ROCrate_decoder as ROCrate_decoder_1)
from .decode import (Decode_uri, Decode_objectNoAdditionalProperties)
from .encode import (try_include, try_include_seq)
from .idtable import encode
from .string_table import (encode_string, decode_string)

__A_ = TypeVar("__A_")

def encoder(d: Data) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], d: Any=d) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2222(value: str, d: Any=d) -> IEncodable:
        class ObjectExpr2221(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2221()

    def _arrow2224(value_2: str, d: Any=d) -> IEncodable:
        class ObjectExpr2223(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr2223()

    def _arrow2226(value_4: str, d: Any=d) -> IEncodable:
        class ObjectExpr2225(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_4)

        return ObjectExpr2225()

    def _arrow2228(value_6: str, d: Any=d) -> IEncodable:
        class ObjectExpr2227(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_6)

        return ObjectExpr2227()

    def _arrow2229(comment: Comment, d: Any=d) -> IEncodable:
        return encoder_1(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("@id", _arrow2222, d.ID), try_include("name", _arrow2224, d.Name), try_include("dataType", ISAJson_encoder_1, d.DataType), try_include("format", _arrow2226, d.Format), try_include("selectorFormat", _arrow2228, d.SelectorFormat), try_include_seq("comments", _arrow2229, d.Comments)]))
    class ObjectExpr2230(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], d: Any=d) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr2230()


def _arrow2237(get: IGetters) -> Data:
    def _arrow2231(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("@id", Decode_uri)

    def _arrow2232(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("name", string)

    def _arrow2233(__unit: None=None) -> DataFile | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("dataType", ISAJson_decoder_1)

    def _arrow2234(__unit: None=None) -> str | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("format", string)

    def _arrow2235(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("selectorFormat", Decode_uri)

    def _arrow2236(__unit: None=None) -> Array[Comment] | None:
        arg_11: Decoder_1[Array[Comment]] = resize_array(decoder_1)
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("comments", arg_11)

    return Data(_arrow2231(), _arrow2232(), _arrow2233(), _arrow2234(), _arrow2235(), _arrow2236())


decoder: Decoder_1[Data] = object(_arrow2237)

def compressed_encoder(string_table: Any, d: Data) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], string_table: Any=string_table, d: Any=d) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2239(s: str, string_table: Any=string_table, d: Any=d) -> IEncodable:
        return encode_string(string_table, s)

    def _arrow2240(s_1: str, string_table: Any=string_table, d: Any=d) -> IEncodable:
        return encode_string(string_table, s_1)

    def _arrow2241(s_2: str, string_table: Any=string_table, d: Any=d) -> IEncodable:
        return encode_string(string_table, s_2)

    def _arrow2242(s_3: str, string_table: Any=string_table, d: Any=d) -> IEncodable:
        return encode_string(string_table, s_3)

    def _arrow2243(comment: Comment, string_table: Any=string_table, d: Any=d) -> IEncodable:
        return encoder_1(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("i", _arrow2239, d.ID), try_include("n", _arrow2240, d.Name), try_include("d", ISAJson_encoder_1, d.DataType), try_include("f", _arrow2241, d.Format), try_include("s", _arrow2242, d.SelectorFormat), try_include_seq("c", _arrow2243, d.Comments)]))
    class ObjectExpr2244(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any], string_table: Any=string_table, d: Any=d) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers.encode_object(arg)

    return ObjectExpr2244()


def compressed_decoder(string_table: Array[str]) -> Decoder_1[Data]:
    def _arrow2251(get: IGetters, string_table: Any=string_table) -> Data:
        def _arrow2245(__unit: None=None) -> str | None:
            arg_1: Decoder_1[str] = decode_string(string_table)
            object_arg: IOptionalGetter = get.Optional
            return object_arg.Field("i", arg_1)

        def _arrow2246(__unit: None=None) -> str | None:
            arg_3: Decoder_1[str] = decode_string(string_table)
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("n", arg_3)

        def _arrow2247(__unit: None=None) -> DataFile | None:
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("d", ISAJson_decoder_1)

        def _arrow2248(__unit: None=None) -> str | None:
            arg_7: Decoder_1[str] = decode_string(string_table)
            object_arg_3: IOptionalGetter = get.Optional
            return object_arg_3.Field("f", arg_7)

        def _arrow2249(__unit: None=None) -> str | None:
            arg_9: Decoder_1[str] = decode_string(string_table)
            object_arg_4: IOptionalGetter = get.Optional
            return object_arg_4.Field("s", arg_9)

        def _arrow2250(__unit: None=None) -> Array[Comment] | None:
            arg_11: Decoder_1[Array[Comment]] = resize_array(decoder_1)
            object_arg_5: IOptionalGetter = get.Optional
            return object_arg_5.Field("c", arg_11)

        return Data(_arrow2245(), _arrow2246(), _arrow2247(), _arrow2248(), _arrow2249(), _arrow2250())

    return object(_arrow2251)


def ROCrate_genID(d: Data) -> str:
    match_value: str | None = d.ID
    if match_value is None:
        match_value_1: str | None = d.Name
        if match_value_1 is None:
            return "#EmptyData"

        else: 
            return replace(match_value_1, " ", "_")


    else: 
        return URIModule_toString(match_value)



def ROCrate_encoder(oa: Data) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2255(__unit: None=None, oa: Any=oa) -> IEncodable:
        value: str = ROCrate_genID(oa)
        class ObjectExpr2254(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2254()

    class ObjectExpr2256(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            return helpers_1.encode_string("Data")

    def _arrow2258(value_2: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2257(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr2257()

    def _arrow2259(value_4: DataFile, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_1(value_4)

    def _arrow2261(value_5: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2260(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr2260()

    def _arrow2263(value_7: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr2262(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_7)

        return ObjectExpr2262()

    def _arrow2264(comment: Comment, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_2(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2255()), ("@type", list_1_1(singleton(ObjectExpr2256()))), try_include("name", _arrow2258, oa.Name), try_include("type", _arrow2259, oa.DataType), try_include("encodingFormat", _arrow2261, oa.Format), try_include("usageInfo", _arrow2263, oa.SelectorFormat), try_include_seq("comments", _arrow2264, oa.Comments), ("@context", context_jsonvalue)]))
    class ObjectExpr2265(IEncodable):
        def Encode(self, helpers_5: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_5))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_5.encode_object(arg)

    return ObjectExpr2265()


def _arrow2272(get: IGetters) -> Data:
    def _arrow2266(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("@id", Decode_uri)

    def _arrow2267(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("name", string)

    def _arrow2268(__unit: None=None) -> DataFile | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("type", ROCrate_decoder_1)

    def _arrow2269(__unit: None=None) -> str | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("encodingFormat", string)

    def _arrow2270(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("usageInfo", Decode_uri)

    def _arrow2271(__unit: None=None) -> Array[Comment] | None:
        arg_11: Decoder_1[Array[Comment]] = resize_array(ROCrate_decoder_2)
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("comments", arg_11)

    return Data(_arrow2266(), _arrow2267(), _arrow2268(), _arrow2269(), _arrow2270(), _arrow2271())


ROCrate_decoder: Decoder_1[Data] = object(_arrow2272)

def ISAJson_encoder(id_map: Any | None, oa: Data) -> IEncodable:
    def f(oa_1: Data, id_map: Any=id_map, oa: Any=oa) -> IEncodable:
        def chooser(tupled_arg: tuple[str, IEncodable | None], oa_1: Any=oa_1) -> tuple[str, IEncodable] | None:
            def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
                return (tupled_arg[0], v_1)

            return map(mapping, tupled_arg[1])

        def _arrow2276(value: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2275(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                    return helpers.encode_string(value)

            return ObjectExpr2275()

        def _arrow2278(value_2: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2277(IEncodable):
                def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_1.encode_string(value_2)

            return ObjectExpr2277()

        def _arrow2279(comment: Comment, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder_2(id_map, comment)

        values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("@id", _arrow2276, ROCrate_genID(oa_1)), try_include("name", _arrow2278, oa_1.Name), try_include("type", ISAJson_encoder_1, oa_1.DataType), try_include_seq("comments", _arrow2279, oa_1.Comments)]))
        class ObjectExpr2280(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any], oa_1: Any=oa_1) -> Any:
                def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                    return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_2))

                arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
                return helpers_2.encode_object(arg)

        return ObjectExpr2280()

    if id_map is not None:
        def _arrow2281(d_1: Data, id_map: Any=id_map, oa: Any=oa) -> str:
            return ROCrate_genID(d_1)

        return encode(_arrow2281, f, oa, id_map)

    else: 
        return f(oa)



ISAJson_allowedFields: FSharpList[str] = of_array(["@id", "name", "type", "comments", "@type", "@context"])

def _arrow2286(get: IGetters) -> Data:
    def _arrow2282(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("@id", Decode_uri)

    def _arrow2283(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("name", string)

    def _arrow2284(__unit: None=None) -> DataFile | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("type", ISAJson_decoder_1)

    def _arrow2285(__unit: None=None) -> Array[Comment] | None:
        arg_7: Decoder_1[Array[Comment]] = resize_array(ISAJson_decoder_2)
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("comments", arg_7)

    return Data(_arrow2282(), _arrow2283(), _arrow2284(), None, None, _arrow2285())


ISAJson_decoder: Decoder_1[Data] = Decode_objectNoAdditionalProperties(ISAJson_allowedFields, _arrow2286)

__all__ = ["encoder", "decoder", "compressed_encoder", "compressed_decoder", "ROCrate_genID", "ROCrate_encoder", "ROCrate_decoder", "ISAJson_encoder", "ISAJson_allowedFields", "ISAJson_decoder"]

