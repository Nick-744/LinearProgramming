import matplotlib as plt
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
  b = np.array([[ 5,  2,  9],
                [ 3,  8,  6],
                [ 1,  0,  4],
                [10,  7,  2]])

  fixed_rows  = np.arange(0, 2)
  sorted_rows = b[2:, 1].argsort()[::-1] + 2
  b = b[np.append(fixed_rows, sorted_rows)]

- Οπότε:
  b -> [[ 5  2  9] \\_ ίδια!
        [ 3  8  6] //
        [10  7  2]  \\_ sorted!
        [ 1  0  4]] //
'''

def gaussianElimination(matrix: np.array):
    # Ensure the input data is safe!
    matrix.flags["WRITEABLE"] = False
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

    matrix.flags["WRITEABLE"] = True

    return tempMatrix;

def main():
    a = np.array([[4,0,1, 4],
                  [1,0,3, 10],
                  [1,2,-1, 5]])
    
    b = gaussianElimination(a)
    print(b)

    return;

if __name__ == "__main__":
    main()