import ast
import operator
from math import ceil, floor, sqrt, trunc
from typing import Set

# supported operators
base_operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg,
    ast.mod: operator.mod,
}

# supported functions
base_functions = {
    "round": round,
    "floor": floor,
    "ceil": ceil,
    "abs": abs,
    "trunc": trunc,
    "sqrt": sqrt,
    "sum": sum,
    "max": max,
    "min": min,
}


# noinspection PyTypeChecker
class BasicEvaluatorVisitor(ast.NodeVisitor):
    operators = base_operators
    functions = base_functions

    def __init__(self, **kwargs):
        self._variables = kwargs

    def visit_Name(self, node: ast.Name):
        if node.id in self._variables:
            return self._variables[node.id]
        else:
            raise AttributeError(f"Variable not found: {node.id}")

    def visit_Constant(self, node: ast.Constant):
        return node.value

    def visit_UnaryOp(self, node: ast.UnaryOp):
        val = self.visit(node.operand)
        op = type(node.op)
        if op in self.operators:
            return self.operators[op](val)
        else:
            raise TypeError(f"Unsupported operation: {op.__name__}")

    def visit_BinOp(self, node: ast.BinOp):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        op = type(node.op)
        if op in self.operators:
            return self.operators[op](lhs, rhs)
        else:
            raise TypeError(f"Unsupported operation: {op.__name__}")

    def visit_Subscript(self, node: ast.Subscript):
        val = self.visit(node.value)
        index = self.visit(node.slice)
        try:
            return val[index]
        except AttributeError:
            return self.generic_visit(node)

    def visit_Index(self, node: ast.Index, **kwargs):
        """df.index[4]"""
        return self.visit(node.value)

    def visit_Slice(self, node: ast.Slice):
        lower = node.lower
        if lower is not None:
            lower = self.visit(lower)
        upper = node.upper
        if upper is not None:
            upper = self.visit(upper)
        step = node.step
        if step is not None:
            step = self.visit(step)

        return slice(lower, upper, step)

    def visit_Call(self, node: ast.Call):
        if node.func.id in self.functions:
            new_args = [self.visit(arg) for arg in node.args]
            return self.functions[node.func.id](*new_args)
        else:
            self.generic_visit(node)

    def generic_visit(self, node):
        if isinstance(node, ast.Call):
            raise TypeError(f"Unsupported operation: {getattr(node.func,'id')}")
        raise ValueError("malformed node or string: " + repr(node))


boolean_operators = {
    **base_operators,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Not: operator.not_,
}


# noinspection PyTypeChecker
class BooleanEvaluatorVisitor(BasicEvaluatorVisitor):
    operators = boolean_operators

    def visit_bool(self, node: bool):
        return node

    def visit_BoolOp(self, node: ast.BoolOp):
        if isinstance(node.op, (ast.And, ast.Or)):
            values = map(self.visit, node.values)
            return all(values) if isinstance(node.op, ast.And) else any(values)
        else:
            return self.generic_visit(self, node)

    def visit_Compare(self, node: ast.Compare, **kwargs):
        # base case: we have something like a CMP b
        if len(node.comparators) == 1:
            bin_op = ast.BinOp(op=node.ops[0], left=node.left, right=node.comparators[0])
            return self.visit(bin_op)

        # recursive case: we have a chained comparison, a CMP b CMP c, etc.
        left = node.left
        values = []
        for op, comp in zip(node.ops, node.comparators):
            new_node = self.visit(ast.Compare(comparators=[comp], left=left, ops=[op]))
            left = comp
            values.append(new_node)
        return self.visit(ast.BoolOp(op=ast.And(), values=values))


def evaluate_expression(expr, **kwargs):
    v = BasicEvaluatorVisitor(**kwargs)
    return v.visit(ast.parse(expr, mode="eval").body)


def evaluate_boolean_expression(expr, **kwargs):
    v = BooleanEvaluatorVisitor(**kwargs)
    return v.visit(ast.parse(expr, mode="eval").body)


def get_expression_variables(source) -> Set:
    variables = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in base_functions:
            variables.add(node.id)
    return variables
