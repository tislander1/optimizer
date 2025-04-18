from time import sleep
import sys
import numpy as np

def safefloat(value):
    """Convert a string to a float, returning the original string if conversion fails."""
    try:
        return float(value)
    except ValueError:
        return value

args = sys.argv[1:]  # Get command line arguments

if len(args) < 2:
    print("Usage: python eggholder.py <instance_num> <val1> <va12> ... <valN>")
    print("Example: python eggholder.py 12 50.0 60")
    sys.exit(1)

instance_num = int(args[0])

vec = [safefloat(item) for item in args[1:]]  # Convert command line arguments to float

print('Ignore this example string with instance_num: -77 and vec: -42 and ans: -1 or a crash can occur.')

sleep(0.2) #Simulate a time-consuming function
ans = (-(vec[1] + 47.0)
        * np.sin(np.sqrt(abs(vec[0]/2.0 + (vec[1] + 47.0))))
        - vec[0] * np.sin(np.sqrt(abs(vec[0] - (vec[1] + 47.0))))
        )

return_string = f"begin_output instance_num: {instance_num}, vec: {vec}, ans: {ans} end_output"
# The output format is important for the regex to work correctly.
# It should contain "begin_output" and "end_output" markers, and the ans value should be in the format "ans: <value>"
# The output should be a single line with no extra spaces or newlines.
# Example output:
# begin_output instance_num: 12, vec: [50.0, 60.0], ans: -1.234567 end_output
# There can be other lines of output, but they should not interfere with the regex matching.
print(return_string)