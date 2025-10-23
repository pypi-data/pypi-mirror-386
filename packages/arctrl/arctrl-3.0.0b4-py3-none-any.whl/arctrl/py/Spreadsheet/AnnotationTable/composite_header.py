from __future__ import annotations
from collections.abc import Callable
from typing import Any
from ...fable_modules.fable_library.array_ import (equals_with, skip, try_find_index)
from ...fable_modules.fable_library.option import map
from ...fable_modules.fable_library.seq import (to_array, delay, append, singleton, empty)
from ...fable_modules.fable_library.string_ import (to_fail, printf, starts_with_exact)
from ...fable_modules.fable_library.types import (Array, to_string)
from ...fable_modules.fable_library.util import IEnumerable_1
from ...Core.Helper.regex import (ActivePatterns__007CUnitColumnHeader_007C__007C, ActivePatterns__007CTANColumnHeader_007C__007C, ActivePatterns__007CTSRColumnHeader_007C__007C, try_parse_parameter_column_header, try_parse_factor_column_header, try_parse_characteristic_column_header, try_parse_component_column_header, ActivePatterns__007CInputColumnHeader_007C__007C, ActivePatterns__007COutputColumnHeader_007C__007C, ActivePatterns__007CComment_007C__007C)
from ...Core.ontology_annotation import OntologyAnnotation
from ...Core.Table.composite_cell import CompositeCell
from ...Core.Table.composite_header import (CompositeHeader, IOType)
from .composite_cell import (term_from_string_cells, unitized_from_string_cells, data_from_string_cells, free_text_from_string_cells)

def ActivePattern_mergeIDInfo(id_space1: str, local_id1: str, id_space2: str, local_id2: str) -> dict[str, Any]:
    if id_space1 != id_space2:
        to_fail(printf("TermSourceRef %s and %s do not match"))(id_space1)(id_space2)

    if local_id1 != local_id2:
        to_fail(printf("LocalID %s and %s do not match"))(local_id1)(local_id2)

    return {
        "TermAccessionNumber": ((("" + id_space1) + ":") + local_id1) + "",
        "TermSourceRef": id_space1
    }


