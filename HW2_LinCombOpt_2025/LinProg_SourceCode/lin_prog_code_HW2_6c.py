# lin_prog_code_HW2_6c.py

from time import time
import pulp

def define_model_and_solve():
    # --- Μοντέλο Δυϊκού LP (με ακέραιες μεταβλητές) ---
    model = pulp.LpProblem('Dual_Knapsack_LP', pulp.LpMinimize)

    # Μεταβλητές: y1 για τον περιορισμό χωρητικότητας, y2–y6 για upper bounds των x1–x5
    y = [pulp.LpVariable(f'y{i}', lowBound = 0, cat = 'Integer') for i in range(1, 7)]
    (y1, y2, y3, y4, y5, y6) = y # Για ευκολία αναφοράς

    # Αντικειμενική συνάρτηση:
    model += (11 * y1 + y2 + y3 + y4 + y5 + y6, 'Objective')

    # Περιορισμοί (ένας για κάθε x_i)
    model += 2 * y1 + y2 >= 10  # x1
    model += 3 * y1 + y3 >= 14  # x2
    model += 4 * y1 + y4 >= 31  # x3
    model += 6 * y1 + y5 >= 48  # x4
    model += 8 * y1 + y6 >= 60  # x5

    # --- Επίλυση ---
    solver = pulp.PULP_CBC_CMD(msg = False)
    model.solve(solver)

    return (model, y);

def main():
    start = time()
    (model, y) = define_model_and_solve()
    print(f'Χρόνος εκτέλεσης: {time() - start:.3f} δευτερόλεπτα')

    # --- Αποτελέσματα ---
    print('\n--- Δυϊκό Πρόβλημα (Ακέραιη Επίλυση) ---')
    print('\nΚατάσταση:', pulp.LpStatus[model.status])
    print(f'Βέλτιστη τιμή Z = {pulp.value(model.objective):.3f}')

    print('\nΤιμές μεταβλητών:')
    print(', '.join([f'{var.name} = {var.varValue:.0f}' for var in model.variables()]))

    return;

if __name__ == "__main__":
    main()
