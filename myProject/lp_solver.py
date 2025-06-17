# lp_solver.py

from models import (
    Drone, Depot, Destination, Supply, Priority, Assignment, 
    DisasterState, ScenarioMetrics, MultiTripAssignment
)
from typing import List, Dict
import pulp

# Global Μεταβλητές
supply_types        = ['food', 'water', 'medicine']
priority_w          = {Priority.HIGH: 0.5, Priority.MEDIUM: 1., Priority.LOW: 1.5}
BIG_M               = 10_000
UNMET_PENALTY       = 1_000
MAX_TRIPS_PER_DRONE = 3    # Μέγιστες αποστολές ανά δρόνο
MAX_MISSION_TIME    = 480. # 8 ώρες αποστολής

# CORE MODEL: Βασικό πρόβλημα μεταφοράς - copy/paste PROTOTYPE
# =========================================================================================
def build_model(drones: List[Drone],
                depots: List[Depot],
                dests:  List[Destination]) -> tuple:
    ''' Δημιουργία/Ορισμός του μαθηματικού μοντέλου [MILP] για το πρόβλημα '''
    model = pulp.LpProblem('DroneDelivery', pulp.LpMinimize) # Πρόβλημα ελαχιστοποίησης

    # Δημιουργία τριπλέτων (drone_id, depot_id, destination_id) ΜΟΝΟ αν ο δρόνος
    # μπορεί να φτάσει στον προορισμό και να επιστρέψει [βάσει εμβέλειας]!
    routes = [(d.id, i.id, j.id)
              for d in drones for i in depots for j in dests
              if d.can_reach(i, j)]
    # Δυαδική ανάθεση αποστολής σε δρόνο - Μεταβλητή y
    y = {r: pulp.LpVariable(f'y_{r[0]}_{r[1]}_{r[2]}', cat = 'Binary') for r in routes}
    # Ποσότητα προμηθειών που μεταφέρεται βάση συγκεκριμένης αποστολής - Μεταβλητή x
    x = {(d, i, j, s): pulp.LpVariable(f'x_{s}_{d}_{i}_{j}', lowBound = 0)
         for (d, i, j) in routes for s in supply_types}
    # Ποσότητα προμηθειών που δεν καλύπτεται από τις αποστολές - Slack Var unmet
    unmet = {(j.id, s): pulp.LpVariable(f'unmet_{s}_{j.id}', lowBound = 0)
             for j in dests for s in supply_types}

    # --- Αντικειμενική συνάρτηση ---
    ''' -> Ο στόχος μας:
    Ελαχιστοποίηση του μεταφορικού κόστους (απόσταση x προτεραιότητα x ανάθεση),
    με ποινή φυσικά για unmet demand! '''
    model += (
        pulp.lpSum(
            depots[i].dist(dests[j]) * priority_w[dests[j].priority] * 
            dests[j].urgency_factor * y[d, i, j]
            for (d, i, j) in routes
        ) +
        pulp.lpSum(UNMET_PENALTY * priority_w[j.priority] * 
                   j.urgency_factor * unmet[j.id, s]
                   for j in dests for s in supply_types)
    )

    # --- Οι περιορισμοί ---
    # Για κάθε δρόνο => 1 αποστολή MAX
    for d in drones:
        model += pulp.lpSum(y[r] for r in routes if r[0] == d.id) <= 1

    # Χωρητικότητα δρόνου
    for (d, i, j) in routes:
        model += (pulp.lpSum(x[d, i, j, s] for s in supply_types) <= \
                  drones[d].capacity * y[d, i, j])

    # Διαθέσιμη προμήθεια στα σημεία εφοδιασμού
    for i in depots:
        for s in supply_types:
            model += (pulp.lpSum(x[d, i.id, j, s]
                                for (d, dep, j) in routes if dep == i.id
                      ) <= getattr(i.supply, s))

    # Ισορροπία ζήτησης σε κάθε σημείο ανάγκης
    for j in dests:
        for s in supply_types:
            delivered = pulp.lpSum(x[d, i, j.id, s] for (d, i, dj) in routes if dj == j.id)
            model    += delivered + unmet[j.id, s] == getattr(j.demand, s)

    # Big‑M
    for (d, i, j) in routes:
        for s in supply_types:
            # - Θέλουμε: Να επιτρέπεται μη μηδενική ποσότητα x[...] μόνο
            # όταν y = 1! Επομένως, καταφεύγουμε σε Big-M τεχνική!
            model += x[d, i, j, s] <= BIG_M * y[d, i, j]
            # Δηλαδή, αν και μόνο αν χρησιμοποιείται ένα route,
            # τότε να επιτρέπεται να σταλούν προμήθειες σε αυτό.

    return (model, y, x, unmet);

