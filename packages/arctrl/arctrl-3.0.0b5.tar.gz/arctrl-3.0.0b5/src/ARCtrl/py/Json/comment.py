from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ..fable_modules.fable_library.option import (map, value as value_6)
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.string_ import replace
from ..fable_modules.fable_library.types import to_string
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IOptionalGetter, string, IGetters, map as map_2)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.comment import Comment
from .context.rocrate.isa_comment_context import context_jsonvalue
from .encode import try_include
from .idtable import encode

__A_ = TypeVar("__A_")

def encoder(comment: Comment) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], comment: Any=comment) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2028(value: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2027(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2027()

    def _arrow2030(value_2: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2029(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr2029()

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("name", _arrow2028, comment.Name), try_include("value", _arrow2030, comment.Value)]))
    class ObjectExpr2031(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_2))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_2.encode_object(arg)

    return ObjectExpr2031()


def _arrow2034(get: IGetters) -> Comment:
    def _arrow2032(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("name", string)

    def _arrow2033(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("value", string)

    return Comment(_arrow2032(), _arrow2033())


decoder: Decoder_1[Comment] = object(_arrow2034)

def ROCrate_genID(c: Comment) -> str:
    match_value: str | None = c.Name
    if match_value is None:
        return "#EmptyComment"

    else: 
        n: str = match_value
        v: str = ("_" + replace(value_6(c.Value), " ", "_")) if (c.Value is not None) else ""
        return ("#Comment_" + replace(n, " ", "_")) + v



def ROCrate_encoder(comment: Comment) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], comment: Any=comment) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2038(__unit: None=None, comment: Any=comment) -> IEncodable:
        value: str = ROCrate_genID(comment)
        class ObjectExpr2037(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2037()

    class ObjectExpr2039(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            return helpers_1.encode_string("Comment")

    def _arrow2041(value_2: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2040(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr2040()

    def _arrow2043(value_4: str, comment: Any=comment) -> IEncodable:
        class ObjectExpr2042(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_4)

        return ObjectExpr2042()

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2038()), ("@type", ObjectExpr2039()), try_include("name", _arrow2041, comment.Name), try_include("value", _arrow2043, comment.Value), ("@context", context_jsonvalue)]))
    class ObjectExpr2044(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr2044()


def _arrow2047(get: IGetters) -> Comment:
    def _arrow2045(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("name", string)

    def _arrow2046(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("value", string)

    return Comment(_arrow2045(), _arrow2046())


ROCrate_decoder: Decoder_1[Comment] = object(_arrow2047)

def ROCrate_encoderDisambiguatingDescription(comment: Comment) -> IEncodable:
    value: str = to_string(comment)
    class ObjectExpr2048(IEncodable):
        def Encode(self, helpers: IEncoderHelpers_1[Any], comment: Any=comment) -> Any:
            return helpers.encode_string(value)

    return ObjectExpr2048()


def ctor(s: str) -> Comment:
    return Comment.from_string(s)


ROCrate_decoderDisambiguatingDescription: Decoder_1[Comment] = map_2(ctor, string)

def ISAJson_encoder(id_map: Any | None, comment: Comment) -> IEncodable:
    def f(comment_1: Comment, id_map: Any=id_map, comment: Any=comment) -> IEncodable:
        def chooser(tupled_arg: tuple[str, IEncodable | None], comment_1: Any=comment_1) -> tuple[str, IEncodable] | None:
            def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
                return (tupled_arg[0], v_1)

            return map(mapping, tupled_arg[1])

        def _arrow2052(value: str, comment_1: Any=comment_1) -> IEncodable:
            class ObjectExpr2051(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                    return helpers.encode_string(value)

            return ObjectExpr2051()

        def _arrow2054(value_2: str, comment_1: Any=comment_1) -> IEncodable:
            class ObjectExpr2053(IEncodable):
                def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_1.encode_string(value_2)

            return ObjectExpr2053()

        def _arrow2056(value_4: str, comment_1: Any=comment_1) -> IEncodable:
            class ObjectExpr2055(IEncodable):
                def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_2.encode_string(value_4)

            return ObjectExpr2055()

        values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("@id", _arrow2052, ROCrate_genID(comment_1)), try_include("name", _arrow2054, comment_1.Name), try_include("value", _arrow2056, comment_1.Value)]))
        class ObjectExpr2057(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any], comment_1: Any=comment_1) -> Any:
                def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                    return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_3))

                arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
                return helpers_3.encode_object(arg)

        return ObjectExpr2057()

    if id_map is None:
        return f(comment)

    else: 
        def _arrow2058(c: Comment, id_map: Any=id_map, comment: Any=comment) -> str:
            return ROCrate_genID(c)

        return encode(_arrow2058, f, comment, id_map)



ISAJson_decoder: Decoder_1[Comment] = decoder

__all__ = ["encoder", "decoder", "ROCrate_genID", "ROCrate_encoder", "ROCrate_decoder", "ROCrate_encoderDisambiguatingDescription", "ROCrate_decoderDisambiguatingDescription", "ISAJson_encoder", "ISAJson_decoder"]

