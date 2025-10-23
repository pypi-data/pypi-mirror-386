from __future__ import annotations
from collections.abc import Callable
from typing import (Any, TypeVar)
from ..fable_modules.fable_library.list import (choose, of_array, FSharpList)
from ..fable_modules.fable_library.option import map
from ..fable_modules.fable_library.seq import map as map_1
from ..fable_modules.fable_library.util import IEnumerable_1
from ..fable_modules.thoth_json_core.decode import (object, IOptionalGetter, string, IGetters)
from ..fable_modules.thoth_json_core.types import (IEncodable, IEncoderHelpers_1, Decoder_1)
from ..Core.iproperty_value import IPropertyValue
from ..Core.ontology_annotation import OntologyAnnotation
from ..Core.value import Value as Value_4
from .context.rocrate.property_value_context import context_jsonvalue
from .encode import try_include
from .ontology_annotation import AnnotationValue_decoder

__A_ = TypeVar("__A_")

_T = TypeVar("_T")

def gen_id(p: IPropertyValue) -> str:
    match_value: OntologyAnnotation | None = p.GetCategory()
    match_value_1: Value_4 | None = p.GetValue()
    match_value_2: OntologyAnnotation | None = p.GetUnit()
    (pattern_matching_result, t, u, v, t_1, v_1) = (None, None, None, None, None, None)
    if match_value is not None:
        if match_value_1 is not None:
            if match_value_2 is None:
                pattern_matching_result = 1
                t_1 = match_value
                v_1 = match_value_1

            else: 
                pattern_matching_result = 0
                t = match_value
                u = match_value_2
                v = match_value_1


        else: 
            pattern_matching_result = 2


    else: 
        pattern_matching_result = 2

    if pattern_matching_result == 0:
        return ((((((("#" + p.GetAdditionalType()) + "/") + t.NameText) + "=") + v.Text) + "") + u.NameText) + ""

    elif pattern_matching_result == 1:
        return ((((("#" + p.GetAdditionalType()) + "/") + t_1.NameText) + "=") + v_1.Text) + ""

    elif pattern_matching_result == 2:
        return ("#Empty" + p.GetAdditionalType()) + ""



