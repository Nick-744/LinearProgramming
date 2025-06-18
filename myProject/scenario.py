# scenario.py

from models import Supply, Priority, Drone, Depot, Destination

def sample_scenario():
    drones = [
        Drone(0, 0, 0, 100, 300, 50),
        Drone(1, 0, 0, 80, 250, 60),
        Drone(2, 0, 0, 120, 350, 40)
    ]

    depots = [Depot(0, 0, 0, 'Depot', Supply(100, 80, 30))]

    dests = [
        Destination(0, 50, 50,  'Hospital',  Supply(40, 30, 10), priority = Priority.HIGH),
        Destination(1, 80, 60,  'Community', Supply(50, 40, 20), priority = Priority.MEDIUM),
        Destination(2, 100, 80, 'School',    Supply(30, 20, 10), priority = Priority.LOW),
        Destination(3, 70, 30,  'Clinic',    Supply(20, 10, 5),  priority = Priority.HIGH),
    ]

    print('-> Πληροφορίες για το δοκιμαστικό σενάριο:')
    for drone in drones:
        print(drone)
    for dest in dests:
        print(dest)
    
    return (drones, depots, dests);
