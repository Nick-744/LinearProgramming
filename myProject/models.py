# models.py

from dataclasses import dataclass, field
from typing import List, Tuple
from enum import Enum
import math

class Priority(Enum):
    HIGH   = 1
    MEDIUM = 2
    LOW    = 3

class DroneStatus(Enum):
    IDLE       = 'idle'
    DELIVERING = 'delivering'
    RETURNING  = 'returning'
    # Προστέθηκε CHARGING για υποστήριξη επαναφόρτισης, καθώς πλέον τα drones
    # μπορούν να εκτελούν πολλαπλές αποστολές (multi-trip λειτουργία)!
    CHARGING   = 'charging'

# Νέα κλάση ώστε να υποστηρίζεται η διαχείριση διαφορετικών τύπων καταστροφών
class DisasterType(Enum):
    FIRE       = 'fire'
    FLOOD      = 'flood'
    EARTHQUAKE = 'earthquake'

@dataclass
class Supply:
    ''' Κλάση διαχείρισης προμηθειών '''
    food:     int = 0
    water:    int = 0
    medicine: int = 0

    def total(self) -> int:
        return self.food + self.water + self.medicine;

    def __add__(self, other: 'Supply') -> 'Supply':
        return Supply(self.food     + other.food,
                      self.water    + other.water,
                      self.medicine + other.medicine);

    def __sub__(self, other: 'Supply') -> 'Supply':
        return Supply(max(0, self.food     - other.food),
                      max(0, self.water    - other.water),
                      max(0, self.medicine - other.medicine));

    def to_dict(self) -> dict:
        return {
            'food':     self.food,
            'water':    self.water,
            'medicine': self.medicine
        };

    def is_zero(self) -> bool:
        return self.total() == 0;

@dataclass
class Location:
    ''' Γενική κλάση τοποθεσίας - ρόλος γονέα '''
    id:   int
    x:    float
    y:    float
    name: str = ''

    def dist(self, other: 'Location') -> float:
        # Ευκλείδεια απόσταση
        return math.hypot(self.x - other.x, self.y - other.y);

@dataclass
class Depot(Location):
    ''' Κλάση σημείου εφοδιασμού - κληρονομεί από Location '''
    supply:       Supply = field(default_factory = Supply)
    max_supply:   Supply = field(default_factory = Supply) # Αρχικά διαθέσιμες προμήθειες
    loading_time: float  = 5. # Χρόνος φόρτωσης σε λεπτά

    def can_supply(self, requested: Supply) -> bool:
        ''' Έλεγχος αν το depot μπορεί να καλύψει τη ζητούμενη ποσότητα '''
        return (
            self.supply.food >= requested.food and
            self.supply.water >= requested.water and
            self.supply.medicine >= requested.medicine
        );

    def consume_supply(self, consumed: Supply) -> None:
        ''' Μείωση διαθέσιμων προμηθειών! '''
        self.supply = self.supply - consumed
        
        return;

@dataclass
class Destination(Location):
    ''' Κλάση σημείου ανάγκης - κληρονομεί από Location '''
    demand:         Supply   = field(default_factory = Supply)
    satisfied:      Supply   = field(default_factory = Supply)
    priority:       Priority = Priority.MEDIUM
    time_window:    Tuple[float, float] = (0, 1440) # (start, end) σε λεπτά
    urgency_factor: float = 1. # Πολλαπλασιαστής για επείγουσες ανάγκες!
    accessibility:  float = 1. # 0-1, 1 = πλήρως προσβάσιμο

    def sat_rate(self) -> float:
        tot = self.demand.total()

        return 1 if tot == 0 else self.satisfied.total() / tot;

    def remaining_demand(self) -> Supply:
        ''' Υπολογισμός υπολειπόμενης ζήτησης '''
        return self.demand - self.satisfied;

    def is_fully_satisfied(self) -> bool:
        # 95% κάλυψη θεωρείται πλήρης πρακτικά
        return self.sat_rate() >= 0.95;

    def update_urgency(self, current_time: float) -> None:
        ''' Ενημέρωση του urgency factor βάσει χρόνου '''
        if current_time > self.time_window[1]:
            self.urgency_factor = min(
                3., 1. + (current_time - self.time_window[1]) / 60.
            )
        elif current_time > self.time_window[0]:
            # Εντός time window - κανονική κατάσταση
            self.urgency_factor = 1.

        return;

