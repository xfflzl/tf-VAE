import numpy as np

shape = (64, 784)

mean_vector = np.random.normal(size=shape)
var_vector = np.log(np.exp(np.random.normal(size=shape)) + 1)

X = np.random.normal(size=shape)
marginal_likelihood = -0.5 * np.sum(np.log(2 * np.pi * var_vector) + np.square(X - mean_vector) / var_vector)
print(marginal_likelihood)