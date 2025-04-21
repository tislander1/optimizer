# Cool optimizer for functions in external executables (COFFEE) - April 20, 2025
This program optimizes (maximizes or minimizes) the output from an external EXE. It is currently configured to minimize the eggholder function in the associated EXE, but it can correct anything as long as inputs and outputs are in the right format.

This program wraps global optimization methods from scipy.minimize SHGO, differential evolution, and dual annealing.  SHGO can be used either in simplicial mode, which quickly zeroes in on the optimum, or in Sobol mode, which explores the entire design space.  Results are saved in a CSV format.

## Attribution
This project was initially authored by tislander1 on April 20, 2025, with assistance from GitHub Copilot, an AI programming assistant.

![image](https://github.com/user-attachments/assets/5f878f61-9108-4807-9282-614cc45badb0)

![image](https://github.com/user-attachments/assets/7a2ca5f6-b8e6-4c06-9491-af5929517b83)

![image](https://github.com/user-attachments/assets/cd376d01-d42b-4be0-81af-5c2e2ff97cca)


<pre>
Inputs:
eggholder.exe instance_num variable info val1 val2 ... valN
Example: eggholder.exe 12 "[myvar1 myvar2]" 50.0 60

Outputs:
begin_output instance_num: instance_num, vars: vec: [val1, val2, ... valN], ans: end_output

The eggholder.exe does not actually use the instance_num and val1, val2 ..., so they can be anything. These are for future use with more complex executables.
</pre>
