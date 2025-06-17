"""enhanced_animate.py
=====================
Enhanced dynamic animation for the drone delivery solver with real-time solving.

Features:
- Real-time visualization of drone movements and solving process
- Live metrics display and progress tracking
- Interactive controls (play/pause, speed adjustment)
- Multi-trip visualization with battery management
- Dynamic scenario updates with disaster states
- Performance metrics and efficiency tracking

Run with:
    python enhanced_animate.py
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider
import matplotlib.patches as patches
from typing import Dict, List, Tuple, Optional
import threading
import time
import queue
from dataclasses import dataclass
from enum import Enum

from scenario import extended_scenario, earthquake_scenario, flood_scenario
from lp_solver import solve_multi_trip, MultiTripAssignment, Assignment, calculate_scenario_metrics
from models import Drone, Depot, Destination, DroneStatus, DisasterState, DisasterType

# Animation state management
class AnimationState(Enum):
    SOLVING = "solving"
    ANIMATING = "animating" 
    PAUSED = "paused"
    COMPLETED = "completed"

@dataclass
class DroneAnimationState:
    """Track individual drone animation state"""
    position: Tuple[float, float]
    target: Optional[Tuple[float, float]]
    status: DroneStatus
    current_assignment: Optional[Assignment]
    battery_level: float
    trip_progress: float
    time_at_target: float

class EnhancedDroneAnimation:
    def __init__(self):
        # Animation control
        self.state = AnimationState.SOLVING
        self.speed_multiplier = 1.0
        self.time_step = 0
        self.max_time_steps = 20
        self.current_frame = 0
        
        # Scenario data
        self.drones: List[Drone] = []
        self.depots: List[Depot] = []
        self.destinations: List[Destination] = []
        self.assignments: List[MultiTripAssignment] = []
        
        # Animation state tracking
        self.drone_states: Dict[int, DroneAnimationState] = {}
        self.solution_queue = queue.Queue()
        self.metrics_history = []
        
        # Visualization components
        self.fig = None
        self.ax_main = None
        self.ax_metrics = None
        self.ax_battery = None
        
        # Interactive elements
        self.play_pause_button = None
        self.speed_slider = None
        self.scenario_buttons = {}
        
        # Visual elements
        self.drone_scatter = None
        self.depot_scatter = None
        self.dest_scatter = None
        self.path_lines = []
        self.battery_bars = []
        self.metrics_plots = {}
        
        # Disaster simulation
        self.disaster_states = []
        self.current_disaster = None
        
    def setup_visualization(self):
        """Initialize the matplotlib figure and subplots"""
        self.fig = plt.figure(figsize=(16, 10))
        
        # Main animation area (left side)
        self.ax_main = plt.subplot2grid((3, 3), (0, 0), colspan=2, rowspan=2)
        self.ax_main.set_title("Dynamic Drone Delivery Simulation", fontsize=14, fontweight='bold')
        self.ax_main.grid(True, alpha=0.3)
        
        # Metrics display (top right)
        self.ax_metrics = plt.subplot2grid((3, 3), (0, 2))
        self.ax_metrics.set_title("Live Metrics", fontsize=12)
        self.ax_metrics.axis('off')
        
        # Battery levels (middle right)
        self.ax_battery = plt.subplot2grid((3, 3), (1, 2))
        self.ax_battery.set_title("Drone Battery Levels", fontsize=12)
        self.ax_battery.set_xlim(0, 100)
        self.ax_battery.set_xlabel("Battery %")
        
        # Control panel (bottom)
        self.ax_controls = plt.subplot2grid((3, 3), (2, 0), colspan=3)
        self.setup_controls()
        
        plt.tight_layout()
        
    def setup_controls(self):
        """Setup interactive controls"""
        self.ax_controls.axis('off')
        
        # Play/Pause button
        ax_play = plt.axes([0.1, 0.05, 0.1, 0.04])
        self.play_pause_button = Button(ax_play, 'Play/Pause')
        self.play_pause_button.on_clicked(self.toggle_play_pause)
        
        # Speed slider
        ax_speed = plt.axes([0.25, 0.05, 0.2, 0.04])
        self.speed_slider = Slider(ax_speed, 'Speed', 0.1, 5.0, valinit=1.0)
        self.speed_slider.on_changed(self.update_speed)
        
        # Scenario selection buttons
        scenarios = [
            ('Extended', extended_scenario),
            ('Earthquake', earthquake_scenario),
            ('Flood', flood_scenario)
        ]
        
        for i, (name, func) in enumerate(scenarios):
            ax_btn = plt.axes([0.5 + i*0.12, 0.05, 0.1, 0.04])
            btn = Button(ax_btn, name)
            btn.on_clicked(lambda x, f=func: self.load_scenario(f))
            self.scenario_buttons[name] = btn
            
    def toggle_play_pause(self, event):
        """Toggle between play and pause states"""
        if self.state == AnimationState.ANIMATING:
            self.state = AnimationState.PAUSED
        elif self.state == AnimationState.PAUSED:
            self.state = AnimationState.ANIMATING
            
    def update_speed(self, val):
        """Update animation speed"""
        self.speed_multiplier = val
        
    def load_scenario(self, scenario_func):
        """Load a new scenario and restart simulation"""
        self.drones, self.depots, self.destinations = scenario_func()
        self.reset_animation()
        self.start_solving_thread()
        
    def reset_animation(self):
        """Reset animation state"""
        self.state = AnimationState.SOLVING
        self.time_step = 0
        self.current_frame = 0
        self.drone_states.clear()
        self.metrics_history.clear()
        
        # Initialize drone states
        for drone in self.drones:
            self.drone_states[drone.id] = DroneAnimationState(
                position=(drone.x, drone.y),
                target=None,
                status=DroneStatus.IDLE,
                current_assignment=None,
                battery_level=drone.battery,
                trip_progress=0.0,
                time_at_target=0.0
            )
            
    def start_solving_thread(self):
        """Start background thread for solving optimization"""
        def solve_continuously():
            for step in range(self.max_time_steps):
                if self.state == AnimationState.COMPLETED:
                    break
                    
                try:
                    # Solve current step
                    multi_trips = solve_multi_trip(self.drones, self.depots, self.destinations)
                    metrics = calculate_scenario_metrics(
                        [a for mt in multi_trips for a in mt.assignments], 
                        self.destinations
                    )
                    
                    # Queue results for main thread
                    self.solution_queue.put((step, multi_trips, metrics))
                    
                    # Update scenario state
                    self.update_scenario_state(step)
                    time.sleep(0.5)  # Simulate solving time
                    
                except Exception as e:
                    print(f"Solving error at step {step}: {e}")
                    break
                    
            self.state = AnimationState.COMPLETED
            
        threading.Thread(target=solve_continuously, daemon=True).start()
        
    def update_scenario_state(self, step: int):
        """Update scenario based on time step (simulate dynamic conditions)"""
        # Simulate disaster progression
        if step == 5:  # Introduce disaster at step 5
            self.current_disaster = DisasterState(
                time_step=step,
                disaster_type=DisasterType.EARTHQUAKE,
                affected_areas=[(100, 100, 50)],
                blocked_routes=[],
                weather_factor=0.8
            )
            
        # Update destination urgency
        for dest in self.destinations:
            dest.update_urgency(step * 30)  # Each step = 30 minutes
            
        # Simulate supply depletion
        for depot in self.depots:
            if step > 0 and depot.supply.total() > 0:
                # Gradual supply consumption
                depot.supply.food = max(0, depot.supply.food - 5)
                depot.supply.water = max(0, depot.supply.water - 5)
                depot.supply.medicine = max(0, depot.supply.medicine - 2)
                
    def process_solution_queue(self):
        """Process solutions from background thread"""
        try:
            while not self.solution_queue.empty():
                step, multi_trips, metrics = self.solution_queue.get_nowait()
                self.assignments = multi_trips
                self.metrics_history.append((step, metrics))
                self.time_step = step
                
                if self.state == AnimationState.SOLVING:
                    self.state = AnimationState.ANIMATING
                    
        except queue.Empty:
            pass
            
    def update_drone_positions(self, frame: int):
        """Update drone positions based on current assignments"""
        dt = 0.1 * self.speed_multiplier  # Time delta
        
        for drone_id, state in self.drone_states.items():
            if state.status == DroneStatus.IDLE:
                # Check for new assignments
                for mt in self.assignments:
                    if mt.drone_id == drone_id and mt.assignments:
                        # Start first assignment
                        assignment = mt.assignments[0]
                        depot = self.depots[assignment.depot_id]
                        state.target = (depot.x, depot.y)
                        state.status = DroneStatus.DELIVERING
                        state.current_assignment = assignment
                        break
                        
            elif state.status == DroneStatus.DELIVERING and state.target:
                # Move towards target
                current_pos = np.array(state.position)
                target_pos = np.array(state.target)
                direction = target_pos - current_pos
                distance = np.linalg.norm(direction)
                
                if distance < 2.0:  # Reached target
                    state.position = tuple(target_pos)
                    
                    if state.current_assignment:
                        # Move to destination
                        dest = self.destinations[state.current_assignment.dest_id]
                        state.target = (dest.x, dest.y)
                        state.status = DroneStatus.RETURNING
                        
                else:
                    # Move towards target
                    speed = self.drones[drone_id].speed * dt
                    move_distance = min(speed, distance)
                    move_vector = (direction / distance) * move_distance
                    new_pos = current_pos + move_vector
                    state.position = tuple(new_pos)
                    
            elif state.status == DroneStatus.RETURNING and state.target:
                # Similar movement logic for return trip
                current_pos = np.array(state.position)
                target_pos = np.array(state.target)
                direction = target_pos - current_pos
                distance = np.linalg.norm(direction)
                
                if distance < 2.0:  # Reached destination
                    state.position = tuple(target_pos)
                    state.status = DroneStatus.IDLE
                    state.target = None
                    state.current_assignment = None
                    # Update battery consumption
                    state.battery_level = max(0, state.battery_level - 10)
                    
                else:
                    speed = self.drones[drone_id].speed * dt
                    move_distance = min(speed, distance)
                    move_vector = (direction / distance) * move_distance
                    new_pos = current_pos + move_vector
                    state.position = tuple(new_pos)
                    
    def update_visualization(self, frame: int):
        """Update all visualization elements"""
        if self.state == AnimationState.PAUSED:
            return
            
        self.process_solution_queue()
        self.update_drone_positions(frame)
        
        # Update main plot
        self.update_main_plot()
        self.update_metrics_display()
        self.update_battery_display()
        
        self.current_frame = frame
        
    def update_main_plot(self):
        """Update the main animation plot"""
        self.ax_main.clear()
        
        # Set bounds based on all locations
        all_x = [d.x for d in self.destinations + self.depots] + [s.position[0] for s in self.drone_states.values()]
        all_y = [d.y for d in self.destinations + self.depots] + [s.position[1] for s in self.drone_states.values()]
        
        if all_x and all_y:
            margin = 20
            self.ax_main.set_xlim(min(all_x) - margin, max(all_x) + margin)
            self.ax_main.set_ylim(min(all_y) - margin, max(all_y) + margin)
        
        # Draw depots
        depot_x = [d.x for d in self.depots]
        depot_y = [d.y for d in self.depots]
        self.ax_main.scatter(depot_x, depot_y, marker='s', s=150, c='blue', 
                           label='Depots', alpha=0.8, edgecolors='darkblue')
        
        # Draw destinations with status colors
        dest_colors = []
        for dest in self.destinations:
            if dest.is_fully_satisfied():
                dest_colors.append('green')
            elif dest.sat_rate() > 0:
                dest_colors.append('orange') 
            else:
                dest_colors.append('red')
                
        dest_x = [d.x for d in self.destinations]
        dest_y = [d.y for d in self.destinations]
        self.ax_main.scatter(dest_x, dest_y, marker='X', s=120, c=dest_colors,
                           label='Destinations', alpha=0.8, edgecolors='darkred')
        
        # Draw drones with status colors
        drone_colors = []
        drone_sizes = []
        for drone in self.drones:
            state = self.drone_states[drone.id]
            if state.status == DroneStatus.IDLE:
                drone_colors.append('gray')
            elif state.status == DroneStatus.DELIVERING:
                drone_colors.append('yellow')
            else:
                drone_colors.append('cyan')
            
            # Size based on battery level
            drone_sizes.append(100 + state.battery_level)
            
        drone_x = [self.drone_states[d.id].position[0] for d in self.drones]
        drone_y = [self.drone_states[d.id].position[1] for d in self.drones]
        self.ax_main.scatter(drone_x, drone_y, marker='o', s=drone_sizes, c=drone_colors,
                           label='Drones', alpha=0.9, edgecolors='black')
        
        # Draw paths for active assignments
        for drone_id, state in self.drone_states.items():
            if state.target and state.status != DroneStatus.IDLE:
                self.ax_main.plot([state.position[0], state.target[0]], 
                                [state.position[1], state.target[1]], 
                                'k--', alpha=0.5, linewidth=1)
        
        # Draw disaster area if active
        if self.current_disaster:
            for (x, y, radius) in self.current_disaster.affected_areas:
                circle = patches.Circle((x, y), radius, fill=False, 
                                      edgecolor='red', linewidth=2, linestyle='--')
                self.ax_main.add_patch(circle)
        
        # Add labels
        for depot in self.depots:
            self.ax_main.annotate(depot.name, (depot.x, depot.y), 
                                xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        for dest in self.destinations:
            satisfaction = f"{dest.sat_rate()*100:.0f}%"
            self.ax_main.annotate(f"{dest.name}\n{satisfaction}", 
                                (dest.x, dest.y), xytext=(5, 5), 
                                textcoords='offset points', fontsize=8)
        
        self.ax_main.set_title(f"Time Step: {self.time_step} | State: {self.state.value}")
        self.ax_main.legend(loc='upper left')
        self.ax_main.grid(True, alpha=0.3)
        
    def update_metrics_display(self):
        """Update metrics text display"""
        self.ax_metrics.clear()
        self.ax_metrics.axis('off')
        
        if self.metrics_history:
            _, latest_metrics = self.metrics_history[-1]
            
            metrics_text = f"""
