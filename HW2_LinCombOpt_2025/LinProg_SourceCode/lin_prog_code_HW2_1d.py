# lin_prog_code_HW2_1d.py

from time import time
import pulp

def define_dual_lp():
    dual = pulp.LpProblem('DualProblem', pulp.LpMinimize)

    # Δυϊκές μεταβλητές
    y1 = pulp.LpVariable('y1', lowBound = 0) # ≤-περιορισμός
    y2 = pulp.LpVariable('y2', upBound  = 0) # ≥-περιορισμός
    y3 = pulp.LpVariable('y3', lowBound = 0) # ≤-περιορισμός

    # Αντικειμενική
    dual += (4 * y1 + y3, 'W')

    # Περιορισμοί στήλης
    dual += (              y2 +     y3 ==   3, 'Constraint 1')
    dual += (     y1 -     y2 +     y3 >=  11, 'Constraint 2')
    dual += (     y1 +     y2 +     y3 >=   9, 'Constraint 3')
    dual += (     y1 + 2 * y2          >=  -1, 'Constraint 4')
    dual += (-2 * y1 +     y2 - 3 * y3 >= -29, 'Constraint 5')

    dual.solve(pulp.PULP_CBC_CMD(msg = False))

    return dual;

if __name__ == '__main__':
    start = time()
    model = define_dual_lp()
    print(f'\nΧρόνος εκτέλεσης: {time() - start:.2f} δευτερόλεπτα\n')

    print('Βέλτιστη λύση:')
    for v in model.variables():
        print(f'  {v.name} = {v.varValue:.2f}')
    print(f'\n  Z* = {pulp.value(model.objective):.2f}')
