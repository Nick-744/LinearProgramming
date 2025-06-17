import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random
from time import time
from enum import Enum
import pulp # Linear Programming library

class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class DroneStatus(Enum):
    IDLE = 'idle'
    DELIVERING = 'delivering'
    RETURNING = 'returning'

@dataclass
class Supply:
    '''Represents different types of supplies (food, water, medicine)'''
    food: int = 0
    water: int = 0
    medicine: int = 0
    
    def total(self) -> int:
        return self.food + self.water + self.medicine
    
    def to_dict(self) -> Dict[str, int]:
        return {'food': self.food, 'water': self.water, 'medicine': self.medicine}
    
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
    '''Base class for locations in the system'''
    id: int
    x: float
    y: float
    name: str = ''
    
    def distance_to(self, other: 'Location') -> float:
        '''Calculate Euclidean distance to another location'''
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

@dataclass
class Depot(Location):
    '''Supply depot that stores resources'''
    supply: Supply = field(default_factory=Supply)
    
@dataclass
class Destination(Location):
    '''Destination that requires supplies'''
    demand: Supply = field(default_factory=Supply)
    satisfied: Supply = field(default_factory=Supply)
    priority: Priority = Priority.MEDIUM
    
    def satisfaction_rate(self) -> float:
        '''Calculate how much of the demand has been satisfied (0-1)'''
        total_demand = self.demand.total()
        if total_demand == 0:
            return 1.0
        return self.satisfied.total() / total_demand
    
    def is_fully_satisfied(self) -> bool:
        '''Check if destination is fully satisfied (>99%)'''
        return self.satisfaction_rate() >= 0.99

@dataclass
class Drone:
    '''Drone that can carry and deliver supplies'''
    id: int
    x: float
    y: float
    capacity: int  # Maximum cargo capacity
    max_range: float  # Maximum flight range
    speed: float  # Travel speed
    status: DroneStatus = DroneStatus.IDLE
    cargo: Supply = field(default_factory=Supply)
    target: Optional[Location] = None
    assignment: Optional['DeliveryAssignment'] = None
    battery: float = 100.0  # Battery percentage
    
    def can_reach(self, destination: Location, depot: Location) -> bool:
        '''Check if drone can reach destination and return to depot'''
        total_distance = depot.distance_to(destination) * 2  # Round trip
        return total_distance <= self.max_range
    
    def time_to_deliver(self, destination: Location, depot: Location) -> float:
        '''Calculate time needed for delivery (round trip)'''
        total_distance = depot.distance_to(destination) * 2
        return total_distance / self.speed

@dataclass
class DeliveryAssignment:
    '''Assignment of a drone to deliver supplies from depot to destination'''
    drone_id: int
    depot_id: int
    destination_id: int
    supply: Supply
    cost: float
    distance: float
    priority_weight: float

