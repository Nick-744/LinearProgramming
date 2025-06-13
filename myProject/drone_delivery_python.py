import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random
from enum import Enum

class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class DroneStatus(Enum):
    IDLE = "idle"
    DELIVERING = "delivering"
    RETURNING = "returning"

@dataclass
class Supply:
    food: int = 0
    water: int = 0
    medicine: int = 0
    
    def total(self) -> int:
        return self.food + self.water + self.medicine
    
    def to_dict(self) -> Dict[str, int]:
        return {"food": self.food, "water": self.water, "medicine": self.medicine}
    
    def __add__(self, other):
        return Supply(
            self.food + other.food,
            self.water + other.water,
            self.medicine + other.medicine
        )
    
    def __sub__(self, other):
        return Supply(
            max(0, self.food - other.food),
            max(0, self.water - other.water),
            max(0, self.medicine - other.medicine)
        )

@dataclass
class Location:
    id: int
    x: float
    y: float
    name: str = ""
    
    def distance_to(self, other: 'Location') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

@dataclass
class Depot(Location):
    supply: Supply = field(default_factory=Supply)
    
@dataclass
class Destination(Location):
    demand: Supply = field(default_factory=Supply)
    satisfied: Supply = field(default_factory=Supply)
    priority: Priority = Priority.MEDIUM
    
    def satisfaction_rate(self) -> float:
        total_demand = self.demand.total()
        if total_demand == 0:
            return 1.0
        return self.satisfied.total() / total_demand
    
    def is_fully_satisfied(self) -> bool:
        return self.satisfaction_rate() >= 0.99

@dataclass
class Drone:
    id: int
    x: float
    y: float
    capacity: int
    max_range: float
    speed: float
    status: DroneStatus = DroneStatus.IDLE
    cargo: Supply = field(default_factory=Supply)
    target: Optional[Location] = None
    assignment: Optional['DeliveryAssignment'] = None
    battery: float = 100.0  # Battery percentage
    
    def can_reach(self, destination: Location, depot: Location) -> bool:
        """Check if drone can reach destination and return to depot"""
        total_distance = depot.distance_to(destination) * 2  # Round trip
        return total_distance <= self.max_range
    
    def time_to_deliver(self, destination: Location, depot: Location) -> float:
        """Calculate time needed for delivery (round trip)"""
        total_distance = depot.distance_to(destination) * 2
        return total_distance / self.speed

@dataclass
class DeliveryAssignment:
    drone_id: int
    depot_id: int
    destination_id: int
    supply: Supply
    cost: float
    distance: float
    priority_weight: float

