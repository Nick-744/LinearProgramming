# lin_prog_code_HW2_1a.py

from time import time
import numpy as np
import pulp

def define_and_solve_lp() -> pulp.LpProblem:
    model = pulp.LpProblem('LP1', pulp.LpMaximize)

    # Μεταβλητές απόφασης
    x1 = pulp.LpVariable('x1', cat = 'Continuous')
    x2 = pulp.LpVariable('x2', lowBound = 0)
    x3 = pulp.LpVariable('x3', lowBound = 0)
    x4 = pulp.LpVariable('x4', lowBound = 0)
    x5 = pulp.LpVariable('x5', lowBound = 0)

    # Ορισμός της αντικειμενικής συνάρτησης
    model += (3 * x1 + 11 * x2 + 9 * x3 - x4 - 29 * x5, 'Objective')

    # Περιορισμοί
    model += (     x2 + x3 +     x4 - 2 * x5 <= 4, 'Constraint 1')
    model += (x1 - x2 + x3 + 2 * x4 +     x5 >= 0, 'Constraint 2')
    model += (x1 + x2 + x3          - 3 * x5 <= 1, 'Constraint 3')

    # Επίλυση του μοντέλου/προβλήματος
    model.solve(pulp.PULP_CBC_CMD(msg = False))

    return model;

def print_solution(model: pulp.LpProblem) -> tuple:
    # --- Αποτελέσματα
    print('\nΒέλτιστη λύση:')
    var_values = {v.name: v.varValue for v in model.variables()}
    for (name, value) in var_values.items():
        print(f"{name} = {value:.2f}")
    
    temp = f'{pulp.value(model.objective):.2f}'
    print(f'\nΒέλτιστη τιμή της αντικειμενικής συνάρτησης: {temp}')
    
    # --- Χαρακτηρισμός μεταβλητών
    basic_vars = []
    print('\nΧαρακτηρισμός των μεταβλητών:')
    for (name, value) in var_values.items():
        status = 'βασική' if abs(value) > 1e-6 else 'μη-βασική'
        print(f"{name}: {status}")
        if status == 'βασική':
            basic_vars.append(name)

    # --- Ανάλυση περιορισμών
    print('\nΑνάλυση των περιορισμών (δεσμευτικοί / μη δεσμευτικοί):')
    (constraint_status, B_rows, constraint_names) = ({}, [], [])
    for (cname, cons) in model.constraints.items():
        lhs = sum(
            var_values[v.name] * coef for (v, coef) in cons.items()
        )
        rhs = -cons.constant  # Pulp stores as lhs - rhs ≤ 0!!!
        relation = ('<=' if (cons.sense == -1) else \
                    ('>=' if (cons.sense == 1) else '='))

        binding = abs(lhs - rhs) < 1e-6
        status = 'δεσμευτικός' if binding else 'μη δεσμευτικός'
        print(f"{cname}: {lhs:.2f} {relation} {rhs:.2f} -> {status}")
        constraint_status[cname] = status

        if binding:
            B_rows.append([cons.get(v, 0) for v in model.variables() \
                           if v.name in basic_vars])
            constraint_names.append(cname)

    if constraint_names:
        print('\nΆρα, η βέλτιστη κορυφή καθορίζεται από τους περιορισμούς:')
        print(', '.join(constraint_names))

    # --- Πίνακας B
    B_matrix = np.array(B_rows)
    print('\nΒέλτιστος βασικός πίνακας [B]:')
    print_matrix(B_matrix, basic_vars)
    
    return (basic_vars, constraint_status, B_matrix);

def find_matrix_N(model: pulp.LpProblem,
                  basic_vars: list,
                  constraint_status: dict) -> tuple:
    non_basic_vars = [
        v.name for v in model.variables() if v.name not in basic_vars
    ]
    N_rows = []

    for (cname, cons) in model.constraints.items():
        if constraint_status[cname] == 'δεσμευτικός':
            N_rows.append(
                [cons.get(v, 0) for v in model.variables() \
                 if v.name in non_basic_vars]
            )
    
    N_matrix = np.array(N_rows)

    return (non_basic_vars, N_matrix);

