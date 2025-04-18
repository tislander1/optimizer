import scipy.optimize as opt
import numpy as np
from functools import partial
from time import sleep

evaluation_log = []

def eggholder(vec):
    sleep(0.1) # Simulate a time-consuming function
    print(f"Evaluating {vec}")
    return (-(vec[1] + 47.0)
            * np.sin(np.sqrt(abs(vec[0]/2.0 + (vec[1] + 47.0))))
            - vec[0] * np.sin(np.sqrt(abs(vec[0] - (vec[1] + 47.0))))
            )

def logged_function(func, vec):
    value = func(vec)
    evaluation_log.append((vec, value))  # Log the input and output
    return value

bounds = [(-512, 512), (-512, 512)]
function_name = 'eggholder'

results = dict()
results['shgo_sobol'] = opt.shgo(partial(logged_function, locals()[function_name]), bounds, sampling_method='sobol')

minima_list_inputs = results['shgo_sobol'].xl
minima_list_outputs = results['shgo_sobol'].funl
global_minimum_location = results['shgo_sobol'].x
global_minimum = results['shgo_sobol'].fun

function_evaluations = results['shgo_sobol'].nfev

x = 2