def encoder(pv: IPropertyValue) -> IEncodable:
    pattern_input: tuple[str | None, str | None]
    match_value: OntologyAnnotation | None = pv.GetCategory()
    if match_value is None:
        pattern_input = (None, None)

    else: 
        oa: OntologyAnnotation = match_value
        pattern_input = (oa.Name, oa.TermAccessionNumber)

    pattern_input_1: tuple[IEncodable | None, IEncodable | None]
    match_value_1: Value_4 | None = pv.GetValue()
    if match_value_1 is None:
        pattern_input_1 = (None, None)

    else: 
        v: Value_4 = match_value_1
        if v.tag == 1:
            class ObjectExpr2131(IEncodable):
                def Encode(self, helpers_1: IEncoderHelpers_1[Any], pv: Any=pv) -> Any:
                    return helpers_1.encode_signed_integral_number(v.fields[0])

            pattern_input_1 = (ObjectExpr2131(), None)

        elif v.tag == 2:
            class ObjectExpr2132(IEncodable):
                def Encode(self, helpers_2: IEncoderHelpers_1[Any], pv: Any=pv) -> Any:
                    return helpers_2.encode_decimal_number(v.fields[0])

            pattern_input_1 = (ObjectExpr2132(), None)

        elif v.tag == 0:
            oa_1: OntologyAnnotation = v.fields[0]
            def _arrow2134(value_3: str, pv: Any=pv) -> IEncodable:
                class ObjectExpr2133(IEncodable):
                    def Encode(self, helpers_3: IEncoderHelpers_1[Any]) -> Any:
                        return helpers_3.encode_string(value_3)

                return ObjectExpr2133()

            def _arrow2136(value_5: str, pv: Any=pv) -> IEncodable:
                class ObjectExpr2135(IEncodable):
                    def Encode(self, helpers_4: IEncoderHelpers_1[Any]) -> Any:
                        return helpers_4.encode_string(value_5)

                return ObjectExpr2135()

            pattern_input_1 = (map(_arrow2134, oa_1.Name), map(_arrow2136, oa_1.TermAccessionNumber))

        else: 
            class ObjectExpr2137(IEncodable):
                def Encode(self, helpers: IEncoderHelpers_1[Any], pv: Any=pv) -> Any:
                    return helpers.encode_string(v.fields[0])

            pattern_input_1 = (ObjectExpr2137(), None)


    pattern_input_2: tuple[str | None, str | None]
    match_value_2: OntologyAnnotation | None = pv.GetUnit()
    if match_value_2 is None:
        pattern_input_2 = (None, None)

    else: 
        oa_2: OntologyAnnotation = match_value_2
        pattern_input_2 = (oa_2.Name, oa_2.TermAccessionNumber)

    def chooser(tupled_arg: tuple[str, IEncodable | None], pv: Any=pv) -> tuple[str, IEncodable] | None:
        def mapping(v_1_1: IEncodable, tupled_arg: Any=tupled_arg) -> tuple[str, IEncodable]:
            return (tupled_arg[0], v_1_1)

        return map(mapping, tupled_arg[1])

    def _arrow2141(__unit: None=None, pv: Any=pv) -> IEncodable:
        value_8: str = gen_id(pv)
        class ObjectExpr2140(IEncodable):
            def Encode(self, helpers_5: IEncoderHelpers_1[Any]) -> Any:
                return helpers_5.encode_string(value_8)

        return ObjectExpr2140()

    class ObjectExpr2142(IEncodable):
        def Encode(self, helpers_6: IEncoderHelpers_1[Any], pv: Any=pv) -> Any:
            return helpers_6.encode_string("PropertyValue")

    def _arrow2144(__unit: None=None, pv: Any=pv) -> IEncodable:
        value_10: str = pv.GetAdditionalType()
        class ObjectExpr2143(IEncodable):
            def Encode(self, helpers_7: IEncoderHelpers_1[Any]) -> Any:
                return helpers_7.encode_string(value_10)

        return ObjectExpr2143()

    def _arrow2146(value_11: str, pv: Any=pv) -> IEncodable:
        class ObjectExpr2145(IEncodable):
            def Encode(self, helpers_8: IEncoderHelpers_1[Any]) -> Any:
                return helpers_8.encode_string(value_11)

        return ObjectExpr2145()

    def _arrow2148(value_13: str, pv: Any=pv) -> IEncodable:
        class ObjectExpr2147(IEncodable):
            def Encode(self, helpers_9: IEncoderHelpers_1[Any]) -> Any:
                return helpers_9.encode_string(value_13)

        return ObjectExpr2147()

    def _arrow2150(value_15: str, pv: Any=pv) -> IEncodable:
        class ObjectExpr2149(IEncodable):
            def Encode(self, helpers_10: IEncoderHelpers_1[Any]) -> Any:
                return helpers_10.encode_string(value_15)

        return ObjectExpr2149()

    def _arrow2152(value_17: str, pv: Any=pv) -> IEncodable:
        class ObjectExpr2151(IEncodable):
            def Encode(self, helpers_11: IEncoderHelpers_1[Any]) -> Any:
                return helpers_11.encode_string(value_17)

        return ObjectExpr2151()

    def _arrow2154(value_19: str, pv: Any=pv) -> IEncodable:
        class ObjectExpr2153(IEncodable):
            def Encode(self, helpers_12: IEncoderHelpers_1[Any]) -> Any:
                return helpers_12.encode_string(value_19)

        return ObjectExpr2153()

    def _arrow2155(x: IEncodable, pv: Any=pv) -> IEncodable:
        return x

    def _arrow2156(x_1: IEncodable, pv: Any=pv) -> IEncodable:
        return x_1

    def _arrow2158(value_21: str, pv: Any=pv) -> IEncodable:
        class ObjectExpr2157(IEncodable):
            def Encode(self, helpers_13: IEncoderHelpers_1[Any]) -> Any:
                return helpers_13.encode_string(value_21)

        return ObjectExpr2157()

    def _arrow2160(value_23: str, pv: Any=pv) -> IEncodable:
        class ObjectExpr2159(IEncodable):
            def Encode(self, helpers_14: IEncoderHelpers_1[Any]) -> Any:
                return helpers_14.encode_string(value_23)

        return ObjectExpr2159()

    values: FSharpList[tuple[str, IEncodable]] = choose(chooser, of_array([("@id", _arrow2141()), ("@type", ObjectExpr2142()), ("additionalType", _arrow2144()), try_include("alternateName", _arrow2146, pv.AlternateName()), try_include("measurementMethod", _arrow2148, pv.MeasurementMethod()), try_include("description", _arrow2150, pv.Description()), try_include("category", _arrow2152, pattern_input[0]), try_include("categoryCode", _arrow2154, pattern_input[1]), try_include("value", _arrow2155, pattern_input_1[0]), try_include("valueCode", _arrow2156, pattern_input_1[1]), try_include("unit", _arrow2158, pattern_input_2[0]), try_include("unitCode", _arrow2160, pattern_input_2[1]), ("@context", context_jsonvalue)]))
    class ObjectExpr2161(IEncodable):
        def Encode(self, helpers_15: IEncoderHelpers_1[Any], pv: Any=pv) -> Any:
            def mapping_1(tupled_arg_1: tuple[str, IEncodable]) -> tuple[str, __A_]:
                return (tupled_arg_1[0], tupled_arg_1[1].Encode(helpers_15))

            arg: IEnumerable_1[tuple[str, __A_]] = map_1(mapping_1, values)
            return helpers_15.encode_object(arg)

    return ObjectExpr2161()


