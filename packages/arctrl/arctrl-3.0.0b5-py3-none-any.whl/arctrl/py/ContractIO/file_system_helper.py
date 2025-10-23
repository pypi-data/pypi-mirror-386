from __future__ import annotations
from collections.abc import Callable
from pathlib import Path
import shutil
import os
from typing import Any
from ..cross_async import all
from ..fable_modules.fable_library.array_ import map
from ..fable_modules.fable_library.async_builder import (singleton, Async)
from ..fable_modules.fable_library.seq import (is_empty, empty, map as map_1, concat, append, to_array)
from ..fable_modules.fable_library.string_ import (starts_with_exact, trim as trim_1, replace, substring)
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import (IEnumerable_1, to_enumerable)
from ..fable_modules.fs_spreadsheet.fs_workbook import FsWorkbook
from ..fable_modules.fs_spreadsheet_py.fs_extension import (FsSpreadsheet_FsWorkbook__FsWorkbook_fromXlsxFile_Static_Z721C83C5, FsSpreadsheet_FsWorkbook__FsWorkbook_toXlsxFile_Static)

shutil

os

Path

def directory_exists_async(path: str) -> Async[bool]:
    def _arrow3756(__unit: None=None, path: Any=path) -> Async[bool]:
        return singleton.Return(Path(path).is_dir())

    return singleton.Delay(_arrow3756)


def create_directory_async(path: str) -> Async[None]:
    def _arrow3757(__unit: None=None, path: Any=path) -> Async[None]:
        Path(path).mkdir(parents=True, exist_ok=True)
        return singleton.Zero()

    return singleton.Delay(_arrow3757)


def ensure_directory_async(path: str) -> Async[None]:
    def _arrow3759(__unit: None=None, path: Any=path) -> Async[None]:
        def _arrow3758(_arg: bool) -> Async[None]:
            return singleton.ReturnFrom(create_directory_async(path)) if (not _arg) else singleton.Zero()

        return singleton.Bind(directory_exists_async(path), _arrow3758)

    return singleton.Delay(_arrow3759)


def ensure_directory_of_file_async(file_path: str) -> Async[None]:
    def _arrow3760(__unit: None=None, file_path: Any=file_path) -> Async[None]:
        return singleton.ReturnFrom(ensure_directory_async(Path(file_path).parent))

    return singleton.Delay(_arrow3760)


def file_exists_async(path: str) -> Async[bool]:
    def _arrow3761(__unit: None=None, path: Any=path) -> Async[bool]:
        return singleton.Return(Path(path).is_file())

    return singleton.Delay(_arrow3761)


def read_file_text_async(path: str) -> Async[str]:
    def _arrow3763(__unit: None=None, path: Any=path) -> Async[str]:
        def _arrow3762(__unit: None=None) -> str:
            with open(path, 'r', encoding='utf-8') as f: return f.read()

        return singleton.Return(_arrow3762())

    return singleton.Delay(_arrow3763)


def read_file_binary_async(path: str) -> Async[bytearray]:
    def _arrow3765(__unit: None=None, path: Any=path) -> Async[bytearray]:
        def _arrow3764(__unit: None=None) -> bytearray:
            with open(path, 'rb') as f: return f.read()

        return singleton.Return(_arrow3764())

    return singleton.Delay(_arrow3765)


def read_file_xlsx_async(path: str) -> Async[FsWorkbook]:
    def _arrow3766(__unit: None=None, path: Any=path) -> Async[FsWorkbook]:
        return singleton.Return(FsSpreadsheet_FsWorkbook__FsWorkbook_fromXlsxFile_Static_Z721C83C5(path))

    return singleton.Delay(_arrow3766)


def move_file_async(old_path: str, new_path: str) -> Async[None]:
    def _arrow3767(__unit: None=None, old_path: Any=old_path, new_path: Any=new_path) -> Async[None]:
        shutil.move(old_path, new_path)
        return singleton.Zero()

    return singleton.Delay(_arrow3767)


def move_directory_async(old_path: str, new_path: str) -> Async[None]:
    return move_file_async(old_path, new_path)


def delete_file_async(path: str) -> Async[None]:
    def _arrow3768(__unit: None=None, path: Any=path) -> Async[None]:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        return singleton.Zero()

    return singleton.Delay(_arrow3768)


def delete_directory_async(path: str) -> Async[None]:
    def _arrow3769(__unit: None=None, path: Any=path) -> Async[None]:
        shutil.rmtree(path, ignore_errors=True)
        return singleton.Zero()

    return singleton.Delay(_arrow3769)


def write_file_text_async(path: str, text: str) -> Async[None]:
    def _arrow3770(__unit: None=None, path: Any=path, text: Any=text) -> Async[None]:
        with open(path, 'w') as f: f.write(text)
        return singleton.Zero()

    return singleton.Delay(_arrow3770)


def write_file_binary_async(path: str, bytes: bytearray) -> Async[None]:
    def _arrow3771(__unit: None=None, path: Any=path, bytes: Any=bytes) -> Async[None]:
        with open(path, 'wb') as f: f.write(bytes)
        return singleton.Zero()

    return singleton.Delay(_arrow3771)


def write_file_xlsx_async(path: str, wb: FsWorkbook) -> Async[None]:
    def _arrow3772(__unit: None=None, path: Any=path, wb: Any=wb) -> Async[None]:
        FsSpreadsheet_FsWorkbook__FsWorkbook_toXlsxFile_Static(path, wb)
        return singleton.Zero()

    return singleton.Delay(_arrow3772)


