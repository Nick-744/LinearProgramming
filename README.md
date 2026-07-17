# 🚁 POST-DISASTER SUPPLY DELIVERY BY DRONES USING LINEAR PROGRAMMING

[`myProject`](myProject/) στο μάθημα: Γραμμική και Συνδυαστική Βελτιστοποίηση [EE916]

## 🧭 Εισαγωγή

Σε κρίσεις (όπως οι σεισμοί και οι πλημμύρες) η γρήγορη διανομή τροφίμων, φαρμάκων και νερού σε δύσβατα σημεία σώσει ζωές. Τα επανδρωμένα μέσα, ωστόσο, συχνά καθυστερούν λόγω πρόσβασης ή συντονισμού. Οι ημιαυτόνομοι δρόνοι (Μη Επανδρωμένα Αεροσκάφη) αποτελούν μία ασφαλή και ευέλικτη λύση στο πρόβλημα. Ωστόσο, το ερώτημα που πρέπει να απαντηθεί είναι:

**Ποιος δρόνος πρέπει να σταλεί, από ποιο σημείο εφοδιασμού, προς ποιον προορισμό και με πόσο φορτίο, ώστε να ελαχιστοποιηθεί το συνολικό «κόστος ανθρωπιστικής παράδοσης»;**

---

## 📦 Requirements

Before running the project, make sure the following Python packages are installed:

```bash
pip install pulp matplotlib numpy
```

---

## ✨ Run the Optimizer (Command-line output)

To run the optimization model and view the results in the terminal:

```bash
python main.py
```

---

## 🎨 Animated Visualization (2D)

To view the solution as a 2D animation:

```bash
python animation_2D.py
```

---

## ⚡ Environment Requirements

- Python >= 3.8
- `pulp` (with built-in CBC solver)
- GUI-capable system to display matplotlib animations
