import math
import random
import numpy as np
import matplotlib.pyplot as pyplot

BINS = 3
eps = 2 

N = 1000 # number of subjects

delta_f = (BINS -1)/BINS

laplace_parameter = delta_f / eps

raw_data: list[float] = []
true_bin: list[int] = []
perturbed_bin: list[int] = []

for _ in range(N):
    datum = random.random()
    raw_data.append(datum)
    true_bin.append(int(math.floor(datum * BINS)))
    perturbed_datum = datum + np.random.laplace(scale =laplace_parameter)
    if perturbed_datum >= 1:
        perturbed_datum = 1 - 0.000000001
    elif perturbed_datum < 0:
        perturbed_datum = 0

    perturbed_bin.append(int(math.floor(perturbed_datum * BINS)))


pyplot.hist(true_bin, align='left')
pyplot.hist(perturbed_bin, align='right')
pyplot.show()

same_bin: int = 0
for i in range(len(true_bin)):
    if perturbed_bin[i] == true_bin[i]:
        same_bin += 1

print(f'{same_bin} out of {i+1} are in the same bin')