def solve(drones: List[Drone],
          depots: List[Depot],
          dests:  List[Destination]) -> List[Assignment]:
    ''' Λύση του προβλήματος με χρήση του Pulp '''
    (model, y, x, _) = build_model(drones, depots, dests)

    # Δεν μου αρέσει να εμφανίζει τις πληροφορίες από τον solver => msg = 0
    model.solve(pulp.PULP_CBC_CMD(msg = 0)) 

    if pulp.LpStatus[model.status] != 'Optimal':
        raise RuntimeError('Δεν βρέθηκε βέλτιστη λύση!');

    assignments = []
    for ((d, i, j), var) in y.items():
        if var.value() > 0.5: # Εφικτή αποστολή
            sup  = Supply(**{s: int(round(x[d, i, j, s].value())) for s in supply_types})
            dist = depots[i].dist(dests[j])

            # Όσο πιο σημαντικός ο προορισμός, τόσο χαμηλότερο το κόστος ανά μονάδα
            cost = dist * priority_w[dests[j].priority] * dests[j].urgency_factor

            # Δημιουργία της ανάθεσης
            assignment            = Assignment(d, i, j, sup, dist, cost)
            assignment.start_time = 0.
            assignment.end_time   = drones[d].travel_time(depots[i], dests[j])
            assignments.append(assignment)

            # Ενημέρωση της ποσότητας που καλύφθηκε στον προορισμό!
            dests[j].satisfied = dests[j].satisfied + sup
    
    return assignments;

# ADVANCED EXTENSION: Μοντέλο με πολλαπλές αποστολές
# =========================================================================================
def build_multi_trip_model(drones:    List[Drone],
                           depots:    List[Depot], 
                           dests:     List[Destination],
                           max_trips: int = MAX_TRIPS_PER_DRONE) -> tuple:
    ''' Μοντέλο για πολλαπλές αποστολές ανά δρόνο '''
    model = pulp.LpProblem('MultiTripDroneDelivery', pulp.LpMinimize)
    
    # Δημιουργία routes για κάθε trip
    routes = [(d.id, i.id, j.id, t)
              for d in drones for i in depots for j in dests
              for t in range(max_trips)
              if d.can_reach(i, j)]
    
    # Μεταβλητές
    y = {r: pulp.LpVariable(f'y_{r[0]}_{r[1]}_{r[2]}_{r[3]}', cat='Binary') 
         for r in routes}
    x = {(d, i, j, t, s): pulp.LpVariable(f'x_{s}_{d}_{i}_{j}_{t}', lowBound = 0)
         for (d, i, j, t) in routes for s in supply_types}
    unmet = {(j.id, s): pulp.LpVariable(f'unmet_{s}_{j.id}', lowBound = 0)
             for j in dests for s in supply_types}
    
    # --- Αντικειμενική συνάρτηση ---
    model += (
        pulp.lpSum(
            depots[i].dist(dests[j]) * priority_w[dests[j].priority] * 
            dests[j].urgency_factor * y[d, i, j, t]
            for (d, i, j, t) in routes
        ) +
        pulp.lpSum(UNMET_PENALTY * priority_w[j.priority] * 
                   j.urgency_factor * unmet[j.id, s]
                   for j in dests for s in supply_types)
    )
    
    # --- Οι περιορισμοί ---
    # Χρονικός περιορισμός ανά δρόνο
    for d in drones:
        total_time = pulp.lpSum(
            drones[d].travel_time(depots[i], dests[j]) * y[d, i, j, t]
            for (drone_id, i, j, t) in routes if drone_id == d
        )
        model += total_time <= MAX_MISSION_TIME
    
    # Σειριακότητα trips (trip t+1 μόνο αν έχει γίνει trip t)
    for d in drones:
        for t in range(1, max_trips):
            current_trips = pulp.lpSum(
                y[d, i, j, t] for (drone_id, i, j, trip) in routes 
                if drone_id == d and trip == t
            )
            prev_trips = pulp.lpSum(
                y[d, i, j, t-1] for (drone_id, i, j, trip) in routes 
                if drone_id == d and trip == t-1
            )
            model += current_trips <= prev_trips
    
    # Υπόλοιποι περιορισμοί όπως πριν, με επέκταση για trips
    for (d, i, j, t) in routes:
        model += (
            pulp.lpSum(x[d, i, j, t, s] for s in supply_types) <= 
            drones[d].capacity * y[d, i, j, t]
        )
    
    # Διαθέσιμη προμήθεια στα depots (συνολικά για όλα τα trips)
    for i in depots:
        for s in supply_types:
            model += (pulp.lpSum(x[d, i.id, j, t, s] 
                                for (d, dep, j, t) in routes if dep == i.id
                      ) <= getattr(i.supply, s))
    
    # Ισορροπία ζήτησης
    for j in dests:
        for s in supply_types:
            delivered = pulp.lpSum(
                x[d, i, j.id, t, s] for (d, i, dj, t) in routes if dj == j.id
            )
            model += delivered + unmet[j.id, s] == getattr(j.demand, s)
    
    # Big-M
    for (d, i, j, t) in routes:
        for s in supply_types:
            model += x[d, i, j, t, s] <= BIG_M * y[d, i, j, t]
    
    return (model, y, x, unmet);

