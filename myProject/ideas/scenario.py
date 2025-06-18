# scenario.py

from models import (Supply, Priority, Drone, Depot, Destination)
from typing import List, Tuple
import random

def sample_scenario():
    ''' Το αρχικό σενάριο - διατηρείται για συμβατότητα '''
    drones = [
        Drone(0, 0, 0, 100, 300, 50),
        Drone(1, 0, 0, 80, 250, 60)
    ]

    depots = [Depot(0, 0, 0, 'Depot', Supply(150, 120, 60))]

    dests = [
        Destination(0, 50, 50, 'Hospital',  Supply(40, 30, 10), priority = Priority.HIGH),
        Destination(1, 80, 60, 'Community', Supply(50, 40, 20), priority = Priority.MEDIUM)
    ]
    
    return (drones, depots, dests);

def extended_scenario():
    ''' Εκτεταμένο σενάριο με περισσότερα στοιχεία '''
    drones = [
        Drone(0,  0,  0, 120, 400, 60), # Μεγάλος drone
        Drone(1,  0,  0,  80, 300, 70), # Μεσαίος drone  
        Drone(2,  0,  0,  60, 250, 80), # Μικρός γρήγορος
        Drone(3, 10, 10, 100, 350, 55), # Εφεδρικός drone
    ]

    depots = [
        Depot(0, 0, 0, 'Main Depot', Supply(300, 250, 150)),
        Depot(1, 100, 20, 'Secondary Depot', Supply(200, 180, 80)),
    ]

    dests = [
        Destination(0, 50, 50, 'Hospital',          Supply(60, 40, 25), 
                   priority = Priority.HIGH,   time_window = (0, 120)),
        Destination(1, 80, 60, 'School',            Supply(40, 60, 15), 
                   priority = Priority.HIGH,   time_window = (0, 180)),
        Destination(2, 120, 30, 'Community Center', Supply(80, 70, 30), 
                   priority = Priority.MEDIUM, time_window = (0, 300)),
        Destination(3, 150, 80, 'Elderly Home',     Supply(30, 25, 40), 
                   priority = Priority.HIGH,   time_window = (0, 90)),
        Destination(4, 90, 120, 'Shelter A',        Supply(100, 80, 20), 
                   priority = Priority.MEDIUM, time_window = (60, 360)),
        Destination(5, 180, 100, 'Remote Village',  Supply(70, 90, 35), 
                   priority = Priority.LOW,    time_window = (120, 480)),
    ]
    
    return (drones, depots, dests);

def earthquake_scenario():
    ''' Σενάριο σεισμού με υψηλή ζήτηση ιατρικών προμηθειών '''
    drones = [
        Drone(0, 20, 20, 100, 350, 55),
        Drone(1, 20, 20, 85, 280, 65),
        Drone(2, 20, 20, 70, 220, 75),
    ]

    depots = [
        Depot(0, 20, 20, 'Emergency Depot', Supply(200, 150, 200)), # Περισσότερα φάρμακα
    ]

    dests = [
        Destination(0, 70, 80, 'Main Hospital',  Supply(50, 30, 60), 
                   priority = Priority.HIGH,   urgency_factor = 1.5),
        Destination(1, 120, 60, 'Field Hospital', Supply(30, 20, 40), 
                   priority = Priority.HIGH,   urgency_factor = 1.8),
        Destination(2, 90, 120, 'Rescue Center',  Supply(40, 50, 30), 
                   priority = Priority.MEDIUM, urgency_factor = 1.2),
        Destination(3, 160, 90, 'Damaged Area',  Supply(60, 80, 45), 
                   priority = Priority.HIGH,   urgency_factor = 2.0, accessibility = 0.7),
    ]
    
    return (drones, depots, dests);

