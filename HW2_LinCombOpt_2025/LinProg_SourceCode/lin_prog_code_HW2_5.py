# lin_prog_code_HW2_5.py

from time import time
import pulp

# Global μεταβλητή κατάστασης
best_Z_int          = float('-inf') # Βέλτιστη τιμή αντικειμενικής
                                  # (Global Upper Bound - GUB)
best_x_int_solution = None        # Βέλτιστη ακέραια λύση (dictionary)
node_id_counter     = 0           # Αναγνωριστικό κόμβων για debug!

solver = pulp.PULP_CBC_CMD(msg = False) # Solver χωρίς output

# Συνάρτηση επίλυσης LP κόμβου
def solve_lp_node(branch_constraints):
    model = pulp.LpProblem('BranchAndBoundLP', pulp.LpMaximize)

    # Μεταβλητές απόφασης
    x = [pulp.LpVariable(
        f'x{i}', lowBound = 0, cat = 'Continuous') \
            for i in range(1, 4)
    ]
    (x1, x2, x3) = x # Για ευκολία αναφοράς

    # Αντικειμενική συνάρτηση:
    model += 34 * x1 + 29 * x2 + 2 * x3

    # Περιορισμοί
    model += 7 * x1 + 5 * x2 -     x3 <= 16
    model +=    -x1 + 3 * x2 +     x3 <= 10
    model +=             -x2 + 2 * x3 <= 3

    # Εφαρμογή των περιορισμών διακλάδωσης
    for (idx, op, val) in branch_constraints:
        if op == '<=':
            model += x[idx - 1] <= val
        else:
            model += x[idx - 1] >= val

    # Επίλυση του LP
    model.solve(solver)

    if pulp.LpStatus[model.status] == 'Optimal':
        Z = pulp.value(model.objective)
        x_sol = {v.name: v.varValue for v in model.variables()}
        return (Z, x_sol, True);
    else:
        return (float('-inf'), None, False);

# Αναδρομική συνάρτηση Branch & Bound!
def branch_and_bound_recursive(
    parent_id, constraints, depth, max_depth = 5
):
    global best_Z_int, best_x_int_solution, node_id_counter

    node_id = f'N{node_id_counter}'
    node_id_counter += 1

    (Z, x_sol, feasible) = solve_lp_node(constraints)

    print(f'\nΚόμβος {node_id} (Βάθος {depth})', end = ' - ')
    print(f'Προέλευση: {parent_id or 'ROOT'}')
    if not feasible:
        print('- Κατάσταση: Μη εφικτό — Απορρίπτεται')
        return;

    print(f'Τιμή αντικειμενικής συνάρτησης: Z = {Z:.3f}')
    print('Τιμές μεταβλητών: ' + \
        ', '.join(f'{k}={v:.2f}' \
            for (k, v) in sorted(
                x_sol.items(), key = lambda x: int(x[0][1:])
            )
        )
    )

    if Z < best_Z_int:
        print(f'- Κατάσταση: Bound (Z = {Z:.3f} < GUB = {best_Z_int:.3f})')
        return;

    (var_idx, frac_val) = get_fractional_variable_info(x_sol)

    if var_idx is None:
        print('- Κατάσταση: Ακέραια λύση')
        if Z > best_Z_int:
            best_Z_int = Z
            best_x_int_solution = x_sol
            print(f'-> Νέα βέλτιστη ακέραια λύση! GUB = {best_Z_int:.3f}')
        return;

    if depth >= max_depth:
        print(f'- Κατάσταση: Μέγιστο βάθος {max_depth} — ΤΕΡΜΑΤΙΣΜΟΣ')
        return;

    print(f'- Κατάσταση: Branch στη x{var_idx} = {frac_val:.3f}')

    floor_val = int(frac_val)
    ceil_val = floor_val + 1

    # Διακλάδωση 1: x ≤ floor
    branch_and_bound_recursive(
        node_id,
        constraints + [(var_idx, '<=', floor_val)],
        depth + 1,
        max_depth
    )

    # Διακλάδωση 2: x ≥ ceil
    branch_and_bound_recursive(
        node_id,
        constraints + [(var_idx, '>=', ceil_val)],
        depth + 1,
        max_depth
    )

    return;

# --- Helpers ---
def get_fractional_variable_info(x_dict):
    # Συνάρτηση εύρεσης 1ης μη ακέραιας μεταβλητής
    for i in range(1, 4):
        var = f'x{i}'
        val = x_dict.get(var, 0.)
        if abs(val - round(val)) > 1e-5:
            return (i, val);

    return (None, None);

def main():
    global best_Z_int, best_x_int_solution, node_id_counter

    best_Z_int          = float('-inf')
    best_x_int_solution = None
    node_id_counter     = 0

    print('-> Εκκίνηση Branch & Bound')
    start = time()
    branch_and_bound_recursive(None, [], 0, max_depth = 20)
    print(f'\n-> Χρόνος εκτέλεσης: {time() - start:.3f} δευτερόλεπτα')

    print('\n--- Τελικό Αποτέλεσμα')
    if best_x_int_solution:
        sorted_x = sorted(
            best_x_int_solution.items(), key = lambda x: int(x[0][1:])
        )
        print(f'Βέλτιστη ακέραια λύση: Z = {best_Z_int:.0f}')
        print('x = {' + \
            ', '.join(f'{k} = {v:.0f}' for (k, v) in sorted_x) + '}'
        )
    else:
        print('Δεν βρέθηκε ακέραια λύση.')

    return;

if __name__ == '__main__':
    main()
