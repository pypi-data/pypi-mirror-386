import numpy as np
from ambiegen.crossover.abstract_crossover import AbstractCrossover



class OnePointCrossover(AbstractCrossover):
    def __init__(self, cross_prob: float = 0.9):
        super().__init__(cross_prob)


    def _do_crossover(self, problem, a, b) -> tuple:
        n_var = problem.n_var
        n = np.random.randint(1, n_var-1)
        off_a = np.concatenate([a[:n], b[n:]])
        off_b = np.concatenate([b[:n], a[n:]])
        return off_a, off_b