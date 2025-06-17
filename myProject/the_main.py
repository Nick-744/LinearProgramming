# the_main.py

from scenario import extended_scenario
from lp_solver import solve_multi_trip

if __name__ == '__main__':
    (drones, depots, dests) = extended_scenario()
    assignments             = solve_multi_trip(drones, depots, dests)

    print('\nΒέλτιστες αναθέσεις αποστολών (πολλαπλές διαδρομές):')
    for group in assignments:
        for a in group.assignments:
            dest_name = dests[a.dest_id].name
            cargo     = a.supply.to_dict()
            print(
                f'Δρόνος {a.drone_id} (διαδρομή {a.trip_number}) -> {dest_name:<18} | '
                f'Απόσταση: {a.distance:5.1f} μον. | '
                f"Φορτίο: {cargo['food']:>3} τρόφιμα, {cargo['water']:>3} νερό, "
                f"{cargo['medicine']:>3} φάρμακα | Χρόνος: {a.start_time:.1f}-{a.end_time:.1f} λεπτά"
            )

    print('\nΠοσοστά κάλυψης προμηθειών ανά προορισμό:')
    for d in dests:
        print(f'  {d.name}: {d.sat_rate() * 100:.1f}%')
