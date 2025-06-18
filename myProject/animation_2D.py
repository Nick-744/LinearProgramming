# animation_2D_PROTOTYPE.py

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from scenario import sample_scenario
from lp_solver import solve
from models import Destination, Drone, Assignment

class DroneAnimator:
    """Lightweight, self-contained visualisation for the prototype model."""

    def __init__(self, dt: float = 0.1):
        # Scenario
        (self.drones, self.depots, self.destinations) = sample_scenario()

        self.assignments = solve(self.drones, self.depots, self.destinations)

        # Build trajectories -------------------------------------------------------
        # Δημιουργία διαδρομών/
        self.dt = dt
        self.trajectories = {}
        self._build_trajectories()
        self.max_frames = max(t.n_frames for t in self.trajectories.values())

        # Matplotlib set-up --------------------------------------------------------
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_title("Prototype Drone-Delivery Animation")
        self._setup_static_artists()
        self.scat_drones = self.ax.scatter([], [], c="grey", edgecolors="k", s=120, zorder=3)
        self.text_time = self.ax.text(0.98, 0.95, "", transform=self.ax.transAxes,
                                      fontsize=9, ha="right", va="top")

        # Track which destinations have turned green
        self._dest_satisfied: List[bool] = [False] * len(self.destinations)

    # ---------------------------------------------------------------------
    # Trajectory construction
    # ---------------------------------------------------------------------
    def _build_trajectories(self) -> None:
        depot_by_id = {d.id: d for d in self.depots}
        dest_by_id = {d.id: d for d in self.destinations}
        idle_repeat = 100  # frames for idle drones

        for drone in self.drones:
            # Find assignment, if any
            assign = next((a for a in self.assignments if a.drone_id == drone.id), None)
            if assign is None:
                self.trajectories[drone.id] = _Trajectory([(drone.x, drone.y)] * idle_repeat, None)
                continue

            depot = depot_by_id[assign.depot_id]
            dest = dest_by_id[assign.dest_id]

            waypoints = [
                (drone.x, drone.y),      # home
                (depot.x, depot.y),      # pick-up
                (dest.x, dest.y),        # delivery
                (depot.x, depot.y),      # return
            ]

            frames: List[Tuple[float, float]] = []
            dest_frame: int | None = None
            for idx, (p0, p1) in enumerate(zip(waypoints, waypoints[1:])):
                segment = _interpolate(p0, p1, drone.speed, self.dt)
                if idx == 1:  # arrival into destination is after segment 1
                    dest_frame = len(frames) + len(segment) - 1
                frames.extend(segment)
            frames.append(waypoints[-1])
            self.trajectories[drone.id] = _Trajectory(frames, dest_frame)

    # ---------------------------------------------------------------------
    # Static plot elements
    # ---------------------------------------------------------------------
    def _setup_static_artists(self):
        # Axis limits -----------------------------------------------------------
        xs = [d.x for d in self.depots + self.destinations]
        ys = [d.y for d in self.depots + self.destinations]
        margin = 10
        self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
        self.ax.set_ylim(min(ys) - margin, max(ys) + margin)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(alpha=0.3)

        # Depots ----------------------------------------------------------------
        self.ax.scatter([d.x for d in self.depots], [d.y for d in self.depots],
                        marker="s", s=150, c="tab:blue", edgecolors="k", label="Depots")

        # Destinations (all red to start) ---------------------------------------
        dest_colors_init = ["red"] * len(self.destinations)
        self._dest_scatter = self.ax.scatter([d.x for d in self.destinations],
                                             [d.y for d in self.destinations],
                                             marker="X", s=120, c=dest_colors_init,
                                             edgecolors="k", label="Destinations")
        self.ax.legend(loc="upper left")

    # ---------------------------------------------------------------------
    # Animation callbacks
    # ---------------------------------------------------------------------
    def _init_anim(self):
        self.scat_drones.set_offsets(np.empty((0, 2)))
        self.text_time.set_text("")
        return self.scat_drones, self.text_time, self._dest_scatter

    def _update_anim(self, frame: int):
        # Drone positions -------------------------------------------------------
        positions = [self.trajectories[d.id].pos_at(frame) for d in self.drones]
        self.scat_drones.set_offsets(positions)

        # Destination-colour updates -------------------------------------------
        dest_colors = self._dest_scatter.get_facecolors()
        n_dest = len(self.destinations)
        if dest_colors.shape[0] < n_dest:  # Happens when matplotlib collapsed colours
            dest_colors = np.tile(dest_colors, (n_dest, 1))
        for dest_idx, dest in enumerate(self.destinations):
            assign = next((a for a in self.assignments if a.dest_id == dest.id), None)
            if assign is None:
                continue
            traj = self.trajectories[assign.drone_id]
            if traj.dest_frame is not None and frame >= traj.dest_frame and not self._dest_satisfied[dest_idx]:
                dest_colors[dest_idx, :3] = (0.0, 0.6, 0.0)  # turn green
                self._dest_satisfied[dest_idx] = True
        self._dest_scatter.set_facecolors(dest_colors)

        # Clock -----------------------------------------------------------------
        self.text_time.set_text(f"Frame: {frame}/{self.max_frames - 1}")
        return self.scat_drones, self.text_time, self._dest_scatter

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def run(self):
        anim = FuncAnimation(self.fig, self._update_anim, frames=self.max_frames,
                             init_func=self._init_anim, interval=50, blit=True, repeat=False)
        plt.show()
        return anim

# --- Helpers ---
class _Trajectory:
    """A fully expanded per-frame path for a single drone."""

    def __init__(self, positions: List[Tuple[float, float]], dest_frame: int | None):
        self.positions = positions
        self.dest_frame = dest_frame            # arrival frame at destination

    @property
    def n_frames(self) -> int:
        return len(self.positions)

    def pos_at(self, frame: int) -> Tuple[float, float]:
        idx = min(frame, self.n_frames - 1)
        return self.positions[idx]


def _interpolate(p0: Tuple[float, float], p1: Tuple[float, float], speed: float, dt: float) -> List[Tuple[float, float]]:
    """Evenly spaced points from *p0* to *p1* given *speed* units per *dt*."""
    vec = np.asarray(p1) - np.asarray(p0)
    dist = float(np.hypot(*vec))
    if dist == 0:
        return []
    n_steps = max(1, math.ceil(dist / (speed * dt)))
    direction = vec / dist
    return [tuple(np.asarray(p0) + direction * speed * dt * i) for i in range(1, n_steps + 1)]

if __name__ == "__main__":
    DroneAnimator().run()
