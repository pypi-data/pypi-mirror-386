from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.date import (today, to_string)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList, unzip, empty)
from ..fable_modules.fable_library.option import (map, default_arg)
from ..fable_modules.fable_library.seq import (map as map_1, concat)
from ..fable_modules.fable_library.seq2 import distinct_by
from ..fable_modules.fable_library.types import Array
from ..fable_modules.fable_library.util import (IEnumerable_1, string_hash)
from ..fable_modules.thoth_json_core.decode import (object, IRequiredGetter, string, IOptionalGetter, resize_array, IGetters, list_1 as list_1_1)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.arc_types import (ArcAssay, ArcStudy, ArcInvestigation)
from ..Core.comment import Comment
from ..Core.Helper.identifier import create_missing_identifier
from ..Core.ontology_annotation import OntologyAnnotation
from ..Core.ontology_source_reference import OntologySourceReference
from ..Core.person import Person
from ..Core.publication import Publication
from ..Core.Table.composite_cell import CompositeCell
from .assay import (encoder as encoder_4, decoder as decoder_6, encoder_compressed as encoder_compressed_1, decoder_compressed as decoder_compressed_1)
from .comment import (encoder as encoder_6, decoder as decoder_8, ROCrate_encoder as ROCrate_encoder_5, ROCrate_decoder as ROCrate_decoder_5, ISAJson_encoder as ISAJson_encoder_5, ISAJson_decoder as ISAJson_decoder_5)
from .context.rocrate.isa_investigation_context import context_jsonvalue
from .context.rocrate.rocrate_context import (conforms_to_jsonvalue, context_jsonvalue as context_jsonvalue_1)
from .decode import Decode_objectNoAdditionalProperties
from .encode import (try_include, try_include_seq)
from .ontology_source_reference import (encoder as encoder_1, decoder as decoder_3, ROCrate_encoder as ROCrate_encoder_1, ROCrate_decoder as ROCrate_decoder_2, ISAJson_encoder as ISAJson_encoder_1, ISAJson_decoder as ISAJson_decoder_2)
from .person import (encoder as encoder_3, decoder as decoder_5, ROCrate_encoder as ROCrate_encoder_3, ROCrate_decoder as ROCrate_decoder_4, ISAJson_encoder as ISAJson_encoder_3, ISAJson_decoder as ISAJson_decoder_4)
from .publication import (encoder as encoder_2, decoder as decoder_4, ROCrate_encoder as ROCrate_encoder_2, ROCrate_decoder as ROCrate_decoder_3, ISAJson_encoder as ISAJson_encoder_2, ISAJson_decoder as ISAJson_decoder_3)
from .study import (encoder as encoder_5, decoder as decoder_7, encoder_compressed as encoder_compressed_2, decoder_compressed as decoder_compressed_2, ROCrate_encoder as ROCrate_encoder_4, ROCrate_decoder as ROCrate_decoder_1, ISAJson_encoder as ISAJson_encoder_4, ISAJson_decoder as ISAJson_decoder_1)

__A_ = TypeVar("__A_")

