#!/usr/bin/env python3
"""
AST to JSON serialization utilities for pyDPM
"""

from py_dpm.AST.ASTVisitor import NodeVisitor

class ASTToJSONVisitor(NodeVisitor):
    """Visitor that converts AST nodes to JSON using the existing visitor pattern infrastructure."""

    def __init__(self, with_context=None):
        self.with_context = with_context

    def visit(self, node):
        """Override the base visit to handle None values."""
        if node is None:
            return None
        return super().visit(node)

    def visit_BinOp(self, node):
        """Visit BinOp nodes."""
        # Handle match operations as MatchCharactersOp
        if node.op == 'match':
            return {
                'class_name': 'MatchCharactersOp',
                'operand': self.visit(node.left),
                'pattern': self.visit(node.right)
            }

        return {
            'class_name': 'BinOp',
            'op': node.op,
            'left': self.visit(node.left),
            'right': self.visit(node.right)
        }

    def visit_UnaryOp(self, node):
        """Visit UnaryOp nodes."""
        return {
            'class_name': 'UnaryOp',
            'op': node.op,
            'operand': self.visit(node.operand)
        }

    def visit_VarID(self, node):
        """Visit VarID nodes with context handling."""
        result = {
            'class_name': 'VarID'
        }

        # Helper function to check if a value represents multiple items, ranges, or wildcards
        def is_multi_range_or_wildcard(values):
            if not isinstance(values, list):
                return False
            if len(values) != 1:
                return len(values) > 1  # Multiple values
            # Check if single value contains range syntax or wildcards
            single_val = values[0]
            if isinstance(single_val, str):
                return '-' in single_val or single_val == '*'
            return False

        # Apply context first, then override with node-specific values
        if self.with_context:
            # Handle simple context fields
            for context_attr in ['table', 'interval', 'default']:
                if hasattr(self.with_context, context_attr):
                    context_value = getattr(self.with_context, context_attr)
                    # Special handling for interval field
                    if context_attr == 'interval':
                        if context_value is not None:
                            # Context has explicit interval value, use it
                            result[context_attr] = context_value
                        else:
                            # Context interval is None, will be handled by node processing
                            pass
                    elif context_value is not None:
                        # Handle AST objects in context (like Constant)
                        if hasattr(context_value, 'toJSON'):
                            if context_value.__class__.__name__ == 'Constant':
                                context_json = context_value.toJSON()
                                result[context_attr] = context_json.get('value', context_value)
                            else:
                                result[context_attr] = self.visit(context_value)
                        else:
                            result[context_attr] = context_value

            # Handle array context fields (rows, cols, sheets) - only convert to scalar if single value and not range
            array_mappings = {'rows': 'row', 'cols': 'column', 'sheets': 'sheet'}
            for context_attr, result_key in array_mappings.items():
                if hasattr(self.with_context, context_attr):
                    context_value = getattr(self.with_context, context_attr)
                    if context_value is not None:
                        # Only create scalar field if it's a single non-range, non-wildcard value
                        if isinstance(context_value, list) and len(context_value) == 1 and not is_multi_range_or_wildcard(context_value):
                            result[result_key] = context_value[0]
                        # For multi-value, range, or wildcard contexts, don't create scalar fields
                        # The expected JSON has data field instead (handled by database layer)

        # Override with node-specific values using same logic
        node_array_mappings = {'rows': 'row', 'cols': 'column', 'sheets': 'sheet'}

        # Handle simple node fields
        for node_attr in ['table', 'interval', 'default']:
            if hasattr(node, node_attr):
                node_value = getattr(node, node_attr)
                # Special handling for interval field
                if node_attr == 'interval':
                    if node_value is not None:
                        # Node has explicit interval value, use it
                        result[node_attr] = node_value
                    elif node_attr not in result:
                        # No context value and node value is None
                        # Check data type to determine if interval should be False or None
                        # Extract data_type from node.data if available
                        data_type = None
                        if hasattr(node, 'data') and node.data is not None:
                            if hasattr(node.data, 'to_dict'):
                                # DataFrame - get first entry's data_type
                                data_records = node.data.to_dict('records')
                                if data_records:
                                    data_type = data_records[0].get('data_type')
                            elif isinstance(node.data, list) and node.data:
                                # List - get first entry's data_type
                                data_type = node.data[0].get('data_type') if isinstance(node.data[0], dict) else None

                        # Set interval to False for all data types
                        result[node_attr] = False
                    # If context already set this field, don't override
                elif node_value is not None:
                    # Handle AST objects (like Constant)
                    if hasattr(node_value, 'toJSON'):
                        if node_value.__class__.__name__ == 'Constant':
                            node_json = node_value.toJSON()
                            result[node_attr] = node_json.get('value', node_value)
                        else:
                            result[node_attr] = self.visit(node_value)
                    else:
                        result[node_attr] = node_value

        # Handle array node fields
        for node_attr, result_key in node_array_mappings.items():
            if hasattr(node, node_attr):
                node_value = getattr(node, node_attr)
                if node_value is not None:
                    # Only create scalar field if it's a single non-range, non-wildcard value
                    if isinstance(node_value, list) and len(node_value) == 1 and not is_multi_range_or_wildcard(node_value):
                        result[result_key] = node_value[0]

        # Handle data field if present (contains datapoint and operand_reference_id)
        if hasattr(node, 'data') and node.data is not None:
            # Convert pandas DataFrame to list of dictionaries
            if hasattr(node.data, 'to_dict'):
                data_records = node.data.to_dict('records')

                # Determine if this is a multi-column or multi-row expression from context
                context_cols = []
                if self.with_context and hasattr(self.with_context, 'cols') and self.with_context.cols:
                    context_cols = self.with_context.cols

                # Parse cell_code to extract row/column/sheet if needed
                # Some databases store these in separate fields, others embed them in cell_code
                import re
                for record in data_records:
                    if not record.get('row_code') or str(record.get('row_code')) == 'None':
                        # Try to extract from cell_code like "{K_04.00.a, r0010, c0020, s0001}"
                        cell_code = record.get('cell_code', '')
                        if cell_code:
                            row_match = re.search(r'r(\d+)', cell_code)
                            col_match = re.search(r'c(\d+)', cell_code)
                            sheet_match = re.search(r's(\d+)', cell_code)
                            if row_match:
                                record['row_code'] = row_match.group(1)
                            if col_match:
                                record['column_code'] = col_match.group(1)
                            if sheet_match:
                                record['sheet_code'] = sheet_match.group(1)

                # Group data entries by row_code
                entries_by_row = {}
                for record in data_records:
                    row_code = record.get('row_code', '')
                    if row_code not in entries_by_row:
                        entries_by_row[row_code] = []
                    entries_by_row[row_code].append(record)

                rows = list(entries_by_row.keys())

                # Build column order if not in context (for wildcard expansion)
                if not context_cols:
                    # Extract unique columns from data in order
                    context_cols = []
                    seen_cols = set()
                    for record in data_records:
                        col = record.get('column_code', '')
                        if col and col not in seen_cols:
                            context_cols.append(col)
                            seen_cols.add(col)

                # Transform the data to match expected JSON structure
                transformed_data = []
                for x_index, row_code in enumerate(rows, 1):
                    for record in entries_by_row[row_code]:
                        # Start with minimal required fields
                        transformed_record = {}

                        # Core fields (always present)
                        if 'variable_id' in record and record['variable_id'] is not None:
                            transformed_record['datapoint'] = record['variable_id']
                        if 'cell_id' in record and record['cell_id'] is not None:
                            transformed_record['operand_reference_id'] = record['cell_id']

                        # Check if data type is scalar (no x/y/z coordinates)
                        # Scalar types: b (boolean), s (string), e (enumeration/item)
                        # Non-scalar types: i, r, m, p (integer, decimal, monetary, percentage)
                        data_type = record.get('data_type', '')
                        is_scalar_type = data_type in ['b', 's', 'e']

                        column_code = record.get('column_code', '')
                        sheet_code = record.get('sheet_code', '')

                        # Add x/y/z coordinates for non-scalar types only
                        if not is_scalar_type:
                            transformed_record['x'] = x_index

                            # Find y coordinate based on column position in context
                            y_index = 1  # default
                            if context_cols and column_code in context_cols:
                                y_index = context_cols.index(column_code) + 1
                            transformed_record['y'] = y_index

                            # Add z coordinate if sheet data exists
                            if sheet_code:
                                # For now, use a simple index; could be enhanced with sheet position logic
                                transformed_record['z'] = 1  # This could be enhanced with actual sheet indexing

                        # Note: column and row are at VarID level, not in data entries

                        # Add additional fields required by ADAM engine
                        # CRITICAL: data_type determines how the engine processes values
                        if 'data_type' in record and record['data_type'] is not None:
                            transformed_record['data_type'] = record['data_type']

                        # Add metadata fields (cell_code, table_code, table_vid)
                        # NOTE: row, column, sheet are NOT included in data - they're at VarID level
                        if 'cell_code' in record and record['cell_code'] is not None:
                            transformed_record['cell_code'] = record['cell_code']
                        if 'table_code' in record and record['table_code'] is not None:
                            transformed_record['table_code'] = record['table_code']
                        if 'table_vid' in record and record['table_vid'] is not None:
                            transformed_record['table_vid'] = record['table_vid']

                        transformed_data.append(transformed_record)

                # Remove common coordinates (coordinates with the same value across all entries)
                # Common coordinates act like "defining variables" and should not be in data entries
                # Variable coordinates should include their dimension codes (row/column/sheet)
                if transformed_data:
                    # Collect all coordinate values to detect which are common
                    coord_values = {'x': set(), 'y': set(), 'z': set()}

                    for record in transformed_data:
                        for coord in ['x', 'y', 'z']:
                            if coord in record:
                                coord_values[coord].add(record[coord])

                    # Identify common vs variable coordinates
                    common_coords = []
                    variable_coords = []
                    for coord, values in coord_values.items():
                        if len(values) == 1:  # All entries have the same value
                            common_coords.append(coord)
                        elif len(values) > 1:  # Coordinate varies
                            variable_coords.append(coord)

                    # For variable coordinates, add dimension codes to each entry
                    # Map coordinates to their dimension codes from original data
                    coord_to_dimension = {
                        'x': 'row_code',
                        'y': 'column_code',
                        'z': 'sheet_code'
                    }
                    coord_to_field = {
                        'x': 'row',
                        'y': 'column',
                        'z': 'sheet'
                    }

                    # Add dimension codes for variable coordinates
                    # We need to match each transformed record back to its original record
                    record_index = 0
                    for x_index, row_code in enumerate(rows, 1):
                        for original_record in entries_by_row[row_code]:
                            if record_index < len(transformed_data):
                                transformed_record = transformed_data[record_index]

                                # Add dimension codes for variable coordinates
                                for coord in variable_coords:
                                    dimension_field = coord_to_dimension[coord]
                                    output_field = coord_to_field[coord]

                                    if dimension_field in original_record and original_record[dimension_field]:
                                        transformed_record[output_field] = original_record[dimension_field]

                                record_index += 1

                    # Remove common coordinates from all entries
                    for record in transformed_data:
                        for coord in common_coords:
                            record.pop(coord, None)

                result['data'] = transformed_data
            else:
                # Handle other data formats if needed
                result['data'] = node.data

        # Filter out None values and internal fields
        filtered_result = {k: v for k, v in result.items() if v is not None}
        return filtered_result

    def visit_AggregationOp(self, node):
        """Visit AggregationOp nodes."""
        return {
            'class_name': 'AggregationOp',
            'op': node.op,
            'operand': self.visit(node.operand)
        }

    def visit_ComplexNumericOp(self, node):
        """Visit ComplexNumericOp nodes (max, min)."""
        return {
            'class_name': 'ComplexNumericOp',
            'op': node.op,
            'operands': [self.visit(operand) for operand in node.operands] if node.operands else []
        }

    def visit_Constant(self, node):
        """Visit Constant nodes."""
        return {
            'class_name': 'Constant',
            'type_': getattr(node, 'type_', getattr(node, 'type', None)),
            'value': node.value
        }

    def visit_ParExpr(self, node):
        """Visit ParExpr nodes."""
        return {
            'class_name': 'ParExpr',
            'expression': self.visit(node.expression)
        }

    def visit_ConditionalOp(self, node):
        """Visit ConditionalOp nodes."""
        result = {
            'class_name': 'ConditionalOp',
            'condition': self.visit(node.condition),
            'then_expr': self.visit(node.then_expr)
        }

        if hasattr(node, 'else_expr') and node.else_expr is not None:
            result['else_expr'] = self.visit(node.else_expr)

        return result

    def visit_Function(self, node):
        """Visit Function nodes."""
        result = {
            'class_name': 'Function',
            'name': node.name
        }

        if hasattr(node, 'args') and node.args:
            result['args'] = [self.visit(arg) for arg in node.args]

        return result

    def visit_Scalar(self, node):
        """Visit Scalar nodes with item name normalization."""
        result = {
            'class_name': 'Scalar'
        }

        # Apply item name normalization for version compatibility
        if hasattr(node, 'item') and node.item:
            item_name = node.item
            # Handle version differences in scalar naming
            # e.g., eba_qEC -> eba_EC, eba_qLR -> eba_LR
            if isinstance(item_name, str) and item_name.startswith('eba_q'):
                normalized_item = item_name.replace('eba_q', 'eba_')
                result['item'] = normalized_item
            else:
                result['item'] = item_name

        # Include scalar_type field (REQUIRED by ADAM Engine)
        if hasattr(node, 'scalar_type') and node.scalar_type:
            result['scalar_type'] = node.scalar_type

        if hasattr(node, 'member') and node.member:
            result['member'] = node.member

        return result

    def generic_visit(self, node):
        """Generic visit method for nodes without specific visitors."""
        result = {
            'class_name': node.__class__.__name__
        }

        # Try to get common attributes
        for attr in ['op', 'name', 'value', 'type_', 'item', 'member']:
            if hasattr(node, attr):
                attr_value = getattr(node, attr)
                if attr_value is not None:
                    result[attr] = attr_value

        # Handle child nodes
        for attr in ['left', 'right', 'operand', 'expression', 'condition', 'then_expr', 'else_expr']:
            if hasattr(node, attr):
                attr_value = getattr(node, attr)
                if attr_value is not None:
                    result[attr] = self.visit(attr_value)

        # Handle lists of child nodes
        for attr in ['children', 'args', 'operands']:
            if hasattr(node, attr):
                attr_value = getattr(node, attr)
                if attr_value and isinstance(attr_value, list):
                    result[attr] = [self.visit(child) for child in attr_value]

        return result