def solve_multi_trip(drones:    List[Drone],
                     depots:    List[Depot],
                     dests:     List[Destination],
                     max_trips: int = MAX_TRIPS_PER_DRONE) -> List[MultiTripAssignment]:
    ''' Λύση με πολλαπλές αποστολές ανά δρόνο - Επέκταση λογικής του solve '''
    (model, y, x, _) = build_multi_trip_model(drones, depots, dests, max_trips)
    
    model.solve(pulp.PULP_CBC_CMD(msg = 0))
    
    if pulp.LpStatus[model.status] != 'Optimal':
        raise RuntimeError('Δεν βρέθηκε βέλτιστη λύση για multi-trip μοντέλο!');
    
    # Οργάνωση αποτελεσμάτων ανά δρόνο
    drone_assignments = {d.id: MultiTripAssignment(d.id) for d in drones}
    
    for ((d, i, j, t), var) in y.items():
        if var.value() > 0.5:
            sup = Supply(**{s: int(round(x[d, i, j, t, s].value())) 
                            for s in supply_types})
            dist = depots[i].dist(dests[j])
            cost = dist * priority_w[dests[j].priority] * dests[j].urgency_factor
            
            assignment = Assignment(d, i, j, sup, dist, cost, t)
            drone_assignments[d].add_assignment(assignment)
            
            # Ενημέρωση satisfaction
            dests[j].satisfied = dests[j].satisfied + sup
    
    return [ma for ma in drone_assignments.values() if ma.assignments];

def solve_dynamic(drones:          List[Drone],
                  depots:          List[Depot], 
                  dests:           List[Destination],
                  disaster_states: List[DisasterState],
                  time_horizon:    int = 10) -> Dict[int, List[Assignment]]:
    ''' *Δυναμικό μοντέλο που λύνει το πρόβλημα σε διαδοχικά time steps!!! '''
    all_assignments = {}
    
    for step in range(time_horizon):
        print(f'Λύση για χρονικό βήμα {step}...')
        
        # Ενημέρωση κατάστασης καταστροφής
        if step < len(disaster_states):
            current_state = disaster_states[step]
            update_scenario_with_disaster(drones, depots, dests, current_state)
        
        # Ενημέρωση urgency factors
        for dest in dests:
            dest.update_urgency(step * 60.) # Κάθε step = 1 ώρα
        
        # Λύση για το τρέχον step
        try:
            assignments = solve(drones, depots, dests)
            all_assignments[step] = assignments
            
            # Ενημέρωση καταστάσεων μετά τη λύση
            update_post_solution(drones, depots, assignments)
            
        except RuntimeError as e:
            print(f'Αδυναμία λύσης στο βήμα {step}: {e}')
            all_assignments[step] = []
    
    return all_assignments;

