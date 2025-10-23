from bloqade import qasm2
from bloqade.qasm2 import noise as native
from bloqade.qasm2.rewrite.noise.remove_noise import RemoveNoisePass


def test():

    @qasm2.extended
    def test_atom_loss():
        q = qasm2.qreg(2)
        native.atom_loss_channel([q[0], q[1]], prob=0.7)
        native.cz_pauli_channel(
            [q[0]],
            [q[1]],
            paired=False,
            px_ctrl=0.1,
            py_ctrl=0.4,
            pz_ctrl=0.3,
            px_qarg=0.2,
            py_qarg=0.2,
            pz_qarg=0.2,
        )  # no noise here
        qasm2.parallel.cz([q[0]], [q[1]])
        native.atom_loss_channel([q[0], q[1]], prob=0.7)
        native.cz_pauli_channel(
            [q[0]],
            [q[1]],
            paired=False,
            px_ctrl=0.1,
            py_ctrl=0.4,
            pz_ctrl=0.3,
            px_qarg=0.2,
            py_qarg=0.2,
            pz_qarg=0.2,
        )
        qasm2.parallel.cz([q[0]], [q[1]])
        return q

    @qasm2.extended
    def tests():
        q = qasm2.qreg(2)
        qasm2.parallel.cz([q[0]], [q[1]])
        qasm2.parallel.cz([q[0]], [q[1]])
        return q

    RemoveNoisePass(qasm2.extended)(test_atom_loss)
    assert test_atom_loss.callable_region.is_structurally_equal(tests.callable_region)