PERFORMANCE METRICS
─────────────────────
Total Distance: {latest_metrics.total_distance:.1f} km
Total Cost: {latest_metrics.total_cost:.1f}
Avg Satisfaction: {latest_metrics.avg_satisfaction*100:.1f}%
High Priority Coverage: {latest_metrics.high_priority_coverage*100:.1f}%
Drones Utilized: {latest_metrics.drones_utilized}/{len(self.drones)}
Efficiency Score: {latest_metrics.calculate_efficiency_score():.1f}

SCENARIO STATUS
─────────────────────
Active Drones: {sum(1 for s in self.drone_states.values() if s.status != DroneStatus.IDLE)}
Completed Deliveries: {sum(1 for d in self.destinations if d.is_fully_satisfied())}
Disaster Active: {'Yes' if self.current_disaster else 'No'}
            """
            
            self.ax_metrics.text(0.05, 0.95, metrics_text, transform=self.ax_metrics.transAxes,
                               fontsize=9, verticalalignment='top', fontfamily='monospace')
        
    def update_battery_display(self):
        """Update battery level bars"""
        self.ax_battery.clear()
        
        drone_ids = [d.id for d in self.drones]
        battery_levels = [self.drone_states[d_id].battery_level for d_id in drone_ids]
        
        colors = ['red' if b < 20 else 'orange' if b < 50 else 'green' for b in battery_levels]
        
        bars = self.ax_battery.barh(drone_ids, battery_levels, color=colors, alpha=0.7)
        
        # Add battery percentage labels
        for i, (drone_id, battery) in enumerate(zip(drone_ids, battery_levels)):
            self.ax_battery.text(battery + 2, i, f'{battery:.1f}%', 
                               va='center', fontsize=8)
        
        self.ax_battery.set_xlabel('Battery Level (%)')
        self.ax_battery.set_ylabel('Drone ID')
        self.ax_battery.set_xlim(0, 105)
        self.ax_battery.set_title('Battery Levels')
        self.ax_battery.grid(True, alpha=0.3)
        
    def run_animation(self):
        """Start the complete animation system"""
        # Load initial scenario
        self.drones, self.depots, self.destinations = extended_scenario()
        
        # Setup visualization
        self.setup_visualization()
        self.reset_animation()
        
        # Start solving thread
        self.start_solving_thread()
        
        # Create animation
        anim = FuncAnimation(
            self.fig, 
            self.update_visualization,
            interval=100,  # 100ms updates
            blit=False,
            repeat=True
        )
        
        plt.show()
        return anim

def run_enhanced_animation():
    """Main entry point for enhanced animation"""
    animation = EnhancedDroneAnimation()
    return animation.run_animation()

if __name__ == "__main__":
    run_enhanced_animation()