# Original serialization functions (kept for backward compatibility)
import json
from py_dpm.AST import ASTObjects


def expand_with_expression(node):
    """
    Recursively expand WithExpression nodes by merging partial selections into cell references.

    Args:
        node: AST node to process

    Returns:
        Expanded AST node
    """
    if node is None:
        return None

    if isinstance(node, list):
        return [expand_with_expression(item) for item in node]

    if isinstance(node, dict):
        return {key: expand_with_expression(value) for key, value in node.items()}

    # Handle WithExpression expansion
    if isinstance(node, ASTObjects.WithExpression):
        partial_selection = node.partial_selection
        expression = expand_with_expression(node.expression)

        # Apply partial selection to all VarID nodes in the expression
        return apply_partial_selection(expression, partial_selection)

    # Handle Start node - check if it contains WithExpression
    if isinstance(node, ASTObjects.Start):
        expanded_children = []
        for child in node.children:
            if isinstance(child, ASTObjects.WithExpression):
                # Expand the WithExpression and return just the expanded expression
                expanded = expand_with_expression(child)
                expanded_children.append(expanded)
            else:
                expanded_children.append(expand_with_expression(child))

        # If we have a single expanded child that came from a WithExpression,
        # return the expanded expression directly (no Start wrapper)
        if len(expanded_children) == 1:
            return expanded_children[0]
        else:
            return ASTObjects.Start(children=expanded_children)

    # For other node types, recursively expand children
    if hasattr(node, '__dict__'):
        expanded_node = type(node).__new__(type(node))
        for attr_name, attr_value in node.__dict__.items():
            setattr(expanded_node, attr_name, expand_with_expression(attr_value))
        return expanded_node

    return node


