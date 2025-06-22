# animation_2D.py

from __future__ import annotations

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from typing import List, Tuple
from time import time
import numpy as np
import math
import os

from models import Drone, Depot, Destination, Supply
from scenario import (
    big_city_scenario, silent_hill_scenario, raccoon_city_scenario
)
from lp_solver import solve

base_dir = os.path.dirname(__file__)

# --- Global μεταβλητές εμφάνισης ---
WINDOW_SIZE     = (14, 7)
LABELS_FONTSIZE = 10 # Μέγεθος γραμματοσειράς των labels στον χάρτη
TABLE_FONTSIZE  = 12 # Μέγεθος γραμματοσειράς των πινάκων πληροφοριών

class DroneAnimator:
    ''' Ανεξάρτητη κλάση για την οπτικοποίηση της παράδοσης
    με δρόνους [+ πληροφορίες/κατάσταση]. '''

    def __init__(self,
                 scenario:      tuple[list[Drone], list[Depot], list[Destination]],
                 map_path:      str   = None,
                 dt:            float = 0.01,
                 print_results: bool  = True) -> None:
        (self.drones, self.depots, self.destinations) = scenario
        
        start = time()
        self.assignments   = solve(self.drones, self.depots, self.destinations)
        self.solution_time = time() - start # Χρόνος επίλυσης
        
        if print_results:
            print(f'\n{self.__str__()}')
            self.print_satisfaction_rates()
        
        # Reset για το animation - Θα ανακτηθούν από την προσομοίωση
        for d in self.destinations:
            d.satisfied = Supply()
        
        self.map_path = map_path
        self.dt       = dt
        
        # Δημιουργία διαδρομών για τους δρόνους & προγραμματισμός γεγονότων
        self.trajectories = {}
        self.drone_cargo  = {d.id: Supply() for d in self.drones} # Φορτίο κάθε δρόνου
        self._events      = [] # Event schedule
        self._build_trajectories()
        self.max_frames = max(
            t.n_frames for t in self.trajectories.values()
        ) if self.trajectories else 1
        
        # Setup matplotlib
        self._setup_figure()
        self._setup_static_elements()
        self._setup_dynamic_elements()
        
        # Animation state
        self._dest_satisfied  = [False] * len(self.destinations) # Έλεγχος ολοκλήρωσης!
        self._animation_stats = {
            'total_deliveries':     len(self.assignments),
            'completed_deliveries': 0,
            'drones_in_flight':     0
        }

        return;

    def __str__(self) -> str:
        lines = ['-> Λύση σεναρίου:']
        
        if not self.assignments:
            lines.append('Δεν υπάρχουν αναθέσεις.')
            return '\n'.join(lines);
        
        # Ομαδοποίηση αναθέσεων ανά δρόνου -> καλύτερη οργάνωση
        drone_assignments = {}
        for a in self.assignments:
            drone_assignments.setdefault(a.drone_id, []).append(a)
        
        for (drone_id, assignments) in sorted(drone_assignments.items()):
            lines.append(f'\nΔρόνος {drone_id}:')
            total_distance = 0
            for a in assignments:
                dest_name = self.destinations[a.dest_id].name
                cargo     = a.supply.to_dict()
                lines.append(
                    f'  -> {dest_name:<12} | Απόσταση: {a.distance:5.1f} | '
                    f"Φορτίο: {cargo['food']:>2}F {cargo['water']:>2}W "
                    f"{cargo['medicine']:>2}M"
                )
                total_distance += a.distance
            lines.append(f'  Συνολική απόσταση: {total_distance:.1f}')
        
        lines.append(f'\nΧρόνος επίλυσης: {self.solution_time:.3f}s')

        return '\n'.join(lines);

    def print_satisfaction_rates(self) -> None:
        ''' Εκτύπωση ποσοστών κάλυψης προμηθειών ανά προορισμό. '''

        print('\nΠοσοστά κάλυψης προμηθειών ανά προορισμό:')
        total_satisfaction = 0
        for d in self.destinations:
            rate = d.sat_rate() * 100
            total_satisfaction += rate
            status = '✓' if rate >= 90 else '!' if rate >= 50 else '✗'
            print(f'  {status} {d.name:<12}: {rate:5.1f}%')
        
        avg_satisfaction = (
            total_satisfaction / len(self.destinations) if self.destinations else 0
        )
        print(f'\nΜέση κάλυψη: {avg_satisfaction:.1f}%')

        return;

    def _setup_figure(self) -> None:
        ''' Setup του matplotlib figure. '''
        self.fig = plt.figure(figsize = WINDOW_SIZE, constrained_layout = True)
        
        # Grid Layout - 3 γραμμές, 4 στήλες - Καλύτερη οργάνωση
        gs = self.fig.add_gridspec(3, 4, hspace = 0.3, wspace = 0.3)
        
        # Βασική περιοχή animation
        self.ax = self.fig.add_subplot(gs[:, 1:3])
        self.ax.set_title(
            'Drone Delivery Animation', fontsize = 14, fontweight = 'bold'
        )
        
        # Πίνακες πληροφοριών
        self.info_ax_left  = self.fig.add_subplot(gs[:, 0])
        self.info_ax_right = self.fig.add_subplot(gs[:, 3])
        
        # Απενεργοποίηση άξονων για τους πίνακες πληροφοριών
        for ax in [self.info_ax_left, self.info_ax_right]:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor('black')

        return;

    def _setup_static_elements(self) -> None:
        ''' Ζωγραφική των στατικών στοιχείων της σκηνής. '''
        # Δεν θέλουμε να έχουμε προβλήματα Out Of Bounds!
        all_x = [d.x for d in self.depots + self.destinations]
        all_y = [d.y for d in self.depots + self.destinations]
        
        if not all_x or not all_y:
            return;
        
        margin = max(10, (max(all_x) - min(all_x)) * 0.1)
        self.ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        self.ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
        self.ax.set_aspect('equal', adjustable = 'box')
        self.ax.grid(alpha = 0.3, linestyle = '--')
        
        # Βάλε τον χάρτη πόλης ως φόντο [εάν υπάρχει]
        if self.map_path and os.path.exists(self.map_path):
            try:
                bg_img = plt.imread(self.map_path)
                self.ax.imshow(
                    bg_img,
                    extent = [
                        min(all_x) - margin, max(all_x) + margin,
                        min(all_y) - margin, max(all_y) + margin
                    ],
                    origin = 'upper',
                    alpha  = 0.7,
                    zorder = 0 # Βάλε το χάρτη πίσω από όλα τα άλλα στοιχεία!
                )
            except Exception as e:
                print(f'Δεν ήταν δυνατή η φόρτωση του χάρτη: {e}');

        # Σημεία εφοδιασμού
        if self.depots:
            self.ax.scatter(
                [d.x for d in self.depots], [d.y for d in self.depots],
                marker = 's', s = 200, c = 'tab:cyan', edgecolors = 'navy',
                label = 'Depots', zorder = 2
            )
            # Προσθήκη ετικετών για τις αποθήκες
            for depot in self.depots:
                self.ax.annotate(
                    depot.name, (depot.x, depot.y), 
                    xytext = (5, 5), textcoords = 'offset points',
                    fontsize = LABELS_FONTSIZE, fontweight = 'bold', color = 'navy'
                )
        
        # Σημεία ανάγκης X [αρχικά όλα κόκκινα]
        if self.destinations:
            self._dest_scatter = self.ax.scatter(
                [d.x for d in self.destinations], [d.y for d in self.destinations],
                marker = 'X', s = 150, c = 'red', edgecolors = 'darkred',
                label = 'Destinations', zorder = 2
            )
            # Προσθήκη ετικετών για τα σημεία ανάγκης
            for dest in self.destinations:
                self.ax.annotate(
                    dest.name, (dest.x, dest.y),
                    xytext = (5, -15), textcoords = 'offset points',
                    fontsize = LABELS_FONTSIZE, fontweight = 'bold', color = 'darkred'
                )
        
        self.ax.legend(loc = 'upper left', framealpha = 0.9)

        return;

    def _setup_dynamic_elements(self) -> None:
        ''' Δημιουργία των δυναμικών στοιχείων της σκηνής. '''
        # Scatter plot [αναπαράσταση δρόνων]
        self.scat_drones = self.ax.scatter(
            [], [], c = 'magenta', edgecolors = 'purple', s = 150, 
            linewidths = 2, zorder = 4, label = 'Drones'
        )
        
        # Status display
        self.text_status = self.ax.text(
            0.98, 0.02, '', transform = self.ax.transAxes, fontsize = 10,
            ha = 'right', va = 'bottom', color = 'white',
            bbox = dict(boxstyle = 'round,pad=0.5', facecolor = 'black', alpha = 0.8)
        )
        
        # Setup πινάκων πληροφοριών
        self._setup_info_panels()

        return;

    def _setup_info_panels(self) -> None:
        # Αριστερός πίνακας - Πληροφορίες δρόνων & σημείων εφοδιασμού
        self.info_ax_left.set_title(
            'Drones & Depots', color = 'white',
            fontsize = TABLE_FONTSIZE + 4, pad = 20
        )
        self.left_text = self.info_ax_left.text(
            0.05, 0.95, '', transform = self.info_ax_left.transAxes,
            va = 'top', ha = 'left', fontsize = TABLE_FONTSIZE,
            color = 'white', family = 'monospace'
        )
        
        # Δεξιός πίνακας - Πληροφορίες σημείων ανάγκης
        self.info_ax_right.set_title(
            'Destinations', color = 'white',
            fontsize = TABLE_FONTSIZE + 4, pad = 20
        )
        self.right_text = self.info_ax_right.text(
            0.05, 0.95, '', transform = self.info_ax_right.transAxes,
            va = 'top', ha = 'left', fontsize = TABLE_FONTSIZE,
            color = 'white', family = 'monospace'
        )

        return;

    def _build_trajectories(self) -> None:
        ''' Δημιουργία διαδρομών για κάθε δρόνο με βάση τις αναθέσεις. '''
        depot_by_id = {d.id: d for d in self.depots}
        dest_by_id  = {d.id: d for d in self.destinations}
        
        # Ομαδοποίηση αναθέσεων ανά δρόνο
        assignments_by_drone = {}
        for a in self.assignments:
            assignments_by_drone.setdefault(a.drone_id, []).append(a)
        
        for drone in self.drones:
            assigns = assignments_by_drone.get(drone.id, [])
            
            if not assigns:
                # Δρόνος χωρίς αναθέσεις - idle state
                idle_frames = max(
                    100, self.max_frames
                ) if hasattr(self, 'max_frames') else 100
                self.trajectories[drone.id] = _Trajectory(
                    [(drone.x, drone.y)] * idle_frames, []
                )
                continue;
            
            pos         = (drone.x, drone.y)
            frames      = []
            dest_frames = []
            for assignment in assigns:
                depot = depot_by_id[assignment.depot_id]
                dest  = dest_by_id[assignment.dest_id]
                
                # Αρχική θέση του δρόνου -> Σημείο εφοδιασμού
                segment      = _interpolate(pos, (depot.x, depot.y), drone.speed, self.dt)
                pickup_frame = len(frames) + len(segment) - 1 if segment else len(frames)
                
                self._events.append(
                    (pickup_frame, 'pickup', drone.id, depot.id, assignment.supply)
                )
                frames.extend(segment)
                pos = (depot.x, depot.y)
                
                # Σημείο εφοδιασμού -> Σημείο ανάγκης
                segment    = _interpolate(pos, (dest.x, dest.y), drone.speed, self.dt)
                drop_frame = len(frames) + len(segment) - 1 if segment else len(frames)
                
                self._events.append(
                    (drop_frame, 'drop', drone.id, dest.id, assignment.supply)
                )
                dest_frames.append((assignment.dest_id, drop_frame))
                frames.extend(segment)
                pos = (dest.x, dest.y)
                
                # Σημείο ανάγκης -> Σημείο εφοδιασμού
                return_segment = _interpolate(pos, (depot.x, depot.y), drone.speed, self.dt)
                frames.extend(return_segment)
                pos = (depot.x, depot.y)
            
            if not frames: # Μην γίνει πατάτα αν δεν υπάρχουν frames!!!
                frames = [(drone.x, drone.y)]
            
            self.trajectories[drone.id] = _Trajectory(frames, dest_frames)

        return;

    def _format_supply_info(self, supply: Supply) -> str:
        ''' Μορφοποίηση πληροφοριών προμηθειών για καλύτερη αναγνωσιμότητα! '''
        s = supply.to_dict()

        return (
            f"{'F:':>3}{s['food']:>3} {'W:':>3}{s['water']:>3} {'M:':>3}{s['medicine']:>3}"
        );

    def _update_info_panels(self, frame: int | None = None) -> None:
        # Πίνακας αριστερά - Πληροφορίες δρόνων & σημείων εφοδιασμού
        left_info = []
        left_info.append('Drones')
        left_info.append('-' * 25)
        
        for drone in self.drones:
            cargo = self.drone_cargo[drone.id]
            status = 'On-Duty' if any(cargo.to_dict().values()) else 'Idle'
            left_info.append(f'{status} Drone {drone.id:2d}')
            left_info.append(f'   {self._format_supply_info(cargo)}')
        
        left_info.append('\nDepots')
        left_info.append('-' * 25)
        
        for depot in self.depots:
            left_info.append(f'{depot.name}')
            left_info.append(f'   {self._format_supply_info(depot.supply)}')
        
        self.left_text.set_text('\n'.join(left_info))
        
        # Πίνακας δεξιά - Πληροφορίες σημείων ανάγκης
        right_info = []
        right_info.append('Destinations')
        right_info.append('-' * 25)
        
        for (i, dest) in enumerate(self.destinations):
            rate = dest.sat_rate() * 100
            status = '✓' if rate >= 90 else '!' if rate >= 50 else '✗'
            right_info.append(f'{status} {dest.name}')
            right_info.append(f'   {rate:5.1f}%')
            right_info.append(f'   {self._format_supply_info(dest.satisfied)}')
        
        self.right_text.set_text('\n'.join(right_info))

        return;

    # --- Animation callbacks ---
    def _init_animation(self) -> tuple:
        self.scat_drones.set_offsets(np.empty((0, 2)))
        self.text_status.set_text('')
        self._update_info_panels(0)
        
        return (
            self.scat_drones,
            self.text_status,
            self._dest_scatter,
            self.left_text,
            self.right_text
        );

    def _update_animation(self, frame: int) -> tuple:
        '''Update animation for current frame with enhanced event handling.'''
        # Επεξεργασία γεγονότων για το τρέχον frame!
        active_drones = set()
        
        for (event_frame, event_type, drone_id, location_id, supply) in self._events:
            if frame == event_frame:
                if event_type == 'pickup':
                    depot = next((d for d in self.depots if d.id == location_id), None)
                    if depot:
                        depot.supply               = depot.supply - supply
                        self.drone_cargo[drone_id] = supply
                
                elif event_type == 'drop':
                    dest = next((d for d in self.destinations if d.id == location_id), None)
                    if dest:
                        dest.satisfied             = dest.satisfied + supply
                        self.drone_cargo[drone_id] = Supply()
                        self._animation_stats['completed_deliveries'] += 1
        
        # Ενημέρωση θέσεων δρόνων
        positions = []
        for drone in self.drones:
            pos = self.trajectories[drone.id].pos_at(frame)
            positions.append(pos)
            
            # Έλεγχος αν ο δρόνος έχει ενεργό φορτίο
            if any(self.drone_cargo[drone.id].to_dict().values()):
                active_drones.add(drone.id)
        
        self.scat_drones.set_offsets(positions)
        self._animation_stats['drones_in_flight'] = len(active_drones)
        
        self._update_destination_colors(frame) # Ενημέρωση χρωμάτων σημείων ανάγκης
        
        # Ενημέρωση κατάστασης
        status_text = (
            f'Frame: {frame:4d}/{self.max_frames-1:4d}\n'

            f"Deliveries: {self._animation_stats[
                'completed_deliveries'
            ]:2d}/{self._animation_stats['total_deliveries']:2d}\n"

            f"On-Duty Drones: {self._animation_stats['drones_in_flight']:2d}"
        )
        self.text_status.set_text(status_text)
        
        self._update_info_panels(frame) # Ενημέρωση πληροφοριών στους πίνακες
        
        return (
            self.scat_drones,
            self.text_status,
            self._dest_scatter,
            self.left_text,
            self.right_text
        );

    def _update_destination_colors(self, frame: int) -> None:
        ''' Ενημέρωση χρωμάτων των σημείων ανάγκης ανάλογα με την κατάσταση ολοκλήρωσης. '''
        colors = []
        for (i, dest) in enumerate(self.destinations):
            if self._dest_satisfied[i]:
                colors.append('lightgreen')
            else:
                # Έλεγχος αν έχει ολοκληρωθεί παράδοση για το σημείο ανάγκης
                for traj in self.trajectories.values():
                    for (dest_id, completion_frame) in traj.dest_frames:
                        if (dest_id == dest.id) and (frame >= completion_frame):
                            colors.append('lightgreen')
                            self._dest_satisfied[i] = True
                            break;
                    else:
                        continue;
                    break;
                else:
                    colors.append('red')
        
        if colors: self._dest_scatter.set_facecolors(colors)

        return;

    def run(self) -> FuncAnimation:
        anim = FuncAnimation(
            self.fig, self._update_animation, frames = self.max_frames,
            init_func = self._init_animation, interval = 50, blit = True, repeat = False
        )

        # Maximize window - Δεν δουλεύει σε όλα τα PC!!!
        # try:
        #     mng = plt.get_current_fig_manager()
        #     mng.window.state('zoomed') # TkAgg -> Windows
        # except:
        #     try:
        #         mng.window.showMaximized() # Qt backends
        #     except:
        #         pass;
        
        plt.show()
        
        return anim;



