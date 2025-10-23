# src/qflow/animate.py
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from .core import Circuit, State, apply_gate


def animate(
    state: State,
    circuit: Circuit,
    interval_ms: int = 600,
    frames_per_gate: int = 1,
):
    """
    Animate how the state vector's probabilities evolve through the circuit.

    Args:
        state: initial State object.
        circuit: Circuit containing gates to apply.
        interval_ms: time between animation frames (in milliseconds).
        frames_per_gate: if >1, interpolate between pre/post gate states for smoothness.

    Returns:
        The Matplotlib FuncAnimation object (so user can save() if desired).
    """
    n = state.n_qubits

    # Create labels for each computational basis state (little-endian convention)
    labels = [format(i, f"0{n}b")[::-1] for i in range(2**n)]

    # Precompute all intermediate states
    states = [state.vector.copy()]
    v = state.vector.copy()

    for g in circuit._gates:
        before = v.copy()
        after = apply_gate(v, n, g)
        # Optionally interpolate amplitudes for smoother visuals (not physically accurate)
        if frames_per_gate > 1:
            for t in range(1, frames_per_gate):
                alpha = t / frames_per_gate
                interp = (1 - alpha) * before + alpha * after
                states.append(interp)
        states.append(after)
        v = after

    # Convert all to probabilities (magnitudes squared)
    probs = [np.abs(s)**2 for s in states]

    # --- Create the figure ---
    fig, ax = plt.subplots()
    bars = ax.bar(range(2**n), probs[0])

    ax.set_ylim(0, 1)
    ax.set_xlim(-0.5, 2**n - 0.5)
    ax.set_xticks(range(2**n), labels)
    ax.set_ylabel("Probability")
    ax.set_xlabel("Basis state (little-endian)")
    ax.set_title("qflow: State evolution")

    # --- Frame update function ---
    def update(frame):
        p = probs[frame]
        for rect, h in zip(bars, p):
            rect.set_height(float(h))
        return bars

    # --- Run the animation ---
    anim = FuncAnimation(
        fig,
        update,
        frames=len(probs),
        interval=interval_ms,
        blit=False,
    )

    plt.show()
    return anim
