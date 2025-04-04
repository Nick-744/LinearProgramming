import matplotlib.pyplot as plt
import numpy as np

def main():
    # Δημιουργούμε πίνακα τιμών του c2
    c2_vals = np.linspace(-1, 4, 500)

    # Υπολογίζουμε τις αντίστοιχες τιμές για κάθε ανισότητα:
    bound1 = (6/7) * c2_vals * (-5/3) # κατώτερο όριο
    bound2 = c2_vals / 2.5            # κατώτερο όριο
    bound3 = c2_vals * 2              # ανώτερο όριο
    bound4 = c2_vals * (3/2.5)        # ανώτερο όριο
    bound5 = c2_vals * (2.143/2.5)    # κατώτερο όριο

    # Υπολογίζουμε τα κατώτερα και ανώτερα όρια
    lower_bound = np.maximum.reduce([bound1, bound2, bound5])
    upper_bound = np.minimum(bound3, bound4)

    # Σχεδίαση
    plt.figure(figsize = (10, 6))
    plt.plot(c2_vals, bound1, label = 'c1 (7/6) > c2 (-5/3)')
    plt.plot(c2_vals, bound2, label = 'c1 2.5 > c2')
    plt.plot(c2_vals, bound3, label = 'c1 < c2 2', linestyle = '--')
    plt.plot(c2_vals, bound4, label = 'c1 2.5 < c2 3', linestyle = '--')
    plt.plot(c2_vals, bound5, label = 'c1 2.5 > c2 2.143', linestyle = ':')

    plt.fill_between(c2_vals, lower_bound, upper_bound, 
                    where = lower_bound < upper_bound, 
                    color = 'cyan', alpha = 0.3, label = 'Έγκυρη περιοχή')

    plt.xlabel('c2')
    plt.ylabel('c1')
    plt.title('Περιορισμοί για τα c1 & c2 ώστε η κορυφή (2.5, 3) να είναι βέλτιστη!')
    plt.grid(True)
    plt.legend()
    plt.ylim(0, 4)
    plt.xlim(-1, 4)

    plt.show()

    return;

if __name__ == '__main__':
    main()
