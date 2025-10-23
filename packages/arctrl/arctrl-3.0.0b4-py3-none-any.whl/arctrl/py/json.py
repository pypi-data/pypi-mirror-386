from __future__ import annotations
from collections.abc import Callable
from .Core.arc_types import (ArcAssay, ArcStudy, ArcInvestigation)
from .Core.ontology_annotation import OntologyAnnotation
from .ROCrate.ldobject import (LDGraph, LDNode)
from .arc import ARC
from .JsonIO.assay import (ARCtrl_ArcAssay__ArcAssay_fromJsonString_Static_Z721C83C5, ARCtrl_ArcAssay__ArcAssay_fromCompressedJsonString_Static_Z721C83C5, ARCtrl_ArcAssay__ArcAssay_fromISAJsonString_Static_Z721C83C5, ARCtrl_ArcAssay__ArcAssay_fromROCrateJsonString_Static_Z721C83C5, ARCtrl_ArcAssay__ArcAssay_toJsonString_Static_71136F3F, ARCtrl_ArcAssay__ArcAssay_toCompressedJsonString_Static_71136F3F, ARCtrl_ArcAssay__ArcAssay_toISAJsonString_Static_Z3B036AA, ARCtrl_ArcAssay__ArcAssay_toROCrateJsonString_Static_5CABCA47)
from .JsonIO.investigation import (ARCtrl_ArcInvestigation__ArcInvestigation_fromJsonString_Static_Z721C83C5, ARCtrl_ArcInvestigation__ArcInvestigation_fromCompressedJsonString_Static_Z721C83C5, ARCtrl_ArcInvestigation__ArcInvestigation_fromISAJsonString_Static_Z721C83C5, ARCtrl_ArcInvestigation__ArcInvestigation_fromROCrateJsonString_Static_Z721C83C5, ARCtrl_ArcInvestigation__ArcInvestigation_toJsonString_Static_71136F3F, ARCtrl_ArcInvestigation__ArcInvestigation_toCompressedJsonString_Static_71136F3F, ARCtrl_ArcInvestigation__ArcInvestigation_toISAJsonString_Static_Z3B036AA, ARCtrl_ArcInvestigation__ArcInvestigation_toROCrateJsonString_Static_71136F3F)
from .JsonIO.ldobject import (ARCtrl_ROCrate_LDGraph__LDGraph_fromROCrateJsonString_Static_Z721C83C5, ARCtrl_ROCrate_LDGraph__LDGraph_toROCrateJsonString_Static_71136F3F, ARCtrl_ROCrate_LDNode__LDNode_fromROCrateJsonString_Static_Z721C83C5, ARCtrl_ROCrate_LDNode__LDNode_toROCrateJsonString_Static_71136F3F)
from .JsonIO.ontology_annotation import (ARCtrl_OntologyAnnotation__OntologyAnnotation_fromJsonString_Static_Z721C83C5, ARCtrl_OntologyAnnotation__OntologyAnnotation_fromISAJsonString_Static_Z721C83C5, ARCtrl_OntologyAnnotation__OntologyAnnotation_fromROCrateJsonString_Static_Z721C83C5, ARCtrl_OntologyAnnotation__OntologyAnnotation_toJsonString_Static_71136F3F, ARCtrl_OntologyAnnotation__OntologyAnnotation_toISAJsonString_Static_71136F3F, ARCtrl_OntologyAnnotation__OntologyAnnotation_toROCrateJsonString_Static_71136F3F)
from .JsonIO.study import (ARCtrl_ArcStudy__ArcStudy_fromJsonString_Static_Z721C83C5, ARCtrl_ArcStudy__ArcStudy_fromCompressedJsonString_Static_Z721C83C5, ARCtrl_ArcStudy__ArcStudy_fromISAJsonString_Static_Z721C83C5, ARCtrl_ArcStudy__ArcStudy_fromROCrateJsonString_Static_Z721C83C5, ARCtrl_ArcStudy__ArcStudy_toJsonString_Static_71136F3F, ARCtrl_ArcStudy__ArcStudy_toCompressedJsonString_Static_71136F3F, ARCtrl_ArcStudy__ArcStudy_toISAJsonString_Static_Z3FD920F1, ARCtrl_ArcStudy__ArcStudy_toROCrateJsonString_Static_3BA23086)
from .fable_modules.fable_library.list import FSharpList
from .fable_modules.fable_library.reflection import (TypeInfo, class_type)

