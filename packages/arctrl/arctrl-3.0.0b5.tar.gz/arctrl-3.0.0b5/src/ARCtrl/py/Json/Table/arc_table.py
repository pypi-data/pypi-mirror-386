from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ...fable_modules.fable_library.array_ import (iterate_indexed, fold, fill)
from ...fable_modules.fable_library.list import (FSharpList, empty as empty_1, of_array)
from ...fable_modules.fable_library.map import empty as empty_2
from ...fable_modules.fable_library.map_util import get_item_from_dict
from ...fable_modules.fable_library.mutable_map import Dictionary
from ...fable_modules.fable_library.option import default_arg
from ...fable_modules.fable_library.result import FSharpResult_2
from ...fable_modules.fable_library.seq import (to_list, delay, append, singleton, map, empty)
from ...fable_modules.fable_library.types import Array
from ...fable_modules.fable_library.util import (IEnumerable_1, compare_arrays, equal_arrays, array_hash, get_enumerator, dispose, int32_to_string, ignore)
from ...fable_modules.thoth_json_core.decode import (object, list_1 as list_1_1, IOptionalGetter, map_0027, tuple2, int_1, IRequiredGetter, string, IGetters, map as map_1, resize_array, array as array_1, Helpers_prependPath)
from ...fable_modules.thoth_json_core.encode import list_1
from ...fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1, IDecoderHelpers_1, ErrorReason_1)
from ...Core.ontology_annotation import OntologyAnnotation
from ...Core.Table.arc_table import ArcTable
from ...Core.Table.arc_table_aux import (ColumnValueRefs, ensure_cell_hash_in_value_map, ArcTableValues, Unchecked_setCellAt)
from ...Core.Table.composite_cell import CompositeCell
from ...Core.Table.composite_header import CompositeHeader
from ..decode import (Decode_tryOneOf, Decode_intDictionary, Decode_dictionary)
from ..encode import int_dictionary
from ..string_table import (encode_string, decode_string)
from .cell_table import (decode_cell, encode_cell)
from .composite_cell import (encoder as encoder_1, decoder as decoder_3)
from .composite_header import (encoder as encoder_2, decoder as decoder_2)

__A_ = TypeVar("__A_")

_VALUE_ = TypeVar("_VALUE_")

_VALUE = TypeVar("_VALUE")

