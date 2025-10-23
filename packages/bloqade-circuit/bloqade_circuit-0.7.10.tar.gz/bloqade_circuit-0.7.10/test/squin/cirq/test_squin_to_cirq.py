import math
import typing

import cirq
import pytest
from kirin.emit import EmitError
from kirin.passes import inline
from kirin.dialects import ilist

from bloqade import squin


def test_pauli():
    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        q2 = squin.qubit.new(4)
        x = squin.op.x()
        y = squin.op.y()
        z = squin.op.z()
        squin.qubit.apply(x, q[0])
        squin.qubit.apply(y, q2[0])
        squin.qubit.apply(z, q2[3])

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)

    qbits = circuit.all_qubits()
    assert len(qbits) == 3
    assert isinstance(qbit := list(qbits)[-1], cirq.LineQubit)
    assert qbit.x == 5


@pytest.mark.parametrize("op_name", ["h", "s", "t", "x", "y", "z"])
def test_basic_op(op_name: str):
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        op_ = getattr(squin.op, op_name)()
        squin.qubit.apply(op_, q)

    squin.cirq.emit_circuit(main)


def test_control():
    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        h = squin.op.h()
        squin.qubit.apply(h, q[0])
        cx = squin.op.cx()
        squin.qubit.apply(cx, q)

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)

    assert len(circuit) == 2
    assert circuit[1].operations[0].gate == cirq.CNOT


def test_custom_qubits():
    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        h = squin.op.h()
        squin.qubit.apply(h, q[0])
        cx = squin.op.cx()
        squin.qubit.apply(cx, q)

    qubits = [cirq.GridQubit(0, 1), cirq.GridQubit(2, 2)]
    circuit = squin.cirq.emit_circuit(main, qubits=qubits)

    print(circuit)

    circuit_qubits = circuit.all_qubits()
    assert len(circuit_qubits) == 2
    assert frozenset(qubits) == circuit_qubits


def test_composed_kernels():
    @squin.kernel
    def sub_kernel(q_: ilist.IList[squin.qubit.Qubit, typing.Any]):
        h = squin.op.h()
        squin.qubit.apply(h, q_[0])

    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        sub_kernel(q)

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)

    assert len(circuit) == 1
    assert len(circuit[0].operations) == 1
    assert isinstance(circuit[0].operations[0], cirq.CircuitOperation)


def test_nested_kernels():
    @squin.kernel
    def sub_kernel2(q2_: ilist.IList[squin.qubit.Qubit, typing.Any]):
        cx = squin.op.control(squin.op.x(), n_controls=1)
        squin.qubit.apply(cx, q2_[0], q2_[1])

    @squin.kernel
    def sub_kernel(q_: ilist.IList[squin.qubit.Qubit, typing.Any]):
        h = squin.op.h()
        squin.qubit.apply(h, q_[0])
        id = squin.op.identity(sites=1)
        squin.qubit.apply(id, q_[1])
        sub_kernel2(q_)

    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        sub_kernel(q)

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)


def test_return_value():
    @squin.kernel
    def sub_kernel(q: ilist.IList[squin.qubit.Qubit, typing.Any]):
        h = squin.op.h()
        squin.qubit.apply(h, q[0])
        cx = squin.op.cx()
        squin.qubit.apply(cx, q[0], q[1])
        return h

    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        h_ = sub_kernel(q)
        squin.qubit.apply(h_, q[1])

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)

    with pytest.raises(EmitError):
        squin.cirq.emit_circuit(sub_kernel)

    @squin.kernel
    def main2():
        q = squin.qubit.new(2)
        h_ = sub_kernel(q)
        squin.qubit.apply(h_, q[1])
        return h_

    circuit2 = squin.cirq.emit_circuit(main2, ignore_returns=True)
    print(circuit2)

    assert circuit2 == circuit


def test_return_qubits():
    @squin.kernel
    def sub_kernel(q: ilist.IList[squin.qubit.Qubit, typing.Any]):
        h = squin.op.h()
        squin.qubit.apply(h, q[0])
        cx = squin.op.cx()
        q2 = squin.qubit.new(3)
        squin.qubit.apply(cx, [q[0], q2[2]])
        return q2

    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        q2_ = sub_kernel(q)
        squin.qubit.apply(squin.op.x(), q2_[0])

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)


def test_measurement():
    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        y = squin.op.y()
        squin.qubit.broadcast(y, q)
        squin.qubit.measure(q)

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)


def test_kron():
    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        x = squin.op.x()
        xx = squin.op.kron(x, x)
        squin.qubit.apply(xx, q)

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)


def test_mult():
    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        x = squin.op.x()
        y = squin.op.y()
        m = squin.op.mult(x, y)
        squin.qubit.apply(m, q[0])

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)