def analyze_perturbation(model: pulp.LpProblem,
                         basic_vars: list,
                         non_basic_vars: list,
                         constraint_status: dict,
                         B_matrix: np.ndarray,
                         N_matrix: np.ndarray) -> None:
    # Πίνακας b από τους δεσμευτικούς περιορισμούς
    b = np.array([
        -model.constraints[name].constant
        for name in constraint_status
        if constraint_status[name] == 'δεσμευτικός'
    ])

    B_inv = np.linalg.inv(B_matrix) # B⁻¹

    # Συντελεστές αντικειμενικής συνάρτησης
    c_all = {v.name: coef for (v, coef) in model.objective.items()}
    c_B = np.array([c_all.get(v, 0) for v in basic_vars])
    c_N = np.array([c_all.get(v, 0) for v in non_basic_vars])

    # --- Ανάλυση συντελεστή βασικής μεταβλητής
    print("\n-> Διαστήματα ανοχής για βασικό συντελεστή:")
    (var, i) = (basic_vars[0], 0) # Επιλέγω την x1 βασική μεταβλητή

    e_k = np.zeros(len(basic_vars))
    e_k[i] = 1
    ekT_Binv = e_k @ B_inv
    ekT_Binv_N = ekT_Binv @ N_matrix

    cN_minus_cB_BinvN = c_N - (c_B @ B_inv @ N_matrix)

    delta_lows = []
    delta_highs = []
    for (ci, ai) in zip(cN_minus_cB_BinvN, ekT_Binv_N):
        if abs(ai) < 1e-8:
            continue;
        bound = ci / ai
        if ai > 0:
            delta_highs.append(bound)
        else:
            delta_lows.append(bound)

    δ_min = max(delta_lows)  if delta_lows  else -np.inf
    δ_max = min(delta_highs) if delta_highs else  np.inf
    (δ_min, δ_max) = (δ_max, δ_min) if δ_min > δ_max else (δ_min, δ_max)

    print(f" - {var}: δ ∈ [{δ_min:.2f}, {δ_max:.2f}]")

    # --- Ανάλυση συντελεστή μη-βασικής μεταβλητής
    print("\n-> Διαστήματα ανοχής για μη-βασικό συντελεστή:")
    (var, i) = (non_basic_vars[0], 0) # Επιλέγω την x4 μη-βασική

    delta_lows = []
    delta_highs = []
    for (ci, ei) in zip(cN_minus_cB_BinvN, e_k):
        if abs(ei) < 1e-8:
            continue;
        bound = -ci / ei
        if ei > 0:
            delta_highs.append(bound)
        else:
            delta_lows.append(bound)

    δ_min = max(delta_lows)  if delta_lows  else -np.inf
    δ_max = min(delta_highs) if delta_highs else  np.inf
    (δ_min, δ_max) = (δ_max, δ_min) if δ_min > δ_max else (δ_min, δ_max)

    print(f" - {var}: δ ∈ [{δ_min:.2f}, {δ_max:.2f}]")

    return;

# --- Helpers
def print_matrix(matrix: np.ndarray, vars: list) -> None:
    # Για την καλύτερη εμφάνιση των πινάκων!
    print(4 * ' ' + (5 * ' ').join(vars))
    for row in matrix:
        row_str = '  '.join(f"{val:>5.2f}" for val in row)
        print(f"[ {row_str} ]")

    return;

def main():
    print('\n--- Άσκηση 1η ---')
    print('Ερώτημα α)')

    start = time()
    model = define_and_solve_lp()
    print(f'\n- Χρόνος εκτέλεσης: {time() - start:.2f} δευτερόλεπτα')

    (basic_vars, constraint_status, B_matrix) = print_solution(model)

    (non_basic_vars, N_matrix) = find_matrix_N(
        model, basic_vars, constraint_status
    )
    print('\nΠίνακας [N]:')
    print_matrix(N_matrix, non_basic_vars)

    # print('\nΕρώτημα β)')

    # analyze_perturbation(
    #     model,
    #     basic_vars,
    #     non_basic_vars,
    #     constraint_status,
    #     B_matrix,
    #     N_matrix
    # )
    
    return;

if __name__ == '__main__':
    main()
