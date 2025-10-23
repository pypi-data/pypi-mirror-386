from dataclasses import dataclass

from kirin import ir, interp
from kirin.dialects import cf, scf, func
from kirin.ir.dialect import Dialect as Dialect

from bloqade.qasm2.parse import ast
from bloqade.qasm2.dialects.uop import SingleQubitGate, TwoQubitCtrlGate
from bloqade.qasm2.dialects.expr import GateFunction

from .base import EmitQASM2Base, EmitQASM2Frame
from ..dialects.core.stmts import Reset, Measure


@dataclass
class EmitQASM2Main(EmitQASM2Base[ast.Statement, ast.MainProgram]):
    keys = ["emit.qasm2.main", "emit.qasm2.gate"]
    dialects: ir.DialectGroup


@func.dialect.register(key="emit.qasm2.main")
class Func(interp.MethodTable):

    @interp.impl(func.Function)
    def emit_func(
        self, emit: EmitQASM2Main, frame: EmitQASM2Frame, stmt: func.Function
    ):
        from bloqade.qasm2.dialects import glob, parallel

        emit.run_ssacfg_region(frame, stmt.body, ())
        if emit.dialects.data.intersection((parallel.dialect, glob.dialect)):
            header = ast.Kirin([dialect.name for dialect in emit.dialects])
        else:
            header = ast.OPENQASM(ast.Version(2, 0))

        emit.output = ast.MainProgram(header=header, statements=frame.body)
        return ()


@cf.dialect.register(key="emit.qasm2.main")
class Cf(interp.MethodTable):

    @interp.impl(cf.Branch)
    def emit_branch(self, emit: EmitQASM2Main, frame: EmitQASM2Frame, stmt: cf.Branch):
        frame.worklist.append(
            interp.Successor(stmt.successor, frame.get_values(stmt.arguments))
        )
        return ()

    @interp.impl(cf.ConditionalBranch)
    def emit_conditional_branch(
        self, emit: EmitQASM2Main, frame: EmitQASM2Frame, stmt: cf.ConditionalBranch
    ):
        cond = emit.assert_node(ast.Cmp, frame.get(stmt.cond))

        with emit.new_frame(stmt) as body_frame:
            body_frame.entries.update(frame.entries)
            body_frame.set_values(
                stmt.then_successor.args, frame.get_values(stmt.then_arguments)
            )
            emit.emit_block(body_frame, stmt.then_successor)

        frame.body.append(
            ast.IfStmt(
                cond,
                body=body_frame.body,  # type: ignore
            )
        )
        frame.worklist.append(
            interp.Successor(stmt.else_successor, frame.get_values(stmt.else_arguments))
        )
        return ()


@scf.dialect.register(key="emit.qasm2.main")
class Scf(interp.MethodTable):

    @interp.impl(scf.Yield)
    def emit_yield(self, emit: EmitQASM2Main, frame: EmitQASM2Frame, stmt: scf.Yield):
        return frame.get_values(stmt.values)

    @interp.impl(scf.IfElse)
    def emit_if_else(
        self, emit: EmitQASM2Main, frame: EmitQASM2Frame, stmt: scf.IfElse
    ):
        else_stmts = stmt.else_body.blocks[0].stmts
        if not (
            len(else_stmts) == 0
            or len(else_stmts) == 1
            and isinstance(else_stmts.at(0), scf.Yield)
        ):
            raise interp.InterpreterError(
                "cannot lower if-else with non-empty else block"
            )

        cond = emit.assert_node(ast.Cmp, frame.get(stmt.cond))

        # NOTE: we need exactly one of those in the then body in order to emit valid QASM2
        AllowedThenType = SingleQubitGate | TwoQubitCtrlGate | Measure | Reset

        then_stmts = stmt.then_body.blocks[0].stmts
        uop_stmts = 0
        for s in then_stmts:
            if isinstance(s, AllowedThenType):
                uop_stmts += 1
                continue

            if isinstance(s, func.Invoke):
                uop_stmts += isinstance(s.callee.code, GateFunction)

        if uop_stmts != 1:
            raise interp.InterpreterError(
                "Cannot lower if-statement: QASM2 only allows exactly one quantum operation in the body."
            )

        with emit.new_frame(stmt) as then_frame:
            then_frame.entries.update(frame.entries)
            emit.emit_block(then_frame, stmt.then_body.blocks[0])
            frame.body.append(
                ast.IfStmt(
                    cond,
                    body=then_frame.body,  # type: ignore
                )
            )

        term = stmt.then_body.blocks[0].last_stmt
        if isinstance(term, scf.Yield):
            return then_frame.get_values(term.values)
        return ()