def test_projector():
    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        h = squin.op.h()
        squin.qubit.broadcast(h, q)
        p0 = squin.op.p0()
        p1 = squin.op.p1()
        squin.qubit.apply(p0, q[0])
        squin.qubit.apply(p1, q[1])
        squin.qubit.measure(q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_sp_sn():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        sp = squin.op.spin_p()
        sn = squin.op.spin_n()
        squin.qubit.apply(sp, q)
        squin.qubit.apply(sn, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_adjoint():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        s = squin.op.s()
        s_dagger = squin.op.adjoint(s)
        squin.qubit.apply(s, q)
        squin.qubit.apply(s_dagger, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_u3():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        u3 = squin.op.u(0.323, 1.123, math.pi / 7)
        squin.qubit.apply(u3, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_scale():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        x = squin.op.x()
        s = 2 * x
        squin.qubit.apply(s, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_phase():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        p = squin.op.phase(math.pi / 3)
        squin.qubit.apply(p, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_shift():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        p = squin.op.shift(math.pi / 7)
        squin.qubit.apply(p, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_reset():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        r = squin.op.reset()
        squin.qubit.apply(r, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_pauli_string():
    @squin.kernel
    def main():
        p = squin.op.pauli_string(string="XYZ")
        q = squin.qubit.new(3)
        squin.qubit.apply(p, q)

    circuit = squin.cirq.emit_circuit(main)
    print(circuit)


def test_invoke_cache():
    @squin.kernel
    def sub_kernel(q_: squin.qubit.Qubit):
        squin.qubit.apply(squin.op.h(), q_)

    @squin.kernel
    def main():
        q = squin.qubit.new(2)
        q0 = q[0]
        sub_kernel(q0)
        sub_kernel(q[1])
        sub_kernel(q0)

    target = squin.cirq.EmitCirq(main.dialects)

    circuit = target.run(main, ())

    print(circuit)

    assert len(target._cached_circuit_operations) == 2


def test_rot():
    @squin.kernel
    def main():
        axis = squin.op.x()
        q = squin.qubit.new(1)
        r = squin.op.rot(axis=axis, angle=math.pi / 2)
        squin.qubit.apply(r, q[0])

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)

    assert circuit[0].operations[0].gate == cirq.Rx(rads=math.pi / 2)

    @squin.kernel
    def main2():
        x = squin.op.x()
        y = squin.op.y()
        q = squin.qubit.new(1)
        r = squin.op.rot(axis=x * y, angle=0.123)
        squin.qubit.apply(r, q[0])

    with pytest.raises(EmitError):
        squin.cirq.emit_circuit(main2)

    @squin.kernel
    def main3():
        op = squin.op.h()
        q = squin.qubit.new(1)
        r = squin.op.rot(axis=op, angle=0.123)
        squin.qubit.apply(r, q[0])

    with pytest.raises(EmitError):
        squin.cirq.emit_circuit(main3)


def test_additional_stmts():
    @squin.kernel
    def main():
        x = squin.op.x()
        r = squin.op.rot(x, 0.123)
        q = squin.qubit.new(3)
        squin.qubit.apply(r, q[0])
        sqrt_x = squin.op.sqrt_x()
        sqrt_y = squin.op.sqrt_y()
        squin.qubit.apply(sqrt_x, q[1])
        squin.qubit.apply(sqrt_y, q[2])

    main.print()

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)

    q = cirq.LineQubit.range(3)
    expected_circuit = cirq.Circuit(
        cirq.Rx(rads=0.123).on(q[0]),
        cirq.X(q[1]) ** 0.5,
        cirq.Y(q[2]) ** 0.5,
    )

    assert circuit == expected_circuit


def test_return_measurement():

    @squin.kernel
    def coinflip():
        qubit = squin.qubit.new(1)[0]
        squin.gate.h(qubit)
        return squin.qubit.measure(qubit)

    coinflip.print()

    circuit = squin.cirq.emit_circuit(coinflip, ignore_returns=True)
    print(circuit)


def test_reset_to_one():
    @squin.kernel
    def main():
        q = squin.qubit.new(1)
        squin.gate.h(q[0])
        squin.gate.reset_to_one(q[0])

    inline.InlinePass(main.dialects)(main)

    main.print()

    circuit = squin.cirq.emit_circuit(main)

    q = cirq.LineQubit(0)
    expected_circuit = cirq.Circuit(
        cirq.H(q),
        cirq.reset(q),
        cirq.X(q),
    )

    print(circuit)

    assert circuit == expected_circuit


def test_overlapping_operations():
    @squin.kernel
    def main():
        q = squin.qubit.new(5)

        x = squin.op.x()
        y = squin.op.y()
        op = x * y

        squin.qubit.broadcast(op, q)

    circuit = squin.cirq.emit_circuit(main)

    print(circuit)
