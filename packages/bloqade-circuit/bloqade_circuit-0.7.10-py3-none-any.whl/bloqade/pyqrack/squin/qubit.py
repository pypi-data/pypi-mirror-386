from typing import Any

from kirin import interp
from kirin.dialects import ilist

from bloqade.squin import qubit
from bloqade.pyqrack.reg import QubitState, Measurement, PyQrackQubit
from bloqade.pyqrack.base import PyQrackInterpreter

from .runtime import OperatorRuntimeABC


@qubit.dialect.register(key="pyqrack")
class PyQrackMethods(interp.MethodTable):
    @interp.impl(qubit.New)
    def new(self, interp: PyQrackInterpreter, frame: interp.Frame, stmt: qubit.New):
        n_qubits: int = frame.get(stmt.n_qubits)
        qreg = ilist.IList(
            [
                PyQrackQubit(i, interp.memory.sim_reg, QubitState.Active)
                for i in interp.memory.allocate(n_qubits=n_qubits)
            ]
        )
        return (qreg,)

    @interp.impl(qubit.Apply)
    def apply(self, interp: PyQrackInterpreter, frame: interp.Frame, stmt: qubit.Apply):
        qubits: list[PyQrackQubit] = [frame.get(qbit) for qbit in stmt.qubits]
        operator: OperatorRuntimeABC = frame.get(stmt.operator)
        operator.apply(*qubits)

    @interp.impl(qubit.Broadcast)
    def broadcast(
        self, interp: PyQrackInterpreter, frame: interp.Frame, stmt: qubit.Broadcast
    ):
        operator: OperatorRuntimeABC = frame.get(stmt.operator)
        qubits: list[ilist.IList[PyQrackQubit, Any]] = [
            frame.get(qbit) for qbit in stmt.qubits
        ]
        operator.broadcast_apply(qubits)

    def _measure_qubit(self, qbit: PyQrackQubit, interp: PyQrackInterpreter):
        if qbit.is_active():
            m = Measurement(bool(qbit.sim_reg.m(qbit.addr)))
        else:
            m = Measurement(interp.loss_m_result)

        interp.set_global_measurement_id(m)
        return m

    @interp.impl(qubit.MeasureQubitList)
    def measure_qubit_list(
        self,
        interp: PyQrackInterpreter,
        frame: interp.Frame,
        stmt: qubit.MeasureQubitList,
    ):
        qubits: ilist.IList[PyQrackQubit, Any] = frame.get(stmt.qubits)
        result = ilist.IList([self._measure_qubit(qbit, interp) for qbit in qubits])
        return (result,)

    @interp.impl(qubit.MeasureQubit)
    def measure_qubit(
        self, interp: PyQrackInterpreter, frame: interp.Frame, stmt: qubit.MeasureQubit
    ):
        qbit: PyQrackQubit = frame.get(stmt.qubit)
        result = self._measure_qubit(qbit, interp)
        return (result,)

    @interp.impl(qubit.QubitId)
    def qubit_id(
        self, interp: PyQrackInterpreter, frame: interp.Frame, stmt: qubit.QubitId
    ):
        qbit: PyQrackQubit = frame.get(stmt.qubit)
        return (qbit.addr,)

    @interp.impl(qubit.MeasurementId)
    def measurement_id(
        self, interp: PyQrackInterpreter, frame: interp.Frame, stmt: qubit.MeasurementId
    ):
        measurement: Measurement = frame.get(stmt.measurement)
        return (measurement.measurement_id,)