def _expr3803() -> TypeInfo:
    return class_type("ARCtrl.JsonHelper.OntologyAnnotationJson", None, JsonHelper_OntologyAnnotationJson)


class JsonHelper_OntologyAnnotationJson:
    def __init__(self, __unit: None=None) -> None:
        pass

    def from_json_string(self, s: str) -> OntologyAnnotation:
        return ARCtrl_OntologyAnnotation__OntologyAnnotation_fromJsonString_Static_Z721C83C5(s)

    def from_isajson_string(self, s: str) -> OntologyAnnotation:
        return ARCtrl_OntologyAnnotation__OntologyAnnotation_fromISAJsonString_Static_Z721C83C5(s)

    def from_rocrate_json_string(self, s: str) -> OntologyAnnotation:
        return ARCtrl_OntologyAnnotation__OntologyAnnotation_fromROCrateJsonString_Static_Z721C83C5(s)

    def to_json_string(self, oa: OntologyAnnotation, spaces: int | None=None) -> str:
        return ARCtrl_OntologyAnnotation__OntologyAnnotation_toJsonString_Static_71136F3F(spaces)(oa)

    def to_isajson_string(self, oa: OntologyAnnotation, spaces: int | None=None) -> str:
        return ARCtrl_OntologyAnnotation__OntologyAnnotation_toISAJsonString_Static_71136F3F(spaces)(oa)

    def to_rocrate_json_string(self, oa: OntologyAnnotation, spaces: int | None=None) -> str:
        return ARCtrl_OntologyAnnotation__OntologyAnnotation_toROCrateJsonString_Static_71136F3F(spaces)(oa)


JsonHelper_OntologyAnnotationJson_reflection = _expr3803

def JsonHelper_OntologyAnnotationJson__ctor(__unit: None=None) -> JsonHelper_OntologyAnnotationJson:
    return JsonHelper_OntologyAnnotationJson(__unit)


def _expr3804() -> TypeInfo:
    return class_type("ARCtrl.JsonHelper.AssayJson", None, JsonHelper_AssayJson)


class JsonHelper_AssayJson:
    def __init__(self, __unit: None=None) -> None:
        pass

    def from_json_string(self, s: str) -> ArcAssay:
        return ARCtrl_ArcAssay__ArcAssay_fromJsonString_Static_Z721C83C5(s)

    def from_compressed_json_string(self, s: str) -> ArcAssay:
        return ARCtrl_ArcAssay__ArcAssay_fromCompressedJsonString_Static_Z721C83C5(s)

    def from_isajson_string(self, s: str) -> ArcAssay:
        return ARCtrl_ArcAssay__ArcAssay_fromISAJsonString_Static_Z721C83C5(s)

    def from_rocrate_json_string(self, s: str) -> ArcAssay:
        return ARCtrl_ArcAssay__ArcAssay_fromROCrateJsonString_Static_Z721C83C5(s)

    def to_json_string(self, assay: ArcAssay, spaces: int | None=None) -> str:
        return ARCtrl_ArcAssay__ArcAssay_toJsonString_Static_71136F3F(spaces)(assay)

    def to_compressed_json_string(self, assay: ArcAssay, spaces: int | None=None) -> str:
        return ARCtrl_ArcAssay__ArcAssay_toCompressedJsonString_Static_71136F3F(spaces)(assay)

    def to_isajson_string(self, assay: ArcAssay, spaces: int | None=None, use_idreferencing: bool | None=None) -> str:
        return ARCtrl_ArcAssay__ArcAssay_toISAJsonString_Static_Z3B036AA(spaces, use_idreferencing)(assay)

    def to_rocrate_json_string(self, assay: ArcAssay, study_name: str, spaces: int | None=None) -> str:
        return ARCtrl_ArcAssay__ArcAssay_toROCrateJsonString_Static_5CABCA47(study_name, spaces)(assay)


JsonHelper_AssayJson_reflection = _expr3804

def JsonHelper_AssayJson__ctor(__unit: None=None) -> JsonHelper_AssayJson:
    return JsonHelper_AssayJson(__unit)


def _expr3805() -> TypeInfo:
    return class_type("ARCtrl.JsonHelper.StudyJson", None, JsonHelper_StudyJson)


