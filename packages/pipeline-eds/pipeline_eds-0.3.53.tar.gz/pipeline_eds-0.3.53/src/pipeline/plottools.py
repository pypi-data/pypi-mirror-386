# pipeline/plottools.py

# import numpy as np # redacted for 0.3.50


# --- Helper Function for Normalization ---
# Normalization function (scaling to range [0, 1])
# Returns the normalized array, min, and max of the original data

#def normalize_np(data):
#    """Normalizes a numpy array to the range [0, 1],
#    and return max and min."""
#    min_val = np.min(data)
#    max_val = np.max(data)
#    # Handle the case where max_val == min_val to avoid division by zero
#    if max_val == min_val:
#        return np.zeros_like(data), min_val, max_val
#    return (data - min_val) / (max_val - min_val), min_val, max_val
def normalize(data):
    """
    Normalize an array to range [0,1] and return max and min.
    Sans numpy.
    """
    min_val = min(data)
    max_val = max(data)
    if max_val == min_val:
        return [0.0] * len(data), min_val, max_val
    return [(d - min_val) / (max_val - min_val) for d in data], min_val, max_val
def normalize_ticks(ticks, data_min, data_max):
    if data_max == data_min:
        return [0.0] * len(ticks)
    return [(t - data_min) / (data_max - data_min) for t in ticks]


# from most recent version of gui_plotly_static.py
# Function to normalize a set of ticks based on the original data's min/max
'''
def normalize_ticks(ticks, data_min, data_max):
    # Handle the case where max_val == min_val
    ticks_arr = np.asarray(ticks, dtype=np.float64)
    if not np.isfinite(data_min) or not np.isfinite(data_max):
        return np.array(ticks_arr - float(data_min)) / (float(data_max) - float(data_min))
    if data_max == data_min:
        return np.zeros_like(ticks_arr)
    return np.array((ticks_arr - float(data_min)) / (float(data_max) - float(data_min)))
'''

def get_ticks_array_n(y_min, y_max, steps):
    # Calculate the step size
    step = (y_max - y_min) / steps
    array_tick_location = []
    for i in range(steps+1):
        array_tick_location.append(y_min+i*step)
    return array_tick_location

def linspace_indices(start, stop, num, length):
    """
    Generates 'num' evenly spaced integer indices between 'start' and 'stop' (inclusive).
    Equivalent to np.linspace(start, stop, num, dtype=int).
    'stop' should typically be len(x_vals) - 1.
    """
    if num <= 0:
        return []
    if num == 1:
        return [int(start)]

    indices = []
    step = (stop - start) / (num - 1)

    for i in range(num):
        # Calculate the index value and round it to the nearest integer
        # This mirrors NumPy's behavior for float-to-int conversion in linspace
        index_val = start + i * step
        indices.append(int(round(index_val)))

    return indices