# Demo - main.py

from scenario import sample_scenario
from lp_solver import solve

if __name__ == '__main__':
    (drones, depots, dests) = sample_scenario()
    assigns = solve(drones, depots, dests)

    print('\nΒέλτιστες αναθέσεις αποστολών:')
    for a in assigns:
        dest_name = dests[a.dest_id].name
        cargo = a.supply.to_dict()
        print(
            f'Δρόνος {a.drone_id} -> {dest_name:<10} | Απόσταση: {a.distance:5.1f} μον.',
            f"| Φορτίο: {cargo['food']:>3} τρόφιμα, {cargo['water']:>3} νερό, "
            f"{cargo['medicine']:>3} φάρμακα"
        )


    print('\nΠοσοστά κάλυψης προμηθειών ανά προορισμό:')
    for d in dests:
        print(f'  {d.name}: {d.sat_rate()*100:.1f}%')
