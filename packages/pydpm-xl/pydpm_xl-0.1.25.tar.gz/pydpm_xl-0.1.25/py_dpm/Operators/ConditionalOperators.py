import warnings
from typing import Union

import pandas as pd

from py_dpm.DataTypes.ScalarTypes import Mixed, ScalarFactory
from py_dpm.DataTypes.TypePromotion import binary_implicit_type_promotion, binary_implicit_type_promotion_with_mixed_types, \
    unary_implicit_type_promotion
from py_dpm.Exceptions import exceptions
from py_dpm.Exceptions.exceptions import SemanticError
from py_dpm.Operators.Operator import Binary, Operator
from py_dpm.Utils import tokens
from py_dpm.semantics.Symbols import ConstantOperand, RecordSet, Scalar, Structure


class ConditionalOperator(Operator):
    propagate_attributes = False

    @classmethod
    def validate(cls, *args):
        pass

    @classmethod
    def create_labeled_scalar(cls, rslt_structure, rslt_type, origin):
        """
        """
        if not isinstance(rslt_structure, ConstantOperand):
            scalar = cls._create_labeled_scalar(origin=origin, result_type=rslt_type)
            return scalar
        else:
            value = rslt_structure.value
            return ConstantOperand(type_=ScalarFactory().scalar_factory(str(rslt_type)), name=None,
                                   origin=origin, value=value)

    @classmethod
    def _check_same_recordset_structures(cls, left: RecordSet, right: RecordSet, origin) -> bool:
        """
        Used for recordset-recordset
        """
        left = left.structure
        right = right.structure
        if len(left.get_key_components()) == len(right.get_key_components()):
            # For better error management
            class_check = Binary()
            class_check.op = cls.op
            class_check.check_same_components(left, right, origin)
            return True
        return False

    @classmethod
    def _check_structures(cls, left: RecordSet, right: RecordSet, origin: str, subset_allowed: bool = True) -> bool:
        """
        Used for recordset-recordset
        """
        left_records = left.records
        right_records = right.records
        if cls._check_same_recordset_structures(left, right, origin):
            # validation for records
            if left_records is not None and right_records is not None:
                result_dataframe = pd.merge(left_records, right_records, on=[col for col in left_records.columns if col != 'data_type'])
                if len(result_dataframe) != len(left_records):
                    raise SemanticError("4-6-0-1")

            return True

        if subset_allowed:
            # operand_is_subset = cls.check_condition_is_subset(selection=left, condition=right)
            operand_is_subset = cls.check_condition_is_subset(selection=right, condition=left)
            if cls.op in (tokens.NVL, tokens.IF):
                operand_is_subset = cls.check_condition_is_subset(selection=right, condition=left)
            else:
                operand_is_subset = cls.check_condition_is_subset(selection=left, condition=right)
            if operand_is_subset:
                return True
            raise exceptions.SemanticError("4-6-0-2", condition=left.name, operand=right.name)

        raise SemanticError(
            "5", op=cls.op, structure_1=left.get_key_components_names(),
            structure_2=right.get_key_components_names()
        )

    @classmethod
    def check_condition_is_subset(cls, selection: RecordSet, condition: RecordSet):

        selection_dpm_components = selection.get_dpm_components()
        condition_dpm_components = condition.get_dpm_components()

        if set(condition.get_key_components_names()) <= set(selection.get_key_components_names()):
            for comp_key, comp_value in condition_dpm_components.items():
                if comp_key not in selection_dpm_components:
                    return False
                if comp_value.type.__class__ != selection_dpm_components[comp_key].type.__class__:
                    return False
            return True
        return False

    @staticmethod
    def generate_result_dataframe(left: RecordSet, right: RecordSet):
        if left.records is not None and right.records is not None:
            result_dataframe = pd.merge(left.records, right.records,
                                        on=[col for col in right.records.columns if col != 'data_type'],
                                        suffixes=('_left', '_right'))

            result_dataframe['data_type'] = result_dataframe['data_type_left']
            result_dataframe = result_dataframe.drop(columns=['data_type_left', 'data_type_right'])

            return result_dataframe

        return None


