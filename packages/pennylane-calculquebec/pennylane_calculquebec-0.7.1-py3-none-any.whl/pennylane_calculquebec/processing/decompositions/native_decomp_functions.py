"""
contains every equivalences needed for decomposing MonarQ non-native gates.
"""

import pennylane_calculquebec.processing.custom_gates as custom
import numpy as np
import pennylane as qml


def is_close_enough_to(angle, other_angle, epsilon=1e-7):
    return np.abs(angle - other_angle) < epsilon


def _custom_tdag(wires):
    """
    a MonarQ native implementation of the adjoint(T) operation
    Args:
        wires (list[int]) : Which wires does the operation act on?

    Returns:
        list[Operation] : Which operations correspond to an adjoint t gate on MonarQ
    """
    return [custom.TDagger(wires)]


def _custom_sx(wires):
    """
    a MonarQ native implementation of the SX operation

    Args:
        wires (list[int]) : Which wires does the operation act on?

    Returns:
        list[Operation] : Which operations correspond to an sx gate on MonarQ
    """
    return [custom.X90(wires)]


def _custom_sxdag(wires):
    """
    a MonarQ native implementation of the adjoint(SX) operation

    Args:
        wires (list[int]) : Which wires does the operation act on?

    Returns:
        list[Operation] : Which operations correspond to an adjoint sx gate on MonarQ
    """
    return [custom.XM90(wires)]


def _custom_s(wires):
    """
    a MonarQ native implementation of the S operation

    Args:
        wires (list[int]) : Which wires does the operation act on?
    Returns:
        list[Operation] : Which operations correspond to an s gate on MonarQ
    """
    return [custom.Z90(wires)]


def _custom_sdag(wires):
    """
    a MonarQ native implementation of the adjoint(S) operation

    Args:
        wires (list[int]) : Which wires does the operation act on?
    Returns:
        list[Operation] : Which operations correspond to an adjoint s gate on MonarQ
    """
    return [custom.ZM90(wires)]


def _custom_h(wires):
    """
    a MonarQ native implementation of the Hadamard operation

    Args:
        wires (list[int]) : Which wires does the operation act on?

    Returns:
        list[Operation] : Which operations correspond to an h gate on MonarQ
    """
    return [custom.Z90(wires), custom.X90(wires), custom.Z90(wires)]


def _custom_cnot(wires):
    """
    a MonarQ native implementation of the CNOT operation

    Args:
        wires (list[int]) : Which wires does the operation act on?

    Returns:
        list[Operation] : Which operations correspond to a cnot gate on MonarQ
    """
    return _custom_h(wires[1]) + [qml.CZ(wires)] + _custom_h(wires[1])


def _custom_cy(wires):
    """
    a MonarQ native implementation of the CY operation

    Args:
        wires (list[int]) : Which wires does the operation act on?

    Returns:
        list[Operation] : Which operations correspond to a cy gate on MonarQ
    """
    return (
        [custom.Y90(wires[1])]
        + _custom_cnot(wires)
        + [custom.YM90(wires[1])]
        + _custom_cnot(wires)
        + _custom_s(wires[0])
    )


def _custom_rz(angle: float, wires, epsilon=1e-8):
    """
    a MonarQ native implementation of the RZ operation

    Args:
        angle : float : What angle should we emulate?
        wires (list[int]) : Which wires does the operation act on?
        epsilon : up to what precision should the angle be emulated?

    Returns:
        list[Operation] : Which operations correspond to a rz gate on MonarQ
    """
    while angle < 0:
        angle += np.pi * 2
    angle %= np.pi * 2
    if is_close_enough_to(angle, 0):
        return []
    elif is_close_enough_to(angle, 7 * np.pi / 4):
        return [custom.TDagger(wires=wires)]
    elif is_close_enough_to(angle, 3 * np.pi / 2):
        return [custom.ZM90(wires=wires)]
    elif is_close_enough_to(angle, np.pi):
        return [qml.PauliZ(wires=wires)]
    elif is_close_enough_to(angle, np.pi / 2):
        return [custom.Z90(wires=wires)]
    elif is_close_enough_to(angle, np.pi / 4):
        return [qml.T(wires=wires)]
    else:
        return [qml.RZ(angle, wires)]


def _custom_rx(angle: float, wires, epsilon=1e-8):
    """
    a MonarQ native implementation of the RX operation

    Args:
        angle : float : What angle should we emulate?
        wires (list[int]) : Which wires does the operation act on?
        epsilon : up to what precision should the angle be emulated?

    Returns:
        list[Operation] : Which operations correspond to a rx gate on MonarQ
    """
    while angle < 0:
        angle += np.pi * 2
    angle %= np.pi * 2

    if is_close_enough_to(angle, 0):
        return []
    elif is_close_enough_to(angle, np.pi / 2):
        return [custom.X90(wires=wires)]
    elif is_close_enough_to(angle, 3 * np.pi / 2):
        return [custom.XM90(wires=wires)]
    elif is_close_enough_to(angle, np.pi):
        return [qml.PauliX(wires=wires)]
    else:
        return _custom_h(wires) + [qml.RZ(angle, wires)] + _custom_h(wires)


def _custom_ry(angle: float, wires, epsilon=1e-8):
    """
    a MonarQ native implementation of the RY operation

    Args:
        angle : float : What angle should we emulate?
        wires (list[int]) : Which wires does the operation act on?
        epsilon : up to what precision should the angle be emulated?

    Returns:
        list[Operation] : Which operations correspond to an ry gate on MonarQ
    """
    while angle < 0:
        angle += np.pi * 2
    angle %= np.pi * 2

    if is_close_enough_to(angle, 0):
        return []
    elif is_close_enough_to(angle, np.pi / 2):
        return [custom.Y90(wires=wires)]
    elif is_close_enough_to(angle, 3 * np.pi / 2):
        return [custom.YM90(wires=wires)]
    elif is_close_enough_to(angle, np.pi):
        return [qml.PauliY(wires=wires)]
    else:
        return _custom_sx(wires) + [qml.RZ(angle, wires=wires)] + _custom_sxdag(wires)


def _custom_swap(wires):
    """
    a MonarQ native implementation of the SWAP operation

    Args:
        wires (list[int]) : Which wires does the operation act on?

    Returns:
        list[Operation] : Which operations correspond to a swap gate on MonarQ
    """
    return (
        _custom_cnot([wires[0], wires[1]])
        + _custom_cnot([wires[1], wires[0]])
        + _custom_cnot([wires[0], wires[1]])
    )
