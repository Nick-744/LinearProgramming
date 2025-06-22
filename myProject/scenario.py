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
        Drone(0,  40.0, 23.0, 120, 300, 60),
        Drone(1, 115.0, 17.0, 100, 280, 55),
        Drone(2,  40.0, 23.0, 150, 350, 50)
    ]

    depots = [
        Depot(0,  40.0, 23.0, 'Depot #1', Supply(120, 100, 80)),
        Depot(1, 115.0, 17.0, 'Depot #2', Supply(100,  90, 70))
    ]

    dests = [
        Destination(
            0,   9.5,   2.0,     'Stadium', Supply(40, 30, 10), priority = Priority.MEDIUM
        ),
        Destination(
            1,  31.0, -20.5,      'School', Supply(30, 20, 10), priority = Priority.HIGH
        ),
        Destination(
            2,  -1.8,  45.0,      'Clinic', Supply(25, 15, 15), priority = Priority.HIGH
        ),
        Destination(
            3,  87.0,  40.0, 'Hospital #1', Supply(50, 40, 25), priority = Priority.HIGH
        ),
        Destination(
            4, 120.0,  51.0,    'Resident', Supply(60, 50, 30), priority = Priority.LOW
        ),
        Destination(
            5,  93.0, -14.5, 'Hospital #2', Supply(45, 35, 20), priority = Priority.MEDIUM
        )
    ]

    print_scenario_info(drones, depots, dests)

    return (drones, depots, dests);

def silent_hill_scenario():
    drones = [
        Drone(0, 68, -78,  50,  50, 50),
        Drone(1, 68, -78, 100,  70, 60),
        Drone(2, 83, -20, 140, 120, 70)
    ]

    depots = [
        Depot(0, 68, -78, 'Depot - Obs. Deck', Supply(100, 120, 80)),
        Depot(1, 83, -20, 'Depot - Old SH   ',    Supply( 50,  30, 20))
    ]

    dests = [
        Destination(
            0, 41.6, -46.6,    'Lakeview', Supply(50, 40,  20), priority = Priority.HIGH
        ),
        Destination(
            1, 52.1, -26.9,     'Midwich', Supply(60, 50, 40), priority = Priority.HIGH
        ),
        Destination(
            2, 42.5, -73.2,  'Brookhaven', Supply( 0, 60, 50), priority = Priority.HIGH
        ),
        Destination(
            3, 80.2, -58.6, 'Overlook P.', Supply(10, 30, 20), priority = Priority.LOW
        ),
        Destination(
            4, 95.0, -46.2,   'Town Hall', Supply(30, 20, 10), priority = Priority.HIGH
        ),
        Destination(
            5, 67.5, -31.5, 'Old Town H.', Supply(20, 10,  5), priority = Priority.LOW
        ),
        Destination(
            6, 88.3, -74.7, "St. Maria's", Supply(25, 15, 10), priority = Priority.HIGH
        ),
        Destination(
            7, 38.0, -65.0,  'Historical', Supply(40, 30, 20), priority = Priority.MEDIUM
        )
    ]

    print_scenario_info(drones, depots, dests)

    return (drones, depots, dests);

def raccoon_city_scenario():
    drones = [
        Drone(0,  48.5, -42.6, 100, 300, 60),
        Drone(1, -37.8, 109.4, 120, 350, 70),
        Drone(2,     0,   -45, 150, 400, 80)
    ]

    depots = [Depot(0, 0, -45, 'RPD', Supply(200, 150, 100))]

    dests = [
        Destination(
            0,  -6.0,   120, 'R.C. Hospital', Supply(40, 30, 20), priority = Priority.HIGH
        ),
        Destination(
            1,  -5.6,  -100,    "Jack's Bar", Supply(30, 20, 10), priority = Priority.MEDIUM
        ),
        Destination(
            2, -81.6, -71.6,   'Sport Stad.', Supply(60, 50, 40), priority = Priority.LOW
        ),
        Destination(
            3, 100.0,   -20,  'R.C. E Elem.', Supply(30, 20, 10), priority = Priority.MEDIUM
        ),
        Destination(
            4, -76.0,  10.8,     'West Park', Supply(20, 10,  5), priority = Priority.HIGH
        ),
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
