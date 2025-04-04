# Άσκηση 5η - β

from sympy import symbols, Matrix, N
from itertools import combinations

def main():
    # Βασικές μεταβλητές x1, x2, x3 και μεταβλητές χαλάρωσης x4, x5, x6, x7
    (x1, x2, x3, x4, x5, x6, x7) = symbols('x1 x2 x3 x4 x5 x6 x7')
    all_vars = [x1, x2, x3, x4, x5, x6, x7]

    # Δημιουργία του πίνακα A (4x7), σύμφωνα με τις ισοδυναμίες:
    #  1)   x1 +   x2        >=  10 =>   x1 +   x2 -        x4          =  10
    #  2)          x2 +   x3 >=  15 =>          x2 +   x3 -    x5       =  15
    #  3)   x1 +          x3 >=  12 =>   x1 +          x3 -       x6    =  12
    #  4) 20x1 + 10x2 + 15x3 <= 300 => 20x1 + 10x2 + 15x3 +          x7 = 300
    A = Matrix([
        [ 1,  1,  0, -1,  0,  0,  0],
        [ 0,  1,  1,  0, -1,  0,  0],
        [ 1,  0,  1,  0,  0, -1,  0],
        [20, 10, 15,  0,  0,  0,  1]
    ])
    b = Matrix([10, 15, 12, 300])

    # Συντελεστές αντικειμενικής συνάρτησης Z = 8x1 + 5x2 + 4x3
    c = Matrix([8, 5, 4, 0, 0, 0, 0])

    # Θα επιλέξουμε 4 στήλες από τις 7 (όσες και οι εξισώσεις), σχηματίζοντας υποπίνακα B
    # Σελ. 31 / 70 - 01. Εισαγωγή στον Γραμμικό Προγραμματισμό - Αλγόριθμος Simplex
    m = 4 # Αριθμός περιορισμών
    count_bfs = 0

    # Συνάρτηση για τον υπολογισμό της τιμής της αντικειμενικής συνάρτησης
    def objective_value(x_full):
        return -sum(c[i] * x_full[i] for i in range(len(all_vars)));

    # Ξεκινάμε τον έλεγχο όλων των συνδυασμών 4 στηλών από 7
    for basis_cols in combinations(range(len(all_vars)), m):
        # Φτιάχνουμε τον 4x4 υποπίνακα
        B = A[:, basis_cols] # Όλες οι γραμμές, μόνο οι στήλες των βάσεων

        try:
            # Επίλυση του συστήματος B * xB = b
            xB = B.LUsolve(b)
        except:
            # Αν ο πίνακας είναι μη αντιστρέψιμος, προχωράμε στον επόμενο!
            continue;

        # Δημιουργία του full_x με 7 θέσεις (για x1..x7), ενημερώνουμε μόνο τις θέσεις βάσης
        full_x = [0.0] * len(all_vars)
        for (i, col_idx) in enumerate(basis_cols):
            full_x[col_idx] = float(N(xB[i]))

        # Υπολογισμός Z
        Z_val = objective_value(full_x)

        # Ελεγχος εκφυλισμού
        # Σελ. 45 / 70 - 01. Εισαγωγή στον Γραμμικό Προγραμματισμό - Αλγόριθμος Simplex
        # εναλλακτικά, μετρώντας πόσες είναι 0
        basic_indices = list(basis_cols) # indices των βασικών μεταβλητών
        degenerate = any(abs(full_x[idx]) < 1e-9 for idx in basic_indices) # Οριακά 0!

        # Τύπωση αποτελέσματος
        temp = 'Δ' if degenerate else '+' # + => εφικτή & Δ => εκφυλισμένη

        # Έλεγχος εφικτότητας: όλες οι x >= 0
        if any(val < -1e-9 for val in full_x):
            temp = '-' # - => μη εφικτή
        
        var_names = [str(all_vars[i]) for i in basis_cols]
        basis_str = '{' + ', '.join(var_names) + '}'
        x_vals_aligned = ', '.join(f"{v}={full_x[idx]:>8.3f}"
                                   for v, idx in zip(var_names, basis_cols))
        print(f"{temp} Βάση: {basis_str} =>   {x_vals_aligned} | Z = {Z_val:8.3f}")

        count_bfs += 1

    print(f"\nΣύνολο βασικών [εφικτών και μη] λύσεων: {count_bfs}")

    return;

if __name__ == '__main__':
    main()
