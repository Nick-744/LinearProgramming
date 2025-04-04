# Άσκηση 1η

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from sympy.solvers import solve
from sympy import Symbol
from sympy import lambdify
from itertools import combinations

def p1(x1: Symbol, x2: Symbol) -> float:
    return 6*x1 + 3*x2 - 12;

def p2(x1: Symbol, x2: Symbol) -> float:
    return 4*x1 + 8*x2 - 16;

def p3(x1: Symbol, x2: Symbol) -> float:
    return 6*x1 + 5*x2 - 30;

def p4(x1: Symbol, x2: Symbol) -> float:
    return 6*x1 + 7*x2 - 36;

# Αντικειμενική συνάρτηση [Z]
def Z(x1: Symbol, x2: Symbol) -> float:
    return 3*x1 + x2;

def main():
    (x1_var, x2_var) = (Symbol('x1'), Symbol('x2'))

    # Οι συναρτήσεις των περιορισμών μας
    constraint_functions = [
        p1(x1_var, x2_var), # ≥ 0
        p2(x1_var, x2_var), # ≥ 0
        p3(x1_var, x2_var), # ≤ 0
        p4(x1_var, x2_var), # ≤ 0
        x1_var, x2_var      # ≥ 0
    ]

    inequality_signs = ['>=', '>=', '<=', '<=', '>=', '>=']
    compiled_constraints = [
        (lambdify((x1_var, x2_var), expr), sign)
        for (expr, sign) in zip(constraint_functions, inequality_signs)
    ] # lambdify: Converts symbolic expressions into Python functions!
    def check_restrictions(x1_val, x2_val, epsilon = 1e-8):
        # epsilon tolerance for floating point comparisons!!!!!
        for (function, sign) in compiled_constraints:
            value = function(x1_val, x2_val) # Γυρνάει float

            if sign == '>=' and value < -epsilon:
                break;
            elif sign == '<=' and value > epsilon:
                break;
        else:
            return True;

        return False;

    # Συνδυασμοί, ανά 2 συναρτήσεων περιορισμών, για τις τομές/κορυφές
    constraint_foos_combo = list(combinations(constraint_functions, 2))

    # Υπολογισμός ΟΛΩΝ των σημείων τομής
    intersection_points = []
    for (cf1, cf2) in constraint_foos_combo:
        sol = solve((cf1, cf2), (x1_var, x2_var))
        if sol: # Ώστε να μην προκύψει IndexError!
            intersection_points.append((float(sol[x1_var]), float(sol[x2_var])))

    # Φιλτράρουμε τα σημεία που δεν ικανοποιούν όλους τους περιορισμούς
    feasible_points = []
    for (candidate_x1, candidate_x2) in intersection_points:
        if check_restrictions(candidate_x1, candidate_x2):
            feasible_points.append((candidate_x1, candidate_x2))

    # Βρίσκουμε το μέγιστο της Z συνάρτησης
    best_value = float('-inf')
    for (candidate_x1, candidate_x2) in feasible_points:
        val = Z(candidate_x1, candidate_x2)
        if val > best_value:
            best_value = val

    print('Κορυφές [εφικτές λύσεις]:')
    for (x1_val, x2_val) in feasible_points:
        print(f'  {(x1_val, x2_val)} -> Z = {Z(x1_val, x2_val)}')
    print() # Καλύτερη αισθητική

    # Γραφική παράσταση
    x_vals = np.linspace(-10, 10, 400)
    plt.figure(figsize = (8, 6))

    # Γραμμές περιορισμών
    graphic_representation = [
        ((12 - 6*x_vals) / 3, '(Π1) 6x1 + 3x2 ≥ 12'),
        ((16 - 4*x_vals) / 8, '(Π2) 4x1 + 8x2 ≥ 16'),
        ((30 - 6*x_vals) / 5, '(Π3) 6x1 + 5x2 ≤ 30'),
        ((36 - 6*x_vals) / 7, '(Π4) 6x1 + 7x2 ≤ 36')
    ]
    for (y_vals, label) in graphic_representation:
        plt.plot(x_vals, y_vals, label = label)
    plt.axhline(0, color = 'black')
    plt.axvline(0, color = 'black')

    # Εφικτά σημεία στην γραφική παράσταση
    for (x1_val, x2_val) in feasible_points:
        plt.plot(x1_val, x2_val, 'mo')
    
    # Περίπου σαν Graham Scan για να βρούμε την εφικτή περιοχή!
    feasible_np = np.array(feasible_points)
    center = np.mean(feasible_np, axis = 0)
    sorted_points = sorted(
        feasible_points,
        key = lambda point: np.arctan2(
            point[1] - center[1], point[0] - center[0]
        )
    )
    x_sorted = [point[0] for point in sorted_points]
    y_sorted = [point[1] for point in sorted_points]
    plt.fill(x_sorted, y_sorted, color = 'magenta',
             alpha = 0.3, label = 'Εφικτή περιοχή')

    plt.xlim(-2, 10)
    plt.ylim(-4, 10)
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.legend()
    plt.title('Γραφική Λύση Γραμμικού Προβλήματος | Άσκηση 1η')
    plt.grid(True)

    # ----- Animation setup -----

    z_line, = plt.plot(
        [], [], linestyle = '--',
        color = 'blue', linewidth = 2
    )
    z_label = plt.text(
        0.05, 0.95, '', transform = plt.gca().transAxes,
        color = 'blue', fontweight = 'bold', fontsize = 12,
        verticalalignment = 'top'
    )

    total_frames = 140 # Το animation μέχρι να φτάσει το max Z!
    total_animation_frames = total_frames + 30 # + 30 για να συνεχίσει λίγο ακόμα

    # ----- Προϋπολογισμός με NumPy για smooth animation -----
    t_vals = np.linspace(0, total_animation_frames / total_frames, total_animation_frames)
    precomputed_z_vals = t_vals * best_value
    precomputed_y_vals = precomputed_z_vals[:, None] - 3*x_vals[None, :]
    precomputed_is_inside = np.array([
        any(check_restrictions(x, y_) for x, y_ in zip(x_vals, y))
        for y in precomputed_y_vals
    ])

    was_inside = [False]
    has_printed = [False]
    def animate_z_line(frame):
        current_z = precomputed_z_vals[frame]
        y_vals = precomputed_y_vals[frame]
        is_inside = precomputed_is_inside[frame]

        z_line.set_data(x_vals, y_vals)

        if was_inside[0] and not is_inside and not has_printed[0]:
            print(f'Max Z = {current_z:.2f} - Καθαρά γραφική επίλυση [Animation]')
            has_printed[0] = True
        was_inside[0] = is_inside

        z_label.set_text(f'Z = {current_z:.2f}')

        if frame == total_animation_frames - 1:
            print('\nΤερματισμός animation...')
            ani.event_source.stop()

        return z_line, z_label;

    ani = animation.FuncAnimation(
        plt.gcf(),
        animate_z_line,
        frames = total_animation_frames,
        interval = 20,
        blit = True # Only redraw the parts of the figure
    )               # that have changed between frames!

    plt.show()

    return;

if __name__ == '__main__':
    main()

# References:
# https://stackoverflow.com/questions/17576508/python-matplotlib-drawing-linear-inequality-functions