def update_scenario_with_disaster(drones:         List[Drone],
                                  dests:          List[Destination],
                                  disaster_state: DisasterState) -> None:
    ''' Ενημέρωση scenario βάσει κατάστασης καταστροφής '''
    
    # Ενημέρωση προσβασιμότητας προορισμών
    for dest in dests:
        if disaster_state.affects_location(dest):
            dest.accessibility *= 0.5 # Μείωση προσβασιμότητας
            # Αύξηση ζήτησης σε επηρεαζόμενες περιοχές
            dest.demand.medicine = int(dest.demand.medicine * 1.5)
    
    # Επηρεασμός ταχύτητας drones από καιρικές συνθήκες
    for drone in drones:
        drone.speed *= disaster_state.weather_factor
    
    # Προσθήκη νέων προορισμών αν υπάρχουν
    if disaster_state.new_demands:
        dests.extend(disaster_state.new_demands)

    return;

def update_post_solution(drones:      List[Drone],
                         depots:      List[Depot],
                         assignments: List[Assignment]) -> None:
    ''' Ενημέρωση μετά τη λύση (κατανάλωση προμηθειών, κατάσταση δρόνων) '''
    
    # Ενημέρωση depot supplies
    for assignment in assignments:
        depot = depots[assignment.depot_id]
        depot.consume_supply(assignment.supply)
    
    # Ενημέρωση drone status και μετρητών
    for assignment in assignments:
        drone = drones[assignment.drone_id]
        drone.total_trips += 1
        drone.battery -= drone.min_battery_for_trip(assignment.distance)
        drone.battery = max(0, drone.battery) # Δεν μπορεί να γίνει αρνητική!

    return;

# Αξιολόγηση σεναρίου και αναφορά αποτελεσμάτων
# ==========================================================================================
def calculate_scenario_metrics(assignments: List[Assignment],
                               dests:       List[Destination]) -> ScenarioMetrics:
    ''' Υπολογισμός μετρικών για την αξιολόγηση του scenario '''
    metrics = ScenarioMetrics()
    
    if not assignments:
        return metrics;
    
    # Βασικές μετρικές
    metrics.total_distance = sum(a.distance for a in assignments)
    metrics.total_cost = sum(a.cost for a in assignments)
    metrics.total_delivery_time = sum(a.end_time - a.start_time for a in assignments)
    metrics.drones_utilized = len(set(a.drone_id for a in assignments))
    
    # Μετρικές κάλυψης
    if dests:
        total_satisfaction = sum(d.sat_rate() for d in dests)
        metrics.avg_satisfaction = total_satisfaction / len(dests)
        
        high_priority_dests = [d for d in dests if d.priority == Priority.HIGH]
        if high_priority_dests:
            high_priority_satisfaction = sum(d.sat_rate() for d in high_priority_dests)
            metrics.high_priority_coverage = (
                high_priority_satisfaction / len(high_priority_dests)
            )
    
    # Ποινή για unmet demand
    for dest in dests:
        remaining = dest.remaining_demand()
        penalty_factor = priority_w[dest.priority] * dest.urgency_factor
        metrics.unmet_demand_penalty += remaining.total() * UNMET_PENALTY * penalty_factor
    
    return metrics;

