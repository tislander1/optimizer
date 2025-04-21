# GUI + Optimizer for external executables
# tislander1 - April 20, 2025
# Some code and assistance provided by GitHub Copilot (AI programming assistant).

import re
import threading
import subprocess
import pandas as pd
import multiprocessing
import scipy.optimize as opt
from time import sleep, time

import tkinter as tk
from tkinter import ttk

def run_optimization_thread():
    # Run the optimization process in a separate thread
    status_label.config(text="Status: Running...")
    threading.Thread(target=run_optimization, daemon=True).start()

# Function to handle double-click on a cell to edit it
def edit_cell(event):
    # Get the selected item
    selected_item = bounds_table.selection()
    if not selected_item:
        return

    # Get the column and row clicked
    region = bounds_table.identify("region", event.x, event.y)
    if region != "cell":
        return

    column = bounds_table.identify_column(event.x)
    row_id = bounds_table.identify_row(event.y)

    # Get the bounding box of the cell
    bbox = bounds_table.bbox(row_id, column)
    if not bbox:
        return  # If bbox is None, the cell is not visible

    x, y, width, height = bbox

    # Get the current value of the cell
    current_value = bounds_table.item(row_id, "values")[int(column[1]) - 1]

    # Create an Entry widget over the cell
    entry = tk.Entry(bounds_table, bg="lightyellow")  # Highlight the cell with a yellow background
    entry.insert(0, current_value)
    entry.place(x=x, y=y, width=width, height=height)

    # Function to save the new value
    def save_edit(event=None):
        new_value = entry.get()
        try:
            # Validate numeric input for Lower Bound and Upper Bound columns
            if column in ("#2", "#3") and new_value.strip() != "":
                float(new_value)  # Ensure it's a valid float
            # Update the Treeview with the new value
            values = list(bounds_table.item(row_id, "values"))
            values[int(column[1]) - 1] = new_value
            bounds_table.item(row_id, values=values)
        except ValueError:
            print("Invalid input. Please enter a numeric value for bounds.")
        finally:
            entry.destroy()

    # Bind events to save the edit
    entry.bind("<Return>", save_edit)  # Save on Enter key
    entry.bind("<FocusOut>", save_edit)  # Save when focus is lost
    entry.focus()


def myfunc(vec, *args):
    executable = str(args[1])  # Get the executable name from args
    variables_liststr = str(args[2])  # Get the variable names list from args
    maximize = bool(args[3])  # Get the maximize flag from args
    instance_num = 1  # Instance number for the command
    command_string = executable + ' ' + str(instance_num) + ' ' + variables_liststr + ' '+ ' '.join(str(item) for item in vec)

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
    try:

        # Get user inputs from the GUI
        optimization_method = optimization_method_var.get()
        executable = executable_var.get()
        csv_results_file = csv_results_file_var.get()
        tolerance = float(tolerance_var.get())
        maximize = maximize_var.get() == "maximize"
        max_threads = max_threads_var.get()
        max_threads = int(max_threads) if max_threads.isdigit() else 1  # Default to 1 if not a digit

        # Create the bounds DataFrame
        # Get bounds data from the Treeview
        bounds_table = get_bounds_from_table()



        # Convert bounds to tuples
        bounds = [tuple(x) for x in bounds_table[['lower bound', 'upper bound']].to_numpy()]
        variables_list = bounds_table['variable'].to_numpy()
        variables_liststr = '"' + str(variables_list) + '"'

        # Run the optimization process
        with multiprocessing.Manager() as manager:
            shared_list = manager.list()
            results = dict()
            if optimization_method == 'shgo_sobol':
                print("Using SHGO with Sobol sampling")
                results = opt.shgo(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds, sampling_method='sobol', minimizer_kwargs={'f_tol': tolerance}, workers=max_threads)
            elif optimization_method == 'shgo_simplicial':
                print("Using SHGO with simplicial sampling")
                results = opt.shgo(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds, sampling_method='simplicial', minimizer_kwargs={'f_tol': tolerance}, workers=max_threads)
            elif optimization_method == 'differential_evolution':
                print("Using differential evolution")
                results = opt.differential_evolution(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds, workers=max_threads, updating='deferred', atol=0, tol=tolerance)
            elif optimization_method == 'dual_annealing':
                print("Using dual annealing.  Workers and tolerance are not supported.")
                results = opt.dual_annealing(myfunc, args=(shared_list, executable, variables_liststr, maximize), bounds=bounds)

            # Save results to CSV
            columns = list(variables_list) + ['out']
            data = []

            # Convert the shared list to a regular list for processing
            shared_list = list(shared_list)

            # sort shared_list by the output value, ascending if minimizing, descending if maximizing
            shared_list.sort(key=lambda x: x['out'], reverse=maximize)

            for entry in shared_list:
                row = list(entry['in']) + [entry['out']]
                data.append(row)
            results_df = pd.DataFrame(data, columns=columns)
            results_df.to_csv(csv_results_file, index=False)
            print("Results saved to:", csv_results_file)
            print("Optimization completed successfully.")
            status_code = 0  # Success
    except Exception as e:
        print(f"Error during optimization: {e}")
        status_code = 1  # Error
    finally:
        # Update the status label back to "Ready" in the main thread
        if status_code == 0:
            root.after(0, lambda: status_label.config(text="Status: Ready.  Results saved to " + csv_results_file))
        else:
            root.after(0, lambda: status_label.config(text="Status: Ready.  Error during optimization."))