class _Trajectory:
    ''' Βοηθητική κλάση για την αποθήκευση της/των διαδρομής/ών ενός δρόνου. '''
    
    def __init__(self,
                 positions:   List[Tuple[float, float]],
                 dest_frames: List[Tuple[int, int]]) -> None:
        self.positions   = positions if positions else [(0, 0)]
        self.dest_frames = dest_frames or [] # Λίστα από (dest_id, arrival_frame)

        return;
    
    @property
    def n_frames(self) -> int:
        return len(self.positions);
    
    def pos_at(self, frame: int) -> Tuple[float, float]:
        ''' Επιστρέφει τη θέση του δρόνου σε συγκεκριμένο frame. '''
        if not self.positions:
            return (0, 0);
        
        idx = max(0, min(frame, self.n_frames - 1))

        return self.positions[idx];



def _interpolate(
    p0: Tuple[float, float], p1: Tuple[float, float], speed: float, dt: float
) -> List[Tuple[float, float]]:
    ''' Evenly spaced points από το p0 στο p1 με δεδομένο speed ανά dt. '''
    if not p0 or not p1 or speed <= 0 or dt <= 0:
        return [];
    
    vec  = np.array(p1) - np.array(p0)
    dist = np.linalg.norm(vec)
    
    if dist < 1e-6: # Πολύ μικρή απόσταση
        return [];
    
    n_steps  = max(1, math.ceil(dist / (speed * dt)))
    step_size = dist / n_steps
    direction = vec / dist
    
    return [
        tuple(np.array(p0) + direction * step_size * i) for i in range(1, n_steps + 1)
    ];



