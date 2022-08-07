import math
import random
from typing import Any, Callable, NewType, TypeGuard
import numpy as np
import matplotlib.pyplot as pyplot


BINS = 3
# largest float32 x such that x * BINS < BINS
ALMOST_ONE = 1.0 - pow(2.0, BINS - 24)

eps = 3

N = 10_000 # number of subjects

delta_f = (BINS -1)/BINS

laplace_parameter = delta_f / eps

# our input ratios are really portions in [0, 1), but I will use the word "ratio". Perturbed data can be outside of that range.
Ratio = NewType('Ratio', float)

def to_ratio(x: Any) -> Ratio:
    v = float(x)
    if math.isnan(v) or math.isinf(v):
        raise ValueError
    return v

# type alias for source distribution function
DistFunction = Callable[..., Ratio]
class Distribution:
    def __init__(self, desc: str, function: DistFunction, **kwargs):
        self.desc: str = desc
        self.function: DistFunction = function
        self.func_args = kwargs

dists: list[Distribution] = []
dists.append(Distribution("uniform", random.random))

def ratio_normal(**kwargs) -> Ratio:
    x =  np.random.normal(**kwargs)
    return to_ratio(x)
    
dists.append(Distribution(
        desc = "normal m= 0.5, sigma = 0.2",
        function =lambda: ratio_normal(loc=0.5,  scale=0.2)))

def main():
    for dist in dists:
        raw_data: list[float] = []
        true_bin: list[int] = []
        perturbed_bin: list[int | None] = []

        for _ in range(N):
            datum = dist.function()
            raw_data.append(datum)
            true_bin.append(datum * BINS)
            perturbed_datum = datum + np.random.laplace(scale =laplace_parameter)

            perturbed_datum *= BINS
            
            perturbed_bin.append(perturbed_datum)
        
        bins = range(math.floor(min(perturbed_bin)),
            math.ceil(max(perturbed_bin)))
        labels = ["True", "Perturbed"]
        pyplot.title(dist.desc)
        pyplot.hist([true_bin, perturbed_bin],
            bins=bins, label=labels)
        pyplot.legend()
        
        pyplot.show()

        same_bin: int = 0
        for i in range(len(true_bin)):
            if perturbed_bin[i] == true_bin[i]:
                same_bin += 1

        print(f'{same_bin} out of {i+1} are in the same bin')

if __name__ == '__main__':
    main()