class JsonHelper_StudyJson:
    def __init__(self, __unit: None=None) -> None:
        pass

    def from_json_string(self, s: str) -> ArcStudy:
        return ARCtrl_ArcStudy__ArcStudy_fromJsonString_Static_Z721C83C5(s)

    def from_compressed_json_string(self, s: str) -> ArcStudy:
        return ARCtrl_ArcStudy__ArcStudy_fromCompressedJsonString_Static_Z721C83C5(s)

    def from_isajson_string(self, s: str) -> tuple[ArcStudy, FSharpList[ArcAssay]]:
        return ARCtrl_ArcStudy__ArcStudy_fromISAJsonString_Static_Z721C83C5(s)

    def from_rocrate_json_string(self, s: str) -> tuple[ArcStudy, FSharpList[ArcAssay]]:
        return ARCtrl_ArcStudy__ArcStudy_fromROCrateJsonString_Static_Z721C83C5(s)

    def to_json_string(self, study: ArcStudy, spaces: int | None=None) -> str:
        return ARCtrl_ArcStudy__ArcStudy_toJsonString_Static_71136F3F(spaces)(study)

    def to_compressed_json_string(self, study: ArcStudy, spaces: int | None=None) -> str:
        return ARCtrl_ArcStudy__ArcStudy_toCompressedJsonString_Static_71136F3F(spaces)(study)

    def to_isajson_string(self, study: ArcStudy, assays: FSharpList[ArcAssay] | None=None, spaces: int | None=None, use_idreferencing: bool | None=None) -> str:
        return ARCtrl_ArcStudy__ArcStudy_toISAJsonString_Static_Z3FD920F1(assays, spaces, use_idreferencing)(study)

    def to_rocrate_json_string(self, study: ArcStudy, assays: FSharpList[ArcAssay] | None=None, spaces: int | None=None) -> str:
        return ARCtrl_ArcStudy__ArcStudy_toROCrateJsonString_Static_3BA23086(assays, spaces)(study)


JsonHelper_StudyJson_reflection = _expr3805

def JsonHelper_StudyJson__ctor(__unit: None=None) -> JsonHelper_StudyJson:
    return JsonHelper_StudyJson(__unit)


def _expr3806() -> TypeInfo:
    return class_type("ARCtrl.JsonHelper.InvestigationJson", None, JsonHelper_InvestigationJson)


class JsonHelper_InvestigationJson:
    def __init__(self, __unit: None=None) -> None:
        pass

    def from_json_string(self, s: str) -> ArcInvestigation:
        return ARCtrl_ArcInvestigation__ArcInvestigation_fromJsonString_Static_Z721C83C5(s)

    def from_compressed_json_string(self, s: str) -> ArcInvestigation:
        return ARCtrl_ArcInvestigation__ArcInvestigation_fromCompressedJsonString_Static_Z721C83C5(s)

    def from_isajson_string(self, s: str) -> ArcInvestigation:
        return ARCtrl_ArcInvestigation__ArcInvestigation_fromISAJsonString_Static_Z721C83C5(s)

    def from_rocrate_json_string(self, s: str) -> ArcInvestigation:
        return ARCtrl_ArcInvestigation__ArcInvestigation_fromROCrateJsonString_Static_Z721C83C5(s)

    def to_json_string(self, investigation: ArcInvestigation, spaces: int | None=None) -> str:
        return ARCtrl_ArcInvestigation__ArcInvestigation_toJsonString_Static_71136F3F(spaces)(investigation)

    def to_compressed_json_string(self, investigation: ArcInvestigation, spaces: int | None=None) -> str:
        return ARCtrl_ArcInvestigation__ArcInvestigation_toCompressedJsonString_Static_71136F3F(spaces)(investigation)

    def to_isajson_string(self, investigation: ArcInvestigation, spaces: int | None=None, use_idreferencing: bool | None=None) -> str:
        return ARCtrl_ArcInvestigation__ArcInvestigation_toISAJsonString_Static_Z3B036AA(spaces, use_idreferencing)(investigation)

    def to_rocrate_json_string(self, investigation: ArcInvestigation, spaces: int | None=None) -> str:
        return ARCtrl_ArcInvestigation__ArcInvestigation_toROCrateJsonString_Static_71136F3F(spaces)(investigation)