def flood_scenario():
    ''' Σενάριο πλημμύρας με υψηλή ζήτηση τροφίμων και νερού '''
    drones = [
        Drone(0,  0,  0, 150, 400, 50), # Drone μεγάλης χωρητικότητας
        Drone(1,  0,  0, 120, 350, 55),
        Drone(2, 10, 10, 100, 300, 60),
        Drone(3, 10, 10,  80, 250, 70),
    ]

    depots = [
        Depot(0, 0, 0, 'Relief Center', Supply(400, 500, 100)), # Πολλά τρόφιμα/νερό
        Depot(1, 150, 0, 'Supply Point', Supply(300, 350, 50)),
    ]

    dests = [
        Destination(0, 80, 100, 'Evacuation Center',  Supply(120, 150, 20), 
                   priority = Priority.HIGH),
        Destination(1, 120, 80, 'Stranded Community', Supply(100, 120, 15), 
                   priority = Priority.HIGH,   accessibility = 0.6),
        Destination(2, 200, 120, 'Isolated Village',  Supply(80, 100, 25), 
                   priority = Priority.MEDIUM, accessibility = 0.4),
        Destination(3, 60, 150, 'Temporary Shelter',  Supply(90, 110, 30), 
                   priority = Priority.MEDIUM),
        Destination(4, 180, 60, 'Emergency Station',  Supply(60, 70, 40), 
                   priority = Priority.LOW),
    ]
    
    return (drones, depots, dests);

def generate_random_scenario(
    num_drones:       int = 4, 
    num_depots:       int = 2, 
    num_destinations: int = 6,
    area_size:        int = 200,
    seed:             int = None
) -> Tuple[List[Drone], List[Depot], List[Destination]]:
    ''' Δημιουργία τυχαίου σεναρίου για δοκιμές '''
    
    if seed is not None:
        random.seed(seed)
    
    # Δημιουργία drones
    drones = []
    for i in range(num_drones):
        x = random.uniform(0, area_size * 0.2) # Κοντά στην αρχή
        y = random.uniform(0, area_size * 0.2)
        capacity    = random.randint(60, 150)
        drone_range = random.uniform(250, 450)
        speed       = random.uniform(45, 80)
        
        drones.append(Drone(i, x, y, capacity, drone_range, speed))
    
    # Δημιουργία depots
    depots = []
    for i in range(num_depots):
        x = random.uniform(0, area_size * 0.3)
        y = random.uniform(0, area_size * 0.3)
        
        # Τυχαία διανομή προμηθειών
        total_supply = random.randint(300, 600)
        food     = random.randint(int(total_supply * 0.3), int(total_supply * 0.5))
        water    = random.randint(int(total_supply * 0.3), int(total_supply * 0.5))
        medicine = total_supply - food - water
        medicine = max(medicine, int(total_supply * 0.1)) # Τουλάχιστον 10% φάρμακα
        
        supply = Supply(food, water, medicine)
        depots.append(Depot(i, x, y, f'Depot_{i}', supply))
    
    # Δημιουργία destinations
    destinations   = []
    priorities     = [Priority.HIGH, Priority.MEDIUM, Priority.LOW]
    location_types = ['Hospital', 'School', 'Community', 'Shelter', 'Village', 'Center']
    
    for i in range(num_destinations):
        # Τυχαία κατανομή στην περιοχή
        x = random.uniform(area_size * 0.2, area_size)
        y = random.uniform(area_size * 0.2, area_size)
        
        # Τυχαία ζήτηση
        total_demand = random.randint(50, 200)
        food     = random.randint(int(total_demand * 0.2), int(total_demand * 0.6))
        water    = random.randint(int(total_demand * 0.2), int(total_demand * 0.6))
        medicine = total_demand - food - water
        medicine = max(medicine, int(total_demand * 0.1))
        
        demand = Supply(food, water, medicine)
        priority = random.choice(priorities)
        location_type = random.choice(location_types)
        
        # Time windows βάσει προτεραιότητας
        if priority == Priority.HIGH:
            time_window = (0, random.randint(90, 180))
        elif priority == Priority.MEDIUM:
            time_window = (0, random.randint(180, 360))
        else:
            time_window = (0, random.randint(300, 480))
        
        accessibility = random.uniform(0.6, 1.0) if priority != Priority.LOW else random.uniform(0.4, 0.9)
        
        destinations.append(Destination(
            i, x, y, f'{location_type}_{i}', demand, 
            priority=priority, time_window=time_window, accessibility=accessibility
        ))
    
    return (drones, depots, destinations);