def encoder(inv: ArcInvestigation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], inv: Any=inv) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3207(__unit: None=None, inv: Any=inv) -> IEncodable:
        value: str = inv.Identifier
        class ObjectExpr3206(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3206()

    def _arrow3209(value_1: str, inv: Any=inv) -> IEncodable:
        class ObjectExpr3208(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3208()

    def _arrow3211(value_3: str, inv: Any=inv) -> IEncodable:
        class ObjectExpr3210(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3210()

    def _arrow3213(value_5: str, inv: Any=inv) -> IEncodable:
        class ObjectExpr3212(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3212()

    def _arrow3215(value_7: str, inv: Any=inv) -> IEncodable:
        class ObjectExpr3214(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_7)

        return ObjectExpr3214()

    def _arrow3216(osr: OntologySourceReference, inv: Any=inv) -> IEncodable:
        return encoder_1(osr)

    def _arrow3217(oa: Publication, inv: Any=inv) -> IEncodable:
        return encoder_2(oa)

    def _arrow3218(person: Person, inv: Any=inv) -> IEncodable:
        return encoder_3(person)

    def _arrow3219(assay: ArcAssay, inv: Any=inv) -> IEncodable:
        return encoder_4(assay)

    def _arrow3220(study: ArcStudy, inv: Any=inv) -> IEncodable:
        return encoder_5(study)

    def _arrow3222(value_9: str, inv: Any=inv) -> IEncodable:
        class ObjectExpr3221(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_9)

        return ObjectExpr3221()

    def _arrow3223(comment: Comment, inv: Any=inv) -> IEncodable:
        return encoder_6(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3207()), try_include("Title", _arrow3209, inv.Title), try_include("Description", _arrow3211, inv.Description), try_include("SubmissionDate", _arrow3213, inv.SubmissionDate), try_include("PublicReleaseDate", _arrow3215, inv.PublicReleaseDate), try_include_seq("OntologySourceReferences", _arrow3216, inv.OntologySourceReferences), try_include_seq("Publications", _arrow3217, inv.Publications), try_include_seq("Contacts", _arrow3218, inv.Contacts), try_include_seq("Assays", _arrow3219, inv.Assays), try_include_seq("Studies", _arrow3220, inv.Studies), try_include_seq("RegisteredStudyIdentifiers", _arrow3222, inv.RegisteredStudyIdentifiers), try_include_seq("Comments", _arrow3223, inv.Comments)]))
    class ObjectExpr3224(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], inv: Any=inv) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr3224()