if __name__ == "__main__":
    multiprocessing.freeze_support()  # For Windows compatibility

    # Create the main window
    root = tk.Tk()
    root.title("Cool optimizer for functions in external executables (COFFEE)")
    root.geometry("550x400")

    # Optimization method
    tk.Label(root, text="Optimization Method:").grid(row=0, column=0, sticky="w")
    optimization_method_var = tk.StringVar(value="shgo_simplicial")
    optimization_method_menu = ttk.Combobox(root, textvariable=optimization_method_var, values=["shgo_sobol", "shgo_simplicial", "differential_evolution", "dual_annealing"])
    optimization_method_menu.grid(row=0, column=1, sticky="w")

    # Executable
    tk.Label(root, text="Executable:").grid(row=1, column=0, sticky="w")
    executable_var = tk.StringVar(value="eggholder.exe")
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
    tk.Label(root, text="Max/Min:").grid(row=4, column=0, sticky="w")
    maximize_var = tk.StringVar(value="minimize")
    maximize_menu = ttk.Combobox(root, textvariable=maximize_var, values=["minimize", "maximize"])
    maximize_menu.grid(row=4, column=1, sticky="w")

    #Max Threads
    tk.Label(root, text="CPU Threads:").grid(row=5, column=0, sticky="w")
    max_threads_var = tk.StringVar(value="1")  # Default to 1 thread
    tk.Entry(root, textvariable=max_threads_var, width=10).grid(row=5, column=1, sticky="w")

    # Bounds table using ttk.Treeview
    tk.Label(root, text="Bounds Table:").grid(row=6, column=0, sticky="w", columnspan=3)

    bounds_table = ttk.Treeview(root, columns=("Variable", "Lower Bound", "Upper Bound"), show="headings", height=5)
    bounds_table.grid(row=7, column=0, columnspan=3, sticky="w")

    # Define column headings
    bounds_table.heading("Variable", text="Variable")
    bounds_table.heading("Lower Bound", text="Lower Bound")
    bounds_table.heading("Upper Bound", text="Upper Bound")

    # Define column widths
    bounds_table.column("Variable", width=100)
    bounds_table.column("Lower Bound", width=100)
    bounds_table.column("Upper Bound", width=100)

    # Add default rows to the table (10 rows, with some blank initially)
    default_bounds = [("x1", "-512", "512"), ("x2", "-512", "512")] + [("", "", "") for _ in range(8)]
    for var, lower, upper in default_bounds:
        bounds_table.insert("", "end", values=(var, lower, upper))
    # Bind double-click to edit cells
    bounds_table.bind("<Double-1>", edit_cell)
        
    # Function to retrieve data from the table
    def get_bounds_from_table():
        bounds_data = []
        for row in bounds_table.get_children():
            values = bounds_table.item(row, "values")
            try:
                if not values[0]:  # Skip empty variable names
                    continue
                # Validate numeric input for Lower Bound and Upper Bound columns

                bounds_data.append({
                    "variable": values[0],
                    "lower bound": float(values[1]),
                    "upper bound": float(values[2])
                })
            except ValueError:
                pass

        x = 2
        print(f"Bounds data: {bounds_data}")
        # Check if bounds_data is empty
        assert len(bounds_data) > 0, "No valid bounds data found."
        return pd.DataFrame(bounds_data)
    

    # Run button
    tk.Button(root, text="Run Optimization", command=run_optimization_thread).grid(row=8, column=0, columnspan=3)
    # Start the GUI event loop

    # Status label
    status_label = tk.Label(root, text="Status: Ready")
    status_label.grid(row=9, column=0, columnspan=3, sticky="w")

    root.mainloop()