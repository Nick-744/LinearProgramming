# animation_2D.py

from __future__ import annotations

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from typing import List, Tuple
import numpy as np
import math
import os

from scenario import sample_scenario
from lp_solver import solve

base_dir = os.path.dirname(__file__)

class DroneAnimator:
    ''' Ανεξάρτητη κλάση για την οπτικοποίηση της παράδοσης με δρόνους. '''

    def __init__(self, map_path: str, dt: float = 0.02) -> None:
        (self.drones, self.depots, self.destinations) = sample_scenario()
        self.assignments = solve(self.drones, self.depots, self.destinations)

        self.map_path = map_path

        # Δημιουργία διαδρομών για τους δρόνους
        self.dt = dt
        self.trajectories = {}
        self._build_trajectories()
        self.max_frames = max(t.n_frames for t in self.trajectories.values())

        # Matplotlib set-up
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_title('Prototype Drone-Delivery Animation')
        self._setup_static_artists()
        self.scat_drones = self.ax.scatter(
            [], [], c = 'grey', edgecolors = 'k', s = 120, zorder = 3
        )
        self.text_time = self.ax.text(
            0.98, 0.95, '', transform = self.ax.transAxes, fontsize = 9,
            ha = 'right', va = 'top'
        )

        # Καταγραφή των προορισμών που έχουν ικανοποιηθεί (χρωματίζονται πράσινοι)
        self._dest_satisfied: List[bool] = [False] * len(self.destinations)

        return;

    def __str__(self) -> str:
        temp_string = ''
        for a in self.assignments:
            dest_name    = self.destinations[a.dest_id].name
            cargo        = a.supply.to_dict()
            temp_string += (
                f'Δρόνος {a.drone_id} -> {dest_name:<10} | Απόσταση: {a.distance:5.1f}'
                f"| Φορτίο: {cargo['food']:>3} τρόφιμα, {cargo['water']:>3} νερό, "
                f"{cargo['medicine']:>3} φάρμακα\n"
            )

        return temp_string;

    def _build_trajectories(self) -> None:
        depot_by_id = {d.id: d for d in self.depots}
        dest_by_id  = {d.id: d for d in self.destinations}
        idle_repeat = 100

        assignments_by_drone = {}
        for a in self.assignments:
            assignments_by_drone.setdefault(a.drone_id, []).append(a)

        for drone in self.drones:
            assigns = assignments_by_drone.get(drone.id, [])
            if not assigns:
                self.trajectories[drone.id] = _Trajectory(
                    [(drone.x, drone.y)] * idle_repeat, []
                )
                continue;

            pos         = (drone.x, drone.y)
            frames      = []
            dest_frames = []

            for a in assigns:
                depot = depot_by_id[a.depot_id]
                dest  = dest_by_id[a.dest_id]

                # Αρχική θέση του δρόνου -> Σημείο εφοδιασμού
                frames += _interpolate(pos, (depot.x, depot.y), drone.speed, self.dt)
                pos     = (depot.x, depot.y)

                # Σημείο εφοδιασμού -> Σημείο ανάγκης
                seg        = _interpolate(pos, (dest.x, dest.y), drone.speed, self.dt)
                dest_frame = len(frames) + len(seg) - 1
                dest_frames.append((a.dest_id, dest_frame))
                frames += seg
                pos     = (dest.x, dest.y)

                # Σημείο ανάγκης -> Σημείο εφοδιασμού
                frames += _interpolate(pos, (depot.x, depot.y), drone.speed, self.dt)
                pos     = (depot.x, depot.y)

            frames.append(pos)
            self.trajectories[drone.id] = _Trajectory(frames, dest_frames)
        
        return;

    def _setup_static_artists(self) -> None:
        ''' Ζωγραφική των στατικών στοιχείων της σκηνής. '''
        
        # Ρυθμίσεις για τους άξονες
        xs     = [d.x for d in self.depots + self.destinations]
        ys     = [d.y for d in self.depots + self.destinations]
        margin = 10
        self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
        self.ax.set_ylim(min(ys) - margin, max(ys) + margin)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.grid(alpha = 0.3)

        # Depots
        self.ax.scatter(
            [d.x for d in self.depots], [d.y for d in self.depots],
            marker = 's', s = 150, c = 'tab:blue',
            edgecolors = 'k', label = 'Depots'
        )

        # Destinations X [αρχικά όλα κόκκινα]
        dest_colors_init = ['red'] * len(self.destinations)
        self._dest_scatter = self.ax.scatter(
            [d.x for d in self.destinations],
            [d.y for d in self.destinations],
            marker = 'X', s = 120, c = dest_colors_init,
            edgecolors = 'k', label = 'Destinations'
        )
        self.ax.legend(loc = 'upper left')

        # Βάλε τον χάρτη πόλης ως φόντο
        bg_img = plt.imread(self.map_path)
        self.ax.imshow(
            bg_img,
            extent = [
                min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin
            ],
            origin = 'upper',
            zorder = 0 # Βάλε το χάρτη πίσω από όλα τα άλλα στοιχεία!
        )

        return;

    # Animation callbacks
    def _init_anim(self) -> Tuple:
        self.scat_drones.set_offsets(np.empty((0, 2)))
        self.text_time.set_text('')

        return (self.scat_drones, self.text_time, self._dest_scatter);

    def _update_anim(self, frame: int) -> Tuple:
        ''' Ενημέρωση της οπτικοποίησης για το τρέχον frame. '''
        # Οι θέσεις των δρόνων
        positions = [self.trajectories[d.id].pos_at(frame) for d in self.drones]
        self.scat_drones.set_offsets(positions)

        # Destination χρώματα
        dest_colors = self._dest_scatter.get_facecolors()
        n_dest      = len(self.destinations)
        if dest_colors.shape[0] < n_dest: # Happens when matplotlib collapsed colours!
            dest_colors = np.tile(dest_colors, (n_dest, 1))
        for dest_idx, dest in enumerate(self.destinations):
            assign = next((a for a in self.assignments if a.dest_id == dest.id), None)
            if assign is None:
                continue;
            traj = self.trajectories[assign.drone_id]
            for dest_id, f in traj.dest_frames:
                dest_idx = dest_id
                if frame >= f and not self._dest_satisfied[dest_idx]:
                    dest_colors[dest_idx, :3] = (0.0, 0.6, 0.0)
                    self._dest_satisfied[dest_idx] = True

        self._dest_scatter.set_facecolors(dest_colors)

        # Clock - Frame
        self.text_time.set_text(f'Frame: {frame}/{self.max_frames - 1}')

        return (self.scat_drones, self.text_time, self._dest_scatter);

    def run(self) -> FuncAnimation:
        ''' Η βασική μέθοδος για την εκτέλεση της οπτικοποίησης. '''
        anim = FuncAnimation(
            self.fig, self._update_anim, frames = self.max_frames,
            init_func = self._init_anim, interval = 50, blit = True, repeat = False
        )
        plt.show()

        return anim;

