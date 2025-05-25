# Γραφική παράσταση για το β ερώτημα της άσκησης 4
# Hardcoded βάση του αποτελέσματος του αρχείου: lin_prog_code_HW2_4b.py

import matplotlib.pyplot as plt
import networkx as nx

# Detailed nodes for the Branch & Bound tree
detailed_nodes = [
    ('N0', 'Z=15.333\nx1=0.33, x2=5.00, x3=2.33,\nx4=0.33, x5=7.00, x6=0.33,\nx7=0.00\nBranch on x1', None),
    ('N1', 'Z=15.500\nx1=0.00, x2=0.00, x3=7.50,\nx4=0.00, x5=7.50, x6=0.00,\nx7=0.50\nBranch on x3', 'N0'),
    ('N2', 'Z=15.500\nx1=0.00, x2=0.50, x3=7.00,\nx4=0.00, x5=7.50, x6=0.00,\nx7=0.50\nBranch on x2', 'N1'),
    ('N3', 'Z=16.000\nx1=0.00, x2=0.00, x3=7.00,\nx4=1.00, x5=7.00, x6=1.00,\nx7=0.00\nInteger ✓',    'N2'),
    ('N4', 'Z=15.500\nx1=0.00, x2=1.00, x3=6.50,\nx4=0.00, x5=7.50, x6=0.00,\nx7=0.50\nMax Depth',    'N2'),
    ('N5', 'Z=16.000\nx1=0.00, x2=0.00, x3=8.00,\nx4=0.00, x5=7.00, x6=0.00,\nx7=1.00\nInteger ✓',    'N1'),
    ('N6', 'Z=16.000\nx1=1.00, x2=5.00, x3=1.00,\nx4=7.00, x5=1.00, x6=1.00,\nx7=0.00\nInteger ✓',    'N0'),
]

# Create graph
G = nx.DiGraph()
for (node_id, label, parent) in detailed_nodes:
    G.add_node(node_id, label = label)
    if parent:
        G.add_edge(parent, node_id)

# Layout
pos = nx.spring_layout(G, k = 5)

# Plot
plt.figure(figsize = (16, 12))
nx.draw(
    G,
    pos,
    with_labels = False,
    node_color  = '#FFF7E6',
    edge_color  = '#555',
    node_size   = 16000
)
labels = nx.get_node_attributes(G, 'label')
nx.draw_networkx_labels(
    G,
    pos,
    labels      = labels,
    font_size   = 8,
    font_family = 'monospace'
)

plt.title(
    'Δέντρο Branch & Bound (3 Ακέραιες Λύσεις)',
    fontsize = 14,
    weight   = 'bold'
)
plt.axis('off')
plt.tight_layout()
plt.show()