class DroneDeliveryLPOptimizer:
    '''
    Η κλάση-καρδιά του προγράμματος! Αποτελεί την βάση για την βελτιστοποίηση
    των αποστολών με drones κάνοντας χρήση ΓΠ μέσω της βιβλιοθήκης PuLP.
    
    Ορίζει το πρόβλημα μεταφοράς ως Μικτό Ακέραιο Γραμμικό Πρόγραμμα (MILP):
    
    Μεταβλητές απόφασης:
    - x[d,i,j,s] = το πλήθος των προμηθειών τύπου s που μεταφέρει ο
                   δρόνος [τέλεια μετάφραση] d από τον σταθμό i στον προορισμό j
    - y[d,i,j]   = δυαδική μεταβλητή: 1 αν ο δρόνος d έχει ανατεθεί στην διαδρομή
                   σταθμός i -> προορισμός j, αλλιώς 0
    
    Αντικειμενική συνάρτηση:
    Minimize total weighted cost = Σ (distance[i,j] * priority_weight[j] * y[d,i,j])
    
    Constraints:
    1. Each drone can be assigned to at most one route
    2. Drone capacity constraints
    3. Drone range constraints  
    4. Supply availability at depots
    5. Demand satisfaction at destinations (soft constraint with penalty)
    '''
    
    def __init__(self):
        self.depots: List[Depot] = []
        self.destinations: List[Destination] = []
        self.drones: List[Drone] = []
        self.assignments: List[DeliveryAssignment] = []
        self.time_step = 0
        
        # Problem parameters for objective function weighting
        self.priority_weights = {
            Priority.HIGH: 0.5,    # Lower cost multiplier = higher priority
            Priority.MEDIUM: 1.0,
            Priority.LOW: 1.5
        }
        
        # Penalty weights for unmet demand (used in soft constraints)
        self.unmet_demand_penalty = 1000.0
        
        # Animation parameters (for future visualization)
        self.fig = None
        self.ax = None
        self.animation = None
        
        # LP Model and solution storage
        self.lp_model = None
        self.solution_status = None
        self.objective_value = None
        
    def add_depot(self, x: float, y: float, supply: Supply, name: str = '') -> Depot:
        '''Add a supply depot to the problem'''
        depot = Depot(len(self.depots), x, y, name, supply)
        self.depots.append(depot)
        return depot
    
    def add_destination(self, x: float, y: float, demand: Supply, 
                       priority: Priority = Priority.MEDIUM, name: str = '') -> Destination:
        '''Add a destination requiring supplies'''
        dest = Destination(
            len(self.destinations), x, y, name, 
            demand, Supply(), priority
        )
        self.destinations.append(dest)
        return dest
    
    def add_drone(self, x: float, y: float, capacity: int, 
                  max_range: float, speed: float = 50.0) -> Drone:
        '''Add a delivery drone to the fleet'''
        drone = Drone(len(self.drones), x, y, capacity, max_range, speed)
        self.drones.append(drone)
        return drone
    
    def create_sample_scenario(self):
        '''Create a sample disaster scenario for testing the LP model'''
        print('Creating sample disaster scenario...')
        
        # Add main depot with abundant supplies
        depot = self.add_depot(50, 50, Supply(1000, 800, 200), 'Emergency Supply Depot')
        print(f'Added depot at ({depot.x}, {depot.y}) with {depot.supply.total()} total supplies')
        
        # Add affected locations with varying priorities and demands
        locations = [
            (150, 100, Supply(80, 60, 20), Priority.HIGH, 'Hospital Complex'),
            (80, 180, Supply(60, 40, 15), Priority.MEDIUM, 'Residential Zone A'),
            (200, 150, Supply(90, 70, 25), Priority.HIGH, 'School Evacuation Center'),
            (180, 220, Supply(40, 30, 10), Priority.LOW, 'Commercial District'),
            (120, 250, Supply(70, 50, 18), Priority.MEDIUM, 'Community Center'),
            (220, 80, Supply(45, 35, 12), Priority.MEDIUM, 'Residential Zone B')
        ]
        
        for x, y, demand, priority, name in locations:
            dest = self.add_destination(x, y, demand, priority, name)
            print(f"Added destination '{name}' at ({x}, {y}) with demand {demand.total()} (Priority: {priority.name})")
        
        # Add drone fleet with different capacities and ranges
        drone_configs = [
            (100, 200, 'Heavy Lift Drone'),    # High capacity, medium range
            (80, 220, 'Medium Drone'),         # Medium capacity, good range  
            (60, 180, 'Light Drone'),          # Lower capacity, shorter range
            (120, 240, 'Long Range Drone'),    # High capacity, long range
            (90, 200, 'Versatile Drone')       # Balanced specifications
        ]
        
        depot_x, depot_y = depot.x, depot.y
        for i, (capacity, max_range, drone_type) in enumerate(drone_configs):
            drone = self.add_drone(depot_x, depot_y, capacity, max_range, speed=50)
            print(f'Added {drone_type} {i+1}: capacity={capacity}, range={max_range}')
    
    def solve_transportation_lp(self) -> List[DeliveryAssignment]:
        '''
        Solve the drone delivery problem using Linear Programming with PuLP
        
        This method formulates and solves a Mixed Integer Linear Program (MILP) to find
        the optimal assignment of drones to delivery routes.
        
        Returns:
            List of optimal delivery assignments
        '''
        if not self.depots or not self.destinations or not self.drones:
            print('ERROR: Cannot solve - missing depots, destinations, or drones')
            return []
        
        print(f'\n=== FORMULATING LINEAR PROGRAM ===')
        print(f'Problem size: {len(self.drones)} drones, {len(self.depots)} depots, {len(self.destinations)} destinations')
        
        # Create the LP problem instance
        self.lp_model = pulp.LpProblem('Drone_Delivery_Optimization', pulp.LpMinimize)
        
        # ==================== DECISION VARIABLES ====================
        
        # Binary variables: y[d,i,j] = 1 if drone d delivers from depot i to destination j
        # This is the main assignment variable
        y = {}
        for d in range(len(self.drones)):
            for i in range(len(self.depots)):
                for j in range(len(self.destinations)):
                    # Only create variables for feasible routes (within drone range)
                    if self.drones[d].can_reach(self.destinations[j], self.depots[i]):
                        y[d,i,j] = pulp.LpVariable(f'assign_drone_{d}_depot_{i}_dest_{j}', 
                                                 cat='Binary')
        
        # Continuous variables: x[d,i,j,s] = amount of supply type s delivered by drone d from depot i to destination j
        # These variables represent the actual cargo carried
        supply_types = ['food', 'water', 'medicine']
        x = {}
        for d in range(len(self.drones)):
            for i in range(len(self.depots)):
                for j in range(len(self.destinations)):
                    if (d,i,j) in y:  # Only for feasible routes
                        for s in supply_types:
                            x[d,i,j,s] = pulp.LpVariable(f'supply_{s}_drone_{d}_depot_{i}_dest_{j}', 
                                                       lowBound=0, cat='Continuous')
        
        # Slack variables for unmet demand (soft constraints)
        # These allow the model to be feasible even if not all demand can be satisfied
        unmet_demand = {}
        for j in range(len(self.destinations)):
            for s in supply_types:
                unmet_demand[j,s] = pulp.LpVariable(f'unmet_{s}_dest_{j}', 
                                                  lowBound=0, cat='Continuous')
        
        print(f'Created {len(y)} binary assignment variables')
        print(f'Created {len(x)} continuous supply variables') 
        print(f'Created {len(unmet_demand)} slack variables for unmet demand')
        
        # ==================== OBJECTIVE FUNCTION ====================
        
        # Minimize: Total weighted transportation cost + penalty for unmet demand
        objective_terms = []
        
        # Transportation costs: distance * priority_weight * assignment
        for d in range(len(self.drones)):
            for i in range(len(self.depots)):
                for j in range(len(self.destinations)):
                    if (d,i,j) in y:
                        distance = self.depots[i].distance_to(self.destinations[j])
                        priority_weight = self.priority_weights[self.destinations[j].priority]
                        cost = distance * priority_weight
                        objective_terms.append(cost * y[d,i,j])
        
        # Penalty for unmet demand (encourages maximum satisfaction)
        for j in range(len(self.destinations)):
            for s in supply_types:
                penalty_weight = self.unmet_demand_penalty * self.priority_weights[self.destinations[j].priority]
                objective_terms.append(penalty_weight * unmet_demand[j,s])
        
        # Set the objective function
        self.lp_model += pulp.lpSum(objective_terms), 'Total_Weighted_Cost'
        print(f'Objective function has {len(objective_terms)} terms')
        
        # ==================== CONSTRAINTS ====================
        
        constraint_count = 0
        
        # CONSTRAINT 1: Each drone can be assigned to at most one route
        # Σ_i Σ_j y[d,i,j] ≤ 1 for all drones d
        for d in range(len(self.drones)):
            assignments_for_drone = []
            for i in range(len(self.depots)):
                for j in range(len(self.destinations)):
                    if (d,i,j) in y:
                        assignments_for_drone.append(y[d,i,j])
            
            if assignments_for_drone:  # Only add constraint if drone has feasible routes
                self.lp_model += pulp.lpSum(assignments_for_drone) <= 1, f'One_Assignment_Per_Drone_{d}'
                constraint_count += 1
        
        print(f'Added {len(self.drones)} drone assignment constraints')
        
        # CONSTRAINT 2: Drone capacity constraints
        # Σ_s x[d,i,j,s] ≤ capacity[d] * y[d,i,j] for all feasible (d,i,j)
        for d in range(len(self.drones)):
            drone = self.drones[d]
            for i in range(len(self.depots)):
                for j in range(len(self.destinations)):
                    if (d,i,j) in y:
                        total_cargo = []
                        for s in supply_types:
                            if (d,i,j,s) in x:
                                total_cargo.append(x[d,i,j,s])
                        
                        if total_cargo:
                            self.lp_model += (pulp.lpSum(total_cargo) <= 
                                            drone.capacity * y[d,i,j]), f'Capacity_Drone_{d}_Route_{i}_{j}'
                            constraint_count += 1
        
        print(f'Added capacity constraints (total: {constraint_count})')
        
        # CONSTRAINT 3: Supply availability at depots
        # Σ_d Σ_j x[d,i,j,s] ≤ available_supply[i,s] for all depots i and supply types s
        for i in range(len(self.depots)):
            depot = self.depots[i]
            supply_amounts = {'food': depot.supply.food, 'water': depot.supply.water, 'medicine': depot.supply.medicine}
            
            for s in supply_types:
                supply_used = []
                for d in range(len(self.drones)):
                    for j in range(len(self.destinations)):
                        if (d,i,j,s) in x:
                            supply_used.append(x[d,i,j,s])
                
                if supply_used:
                    self.lp_model += (pulp.lpSum(supply_used) <= 
                                    supply_amounts[s]), f'Supply_Availability_Depot_{i}_{s}'
                    constraint_count += 1
        
        print(f'Added supply availability constraints (total: {constraint_count})')
        
        # CONSTRAINT 4: Demand satisfaction (soft constraint with slack variables)
        # Σ_d Σ_i x[d,i,j,s] + unmet_demand[j,s] = demand[j,s] for all destinations j and supply types s
        for j in range(len(self.destinations)):
            dest = self.destinations[j]
            demand_amounts = {'food': dest.demand.food, 'water': dest.demand.water, 'medicine': dest.demand.medicine}
            
            for s in supply_types:
                supply_delivered = []
                for d in range(len(self.drones)):
                    for i in range(len(self.depots)):
                        if (d,i,j,s) in x:
                            supply_delivered.append(x[d,i,j,s])
                
                # Demand = Delivered + Unmet
                if supply_delivered:
                    self.lp_model += (pulp.lpSum(supply_delivered) + unmet_demand[j,s] == 
                                    demand_amounts[s]), f'Demand_Balance_Dest_{j}_{s}'
                else:
                    # If no delivery possible, all demand is unmet
                    self.lp_model += unmet_demand[j,s] == demand_amounts[s], f'Demand_Balance_Dest_{j}_{s}'
                constraint_count += 1
        
        print(f'Added demand satisfaction constraints (total: {constraint_count})')
        
        # CONSTRAINT 5: Logical constraint linking assignment and supply variables
        # x[d,i,j,s] ≤ M * y[d,i,j] where M is a large number (Big-M constraint)
        # This ensures that supplies can only be delivered if the route is assigned
        M = 1000  # Big-M constant (should be larger than any possible supply amount)
        
        for d in range(len(self.drones)):
            for i in range(len(self.depots)):
                for j in range(len(self.destinations)):
                    if (d,i,j) in y:
                        for s in supply_types:
                            if (d,i,j,s) in x:
                                self.lp_model += x[d,i,j,s] <= M * y[d,i,j], f'BigM_Drone_{d}_Route_{i}_{j}_{s}'
                                constraint_count += 1
        
        print(f'Added logical linking constraints (total: {constraint_count})')
        print(f'Final LP model has {constraint_count} constraints')
        
        # ==================== SOLVE THE LINEAR PROGRAM ====================
        
        print(f'\n=== SOLVING LINEAR PROGRAM ===')
        print("Using PuLP's default solver (CBC)...")
        
        # Solve the problem
        start_time = time()
        self.lp_model.solve(pulp.PULP_CBC_CMD(msg=1))  # msg=1 shows solver output
        solve_time = time() - start_time
        
        # Check solution status
        self.solution_status = pulp.LpStatus[self.lp_model.status]
        print(f'\nSolution Status: {self.solution_status}')
        print(f'Solve Time: {solve_time:.2f} seconds')
        
        if self.lp_model.status != pulp.LpStatusOptimal:
            print(f'ERROR: Problem not solved optimally! Status: {self.solution_status}')
            return []
        
        # Get objective value
        self.objective_value = pulp.value(self.lp_model.objective)
        print(f'Optimal Objective Value: {self.objective_value:.2f}')
        
        # ==================== EXTRACT SOLUTION ====================
        
        print(f'\n=== EXTRACTING SOLUTION ===')
        assignments = []
        
        # Extract assignments from binary variables
        for d in range(len(self.drones)):
            for i in range(len(self.depots)):
                for j in range(len(self.destinations)):
                    if (d,i,j) in y and pulp.value(y[d,i,j]) > 0.5:  # Binary variable is 1
                        
                        # Extract supply amounts for this assignment
                        delivered_supply = Supply()
                        for s in supply_types:
                            if (d,i,j,s) in x:
                                amount = pulp.value(x[d,i,j,s])
                                if amount > 0.01:  # Avoid numerical errors
                                    if s == 'food':
                                        delivered_supply.food = int(round(amount))
                                    elif s == 'water':
                                        delivered_supply.water = int(round(amount))
                                    elif s == 'medicine':
                                        delivered_supply.medicine = int(round(amount))
                        
                        # Calculate assignment cost and distance
                        distance = self.depots[i].distance_to(self.destinations[j])
                        priority_weight = self.priority_weights[self.destinations[j].priority]
                        cost = distance * priority_weight
                        
                        # Create assignment object
                        assignment = DeliveryAssignment(
                            drone_id=d,
                            depot_id=i, 
                            destination_id=j,
                            supply=delivered_supply,
                            cost=cost,
                            distance=distance,
                            priority_weight=priority_weight
                        )
                        
                        assignments.append(assignment)
                        print(f'Assignment: Drone {d} -> Depot {i} -> Destination {j}')
                        print(f'  Supplies: Food={delivered_supply.food}, Water={delivered_supply.water}, Medicine={delivered_supply.medicine}')
                        print(f'  Distance: {distance:.1f}, Cost: {cost:.2f}')
        
        # Print unmet demand analysis
        print(f'\n=== UNMET DEMAND ANALYSIS ===')
        total_unmet = 0
        for j in range(len(self.destinations)):
            dest = self.destinations[j]
            dest_unmet = 0
            unmet_details = {}
            
            for s in supply_types:
                unmet_amount = pulp.value(unmet_demand[j,s])
                if unmet_amount > 0.01:
                    unmet_details[s] = int(round(unmet_amount))
                    dest_unmet += unmet_amount
            
            if dest_unmet > 0:
                total_unmet += dest_unmet
                print(f'Destination {j} ({dest.name}): {unmet_details} unmet')
            else:
                print(f'Destination {j} ({dest.name}): Fully satisfied')
        
        print(f'Total unmet demand across all destinations: {total_unmet:.1f}')
        satisfaction_rate = (1 - total_unmet / sum(dest.demand.total() for dest in self.destinations)) * 100
        print(f'Overall satisfaction rate: {satisfaction_rate:.1f}%')
        
        return assignments
    
    def execute_assignments(self, assignments: List[DeliveryAssignment]):
        '''Execute the delivery assignments by updating drone and destination states'''
        print(f'\n=== EXECUTING {len(assignments)} ASSIGNMENTS ===')
        
        self.assignments = assignments
        
        for assignment in assignments:
            # Update drone state
            drone = self.drones[assignment.drone_id]
            destination = self.destinations[assignment.destination_id]
            
            drone.status = DroneStatus.DELIVERING
            drone.target = destination
            drone.cargo = assignment.supply
            drone.assignment = assignment
            
            # Update destination satisfied supplies
            destination.satisfied = destination.satisfied + assignment.supply
            
            print(f'Drone {assignment.drone_id} assigned to deliver {assignment.supply.total()} supplies to {destination.name}')
    
    def get_performance_metrics(self) -> Dict[str, float]:
        '''Calculate comprehensive performance metrics'''
        if not self.assignments:
            return {'error': 'No assignments to analyze'}
        
        # Cost metrics
        total_cost = sum(assignment.cost for assignment in self.assignments)
        total_distance = sum(assignment.distance for assignment in self.assignments)
        avg_cost_per_assignment = total_cost / len(self.assignments) if self.assignments else 0
        
        # Satisfaction metrics
        total_demand = sum(dest.demand.total() for dest in self.destinations)
        total_satisfied = sum(dest.satisfied.total() for dest in self.destinations)
        satisfaction_rate = (total_satisfied / total_demand * 100) if total_demand > 0 else 0
        
        # Priority-based satisfaction
        high_priority_satisfaction = 0
        high_priority_demand = 0
        for dest in self.destinations:
            if dest.priority == Priority.HIGH:
                high_priority_demand += dest.demand.total()
                high_priority_satisfaction += dest.satisfied.total()
        
        high_priority_rate = (high_priority_satisfaction / high_priority_demand * 100) if high_priority_demand > 0 else 0
        
        # Drone utilization
        active_drones = sum(1 for drone in self.drones if drone.status != DroneStatus.IDLE)
        utilization_rate = (active_drones / len(self.drones) * 100) if self.drones else 0
        
        # Supply type analysis
        supply_breakdown = {'food': 0, 'water': 0, 'medicine': 0}
        for assignment in self.assignments:
            supply_breakdown['food'] += assignment.supply.food
            supply_breakdown['water'] += assignment.supply.water
            supply_breakdown['medicine'] += assignment.supply.medicine
        
        return {
            'total_cost': total_cost,
            'total_distance': total_distance,
            'avg_cost_per_assignment': avg_cost_per_assignment,
            'satisfaction_rate': satisfaction_rate,
            'high_priority_satisfaction_rate': high_priority_rate,
            'active_drones': active_drones,
            'total_drones': len(self.drones),
            'utilization_rate': utilization_rate,
            'total_assignments': len(self.assignments),
            'supply_delivered': supply_breakdown,
            'objective_value': self.objective_value or 0,
            'solution_status': self.solution_status or 'Unknown'
        }
    
    def print_detailed_status(self):
        '''Print comprehensive status report'''
        print(f"\n{'='*60}")
        print(f'DRONE DELIVERY OPTIMIZATION RESULTS')
        print(f"{'='*60}")
        
        metrics = self.get_performance_metrics()
        
        if 'error' in metrics:
            print(f"ERROR: {metrics['error']}")
            return
        
        # Solution quality
        print(f'\nSOLUTION QUALITY:')
        print(f"  Status: {metrics['solution_status']}")
        print(f"  Objective Value: {metrics['objective_value']:.2f}")
        print(f"  Total Assignments: {metrics['total_assignments']}")
        
        # Cost analysis
        print(f'\nCOST ANALYSIS:')
        print(f"  Total Cost: {metrics['total_cost']:.2f}")
        print(f"  Total Distance: {metrics['total_distance']:.1f}")
        print(f"  Average Cost per Assignment: {metrics['avg_cost_per_assignment']:.2f}")
        
        # Satisfaction analysis
        print(f'\nSATISFACTION ANALYSIS:')
        print(f"  Overall Satisfaction Rate: {metrics['satisfaction_rate']:.1f}%")
        print(f"  High Priority Satisfaction Rate: {metrics['high_priority_satisfaction_rate']:.1f}%")
        
        # Resource utilization
        print(f'\nRESOURCE UTILIZATION:')
        print(f"  Active Drones: {metrics['active_drones']}/{metrics['total_drones']}")
        print(f"  Drone Utilization Rate: {metrics['utilization_rate']:.1f}%")
        
        # Supply delivery breakdown
        print(f'\nSUPPLY DELIVERY BREAKDOWN:')
        supply_delivered = metrics['supply_delivered']
        print(f"  Food: {supply_delivered['food']} units")
        print(f"  Water: {supply_delivered['water']} units") 
        print(f"  Medicine: {supply_delivered['medicine']} units")
        print(f"  Total Delivered: {sum(supply_delivered.values())} units")
        
        # Detailed destination status
        print(f'\nDESTINATION STATUS:')
        for i, dest in enumerate(self.destinations):
            sat_rate = dest.satisfaction_rate() * 100
            demand_total = dest.demand.total()
            satisfied_total = dest.satisfied.total()
            status = '✓ SATISFIED' if sat_rate >= 99 else '⚠ PARTIAL' if sat_rate >= 50 else '✗ UNSATISFIED'
            
            print(f"  {i+1}. {dest.name or f'Destination {i}'}")
            print(f'     Satisfaction: {sat_rate:.1f}% ({satisfied_total}/{demand_total}) {status}')
            print(f'     Priority: {dest.priority.name}')
            print(f'     Demand: Food={dest.demand.food}, Water={dest.demand.water}, Medicine={dest.demand.medicine}')
            print(f'     Satisfied: Food={dest.satisfied.food}, Water={dest.satisfied.water}, Medicine={dest.satisfied.medicine}')
        
        # Assignment details
        print(f'\nASSIGNMENT DETAILS:')
        for i, assignment in enumerate(self.assignments):
            drone = self.drones[assignment.drone_id]
            depot = self.depots[assignment.depot_id]
            dest = self.destinations[assignment.destination_id]
            
            print(f"  {i+1}. Drone {assignment.drone_id} -> {dest.name or f'Destination {assignment.destination_id}'}")
            print(f'     Route: Depot {assignment.depot_id} -> Destination {assignment.destination_id}')
            print(f'     Distance: {assignment.distance:.1f}, Cost: {assignment.cost:.2f}')
            print(f'     Cargo: Food={assignment.supply.food}, Water={assignment.supply.water}, Medicine={assignment.supply.medicine}')
    
    def run_optimization(self):
        '''Run the complete optimization process'''
        print('='*80)
        print('DRONE DELIVERY LINEAR PROGRAMMING OPTIMIZATION')
        print('='*80)
        
        # Step 1: Validate problem setup
        if not self.depots:
            print('ERROR: No depots defined!')
            return
        if not self.destinations:
            print('ERROR: No destinations defined!')
            return
        if not self.drones:
            print('ERROR: No drones defined!')
            return
        
        print(f'Problem Setup Validated:')
        print(f'  Depots: {len(self.depots)}')
        print(f'  Destinations: {len(self.destinations)}')
        print(f'  Drones: {len(self.drones)}')
        
        # Step 2: Solve the Linear Programming problem
        assignments = self.solve_transportation_lp()
        
        if not assignments:
            print('No feasible solution found!')
            return
        
        # Step 3: Execute assignments
        self.execute_assignments(assignments)
        
        # Step 4: Display results
        self.print_detailed_status()
        
        return assignments
    
    def analyze_problem_feasibility(self):
        '''Analyze the feasibility of the problem before solving'''
        print(f'\n=== FEASIBILITY ANALYSIS ===')
        
        # Check total supply vs total demand
        total_supply = sum(depot.supply.total() for depot in self.depots)
        total_demand = sum(dest.demand.total() for dest in self.destinations)
        
        print(f'Total Supply Available: {total_supply}')
        print(f'Total Demand Required: {total_demand}')
        print(f'Supply/Demand Ratio: {total_supply/total_demand:.2f}' if total_demand > 0 else 'N/A')
        
        # Check drone reachability
        reachable_routes = 0
        total_possible_routes = len(self.drones) * len(self.depots) * len(self.destinations)
        
        for drone in self.drones:
            for depot in self.depots:
                for dest in self.destinations:
                    if drone.can_reach(dest, depot):
                        reachable_routes += 1
        
        reachability_rate = (reachable_routes / total_possible_routes * 100) if total_possible_routes > 0 else 0
        print(f'Reachable Routes: {reachable_routes}/{total_possible_routes} ({reachability_rate:.1f}%)')
        
        # Check capacity constraints
        total_drone_capacity = sum(drone.capacity for drone in self.drones)
        print(f'Total Drone Capacity: {total_drone_capacity}')
        print(f'Capacity/Demand Ratio: {total_drone_capacity/total_demand:.2f}' if total_demand > 0 else 'N/A')
        
        # Identify potential bottlenecks
        print(f'\nPOTENTIAL BOTTLENECKS:')
        if total_supply < total_demand:
            print(f'  ⚠ Supply shortage: {total_demand - total_supply} units short')
        if total_drone_capacity < total_demand:
            print(f'  ⚠ Capacity shortage: Need {total_demand - total_drone_capacity} more capacity')
        if reachability_rate < 50:
            print(f'  ⚠ Range limitations: Only {reachability_rate:.1f}% of routes are reachable')
        
        return {
            'total_supply': total_supply,
            'total_demand': total_demand,
            'total_capacity': total_drone_capacity,
            'reachable_routes': reachable_routes,
            'reachability_rate': reachability_rate
        }
    
    def generate_optimization_report(self) -> str:
        '''Generate a comprehensive optimization report'''
        metrics = self.get_performance_metrics()
        feasibility = self.analyze_problem_feasibility()
        
        report = f"""
{'='*80}
DRONE DELIVERY OPTIMIZATION REPORT
{'='*80}

PROBLEM CONFIGURATION:
  Depots: {len(self.depots)}
  Destinations: {len(self.destinations)} 
  Drones: {len(self.drones)}
  
FEASIBILITY ANALYSIS:
  Total Supply Available: {feasibility['total_supply']}
  Total Demand Required: {feasibility['total_demand']}
  Total Drone Capacity: {feasibility['total_capacity']}
  Reachable Routes: {feasibility['reachable_routes']} ({feasibility['reachability_rate']:.1f}%)

OPTIMIZATION RESULTS:
  Solution Status: {metrics.get('solution_status', 'Unknown')}
  Objective Value: {metrics.get('objective_value', 0):.2f}
  Total Assignments: {metrics.get('total_assignments', 0)}
  
PERFORMANCE METRICS:
  Overall Satisfaction Rate: {metrics.get('satisfaction_rate', 0):.1f}%
  High Priority Satisfaction: {metrics.get('high_priority_satisfaction_rate', 0):.1f}%
  Drone Utilization: {metrics.get('utilization_rate', 0):.1f}%
  Total Cost: {metrics.get('total_cost', 0):.2f}
  Total Distance: {metrics.get('total_distance', 0):.1f}

SUPPLY DELIVERY:
  Food: {metrics.get('supply_delivered', {}).get('food', 0)} units
  Water: {metrics.get('supply_delivered', {}).get('water', 0)} units  
  Medicine: {metrics.get('supply_delivered', {}).get('medicine', 0)} units

DESTINATION ANALYSIS:
"""
        
        for i, dest in enumerate(self.destinations):
            sat_rate = dest.satisfaction_rate() * 100
            report += f'  {i+1}. {dest.name}: {sat_rate:.1f}% satisfied ({dest.satisfied.total()}/{dest.demand.total()}) - {dest.priority.name}\n'
        
        report += f'\nASSIGNMENT DETAILS:\n'
        for i, assignment in enumerate(self.assignments):
            dest_name = self.destinations[assignment.destination_id].name
            report += f'  {i+1}. Drone {assignment.drone_id} -> {dest_name} '
            report += f'(Distance: {assignment.distance:.1f}, Cost: {assignment.cost:.2f})\n'
        
        return report


