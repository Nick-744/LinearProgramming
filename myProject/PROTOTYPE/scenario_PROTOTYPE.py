# scenario.py

from models_PROTOTYPE import Supply, Priority, Drone, Depot, Destination

def sample_scenario():
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
