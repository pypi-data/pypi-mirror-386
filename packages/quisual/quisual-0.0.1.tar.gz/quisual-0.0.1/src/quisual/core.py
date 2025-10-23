# src/qflow/core.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

# Type alias for readability
Array = np.ndarray


# ---------------------------------------------------------------------
# Gate: a fixed unitary acting on one or more target qubits
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class Gate:
    """A unitary operation acting on one or more target qubits."""

    name: str
    matrix: Array  # shape (2**k, 2**k)
    targets: tuple[int, ...]  # qubit indices (little-endian convention)

    def __post_init__(self):
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError("Gate matrix must be square")


# ---------------------------------------------------------------------
# State: an n-qubit state vector
# ---------------------------------------------------------------------
@dataclass
class State:
    """Represents the full state vector for an n-qubit system."""

    n_qubits: int
    vector: Array  # shape (2**n,)

    @staticmethod
    def zero(n_qubits: int) -> "State":
        """Return the |00...0> state."""
        v = np.zeros(2**n_qubits, dtype=np.complex128)
        v[0] = 1.0
        return State(n_qubits, v)

    def normalize(self) -> None:
        """Normalize the state vector to unit length."""
        norm = np.linalg.norm(self.vector)
        if norm == 0:
            raise ValueError("Zero vector cannot be normalized")
        self.vector /= norm


# ---------------------------------------------------------------------
# Circuit: holds a sequence of gates and can apply them
# ---------------------------------------------------------------------
class Circuit:
    """A linear sequence of gates acting on a fixed number of qubits."""

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self._gates: list[Gate] = []

    def add(self, gate: Gate) -> "Circuit":
        """Append a gate and return self for chaining."""
        self._gates.append(gate)
        return self

    def apply(self, state: State) -> State:
        """Return a new State after applying all gates to the input."""
        v = state.vector.copy()
        for g in self._gates:
            v = apply_gate(v, self.n_qubits, g)
        return State(self.n_qubits, v)


# ---------------------------------------------------------------------
# Utility: lift a k-qubit gate to an n-qubit operator and apply it
# ---------------------------------------------------------------------
def apply_gate(state: Array, n_qubits: int, gate: Gate) -> Array:
    """Return the new state after applying `gate` to `state`."""
    op = _lift(gate.matrix, gate.targets, n_qubits)
    return op @ state


def _lift(mat: Array, targets: tuple[int, ...], n_qubits: int) -> Array:
    """Lift a k-qubit matrix to an n-qubit operator (v0: contiguous targets only)."""
    k = len(targets)
    if 2**k != mat.shape[0]:
        raise ValueError("Matrix rank and target count mismatch")

    # Start with identity ops for all qubits
    ops = []
    for i in range(n_qubits):
        if i in targets:
            ops.append(None)  # placeholder
        else:
            ops.append(np.eye(2, dtype=np.complex128))

    # Require contiguous target indices for simplicity
    if sorted(targets) != list(range(min(targets), min(targets) + k)):
        raise NotImplementedError("v0: targets must be contiguous; e.g., (0,) or (1,2)")

    start = min(targets)
    ops[start] = mat
    # Remove placeholders after start
    for i in range(start + 1, start + k):
        ops[i] = None

    # Build Kronecker product in little-endian order (highest index first)
    result = None
    for i in reversed(range(n_qubits)):
        op = ops[i]
        if op is None:
            continue
        result = op if result is None else np.kron(op, result)
    return result