class IfOperator(ConditionalOperator):
    """
    """
    op = tokens.IF

    @classmethod
    def create_origin_expression(cls, condition, then_op, else_op=None) -> str:
        condition_name = getattr(condition, 'name', None) or getattr(condition, 'origin')
        then_name = getattr(then_op, 'name', None) or getattr(then_op, 'origin')
        if else_op:
            else_name = getattr(else_op, 'name', None) or getattr(else_op, 'origin')
            origin = f"If {condition_name} then {then_name} else {else_name}"
        else:
            origin = f"If {condition_name} then {then_name}"
        return origin

    @classmethod
    def check_condition(cls, condition: Union[RecordSet, Scalar]) -> bool:
        """
        Check if the condition has Boolean type
        """
        if isinstance(condition, RecordSet):
            condition_type = condition.structure.components["f"].type
        else:
            condition_type = condition.type
        # unary implicit promotion
        error_info = {
            'operand_name': condition.name,
            'op': cls.op
        }
        boolean_type = ScalarFactory().scalar_factory("Boolean")
        type_promotion = unary_implicit_type_promotion(
            operand=condition_type, op_type_to_check=boolean_type, error_info=error_info
        )
        if type_promotion.strictly_same_class(boolean_type):
            return True

        raise SemanticError("4-6-1-1")

    @classmethod
    def check_structures(
            cls, condition: Union[RecordSet, Scalar],
            first: Union[RecordSet, Scalar], second: Union[RecordSet, Scalar], origin):
        """
        """
        if isinstance(condition, Scalar):
            if second:
                if isinstance(first, RecordSet) and isinstance(second, RecordSet):
                    if cls._check_structures(first, second, origin, subset_allowed=False):
                        return first.structure, first.records
                elif isinstance(first, Scalar) and isinstance(second, Scalar):
                    return first, None
                else:
                    raise SemanticError("4-6-1-3")
            else:
                if isinstance(first, RecordSet):
                    raise SemanticError("4-6-1-2")
                return first, None
        else:  # RecordSet
            if second:
                if isinstance(first, RecordSet) and isinstance(second, RecordSet):
                    cls._check_structures(condition, first, origin)
                    cls._check_structures(condition, second, origin)
                if isinstance(first, RecordSet) and isinstance(second, Scalar):
                    cls._check_structures(condition, first, origin)
                if isinstance(first, Scalar) and isinstance(second, RecordSet):
                    cls._check_structures(condition, second, origin)
                return condition.structure, condition.records
            else:
                if isinstance(first, RecordSet):
                    cls._check_structures(condition, first, origin)
                return condition.structure, condition.records


    @classmethod
    def check_types(cls, first: Union[RecordSet, Scalar], result_dataframe: pd.DataFrame, second: Union[RecordSet, Scalar] = None):
        if second:
            if isinstance(first, RecordSet):
                first_type = first.structure.components["f"].type
            else:
                first_type = first.type
            if isinstance(second, RecordSet):
                second_type = second.structure.components["f"].type
            else:
                second_type = second.type
            if isinstance(first_type, Mixed) or isinstance(second_type, Mixed):
                result_dataframe = cls.generate_result_dataframe(first, second)
        else:
            if isinstance(first, RecordSet):
                first_type = first.structure.components["f"].type
            else:
                first_type = first.type
            return first_type, result_dataframe

        if isinstance(first_type, Mixed) or isinstance(second_type, Mixed):
            type_promotion, result_dataframe = binary_implicit_type_promotion_with_mixed_types(result_dataframe, first_type, second_type)
        else:
            type_promotion = binary_implicit_type_promotion(first_type, second_type)

        return type_promotion, result_dataframe

    @classmethod
    def validate(
            cls, condition: Union[RecordSet, Scalar],
            then_op: Union[RecordSet, Scalar], else_op: Union[RecordSet, Scalar] = None) -> Union[RecordSet, Scalar]:
        """
        """
        origin = cls.create_origin_expression(condition, then_op, else_op)
        # check condition
        cls.check_condition(condition)
        # check structures
        rslt_structure, rslt_dataframe = cls.check_structures(condition, then_op, else_op, origin)
        # check_types (with implicit cast)
        rslt_type, rslt_dataframe = cls.check_types(then_op, rslt_dataframe, else_op)
        # Create the result structure with label
        if isinstance(rslt_structure, Structure):
            recordset = cls._create_labeled_recordset(origin=origin, rslt_type=rslt_type, rslt_structure=rslt_structure,
                                                      result_dataframe=rslt_dataframe)
            return recordset
        labeled_scalar = cls.create_labeled_scalar(rslt_structure, rslt_type, origin)
        return labeled_scalar