def trim(path: str) -> str:
    if starts_with_exact(path, "./"):
        return trim_1(replace(path, "./", ""), "/")

    else: 
        return trim_1(path, "/")



def make_relative(directory_path: str, path: str) -> str:
    if True if (True if (directory_path == ".") else (directory_path == "/")) else (directory_path == ""):
        return path

    else: 
        directory_path_1: str = trim(directory_path)
        path_1: str = trim(path)
        if starts_with_exact(path_1, directory_path_1):
            return substring(path_1, len(directory_path_1))

        else: 
            return path_1




def standardize_slashes(path: str) -> str:
    return replace(path, "\\", "/")


def get_sub_directories_async(path: str) -> Async[Array[str]]:
    def _arrow3773(__unit: None=None, path: Any=path) -> Async[Array[str]]:
        paths: Array[str] = [str(entry) for entry in Path(path).iterdir() if entry.is_dir()]
        return singleton.Return(map(standardize_slashes, paths, None))

    return singleton.Delay(_arrow3773)


def get_sub_files_async(path: str) -> Async[Array[str]]:
    def _arrow3774(__unit: None=None, path: Any=path) -> Async[Array[str]]:
        paths: Array[str] = [str(entry) for entry in Path(path).iterdir() if entry.is_file()]
        return singleton.Return(map(standardize_slashes, paths, None))

    return singleton.Delay(_arrow3774)


def get_all_file_paths_async(directory_path: str) -> Async[Array[str]]:
    directory_path_1: str = standardize_slashes(directory_path)
    def _arrow3780(__unit: None=None, directory_path: Any=directory_path) -> Async[Array[str]]:
        def all_files(dirs: IEnumerable_1[str]) -> Async[IEnumerable_1[str]]:
            def _arrow3778(__unit: None=None, dirs: Any=dirs) -> Async[IEnumerable_1[str]]:
                def _arrow3777(_arg: Array[Array[str]]) -> Async[IEnumerable_1[str]]:
                    sub_files_1: IEnumerable_1[str] = concat(_arg)
                    def _arrow3776(_arg_1: Array[Array[str]]) -> Async[IEnumerable_1[str]]:
                        def _arrow3775(_arg_2: Array[IEnumerable_1[str]]) -> Async[IEnumerable_1[str]]:
                            sub_dir_contents_1: IEnumerable_1[str] = concat(_arg_2)
                            return singleton.Return(append(sub_dir_contents_1, sub_files_1))

                        return singleton.Bind(all(map_1(all_files, _arg_1)), _arrow3775)

                    return singleton.Bind(all(map_1(get_sub_directories_async, dirs)), _arrow3776)

                return singleton.Return(empty()) if is_empty(dirs) else singleton.Bind(all(map_1(get_sub_files_async, dirs)), _arrow3777)

            return singleton.Delay(_arrow3778)

        def _arrow3779(_arg_3: IEnumerable_1[str]) -> Async[Array[str]]:
            def mapping_1(arg_2: str) -> str:
                return standardize_slashes(make_relative(directory_path_1, arg_2))

            all_files_relative: Array[str] = map(mapping_1, to_array(_arg_3), None)
            return singleton.Return(all_files_relative)

        return singleton.Bind(all_files(to_enumerable([directory_path_1])), _arrow3779)

    return singleton.Delay(_arrow3780)


def rename_file_or_directory_async(old_path: str, new_path: str) -> Async[None]:
    def _arrow3783(__unit: None=None, old_path: Any=old_path, new_path: Any=new_path) -> Async[None]:
        def _arrow3782(_arg: bool) -> Async[None]:
            def _arrow3781(_arg_1: bool) -> Async[None]:
                if _arg:
                    return singleton.ReturnFrom(move_file_async(old_path, new_path))

                elif _arg_1:
                    return singleton.ReturnFrom(move_directory_async(old_path, new_path))

                else: 
                    return singleton.Zero()


            return singleton.Bind(directory_exists_async(old_path), _arrow3781)

        return singleton.Bind(file_exists_async(old_path), _arrow3782)

    return singleton.Delay(_arrow3783)


def delete_file_or_directory_async(path: str) -> Async[None]:
    def _arrow3786(__unit: None=None, path: Any=path) -> Async[None]:
        def _arrow3785(_arg: bool) -> Async[None]:
            def _arrow3784(_arg_1: bool) -> Async[None]:
                if _arg:
                    return singleton.ReturnFrom(delete_file_async(path))

                elif _arg_1:
                    return singleton.ReturnFrom(delete_directory_async(path))

                else: 
                    return singleton.Zero()


            return singleton.Bind(directory_exists_async(path), _arrow3784)

        return singleton.Bind(file_exists_async(path), _arrow3785)

    return singleton.Delay(_arrow3786)


__all__ = ["directory_exists_async", "create_directory_async", "ensure_directory_async", "ensure_directory_of_file_async", "file_exists_async", "read_file_text_async", "read_file_binary_async", "read_file_xlsx_async", "move_file_async", "move_directory_async", "delete_file_async", "delete_directory_async", "write_file_text_async", "write_file_binary_async", "write_file_xlsx_async", "trim", "make_relative", "standardize_slashes", "get_sub_directories_async", "get_sub_files_async", "get_all_file_paths_async", "rename_file_or_directory_async", "delete_file_or_directory_async"]

