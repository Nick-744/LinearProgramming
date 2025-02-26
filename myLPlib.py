import matplotlib as plt
import numpy as np

def gaussianElimination(matrix: np.array):
    # Ensure the input data is safe!
    matrix.flags["WRITEABLE"] = False
    tempMatrix = np.copy(matrix)
    
    # Calculate how many zeros you have to make
    # for the matrix to become upper triangular
    rows = tempMatrix.shape[0]
    zerosNum = int((rows * (rows - 1)) / 2)

    if tempMatrix[0, 0] != 0:
        tempMatrix[0, :] = tempMatrix[0, :] / tempMatrix[0, 0] # Normalize 1st row
    
    startRowTemp = 1
    startColTemp = 0
    for i in range(rows, 0, -1): # zerosNum
        for j in range(i - 1):
            tempMatrix[j + startRowTemp, :] = tempMatrix[j + startRowTemp, :] - (tempMatrix[j + startRowTemp, startColTemp] * tempMatrix[startRowTemp - 1, :])
            if tempMatrix[startRowTemp, startColTemp + 1] != 0:
                tempMatrix[j + startRowTemp, :] = tempMatrix[j + startRowTemp, :] / tempMatrix[startRowTemp, startColTemp + 1]
        startRowTemp += 1
        startColTemp += 1

    return tempMatrix;

def main():
    a = np.array([[1,2,3],
                  [1,4,5]])
    
    print(gaussianElimination(a))

    return;

if __name__ == "__main__":
    main()