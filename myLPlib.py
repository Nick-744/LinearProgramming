import numpy as np

'''
* Sorting arrays in NumPy by column *

- Έστω:
  a = np.array([[1, 0, 1],
                [4, 0, 3],
                [1, 2,-1]])

- a[:, x].argsort()
  Κάνει sort βάσει της στήλης x του πίνακα a,
επιστρέφει τα index με την sorted σειρά.

- Π.χ.:
  a[:, 0].argsort() -> [0 2 1]

- Οπότε:
  a[ a[:, 0].argsort() ] -> [[ 1  0  1] 
                             [ 1  2 -1] 
                             [ 4  0  3]]

https://stackoverflow.com/questions/2828059/sorting-arrays-in-numpy-by-column

- Ως συνέχεια της ιδέας, μπορούμε να διατηρήσουμε ένα
  τμήμα των γραμμών του πίνακα άθικτο!

- Π.χ.:
  b = np.array([[ 5, 2, 9],
                [ 3, 8, 6],
                [ 1, 0, 4],
                [10, 7, 2]])

  fixed_rows  = np.arange(0, 2)
  sorted_rows = b[2:, 1].argsort()[::-1] + 2
  b = b[np.append(fixed_rows, sorted_rows)]

- Οπότε:
  b -> [[ 5  2  9] \\_ ίδια!
        [ 3  8  6] //
        [10  7  2]  \\_ sorted!
        [ 1  0  4]] //
'''

'''
* Add an extra column to a NumPy array *

- Έστω:
  a = np.array([[4, 0, 1,  4],
                [1, 0, 3, 10],
                [1, 2,-1,  5],
                [4, 3, 5, 10]])

- Ισχύει:
  np.c_[ a[:, [2, 1, 0]], a[:, 3] ] -> [[ 1  0  4  4]
                                        [ 3  0  1 10]
                                        [-1  2  1  5]
                                        [ 5  3  4 10]]

https://stackoverflow.com/questions/8486294/how-do-i-add-an-extra-column-to-a-numpy-array
'''

'''
- numpy.vstack(tup, *, dtype=None, casting='same_kind')
  Stack arrays in sequence vertically (row wise)!

https://numpy.org/doc/stable/reference/generated/numpy.vstack.html
'''

# Python Inner Functions
# https://www.geeksforgeeks.org/python-inner-functions/

def gaussianElimination(matrix: np.array) -> np.array:
    # Ensure the input data is safe!
    tempMatrix = np.copy(matrix.astype("float64"))
    
    (rows, cols) = tempMatrix.shape

    '''
    - Calculate how many zeros you have to make
    for the matrix to become upper triangular

    # zerosNum = int((rows * (rows - 1)) / 2)

    Τελικά δεν το χρησιμοποιεί, αλλά μου άρεσε!
    '''
    
    startRow = 0
    for i in range(cols - 1):
        # Make the row with the biggest pivot the 1st line!
        fixed_rows  = np.arange(0, startRow)
        sorted_rows = tempMatrix[startRow:, i].argsort()[::-1] + startRow
        tempMatrix  = tempMatrix[np.append(fixed_rows, sorted_rows)]

        pivot = tempMatrix[startRow, i]
        if pivot == 0:
            continue;
        tempMatrix[startRow, :] = tempMatrix[startRow, :] / pivot # Make pivot = 1 / # Normalize row

        startRow += 1
        for j in range(startRow, rows):
            tempMatrix[j, :] = tempMatrix[j, :] - (tempMatrix[j, i] * tempMatrix[startRow - 1, :])

    return tempMatrix;

def gaussJordanElimination(matrix: np.array) -> np.array:
    tempMatrix = gaussianElimination(matrix) # Upper triangular

    def upperToLower(): # Inner Function
        nonlocal tempMatrix

        # Reverse rows:
        tempMatrix = tempMatrix[::-1]

        # Reverse variables cols:
        reversed_vars = tempMatrix[:, np.arange((cols - 1) - augmented_mat_len, -1, -1)]

        # Append in reversed_vars the augmented matrix:
        tempMatrix = np.c_[reversed_vars, tempMatrix[:, np.arange(cols - augmented_mat_len, cols)]]

        return;

    (rows, cols) = tempMatrix.shape
    augmented_mat_len = max(rows, cols) - min(rows, cols)
    if rows == cols:
        augmented_mat_len += 1 # So the following changes are valid!
    
    upperToLower() # Transform upper to lower triangular

    if rows == cols:
        augmented_mat_len = 0
        rows -= 1 # Cheat in min(rows, cols)! Upper triangular comes at top!
    
    # Make sure that the upper triangular is at top!
    for _ in range(min(rows, cols)):
        last_row = tempMatrix[-1]
        first_lines = tempMatrix[np.arange((cols -1 ) - augmented_mat_len)]
        tempMatrix = np.vstack([last_row, first_lines])
    
    # Lower triangular (performed with code for upper triangular)
    startRow = 0
    for i in range(cols - 1):
        startRow += 1
        for j in range(startRow, rows):
            tempMatrix[j, :] = tempMatrix[j, :] - (tempMatrix[j, i] * tempMatrix[startRow - 1, :])

    upperToLower()

    return tempMatrix;

def main():
    ab = np.array([[4, 1, 2,-3,-16],
                   [-3,3,-1, 4, 20],
                   [-1,2, 5, 1, -4],
                   [5, 4, 3,-1,-10]])
    
    x = gaussJordanElimination(ab)
    print(x)
    print(np.allclose(np.dot(ab[:, np.arange(ab.shape[1] - 1)], x[:, -1]), ab[:, -1])) # Check solution!
    # https://numpy.org/doc/2.2/reference/generated/numpy.linalg.solve.html

    return;

if __name__ == "__main__":
    main()