def create_complex_disaster_scenario():
    '''Create a more complex disaster scenario for advanced testing'''
    optimizer = DroneDeliveryLPOptimizer()
    
    print('Creating complex multi-depot disaster scenario...')
    
    # Multiple supply depots with different supply profiles
    optimizer.add_depot(50, 50, Supply(400, 300, 80), 'Main Emergency Depot')
    optimizer.add_depot(200, 80, Supply(200, 150, 50), 'Secondary Supply Point') 
    optimizer.add_depot(120, 200, Supply(300, 200, 40), 'Forward Operating Base')
    
    # Diverse affected locations
    disaster_locations = [
        # High priority locations (hospitals, shelters)
        (150, 100, Supply(100, 80, 30), Priority.HIGH, 'City Hospital'),
        (180, 150, Supply(120, 90, 35), Priority.HIGH, 'Emergency Shelter A'),
        (90, 180, Supply(80, 60, 25), Priority.HIGH, 'Medical Center'),
        
        # Medium priority locations (residential, community centers)
        (220, 120, Supply(70, 50, 15), Priority.MEDIUM, 'Residential District 1'),
        (160, 220, Supply(90, 70, 20), Priority.MEDIUM, 'Community Center'),
        (110, 250, Supply(60, 45, 18), Priority.MEDIUM, 'Residential District 2'),
        (250, 180, Supply(75, 55, 22), Priority.MEDIUM, 'School Evacuation Site'),
        
        # Lower priority locations
        (200, 250, Supply(40, 30, 8), Priority.LOW, 'Commercial Zone'),
        (80, 120, Supply(50, 35, 12), Priority.LOW, 'Industrial Area'),
        (260, 220, Supply(45, 30, 10), Priority.LOW, 'Suburban Area')
    ]
    
    for x, y, demand, priority, name in disaster_locations:
        optimizer.add_destination(x, y, demand, priority, name)
    
    # Heterogeneous drone fleet
    drone_fleet = [
        # Heavy lift drones (high capacity, shorter range)
        (150, 180, 'Heavy Lifter 1'),
        (140, 190, 'Heavy Lifter 2'), 
        
        # Long range drones (medium capacity, long range)
        (100, 220, 'Long Range 1'),
        (110, 230, 'Long Range 2'),
        (120, 240, 'Long Range 3'),
        
        # Fast response drones (lower capacity, fast, medium range)
        (80, 200, 'Fast Response 1'),
        (90, 210, 'Fast Response 2'),
        (100, 200, 'Fast Response 3')
    ]
    
    # Add drones with different capabilities
    depot_positions = [(50, 50), (200, 80), (120, 200)]
    
    for i, (capacity, max_range, drone_name) in enumerate(drone_fleet):
        # Distribute drones across depots
        depot_idx = i % len(depot_positions)
        depot_x, depot_y = depot_positions[depot_idx]
        
        if 'Heavy' in drone_name:
            optimizer.add_drone(depot_x, depot_y, capacity=120, max_range=150, speed=40)
        elif 'Long Range' in drone_name:
            optimizer.add_drone(depot_x, depot_y, capacity=80, max_range=250, speed=50)
        else:  # Fast Response
            optimizer.add_drone(depot_x, depot_y, capacity=60, max_range=180, speed=70)
    
    return optimizer


