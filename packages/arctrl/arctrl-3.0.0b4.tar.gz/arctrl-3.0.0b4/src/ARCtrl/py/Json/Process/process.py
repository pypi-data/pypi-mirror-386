from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ...fable_modules.fable_library.list import (choose, singleton, of_array, FSharpList)
from ...fable_modules.fable_library.option import map
from ...fable_modules.fable_library.seq import map as map_1
from ...fable_modules.fable_library.string_ import replace
from ...fable_modules.fable_library.util import IEnumerable_1
from ...fable_modules.thoth_json_core.decode import (object, IOptionalGetter, string, list_1 as list_1_2, IGetters)
from ...fable_modules.thoth_json_core.encode import list_1 as list_1_1
from ...fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ...Core.comment import Comment
from ...Core.Process.process import Process
from ...Core.Process.process_input import ProcessInput
from ...Core.Process.process_output import ProcessOutput
from ...Core.Process.process_parameter_value import ProcessParameterValue
from ...Core.Process.protocol import Protocol
from ...Core.uri import URIModule_toString
from ..comment import (ROCrate_encoder as ROCrate_encoder_5, ROCrate_decoder as ROCrate_decoder_5, ISAJson_encoder as ISAJson_encoder_5, ISAJson_decoder as ISAJson_decoder_5)
from ..context.rocrate.isa_process_context import context_jsonvalue
from ..decode import Decode_uri
from ..encode import (try_include, try_include_list_opt)
from ..idtable import encode
from ..person import (ROCrate_encodeAuthorListString, ROCrate_decodeAuthorListString)
from .process_input import (ROCrate_encoder as ROCrate_encoder_3, ROCrate_decoder as ROCrate_decoder_3, ISAJson_encoder as ISAJson_encoder_3, ISAJson_decoder as ISAJson_decoder_3)
from .process_output import (ROCrate_encoder as ROCrate_encoder_4, ROCrate_decoder as ROCrate_decoder_4, ISAJson_encoder as ISAJson_encoder_4, ISAJson_decoder as ISAJson_decoder_4)
from .process_parameter_value import (ROCrate_encoder as ROCrate_encoder_2, ROCrate_decoder as ROCrate_decoder_2, ISAJson_encoder as ISAJson_encoder_2, ISAJson_decoder as ISAJson_decoder_2)
from .protocol import (ROCrate_encoder as ROCrate_encoder_1, ROCrate_decoder as ROCrate_decoder_1, ISAJson_encoder as ISAJson_encoder_1, ISAJson_decoder as ISAJson_decoder_1)

__A_ = TypeVar("__A_")

def ROCrate_genID(p: Process) -> str:
    match_value: str | None = p.ID
    if match_value is None:
        match_value_1: str | None = p.Name
        if match_value_1 is None:
            return "#EmptyProcess"

        else: 
            return "#Process_" + replace(match_value_1, " ", "_")


    else: 
        return URIModule_toString(match_value)



