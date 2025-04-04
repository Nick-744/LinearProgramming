# Άσκηση 6η - β

import matplotlib.pyplot as plt
import networkx as nx
from sympy import Matrix, symbols
from copy import deepcopy
from collections import deque

# Δημιουργία μεταβλητών
(x1, x2, x3, x4, x5, x6, x7) = symbols('x1 x2 x3 x4 x5 x6 x7')
all_vars = [x1, x2, x3, x4, x5, x6, x7]
var_indices = {v: i for i, v in enumerate(all_vars)}

# Πίνακας περιορισμών και αντικειμενική συνάρτηση
A = Matrix([
    [1, 2,  4, -1, 1, 0, 0],
    [2, 3, -1,  1, 0, 1, 0],
    [1, 0,  1,  1, 0, 0, 1]
])
b = Matrix([6, 12, 2])
c = Matrix([2, 1, 6, -4, 0, 0, 0])

# Αρχικές μεταβλητές
initial_basic = [x5, x6, x7]
initial_nonbasic = [x1, x2, x3, x4]

# Γράφος
G = nx.DiGraph()
node_labels = {}
edge_labels = {}
node_id_map = {}
z_values = {}
node_count = 0

queue = deque()
queue.append((initial_basic, initial_nonbasic))
visited = set()

while queue:
    basic_vars, nonbasic_vars = queue.popleft()
    basis_key = tuple(sorted(str(v) for v in basic_vars))
    if basis_key in visited:
        continue;
    visited.add(basis_key)

    B = A[:, [var_indices[v] for v in basic_vars]]
    try:
        B_inv = B.inv()
        xB = B_inv * b
        if any(val < 0 for val in xB):
            continue;
    except:
        continue;

    # Υπολογισμός Z και z_row
    c_B = Matrix([c[var_indices[v]] for v in basic_vars])
    Z_val = float((c_B.T * xB)[0])
    z_row = []
    for v in all_vars:
        if v in basic_vars:
            z_row.append(0)
        else:
            Aj = A[:, var_indices[v]]
            zj = c[var_indices[v]] - (c_B.T * B_inv * Aj)[0, 0]
            z_row.append(zj)

    # Κόμβος γράφου
    basis_set = frozenset(basic_vars)
    if basis_set not in node_id_map:
        node_name = f"v{node_count}"
        node_id_map[basis_set] = node_name

        # Πλήρης λύση και εμφάνιση μόνο x1-x4 (ταξινομημένα)
        full_solution = [0.0] * len(all_vars)
        for i, v in enumerate(basic_vars):
            full_solution[var_indices[v]] = float(xB[i])
        values = tuple(round(full_solution[i], 2) for i in range(4))

        label = f"BI={{{','.join(str(v)[-1] for v in sorted(basic_vars, key=lambda v: int(str(v)[1:])))}}}\n"
        label += f"{values}\nz={Z_val:.2f}"
        node_labels[node_name] = label
        G.add_node(node_name)
        current_node = node_name
        node_count += 1
    else:
        current_node = node_id_map[basis_set]

    z_values[basis_set] = Z_val

    if all(z <= 0 for z in z_row):
        continue;

    # Εξέταση κάθε εισερχόμενης με z > 0
    for entering_idx, zj in enumerate(z_row):
        if zj <= 0:
            continue;

        entering_var = all_vars[entering_idx]
        if entering_var in basic_vars:
            continue;

        d = B_inv * A[:, var_indices[entering_var]]
        ratios = []
        for i in range(len(d)):
            if d[i] > 0:
                ratios.append(xB[i] / d[i])
            else:
                ratios.append(float('inf'))

        if all(r == float('inf') for r in ratios):
            continue;

        min_ratio = min(ratios)
        for i, r in enumerate(ratios):
            if abs(r - min_ratio) < 1e-8:
                exiting_var = basic_vars[i]

                new_basic = basic_vars.copy()
                new_nonbasic = nonbasic_vars.copy()
                new_basic[i] = entering_var
                new_nonbasic[new_nonbasic.index(entering_var)] = exiting_var

                new_key = frozenset(new_basic)
                B_new = A[:, [var_indices[v] for v in new_basic]]
                try:
                    B_new_inv = B_new.inv()
                    xB_new = B_new_inv * b
                    if any(x < 0 for x in xB_new):
                        continue;
                except:
                    continue;

                if new_key not in node_id_map:
                    node_name = f"v{node_count}"
                    node_id_map[new_key] = node_name
                    z_val_new = float((Matrix([c[var_indices[v]] for v in new_basic]).T * xB_new)[0])

                    full_solution = [0.0] * len(all_vars)
                    for i2, v in enumerate(new_basic):
                        full_solution[var_indices[v]] = float(xB_new[i2])
                    values = tuple(round(full_solution[i], 2) for i in range(4))

                    label = f"BI={{{','.join(str(v)[-1] for v in sorted(new_basic, key=lambda v: int(str(v)[1:])))}}}\n"
                    label += f"{values}\nz={z_val_new:.2f}"
                    node_labels[node_name] = label
                    G.add_node(node_name)
                    target_node = node_name
                    node_count += 1
                else:
                    target_node = node_id_map[new_key]

                G.add_edge(current_node, target_node)
                edge_labels[(current_node, target_node)] = f"+{str(entering_var)} / -{str(exiting_var)} =>"

                queue.append((new_basic, new_nonbasic))

# Ζωγραφική!!!
best_node = max(z_values, key=z_values.get)
best_node_name = node_id_map[best_node]
node_colors = ["lightgreen" if node == best_node_name else "peachpuff" for node in G.nodes()]

plt.figure(figsize=(16, 12))

layout = {
    'v0': (0, 0),
    'v3': (2, 1),
    'v2': (1, 0),
    'v1': (1, -1),
    'v4': (2, 0),
    'v5': (3, 0)
}

nx.draw_networkx_nodes(G, layout, node_color = node_colors,
                       edgecolors = "black", node_size = 11000)
nx.draw_networkx_edges(G, layout)
nx.draw_networkx_labels(G, layout, labels = node_labels, font_size = 10)
nx.draw_networkx_edge_labels(G, layout, edge_labels = edge_labels, font_size = 9)

plt.title("Simplex Adjacency Graph")
plt.axis("off")
plt.tight_layout()
plt.show()