def ActivePattern__007CTerm_007C__007C(category_parser: Callable[[str], str | None], f: Callable[[OntologyAnnotation], CompositeHeader], cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    def _007CAC_007C__007C(s: str, category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> str | None:
        return category_parser(s)

    (pattern_matching_result, name, name_1, term1, term2) = (None, None, None, None, None)
    def _arrow1291(x: str, y: str, category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> bool:
        return x == y

    if (len(cell_values) == 1) if (not equals_with(_arrow1291, cell_values, None)) else False:
        active_pattern_result: str | None = _007CAC_007C__007C(cell_values[0])
        if active_pattern_result is not None:
            pattern_matching_result = 0
            name = active_pattern_result

        else: 
            pattern_matching_result = 2


    else: 
        def _arrow1292(x_1: str, y_1: str, category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> bool:
            return x_1 == y_1

        if (len(cell_values) == 3) if (not equals_with(_arrow1292, cell_values, None)) else False:
            active_pattern_result_1: str | None = _007CAC_007C__007C(cell_values[0])
            if active_pattern_result_1 is not None:
                active_pattern_result_2: dict[str, Any] | None = ActivePatterns__007CTSRColumnHeader_007C__007C(cell_values[1])
                if active_pattern_result_2 is not None:
                    active_pattern_result_3: dict[str, Any] | None = ActivePatterns__007CTANColumnHeader_007C__007C(cell_values[2])
                    if active_pattern_result_3 is not None:
                        pattern_matching_result = 1
                        name_1 = active_pattern_result_1
                        term1 = active_pattern_result_2
                        term2 = active_pattern_result_3

                    else: 
                        pattern_matching_result = 2


                else: 
                    pattern_matching_result = 2


            else: 
                pattern_matching_result = 2


        else: 
            pattern_matching_result = 2


    if pattern_matching_result == 0:
        def _arrow1283(cell_values_1: Array[str], category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> CompositeCell:
            return term_from_string_cells(None, None, cell_values_1)

        return (f(OntologyAnnotation.create(name)), _arrow1283)

    elif pattern_matching_result == 1:
        term: dict[str, Any] = ActivePattern_mergeIDInfo(term1["IDSpace"], term1["LocalID"], term2["IDSpace"], term2["LocalID"])
        def _arrow1284(cell_values_2: Array[str], category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> CompositeCell:
            return term_from_string_cells(1, 2, cell_values_2)

        return (f(OntologyAnnotation.create(name_1, term["TermSourceRef"], term["TermAccessionNumber"])), _arrow1284)

    elif pattern_matching_result == 2:
        (pattern_matching_result_1, name_2, term1_1, term2_1) = (None, None, None, None)
        def _arrow1290(x_2: str, y_2: str, category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> bool:
            return x_2 == y_2

        if (len(cell_values) == 3) if (not equals_with(_arrow1290, cell_values, None)) else False:
            active_pattern_result_4: str | None = _007CAC_007C__007C(cell_values[0])
            if active_pattern_result_4 is not None:
                active_pattern_result_5: dict[str, Any] | None = ActivePatterns__007CTANColumnHeader_007C__007C(cell_values[1])
                if active_pattern_result_5 is not None:
                    active_pattern_result_6: dict[str, Any] | None = ActivePatterns__007CTSRColumnHeader_007C__007C(cell_values[2])
                    if active_pattern_result_6 is not None:
                        pattern_matching_result_1 = 0
                        name_2 = active_pattern_result_4
                        term1_1 = active_pattern_result_6
                        term2_1 = active_pattern_result_5

                    else: 
                        pattern_matching_result_1 = 1


                else: 
                    pattern_matching_result_1 = 1


            else: 
                pattern_matching_result_1 = 1


        else: 
            pattern_matching_result_1 = 1

        if pattern_matching_result_1 == 0:
            term_1: dict[str, Any] = ActivePattern_mergeIDInfo(term1_1["IDSpace"], term1_1["LocalID"], term2_1["IDSpace"], term2_1["LocalID"])
            def _arrow1285(cell_values_3: Array[str], category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> CompositeCell:
                return term_from_string_cells(2, 1, cell_values_3)

            return (f(OntologyAnnotation.create(name_2, term_1["TermSourceRef"], term_1["TermAccessionNumber"])), _arrow1285)

        elif pattern_matching_result_1 == 1:
            (pattern_matching_result_2, name_3, term1_2, term2_2) = (None, None, None, None)
            def _arrow1289(x_3: str, y_3: str, category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> bool:
                return x_3 == y_3

            if (len(cell_values) == 4) if (not equals_with(_arrow1289, cell_values, None)) else False:
                active_pattern_result_7: str | None = _007CAC_007C__007C(cell_values[0])
                if active_pattern_result_7 is not None:
                    if ActivePatterns__007CUnitColumnHeader_007C__007C(cell_values[1]) is not None:
                        active_pattern_result_9: dict[str, Any] | None = ActivePatterns__007CTSRColumnHeader_007C__007C(cell_values[2])
                        if active_pattern_result_9 is not None:
                            active_pattern_result_10: dict[str, Any] | None = ActivePatterns__007CTANColumnHeader_007C__007C(cell_values[3])
                            if active_pattern_result_10 is not None:
                                pattern_matching_result_2 = 0
                                name_3 = active_pattern_result_7
                                term1_2 = active_pattern_result_9
                                term2_2 = active_pattern_result_10

                            else: 
                                pattern_matching_result_2 = 1


                        else: 
                            pattern_matching_result_2 = 1


                    else: 
                        pattern_matching_result_2 = 1


                else: 
                    pattern_matching_result_2 = 1


            else: 
                pattern_matching_result_2 = 1

            if pattern_matching_result_2 == 0:
                term_2: dict[str, Any] = ActivePattern_mergeIDInfo(term1_2["IDSpace"], term1_2["LocalID"], term2_2["IDSpace"], term2_2["LocalID"])
                def _arrow1286(cell_values_4: Array[str], category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> CompositeCell:
                    return unitized_from_string_cells(1, 2, 3, cell_values_4)

                return (f(OntologyAnnotation.create(name_3, term_2["TermSourceRef"], term_2["TermAccessionNumber"])), _arrow1286)

            elif pattern_matching_result_2 == 1:
                (pattern_matching_result_3, name_4, term1_3, term2_3) = (None, None, None, None)
                def _arrow1288(x_4: str, y_4: str, category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> bool:
                    return x_4 == y_4

                if (len(cell_values) == 4) if (not equals_with(_arrow1288, cell_values, None)) else False:
                    active_pattern_result_11: str | None = _007CAC_007C__007C(cell_values[0])
                    if active_pattern_result_11 is not None:
                        if ActivePatterns__007CUnitColumnHeader_007C__007C(cell_values[1]) is not None:
                            active_pattern_result_13: dict[str, Any] | None = ActivePatterns__007CTANColumnHeader_007C__007C(cell_values[2])
                            if active_pattern_result_13 is not None:
                                active_pattern_result_14: dict[str, Any] | None = ActivePatterns__007CTSRColumnHeader_007C__007C(cell_values[3])
                                if active_pattern_result_14 is not None:
                                    pattern_matching_result_3 = 0
                                    name_4 = active_pattern_result_11
                                    term1_3 = active_pattern_result_14
                                    term2_3 = active_pattern_result_13

                                else: 
                                    pattern_matching_result_3 = 1


                            else: 
                                pattern_matching_result_3 = 1


                        else: 
                            pattern_matching_result_3 = 1


                    else: 
                        pattern_matching_result_3 = 1


                else: 
                    pattern_matching_result_3 = 1

                if pattern_matching_result_3 == 0:
                    term_3: dict[str, Any] = ActivePattern_mergeIDInfo(term1_3["IDSpace"], term1_3["LocalID"], term2_3["IDSpace"], term2_3["LocalID"])
                    def _arrow1287(cell_values_5: Array[str], category_parser: Any=category_parser, f: Any=f, cell_values: Any=cell_values) -> CompositeCell:
                        return unitized_from_string_cells(1, 3, 2, cell_values_5)

                    return (f(OntologyAnnotation.create(name_4, term_3["TermSourceRef"], term_3["TermAccessionNumber"])), _arrow1287)

                elif pattern_matching_result_3 == 1:
                    return None






def ActivePattern__007CParameter_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    def _arrow1293(input: str, cell_values: Any=cell_values) -> str | None:
        return try_parse_parameter_column_header(input)

    def _arrow1294(Item: OntologyAnnotation, cell_values: Any=cell_values) -> CompositeHeader:
        return CompositeHeader(3, Item)

    active_pattern_result: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CTerm_007C__007C(_arrow1293, _arrow1294, cell_values)
    if active_pattern_result is not None:
        r: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result
        return r

    else: 
        return None



def ActivePattern__007CFactor_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    def _arrow1295(input: str, cell_values: Any=cell_values) -> str | None:
        return try_parse_factor_column_header(input)

    def _arrow1296(Item: OntologyAnnotation, cell_values: Any=cell_values) -> CompositeHeader:
        return CompositeHeader(2, Item)

    active_pattern_result: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CTerm_007C__007C(_arrow1295, _arrow1296, cell_values)
    if active_pattern_result is not None:
        r: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result
        return r

    else: 
        return None



def ActivePattern__007CCharacteristic_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    def _arrow1297(input: str, cell_values: Any=cell_values) -> str | None:
        return try_parse_characteristic_column_header(input)

    def _arrow1298(Item: OntologyAnnotation, cell_values: Any=cell_values) -> CompositeHeader:
        return CompositeHeader(1, Item)

    active_pattern_result: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CTerm_007C__007C(_arrow1297, _arrow1298, cell_values)
    if active_pattern_result is not None:
        r: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result
        return r

    else: 
        return None



def ActivePattern__007CComponent_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    def _arrow1299(input: str, cell_values: Any=cell_values) -> str | None:
        return try_parse_component_column_header(input)

    def _arrow1300(Item: OntologyAnnotation, cell_values: Any=cell_values) -> CompositeHeader:
        return CompositeHeader(0, Item)

    active_pattern_result: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CTerm_007C__007C(_arrow1299, _arrow1300, cell_values)
    if active_pattern_result is not None:
        r: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result
        return r

    else: 
        return None



def ActivePattern__007CInput_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    if len(cell_values) == 0:
        return None

    else: 
        match_value: str = cell_values[0]
        active_pattern_result: str | None = ActivePatterns__007CInputColumnHeader_007C__007C(match_value)
        if active_pattern_result is not None:
            io_type: str = active_pattern_result
            cols: Array[str] = skip(1, cell_values, None)
            match_value_1: IOType = IOType.of_string(io_type)
            if match_value_1.tag == 2:
                def mapping(y: int, cell_values: Any=cell_values) -> int:
                    return 1 + y

                def predicate(s: str, cell_values: Any=cell_values) -> bool:
                    return starts_with_exact(s, "Data Format")

                format: int | None = map(mapping, try_find_index(predicate, cols))
                def mapping_1(y_1: int, cell_values: Any=cell_values) -> int:
                    return 1 + y_1

                def predicate_1(s_1: str, cell_values: Any=cell_values) -> bool:
                    return starts_with_exact(s_1, "Data Selector Format")

                selector_format: int | None = map(mapping_1, try_find_index(predicate_1, cols))
                def _arrow1301(cell_values_1: Array[str], cell_values: Any=cell_values) -> CompositeCell:
                    return data_from_string_cells(format, selector_format, cell_values_1)

                return (CompositeHeader(11, IOType(2)), _arrow1301)

            else: 
                def _arrow1302(cell_values_2: Array[str], cell_values: Any=cell_values) -> CompositeCell:
                    return free_text_from_string_cells(cell_values_2)

                return (CompositeHeader(11, match_value_1), _arrow1302)


        else: 
            return None




def ActivePattern__007COutput_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    if len(cell_values) == 0:
        return None

    else: 
        match_value: str = cell_values[0]
        active_pattern_result: str | None = ActivePatterns__007COutputColumnHeader_007C__007C(match_value)
        if active_pattern_result is not None:
            io_type: str = active_pattern_result
            cols: Array[str] = skip(1, cell_values, None)
            match_value_1: IOType = IOType.of_string(io_type)
            if match_value_1.tag == 2:
                def mapping(y: int, cell_values: Any=cell_values) -> int:
                    return 1 + y

                def predicate(s: str, cell_values: Any=cell_values) -> bool:
                    return starts_with_exact(s, "Data Format")

                format: int | None = map(mapping, try_find_index(predicate, cols))
                def mapping_1(y_1: int, cell_values: Any=cell_values) -> int:
                    return 1 + y_1

                def predicate_1(s_1: str, cell_values: Any=cell_values) -> bool:
                    return starts_with_exact(s_1, "Data Selector Format")

                selector_format: int | None = map(mapping_1, try_find_index(predicate_1, cols))
                def _arrow1303(cell_values_1: Array[str], cell_values: Any=cell_values) -> CompositeCell:
                    return data_from_string_cells(format, selector_format, cell_values_1)

                return (CompositeHeader(12, IOType(2)), _arrow1303)

            else: 
                def _arrow1304(cell_values_2: Array[str], cell_values: Any=cell_values) -> CompositeCell:
                    return free_text_from_string_cells(cell_values_2)

                return (CompositeHeader(12, match_value_1), _arrow1304)


        else: 
            return None




def ActivePattern__007CComment_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    (pattern_matching_result, key) = (None, None)
    def _arrow1306(x: str, y: str, cell_values: Any=cell_values) -> bool:
        return x == y

    if (len(cell_values) == 1) if (not equals_with(_arrow1306, cell_values, None)) else False:
        active_pattern_result: str | None = ActivePatterns__007CComment_007C__007C(cell_values[0])
        if active_pattern_result is not None:
            pattern_matching_result = 0
            key = active_pattern_result

        else: 
            pattern_matching_result = 1


    else: 
        pattern_matching_result = 1

    if pattern_matching_result == 0:
        def _arrow1305(cell_values_1: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_1)

        return (CompositeHeader(14, key), _arrow1305)

    elif pattern_matching_result == 1:
        return None



def ActivePattern__007CProtocolType_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    def parser(s: str, cell_values: Any=cell_values) -> str | None:
        if s == "Protocol Type":
            return s

        else: 
            return None


    def header(_arg: OntologyAnnotation, cell_values: Any=cell_values) -> CompositeHeader:
        return CompositeHeader(4)

    active_pattern_result: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CTerm_007C__007C(parser, header, cell_values)
    if active_pattern_result is not None:
        r: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result
        return r

    else: 
        return None



def ActivePattern__007CProtocolHeader_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    (pattern_matching_result,) = (None,)
    def _arrow1313(x: str, y: str, cell_values: Any=cell_values) -> bool:
        return x == y

    if (len(cell_values) == 1) if (not equals_with(_arrow1313, cell_values, None)) else False:
        if cell_values[0] == "Protocol REF":
            pattern_matching_result = 0

        elif cell_values[0] == "Protocol Description":
            pattern_matching_result = 1

        elif cell_values[0] == "Protocol Uri":
            pattern_matching_result = 2

        elif cell_values[0] == "Protocol Version":
            pattern_matching_result = 3

        elif cell_values[0] == "Performer":
            pattern_matching_result = 4

        elif cell_values[0] == "Date":
            pattern_matching_result = 5

        else: 
            pattern_matching_result = 6


    else: 
        pattern_matching_result = 6

    if pattern_matching_result == 0:
        def _arrow1307(cell_values_1: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_1)

        return (CompositeHeader(8), _arrow1307)

    elif pattern_matching_result == 1:
        def _arrow1308(cell_values_2: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_2)

        return (CompositeHeader(5), _arrow1308)

    elif pattern_matching_result == 2:
        def _arrow1309(cell_values_3: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_3)

        return (CompositeHeader(6), _arrow1309)

    elif pattern_matching_result == 3:
        def _arrow1310(cell_values_4: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_4)

        return (CompositeHeader(7), _arrow1310)

    elif pattern_matching_result == 4:
        def _arrow1311(cell_values_5: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_5)

        return (CompositeHeader(9), _arrow1311)

    elif pattern_matching_result == 5:
        def _arrow1312(cell_values_6: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_6)

        return (CompositeHeader(10), _arrow1312)

    elif pattern_matching_result == 6:
        return None



def ActivePattern__007CFreeText_007C__007C(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None:
    def _arrow1314(x: str, y: str, cell_values: Any=cell_values) -> bool:
        return x == y

    if (len(cell_values) == 1) if (not equals_with(_arrow1314, cell_values, None)) else False:
        def _arrow1315(cell_values_1: Array[str], cell_values: Any=cell_values) -> CompositeCell:
            return free_text_from_string_cells(cell_values_1)

        return (CompositeHeader(13, cell_values[0]), _arrow1315)

    else: 
        return None



def from_string_cells(cell_values: Array[str]) -> tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]]:
    active_pattern_result: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CParameter_007C__007C(cell_values)
    if active_pattern_result is not None:
        p: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result
        return p

    else: 
        active_pattern_result_1: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CFactor_007C__007C(cell_values)
        if active_pattern_result_1 is not None:
            f: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_1
            return f

        else: 
            active_pattern_result_2: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CCharacteristic_007C__007C(cell_values)
            if active_pattern_result_2 is not None:
                c: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_2
                return c

            else: 
                active_pattern_result_3: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CComponent_007C__007C(cell_values)
                if active_pattern_result_3 is not None:
                    c_1: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_3
                    return c_1

                else: 
                    active_pattern_result_4: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CInput_007C__007C(cell_values)
                    if active_pattern_result_4 is not None:
                        i: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_4
                        return i

                    else: 
                        active_pattern_result_5: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007COutput_007C__007C(cell_values)
                        if active_pattern_result_5 is not None:
                            o: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_5
                            return o

                        else: 
                            active_pattern_result_6: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CProtocolType_007C__007C(cell_values)
                            if active_pattern_result_6 is not None:
                                pt: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_6
                                return pt

                            else: 
                                active_pattern_result_7: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CProtocolHeader_007C__007C(cell_values)
                                if active_pattern_result_7 is not None:
                                    ph: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_7
                                    return ph

                                else: 
                                    active_pattern_result_8: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CComment_007C__007C(cell_values)
                                    if active_pattern_result_8 is not None:
                                        c_2: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_8
                                        return c_2

                                    else: 
                                        active_pattern_result_9: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] | None = ActivePattern__007CFreeText_007C__007C(cell_values)
                                        if active_pattern_result_9 is not None:
                                            ft: tuple[CompositeHeader, Callable[[Array[str]], CompositeCell]] = active_pattern_result_9
                                            return ft

                                        else: 
                                            return to_fail(printf("Could not parse header group %O"))(cell_values)












def to_string_cells(has_unit: bool, header: CompositeHeader) -> Array[str]:
    if header.IsDataColumn:
        return [to_string(header), "Data Format", "Data Selector Format"]

    elif header.IsSingleColumn:
        return [to_string(header)]

    elif header.IsTermColumn:
        def _arrow1319(__unit: None=None, has_unit: Any=has_unit, header: Any=header) -> IEnumerable_1[str]:
            def _arrow1318(__unit: None=None) -> IEnumerable_1[str]:
                def _arrow1317(__unit: None=None) -> IEnumerable_1[str]:
                    def _arrow1316(__unit: None=None) -> IEnumerable_1[str]:
                        return singleton(("Term Accession Number (" + header.GetColumnAccessionShort) + ")")

                    return append(singleton(("Term Source REF (" + header.GetColumnAccessionShort) + ")"), delay(_arrow1316))

                return append(singleton("Unit") if has_unit else empty(), delay(_arrow1317))

            return append(singleton(to_string(header)), delay(_arrow1318))

        return to_array(delay(_arrow1319))

    else: 
        return to_fail(printf("header %O is neither single nor term column"))(header)



__all__ = ["ActivePattern_mergeIDInfo", "ActivePattern__007CTerm_007C__007C", "ActivePattern__007CParameter_007C__007C", "ActivePattern__007CFactor_007C__007C", "ActivePattern__007CCharacteristic_007C__007C", "ActivePattern__007CComponent_007C__007C", "ActivePattern__007CInput_007C__007C", "ActivePattern__007COutput_007C__007C", "ActivePattern__007CComment_007C__007C", "ActivePattern__007CProtocolType_007C__007C", "ActivePattern__007CProtocolHeader_007C__007C", "ActivePattern__007CFreeText_007C__007C", "from_string_cells", "to_string_cells"]