class Nvl(ConditionalOperator):
    """
    """
    op = tokens.NVL

    @classmethod
    def create_origin_expression(cls, left, right) -> str:
        left_name = getattr(left, 'name', None) or getattr(left, 'origin')
        right_name = getattr(right, 'name', None) or getattr(right, 'origin')

        origin = f"{cls.op}({left_name},{right_name})"
        return origin

    @classmethod
    def check_structures(cls, left: Union[RecordSet, Scalar], right: Union[RecordSet, Scalar], origin: str):
        if isinstance(left, RecordSet) and isinstance(right, RecordSet):
            if cls._check_structures(left, right, origin):
                result_dataframe = cls.generate_result_dataframe(left, right)
                return left.structure, result_dataframe
        elif isinstance(left, RecordSet) and isinstance(right, Scalar):
            return left.structure, left.records
        elif isinstance(left, Scalar) and isinstance(right, RecordSet):
            raise SemanticError("4-6-2-1")
        elif isinstance(left, Scalar) and isinstance(right, Scalar):
            return left, None

    @classmethod
    def check_types(cls, first: Union[RecordSet, Scalar], result_dataframe, second: Union[RecordSet, Scalar] = None):
        """
        """
        if isinstance(first, RecordSet):
            first_type = first.structure.components["f"].type
        else:
            first_type = first.type

        if isinstance(second, RecordSet):
            second_type = second.structure.components["f"].type
        else:
            second_type = second.type

        if isinstance(first_type, Mixed) or isinstance(second_type, Mixed):
            type_promotion, result_dataframe = binary_implicit_type_promotion_with_mixed_types(result_dataframe, first_type, second_type)
        else:
            type_promotion = binary_implicit_type_promotion(first_type, second_type)
            if result_dataframe is not None:
                if 'data_type_left' in result_dataframe.columns:
                    result_dataframe = result_dataframe.drop(columns=['data_type_left', 'data_type_right'])
                result_dataframe = result_dataframe.assign(data_type=type_promotion)

        return type_promotion, result_dataframe

    @classmethod
    def validate(cls, left: Union[RecordSet, Scalar], right: Union[RecordSet, Scalar]) -> Union[RecordSet, Scalar]:
        """
        """
        origin: str = cls.create_origin_expression(left, right)
        # check structures
        rslt_structure, rslt_dataframe = cls.check_structures(left, right, origin)
        # check_types
        rslt_type, rslt_dataframe = cls.check_types(first=left, result_dataframe=rslt_dataframe, second=right)
        # Create the result structure with label
        if isinstance(rslt_structure, Structure):
            recordset = cls._create_labeled_recordset(origin=origin, rslt_type=rslt_type, rslt_structure=rslt_structure,
                                                      result_dataframe=rslt_dataframe)
            return recordset
        labeled_scalar = cls.create_labeled_scalar(rslt_structure=rslt_structure, rslt_type=rslt_type, origin=origin)
        return labeled_scalar


class Filter(ConditionalOperator):
    op = tokens.FILTER
    propagate_attributes = False

    @classmethod
    def create_origin_expression(cls, selection, condition) -> str:
        selection_name = getattr(selection, 'name', None) or getattr(selection, 'origin', None)
        condition_name = getattr(condition, 'name', None) or getattr(condition, 'origin', None)

        origin = f"{cls.op} ( {selection_name}, {condition_name} )"
        return origin

    @classmethod
    def _check_filter_structures(cls, selection: RecordSet, condition: RecordSet) -> Structure:
        origin: str = cls.create_origin_expression(selection, condition)
        if cls._check_same_recordset_structures(selection, condition, origin):
            return selection.structure

        else:
            condition_is_subset = cls.check_condition_is_subset(selection=selection, condition=condition)
            if condition_is_subset:
                return selection.structure
            raise exceptions.SemanticError("4-6-0-2", operand=selection.name, condition=condition.name)

    @classmethod
    def validate(cls, selection, condition):

        if isinstance(selection, RecordSet) and isinstance(condition, RecordSet):

            if selection.has_only_global_components:
                warnings.warn(
                    f"Performing a filter operation on recordset: {selection.name} which has only global key components")

            check_condition_type = ScalarFactory().scalar_factory("Boolean")
            condition_fact_component = condition.get_fact_component()
            error_info = {
                'operand_name': condition.name,
                'op': cls.op
            }
            unary_implicit_type_promotion(condition_fact_component.type, check_condition_type, error_info=error_info)
            result_structure = cls._check_filter_structures(selection, condition)

            result_dataframe = None
            if selection.records is not None and condition.records is not None:
                result_dataframe = cls.generate_result_dataframe(selection, condition)

            return cls.create_labeled_recordset(selection=selection, condition=condition,
                                                result_structure=result_structure, result_dataframe=result_dataframe)

        raise exceptions.SemanticError("4-6-3-1")

    @classmethod
    def create_labeled_recordset(cls, selection, condition, result_structure, result_dataframe):
        origin: str = cls.create_origin_expression(selection, condition)
        recordset = cls._create_labeled_recordset(
            origin=origin, rslt_type=result_structure.components["f"].type,
            rslt_structure=result_structure, result_dataframe=result_dataframe
        )
        return recordset
