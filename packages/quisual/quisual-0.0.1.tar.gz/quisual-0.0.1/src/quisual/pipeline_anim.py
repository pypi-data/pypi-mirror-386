# src/quisual/pipeline_anim.py
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

from .core import Circuit, State, apply_gate

''' 
TODO: Stop the clipping problem with the final vector
TODO: Improve stylisation
TODO: Create looping animation
TODO: Implement 2D
TODO: Fix matrix stylisation (try to get latex to work, if not, make the custom implementation prettier)
'''
def animate_pipeline(
    state: State,
    circuit: Circuit,
    interval_ms: int = 600,
    frames_per_gate: int = 25,
    speed_multiplier: float = 1.6,
):
    """
    Animate a single-qubit signal tracing through a wire of quantum gates.
    The wire glows progressively; each gate lights up and stays glowing once reached.
    """
    n = state.n_qubits
    assert n == 1, "Pipeline animation currently supports 1 qubit only."

    # --- Layout parameters ---
    gate_names = [g.name for g in circuit._gates]
    n_gates = len(gate_names)
    spacing = 2.0
    gate_size = 1.0
    wire_y = 0.0

    x_gate_centers = [i * spacing for i in range(n_gates)]
    if x_gate_centers:
        first_center = x_gate_centers[0]
        last_center = x_gate_centers[-1]
    else:
        first_center = 0.0
        last_center = 0.0

    x_start = first_center - spacing / 2
    x_end = last_center + spacing / 2

    # --- Figure setup ---
    fig, ax = plt.subplots()
    margin = gate_size + 1.5
    ax.set_xlim(x_start - margin, x_end + margin)
    ax.set_ylim(-2, 2)
    ax.axis("off")
    fig.patch.set_facecolor("#0D0A10")
    ax.set_facecolor("#0D0A10")

    # Match figure aspect ratio to data extent so gate boxes stay square.
    x_span = ax.get_xlim()[1] - ax.get_xlim()[0]
    y_span = ax.get_ylim()[1] - ax.get_ylim()[0]
    base_height = 3.0
    fig.set_size_inches(base_height * (x_span / y_span), base_height)
    ax.set_aspect("equal", adjustable="box")

    # --- Base (dim) wire ---
    base_wire = Line2D(
        [x_start, x_end], [wire_y, wire_y],
        color="#3A2A44", lw=3, alpha=0.6, zorder=0
    )
    ax.add_line(base_wire)

    # --- Glowing tracer wire (extends over time) ---
    tracer_wire, = ax.plot(
        [x_start, x_start],
        [wire_y, wire_y],
        color="#FF9E5E", lw=3.5, alpha=0.9, zorder=1
    )

    # --- Gates ---
    gate_boxes, gate_texts = [], []
    base_color = "#241B2F"
    glow_color = "#FF9E5E"

    for i, name in enumerate(gate_names):
        x = i * spacing
        rect = FancyBboxPatch(
            (x - gate_size / 2, wire_y - gate_size / 2),
            gate_size, gate_size,
            boxstyle="round,pad=0.05,rounding_size=0.2",
            ec=glow_color, fc=base_color,
            lw=1, zorder=2
        )
        ax.add_patch(rect)
        txt = ax.text(
            x, wire_y, name,
            color=glow_color, fontsize=20,
            ha="center", va="center", weight="bold"
        )
        gate_boxes.append(rect)
        gate_texts.append(txt)

    # --- Precompute states (optional for later) ---
    states = [state.vector.copy()]
    v = state.vector.copy()
    for g in circuit._gates:
        v = apply_gate(v, n, g)
        states.append(v)

    def _clean_float(value: float, places: int = 2) -> float:
        rounded = float(np.round(value, places))
        if np.isclose(rounded, 0.0, atol=10 ** (-places)):
            return 0.0
        return rounded

    def _complex_to_tex(z: complex) -> str:
        real = _clean_float(z.real)
        imag = _clean_float(z.imag)
        if imag == 0.0:
            return f"{real:.2f}"
        if real == 0.0:
            sign = "-" if imag < 0 else ""
            return f"{sign}{abs(imag):.2f}\\,i"
        sign = "+" if imag > 0 else "-"
        return f"{real:.2f}{sign}{abs(imag):.2f}\\,i"

    def _create_vector_label(ax, center_x: float, center_y: float, vec: np.ndarray, color: str):
        entry_spacing = 0.7
        n_entries = len(vec)
        offsets = []
        top_offset = 0.5 * entry_spacing * (n_entries - 1)
        for idx in range(n_entries):
            offsets.append(top_offset - idx * entry_spacing)

        max_chars = max(len(_complex_to_tex(v)) for v in vec) if vec.size else 1
        width = max(1.8, 0.45 * max_chars)
        height = max(entry_spacing * (n_entries - 1) + 0.9, 1.25)
        bracket_depth = 0.35

        texts = []
        for offset, value in zip(offsets, vec):
            txt = ax.text(
                center_x,
                center_y + offset,
                f"${_complex_to_tex(value)}$",
                color=color,
                fontsize=16,
                ha="center",
                va="center",
                zorder=3,
            )
            texts.append(txt)

        # Bracket segments: left vertical, left top, left bottom, right vertical, right top, right bottom
        brackets = []
        for _ in range(6):
            line = Line2D([], [], color=color, lw=2, zorder=2.5)
            ax.add_line(line)
            brackets.append(line)

        return {
            "texts": texts,
            "offsets": offsets,
            "width": width,
            "height": height,
            "brackets": brackets,
            "bracket_depth": bracket_depth,
        }

    def _set_vector_position(vector_artist, center_x: float, center_y: float) -> None:
        half_width = vector_artist["width"] / 2
        half_height = vector_artist["height"] / 2
        depth = vector_artist["bracket_depth"]
        left_x = center_x - half_width
        right_x = center_x + half_width
        top_y = center_y + half_height
        bottom_y = center_y - half_height

        for txt, offset in zip(vector_artist["texts"], vector_artist["offsets"]):
            txt.set_position((center_x, center_y + offset))

        brackets = vector_artist["brackets"]
        brackets[0].set_data([left_x, left_x], [bottom_y, top_y])
        brackets[1].set_data([left_x, left_x + depth], [top_y, top_y])
        brackets[2].set_data([left_x, left_x + depth], [bottom_y, bottom_y])
        brackets[3].set_data([right_x, right_x], [bottom_y, top_y])
        brackets[4].set_data([right_x - depth, right_x], [top_y, top_y])
        brackets[5].set_data([right_x - depth, right_x], [bottom_y, bottom_y])

    def _set_vector_alpha(vector_artist, alpha: float) -> None:
        for line in vector_artist["brackets"]:
            line.set_alpha(alpha)
        for txt in vector_artist["texts"]:
            txt.set_alpha(alpha)

    entry_travel = spacing * 0.9
    exit_travel = spacing * 0.9 if n_gates else spacing
    input_start_x = x_start - entry_travel
    input_end_x = x_start - gate_size / 2 - 0.25
    output_start_x = x_end + gate_size / 2 + 0.25
    output_end_x = x_end + exit_travel

    input_vector = _create_vector_label(
        ax,
        input_start_x,
        wire_y,
        states[0],
        glow_color,
    )
    _set_vector_position(input_vector, input_start_x, wire_y)
    _set_vector_alpha(input_vector, 1.0)

    output_vector = _create_vector_label(
        ax,
        output_start_x,
        wire_y,
        states[-1],
        glow_color,
    )
    _set_vector_position(output_vector, output_start_x, wire_y)
    _set_vector_alpha(output_vector, 0.0)

    vector_artists = (
        input_vector["texts"]
        + output_vector["texts"]
        + input_vector["brackets"]
        + output_vector["brackets"]
    )

    # --- Animation logic ---
    total_frames = max(1, n_gates * frames_per_gate)
    segment_length = x_end - x_start

    def ease_in_out_slow_fast_slow(t: float) -> float:
        """Smoothly ramp up, then down; keeps start/end slow."""
        return t * t * (3 - 2 * t)

    def update(frame):
        # progress from 0 → 1
        t = frame / total_frames
        p = ease_in_out_slow_fast_slow(t)
        tracer_length = segment_length * p
        x_current = x_start + tracer_length
        tracer_wire.set_data([x_start, x_current], [wire_y, wire_y])

        # Highlight gates once tracer passes them
        for i, x in enumerate(x_gate_centers):
            if x_current >= x - gate_size / 2:
                # Already reached → fully bright
                intensity = 1.0
            else:
                # Not reached yet → dim
                intensity = 0.3
            color_val = np.array([1.0, 0.62, 0.37]) * intensity
            hex_color = '#%02x%02x%02x' % tuple((color_val * 255).astype(int))
            gate_boxes[i].set_edgecolor(hex_color)
            gate_texts[i].set_color(hex_color)

            # Gentle size pulse as the tracer passes by
            dist = x_current - x
            pulse = 1.0 + 0.1 * np.exp(- (dist / 0.35) ** 2)
            new_size = gate_size * pulse
            gate_boxes[i].set_bounds(
                x - new_size / 2,
                wire_y - new_size / 2,
                new_size,
                new_size,
            )

        if segment_length > 0:
            entry_divisor = entry_travel if entry_travel > 0 else 1.0
            entry_progress = np.clip(tracer_length / entry_divisor, 0.0, 1.0)
            input_x = input_start_x + (input_end_x - input_start_x) * entry_progress
            _set_vector_position(input_vector, min(input_x, input_end_x), wire_y)
            _set_vector_alpha(input_vector, max(0.0, 1.0 - entry_progress * 1.4))

            exit_divisor = exit_travel if exit_travel > 0 else 1.0
            exit_fraction = (tracer_length - (segment_length - exit_travel)) / exit_divisor
            exit_progress = np.clip(exit_fraction, 0.0, 1.0)
            output_x = output_start_x + (output_end_x - output_start_x) * exit_progress
            _set_vector_position(output_vector, output_x, wire_y)
            _set_vector_alpha(output_vector, exit_progress)
        else:
            _set_vector_position(input_vector, input_end_x, wire_y)
            _set_vector_alpha(input_vector, 1.0)
            _set_vector_position(output_vector, output_start_x, wire_y)
            _set_vector_alpha(output_vector, 0.0)

        return [tracer_wire] + gate_boxes + gate_texts + vector_artists

    # Higher speed_multiplier shortens the per-frame interval -> faster traversal.
    interval_per_frame = (interval_ms / max(frames_per_gate, 1)) / max(speed_multiplier, 1e-6)

    anim = FuncAnimation(
        fig,
        update,
        frames=total_frames + 1,
        interval=interval_per_frame,
        blit=False,
        repeat=False,
    )

    plt.show()
    return anim
