# src/qflow/gates.py
from __future__ import annotations
import numpy as np
from .core import Gate

# ---------------------------------------------------------------------
# Single-qubit standard gates (2x2 matrices)
# ---------------------------------------------------------------------
I = np.eye(2, dtype=np.complex128)

X = np.array([[0, 1],
              [1, 0]], dtype=np.complex128)

Y = np.array([[0, -1j],
              [1j, 0]], dtype=np.complex128)

Z = np.array([[1, 0],
              [0, -1]], dtype=np.complex128)

H = (1 / np.sqrt(2)) * np.array([[1,  1],
                                 [1, -1]], dtype=np.complex128)

S = np.array([[1, 0],
              [0, 1j]], dtype=np.complex128)

T = np.array([[1, 0],
              [0, np.exp(1j * np.pi / 4)]], dtype=np.complex128)


# ---------------------------------------------------------------------
# Parametric rotation gates
# ---------------------------------------------------------------------
def Rx(theta: float) -> np.ndarray:
    """Rotation around X-axis by angle theta."""
    c, s = np.cos(theta / 2), -1j * np.sin(theta / 2)
    return np.array([[c, s],
                     [s, c]], dtype=np.complex128)


def Ry(theta: float) -> np.ndarray:
    """Rotation around Y-axis by angle theta."""
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -s],
                     [s,  c]], dtype=np.complex128)


def Rz(theta: float) -> np.ndarray:
    """Rotation around Z-axis by angle theta."""
    return np.array([[np.exp(-1j * theta / 2), 0],
                     [0, np.exp(1j * theta / 2)]], dtype=np.complex128)


# ---------------------------------------------------------------------
# Gate constructors
# ---------------------------------------------------------------------
def gate(name: str, mat: np.ndarray, *targets: int) -> Gate:
    """Convenience factory: create a Gate with name, matrix, and targets."""
    return Gate(name=name, matrix=mat, targets=tuple(targets))


# ---------------------------------------------------------------------
# Two-qubit gate: CNOT (control 0, target 1 for contiguous targets)
# ---------------------------------------------------------------------
CNOT = np.array([[1, 0, 0, 0],
                 [0, 1, 0, 0],
                 [0, 0, 0, 1],
                 [0, 0, 1, 0]], dtype=np.complex128)
