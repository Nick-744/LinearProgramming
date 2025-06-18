# scenario.py

from models import Supply, Priority, Drone, Depot, Destination

# Για να δημιουργηθεί 1 σενάριο, καλό θα
# ήταν να χρησιμοποιηθεί η δομή που ακολουθεί:
def sample_scenario():
    drones = [
        Drone(0, 0, 0, 100, 300, 50),
        Drone(1, 0, 0,  80, 250, 60),
        Drone(2, 0, 0, 120, 350, 40)
    ]

    depots = [Depot(0, 0, 0, 'Depot', Supply(100, 80, 50))]

    dests = [
        Destination(0,  50, 50,  'Hospital', Supply(40, 30, 10), priority = Priority.HIGH  ),
        Destination(1,  80, 60, 'Community', Supply(50, 40, 20), priority = Priority.MEDIUM),
        Destination(2, 100, 80,    'School', Supply(30, 20, 10), priority = Priority.LOW   ),
        Destination(3,  70, 30,    'Clinic', Supply(20, 10,  5), priority = Priority.HIGH  )
    ]

    print_scenario_info(drones, depots, dests)
    
    return (drones, depots, dests);

def big_city_scenario():
    drones = [
        Drone(0, 33.6, 48.6, 120, 300, 60),
        Drone(1, 96.7, 42.4, 100, 280, 55),
        Drone(2, 33.6, 48.6, 150, 350, 50)
    ]

    depots = [
        Depot(0, 33.6, 48.6, 'Depot #1', Supply(120, 100, 80)),
        Depot(1, 96.1, 42.4, 'Depot #2', Supply(100,  90, 70))
    ]

    dests = [
        Destination(
            0,   9.5, 26.5,     'Stadium', Supply(40, 30, 10), priority=Priority.MEDIUM
        ),
        Destination(
            1,  18.6, -6.6,      'School', Supply(30, 20, 10), priority=Priority.HIGH
        ),
        Destination(
            2,  -0.6,   70,      'Clinic', Supply(25, 15, 15), priority=Priority.HIGH
        ),
        Destination(
            3,  72.5, 66.8, 'Hospital #1', Supply(50, 40, 25), priority=Priority.HIGH
        ),
        Destination(
            4, 102.5, 68.9,    'Resident', Supply(60, 50, 30), priority=Priority.LOW
        ),
        Destination(
            5,  94.1, 14.6, 'Hospital #2', Supply(45, 35, 20), priority=Priority.MEDIUM
        )
    ]

    print_scenario_info(drones, depots, dests)

    return (drones, depots, dests);

# --- Helpers ---
def print_scenario_info(drones: list[Drone],
                        depots: list[Depot],
                        dests:  list[Destination]) -> None:
    ''' Βοηθητική συνάρτηση για την εκτύπωση πληροφοριών σεναρίου. '''

    print('-> Πληροφορίες για το δοκιμαστικό σενάριο:')
    for depot in depots:
        print(depot)
    for drone in drones:
        print(drone)
    for dest in dests:
        print(dest)

    return;