def encoder(table: ArcTable) -> IEncodable:
    value_map: Any = table.Values.ValueMap
    def cell_encoder(hash_1: int, table: Any=table) -> IEncodable:
        return encoder_1(get_item_from_dict(value_map, hash_1))

    def _arrow2837(__unit: None=None, table: Any=table) -> IEnumerable_1[tuple[str, IEncodable]]:
        def _arrow2830(__unit: None=None) -> IEncodable:
            value: str = table.Name
            class ObjectExpr2829(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                    return helpers.encode_string(value)

            return ObjectExpr2829()

        def _arrow2836(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
            def _arrow2831(__unit: None=None) -> IEnumerable_1[IEncodable]:
                return map(encoder_2, table.Headers)

            def _arrow2835(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                def column_encoder(col: ColumnValueRefs) -> IEncodable:
                    if col.tag == 1:
                        return int_dictionary(cell_encoder, col.fields[0])

                    else: 
                        return cell_encoder(col.fields[0])


                def _arrow2834(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                    def _arrow2833(__unit: None=None) -> IEncodable:
                        value_1: int = table.RowCount or 0
                        class ObjectExpr2832(IEncodable):
                            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                                return helpers_1.encode_signed_integral_number(value_1)

                        return ObjectExpr2832()

                    return singleton(("rowCount", _arrow2833()))

                return append(singleton(("columns", int_dictionary(column_encoder, table.Values.Columns))), delay(_arrow2834)) if (table.Values.RowCount != 0) else empty()

            return append(singleton(("headers", list_1(to_list(delay(_arrow2831))))) if (len(table.Headers) != 0) else empty(), delay(_arrow2835))

        return append(singleton(("name", _arrow2830())), delay(_arrow2836))

    values: IEnumerable_1[tuple[str, IEncodable]] = to_list(delay(_arrow2837))
    class ObjectExpr2838(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any], table: Any=table) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_2))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_2.encode_object(arg)

    return ObjectExpr2838()


def _arrow2847(get: IGetters) -> ArcTable:
    def _arrow2839(__unit: None=None) -> FSharpList[CompositeHeader] | None:
        arg_1: Decoder_1[FSharpList[CompositeHeader]] = list_1_1(decoder_2)
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("header", arg_1)

    decoded_header: Array[CompositeHeader] = list(default_arg(_arrow2839(), empty_1()))
    def _arrow2840(__unit: None=None) -> Any | None:
        arg_3: Decoder_1[Any] = map_0027(tuple2(int_1, int_1), decoder_3)
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("values", arg_3)

    class ObjectExpr2841:
        @property
        def Compare(self) -> Callable[[tuple[int, int], tuple[int, int]], int]:
            return compare_arrays

    class ObjectExpr2842:
        @property
        def Equals(self) -> Callable[[tuple[int, int], tuple[int, int]], bool]:
            return equal_arrays

        @property
        def GetHashCode(self) -> Callable[[tuple[int, int]], int]:
            return array_hash

    decoded_values: Any = Dictionary(default_arg(_arrow2840(), empty_2(ObjectExpr2841())), ObjectExpr2842())
    def _arrow2843(__unit: None=None) -> str:
        object_arg_2: IRequiredGetter = get.Required
        return object_arg_2.Field("name", string)

    t: ArcTable = ArcTable.create(_arrow2843(), decoded_header, [])
    enumerator: Any = get_enumerator(decoded_values)
    try: 
        while enumerator.System_Collections_IEnumerator_MoveNext():
            active_pattern_result: tuple[tuple[int, int], CompositeCell] = enumerator.System_Collections_Generic_IEnumerator_1_get_Current()
            t.SetCellAt(active_pattern_result[0][0], active_pattern_result[0][1], active_pattern_result[1])

    finally: 
        dispose(enumerator)

    return t


decoder_v2deprecated: Decoder_1[ArcTable] = object(_arrow2847)

def _arrow2865(__unit: None=None) -> Decoder_1[ArcTable]:
    value_map: Any = dict([])
    def ctor(cell: CompositeCell) -> int:
        return ensure_cell_hash_in_value_map(cell, value_map)

    cell_decoder: Decoder_1[int] = map_1(ctor, decoder_3)
    def ctor_1(Item: int) -> ColumnValueRefs:
        return ColumnValueRefs(0, Item)

    def ctor_2(Item_1: Any) -> ColumnValueRefs:
        return ColumnValueRefs(1, Item_1)

    column_decoder: Decoder_1[ColumnValueRefs] = Decode_tryOneOf(of_array([map_1(ctor_1, cell_decoder), map_1(ctor_2, Decode_intDictionary(cell_decoder))]))
    def _arrow2862(get: IGetters) -> ArcTable:
        def _arrow2854(__unit: None=None) -> Array[CompositeHeader] | None:
            arg_1: Decoder_1[Array[CompositeHeader]] = resize_array(decoder_2)
            object_arg: IOptionalGetter = get.Optional
            return object_arg.Field("headers", arg_1)

        decoded_header: Array[CompositeHeader] = default_arg(_arrow2854(), [])
        def _arrow2859(__unit: None=None) -> Any | None:
            arg_3: Decoder_1[Any] = Decode_dictionary(int_1, column_decoder)
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("columns", arg_3)

        def _arrow2860(__unit: None=None) -> int | None:
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("rowCount", int_1)

        values: ArcTableValues = ArcTableValues(default_arg(_arrow2859(), dict([])), value_map, default_arg(_arrow2860(), 0))
        def _arrow2861(__unit: None=None) -> str:
            object_arg_3: IRequiredGetter = get.Required
            return object_arg_3.Field("name", string)

        return ArcTable.from_arc_table_values(_arrow2861(), decoded_header, values)

    decoder_1: Decoder_1[ArcTable] = object(_arrow2862)
    class ObjectExpr2864(Decoder_1[ArcTable]):
        def Decode(self, helper: IDecoderHelpers_1[Any], column: Any) -> FSharpResult_2[ArcTable, tuple[str, ErrorReason_1[__A_]]]:
            return decoder_v2deprecated.Decode(helper, column) if helper.has_property("values", column) else decoder_1.Decode(helper, column)

    return ObjectExpr2864()


decoder: Decoder_1[ArcTable] = _arrow2865()

def decoder_compressed_column(cell_table: Array[CompositeCell], table: ArcTable, column_index: int) -> Decoder_1[None]:
    class ObjectExpr2875(Decoder_1[None]):
        def Decode(self, helper: IDecoderHelpers_1[Any], column: Any, cell_table: Any=cell_table, table: Any=table, column_index: Any=column_index) -> FSharpResult_2[None, tuple[str, ErrorReason_1[__A_]]]:
            match_value: FSharpResult_2[Array[CompositeCell], tuple[str, ErrorReason_1[__A_]]] = array_1(decode_cell(cell_table)).Decode(helper, column)
            if match_value.tag == 1:
                def _arrow2872(get: IGetters) -> None:
                    from_: int
                    object_arg: IRequiredGetter = get.Required
                    from_ = object_arg.Field("f", int_1)
                    to_: int
                    object_arg_1: IRequiredGetter = get.Required
                    to_ = object_arg_1.Field("t", int_1)
                    value: CompositeCell
                    arg_5: Decoder_1[CompositeCell] = decode_cell(cell_table)
                    object_arg_2: IRequiredGetter = get.Required
                    value = object_arg_2.Field("v", arg_5)
                    for i in range(from_, to_ + 1, 1):
                        Unchecked_setCellAt(column_index, i, value, table.Values)

                range_decoder: Decoder_1[None] = object(_arrow2872)
                match_value_1: FSharpResult_2[Array[None], tuple[str, ErrorReason_1[__A_]]] = array_1(range_decoder).Decode(helper, column)
                return FSharpResult_2(1, match_value_1.fields[0]) if (match_value_1.tag == 1) else FSharpResult_2(0, None)

            else: 
                def action(r: int, cell: CompositeCell) -> None:
                    Unchecked_setCellAt(column_index, r, cell, table.Values)

                iterate_indexed(action, match_value.fields[0])
                return FSharpResult_2(0, None)


    return ObjectExpr2875()


def arrayi(decoderi: Callable[[int], Decoder_1[_VALUE]]) -> Decoder_1[Array[Any]]:
    class ObjectExpr2883(Decoder_1[Array[_VALUE_]]):
        def Decode(self, helpers: IDecoderHelpers_1[Any], value: Any, decoderi: Any=decoderi) -> FSharpResult_2[Array[_VALUE_], tuple[str, ErrorReason_1[__A_]]]:
            if helpers.is_array(value):
                i: int = -1
                tokens: Array[__A_] = helpers.as_array(value)
                def folder(acc: FSharpResult_2[Array[_VALUE_], tuple[str, ErrorReason_1[__A_]]], value_1: __A_) -> FSharpResult_2[Array[_VALUE_], tuple[str, ErrorReason_1[__A_]]]:
                    nonlocal i
                    i = (i + 1) or 0
                    if acc.tag == 0:
                        acc_1: Array[_VALUE_] = acc.fields[0]
                        match_value: FSharpResult_2[_VALUE_, tuple[str, ErrorReason_1[__A_]]] = decoderi(i).Decode(helpers, value_1)
                        if match_value.tag == 0:
                            acc_1[i] = match_value.fields[0]
                            return FSharpResult_2(0, acc_1)

                        else: 
                            def _arrow2881(__unit: None=None, acc: Any=acc, value_1: Any=value_1) -> tuple[str, ErrorReason_1[__A_]]:
                                tupled_arg: tuple[str, ErrorReason_1[__A_]] = match_value.fields[0]
                                return Helpers_prependPath((".[" + int32_to_string(i)) + "]", tupled_arg[0], tupled_arg[1])

                            return FSharpResult_2(1, _arrow2881())


                    else: 
                        return acc


                return fold(folder, FSharpResult_2(0, fill([0] * len(tokens), 0, len(tokens), None)), tokens)

            else: 
                return FSharpResult_2(1, ("", ErrorReason_1(0, "an array", value)))


    return ObjectExpr2883()


def encoder_compressed(string_table: Any, oa_table: Any, cell_table: Any, table: ArcTable) -> IEncodable:
    def cell_encoder(hash_1: int, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, table: Any=table) -> IEncodable:
        return encode_cell(cell_table, get_item_from_dict(table.Values.ValueMap, hash_1))

    def _arrow2895(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, table: Any=table) -> IEnumerable_1[tuple[str, IEncodable]]:
        def _arrow2894(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
            def _arrow2885(__unit: None=None) -> IEnumerable_1[IEncodable]:
                return map(encoder_2, table.Headers)

            def _arrow2893(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                def column_encoder(col: ColumnValueRefs) -> IEncodable:
                    if col.tag == 1:
                        return int_dictionary(cell_encoder, col.fields[0])

                    else: 
                        return cell_encoder(col.fields[0])


                def _arrow2892(__unit: None=None) -> IEnumerable_1[tuple[str, IEncodable]]:
                    def _arrow2891(__unit: None=None) -> IEncodable:
                        value: int = table.RowCount or 0
                        class ObjectExpr2890(IEncodable):
                            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                                return helpers.encode_signed_integral_number(value)

                        return ObjectExpr2890()

                    return singleton(("r", _arrow2891()))

                return append(singleton(("c", int_dictionary(column_encoder, table.Values.Columns))), delay(_arrow2892)) if (table.Values.RowCount != 0) else empty()

            return append(singleton(("h", list_1(to_list(delay(_arrow2885))))) if (len(table.Headers) != 0) else empty(), delay(_arrow2893))

        return append(singleton(("n", encode_string(string_table, table.Name))), delay(_arrow2894))

    values: IEnumerable_1[tuple[str, IEncodable]] = to_list(delay(_arrow2895))
    class ObjectExpr2898(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, table: Any=table) -> Any:
            def mapping(tupled_arg: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg[0], tupled_arg[1].Encode(helpers_1))

            arg: IEnumerable_1[tuple[str, __A_]] = map(mapping, values)
            return helpers_1.encode_object(arg)

    return ObjectExpr2898()


def decoder_compressed_v2deprecated(string_table: Array[str], oa_table: Array[OntologyAnnotation], cell_table: Array[CompositeCell]) -> Decoder_1[ArcTable]:
    def _arrow2904(get: IGetters, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ArcTable:
        def _arrow2900(__unit: None=None) -> FSharpList[CompositeHeader] | None:
            arg_1: Decoder_1[FSharpList[CompositeHeader]] = list_1_1(decoder_2)
            object_arg: IOptionalGetter = get.Optional
            return object_arg.Field("h", arg_1)

        decoded_header: Array[CompositeHeader] = list(default_arg(_arrow2900(), empty_1()))
        def _arrow2901(__unit: None=None) -> str:
            arg_3: Decoder_1[str] = decode_string(string_table)
            object_arg_1: IRequiredGetter = get.Required
            return object_arg_1.Field("n", arg_3)

        table: ArcTable = ArcTable.create(_arrow2901(), decoded_header, [])
        def _arrow2903(__unit: None=None) -> Array[None] | None:
            def _arrow2902(column_index: int) -> Decoder_1[None]:
                return decoder_compressed_column(cell_table, table, column_index)

            arg_5: Decoder_1[Array[None]] = arrayi(_arrow2902)
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("c", arg_5)

        ignore(_arrow2903())
        return table

    return object(_arrow2904)


def decoder_compressed(string_table: Array[str], oa_table: Array[OntologyAnnotation], cell_table: Array[CompositeCell]) -> Decoder_1[ArcTable]:
    value_map: Any = dict([])
    def ctor(i: int, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> int:
        return ensure_cell_hash_in_value_map(cell_table[i], value_map)

    cell_decoder: Decoder_1[int] = map_1(ctor, int_1)
    def ctor_1(Item: int, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ColumnValueRefs:
        return ColumnValueRefs(0, Item)

    def ctor_2(Item_1: Any, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ColumnValueRefs:
        return ColumnValueRefs(1, Item_1)

    column_decoder: Decoder_1[ColumnValueRefs] = Decode_tryOneOf(of_array([map_1(ctor_1, cell_decoder), map_1(ctor_2, Decode_intDictionary(cell_decoder))]))
    def _arrow2920(get: IGetters, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ArcTable:
        def _arrow2912(__unit: None=None) -> Array[CompositeHeader] | None:
            arg_1: Decoder_1[Array[CompositeHeader]] = resize_array(decoder_2)
            object_arg: IOptionalGetter = get.Optional
            return object_arg.Field("h", arg_1)

        decoded_header: Array[CompositeHeader] = default_arg(_arrow2912(), [])
        def _arrow2917(__unit: None=None) -> Any | None:
            arg_3: Decoder_1[Any] = Decode_dictionary(int_1, column_decoder)
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("c", arg_3)

        def _arrow2918(__unit: None=None) -> int | None:
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("r", int_1)

        values: ArcTableValues = ArcTableValues(default_arg(_arrow2917(), dict([])), value_map, default_arg(_arrow2918(), 0))
        def _arrow2919(__unit: None=None) -> str:
            arg_7: Decoder_1[str] = decode_string(string_table)
            object_arg_3: IRequiredGetter = get.Required
            return object_arg_3.Field("n", arg_7)

        return ArcTable.from_arc_table_values(_arrow2919(), decoded_header, values)

    decoder_1: Decoder_1[ArcTable] = object(_arrow2920)
    class ObjectExpr2924(Decoder_1[ArcTable]):
        def Decode(self, helper: IDecoderHelpers_1[Any], column: Any, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> FSharpResult_2[ArcTable, tuple[str, ErrorReason_1[__A_]]]:
            return decoder_compressed_v2deprecated(string_table, oa_table, cell_table).Decode(helper, column) if (not helper.has_property("r", column)) else decoder_1.Decode(helper, column)

    return ObjectExpr2924()


__all__ = ["encoder", "decoder_v2deprecated", "decoder", "decoder_compressed_column", "arrayi", "encoder_compressed", "decoder_compressed_v2deprecated", "decoder_compressed"]

