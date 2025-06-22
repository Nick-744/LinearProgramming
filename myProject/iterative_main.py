# Demo - iterative_main.py (Iterative Solving)

from scenario import big_city_scenario, silent_hill_scenario
from models import Supply, Depot, Destination, Drone
from typing import List, Dict, Tuple
from lp_solver import solve
from time import time
import copy

def update_supplies_after_assignments(depots:      List[Depot],
                                      assignments: List) -> None:
    '''Ενημερώνει τις διαθέσιμες προμήθειες στα depots μετά από τις αναθέσεις'''
    for assignment in assignments:
        depot        = depots[assignment.depot_id]
        depot.supply = depot.supply - assignment.supply

    return;

def create_unsatisfied_destinations_with_mapping(
    dests: List[Destination]
) -> Tuple[List[Destination], Dict[int, int]]:
    '''
    Δημιουργεί λίστα με μη ικανοποιημένους προορισμούς και mapping των IDs

    Returns: (unsatisfied_destinations, mapping_new_to_original_id)
    '''
    unsatisfied = []
    id_mapping  = {}
    new_id      = 0
    
    for (original_id, dest) in enumerate(dests):
        remaining_demand = dest.demand - dest.satisfied
        if remaining_demand.total() > 0:
            # Δημιουργούμε νέο προορισμό με την υπολειπόμενη ζήτηση
            new_dest           = copy.deepcopy(dest)
            new_dest.id        = new_id # Νέο sequential ID
            new_dest.demand    = remaining_demand
            new_dest.satisfied = Supply() # Reset για την επόμενη επανάληψη
            
            unsatisfied.append(new_dest)
            id_mapping[new_id] = original_id # Mapping: νέο ID -> πρωτότυπο ID
            new_id            += 1
    
    return (unsatisfied, id_mapping);

def has_available_supplies(depots: List[Depot]) -> bool:
    '''Ελέγχει αν υπάρχουν ακόμη διαθέσιμες προμήθειες στα depots'''
    for depot in depots:
        if depot.supply.total() > 0:
            return True;

    return False;

def reset_drone_status(drones: List[Drone]) -> None:
    '''Επαναφέρει όλους τους δρόνους σε κατάσταση IDLE'''
    from models import DroneStatus
    for drone in drones:
        drone.status = DroneStatus.IDLE
    
    return;

def print_iteration_summary(iteration:      int,
                            assignments:    List,
                            original_dests: List[Destination], 
                            id_mapping:     Dict[int, int]) -> None:
    '''Εκτυπώνει περίληψη της επανάληψης'''
    print(f'\n=== ΕΠΑΝΑΛΗΨΗ {iteration} ===')
    
    if not assignments:
        print('Δεν βρέθηκαν εφικτές αναθέσεις σε αυτή την επανάληψη.')
        return;
    
    print(f'Αναθέσεις αποστολών (Επανάληψη {iteration}):')
    for a in assignments:
        # Χρησιμοποιούμε το mapping για να βρούμε το σωστό όνομα
        original_dest_id = id_mapping.get(a.dest_id, a.dest_id)
        if original_dest_id < len(original_dests):
            dest_name = original_dests[original_dest_id].name
        else:
            dest_name = f'Dest_{original_dest_id}'
            
        cargo = a.supply.to_dict()
        print(
            f'  Δρόνος {a.drone_id} -> {dest_name:<15} | Απόσταση: {a.distance:5.1f} '
            f"| Φορτίο: {cargo['food']:>3} τρόφιμα, {cargo['water']:>3} νερό, "
            f"{cargo['medicine']:>3} φάρμακα"
        )
    
    return;

def print_final_summary(all_assignments: List,
                        original_dests:  List[Destination], 
                        total_time:      float,
                        iterations:      int) -> None:
    '''Εκτυπώνει τελική περίληψη όλων των επαναλήψεων'''
    print(f'\n{"="*80}')
    print(f'- ΤΕΛΙΚΗ ΠΕΡΙΛΗΨΗ - {iterations} Επαναλήψεις')
    print(f'{"="*80}')
    print(f'Συνολικός χρόνος επίλυσης: {total_time:.2f} sec')
    print(f'Συνολικές αναθέσεις:       {len(all_assignments)}')
    
    print('\nΌλες οι αναθέσεις αποστολών:')
    for (i, a) in enumerate(all_assignments, 1):
        if a.dest_id < len(original_dests):
            dest_name = original_dests[a.dest_id].name
        else:
            dest_name = f'Dest_{a.dest_id}'
            
        cargo = a.supply.to_dict()
        print(
            f'{i:2}. Δρόνος {a.drone_id} -> {dest_name:<15} | Απόσταση: {a.distance:5.1f} '
            f"| Φορτίο: {cargo['food']:>3} τρόφιμα, {cargo['water']:>3} νερό, "
            f"{cargo['medicine']:>3} φάρμακα"
        )

    print('\nΤελικά ποσοστά κάλυψης προμηθειών ανά προορισμό:')
    for d in original_dests:
        satisfaction_rate = d.sat_rate() * 100
        status = '[✓] ΠΛΗΡΩΣ' if satisfaction_rate >= 99.9 else '[!] ΜΕΡΙΚΩΣ' if satisfaction_rate > 0 else '[✗] ΚΑΘΟΛΟΥ'
        print(f'  {d.name:<12}: {satisfaction_rate:5.1f}% {status}')

    return;

def safe_update_destination(dest_list:     List[Destination],
                            dest_id:       int,
                            supply_to_add: Supply) -> bool:
    '''Ασφαλής ενημέρωση προορισμού με έλεγχο ορίων'''
    if 0 <= dest_id < len(dest_list):
        dest_list[dest_id].satisfied = dest_list[dest_id].satisfied + supply_to_add
        return True;
    else:
        print(f'Προειδοποίηση: Μη έγκυρο dest_id {dest_id} (max: {len(dest_list)-1})')
        return False;