# --- Helpers ---
class _Trajectory:
    ''' Βοηθητική κλάση για την αποθήκευση της/των διαδρομής/ών ενός δρόνου. '''

    def __init__(self,
                 positions:   List[Tuple[float, float]],
                 dest_frames: List[Tuple[int, int]]) -> None:
        self.positions   = positions
        self.dest_frames = dest_frames # Λίστα από (dest_id, arrival_frame)

        return;

    @property
    def n_frames(self) -> int:
        return len(self.positions);

    def pos_at(self, frame: int) -> Tuple[float, float]:
        idx = min(frame, self.n_frames - 1)

        return self.positions[idx];

def _interpolate(
    p0: Tuple[float, float], p1: Tuple[float, float], speed: float, dt: float
) -> List[Tuple[float, float]]:
    ''' Evenly spaced points από το p0 στο p1 με δεδομένο speed ανά dt. '''
    vec  = np.asarray(p1) - np.asarray(p0)
    dist = float(np.hypot(*vec))
    if dist == 0:
        return [];

    n_steps   = max(1, math.ceil(dist / (speed * dt)))
    direction = vec / dist

    return [
        tuple(np.asarray(p0) + direction * speed * dt * i) for i in range(1, n_steps + 1)
    ];

def main():
    temp = DroneAnimator(
        map_path = os.path.join(base_dir, 'maps', 'map_background.png')
    )
    print('\n-> Λύση σεναρίου:')
    print(temp)
    temp.run()

    return;

if __name__ == '__main__':
    main()
