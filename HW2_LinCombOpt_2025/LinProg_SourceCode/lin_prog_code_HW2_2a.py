# lin_prog_code_HW2_2a.py

from time import time
import numpy as np
import pulp

def define_and_solve_lp() -> pulp.LpProblem:
    model = pulp.LpProblem('LP1', pulp.LpMinimize)

    # Μεταβλητές απόφασης
    x1 = pulp.LpVariable('x1', upBound = 0)
    x2 = pulp.LpVariable('x2', lowBound = 0)
    x3 = pulp.LpVariable('x3', cat = 'Continuous')
    x4 = pulp.LpVariable('x4', lowBound = 0)

    # Ορισμός της αντικειμενικής συνάρτησης
    model += (x1 + x2, 'Objective Function')

    # Περιορισμοί
    model += (2 * x1 + 3 * x2 +     x3 +     x4 <= 0, 'Constraint 1')
    model += (   -x1 +     x2 + 2 * x3 +     x4 == 6, 'Constraint 2')
    model += (3 * x1 +     x2 + 4 * x3 + 2 * x4 >= 3, 'Constraint 3')

    # Επίλυση του μοντέλου/προβλήματος
    model.solve(pulp.PULP_CBC_CMD(msg = False))

    return model;

def define_dual_lp() -> pulp.LpProblem:
    dual = pulp.LpProblem('Dual_LP', pulp.LpMaximize)

    # Δυϊκές μεταβλητές
    #   Constraint 1 (<=) -> y1 ≤ 0
    #   Constraint 2 ( =) -> y2 free
    #   Constraint 3 (>=) -> y3 ≥ 0
    y1 = pulp.LpVariable('y1', upBound = 0)
    y2 = pulp.LpVariable('y2', cat = 'Continuous')
    y3 = pulp.LpVariable('y3', lowBound = 0)

    # Αντικειμενική συνάρτηση
    dual += (6 * y2 + 3 * y3, 'Dual_Objective')

    # Περιορισμοί
    dual += (2 * y1 -     y2 + 3 * y3 >= 1, 'Constraint x1')
    dual += (3 * y1 +     y2 +     y3 <= 1, 'Constraint x2')
    dual += (    y1 + 2 * y2 + 4 * y3 == 0, 'Constraint x3')
    dual += (    y1 +     y2 + 2 * y3 <= 0, 'Constraint x4')

    dual.solve(pulp.PULP_CBC_CMD(msg = False))
    
    return dual;

def print_solution_dual(model: pulp.LpProblem) -> dict:
    # --- Αποτελέσματα
    print('\nΒέλτιστη λύση:')
    var_values = {v.name: v.varValue for v in model.variables()}
    for (name, value) in var_values.items():
        print(f'{name} = {value:.2f}')
    
    temp = f'{pulp.value(model.objective):.2f}'
    print(f'\nΒέλτιστη τιμή της αντικειμενικής συνάρτησης: {temp}')
    
    # --- Χαρακτηρισμός μεταβλητών
    basic_vars = []
    for (name, value) in var_values.items():
        status = 'βασική' if abs(value) > 1e-6 else 'μη-βασική'
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
        print(f'{cname}: {lhs:.2f} {relation} {rhs:.2f} -> {status}')
        constraint_status[cname] = status

        if binding:
            B_rows.append([cons.get(v, 0) for v in model.variables() \
                           if v.name in basic_vars])
            constraint_names.append(cname)

    if constraint_names:
        print('\nΆρα, η βέλτιστη κορυφή καθορίζεται από τους περιορισμούς:')
        print(', '.join(constraint_names))
    
    return var_values;

def main():
    print('\n--- Άσκηση 2η ---')
    print('Ερώτημα α)')

    # print('\n- Πρωτεύον πρόβλημα:')
    # start = time()
    model = define_and_solve_lp()
    # print(f'Χρόνος εκτέλεσης: {time() - start:.2f} δευτερόλεπτα')
    # print_solution(model)

    print('\n- Δυϊκό πρόβλημα:')
    start = time()
    dual = define_dual_lp()
    print(f'Χρόνος εκτέλεσης: {time() - start:.2f} δευτερόλεπτα')
    dual_var_solution = print_solution_dual(dual)

    # --- Έλεγχος της λύσης του δυϊκού προβλήματος!
    print('\nΕπαλήθευση της λύσης του δυϊκού προβλήματος:')
    assert np.isclose(
        pulp.value(model.objective),
        pulp.value(dual.objective),
        atol = 1e-5
    ), f'Οι τιμές των αντικειμενικών συναρτήσεων δεν είναι ίσες!'
    dual_map = {
        'y1': 'Constraint_1',
        'y2': 'Constraint_2',
        'y3': 'Constraint_3'
    }
    for (y_name, cname) in dual_map.items():
        expected = model.constraints[cname].pi
        actual   = dual_var_solution[y_name]
        assert np.isclose(
            actual,
            expected,
            atol = 1e-5
        ), f'{y_name} = {actual:.2f} != {expected:.2f} = {cname}'
    print('Complete! Ο έλεγχος ήταν επιτυχής!')
    
    return;

if __name__ == '__main__':
    main()
