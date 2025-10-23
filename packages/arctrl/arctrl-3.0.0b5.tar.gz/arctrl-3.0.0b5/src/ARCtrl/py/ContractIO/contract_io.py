from __future__ import annotations
from collections.abc import Callable
from typing import Any
from ..Contract.contract import (Contract, DTOType, DTO as DTO_2)
from ..FileSystem.path import combine
from ..cross_async import (catch_with, start_sequential)
from ..fable_modules.fable_library.array_ import (fold, append)
from ..fable_modules.fable_library.async_builder import (singleton, Async)
from ..fable_modules.fable_library.result import FSharpResult_2
from ..fable_modules.fable_library.string_ import (to_text, printf)
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import curry2
from ..fable_modules.fs_spreadsheet.fs_workbook import FsWorkbook
from .file_system_helper import (read_file_xlsx_async, read_file_text_async, ensure_directory_of_file_async, write_file_text_async, write_file_xlsx_async, rename_file_or_directory_async, delete_file_or_directory_async)

def fulfill_read_contract_async(base_path: str, c: Contract) -> Async[FSharpResult_2[Contract, str]]:
    def f(e_1: Exception, base_path: Any=base_path, c: Any=c) -> FSharpResult_2[Contract, str]:
        def _arrow3797(__unit: None=None, e_1: Any=e_1) -> str:
            arg_4: str = str(e_1)
            return to_text(printf("Error reading contract %s: %s"))(c.Path)(arg_4)

        return FSharpResult_2(1, _arrow3797())

    def _arrow3803(__unit: None=None, base_path: Any=base_path, c: Any=c) -> Async[FSharpResult_2[Contract, str]]:
        def _arrow3800(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
            match_value: DTOType | None = c.DTOType
            (pattern_matching_result,) = (None,)
            if match_value is not None:
                if match_value.tag == 0:
                    pattern_matching_result = 0

                elif match_value.tag == 4:
                    pattern_matching_result = 0

                elif match_value.tag == 1:
                    pattern_matching_result = 0

                elif match_value.tag == 2:
                    pattern_matching_result = 0

                elif match_value.tag == 3:
                    pattern_matching_result = 0

                elif match_value.tag == 5:
                    pattern_matching_result = 0

                elif match_value.tag == 10:
                    pattern_matching_result = 1

                else: 
                    pattern_matching_result = 2


            else: 
                pattern_matching_result = 2

            if pattern_matching_result == 0:
                path: str = combine(base_path, c.Path)
                def _arrow3798(_arg: FsWorkbook) -> Async[FSharpResult_2[Contract, str]]:
                    return singleton.Return(FSharpResult_2(0, Contract(c.Operation, c.Path, c.DTOType, DTO_2(0, _arg))))

                return singleton.Bind(read_file_xlsx_async(path), _arrow3798)

            elif pattern_matching_result == 1:
                path_1: str = combine(base_path, c.Path)
                def _arrow3799(_arg_1: str) -> Async[FSharpResult_2[Contract, str]]:
                    return singleton.Return(FSharpResult_2(0, Contract(c.Operation, c.Path, c.DTOType, DTO_2(1, _arg_1))))

                return singleton.Bind(read_file_text_async(path_1), _arrow3799)

            elif pattern_matching_result == 2:
                return singleton.Return(FSharpResult_2(1, to_text(printf("Contract %s is neither an ISA nor a freetext contract"))(c.Path)))


        def _arrow3802(_arg_2: Exception) -> Async[FSharpResult_2[Contract, str]]:
            def _arrow3801(__unit: None=None) -> str:
                arg_2: str = str(_arg_2)
                return to_text(printf("Error reading contract %s: %s"))(c.Path)(arg_2)

            return singleton.Return(FSharpResult_2(1, _arrow3801()))

        return singleton.TryWith(singleton.Delay(_arrow3800), _arrow3802)

    return catch_with(f, singleton.Delay(_arrow3803))


def fullfill_contract_batch_async_by(contract_f: Callable[[str, Contract], Async[FSharpResult_2[Contract, str]]], base_path: str, cs: Array[Contract]) -> Async[FSharpResult_2[Array[Contract], Array[str]]]:
    def _arrow3805(__unit: None=None, contract_f: Any=contract_f, base_path: Any=base_path, cs: Any=cs) -> Async[FSharpResult_2[Array[Contract], Array[str]]]:
        def _arrow3804(_arg: Array[FSharpResult_2[Contract, str]]) -> Async[FSharpResult_2[Array[Contract], Array[str]]]:
            def folder(acc: FSharpResult_2[Array[Contract], Array[str]], cr: FSharpResult_2[Contract, str]) -> FSharpResult_2[Array[Contract], Array[str]]:
                copy_of_struct: FSharpResult_2[Array[Contract], Array[str]] = acc
                if copy_of_struct.tag == 1:
                    copy_of_struct_1: FSharpResult_2[Contract, str] = cr
                    if copy_of_struct_1.tag == 1:
                        return FSharpResult_2(1, append(copy_of_struct.fields[0], [copy_of_struct_1.fields[0]], None))

                    else: 
                        return FSharpResult_2(1, copy_of_struct.fields[0])


                else: 
                    copy_of_struct_2: FSharpResult_2[Contract, str] = cr
                    if copy_of_struct_2.tag == 1:
                        return FSharpResult_2(1, [copy_of_struct_2.fields[0]])

                    else: 
                        return FSharpResult_2(0, append(copy_of_struct.fields[0], [copy_of_struct_2.fields[0]], None))



            res: FSharpResult_2[Array[Contract], Array[str]] = fold(folder, FSharpResult_2(0, []), _arg)
            return singleton.Return(res)

        return singleton.Bind(start_sequential(curry2(contract_f)(base_path), cs), _arrow3804)

    return singleton.Delay(_arrow3805)


def fulfill_write_contract_async(base_path: str, c: Contract) -> Async[FSharpResult_2[Contract, str]]:
    def f(e_1: Exception, base_path: Any=base_path, c: Any=c) -> FSharpResult_2[Contract, str]:
        def _arrow3806(__unit: None=None, e_1: Any=e_1) -> str:
            arg_4: str = str(e_1)
            return to_text(printf("Error writing contract %s: %s"))(c.Path)(arg_4)

        return FSharpResult_2(1, _arrow3806())

    def _arrow3816(__unit: None=None, base_path: Any=base_path, c: Any=c) -> Async[FSharpResult_2[Contract, str]]:
        def _arrow3813(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
            match_value: DTO_2 | None = c.DTO
            if match_value is None:
                path_2: str = combine(base_path, c.Path)
                def _arrow3808(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                    def _arrow3807(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                        return singleton.Return(FSharpResult_2(0, c))

                    return singleton.Bind(write_file_text_async(path_2, ""), _arrow3807)

                return singleton.Bind(ensure_directory_of_file_async(path_2), _arrow3808)

            elif match_value.tag == 1:
                t: str = match_value.fields[0]
                path: str = combine(base_path, c.Path)
                def _arrow3810(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                    def _arrow3809(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                        return singleton.Return(FSharpResult_2(0, c))

                    return singleton.Bind(write_file_text_async(path, t), _arrow3809)

                return singleton.Bind(ensure_directory_of_file_async(path), _arrow3810)

            elif match_value.tag == 0:
                wb: Any = match_value.fields[0]
                path_1: str = combine(base_path, c.Path)
                def _arrow3812(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                    def _arrow3811(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                        return singleton.Return(FSharpResult_2(0, c))

                    return singleton.Bind(write_file_xlsx_async(path_1, wb), _arrow3811)

                return singleton.Bind(ensure_directory_of_file_async(path_1), _arrow3812)

            else: 
                return singleton.Return(FSharpResult_2(1, to_text(printf("Contract %s is not an ISA contract"))(c.Path)))


        def _arrow3815(_arg_6: Exception) -> Async[FSharpResult_2[Contract, str]]:
            def _arrow3814(__unit: None=None) -> str:
                arg_2: str = str(_arg_6)
                return to_text(printf("Error writing contract %s: %s"))(c.Path)(arg_2)

            return singleton.Return(FSharpResult_2(1, _arrow3814()))

        return singleton.TryWith(singleton.Delay(_arrow3813), _arrow3815)

    return catch_with(f, singleton.Delay(_arrow3816))


def fulfill_update_contract_async(base_path: str, c: Contract) -> Async[FSharpResult_2[Contract, str]]:
    def f(e_1: Exception, base_path: Any=base_path, c: Any=c) -> FSharpResult_2[Contract, str]:
        def _arrow3817(__unit: None=None, e_1: Any=e_1) -> str:
            arg_4: str = str(e_1)
            return to_text(printf("Error updating contract %s: %s"))(c.Path)(arg_4)

        return FSharpResult_2(1, _arrow3817())

    def _arrow3827(__unit: None=None, base_path: Any=base_path, c: Any=c) -> Async[FSharpResult_2[Contract, str]]:
        def _arrow3824(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
            match_value: DTO_2 | None = c.DTO
            if match_value is None:
                path_2: str = combine(base_path, c.Path)
                def _arrow3819(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                    def _arrow3818(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                        return singleton.Return(FSharpResult_2(0, c))

                    return singleton.Bind(write_file_text_async(path_2, ""), _arrow3818)

                return singleton.Bind(ensure_directory_of_file_async(path_2), _arrow3819)

            elif match_value.tag == 1:
                t: str = match_value.fields[0]
                path: str = combine(base_path, c.Path)
                def _arrow3821(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                    def _arrow3820(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                        return singleton.Return(FSharpResult_2(0, c))

                    return singleton.Bind(write_file_text_async(path, t), _arrow3820)

                return singleton.Bind(ensure_directory_of_file_async(path), _arrow3821)

            elif match_value.tag == 0:
                wb: Any = match_value.fields[0]
                path_1: str = combine(base_path, c.Path)
                def _arrow3823(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                    def _arrow3822(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                        return singleton.Return(FSharpResult_2(0, c))

                    return singleton.Bind(write_file_xlsx_async(path_1, wb), _arrow3822)

                return singleton.Bind(ensure_directory_of_file_async(path_1), _arrow3823)

            else: 
                return singleton.Return(FSharpResult_2(1, to_text(printf("Contract %s is not an ISA contract"))(c.Path)))


        def _arrow3826(_arg_6: Exception) -> Async[FSharpResult_2[Contract, str]]:
            def _arrow3825(__unit: None=None) -> str:
                arg_2: str = str(_arg_6)
                return to_text(printf("Error updating contract %s: %s"))(c.Path)(arg_2)

            return singleton.Return(FSharpResult_2(1, _arrow3825()))

        return singleton.TryWith(singleton.Delay(_arrow3824), _arrow3826)

    return catch_with(f, singleton.Delay(_arrow3827))


def fullfill_rename_contract_async(base_path: str, c: Contract) -> Async[FSharpResult_2[Contract, str]]:
    def f(e_1: Exception, base_path: Any=base_path, c: Any=c) -> FSharpResult_2[Contract, str]:
        def _arrow3828(__unit: None=None, e_1: Any=e_1) -> str:
            arg_5: str = str(e_1)
            return to_text(printf("Error renaming contract %s: %s"))(c.Path)(arg_5)

        return FSharpResult_2(1, _arrow3828())

    def _arrow3833(__unit: None=None, base_path: Any=base_path, c: Any=c) -> Async[FSharpResult_2[Contract, str]]:
        def _arrow3830(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
            match_value: DTO_2 | None = c.DTO
            (pattern_matching_result, t_2) = (None, None)
            if match_value is not None:
                if match_value.tag == 1:
                    if match_value.fields[0] == c.Path:
                        pattern_matching_result = 0

                    else: 
                        pattern_matching_result = 1
                        t_2 = match_value.fields[0]


                else: 
                    pattern_matching_result = 2


            else: 
                pattern_matching_result = 2

            if pattern_matching_result == 0:
                return singleton.Return(FSharpResult_2(1, to_text(printf("Rename Contract %s old and new Path are the same"))(c.Path)))

            elif pattern_matching_result == 1:
                new_path: str = combine(base_path, t_2)
                old_path: str = combine(base_path, c.Path)
                def _arrow3829(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                    return singleton.Return(FSharpResult_2(0, c))

                return singleton.Bind(rename_file_or_directory_async(old_path, new_path), _arrow3829)

            elif pattern_matching_result == 2:
                return singleton.Return(FSharpResult_2(1, to_text(printf("Rename Contract %s does not contain new Path"))(c.Path)))


        def _arrow3832(_arg_1: Exception) -> Async[FSharpResult_2[Contract, str]]:
            def _arrow3831(__unit: None=None) -> str:
                arg_3: str = str(_arg_1)
                return to_text(printf("Error renaming contract %s: %s"))(c.Path)(arg_3)

            return singleton.Return(FSharpResult_2(1, _arrow3831()))

        return singleton.TryWith(singleton.Delay(_arrow3830), _arrow3832)

    return catch_with(f, singleton.Delay(_arrow3833))


def fullfill_delete_contract_async(base_path: str, c: Contract) -> Async[FSharpResult_2[Contract, str]]:
    def f(e_1: Exception, base_path: Any=base_path, c: Any=c) -> FSharpResult_2[Contract, str]:
        def _arrow3834(__unit: None=None, e_1: Any=e_1) -> str:
            arg_3: str = str(e_1)
            return to_text(printf("Error deleting contract %s: %s"))(c.Path)(arg_3)

        return FSharpResult_2(1, _arrow3834())

    def _arrow3839(__unit: None=None, base_path: Any=base_path, c: Any=c) -> Async[FSharpResult_2[Contract, str]]:
        def _arrow3836(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
            path: str = combine(base_path, c.Path)
            def _arrow3835(__unit: None=None) -> Async[FSharpResult_2[Contract, str]]:
                return singleton.Return(FSharpResult_2(0, c))

            return singleton.Bind(delete_file_or_directory_async(path), _arrow3835)

        def _arrow3838(_arg_1: Exception) -> Async[FSharpResult_2[Contract, str]]:
            def _arrow3837(__unit: None=None) -> str:
                arg_1: str = str(_arg_1)
                return to_text(printf("Error deleting contract %s: %s"))(c.Path)(arg_1)

            return singleton.Return(FSharpResult_2(1, _arrow3837()))

        return singleton.TryWith(singleton.Delay(_arrow3836), _arrow3838)

    return catch_with(f, singleton.Delay(_arrow3839))


def full_fill_contract(base_path: str, c: Contract) -> Async[FSharpResult_2[Contract, str]]:
    def f(e: Exception, base_path: Any=base_path, c: Any=c) -> FSharpResult_2[Contract, str]:
        def _arrow3840(__unit: None=None, e: Any=e) -> str:
            arg_2: str = str(e)
            return to_text(printf("Error fulfilling contract %s: %s"))(c.Path)(arg_2)

        return FSharpResult_2(1, _arrow3840())

    def _arrow3841(__unit: None=None, base_path: Any=base_path, c: Any=c) -> Async[FSharpResult_2[Contract, str]]:
        match_value: str = c.Operation
        return singleton.ReturnFrom(fulfill_read_contract_async(base_path, c)) if (match_value == "READ") else (singleton.ReturnFrom(fulfill_write_contract_async(base_path, c)) if (match_value == "CREATE") else (singleton.ReturnFrom(fulfill_update_contract_async(base_path, c)) if (match_value == "UPDATE") else (singleton.ReturnFrom(fullfill_delete_contract_async(base_path, c)) if (match_value == "DELETE") else (singleton.ReturnFrom(fullfill_rename_contract_async(base_path, c)) if (match_value == "RENAME") else singleton.Return(FSharpResult_2(1, to_text(printf("Operation %A not supported"))(c.Operation)))))))

    return catch_with(f, singleton.Delay(_arrow3841))


def full_fill_contract_batch_async(base_path: str, cs: Array[Contract]) -> Async[FSharpResult_2[Array[Contract], Array[str]]]:
    def _arrow3842(base_path_1: str, c: Contract, base_path: Any=base_path, cs: Any=cs) -> Async[FSharpResult_2[Contract, str]]:
        return full_fill_contract(base_path_1, c)

    return fullfill_contract_batch_async_by(_arrow3842, base_path, cs)


__all__ = ["fulfill_read_contract_async", "fullfill_contract_batch_async_by", "fulfill_write_contract_async", "fulfill_update_contract_async", "fullfill_rename_contract_async", "fullfill_delete_contract_async", "full_fill_contract", "full_fill_contract_batch_async"]