class DroneDeliveryOptimizer:
    """
    Main class for optimizing drone delivery operations using Linear Programming
    """
    
    def __init__(self):
        self.depots: List[Depot] = []
        self.destinations: List[Destination] = []
        self.drones: List[Drone] = []
        self.assignments: List[DeliveryAssignment] = []
        self.time_step = 0
        
        # Problem parameters
        self.priority_weights = {
            Priority.HIGH: 0.5,    # Lower cost multiplier = higher priority
            Priority.MEDIUM: 1.0,
            Priority.LOW: 1.5
        }
        
        # Animation parameters
        self.fig = None
        self.ax = None
        self.animation = None
        
    def add_depot(self, x: float, y: float, supply: Supply, name: str = "") -> Depot:
        """Add a supply depot"""
        depot = Depot(len(self.depots), x, y, name, supply)
        self.depots.append(depot)
        return depot
    
    def add_destination(self, x: float, y: float, demand: Supply, 
                       priority: Priority = Priority.MEDIUM, name: str = "") -> Destination:
        """Add a destination requiring supplies"""
        dest = Destination(
            len(self.destinations), x, y, name, 
            demand, Supply(), priority
        )
        self.destinations.append(dest)
        return dest
    
    def add_drone(self, x: float, y: float, capacity: int, 
                  max_range: float, speed: float = 50.0) -> Drone:
        """Add a delivery drone"""
        drone = Drone(len(self.drones), x, y, capacity, max_range, speed)
        self.drones.append(drone)
        return drone
    
    def create_sample_scenario(self):
        """Create a sample disaster scenario for testing"""
        # Add main depot
        depot = self.add_depot(50, 50, Supply(500, 300, 100), "Main Depot")
        
        # Add affected locations with varying priorities
        self.add_destination(150, 100, Supply(80, 60, 20), Priority.HIGH, "Hospital Area")
        self.add_destination(80, 180, Supply(60, 40, 15), Priority.MEDIUM, "Residential Zone")
        self.add_destination(200, 150, Supply(90, 70, 25), Priority.HIGH, "School Shelter")
        self.add_destination(180, 220, Supply(40, 30, 10), Priority.LOW, "Commercial District")
        self.add_destination(120, 250, Supply(70, 50, 18), Priority.MEDIUM, "Community Center")
        
        # Add drone fleet
        for i in range(4):
            self.add_drone(depot.x, depot.y, capacity=100, max_range=200, speed=50)
    
    def solve_transportation_lp(self) -> List[DeliveryAssignment]:
        """
        Solve the transportation problem using Linear Programming
        
        This implements a simplified version of the transportation problem:
        - Minimize: Sum of (distance * priority_weight * amount)
        - Subject to: supply constraints, demand constraints, drone capacity
        """
        if not self.depots or not self.destinations or not self.drones:
            return []
        
        n_depots = len(self.depots)
        n_destinations = len(self.destinations)
        n_drones = len(self.drones)
        
        assignments = []
        
        # Create distance and cost matrices
        distances = np.zeros((n_depots, n_destinations))
        costs = np.zeros((n_depots, n_destinations))
        
        for i, depot in enumerate(self.depots):
            for j, dest in enumerate(self.destinations):
                dist = depot.distance_to(dest)
                distances[i, j] = dist
                priority_weight = self.priority_weights[dest.priority]
                costs[i, j] = dist * priority_weight
        
        # Greedy assignment with priority sorting
        available_drones = [d for d in self.drones if d.status == DroneStatus.IDLE]
        remaining_supply = {i: depot.supply.total() for i, depot in enumerate(self.depots)}
        
        # Sort destinations by priority and distance
        dest_priorities = [
            (i, dest, distances[0, i], dest.priority) 
            for i, dest in enumerate(self.destinations)
            if not dest.is_fully_satisfied()
        ]
        
        dest_priorities.sort(key=lambda x: (x[3].value, x[2]))  # Priority first, then distance
        
        drone_idx = 0
        for dest_idx, dest, dist, priority in dest_priorities:
            if drone_idx >= len(available_drones):
                break
                
            drone = available_drones[drone_idx]
            depot_idx = 0  # Using first depot for simplicity
            depot = self.depots[depot_idx]
            
            # Check if drone can reach destination
            if not drone.can_reach(dest, depot):
                continue
            
            # Calculate delivery amount
            remaining_demand = dest.demand.total() - dest.satisfied.total()
            available_supply = remaining_supply[depot_idx]
            delivery_amount = min(remaining_demand, available_supply, drone.capacity)
            
            if delivery_amount > 0:
                # Create proportional supply delivery
                total_demand = dest.demand.total()
                if total_demand > 0:
                    supply_ratio = delivery_amount / total_demand
                    delivery_supply = Supply(
                        int(dest.demand.food * supply_ratio),
                        int(dest.demand.water * supply_ratio),
                        int(dest.demand.medicine * supply_ratio)
                    )
                else:
                    delivery_supply = Supply()
                
                assignment = DeliveryAssignment(
                    drone.id, depot_idx, dest_idx,
                    delivery_supply, costs[depot_idx, dest_idx],
                    distances[depot_idx, dest_idx],
                    self.priority_weights[priority]
                )
                
                assignments.append(assignment)
                remaining_supply[depot_idx] -= delivery_amount
                drone_idx += 1
        
        return assignments
    
    def execute_assignments(self, assignments: List[DeliveryAssignment]):
        """Execute the delivery assignments"""
        self.assignments = assignments
        
        for assignment in assignments:
            drone = self.drones[assignment.drone_id]
            destination = self.destinations[assignment.destination_id]
            
            drone.status = DroneStatus.DELIVERING
            drone.target = destination
            drone.cargo = assignment.supply
            drone.assignment = assignment
    
    def update_simulation_step(self):
        """Update one step of the simulation"""
        self.time_step += 1
        
        for drone in self.drones:
            if drone.status == DroneStatus.DELIVERING and drone.target:
                # Move towards target
                dx = drone.target.x - drone.x
                dy = drone.target.y - drone.y
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance < drone.speed:
                    # Reached destination
                    drone.x = drone.target.x
                    drone.y = drone.target.y
                    
                    # Deliver cargo
                    if drone.assignment:
                        dest = self.destinations[drone.assignment.destination_id]
                        dest.satisfied = dest.satisfied + drone.cargo
                    
                    drone.status = DroneStatus.RETURNING
                    drone.target = self.depots[0]  # Return to first depot
                    drone.cargo = Supply()
                    
                else:
                    # Move towards target
                    drone.x += (dx / distance) * drone.speed
                    drone.y += (dy / distance) * drone.speed
                    
            elif drone.status == DroneStatus.RETURNING and drone.target:
                # Return to depot
                dx = drone.target.x - drone.x
                dy = drone.target.y - drone.y
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance < drone.speed:
                    # Reached depot
                    drone.x = drone.target.x
                    drone.y = drone.target.y
                    drone.status = DroneStatus.IDLE
                    drone.target = None
                    drone.assignment = None
                else:
                    # Move towards depot
                    drone.x += (dx / distance) * drone.speed
                    drone.y += (dy / distance) * drone.speed
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        total_cost = sum(assignment.cost for assignment in self.assignments)
        
        total_demand = sum(dest.demand.total() for dest in self.destinations)
        total_satisfied = sum(dest.satisfied.total() for dest in self.destinations)
        satisfaction_rate = (total_satisfied / total_demand * 100) if total_demand > 0 else 0
        
        active_drones = sum(1 for drone in self.drones if drone.status != DroneStatus.IDLE)
        
        return {
            "total_cost": total_cost,
            "satisfaction_rate": satisfaction_rate,
            "active_drones": active_drones,
            "total_drones": len(self.drones),
            "time_step": self.time_step
        }
    
    def print_status(self):
        """Print current status of the system"""
        print(f"\n=== Time Step {self.time_step} ===")
        
        metrics = self.get_performance_metrics()
        print(f"Total Cost: {metrics['total_cost']:.2f}")
        print(f"Satisfaction Rate: {metrics['satisfaction_rate']:.1f}%")
        print(f"Active Drones: {metrics['active_drones']}/{metrics['total_drones']}")
        
        print("\nDestination Status:")
        for dest in self.destinations:
            sat_rate = dest.satisfaction_rate() * 100
            print(f"  {dest.name or f'Dest {dest.id}'}: {sat_rate:.1f}% satisfied "
                  f"({dest.satisfied.total()}/{dest.demand.total()}) - Priority: {dest.priority.name}")
        
        print("\nDrone Status:")
        for drone in self.drones:
            cargo_info = f"Cargo: {drone.cargo.total()}" if drone.cargo.total() > 0 else "Empty"
            print(f"  Drone {drone.id}: {drone.status.value} - {cargo_info}")
    
    def setup_visualization(self, figsize=(12, 8)):
        """Setup matplotlib visualization"""
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Main simulation plot
        self.ax1.set_xlim(0, 300)
        self.ax1.set_ylim(0, 300)
        self.ax1.set_aspect('equal')
        self.ax1.set_title('Drone Delivery Simulation')
        self.ax1.grid(True, alpha=0.3)
        
        # Performance metrics plot
        self.ax2.set_title('Performance Metrics')
        
        plt.tight_layout()
    
    def update_visualization(self):
        """Update the visualization"""
        if self.ax1 is None:
            return
            
        self.ax1.clear()
        self.ax1.set_xlim(0, 300)
        self.ax1.set_ylim(0, 300)
        self.ax1.set_aspect('equal')
        self.ax1.set_title(f'Drone Delivery Simulation - Step {self.time_step}')
        self.ax1.grid(True, alpha=0.3)
        
        # Draw depots
        for depot in self.depots:
            rect = Rectangle((depot.x-15, depot.y-15), 30, 30, 
                           facecolor='blue', alpha=0.7, edgecolor='darkblue')
            self.ax1.add_patch(rect)
            self.ax1.text(depot.x, depot.y-25, 'DEPOT', ha='center', fontweight='bold')
        
        # Draw destinations
        for dest in self.destinations:
            sat_rate = dest.satisfaction_rate()
            color = 'green' if sat_rate > 0.8 else 'orange' if sat_rate > 0.4 else 'red'
            
            circle = Circle((dest.x, dest.y), 12, facecolor=color, alpha=0.7, edgecolor='black')
            self.ax1.add_patch(circle)
            
            # Priority indicator
            priority_colors = {Priority.HIGH: 'red', Priority.MEDIUM: 'yellow', Priority.LOW: 'green'}
            priority_circle = Circle((dest.x+15, dest.y+15), 4, 
                                   facecolor=priority_colors[dest.priority], alpha=0.8)
            self.ax1.add_patch(priority_circle)
            
            self.ax1.text(dest.x, dest.y, str(dest.id), ha='center', va='center', 
                         fontweight='bold', color='white')
            self.ax1.text(dest.x, dest.y-20, f'{sat_rate:.0%}', ha='center', fontsize=8)
        
        # Draw drones
        for drone in self.drones:
            drone_colors = {
                DroneStatus.IDLE: 'gray',
                DroneStatus.DELIVERING: 'orange', 
                DroneStatus.RETURNING: 'lightblue'
            }
            
            circle = Circle((drone.x, drone.y), 8, 
                          facecolor=drone_colors[drone.status], alpha=0.8, edgecolor='black')
            self.ax1.add_patch(circle)
            
            self.ax1.text(drone.x, drone.y, f'D{drone.id}', ha='center', va='center', 
                         fontweight='bold', fontsize=8)
            
            if drone.cargo.total() > 0:
                self.ax1.text(drone.x, drone.y-15, f'{drone.cargo.total()}', 
                            ha='center', fontsize=8, color='red')
        
        # Draw flight paths
        for assignment in self.assignments:
            drone = self.drones[assignment.drone_id]
            dest = self.destinations[assignment.destination_id]
            depot = self.depots[assignment.depot_id]
            
            if drone.status != DroneStatus.IDLE:
                self.ax1.plot([depot.x, dest.x], [depot.y, dest.y], 
                            'b--', alpha=0.5, linewidth=2)
        
        # Legend
        legend_elements = [
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='blue', 
                      markersize=10, label='Depot'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', 
                      markersize=10, label='Satisfied (>80%)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
                      markersize=10, label='Partial (40-80%)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                      markersize=10, label='Unsatisfied (<40%)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                      markersize=8, label='Drone (Idle)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
                      markersize=8, label='Drone (Delivering)')
        ]
        self.ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)
        
        plt.draw()
    
    def run_static_optimization(self):
        """Run static optimization and display results"""
        print("=== STATIC LINEAR PROGRAMMING OPTIMIZATION ===")
        
        # Solve the transportation problem
        assignments = self.solve_transportation_lp()
        self.execute_assignments(assignments)
        
        print(f"\nFound {len(assignments)} optimal assignments:")
        for i, assignment in enumerate(assignments):
            drone = self.drones[assignment.drone_id]
            dest = self.destinations[assignment.destination_id]
            print(f"  Assignment {i+1}: Drone {assignment.drone_id} -> "
                  f"Destination {assignment.destination_id} "
                  f"(Distance: {assignment.distance:.1f}, Cost: {assignment.cost:.1f})")
        
        self.print_status()
        
        return assignments
    
    def run_dynamic_simulation(self, max_steps=100, visualization=True):
        """Run dynamic simulation with evolving scenario"""
        print("\n=== DYNAMIC SIMULATION ===")
        
        if visualization:
            self.setup_visualization()
            plt.ion()
        
        # Initial optimization
        self.run_static_optimization()
        
        for step in range(max_steps):
            # Update simulation
            self.update_simulation_step()
            
            # Check if new optimization is needed
            idle_drones = [d for d in self.drones if d.status == DroneStatus.IDLE]
            unsatisfied_destinations = [d for d in self.destinations if not d.is_fully_satisfied()]
            
            if idle_drones and unsatisfied_destinations and step % 10 == 0:
                # Re-optimize with remaining resources
                new_assignments = self.solve_transportation_lp()
                if new_assignments:
                    self.execute_assignments(new_assignments)
                    print(f"\nStep {self.time_step}: Re-optimized with {len(new_assignments)} new assignments")
            
            # Dynamic scenario evolution (optional)
            if step % 20 == 0 and step > 0:
                self.evolve_scenario()
            
            # Update visualization
            if visualization:
                self.update_visualization()
                plt.pause(0.1)
            
            # Print status every 10 steps
            if step % 10 == 0:
                self.print_status()
            
            # Check if all destinations are satisfied
            if all(dest.is_fully_satisfied() for dest in self.destinations):
                print(f"\nAll destinations satisfied at step {self.time_step}!")
                break
        
        if visualization:
            plt.ioff()
            plt.show()
    
    def evolve_scenario(self):
        """Simulate dynamic changes in the disaster scenario"""
        # Randomly increase demand at some locations (spreading disaster)
        for dest in self.destinations:
            if random.random() < 0.2:  # 20% chance of increased demand
                increase = Supply(
                    random.randint(0, 20),
                    random.randint(0, 15), 
                    random.randint(0, 5)
                )
                dest.demand = dest.demand + increase
                print(f"  Increased demand at {dest.name or f'Destination {dest.id}'} "
                      f"by {increase.total()} units")
    
    def generate_report(self) -> str:
        """Generate a comprehensive performance report"""
        metrics = self.get_performance_metrics()
        
        report = f"""
=== DRONE DELIVERY OPTIMIZATION REPORT ===

Problem Configuration:
- Depots: {len(self.depots)}
- Destinations: {len(self.destinations)}
- Drones: {len(self.drones)}
- Time Steps: {metrics['time_step']}

Performance Metrics:
- Total Cost: {metrics['total_cost']:.2f}
- Overall Satisfaction Rate: {metrics['satisfaction_rate']:.1f}%
- Drone Utilization: {metrics['active_drones']}/{metrics['total_drones']}

Destination Analysis:
"""
        
        for dest in self.destinations:
            sat_rate = dest.satisfaction_rate() * 100
            report += f"- {dest.name or f'Destination {dest.id}'}: {sat_rate:.1f}% satisfied "
            report += f"({dest.satisfied.total()}/{dest.demand.total()}) "
            report += f"Priority: {dest.priority.name}\n"
        
        report += f"\nAssignments Made: {len(self.assignments)}\n"
        
        for assignment in self.assignments:
            report += f"- Drone {assignment.drone_id} -> Destination {assignment.destination_id} "
            report += f"(Cost: {assignment.cost:.2f}, Distance: {assignment.distance:.1f})\n"
        
        return report

def main():
    """Main function demonstrating the drone delivery optimization system"""
    
    # Create optimizer instance
    optimizer = DroneDeliveryOptimizer()
    
    # Create sample scenario
    print("Creating sample disaster scenario...")
    optimizer.create_sample_scenario()
    
    print(f"Scenario created with:")
    print(f"- {len(optimizer.depots)} depot(s)")
    print(f"- {len(optimizer.destinations)} affected location(s)")
    print(f"- {len(optimizer.drones)} drone(s)")
    
    # Run static optimization
    optimizer.run_static_optimization()
    
    # Option 1: Run dynamic simulation with visualization
    print("\nStarting dynamic simulation...")
    print("Close the plot window to continue...")
    
    try:
        optimizer.run_dynamic_simulation(max_steps=50, visualization=True)
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    
    # Generate final report
    print("\n" + optimizer.generate_report())

if __name__ == "__main__":
    main()