def main():
    '''Main function demonstrating the Linear Programming optimization'''
    
    print('DRONE DELIVERY OPTIMIZATION USING LINEAR PROGRAMMING')
    print('Developed using PuLP - Python Linear Programming Library')
    print('='*80)
    
    # Test 1: Simple scenario
    print('\n1. TESTING SIMPLE SCENARIO')
    print('-' * 40)
    
    simple_optimizer = DroneDeliveryLPOptimizer()
    simple_optimizer.create_sample_scenario()
    simple_optimizer.analyze_problem_feasibility()
    assignments = simple_optimizer.run_optimization()
    
    # Test 2: Complex scenario
    print('\n\n2. TESTING COMPLEX MULTI-DEPOT SCENARIO')
    print('-' * 50)
    
    complex_optimizer = create_complex_disaster_scenario()
    complex_optimizer.analyze_problem_feasibility()
    complex_assignments = complex_optimizer.run_optimization()
    
    # Comparison
    print('\n\n3. SCENARIO COMPARISON')
    print('-' * 30)
    
    simple_metrics = simple_optimizer.get_performance_metrics()
    complex_metrics = complex_optimizer.get_performance_metrics()
    
    print(f'Simple Scenario:')
    print(f"  Satisfaction Rate: {simple_metrics.get('satisfaction_rate', 0):.1f}%")
    print(f"  Total Cost: {simple_metrics.get('total_cost', 0):.2f}")
    print(f"  Drone Utilization: {simple_metrics.get('utilization_rate', 0):.1f}%")
    
    print(f"\nComplex Scenario:")
    print(f"  Satisfaction Rate: {complex_metrics.get('satisfaction_rate', 0):.1f}%")
    print(f"  Total Cost: {complex_metrics.get('total_cost', 0):.2f}")
    print(f"  Drone Utilization: {complex_metrics.get('utilization_rate', 0):.1f}%")
    
    # Generate detailed reports
    print('\n\n4. GENERATING DETAILED REPORTS')
    print('-' * 40)
    
    simple_report = simple_optimizer.generate_optimization_report()
    complex_report = complex_optimizer.generate_optimization_report()
    
    print('Simple Scenario Report:')
    print(simple_report)
    
    print('\n' + '='*80)
    print('Complex Scenario Report:')
    print(complex_report)
    
    print('\n' + '='*80)
    print('OPTIMIZATION COMPLETE')
    print('='*80)


if __name__ == '__main__':
    # Check if PuLP is installed
    try:
        import pulp
        print('PuLP library detected - proceeding with optimization')
        main()
    except ImportError:
        print('ERROR: PuLP library not found!')
        print('Please install PuLP using: pip install pulp')
        print('PuLP is required for Linear Programming optimization')
