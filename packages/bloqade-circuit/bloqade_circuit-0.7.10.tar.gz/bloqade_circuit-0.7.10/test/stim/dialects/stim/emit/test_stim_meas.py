from bloqade import stim
from bloqade.stim.dialects import collapse

from .base import codegen


def test_meas():

    @stim.main
    def test_simple_meas():
        collapse.MX(p=0.3, targets=(0, 3, 4, 5))

    out = codegen(test_simple_meas)

    assert out.strip() == "MX(0.30000000) 0 3 4 5"
