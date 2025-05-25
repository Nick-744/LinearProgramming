# Γραφική παράσταση για την άσκηση 5
# Hardcoded βάση του αποτελέσματος του αρχείου: lin_prog_code_HW2_5.py

import matplotlib.pyplot as plt
import networkx as nx

nodes = [
    ('N0', 'Z=109.621\nx1=0.79, x2=2.66,\nx3=2.83\nBranch on x1', None),
    ('N1', 'Z=94.750\nx1=0.00, x2=3.25,\nx3=0.25\nBranch on x2',  'N0'),
    ('N2', 'Z=89.000\nx1=0.00, x2=3.00,\nx3=1.00\nInteger ✓',     'N1'),
    ('N3', 'Infeasible', 'N1'),
    ('N4', 'Z=107.000\nx1=1.00, x2=2.33,\nx3=2.67\nBranch on x2', 'N0'),
    ('N5', 'Z=104.286\nx1=1.21, x2=2.00,\nx3=2.50\nBranch on x1', 'N4'),
    ('N6', 'Z=97.000\nx1=1.00, x2=2.00,\nx3=2.50\nBranch on x3',  'N5'),
    ('N7', 'Z=96.000\nx1=1.00, x2=2.00,\nx3=2.00\nInteger ✓',     'N6'),
    ('N8', 'Infeasible', 'N6'),
    ('N9', 'Z=94.333\nx1=2.00, x2=0.78,\nx3=1.89\nBounded',       'N5'),
    ('N10', 'Infeasible', 'N4'),
]

# Δημιουργία γράφου
G = nx.DiGraph()
for (node_id, label, parent) in nodes:
    G.add_node(node_id, label=label)
    if parent:
        G.add_edge(parent, node_id)

# Θέσεις κόμβων
pos = nx.spring_layout(G, k = 10, iterations = 1000)

# Σχεδίαση κόμβων και ακμών
plt.figure(figsize = (16, 12))
nx.draw(
    G,
    pos,
    with_labels = False,
    node_color  = '#FFF7E6',
    edge_color  = '#555',
    node_size   = 12000,
    arrowsize   = 18
)
labels = nx.get_node_attributes(G, 'label')
nx.draw_networkx_labels(
    G,
    pos,
    labels      = labels,
    font_size   = 9,
    font_family = 'monospace'
)

plt.title(
    'Δέντρο Branch & Bound (Άσκηση 5)',
    fontsize = 14,
    weight   = 'bold'
)
plt.axis('off')
plt.tight_layout()
plt.show()
