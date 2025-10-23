from typing import TypeVar
from dataclasses import field

from kirin import ir, interp
from kirin.analysis import Forward, const
from kirin.analysis.forward import ForwardFrame

from bloqade.types import QubitType

from .lattice import Address


class AddressAnalysis(Forward[Address]):
    """
    This analysis pass can be used to track the global addresses of qubits and wires.
    """

    keys = ["qubit.address"]
    lattice = Address
    next_address: int = field(init=False)

    def initialize(self):
        super().initialize()
        self.next_address: int = 0
        return self

    @property
    def qubit_count(self) -> int:
        """Total number of qubits found by the analysis."""
        return self.next_address

    T = TypeVar("T")

    def get_const_value(self, typ: type[T], value: ir.SSAValue) -> T:
        if isinstance(hint := value.hints.get("const"), const.Value):
            data = hint.data
            if isinstance(data, typ):
                return hint.data
            raise interp.InterpreterError(
                f"Expected constant value <type = {typ}>, got {data}"
            )
        raise interp.InterpreterError(
            f"Expected constant value <type = {typ}>, got {value}"
        )

    def eval_stmt_fallback(
        self, frame: ForwardFrame[Address], stmt: ir.Statement
    ) -> tuple[Address, ...] | interp.SpecialValue[Address]:
        return tuple(
            (
                self.lattice.top()
                if result.type.is_subseteq(QubitType)
                else self.lattice.bottom()
            )
            for result in stmt.results
        )

    def run_method(self, method: ir.Method, args: tuple[Address, ...]):
        # NOTE: we do not support dynamic calls here, thus no need to propagate method object
        return self.run_callable(method.code, (self.lattice.bottom(),) + args)
