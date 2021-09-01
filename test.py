# coding = utf-8
import numpy as np
#
# matrix = np.array([[2,0],[0,2]])
# p = np.array([[3],[4]])
#
# print(matrix.dot(p)+p)
#

start = 1
stop = 2
length = 10000
x = np.linspace(start, stop, length)
y = x**2
result = sum(y*(stop-start)/length)
print(result)