from __future__ import annotations
from collections.abc import Callable
from typing import Any
from ...Core.Process.factor import Factor
from ...Json.encode import default_spaces
from ...Json.Process.factor import (decoder as decoder_1, encoder)
from ...fable_modules.fable_library.result import FSharpResult_2
from ...fable_modules.fable_library.string_ import (to_text, printf)
from ...fable_modules.thoth_json_core.types import IEncodable
from ...fable_modules.thoth_json_python.decode import Decode_fromString
from ...fable_modules.thoth_json_python.encode import to_string

def ARCtrl_Process_Factor__Factor_fromISAJsonString_Static_Z721C83C5(s: str) -> Factor:
    match_value: FSharpResult_2[Factor, str] = Decode_fromString(decoder_1, s)
    if match_value.tag == 1:
        raise Exception(to_text(printf("Error decoding string: %O"))(match_value.fields[0]))

    else: 
        return match_value.fields[0]



def ARCtrl_Process_Factor__Factor_toISAJsonString_Static_71136F3F(spaces: int | None=None) -> Callable[[Factor], str]:
    def _arrow3552(f: Factor, spaces: Any=spaces) -> str:
        value: IEncodable = encoder(None, f)
        return to_string(default_spaces(spaces), value)

    return _arrow3552


def ARCtrl_Process_Factor__Factor_ToISAJsonString_71136F3F(this: Factor, spaces: int | None=None) -> str:
    return ARCtrl_Process_Factor__Factor_toISAJsonString_Static_71136F3F(spaces)(this)


__all__ = ["ARCtrl_Process_Factor__Factor_fromISAJsonString_Static_Z721C83C5", "ARCtrl_Process_Factor__Factor_toISAJsonString_Static_71136F3F", "ARCtrl_Process_Factor__Factor_ToISAJsonString_71136F3F"]