@dataclass
class Drone:
    ''' Κλάση δρόνος - αναπαράσταση του αποστολέα '''
    id:           int
    x:            float
    y:            float
    capacity:     int
    range:        float
    speed:        float
    status:       DroneStatus = DroneStatus.IDLE
    battery:      float       = 100.  # Ποσοστό μπαταρίας
    total_trips:  int         = 0     # Συνολικές αποστολές
    current_load: Supply      = field(default_factory = Supply)

    def can_reach(self, depot: Depot, dest: Destination) -> bool:
        # Βασικός έλεγχος εμβέλειας + έλεγχος προσβασιμότητας
        total_dist = depot.dist(dest) * 2 # Πήγαινε - έλα

        return (
            total_dist <= self.range and 
            dest.accessibility > 0.5 and
            self.battery >= self.min_battery_for_trip(total_dist)
        );

    def min_battery_for_trip(self, distance: float) -> float:
        ''' Ελάχιστη μπαταρία που χρειάζεται για μια αποστολή '''
        #                                    + 10% ρεζερβ
        return (distance / self.range) * 100 + 10;

    def travel_time(self, depot: Depot, dest: Destination) -> float:
        ''' Χρόνος ταξιδιού σε λεπτά (πήγαινε - έλα + φόρτωση) '''
        return (depot.dist(dest) * 2 / self.speed) * 60 + depot.loading_time;

    def can_carry(self, supply: Supply) -> bool:
        ''' Έλεγχος αν ο δρόνος μπορεί να μεταφέρει τη συγκεκριμένη ποσότητα '''
        return supply.total() <= self.capacity;

@dataclass
class Assignment:
    ''' Αντιπροσωπεύει μία λύση του προβλήματος, δρόνος -> αποστολή/ανάθεση '''
    drone_id:    int
    depot_id:    int
    dest_id:     int
    supply:      Supply
    distance:    float
    cost:        float
    trip_number: int   = 0  # Αριθμός διαδρομής (για πολλαπλές αποστολές)
    start_time:  float = 0. # Χρόνος έναρξης αποστολής
    end_time:    float = 0. # Χρόνος ολοκλήρωσης

@dataclass
class DisasterState:
    ''' Κατάσταση καταστροφής για δυναμικό περιβάλλον '''
    time_step:      int
    disaster_type:  DisasterType
    affected_areas: List[Tuple[float, float, float]] # (x, y, radius)
    blocked_routes: List[Tuple[int, int]]            # (depot_id, dest_id)
    new_demands:    List[Destination] = field(default_factory = list)
    weather_factor: float = 1. # Επηρεάζει την ταχύτητα των drones, ίσως λίγο υπερβολικό...

    def is_route_blocked(self, depot_id: int, dest_id: int) -> bool:
        return (depot_id, dest_id) in self.blocked_routes;

    def affects_location(self, location: Location) -> bool:
        ''' Έλεγχος αν η τοποθεσία επηρεάζεται από την καταστροφή '''
        temp = False
        for (ax, ay, radius) in self.affected_areas:
            if math.hypot(location.x - ax, location.y - ay) <= radius:
                temp = True
                break;
        
        return temp;

@dataclass
class ScenarioMetrics:
    ''' Μετρικές αξιολόγησης για ένα scenario '''
    total_distance:         float = 0.
    total_cost:             float = 0.
    avg_satisfaction:       float = 0.
    high_priority_coverage: float = 0.
    total_delivery_time:    float = 0.
    drones_utilized:        int   = 0
    unmet_demand_penalty:   float = 0.

    def calculate_efficiency_score(self) -> float:
        ''' Υπολογισμός συνολικού score αποδοτικότητας '''
        # Καλύτερο score = υψηλότερη κάλυψη, χαμηλότερο κόστος
        satisfaction_score = self.avg_satisfaction * 100
        priority_score     = self.high_priority_coverage * 50
        efficiency_penalty = (self.total_cost / 1000) if self.total_cost > 0 else 0
        
        return max(0, satisfaction_score + priority_score - efficiency_penalty);

@dataclass 
class MultiTripAssignment:
    ''' Αναπαράσταση πολλαπλών αποστολών για έναν δρόνο '''
    drone_id:    int
    assignments: List[Assignment] = field(default_factory = list)
    total_time:  float = 0.
    total_cost:  float = 0.

    def add_assignment(self, assignment: Assignment) -> None:
        self.assignments.append(assignment)
        self.total_cost += assignment.cost
        # Υπολογισμός συνολικού χρόνου
        if self.assignments:
            assignment.trip_number = len(self.assignments)
            if len(self.assignments) == 1:
                assignment.start_time = 0.
            else:
                prev_assignment = self.assignments[-2]
                #                                                + 10 λεπτά αν τύχει κάτι...
                assignment.start_time = prev_assignment.end_time + 10

        return;
        
    def can_add_assignment(self,
                           new_assignment:  Assignment, 
                          max_mission_time: float = 480.) -> bool:
        ''' Έλεγχος αν μπορεί να προστεθεί νέα αποστολή '''
        estimated_time = (
            self.total_time + new_assignment.end_time - new_assignment.start_time
        )

        return estimated_time <= max_mission_time;
