# Άσκηση 5η - α

import numpy as np
from sympy.solvers import solve
from sympy import Symbol
from sympy import lambdify
from itertools import combinations

def p1(x1: Symbol, x2: Symbol, x3: Symbol) -> float:
    return x1 + x2 - 10;

def p2(x1: Symbol, x2: Symbol, x3: Symbol) -> float:
    return x2 + x3 - 15;

def p3(x1: Symbol, x2: Symbol, x3: Symbol) -> float:
    return x1 + x3 - 12;

def p4(x1: Symbol, x2: Symbol, x3: Symbol) -> float:
    return 20*x1 + 10*x2 + 15*x3 - 300;

# Αντικειμενική συνάρτηση [Z]
def Z(x1: Symbol, x2: Symbol, x3: Symbol) -> float:
    return -(8*x1 + 5*x2 + 4*x3);

def main():
    x1_var = Symbol('x1')
    x2_var = Symbol('x2')
    x3_var = Symbol('x3')

    # Οι συναρτήσεις των περιορισμών μας
    constraint_functions = [
        p1(x1_var, x2_var, x3_var), # ≥ 0
        p2(x1_var, x2_var, x3_var), # ≥ 0
        p3(x1_var, x2_var, x3_var), # ≥ 0
        p4(x1_var, x2_var, x3_var), # ≤ 0
        x1_var, x2_var, x3_var      # ≥ 0
    ]

    inequality_signs = ['>=', '>=', '>=', '<=', '>=', '>=', '>=']
    compiled_constraints = [
        (lambdify((x1_var, x2_var, x3_var), expr), sign)
        for (expr, sign) in zip(constraint_functions, inequality_signs)
    ] # lambdify: Converts symbolic expressions into Python functions!
    def check_restrictions(x1_val, x2_val, x3_val, epsilon = 1e-8):
        # epsilon tolerance for floating point comparisons!!!!!
        for (function, sign) in compiled_constraints:
            value = function(x1_val, x2_val, x3_val) # Γυρνάει float

            if sign == '>=' and value < -epsilon:
                break;
            elif sign == '<=' and value > epsilon:
                break;
        else:
            return True;

        return False;

    # Συνάρτηση για να ελέγξουμε αν η κορυφή είναι εκφυλισμένη
    def is_degenerate(x1, x2, x3, epsilon = 1e-8):
        active_constraints = 0
        for (f, sign) in compiled_constraints:
            val = f(x1, x2, x3)
            if sign in ['>=', '<='] and np.isclose(val, 0, atol = epsilon):
                active_constraints += 1
            elif sign == '=' and np.isclose(val, 0, atol=epsilon):
                active_constraints += 1

        return active_constraints > 3;

    # Συνδυασμοί, ανά 2 συναρτήσεων περιορισμών, για τις τομές/κορυφές
    constraint_foos_combo = list(combinations(constraint_functions, 3))

    # Υπολογισμός ΟΛΩΝ των σημείων τομής
    intersection_points = []
    for (cf1, cf2, cf3) in constraint_foos_combo:
        sol = solve((cf1, cf2, cf3), (x1_var, x2_var, x3_var))
        if sol: # Ώστε να μην προκύψει IndexError!
            intersection_points.append(
                (float(sol[x1_var]), float(sol[x2_var]), float(sol[x3_var]))
            )

    # Φιλτράρουμε τα σημεία που δεν ικανοποιούν όλους τους περιορισμούς
    feasible_points = []
    for (candidate_x1, candidate_x2, candidate_x3) in intersection_points:
        if check_restrictions(candidate_x1, candidate_x2, candidate_x3):
            feasible_points.append((candidate_x1, candidate_x2, candidate_x3))

    # Βρίσκουμε το μέγιστο της Z συνάρτησης
    best_value = float('-inf')
    for (candidate_x1, candidate_x2, candidate_x3) in feasible_points:
        val = Z(candidate_x1, candidate_x2, candidate_x3)
        if val > best_value:
            best_value = val

    print('Κορυφές [Εφικτές: + | Εκφυλισμένες: Δ | Μη εφικτές: -]:')
    for (x1_val, x2_val, x3_val) in intersection_points:
        temp = '-'
        if (x1_val, x2_val, x3_val) in feasible_points:
            temp = '+'
            if is_degenerate(x1_val, x2_val, x3_val):
                temp = 'Δ' # Εκφυλισμένη κορυφή!
        print(f' {temp} {(x1_val, x2_val, x3_val)} -> Z = {Z(x1_val, x2_val, x3_val)}')
    print() # Καλύτερη αισθητική

    return;

if __name__ == '__main__':
    main()