def apply_partial_selection(expression, partial_selection):
    """
    Apply partial selection to VarID nodes in the expression.

    Args:
        expression: Expression AST node
        partial_selection: Partial selection VarID node

    Returns:
        Modified expression with partial selection applied
    """
    if expression is None:
        return None

    if isinstance(expression, list):
        return [apply_partial_selection(item, partial_selection) for item in expression]

    if isinstance(expression, dict):
        return {key: apply_partial_selection(value, partial_selection) for key, value in expression.items()}

    # Apply partial selection to VarID nodes
    if isinstance(expression, ASTObjects.VarID):
        # Create a new VarID with merged properties
        new_varid = ASTObjects.VarID(
            table=partial_selection.table if expression.table is None else expression.table,
            rows=partial_selection.rows if expression.rows is None else expression.rows,
            cols=expression.cols,  # Keep the original cols from the expression
            sheets=partial_selection.sheets if expression.sheets is None else expression.sheets,
            interval=partial_selection.interval if expression.interval is None else expression.interval,
            default=partial_selection.default if expression.default is None else expression.default,
            is_table_group=partial_selection.is_table_group if hasattr(partial_selection, 'is_table_group') else False
        )
        return new_varid

    # For other node types, recursively apply to children
    if hasattr(expression, '__dict__'):
        modified_expr = type(expression).__new__(type(expression))
        for attr_name, attr_value in expression.__dict__.items():
            setattr(modified_expr, attr_name, apply_partial_selection(attr_value, partial_selection))
        return modified_expr

    return expression