def generate_detailed_report(assignments: List[Assignment],
                             dests: List[Destination], 
                             drones: List[Drone],
                             depots: List[Depot]) -> str:
    ''' Απλή αναφορά αποτελεσμάτων αποστολών '''

    metrics = calculate_scenario_metrics(assignments, dests, drones)
    report = []
    
    report.append("=" * 60)
    report.append("ΑΝΑΛΥΤΙΚΗ ΑΝΑΦΟΡΑ DRONE DELIVERY")
    report.append("=" * 60)

    # Γενικά στοιχεία
    report.append("\nΓΕΝΙΚΑ ΣΤΟΙΧΕΙΑ:")
    report.append(f" - Σύνολο drones: {len(drones)}")
    report.append(f" - Αποθήκες:      {len(depots)}")
    report.append(f" - Προορισμοί:    {len(dests)}")
    report.append(f" - Αποστολές:     {len(assignments)}")
    report.append(f" - Χρήση drones:  {metrics.drones_utilized}/{len(drones)}")

    # Απόδοση
    report.append("\nΜΕΤΡΙΚΕΣ:")
    report.append(f" - Συνολική απόσταση:      {metrics.total_distance:.2f} km")
    report.append(f" - Συνολικό κόστος:        {metrics.total_cost:.2f}")
    report.append(f" - Μέσος χρόνος παράδοσης: {metrics.total_delivery_time / max(1, len(assignments)):.1f} λεπτά")
    report.append(f" - Αποδοτικότητα:          {metrics.calculate_efficiency_score():.1f}")
    report.append(f" - Μέση κάλυψη:            {metrics.avg_satisfaction * 100:.1f}%")
    report.append(f" - Κάλυψη υψηλής προτεραιότητας: {metrics.high_priority_coverage * 100:.1f}%")

    # Προορισμοί
    report.append("\nΚΑΤΑΣΤΑΣΗ ΠΡΟΟΡΙΣΜΩΝ:")
    for dest in sorted(dests, key=lambda d: d.priority.value):
        status = "Πλήρης" if dest.is_fully_satisfied() else \
                 "Μερική" if dest.sat_rate() > 0.5 else "Ανεπαρκής"
        report.append(f" - {dest.name:<15} | {status:<10} | "
                      f"Κάλυψη:        {dest.sat_rate() * 100:5.1f}% | "
                      f"Ζήτηση:        {dest.demand.total():3d} | "
                      f"Εξυπηρετήθηκε: {dest.satisfied.total():3d}")

    # Χρήση drones
    report.append("\nΑΝΑΘΕΣΕΙΣ DRONES:")
    drone_usage = {}
    for a in assignments:
        drone_usage.setdefault(a.drone_id, []).append(a)

    for drone_id in sorted(drone_usage):
        drone = drones[drone_id]
        group = drone_usage[drone_id]
        total_dist = sum(a.distance for a in group)
        total_load = sum(a.supply.total() for a in group)
        report.append(f" - Drone  {drone_id}: {len(group)} αποστολές | "
                      f"Απόσταση: {total_dist:.1f} km | "
                      f"Φορτίο:   {total_load}/{drone.capacity} | "
                      f"Μπαταρία: {drone.battery:.1f}%")

    # Λεπτομέρειες αποστολών
    report.append("\nΛΕΠΤΟΜΕΡΕΙΕΣ ΑΠΟΣΤΟΛΩΝ:")
    for i, a in enumerate(sorted(assignments, key=lambda a: a.start_time), 1):
        depot = depots[a.depot_id]
        dest = dests[a.dest_id]
        report.append(f" {i:2d}. Drone {a.drone_id} | {depot.name} → {dest.name} | "
                      f"F:{a.supply.food} W:{a.supply.water} M:{a.supply.medicine} | "
                      f"{a.distance:.1f} km | Κόστος: {a.cost:.2f}")

    # Unmet demand
    if metrics.unmet_demand_penalty > 0:
        report.append("\nΑΝΙΚΑΝΟΠΟΙΗΤΗ ΖΗΤΗΣΗ:")
        report.append(f" - Συνολική ποινή: {metrics.unmet_demand_penalty:.2f}")
        for d in dests:
            rem = d.remaining_demand()
            if rem.total() > 0:
                report.append(f" - {d.name}: F:{rem.food}, W:{rem.water}, M:{rem.medicine}")

    report.append("\n" + "=" * 60)

    return "\n".join(report);
