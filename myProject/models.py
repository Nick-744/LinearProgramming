# models.py

from dataclasses import dataclass, field
from enum import Enum
import math

# Προσεγγίζει αρκετά την λογική που χρησιμοποιούμε στον προγραμματισμό με C!
class Priority(Enum):
    HIGH   = 1
    MEDIUM = 2
    LOW    = 3

class DroneStatus(Enum):
    IDLE       = 'idle'
    DELIVERING = 'delivering'
    RETURNING  = 'returning'

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
    supply: Supply = field(default_factory = Supply)

@dataclass
class Destination(Location):
    ''' Κλάση σημείου ανάγκης - κληρονομεί από Location '''
    demand:    Supply   = field(default_factory = Supply)
    satisfied: Supply   = field(default_factory = Supply)
    priority:  Priority = Priority.MEDIUM

    def sat_rate(self) -> float:
        tot = self.demand.total()
        return 1 if tot == 0 else self.satisfied.total() / tot;

@dataclass
class Drone:
    ''' Κλάση δρόνος - αναπαράσταση του αποστολέα '''
    id:       int
    x:        float
    y:        float
    capacity: int
    range:    float
    speed:    float
    status:   DroneStatus = DroneStatus.IDLE

    def can_reach(self, depot: Depot, dest: Destination) -> bool:
        return depot.dist(dest) * 2 <= self.range;

@dataclass
class Assignment:
    ''' Αντιπροσωπεύει μία λύση του προβλήματος, δρόνος -> αποστολή/ανάθεση '''
    drone_id: int
    depot_id: int
    dest_id:  int
    supply:   Supply
    distance: float
    cost:     float
