from typing import Union

from kirin.lowering import wraps

from .dialects import gate, noise, collapse, auxiliary


# dialect:: gate
## 1q
@wraps(gate.X)
def x(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.Y)
def y(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.Z)
def z(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.Identity)
def identity(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.H)
def h(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.S)
def s(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.SqrtX)
def sqrt_x(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.SqrtY)
def sqrt_y(targets: tuple[int, ...], dagger: bool = False) -> None: ...


@wraps(gate.SqrtZ)
def sqrt_z(targets: tuple[int, ...], dagger: bool = False) -> None: ...


## clif 2q
@wraps(gate.Swap)
def swap(targets: tuple[int, ...], dagger: bool = False) -> None: ...


## ctrl 2q
@wraps(gate.CX)
def cx(
    controls: tuple[int, ...], targets: tuple[int, ...], dagger: bool = False
) -> None: ...


@wraps(gate.CY)
def cy(
    controls: tuple[int, ...], targets: tuple[int, ...], dagger: bool = False
) -> None: ...


@wraps(gate.CZ)
def cz(
    controls: tuple[int, ...], targets: tuple[int, ...], dagger: bool = False
) -> None: ...


## pp
@wraps(gate.SPP)
def spp(targets: tuple[auxiliary.PauliString, ...], dagger=False) -> None: ...


# dialect:: aux
@wraps(auxiliary.GetRecord)
def rec(id: int) -> auxiliary.RecordResult: ...


@wraps(auxiliary.Detector)
def detector(
    coord: tuple[Union[int, float], ...], targets: tuple[auxiliary.RecordResult, ...]
) -> None: ...


@wraps(auxiliary.ObservableInclude)
def observable_include(
    idx: int, targets: tuple[auxiliary.RecordResult, ...]
) -> None: ...


@wraps(auxiliary.Tick)
def tick() -> None: ...


@wraps(auxiliary.NewPauliString)
def pauli_string(
    string: tuple[str, ...], flipped: tuple[bool, ...], targets: tuple[int, ...]
) -> auxiliary.PauliString: ...


@wraps(auxiliary.QubitCoordinates)
def qubit_coords(coord: tuple[Union[int, float], ...], target: int) -> None: ...


# dialect:: collapse
@wraps(collapse.MZ)
def mz(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(collapse.MY)
def my(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(collapse.MX)
def mx(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(collapse.MZZ)
def mzz(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(collapse.MYY)
def myy(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(collapse.MXX)
def mxx(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(collapse.PPMeasurement)
def mpp(p: float, targets: tuple[auxiliary.PauliString, ...]) -> None: ...


@wraps(collapse.RZ)
def rz(targets: tuple[int, ...]) -> None: ...


@wraps(collapse.RY)
def ry(targets: tuple[int, ...]) -> None: ...


@wraps(collapse.RX)
def rx(targets: tuple[int, ...]) -> None: ...


# dialect:: noise
@wraps(noise.Depolarize1)
def depolarize1(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(noise.Depolarize2)
def depolarize2(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(noise.PauliChannel1)
def pauli_channel1(
    px: float, py: float, pz: float, targets: tuple[int, ...]
) -> None: ...


@wraps(noise.PauliChannel2)
def pauli_channel2(
    pix: float,
    piy: float,
    piz: float,
    pxi: float,
    pxx: float,
    pxy: float,
    pxz: float,
    pyi: float,
    pyx: float,
    pyy: float,
    pyz: float,
    pzi: float,
    pzx: float,
    pzy: float,
    pzz: float,
    targets: tuple[int, ...],
) -> None: ...


@wraps(noise.XError)
def x_error(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(noise.YError)
def y_error(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(noise.ZError)
def z_error(p: float, targets: tuple[int, ...]) -> None: ...


@wraps(noise.QubitLoss)
def qubit_loss(probs: tuple[float, ...], targets: tuple[int, ...]) -> None: ...