def _arrow3237(get: IGetters) -> ArcInvestigation:
    def _arrow3225(__unit: None=None) -> str:
        object_arg: IRequiredGetter = get.Required
        return object_arg.Field("Identifier", string)

    def _arrow3226(__unit: None=None) -> str | None:
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("Title", string)

    def _arrow3227(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("Description", string)

    def _arrow3228(__unit: None=None) -> str | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("SubmissionDate", string)

    def _arrow3229(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("PublicReleaseDate", string)

    def _arrow3230(__unit: None=None) -> Array[OntologySourceReference] | None:
        arg_11: Decoder_1[Array[OntologySourceReference]] = resize_array(decoder_3)
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("OntologySourceReferences", arg_11)

    def _arrow3231(__unit: None=None) -> Array[Publication] | None:
        arg_13: Decoder_1[Array[Publication]] = resize_array(decoder_4)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("Publications", arg_13)

    def _arrow3232(__unit: None=None) -> Array[Person] | None:
        arg_15: Decoder_1[Array[Person]] = resize_array(decoder_5)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("Contacts", arg_15)

    def _arrow3233(__unit: None=None) -> Array[ArcAssay] | None:
        arg_17: Decoder_1[Array[ArcAssay]] = resize_array(decoder_6)
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("Assays", arg_17)

    def _arrow3234(__unit: None=None) -> Array[ArcStudy] | None:
        arg_19: Decoder_1[Array[ArcStudy]] = resize_array(decoder_7)
        object_arg_9: IOptionalGetter = get.Optional
        return object_arg_9.Field("Studies", arg_19)

    def _arrow3235(__unit: None=None) -> Array[str] | None:
        arg_21: Decoder_1[Array[str]] = resize_array(string)
        object_arg_10: IOptionalGetter = get.Optional
        return object_arg_10.Field("RegisteredStudyIdentifiers", arg_21)

    def _arrow3236(__unit: None=None) -> Array[Comment] | None:
        arg_23: Decoder_1[Array[Comment]] = resize_array(decoder_8)
        object_arg_11: IOptionalGetter = get.Optional
        return object_arg_11.Field("Comments", arg_23)

    return ArcInvestigation(_arrow3225(), _arrow3226(), _arrow3227(), _arrow3228(), _arrow3229(), _arrow3230(), _arrow3231(), _arrow3232(), _arrow3233(), _arrow3234(), None, None, _arrow3235(), _arrow3236())


decoder: Decoder_1[ArcInvestigation] = object(_arrow3237)

def encoder_compressed(string_table: Any, oa_table: Any, cell_table: Any, inv: ArcInvestigation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3242(__unit: None=None, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        value: str = inv.Identifier
        class ObjectExpr3241(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3241()

    def _arrow3244(value_1: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        class ObjectExpr3243(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3243()

    def _arrow3247(value_3: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        class ObjectExpr3246(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_3)

        return ObjectExpr3246()

    def _arrow3249(value_5: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        class ObjectExpr3248(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_5)

        return ObjectExpr3248()

    def _arrow3251(value_7: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        class ObjectExpr3250(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_7)

        return ObjectExpr3250()

    def _arrow3252(osr: OntologySourceReference, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        return encoder_1(osr)

    def _arrow3253(oa: Publication, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        return encoder_2(oa)

    def _arrow3254(person: Person, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        return encoder_3(person)

    def _arrow3255(assay: ArcAssay, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        return encoder_compressed_1(string_table, oa_table, cell_table, assay)

    def _arrow3256(study: ArcStudy, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        return encoder_compressed_2(string_table, oa_table, cell_table, study)

    def _arrow3258(value_9: str, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        class ObjectExpr3257(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_9)

        return ObjectExpr3257()

    def _arrow3259(comment: Comment, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> IEncodable:
        return encoder_6(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("Identifier", _arrow3242()), try_include("Title", _arrow3244, inv.Title), try_include("Description", _arrow3247, inv.Description), try_include("SubmissionDate", _arrow3249, inv.SubmissionDate), try_include("PublicReleaseDate", _arrow3251, inv.PublicReleaseDate), try_include_seq("OntologySourceReferences", _arrow3252, inv.OntologySourceReferences), try_include_seq("Publications", _arrow3253, inv.Publications), try_include_seq("Contacts", _arrow3254, inv.Contacts), try_include_seq("Assays", _arrow3255, inv.Assays), try_include_seq("Studies", _arrow3256, inv.Studies), try_include_seq("RegisteredStudyIdentifiers", _arrow3258, inv.RegisteredStudyIdentifiers), try_include_seq("Comments", _arrow3259, inv.Comments)]))
    class ObjectExpr3260(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table, inv: Any=inv) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_6))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_6.encode_object(arg)

    return ObjectExpr3260()


def decoder_compressed(string_table: Array[str], oa_table: Array[OntologyAnnotation], cell_table: Array[CompositeCell]) -> Decoder_1[ArcInvestigation]:
    def _arrow3274(get: IGetters, string_table: Any=string_table, oa_table: Any=oa_table, cell_table: Any=cell_table) -> ArcInvestigation:
        def _arrow3262(__unit: None=None) -> str:
            object_arg: IRequiredGetter = get.Required
            return object_arg.Field("Identifier", string)

        def _arrow3263(__unit: None=None) -> str | None:
            object_arg_1: IOptionalGetter = get.Optional
            return object_arg_1.Field("Title", string)

        def _arrow3264(__unit: None=None) -> str | None:
            object_arg_2: IOptionalGetter = get.Optional
            return object_arg_2.Field("Description", string)

        def _arrow3265(__unit: None=None) -> str | None:
            object_arg_3: IOptionalGetter = get.Optional
            return object_arg_3.Field("SubmissionDate", string)

        def _arrow3266(__unit: None=None) -> str | None:
            object_arg_4: IOptionalGetter = get.Optional
            return object_arg_4.Field("PublicReleaseDate", string)

        def _arrow3267(__unit: None=None) -> Array[OntologySourceReference] | None:
            arg_11: Decoder_1[Array[OntologySourceReference]] = resize_array(decoder_3)
            object_arg_5: IOptionalGetter = get.Optional
            return object_arg_5.Field("OntologySourceReferences", arg_11)

        def _arrow3268(__unit: None=None) -> Array[Publication] | None:
            arg_13: Decoder_1[Array[Publication]] = resize_array(decoder_4)
            object_arg_6: IOptionalGetter = get.Optional
            return object_arg_6.Field("Publications", arg_13)

        def _arrow3269(__unit: None=None) -> Array[Person] | None:
            arg_15: Decoder_1[Array[Person]] = resize_array(decoder_5)
            object_arg_7: IOptionalGetter = get.Optional
            return object_arg_7.Field("Contacts", arg_15)

        def _arrow3270(__unit: None=None) -> Array[ArcAssay] | None:
            arg_17: Decoder_1[Array[ArcAssay]] = resize_array(decoder_compressed_1(string_table, oa_table, cell_table))
            object_arg_8: IOptionalGetter = get.Optional
            return object_arg_8.Field("Assays", arg_17)

        def _arrow3271(__unit: None=None) -> Array[ArcStudy] | None:
            arg_19: Decoder_1[Array[ArcStudy]] = resize_array(decoder_compressed_2(string_table, oa_table, cell_table))
            object_arg_9: IOptionalGetter = get.Optional
            return object_arg_9.Field("Studies", arg_19)

        def _arrow3272(__unit: None=None) -> Array[str] | None:
            arg_21: Decoder_1[Array[str]] = resize_array(string)
            object_arg_10: IOptionalGetter = get.Optional
            return object_arg_10.Field("RegisteredStudyIdentifiers", arg_21)

        def _arrow3273(__unit: None=None) -> Array[Comment] | None:
            arg_23: Decoder_1[Array[Comment]] = resize_array(decoder_8)
            object_arg_11: IOptionalGetter = get.Optional
            return object_arg_11.Field("Comments", arg_23)

        return ArcInvestigation(_arrow3262(), _arrow3263(), _arrow3264(), _arrow3265(), _arrow3266(), _arrow3267(), _arrow3268(), _arrow3269(), _arrow3270(), _arrow3271(), None, None, _arrow3272(), _arrow3273())

    return object(_arrow3274)


def ROCrate_genID(i: ArcInvestigation) -> str:
    return "./"


def ROCrate_encoder(oa: ArcInvestigation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3278(__unit: None=None, oa: Any=oa) -> IEncodable:
        value: str = ROCrate_genID(oa)
        class ObjectExpr3277(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3277()

    class ObjectExpr3279(IEncodable):
        def Encode(self, helpers_1: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            return helpers_1.encode_string("Investigation")

    class ObjectExpr3280(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            return helpers_2.encode_string("Investigation")

    def _arrow3282(__unit: None=None, oa: Any=oa) -> IEncodable:
        value_3: str = oa.Identifier
        class ObjectExpr3281(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_3)

        return ObjectExpr3281()

    def _arrow3284(__unit: None=None, oa: Any=oa) -> IEncodable:
        value_4: str = ArcInvestigation.FileName()
        class ObjectExpr3283(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_4)

        return ObjectExpr3283()

    def _arrow3286(value_5: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr3285(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_5)

        return ObjectExpr3285()

    def _arrow3288(value_7: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr3287(IEncodable):
            def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
                return helpers_6.encode_string(value_7)

        return ObjectExpr3287()

    def _arrow3290(value_9: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr3289(IEncodable):
            def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
                return helpers_7.encode_string(value_9)

        return ObjectExpr3289()

    def _arrow3293(__unit: None=None, oa: Any=oa) -> IEncodable:
        def _arrow3291(__unit: None=None) -> str:
            copy_of_struct: Any = today()
            return to_string(copy_of_struct, "yyyy-MM-dd")

        value_12: str = default_arg(oa.PublicReleaseDate, _arrow3291())
        class ObjectExpr3292(IEncodable):
            def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
                return helpers_8.encode_string(value_12)

        return ObjectExpr3292()

    def _arrow3294(osr: OntologySourceReference, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_1(osr)

    def _arrow3295(oa_1: Publication, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_2(oa_1)

    def _arrow3296(oa_2: Person, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_3(oa_2)

    def _arrow3297(s: ArcStudy, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_4(None, s)

    def _arrow3298(comment: Comment, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder_5(comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow3278()), ("@type", ObjectExpr3279()), ("additionalType", ObjectExpr3280()), ("identifier", _arrow3282()), ("filename", _arrow3284()), try_include("title", _arrow3286, oa.Title), try_include("description", _arrow3288, oa.Description), try_include("submissionDate", _arrow3290, oa.SubmissionDate), ("publicReleaseDate", _arrow3293()), try_include_seq("ontologySourceReferences", _arrow3294, oa.OntologySourceReferences), try_include_seq("publications", _arrow3295, oa.Publications), try_include_seq("people", _arrow3296, oa.Contacts), try_include_seq("studies", _arrow3297, oa.Studies), try_include_seq("comments", _arrow3298, oa.Comments), ("@context", context_jsonvalue)]))
    class ObjectExpr3299(IEncodable):
        def Encode(self, helpers_9: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_9))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_9.encode_object(arg)

    return ObjectExpr3299()


def _arrow3311(get: IGetters) -> ArcInvestigation:
    identifier: str
    match_value: str | None
    object_arg: IOptionalGetter = get.Optional
    match_value = object_arg.Field("identifier", string)
    identifier = create_missing_identifier() if (match_value is None) else match_value
    def _arrow3300(__unit: None=None) -> FSharpList[tuple[ArcStudy, FSharpList[ArcAssay]]] | None:
        arg_3: Decoder_1[FSharpList[tuple[ArcStudy, FSharpList[ArcAssay]]]] = list_1_1(ROCrate_decoder_1)
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("studies", arg_3)

    pattern_input: tuple[FSharpList[ArcStudy], FSharpList[FSharpList[ArcAssay]]] = unzip(default_arg(_arrow3300(), empty()))
    studies_raw: FSharpList[ArcStudy] = pattern_input[0]
    def projection(a: ArcAssay) -> str:
        return a.Identifier

    class ObjectExpr3302:
        @property
        def Equals(self) -> Callable[[str, str], bool]:
            def _arrow3301(x: str, y: str) -> bool:
                return x == y

            return _arrow3301

        @property
        def GetHashCode(self) -> Callable[[str], int]:
            return string_hash

    assays: Array[ArcAssay] = list(distinct_by(projection, concat(pattern_input[1]), ObjectExpr3302()))
    studies: Array[ArcStudy] = list(studies_raw)
    def mapping(a_1: ArcStudy) -> str:
        return a_1.Identifier

    study_identifiers: Array[str] = list(map_1(mapping, studies_raw))
    def _arrow3303(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("title", string)

    def _arrow3304(__unit: None=None) -> str | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("description", string)

    def _arrow3305(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("submissionDate", string)

    def _arrow3306(__unit: None=None) -> str | None:
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("publicReleaseDate", string)

    def _arrow3307(__unit: None=None) -> Array[OntologySourceReference] | None:
        arg_13: Decoder_1[Array[OntologySourceReference]] = resize_array(ROCrate_decoder_2)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("ontologySourceReferences", arg_13)

    def _arrow3308(__unit: None=None) -> Array[Publication] | None:
        arg_15: Decoder_1[Array[Publication]] = resize_array(ROCrate_decoder_3)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("publications", arg_15)

    def _arrow3309(__unit: None=None) -> Array[Person] | None:
        arg_17: Decoder_1[Array[Person]] = resize_array(ROCrate_decoder_4)
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("people", arg_17)

    def _arrow3310(__unit: None=None) -> Array[Comment] | None:
        arg_19: Decoder_1[Array[Comment]] = resize_array(ROCrate_decoder_5)
        object_arg_9: IOptionalGetter = get.Optional
        return object_arg_9.Field("comments", arg_19)

    return ArcInvestigation(identifier, _arrow3303(), _arrow3304(), _arrow3305(), _arrow3306(), _arrow3307(), _arrow3308(), _arrow3309(), assays, studies, None, None, study_identifiers, _arrow3310())


ROCrate_decoder: Decoder_1[ArcInvestigation] = object(_arrow3311)

def ROCrate_encodeRoCrate(oa: ArcInvestigation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], oa: Any=oa) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3315(value: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr3314(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3314()

    def _arrow3317(value_2: str, oa: Any=oa) -> IEncodable:
        class ObjectExpr3316(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_2)

        return ObjectExpr3316()

    def _arrow3318(oa_1: ArcInvestigation, oa: Any=oa) -> IEncodable:
        return ROCrate_encoder(oa_1)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([try_include("@type", _arrow3315, "CreativeWork"), try_include("@id", _arrow3317, "ro-crate-metadata.json"), try_include("about", _arrow3318, oa), ("conformsTo", conforms_to_jsonvalue), ("@context", context_jsonvalue_1)]))
    class ObjectExpr3319(IEncodable):
        def Encode(self, helpers_2: IEncoderHelpers_1[Any], oa: Any=oa) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_2))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_2.encode_object(arg)

    return ObjectExpr3319()


ISAJson_allowedFields: FSharpList[str] = of_array(["@id", "filename", "identifier", "title", "description", "submissionDate", "publicReleaseDate", "ontologySourceReferences", "publications", "people", "studies", "comments", "@type", "@context"])

def ISAJson_encoder(id_map: Any | None, inv: ArcInvestigation) -> IEncodable:
    def chooser(tupled_arg: tuple[str, IEncodable | None], id_map: Any=id_map, inv: Any=inv) -> tuple[str, IEncodable] | None:
        def mapping(v_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1)

        return map(mapping, tupled_arg[1])

    def _arrow3323(__unit: None=None, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        value: str = ROCrate_genID(inv)
        class ObjectExpr3322(IEncodable):
            def Encode(self, helpers: IEncoderHelpers_1[Any]) -> Any:
                return helpers.encode_string(value)

        return ObjectExpr3322()

    def _arrow3325(__unit: None=None, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        value_1: str = ArcInvestigation.FileName()
        class ObjectExpr3324(IEncodable):
            def Encode(self, helpers_1: IEncoderHelpers_1[Any]) -> Any:
                return helpers_1.encode_string(value_1)

        return ObjectExpr3324()

    def _arrow3327(__unit: None=None, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        value_2: str = inv.Identifier
        class ObjectExpr3326(IEncodable):
            def Encode(self, helpers_2: IEncoderHelpers_1[Any]) -> Any:
                return helpers_2.encode_string(value_2)

        return ObjectExpr3326()

    def _arrow3329(value_3: str, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        class ObjectExpr3328(IEncodable):
            def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                return helpers_3.encode_string(value_3)

        return ObjectExpr3328()

    def _arrow3331(value_5: str, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        class ObjectExpr3330(IEncodable):
            def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                return helpers_4.encode_string(value_5)

        return ObjectExpr3330()

    def _arrow3333(value_7: str, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        class ObjectExpr3332(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_7)

        return ObjectExpr3332()

    def _arrow3335(value_9: str, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        class ObjectExpr3334(IEncodable):
            def Encode(self, helpers_6: IEncoderHelpers_1[Any]) -> Any:
                return helpers_6.encode_string(value_9)

        return ObjectExpr3334()

    def _arrow3336(osr: OntologySourceReference, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        return ISAJson_encoder_1(id_map, osr)

    def _arrow3337(oa: Publication, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        return ISAJson_encoder_2(id_map, oa)

    def _arrow3338(person: Person, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        return ISAJson_encoder_3(id_map, person)

    def _arrow3339(s: ArcStudy, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        return ISAJson_encoder_4(id_map, None, s)

    def _arrow3340(comment: Comment, id_map: Any=id_map, inv: Any=inv) -> IEncodable:
        return ISAJson_encoder_5(id_map, comment)

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow3323()), ("filename", _arrow3325()), ("identifier", _arrow3327()), try_include("title", _arrow3329, inv.Title), try_include("description", _arrow3331, inv.Description), try_include("submissionDate", _arrow3333, inv.SubmissionDate), try_include("publicReleaseDate", _arrow3335, inv.PublicReleaseDate), try_include_seq("ontologySourceReferences", _arrow3336, inv.OntologySourceReferences), try_include_seq("publications", _arrow3337, inv.Publications), try_include_seq("people", _arrow3338, inv.Contacts), try_include_seq("studies", _arrow3339, inv.Studies), try_include_seq("comments", _arrow3340, inv.Comments)]))
    class ObjectExpr3341(IEncodable):
        def Encode(self, helpers_7: IEncoderHelpers_1[Any], id_map: Any=id_map, inv: Any=inv) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_7))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_7.encode_object(arg)

    return ObjectExpr3341()


def _arrow3353(get: IGetters) -> ArcInvestigation:
    identifer: str
    match_value: str | None
    object_arg: IOptionalGetter = get.Optional
    match_value = object_arg.Field("identifier", string)
    identifer = create_missing_identifier() if (match_value is None) else match_value
    def _arrow3342(__unit: None=None) -> FSharpList[tuple[ArcStudy, FSharpList[ArcAssay]]] | None:
        arg_3: Decoder_1[FSharpList[tuple[ArcStudy, FSharpList[ArcAssay]]]] = list_1_1(ISAJson_decoder_1)
        object_arg_1: IOptionalGetter = get.Optional
        return object_arg_1.Field("studies", arg_3)

    pattern_input: tuple[FSharpList[ArcStudy], FSharpList[FSharpList[ArcAssay]]] = unzip(default_arg(_arrow3342(), empty()))
    studies_raw: FSharpList[ArcStudy] = pattern_input[0]
    def projection(a: ArcAssay) -> str:
        return a.Identifier

    class ObjectExpr3344:
        @property
        def Equals(self) -> Callable[[str, str], bool]:
            def _arrow3343(x: str, y: str) -> bool:
                return x == y

            return _arrow3343

        @property
        def GetHashCode(self) -> Callable[[str], int]:
            return string_hash

    assays: Array[ArcAssay] = list(distinct_by(projection, concat(pattern_input[1]), ObjectExpr3344()))
    studies: Array[ArcStudy] = list(studies_raw)
    def mapping(a_1: ArcStudy) -> str:
        return a_1.Identifier

    study_identifiers: Array[str] = list(map_1(mapping, studies_raw))
    def _arrow3345(__unit: None=None) -> str | None:
        object_arg_2: IOptionalGetter = get.Optional
        return object_arg_2.Field("title", string)

    def _arrow3346(__unit: None=None) -> str | None:
        object_arg_3: IOptionalGetter = get.Optional
        return object_arg_3.Field("description", string)

    def _arrow3347(__unit: None=None) -> str | None:
        object_arg_4: IOptionalGetter = get.Optional
        return object_arg_4.Field("submissionDate", string)

    def _arrow3348(__unit: None=None) -> str | None:
        object_arg_5: IOptionalGetter = get.Optional
        return object_arg_5.Field("publicReleaseDate", string)

    def _arrow3349(__unit: None=None) -> Array[OntologySourceReference] | None:
        arg_13: Decoder_1[Array[OntologySourceReference]] = resize_array(ISAJson_decoder_2)
        object_arg_6: IOptionalGetter = get.Optional
        return object_arg_6.Field("ontologySourceReferences", arg_13)

    def _arrow3350(__unit: None=None) -> Array[Publication] | None:
        arg_15: Decoder_1[Array[Publication]] = resize_array(ISAJson_decoder_3)
        object_arg_7: IOptionalGetter = get.Optional
        return object_arg_7.Field("publications", arg_15)

    def _arrow3351(__unit: None=None) -> Array[Person] | None:
        arg_17: Decoder_1[Array[Person]] = resize_array(ISAJson_decoder_4)
        object_arg_8: IOptionalGetter = get.Optional
        return object_arg_8.Field("people", arg_17)

    def _arrow3352(__unit: None=None) -> Array[Comment] | None:
        arg_19: Decoder_1[Array[Comment]] = resize_array(ISAJson_decoder_5)
        object_arg_9: IOptionalGetter = get.Optional
        return object_arg_9.Field("comments", arg_19)

    return ArcInvestigation(identifer, _arrow3345(), _arrow3346(), _arrow3347(), _arrow3348(), _arrow3349(), _arrow3350(), _arrow3351(), assays, studies, None, None, study_identifiers, _arrow3352())


ISAJson_decoder: Decoder_1[ArcInvestigation] = Decode_objectNoAdditionalProperties(ISAJson_allowedFields, _arrow3353)

__all__ = ["encoder", "decoder", "encoder_compressed", "decoder_compressed", "ROCrate_genID", "ROCrate_encoder", "ROCrate_decoder", "ROCrate_encodeRoCrate", "ISAJson_allowedFields", "ISAJson_encoder", "ISAJson_decoder"]