def main():
    (drones, depots, dests) = big_city_scenario()
    
    # Δημιουργία αντιγράφων για επεξεργασία
    working_depots = copy.deepcopy(depots)
    working_dests  = copy.deepcopy(dests)
    original_dests = copy.deepcopy(dests) # Κρατάμε τα πρωτότυπα για τελική αναφορά
    
    all_assignments = []
    iteration       = 1
    max_iterations  = 10 # Μέγιστος αριθμός επαναλήψεων
    
    print('\nΕΝΑΡΞΗ ΕΠΑΝΑΛΗΠΤΙΚΗΣ ΕΠΙΛΥΣΗΣ')
    print('=' * 60)
    
    # Εκτύπωση αρχικής κατάστασης
    print(f'Αρχική κατάσταση:')
    print(f'  Συνολικές προμήθειες: {sum(d.supply.total() for d in depots)}')
    print(f'  Συνολική ζήτηση:      {sum(d.demand.total() for d in dests)}')
    
    start_time = time()
    
    while iteration <= max_iterations:
        print(f'\n--- Προετοιμασία Επανάληψης {iteration} ---')
        
        # Δημιουργία λίστας μη ικανοποιημένων προορισμών με mapping
        unsatisfied_dests, id_mapping = create_unsatisfied_destinations_with_mapping(working_dests)
        
        if not unsatisfied_dests:
            print('Όλοι οι προορισμοί έχουν καλυφθεί πλήρως!')
            break;
        
        # Ελέγχουμε αν υπάρχουν ακόμη διαθέσιμες προμήθειες
        if not has_available_supplies(working_depots):
            print('Δεν υπάρχουν άλλες διαθέσιμες προμήθειες στα depots.')
            break;
        
        print(f'Μη ικανοποιημένοι προορισμοί: {len(unsatisfied_dests)}')
        print(f'Διαθέσιμες προμήθειες:        {sum(d.supply.total() for d in working_depots)}')
        
        reset_drone_status(drones) # Επαναφορά κατάστασης δρόνων σε IDLE
        
        try:
            # Επίλυση για την τρέχουσα επανάληψη
            iteration_start = time()
            assignments     = solve(drones, working_depots, unsatisfied_dests)
            iteration_time  = time() - iteration_start
            
            print(f'Χρόνος επανάληψης {iteration}:          {iteration_time:.2f} sec')
            
            if not assignments:
                print('\n-> Δεν βρέθηκαν εφικτές αναθέσεις.')
                break;
            
            # Εκτύπωση αποτελεσμάτων επανάληψης
            print_iteration_summary(iteration, assignments, original_dests, id_mapping)
            
            # Ενημέρωση προορισμών
            success_count = 0
            for assignment in assignments:
                # Βρίσκουμε το πρωτότυπο ID
                original_dest_id = id_mapping.get(assignment.dest_id)
                
                if original_dest_id is not None:
                    # Ενημέρωση πρωτότυπων προορισμών
                    if safe_update_destination(original_dests, original_dest_id, assignment.supply):
                        # Ενημέρωση working προορισμών
                        safe_update_destination(working_dests, original_dest_id, assignment.supply)
                        success_count += 1
                    
                    # Δημιουργία διορθωμένης ανάθεσης για την τελική λίστα
                    corrected_assignment         = copy.deepcopy(assignment)
                    corrected_assignment.dest_id = original_dest_id
                    all_assignments.append(corrected_assignment)
                else:
                    print(f'Προειδοποίηση: Δεν βρέθηκε mapping για dest_id {assignment.dest_id}')
            
            print(f'Επιτυχείς ενημερώσεις: {success_count}/{len(assignments)}')
            
            # Ενημέρωση διαθέσιμων προμηθειών στα depots
            update_supplies_after_assignments(working_depots, assignments)
            
            iteration += 1
            
        except Exception as e:
            print(f'Σφάλμα στην επανάληψη {iteration}: {e}')
            print(f'Τύπος σφάλματος:      {type(e).__name__}')
            
            # --- Debug
            print('Debug Info:')
            print(f'  Αριθμός unsatisfied_dests: {len(unsatisfied_dests)}')
            print(f'  ID mapping:                {id_mapping}')
            if assignments:
                print(f'  Assignment dest_ids:   {[a.dest_id for a in assignments]}')
            
            break;
    
    total_time = time() - start_time
    
    # Τελική αναφορά
    print_final_summary(all_assignments, original_dests, total_time, iteration - 1)
    
    # Στατιστικά
    print(f'\nΣΤΑΤΙΣΤΙΚΑ:')
    fully_satisfied     = sum(1 for d in original_dests if d.sat_rate() >= 0.999)
    partially_satisfied = sum(1 for d in original_dests if 0 < d.sat_rate() < 0.999)
    unsatisfied         = sum(1 for d in original_dests if d.sat_rate() == 0)
    
    print(f'  Πλήρως ικανοποιημένοι προορισμοί:  {fully_satisfied}/{len(original_dests)}')
    print(f'  Μερικώς ικανοποιημένοι προορισμοί: {partially_satisfied}/{len(original_dests)}')
    print(f'  Μη ικανοποιημένοι προορισμοί:      {unsatisfied}/{len(original_dests)}')
    
    remaining_supplies = sum(d.supply.total() for d in working_depots)
    print(f'  Εναπομείνασες προμήθειες:          {remaining_supplies}')

    return all_assignments;

if __name__ == '__main__':
    main()
