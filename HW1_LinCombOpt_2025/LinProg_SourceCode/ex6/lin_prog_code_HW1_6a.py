# Άσκηση 6η - α

from sympy import symbols, Matrix, nsimplify

def print_tableau(iteration, basic_vars, tableau, xB_values, z_row, Z_val):
    # Global μεταβλητές: all_vars, var_indices
    
    col_width = 6
    header = [f"Βήμα {iteration}"] + [str(v) for v in all_vars] + ["b"]
    
    # Επικεφαλίδα
    print(" " + " | ".join(f"{name:>{col_width}}" for name in header))
    print("-" * ((col_width + 3) * len(header) - 1)) # διαχωριστική γραμμή

    # Γραμμή -Z
    z_line = ["-Z"] + [str(v) for v in z_row] + [str(Z_val)]
    print(" " + " | ".join(f"{val:>{col_width}}" for val in z_line))

    print("-" * ((col_width + 3) * len(header) - 1)) # διαχωριστική γραμμή

    # Γραμμές βασικών μεταβλητών
    for (i, v) in enumerate(basic_vars):
        row_vals = [tableau[i, var_indices[var]] for var in all_vars]
        row = [str(v)] + [str(val) for val in row_vals] + [str(xB_values[i])]

        line = " " + " | ".join(f"{val:>{col_width}}" for val in row)
        if xB_values[i].is_zero:
            line += " <-- Εκφυλισμένη"
        print(line)

    return;

def main():
    # Βασικές μεταβλητές x1, x2, x3, x4 και μεταβλητές χαλάρωσης x5, x6, x7
    (x1, x2, x3, x4, x5, x6, x7) = symbols('x1 x2 x3 x4 x5 x6 x7')
    global all_vars # Δημιουργία καθολής μεταβλητής για όλες τις μεταβλητές!
    all_vars = [x1, x2, x3, x4, x5, x6, x7]

    # Δημιουργία του πίνακα A (3x7), σύμφωνα με τις ισοδυναμίες:
    #  1)  x1 + 2x2 + 4x3 - x4 ≤  6 =>  x1 + 2x2 + 4x3 - x4 + x5       =  6
    #  2) 2x1 + 3x2 -  x3 + x4 ≤ 12 => 2x1 + 3x2 -  x3 + x4 +    x6    = 12
    #  3)  x1 +        x3 + x4 ≤  2 =>  x1 +        x3 + x4 +       x7 =  2
    A = Matrix([
        [1, 2,  4, -1, 1, 0, 0],
        [2, 3, -1,  1, 0, 1, 0],
        [1, 0,  1,  1, 0, 0, 1]
    ])
    b = Matrix([6, 12, 2])

    # Συντελεστές αντικειμενικής συνάρτησης Z = 2x1 + x2 + 6x3 - 4x4
    c = Matrix([2, 1, 6, -4, 0, 0, 0])

    # Αρχική βάση: x5, x6, x7 | ### Βήμα - Αρχικοποίηση
    '''Σελ. 47=>49 / 70 - 01. Εισαγωγή στον Γραμμικό Προγραμματισμό
                            - Αλγόριθμος Simplex'''
    basic_vars    = [x5, x6, x7]
    nonbasic_vars = [x1, x2, x3, x4]

    # Δείκτες μεταβλητών
    global var_indices # Δημιουργία καθολικής μεταβλητής για τους δείκτες των μεταβλητών!
    var_indices = {v: i for (i, v) in enumerate(all_vars)}

    iteration = 0
    while True:
        ### Βήμα - Απαλοιφή Gauss
        B = A[:, [var_indices[v] for v in basic_vars]]
        B_inv = B.inv()

        tableau = B_inv * A
        xB_values = B_inv * b
        if any(val < 0 for val in xB_values):
            print('Δεν υπάρχει αρχικά εφικτή λύση: B⁻¹b < 0!')
            return;

        # Υπολογισμός της γραμμής Z
        c_B = Matrix([c[var_indices[v]] for v in basic_vars])

        z_row = []
        for v in all_vars:
            if v in basic_vars:
                z_row.append(0)
            else:
                Aj = A[:, var_indices[v]]
                zj = c[var_indices[v]] - (c_B.T * B_inv * Aj)[0, 0]
                z_row.append(zj)

        Z_val = -(Matrix([c[var_indices[v]] for v in basic_vars]).T * xB_values)[0, 0]
        print_tableau(iteration, basic_vars, tableau, xB_values, z_row, Z_val)

        # Έλεγχος βέλτιστης λύσης
        if all(z <= 0 for z in z_row):
            print('\nΗ λύση είναι βέλτιστη!')
            break;

        ### Βήμα - Επιλογή νέας βασικής μεταβλητής
        entering_idx = None
        print(f'\nΕπιλογή της 1ης μεταβλητής με Z > 0 ως εισερχόμενη:')
        for i in range(len(z_row)):
            print(f'z = {str(z_row[i]):>5} | {all_vars[i]}', end = ' ')
            if z_row[i] > 0:
                entering_idx = i
                print(' <-- Εισερχόμενη βασική μεταβλητή')
                break;
            print() # Καλύτερη αισθητική
        
        entering_var = nonbasic_vars[entering_idx]

        ### Βήμα - Κριτήριο ελαχίστου λόγου
        d = B_inv * A[:, var_indices[entering_var]]
        ratios = []
        for i in range(len(d)):
            if d[i] > 0:
                ratios.append(xB_values[i] / d[i])
            else:
                ratios.append(float('inf'))

        if all(r == float('inf') for r in ratios):
            print("Το πρόβλημα δεν είναι φραγμένο!")
            return;

        min_ratio = min(ratios)
        exiting_idx = ratios.index(min_ratio)
        exiting_var = basic_vars[exiting_idx]

        # Εμφάνιση του πίνακα με τους λόγους
        print("\nΚριτήριο ελαχίστου λόγου:")
        print("-" * 40)
        print(f"{'Βασική':<10} | {'xB[i]':>7} | {'d[i]':>7} | {'Λόγος':>7}")
        print("-" * 40)
        for i, v in enumerate(basic_vars):
            xb = xB_values[i]
            di = d[i]
            ratio_str = "-" if di <= 0 else f"{xb/di}"
            selected = "  <-- ελάχιστος" if i == exiting_idx else ""
            print(f"{str(v):<10} | {str(xb):>7} | {str(di):>7} | {ratio_str:>7}{selected}")

        print(f"Εξερχόμενη μεταβλητή: {exiting_var}\n")

        ### Βήμα - Ανταλλαγή μεταβλητών
        basic_vars[exiting_idx] = entering_var
        nonbasic_vars[entering_idx] = exiting_var
        iteration += 1

    # --- Εκτύπωση τελικής λύσης ---
    full_solution = [0.0] * len(all_vars)
    for (i, var) in enumerate(basic_vars):
        full_solution[var_indices[var]] = float(xB_values[i])

    print() # Καλύτερη αισθητική
    Z_val = sum(c[i] * full_solution[i] for i in range(len(all_vars)))
    for (i, val) in enumerate(full_solution):
        val_rat = nsimplify(val)
        print(f"x{i+1} = {val_rat}", end=", " if i < len(full_solution) - 1 else " ")
    Z_rat = nsimplify(Z_val)
    print(f"με Z = {Z_rat}\n")

    return;

if __name__ == '__main__':
    main()