def decoder(create: Callable[[str | None, str | None, str | None, OntologyAnnotation | None, Value_4 | None, OntologyAnnotation | None], _T]) -> Decoder_1[Any]:
    def _arrow2163(get: IGetters, create: Any=create) -> _T:
        alternate_name: str | None
        object_arg: IOptionalGetter = get.Optional
        alternate_name = object_arg.Field("alternateName", string)
        measurement_method: str | None
        object_arg_1: IOptionalGetter = get.Optional
        measurement_method = object_arg_1.Field("measurementMethod", string)
        description: str | None
        object_arg_2: IOptionalGetter = get.Optional
        description = object_arg_2.Field("description", string)
        category: OntologyAnnotation | None
        name: str | None
        object_arg_3: IOptionalGetter = get.Optional
        name = object_arg_3.Field("category", string)
        code: str | None
        object_arg_4: IOptionalGetter = get.Optional
        code = object_arg_4.Field("categoryCode", string)
        (pattern_matching_result, code_1) = (None, None)
        if name is None:
            if code is not None:
                if code == "":
                    pattern_matching_result = 0

                else: 
                    pattern_matching_result = 2
                    code_1 = code


            else: 
                pattern_matching_result = 0


        elif code is not None:
            if code == "":
                pattern_matching_result = 1

            else: 
                pattern_matching_result = 2
                code_1 = code


        else: 
            pattern_matching_result = 1

        if pattern_matching_result == 0:
            category = None

        elif pattern_matching_result == 1:
            try: 
                category = OntologyAnnotation.create(name)

            except Exception as err:
                raise Exception(((("Error while decoding category (name:" + str(name)) + "): ") + str(err)) + "")


        elif pattern_matching_result == 2:
            try: 
                category = OntologyAnnotation.from_term_annotation(code_1, name)

            except Exception as err_1:
                raise Exception(((((("Error while decoding category (name:" + str(name)) + ", code:") + code_1) + "): ") + str(err_1)) + "")


        unit: OntologyAnnotation | None
        name_1: str | None
        object_arg_5: IOptionalGetter = get.Optional
        name_1 = object_arg_5.Field("unit", string)
        code_2: str | None
        object_arg_6: IOptionalGetter = get.Optional
        code_2 = object_arg_6.Field("unitCode", string)
        (pattern_matching_result_1, code_3) = (None, None)
        if name_1 is None:
            if code_2 is not None:
                if code_2 == "":
                    pattern_matching_result_1 = 0

                else: 
                    pattern_matching_result_1 = 2
                    code_3 = code_2


            else: 
                pattern_matching_result_1 = 0


        elif code_2 is not None:
            if code_2 == "":
                pattern_matching_result_1 = 1

            else: 
                pattern_matching_result_1 = 2
                code_3 = code_2


        else: 
            pattern_matching_result_1 = 1

        if pattern_matching_result_1 == 0:
            unit = None

        elif pattern_matching_result_1 == 1:
            try: 
                unit = OntologyAnnotation.create(name_1)

            except Exception as err_2:
                raise Exception(((("Error while decoding unit (name:" + str(name_1)) + "): ") + str(err_2)) + "")


        elif pattern_matching_result_1 == 2:
            try: 
                unit = OntologyAnnotation.from_term_annotation(code_3, name_1)

            except Exception as err_3:
                raise Exception(((((("Error while decoding unit (name:" + str(name_1)) + ", code:") + code_3) + "): ") + str(err_3)) + "")


        def _arrow2162(__unit: None=None) -> Value_4 | None:
            value: str | None
            object_arg_7: IOptionalGetter = get.Optional
            value = object_arg_7.Field("value", AnnotationValue_decoder)
            code_4: str | None
            object_arg_8: IOptionalGetter = get.Optional
            code_4 = object_arg_8.Field("valueCode", string)
            if (code_4 is None) if (value is None) else False:
                return None

            else: 
                try: 
                    return Value_4.from_options(value, None, code_4)

                except Exception as err_4:
                    raise Exception(((((("Error while decoding value " + str(value)) + ",") + str(code_4)) + ": ") + str(err_4)) + "")



        return create(alternate_name, measurement_method, description, category, _arrow2162(), unit)

    return object(_arrow2163)


__all__ = ["gen_id", "encoder", "decoder"]

