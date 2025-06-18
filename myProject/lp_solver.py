# lp_solver.py

from models import Drone, Depot, Destination, Supply, Priority, Assignment
from typing import List
import pulp

# Global Μεταβλητές
supply_types  = ['food', 'water', 'medicine']

# Συντελεστής βαρύτητας ανά προτεραιότητα – ΜΕΓΑΛΥΤΕΡΟ νούμερο = ΥΨΗΛΟΤΕΡΗ προτεραιότητα.
# Δεν έχει καμία σχέση με τα .value του Enum (HIGH=1, MEDIUM=2, LOW=3).
priority_w    = {Priority.HIGH: 3., Priority.MEDIUM: 2., Priority.LOW: 1.}

BIG_M         = 10_000
UNMET_PENALTY = 1_000

def build_model(drones: List[Drone],
                depots: List[Depot],
                dests:  List[Destination]) -> tuple:
    ''' Δημιουργία/Ορισμός του μαθηματικού μοντέλου [MILP] για το πρόβλημα '''
    model = pulp.LpProblem('DroneDelivery', pulp.LpMinimize) # Πρόβλημα ελαχιστοποίησης

    # Δημιουργία τριπλέτων (drone_id, depot_id, destination_id) ΜΟΝΟ αν ο δρόνος
    # μπορεί να φτάσει στον προορισμό και να επιστρέψει [βάσει εμβέλειας]!
    routes = [
        (d.id, i.id, j.id) for d in drones for i in depots for j in dests 
        if d.can_reach(i, j)
    ]
    # Δυαδική ανάθεση αποστολής σε δρόνο - Μεταβλητή y
    y = {r: pulp.LpVariable(f'y_{r[0]}_{r[1]}_{r[2]}', cat = 'Binary') for r in routes}
    # Ποσότητα προμηθειών που μεταφέρεται βάση συγκεκριμένης αποστολής - Μεταβλητή x
    x = {
        (d, i, j, s): pulp.LpVariable(f'x_{s}_{d}_{i}_{j}', lowBound = 0)
        for (d, i, j) in routes for s in supply_types
    }
    # Ποσότητα προμηθειών που δεν καλύπτεται από τις αποστολές - Slack Var unmet
    unmet = {
        (j.id, s): pulp.LpVariable(f'unmet_{s}_{j.id}', lowBound = 0)
        for j in dests for s in supply_types
    }

    # --- Αντικειμενική συνάρτηση ---
    ''' -> Ο στόχος μας:
    Ελαχιστοποίηση του μεταφορικού κόστους (απόσταση x προτεραιότητα x ανάθεση),
    με ποινή φυσικά για unmet demand! '''
    model += (
        pulp.lpSum(
            depots[i].dist(dests[j]) * priority_w[dests[j].priority] * y[d, i, j]
            for (d, i, j) in routes
        ) +
        pulp.lpSum(
            UNMET_PENALTY * priority_w[j.priority] * unmet[j.id, s]
            for j in dests for s in supply_types
        )
    )

    # --- Οι περιορισμοί ---

    # Χωρητικότητα δρόνου - περιορίζουμε το συνολικό
    # φορτίο ανά δρόνο [λόγω πολλαπλών αποστολών]!
    for d in drones:
        model += (
            pulp.lpSum(
                x[d.id, i, j, s] for (drone_id, i, j) in routes if drone_id == d.id
                for s in supply_types
            ) <= d.capacity
        )

    # Διαθέσιμη προμήθεια στα σημεία εφοδιασμού
    for i in depots:
        for s in supply_types:
            model += (
                pulp.lpSum(
                    x[d, i.id, j, s] for (d, dep, j) in routes if dep == i.id
                ) <= getattr(i.supply, s)
            )

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
            cost = dist * priority_w[dests[j].priority]

            # Δημιουργία της ανάθεσης
            assignments.append(Assignment(d, i, j, sup, dist, cost))

            # Ενημέρωση της ποσότητας που καλύφθηκε στον προορισμό!
            dests[j].satisfied = dests[j].satisfied + sup
    
    return assignments;