def main():
    choices = {
        1: big_city_scenario,
        2: silent_hill_scenario,
        3: raccoon_city_scenario
    }
    available_maps = [
        'map_background.png',
        'sh_map_by_jam6i_full.jpg',
        'map_raccoon_city.png' # FIX IT!
    ]

    # --- Επιλογή σεναρίου ---
    user_input = input(
        'Επιλέξτε 1 από τα παρακάτω σενάρια:\n'
        ' 1. Μεγάλη Πόλη\n'
        ' 2. Silent Hill\n'
        ' 3. Raccoon City\n'
        f'Εισάγετε επιλογή ({", ".join(map(str, choices.keys()))}): '
    )
    print('') # Για καλύτερη εμφάνιση

    try:
        user_input = int(user_input)
        if user_input not in choices.keys():
            raise ValueError('Μη έγκυρη επιλογή!');
    except ValueError as e:
        print(f'[X] {e} - Χρησιμοποιείται το προεπιλεγμένο σενάριο.\n')
        user_input = 1 # Προεπιλογή στο big_city_scenario
    
    my_scenario = choices.get(user_input, big_city_scenario)()
    my_map = os.path.join(
        base_dir, 'maps', available_maps[user_input - 1]
    )
    
    # --- Δημιουργία και εκτέλεση του animation ---
    animator = DroneAnimator(
        scenario = my_scenario,
        map_path = my_map if os.path.exists(my_map) else None,
        dt       = 0.01
    )
    
    animator.run()

    return;

if __name__ == '__main__':
    main()