def ROCrate_encoder(study_name: str | None, assay_name: str | None, oa: Process) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow2733(__unit: None=None, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        value: str = ROCrate_genID(oa)
        class ObjectExpr2732(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr2732()

    class ObjectExpr2734(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> Any:
            return helpers_1.encode_string("Process")

    def _arrow2736(value_2: str, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        class ObjectExpr2735(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr2735()

    def _arrow2737(oa_1: Protocol, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_1(study_name, assay_name, oa.Name, oa_1)

    def _arrow2738(author_list: str, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        return ROCrate_encodeAuthorListString(author_list)

    def _arrow2740(value_4: str, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        class ObjectExpr2739(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_4)

        return ObjectExpr2739()

    def _arrow2741(value_6: ProcessInput, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_3(value_6)

    def _arrow2742(value_7: ProcessOutput, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_4(value_7)

    def _arrow2743(comment: Comment, study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_5(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2733()), ("@type", list_1_1(singleton(ObjectExpr2734()))), try_include("name", _arrow2736, oa.Name), try_include("executesProtocol", _arrow2737, oa.ExecutesProtocol), try_include_list_opt("parameterValues", ROCrate_encoder_2, oa.ParameterValues), try_include("performer", _arrow2738, oa.Performer), try_include("date", _arrow2740, oa.Date), try_include_list_opt("inputs", _arrow2741, oa.Inputs), try_include_list_opt("outputs", _arrow2742, oa.Outputs), try_include_list_opt("comments", _arrow2743, oa.Comments), ("@context", context_jsonvalue)]))
    class ObjectExpr2744(IEncodable):
        def Encode(self, helpers_4: IEncoderHelpers_1[Any], study_name: Any=study_name, assay_name: Any=assay_name, oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_4.encode_object(arg)

    return ObjectExpr2744()


def _arrow2754(get: IGetters) -> Process:
    def _arrow2745(__unit: None=None) -> str | None:
        object_arg: IOptionalGetter = get.Optional
        return object_arg.Field("@id", Decode_uri)

    def _arrow2746(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("name", string)

    def _arrow2747(__unit: None=None) -> Protocol | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("executesProtocol", ROCrate_decoder_1)

    def _arrow2748(__unit: None=None) -> FSharpList[ProcessParameterValue] | None:
        arg_7: Decoder_1[FSharpList[ProcessParameterValue]] = list_1_2(ROCrate_decoder_2)
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("parameterValues", arg_7)

    def _arrow2749(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("performer", ROCrate_decodeAuthorListString)

    def _arrow2750(__unit: None=None) -> str | None:
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("date", string)

    def _arrow2751(__unit: None=None) -> FSharpList[ProcessInput] | None:
        arg_13: Decoder_1[FSharpList[ProcessInput]] = list_1_2(ROCrate_decoder_3)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("inputs", arg_13)

    def _arrow2752(__unit: None=None) -> FSharpList[ProcessOutput] | None:
        arg_15: Decoder_1[FSharpList[ProcessOutput]] = list_1_2(ROCrate_decoder_4)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("outputs", arg_15)

    def _arrow2753(__unit: None=None) -> FSharpList[Comment] | None:
        arg_17: Decoder_1[FSharpList[Comment]] = list_1_2(ROCrate_decoder_5)
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("comments", arg_17)

    return Process(_arrow2745(), _arrow2746(), _arrow2747(), _arrow2748(), _arrow2749(), _arrow2750(), None, None, _arrow2751(), _arrow2752(), _arrow2753())


ROCrate_decoder: Decoder_1[Process] = object(_arrow2754)

def ISAJson_encoder(study_name: str | None, assay_name: str | None, id_map: Any | None, oa: Process) -> IEncodable:
    def f(oa_1: Process, study_name: Any=study_name, assay_name: Any=assay_name, id_map: Any=id_map, oa: Any=oa) -> IEncodable:
        def chooser(tupled_arg: tuple[str, IEncodable | None], oa_1: Any=oa_1) -> tuple[str, IEncodable] | None:
            def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
                return (tupled_arg[0], v_1)

            return map(mapping, tupled_arg[1])

        def _arrow2758(value: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2757(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                    return helpers.encode_string(value)

            return ObjectExpr2757()

        def _arrow2760(value_2: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2759(IEncodable):
                def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_1.encode_string(value_2)

            return ObjectExpr2759()

        def _arrow2761(oa_2: Protocol, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder_1(study_name, assay_name, oa_1.Name, id_map, oa_2)

        def _arrow2762(oa_3: ProcessParameterValue, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder_2(id_map, oa_3)

        def _arrow2764(value_4: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2763(IEncodable):
                def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_2.encode_string(value_4)

            return ObjectExpr2763()

        def _arrow2766(value_6: str, oa_1: Any=oa_1) -> IEncodable:
            class ObjectExpr2765(IEncodable):
                def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                    return helpers_3.encode_string(value_6)

            return ObjectExpr2765()

        def _arrow2767(oa_4: Process, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder(study_name, assay_name, id_map, oa_4)

        def _arrow2768(oa_5: Process, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder(study_name, assay_name, id_map, oa_5)

        def _arrow2769(value_8: ProcessInput, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder_3(id_map, value_8)

        def _arrow2770(value_9: ProcessOutput, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder_4(id_map, value_9)

        def _arrow2771(comment: Comment, oa_1: Any=oa_1) -> IEncodable:
            return ISAJson_encoder_5(id_map, comment)

        values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("@id", _arrow2758, ROCrate_genID(oa_1)), try_include("name", _arrow2760, oa_1.Name), try_include("executesProtocol", _arrow2761, oa_1.ExecutesProtocol), try_include_list_opt("parameterValues", _arrow2762, oa_1.ParameterValues), try_include("performer", _arrow2764, oa_1.Performer), try_include("date", _arrow2766, oa_1.Date), try_include("previousProcess", _arrow2767, oa_1.PreviousProcess), try_include("nextProcess", _arrow2768, oa_1.NextProcess), try_include_list_opt("inputs", _arrow2769, oa_1.Inputs), try_include_list_opt("outputs", _arrow2770, oa_1.Outputs), try_include_list_opt("comments", _arrow2771, oa_1.Comments)]))
        class ObjectExpr2772(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any], oa_1: Any=oa_1) -> Any:
                def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                    return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_4))

                arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
                return helpers_4.encode_object(arg)

        return ObjectExpr2772()

    if id_map is not None:
        def _arrow2773(p: Process, study_name: Any=study_name, assay_name: Any=assay_name, id_map: Any=id_map, oa: Any=oa) -> str:
            return ROCrate_genID(p)

        return encode(_arrow2773, f, oa, id_map)

    else: 
        return f(oa)



def _arrow2786(__unit: None=None) -> Decoder_1[Process]:
    def decode(__unit: None=None) -> Decoder_1[Process]:
        def _arrow2785(get: IGetters) -> Process:
            def _arrow2774(__unit: None=None) -> str | None:
                object_arg: IOptionalGetter = get.Optional
                return object_arg.Field("@id", Decode_uri)

            def _arrow2775(__unit: None=None) -> str | None:
                object_arg_1: IOptionalGetter = get.Optional
                return object_arg_1.Field("name", string)

            def _arrow2776(__unit: None=None) -> Protocol | None:
                object_arg_2: IOptionalGetter = get.Optional
                return object_arg_2.Field("executesProtocol", ISAJson_decoder_1)

            def _arrow2777(__unit: None=None) -> FSharpList[ProcessParameterValue] | None:
                arg_7: Decoder_1[FSharpList[ProcessParameterValue]] = list_1_2(ISAJson_decoder_2)
                object_arg_3: IOptionalGetter = get.Optional
                return object_arg_3.Field("parameterValues", arg_7)

            def _arrow2778(__unit: None=None) -> str | None:
                object_arg_4: IOptionalGetter = get.Optional
                return object_arg_4.Field("performer", string)

            def _arrow2779(__unit: None=None) -> str | None:
                object_arg_5: IOptionalGetter = get.Optional
                return object_arg_5.Field("date", string)

            def _arrow2780(__unit: None=None) -> Process | None:
                arg_13: Decoder_1[Process] = decode(None)
                object_arg_6: IOptionalGetter = get.Optional
                return object_arg_6.Field("previousProcess", arg_13)

            def _arrow2781(__unit: None=None) -> Process | None:
                arg_15: Decoder_1[Process] = decode(None)
                object_arg_7: IOptionalGetter = get.Optional
                return object_arg_7.Field("nextProcess", arg_15)

            def _arrow2782(__unit: None=None) -> FSharpList[ProcessInput] | None:
                arg_17: Decoder_1[FSharpList[ProcessInput]] = list_1_2(ISAJson_decoder_3)
                object_arg_8: IOptionalGetter = get.Optional
                return object_arg_8.Field("inputs", arg_17)

            def _arrow2783(__unit: None=None) -> FSharpList[ProcessOutput] | None:
                arg_19: Decoder_1[FSharpList[ProcessOutput]] = list_1_2(ISAJson_decoder_4)
                object_arg_9: IOptionalGetter = get.Optional
                return object_arg_9.Field("outputs", arg_19)

            def _arrow2784(__unit: None=None) -> FSharpList[Comment] | None:
                arg_21: Decoder_1[FSharpList[Comment]] = list_1_2(ISAJson_decoder_5)
                object_arg_10: IOptionalGetter = get.Optional
                return object_arg_10.Field("comments", arg_21)

            return Process(_arrow2774(), _arrow2775(), _arrow2776(), _arrow2777(), _arrow2778(), _arrow2779(), _arrow2780(), _arrow2781(), _arrow2782(), _arrow2783(), _arrow2784())

        return object(_arrow2785)

    return decode(None)


ISAJson_decoder: Decoder_1[Process] = _arrow2786()

__all__ = ["ROCrate_genID", "ROCrate_encoder", "ROCrate_decoder", "ISAJson_encoder", "ISAJson_decoder"]

