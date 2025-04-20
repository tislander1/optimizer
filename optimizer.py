import re
import subprocess
import pandas as pd
import multiprocessing
from time import sleep, time
import scipy.optimize as opt




def myfunc(vec, *args):
    executable = str(args[1])  # Get the executable name from args
    variables_liststr = str(args[2])  # Get the variable names list from args
    maximize = bool(args[3])  # Get the maximize flag from args
    command_string = executable + ' ' + variables_liststr + ' '+ ' '.join(str(item) for item in vec)

    maximize_factor = -1 if maximize else 1  # Set the factor for maximizing or minimizing

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
            return maximize_factor * float('inf')  # Return a high value to indicate failure
        print(f"Command executed: {command_string}, Output: {output}")
        args[0].append({'in': vec, 'out': output})  # Append the input and output to the shared list
        return maximize_factor * output

    except Exception as e:
        print(f"Exception occurred while executing command: {e}")
        return float('inf')  # Return a high value to indicate failure

def fix_results_polarity(results, maximize):
    """Fix the polarity of the results based on the maximize flag."""
    if maximize:
        results.fun = -results.fun  # Negate the function value for maximization
        if 'funl' in results:
            results.funl = -results.funl  # Negate local optimum output if present
    return results

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

    #begin fields to put into the future GUI ----------------------------------------------

    # Define the bounds for the optimization variables in a table format
    bounds_table = pd.DataFrame( #define a dataframe with columns 'variable' 'lower bound' and 'upper bound'
        {
            'variable': ['x1', 'x2'],
            'lower bound': [-512, -512],
            'upper bound': [512, 512]
        },
    )

    max_threads = 3  # Number of workers for parallelization
    num_sampling_points = 100  # Number of evaluations
    use_default_num_points = True  # Use default number of points for each method

    # optimization_method = 'shgo_simplicial'  # Uncomment to use shgo with simplicial sampling
    # optimization_method = 'shgo_sobol'  # Uncomment to use shgo with Sobol sampling
    optimization_method = 'differential_evolution'  # Uncomment to use differential evolution
    # optimization_method = 'dual_annealing'  # Uncomment to use dual annealing
    # optimization_method = 'basinhopping'  # Uncomment to use basinhopping

    executable = 'python eggholder.py 1'  # Replace with your executable 
    csv_results_file = 'results.csv'  # CSV results file

    maximize = True  # Set to True if you want to maximize the function
    # If maximize is True, the function will be negated to find the maximum

    #end fields to put into the future GUI ---------------------------------------------

    # Convert the DataFrame to a list of tuples for bounds, e.g., [(-512, 512), (-512, 512)]
    # This is necessary for the optimization functions in scipy.optimize
    # The bounds are defined as tuples of (lower bound, upper bound) for each variable
    bounds = [tuple(x) for x in bounds_table[['lower bound', 'upper bound']].to_numpy()]
    variables_list = bounds_table['variable'].to_numpy()  # Get the variable names
    variables_liststr = '"' + str(variables_list) + '"'  # Convert to string format for the command line

    with multiprocessing.Manager() as manager:  # Create a manager
        shared_list = manager.list()  # Create a synchronized list

        results = dict()
        t = get_time()
        if optimization_method == 'shgo_sobol':
            print('Running SHGO with Sobol sampling...')
            if use_default_num_points:
                results = opt.shgo(myfunc, args = (shared_list, executable, variables_liststr, maximize),  bounds=bounds, sampling_method='sobol', workers=max_threads)
            else:
                results = opt.shgo(myfunc, args = (shared_list, executable, variables_liststr, maximize), bounds=bounds, n=num_sampling_points, sampling_method='sobol', workers=max_threads)
        elif optimization_method == 'shgo_simplicial':
            print('Running SHGO with regular sampling...')
            if use_default_num_points:
                results = opt.shgo(myfunc, args = (shared_list, executable, variables_liststr, maximize), bounds=bounds, sampling_method='shgo_simplicial', workers=max_threads)
            else:
                results = opt.shgo(myfunc, args = (shared_list, executable, variables_liststr, maximize), bounds=bounds, n=num_sampling_points, sampling_method='shgo_simplicial', workers=max_threads)
        elif optimization_method == 'differential_evolution':
            print('Running Differential Evolution...')
            if use_default_num_points:
                results = opt.differential_evolution(myfunc, args = (shared_list, executable, variables_liststr, maximize), bounds=bounds, workers=max_threads, updating='deferred')
            else:
                results = opt.differential_evolution(myfunc, args = (shared_list, executable, variables_liststr, maximize), bounds=bounds, maxfun=num_sampling_points, workers=max_threads, updating='deferred')
        elif optimization_method == 'dual_annealing':
            print('Running Dual Annealing (workers is not supported)...')
            results = opt.dual_annealing(myfunc, args = (shared_list, executable, variables_liststr, maximize), bounds=bounds)
        print('Elapsed time:', t.delta())

        results = fix_results_polarity(results, maximize)  # Fix the polarity of the results if maximizing

        function_evaluations = results.nfev
        print('Function evaluations:', function_evaluations)
        print('Global optimum input:', results.x)
        print('Global optimum output:', results.fun)
        if 'xl' in results:
            print('Local optimum inputs:', results.xl)
        if 'funl' in results:
            print('Local optimum outputs:', results.funl)

        # print(shared_list)

        # Convert shared_list into a DataFrame
        columns = list(variables_list) + ['out']  # Use variable names from variables_list and add 'out' for the output
        data = []

        for entry in shared_list:
            row = list(entry['in']) + [entry['out']]  # Combine input variables and output into a single row
            data.append(row)

        results_df = pd.DataFrame(data, columns=columns)
        # sort the DataFrame by the output column in ascending order
        results_df.sort_values(by='out', ascending=(not maximize), inplace=True)

        # Print the resulting DataFrame
        results_df.to_csv(csv_results_file, index=False)
        print("Results DataFrame has been exported to: " + str(csv_results_file))

        x = 2

x = 2
