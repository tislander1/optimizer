import re
import subprocess
import multiprocessing
from time import sleep, time
import scipy.optimize as opt




def myfunc(vec, *args):
    executable = str(args[1])  # Get the executable name from args
    command_string = executable + ' ' + ' '.join(str(item) for item in vec)

    try:
        # Execute the command and capture the output
        result = subprocess.run(
            command_string,  # Command to execute
            shell=True,  # Use shell to execute the command string
            capture_output=True,  # Capture stdout and stderr
            text=True  # Decode output as text
        )

        # Check if the command was successful
        if result.returncode != 0:
            print(f"Error executing command: {result.stderr}")
            return float('inf')  # Return a high value to indicate failure

        # Parse the output (assuming the program prints a single float value)
        output = result.stdout.strip()

        # Use a regular expression to extract the value of ans.
        # The regex looks for the pattern "begin_output" followed by "ans:" and captures the number until "end_output"
        match = re.search(r"begin_output.*?ans:\s*([\d\.\-e]+).*?end_output", output)
        if match:
            output = float(match.group(1))  # Extract the ans value
        else:
            print("No valid output found in the command output.")
            return float('inf')  # Return a high value to indicate failure
        print(f"Command executed: {command_string}, Output: {output}")
        args[0].append({'in': vec, 'out': output})  # Append the input and output to the shared list
        return output

    except Exception as e:
        print(f"Exception occurred while executing command: {e}")
        return float('inf')  # Return a high value to indicate failure

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

    executable = 'python eggholder.py 1'  # Replace with your executable name

    with multiprocessing.Manager() as manager:  # Create a manager
        shared_list = manager.list()  # Create a synchronized list

        results = dict()
        t = get_time()
        if optimization_method == 'shgo_sobol':
            print('Running SHGO with Sobol sampling...')
            if use_default_num_points:
                results = opt.shgo(myfunc, args = (shared_list, executable),  bounds=bounds, sampling_method='sobol', workers=max_threads)
            else:
                results = opt.shgo(myfunc, args = (shared_list, executable), bounds=bounds, n=num_sampling_points, sampling_method='sobol', workers=max_threads)
        elif optimization_method == 'shgo_simplicial':
            print('Running SHGO with regular sampling...')
            if use_default_num_points:
                results = opt.shgo(myfunc, args = (shared_list, executable), bounds=bounds, sampling_method='shgo_simplicial', workers=max_threads)
            else:
                results = opt.shgo(myfunc, args = (shared_list, executable), bounds=bounds, n=num_sampling_points, sampling_method='shgo_simplicial', workers=max_threads)
        elif optimization_method == 'differential_evolution':
            print('Running Differential Evolution...')
            if use_default_num_points:
                results = opt.differential_evolution(myfunc, args = (shared_list, executable), bounds=bounds, workers=max_threads, updating='deferred')
            else:
                results = opt.differential_evolution(myfunc, args = (shared_list, executable), bounds=bounds, maxfun=num_sampling_points, workers=max_threads, updating='deferred')
        elif optimization_method == 'dual_annealing':
            print('Running Dual Annealing (workers is not supported)...')
            results = opt.dual_annealing(myfunc, args = (shared_list, executable), bounds=bounds)
        print('Elapsed time:', t.delta())

        function_evaluations = results.nfev
        print('Function evaluations:', function_evaluations)
        print('Global optimum input:', results.x)
        print('Global optimum output:', results.fun)
        if 'xl' in results:
            print('Local optimum inputs:', results.xl)
        if 'funl' in results:
            print('Local optimum outputs:', results.funl)
        print(shared_list)

x = 2
