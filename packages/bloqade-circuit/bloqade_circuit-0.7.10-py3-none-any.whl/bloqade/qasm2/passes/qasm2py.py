"""Rewrite qasm dialects into py dialects."""

import math as pymath

from kirin import ir
from kirin.passes import Pass
from kirin.rewrite import Walk, Fixpoint
from kirin.dialects import py, math
from kirin.rewrite.abc import RewriteRule, RewriteResult

from bloqade.qasm2.dialects import core, expr


class _QASM2Py(RewriteRule):
    """Rewrite qasm dialects into py dialects."""

    UNARY_OPS = {
        expr.Neg: py.USub,
        expr.Sin: math.stmts.sin,
        expr.Cos: math.stmts.cos,
        expr.Tan: math.stmts.tan,
        expr.Exp: math.stmts.exp,
        expr.Sqrt: math.stmts.sqrt,
    }

    BINARY_OPS = {
        expr.Add: py.Add,
        expr.Sub: py.Sub,
        expr.Mul: py.Mult,
        expr.Div: py.Div,
        expr.Pow: py.Pow,
    }

    def rewrite_Statement(self, node: ir.Statement) -> RewriteResult:
        if isinstance(node, (expr.ConstInt, expr.ConstFloat)):
            node.replace_by(py.Constant(value=node.value))
            return RewriteResult(has_done_something=True)
        elif isinstance(node, expr.Neg):
            node.replace_by(self.UNARY_OPS[type(node)](value=node.value))
            return RewriteResult(has_done_something=True)
        elif isinstance(node, (expr.Sin, expr.Cos, expr.Tan, expr.Exp, expr.Sqrt)):
            node.replace_by(self.UNARY_OPS[type(node)](x=node.value))
            return RewriteResult(has_done_something=True)
        elif isinstance(node, (expr.Add, expr.Sub, expr.Mul, expr.Div, expr.Pow)):
            node.replace_by(self.BINARY_OPS[type(node)](lhs=node.lhs, rhs=node.rhs))
            return RewriteResult(has_done_something=True)
        elif isinstance(node, core.CRegEq):
            node.replace_by(py.cmp.Eq(node.lhs, node.rhs))
            return RewriteResult(has_done_something=True)
        elif isinstance(node, expr.ConstPI):
            node.replace_by(py.Constant(value=pymath.pi))
            return RewriteResult(has_done_something=True)
        else:
            return RewriteResult()


class QASM2Py(Pass):

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        return Fixpoint(Walk(_QASM2Py())).rewrite(mt.code)