JsonHelper_InvestigationJson_reflection = _expr3806

def JsonHelper_InvestigationJson__ctor(__unit: None=None) -> JsonHelper_InvestigationJson:
    return JsonHelper_InvestigationJson(__unit)


def _expr3807() -> TypeInfo:
    return class_type("ARCtrl.JsonHelper.ARCJson", None, JsonHelper_ARCJson)


class JsonHelper_ARCJson:
    def __init__(self, __unit: None=None) -> None:
        pass

    def from_rocrate_json_string(self, s: str) -> ARC:
        return ARC.from_rocrate_json_string(s)

    def to_rocrate_json_string(self, spaces: int | None=None) -> Callable[[ARC], str]:
        return ARC.to_rocrate_json_string(spaces)


JsonHelper_ARCJson_reflection = _expr3807

def JsonHelper_ARCJson__ctor(__unit: None=None) -> JsonHelper_ARCJson:
    return JsonHelper_ARCJson(__unit)


def _expr3808() -> TypeInfo:
    return class_type("ARCtrl.JsonHelper.LDGraphJson", None, JsonHelper_LDGraphJson)


class JsonHelper_LDGraphJson:
    def __init__(self, __unit: None=None) -> None:
        pass

    def from_rocrate_json_string(self, s: str) -> LDGraph:
        return ARCtrl_ROCrate_LDGraph__LDGraph_fromROCrateJsonString_Static_Z721C83C5(s)

    def to_rocrate_json_string(self, spaces: int | None=None) -> Callable[[LDGraph], str]:
        return ARCtrl_ROCrate_LDGraph__LDGraph_toROCrateJsonString_Static_71136F3F(spaces)


JsonHelper_LDGraphJson_reflection = _expr3808

def JsonHelper_LDGraphJson__ctor(__unit: None=None) -> JsonHelper_LDGraphJson:
    return JsonHelper_LDGraphJson(__unit)


def _expr3809() -> TypeInfo:
    return class_type("ARCtrl.JsonHelper.LDNodeJson", None, JsonHelper_LDNodeJson)


class JsonHelper_LDNodeJson:
    def __init__(self, __unit: None=None) -> None:
        pass

    def from_rocrate_json_string(self, s: str) -> LDNode:
        return ARCtrl_ROCrate_LDNode__LDNode_fromROCrateJsonString_Static_Z721C83C5(s)

    def to_rocrate_json_string(self, spaces: int | None=None) -> Callable[[LDNode], str]:
        return ARCtrl_ROCrate_LDNode__LDNode_toROCrateJsonString_Static_71136F3F(spaces)


JsonHelper_LDNodeJson_reflection = _expr3809

def JsonHelper_LDNodeJson__ctor(__unit: None=None) -> JsonHelper_LDNodeJson:
    return JsonHelper_LDNodeJson(__unit)


def _expr3810() -> TypeInfo:
    return class_type("ARCtrl.JsonController", None, JsonController)


class JsonController:
    @staticmethod
    def OntologyAnnotation() -> JsonHelper_OntologyAnnotationJson:
        return JsonHelper_OntologyAnnotationJson()

    @staticmethod
    def Assay() -> JsonHelper_AssayJson:
        return JsonHelper_AssayJson()

    @staticmethod
    def Study() -> JsonHelper_StudyJson:
        return JsonHelper_StudyJson()

    @staticmethod
    def Investigation() -> JsonHelper_InvestigationJson:
        return JsonHelper_InvestigationJson()

    @staticmethod
    def ARC() -> JsonHelper_ARCJson:
        return JsonHelper_ARCJson()

    @staticmethod
    def LDGraph() -> JsonHelper_LDGraphJson:
        return JsonHelper_LDGraphJson()

    @staticmethod
    def LDNode() -> JsonHelper_LDNodeJson:
        return JsonHelper_LDNodeJson()


JsonController_reflection = _expr3810

__all__ = ["JsonHelper_OntologyAnnotationJson_reflection", "JsonHelper_AssayJson_reflection", "JsonHelper_StudyJson_reflection", "JsonHelper_InvestigationJson_reflection", "JsonHelper_ARCJson_reflection", "JsonHelper_LDGraphJson_reflection", "JsonHelper_LDNodeJson_reflection", "JsonController_reflection"]

