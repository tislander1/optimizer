import scipy.optimize as opt
import numpy as np
from functools import partial
from time import sleep, time
import multiprocessing


def myfunc(vec):
    sleep(0.2) #Simulate a time-consuming function
    # print(f"Evaluating {vec}")
    return (-(vec[1] + 47.0)
            * np.sin(np.sqrt(abs(vec[0]/2.0 + (vec[1] + 47.0))))
            - vec[0] * np.sin(np.sqrt(abs(vec[0] - (vec[1] + 47.0))))
            )

class get_time:
    """A context manager to measure the execution time of a block of code."""
    def __init__ (self):
        self.start = time()
        self.previous = time()

    def delta(self):
        self.end = time()
        self.interval = self.end - self.start
        self.delta = self.end - self.previous
        self.previous = self.end
        return (self.delta, self.interval)


if __name__ == '__main__':
    multiprocessing.freeze_support()  # For Windows compatibility
    bounds = [(-512, 512), (-512, 512)]
    max_threads = 3  # Number of workers for parallelization
    num_sampling_points = 100  # Number of evaluations
    use_default_num_points = True  # Use default number of points for each method

    # optimization_method = 'shgo_simplicial'  # Uncomment to use shgo with simplicial sampling
    # optimization_method = 'shgo_sobol'  # Uncomment to use shgo with Sobol sampling
    optimization_method = 'differential_evolution'  # Uncomment to use differential evolution
    # optimization_method = 'dual_annealing'  # Uncomment to use dual annealing
    # optimization_method = 'basinhopping'  # Uncomment to use basinhopping


    results = dict()
    t = get_time()
    if optimization_method == 'shgo_sobol':
        print('Running SHGO with Sobol sampling...')
        if use_default_num_points:
            results = opt.shgo(myfunc, bounds, sampling_method='sobol', workers=max_threads)
        else:
            results = opt.shgo(myfunc, bounds, n=num_sampling_points, sampling_method='sobol', workers=max_threads)
    elif optimization_method == 'shgo_simplicial':
        print('Running SHGO with regular sampling...')
        if use_default_num_points:
            results = opt.shgo(myfunc, bounds, sampling_method='shgo_simplicial', workers=max_threads)
        else:
            results = opt.shgo(myfunc, bounds, n=num_sampling_points, sampling_method='shgo_simplicial', workers=max_threads)
    elif optimization_method == 'differential_evolution':
        print('Running Differential Evolution...')
        if use_default_num_points:
            results = opt.differential_evolution(myfunc, bounds, workers=max_threads, updating='deferred')
        else:
            results = opt.differential_evolution(myfunc, bounds, maxfun=num_sampling_points, workers=max_threads, updating='deferred')
    elif optimization_method == 'dual_annealing':
        print('Running Dual Annealing (workers is not supported)...')
        results = opt.dual_annealing(myfunc, bounds)
    print('Elapsed time:', t.delta())

    function_evaluations = results['shgo_sobol'].nfev

x = 2