def serialize_ast(ast_obj):
    """
    Serialize an AST object to a JSON-serializable dictionary.
    Expands WithExpression nodes before serialization.

    Args:
        ast_obj: An AST object instance

    Returns:
        dict: JSON-serializable dictionary representation
    """
    if ast_obj is None:
        return None

    # First expand any WithExpression nodes
    expanded_obj = expand_with_expression(ast_obj)

    if isinstance(expanded_obj, list):
        return [serialize_ast(item) for item in expanded_obj]

    if isinstance(expanded_obj, dict):
        return {key: serialize_ast(value) for key, value in expanded_obj.items()}

    if hasattr(expanded_obj, 'toJSON'):
        serialized = expanded_obj.toJSON()
        # Recursively serialize nested AST objects
        for key, value in serialized.items():
            if key != 'class_name':
                serialized[key] = serialize_ast(value)
        return serialized

    # For basic types (str, int, float, bool)
    if isinstance(expanded_obj, (str, int, float, bool, type(None))):
        return expanded_obj

    # Fallback: serialize as dict for objects without toJSON
    return expanded_obj.__dict__


def deserialize_ast(data):
    """
    Deserialize a JSON dictionary back to an AST object.

    Args:
        data: Dictionary or list from JSON

    Returns:
        AST object instance
    """
    if data is None:
        return None

    if isinstance(data, list):
        return [deserialize_ast(item) for item in data]

    if isinstance(data, dict):
        if 'class_name' in data:
            # This is an AST object
            class_name = data['class_name']

            # Get the class from ASTObjects module
            if hasattr(ASTObjects, class_name):
                cls = getattr(ASTObjects, class_name)

                # Create a new instance
                obj = object.__new__(cls)

                # Initialize the base AST attributes
                obj.num = None
                obj.prev = None

                # Set all the attributes from the serialized data
                for key, value in data.items():
                    if key != 'class_name':
                        setattr(obj, key, deserialize_ast(value))

                return obj
            else:
                raise ValueError(f"Unknown AST class: {class_name}")
        else:
            # Regular dictionary, deserialize values
            return {key: deserialize_ast(value) for key, value in data.items()}

    # For basic types
    return data


def ast_to_json_string(ast_obj, indent=None):
    """
    Convert AST object to JSON string.

    Args:
        ast_obj: AST object to serialize
        indent: JSON indentation (optional)

    Returns:
        str: JSON string representation
    """
    return json.dumps(serialize_ast(ast_obj), indent=indent)


def ast_from_json_string(json_str):
    """
    Create AST object from JSON string.

    Args:
        json_str: JSON string representation

    Returns:
        AST object instance
    """
    data = json.loads(json_str)
    return deserialize_ast(data)