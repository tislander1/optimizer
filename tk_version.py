import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
import multiprocessing
import scipy.optimize as opt

import re
import subprocess
import multiprocessing
from time import sleep, time

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

def run_optimization():
    # Get user inputs from the GUI
    optimization_method = optimization_method_var.get()
    executable = executable_var.get()
    csv_results_file = csv_results_file_var.get()
    tolerance = float(tolerance_var.get())
    maximize = maximize_var.get() == "True"

    # Create the bounds DataFrame
    bounds_data = []
    for i in range(len(bounds_table_entries)):
        variable = bounds_table_entries[i][0].get()
        lower_bound = float(bounds_table_entries[i][1].get())
        upper_bound = float(bounds_table_entries[i][2].get())
        bounds_data.append({'variable': variable, 'lower bound': lower_bound, 'upper bound': upper_bound})
    bounds_table = pd.DataFrame(bounds_data)

    # Convert bounds to tuples
    bounds = [tuple(x) for x in bounds_table[['lower bound', 'upper bound']].to_numpy()]
    variables_list = bounds_table['variable'].to_numpy()
    variables_liststr = '"' + str(variables_list) + '"'

    # Run the optimization process
    with multiprocessing.Manager() as manager:
        shared_list = manager.list()
        results = dict()
        if optimization_method == 'shgo_sobol':
            results = opt.shgo(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds, sampling_method='sobol')
        elif optimization_method == 'shgo_simplicial':
            results = opt.shgo(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds, sampling_method='simplicial')
        elif optimization_method == 'differential_evolution':
            results = opt.differential_evolution(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds)
        elif optimization_method == 'dual_annealing':
            results = opt.dual_annealing(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds)

        # Save results to CSV
        columns = list(variables_list) + ['out']
        data = []
        for entry in shared_list:
            row = list(entry['in']) + [entry['out']]
            data.append(row)
        results_df = pd.DataFrame(data, columns=columns)
        results_df.to_csv(csv_results_file, index=False)
        print("Results saved to:", csv_results_file)

if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    root.title("Optimization GUI")

    # Optimization method
    tk.Label(root, text="Optimization Method:").grid(row=0, column=0, sticky="w")
    optimization_method_var = tk.StringVar(value="shgo_sobol")
    optimization_method_menu = ttk.Combobox(root, textvariable=optimization_method_var, values=["shgo_sobol", "shgo_simplicial", "differential_evolution", "dual_annealing"])
    optimization_method_menu.grid(row=0, column=1, sticky="w")

    # Executable
    tk.Label(root, text="Executable:").grid(row=1, column=0, sticky="w")
    executable_var = tk.StringVar(value="python eggholder.py 1")
    tk.Entry(root, textvariable=executable_var, width=50).grid(row=1, column=1, sticky="w")

    # CSV results file
    tk.Label(root, text="CSV Results File:").grid(row=2, column=0, sticky="w")
    csv_results_file_var = tk.StringVar(value="results.csv")
    tk.Entry(root, textvariable=csv_results_file_var, width=50).grid(row=2, column=1, sticky="w")

    # Tolerance
    tk.Label(root, text="Tolerance:").grid(row=3, column=0, sticky="w")
    tolerance_var = tk.StringVar(value="1")
    tk.Entry(root, textvariable=tolerance_var, width=10).grid(row=3, column=1, sticky="w")

    # Maximize
    tk.Label(root, text="Maximize:").grid(row=4, column=0, sticky="w")
    maximize_var = tk.StringVar(value="False")
    maximize_menu = ttk.Combobox(root, textvariable=maximize_var, values=["True", "False"])
    maximize_menu.grid(row=4, column=1, sticky="w")

    # Bounds table
    tk.Label(root, text="Bounds Table:").grid(row=5, column=0, sticky="w")
    bounds_table_entries = []
    for i, variable in enumerate(["x1", "x2"]):  # Default variables
        variable_var = tk.StringVar(value=variable)
        lower_bound_var = tk.StringVar(value="-512")
        upper_bound_var = tk.StringVar(value="512")
        tk.Entry(root, textvariable=variable_var, width=10).grid(row=6 + i, column=0, sticky="w")
        tk.Entry(root, textvariable=lower_bound_var, width=10).grid(row=6 + i, column=1, sticky="w")
        tk.Entry(root, textvariable=upper_bound_var, width=10).grid(row=6 + i, column=2, sticky="w")
        bounds_table_entries.append((variable_var, lower_bound_var, upper_bound_var))

    # Run button
    tk.Button(root, text="Run Optimization", command=run_optimization).grid(row=8, column=0, columnspan=3)

    # Start the GUI event loop
    root.mainloop()