from typing import Union

from py_dpm.DataTypes.ScalarTypes import ScalarFactory, TimeInterval
from py_dpm.DataTypes.TypePromotion import unary_implicit_type_promotion
from py_dpm.Exceptions import exceptions
from py_dpm.Operators.Operator import Operator
from py_dpm.Utils import tokens
from py_dpm.semantics.Symbols import ConstantOperand, RecordSet, Scalar


class TimeShift(Operator):
    op = tokens.TIME_SHIFT
    type_to_check = TimeInterval
    propagate_attributes = True

    @classmethod
    def validate(cls, operand: Union[RecordSet, Scalar, ConstantOperand], component_name: str, period: str,
                 shift_number: int):

        type_to_check = ScalarFactory().scalar_factory(cls.type_to_check.__name__)
        error_info = {
            'operand_name': operand.name,
            'op': cls.op
        }

        if isinstance(operand, RecordSet):
            if not component_name:
                raise exceptions.SemanticError("4-7-3")

            if not component_name == tokens.FACT:
                components = {**operand.get_dpm_components(), **operand.get_attributes()}
                if not components or component_name not in components:
                    raise exceptions.SemanticError("2-8", op=cls.op, dpm_keys=component_name,
                                                   recordset=operand.name)

            component = operand.structure.components[component_name]

            result_type = unary_implicit_type_promotion(
                operand=component.type, op_type_to_check=type_to_check, error_info=error_info)

            origin = f"{cls.op} ( {operand.name}, {period}, {shift_number}, {component_name} )"
            return cls._create_labeled_recordset(origin, operand.get_fact_component().type, operand.structure, operand.records)

        if component_name:
            raise exceptions.SemanticError("4-7-2")

        final_type = unary_implicit_type_promotion(
            operand=operand.type, op_type_to_check=type_to_check, error_info=error_info)
        if isinstance(operand, ConstantOperand):
            return operand

        origin = f"{cls.op}({operand.name}, {period}, {shift_number})"
        return cls._create_labeled_scalar(origin, result_type=final_type)
