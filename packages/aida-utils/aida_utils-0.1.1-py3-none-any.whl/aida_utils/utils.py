from scipy.spatial.distance import squareform
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
import random
import statistics
import collections
import matplotlib.cm as cm
import matplotlib.colors as colors
import math

from numpy import maximum

## Topological data analysis utilities
def alter_distances(distances, max_amount=0):
    if max_amount == 0:
        max_amount = np.std(distances) / 50
    changer = lambda t: t + random.uniform(0, max_amount)
    return np.array([changer(d) for d in distances])

def calculate_mst(distances):
    X = csr_matrix(squareform(distances))
    mst = minimum_spanning_tree(X)
    return np.nonzero(mst)

def add_mst_to_links(links, mst):
    for i in range(0,len(mst[0])):
        # links.append('{"source":' + str(mst[0][i]) + ', "target":' + str(mst[1][i]) + '}')
        links.append([mst[0][i], mst[1][i]])
    return links

def multi_mst(distances, nr_msts=10):
    """
    Generate multiple minimum spanning trees from the given distances.
    """
    links = []
    for _ in range(nr_msts):
        altered_distances = alter_distances(distances)
        mst = calculate_mst(altered_distances)
        add_mst_to_links(links, mst)
    return links

## Rescaling utilities
def rescale(x, domain_min, domain_max, range_min, range_max):
    scale = (range_max - range_min) / (domain_max - domain_min)
    return range_min + (x - domain_min) * scale

def rescale_array(arr, domain_min, domain_max, range_min, range_max):
    return np.array([rescale(x, domain_min, domain_max, range_min, range_max) for x in arr])

def rescale_matrix(matrix, domain_min, domain_max, range_min, range_max):
    return np.array([[rescale(x, domain_min, domain_max, range_min, range_max) for x in row] for row in matrix])

## Feature ranking utilities
def _is_numeric_value(val):
    return isinstance(val, (int, float))

def _median_difference_numeric(arr1, arr2, feature, normalised=True):
    """
    Calculates the difference between the medians of a specified feature
    in two arrays of dictionaries.

    Args:
        arr1 (list): The first list of dictionaries.
        arr2 (list): The second list of dictionaries.
        feature (str): The key in the dictionaries to extract numeric values from.
        normalised (bool, optional): If True, normalises the feature values
                                     between 0 and 1 before calculating medians.
                                     Defaults to True.

    Returns:
        float: The difference between the medians (median1 - median2).
               Returns 0.0 if an error occurs or if no numeric values are found.
    """
    try:
        if normalised:
            arr1_values = [d[feature] for d in arr1]
            arr2_values = [d[feature] for d in arr2]

            # Combine all values to determine the scaling domain
            all_values = arr1_values + arr2_values

            # Handle cases where no values are present or values are not numeric
            if not all_values:
                return 0.0
            
            # Ensure all values are numeric for min/max calculation
            numeric_all_values = [v for v in all_values if isinstance(v, (int, float))]
            if not numeric_all_values:
                return 0.0 # No numeric values to process

            min_val = min(numeric_all_values)
            max_val = max(numeric_all_values)

            # Handle division by zero if all values are identical
            if min_val == max_val:
                # If all values are the same, their scaled medians will also be the same.
                # Thus, the difference will be zero.
                return 0.0

            # Linear scaling function
            def scale_value(val):
                return (val - min_val) / (max_val - min_val)

            # Calculate scaled medians
            scaled_arr1_values = [scale_value(v) for v in arr1_values if isinstance(v, (int, float))]
            scaled_arr2_values = [scale_value(v) for v in arr2_values if isinstance(v, (int, float))]

            if not scaled_arr1_values or not scaled_arr2_values:
                return 0.0 # Not enough numeric values for median

            median_1 = statistics.median(scaled_arr1_values)
            median_2 = statistics.median(scaled_arr2_values)
            
            return median_1 - median_2
        else:
            # If not normalised
            # Extract values, filtering out non-numeric entries
            arr1_values = [d[feature] for d in arr1 if isinstance(d[feature], (int, float))]
            arr2_values = [d[feature] for d in arr2 if isinstance(d[feature], (int, float))]
            
            if not arr1_values or not arr2_values:
                return 0.0 # Not enough numeric values for median

            median_1 = statistics.median(arr1_values)
            median_2 = statistics.median(arr2_values)
            
            return median_1 - median_2
    except Exception as e:
        # Mimic console.log for debugging purposes
        print(f"Feature: {feature}")
        if arr1:
            print(f"First element of arr1: {arr1[0]}")
        print(f"Error: {e}")
        return 0.0 # Return 0.0 or handle the error as appropriate for your application

def _proportion_difference_categorical(arr1, arr2, feature):
    """
    Calculates the sum of absolute differences in proportions for each category
    of a specified feature between two lists of dictionaries.

    Procedure:
    1. Extract all values for the 'feature' from arr1 and arr2.
    2. Identify all unique categories (factors) present across both arrays.
    3. Count occurrences of each category in arr1 and arr2.
    4. Normalise counts to proportions for arr1 and arr2.
    5. For each category, calculate the absolute difference between its proportion in arr1 and arr2.
    6. Sum these absolute differences.

    Args:
        arr1 (list): The first list of dictionaries.
        arr2 (list): The second list of dictionaries.
        feature (str): The key in the dictionaries representing the categorical feature.

    Returns:
        float: The sum of absolute differences in proportions.
               Returns 0.0 if either input array is empty or an error occurs.
    """
    try:
        arr1_values = [d.get(feature) for d in arr1] # Use .get to handle missing feature gracefully
        arr2_values = [d.get(feature) for d in arr2]

        # Get all unique factors from both arrays
        # Use set for uniqueness and list for consistent iteration order
        all_factors = list(set(arr1_values + arr2_values))

        # Handle None values if feature might be missing in some dictionaries
        # Remove None from factors if it's not a valid category to compare
        all_factors = [f for f in all_factors if f is not None]

        # Count occurrences for each array
        arr1_counts = collections.Counter(arr1_values)
        arr2_counts = collections.Counter(arr2_values)

        arr1_len = len(arr1)
        arr2_len = len(arr2)

        # Calculate proportions for each category
        # Handle empty arrays to prevent ZeroDivisionError
        arr1_proportions = {}
        if arr1_len > 0:
            for factor in all_factors:
                arr1_proportions[factor] = arr1_counts.get(factor, 0) / arr1_len
        else: # If arr1 is empty, all its proportions are 0
            for factor in all_factors:
                arr1_proportions[factor] = 0.0

        arr2_proportions = {}
        if arr2_len > 0:
            for factor in all_factors:
                arr2_proportions[factor] = arr2_counts.get(factor, 0) / arr2_len
        else: # If arr2 is empty, all its proportions are 0
            for factor in all_factors:
                arr2_proportions[factor] = 0.0

        # Calculate the sum of absolute differences
        total_sum = 0.0
        for factor in all_factors:
            prop1 = arr1_proportions.get(factor, 0.0)
            prop2 = arr2_proportions.get(factor, 0.0)
            total_sum += prop1 - prop2

        return total_sum

    except Exception as e:
        # Mimic console.log for debugging purposes
        print(f"Feature: {feature}")
        if arr1:
            print(f"First element of arr1: {arr1[0]}")
        print(f"Error: {e}")
        return 0.0 # Return 0.0 or handle the error as appropriate for your application


def median_rank_difference(arr1, arr2, features):
    """
    Calculates the median or proportion difference for a list of features
    between two arrays of dictionaries and returns them sorted by difference.

    It determines if a feature is numeric or categorical based on the value
    of the feature in the first element of arr1.

    Args:
        arr1 (list): The first list of dictionaries.
        arr2 (list): The second list of dictionaries.
        features (list): A list of strings, where each string is a feature key.

    Returns:
        list: A list of dictionaries, each with 'feature' and 'difference' keys,
              sorted in descending order by 'difference'.
              Returns an empty list if an error occurs.
    """
    differences = []

    try:
        for f in features:
            # Determine if the feature is numeric or categorical based on the first element of arr1.
            # This mimics the JavaScript behaviour. Be aware that this assumes
            # type consistency across the dataset for a given feature.
            is_feature_numeric = False
            if arr1 and f in arr1[0]:
                is_feature_numeric = _is_numeric_value(arr1[0][f])
            elif arr2 and f in arr2[0]: # If arr1 is empty, check arr2
                is_feature_numeric = _is_numeric_value(arr2[0][f])
            
            # If both arrays are empty or the feature is missing, we might default.
            # The helper functions already return 0.0 in these edge cases.
            
            if is_feature_numeric:
                diff = _median_difference_numeric(arr1, arr2, f)
                differences.append({'feature': f, 'difference': diff})
            else:
                diff = _proportion_difference_categorical(arr1, arr2, f)
                differences.append({'feature': f, 'difference': diff})
        filtered_differences = [item for item in differences if not math.isnan(item['difference'])]
        minimum = min(map(lambda x: x['difference'], filtered_differences))
        maximum = max(map(lambda x: x['difference'], filtered_differences))

        absolute_max = max(abs(minimum), abs(maximum))
        if absolute_max == 0:
            absolute_max = 1  # prevent division by zero
        for item in filtered_differences:
            item['difference'] = item['difference'] / absolute_max
    except Exception as e:
        print(f"Error in median_rank_difference: {e}")
        return []

    # Sort the differences in descending order
    return sorted(filtered_differences, key=lambda x: x['difference'], reverse=True)

def interpolated_colour(value, vmin=-1, vmax=1):
    """
    Interpolates a colour between red (-1), white (0), and blue (1).

    Args:
        value (float): The numerical value to map to a colour, expected between vmin and vmax.
        vmin (float): The minimum value of the data range, corresponding to red. Defaults to -1.
        vmax (float): The maximum value of the data range, corresponding to blue. Defaults to 1.

    Returns:
        tuple: An RGBA tuple (red, green, blue, alpha) where each component is between 0 and 1.
    """
    # Define the colormap (Red-White-Blue)
    # RdBu goes from Red (low) -> White (mid) -> Blue (high)
    cmap = cm.get_cmap('RdBu')

    # Normalise the input value to the [0, 1] range of the colormap
    # The normalisation maps vmin to 0, vmax to 1, and 0 to 0.5 (for a symmetrical diverging map)
    norm = colors.Normalize(vmin=vmin, vmax=vmax)

    # Get the RGBA colour
    rgba_colour = cmap(norm(value))
    
    # Extract RGB components (first three elements)
    # Multiply by 255 and convert to integer to get 0-255 range for SVG
    r = int(rgba_colour[0] * 255)
    g = int(rgba_colour[1] * 255)
    b = int(rgba_colour[2] * 255)
    
    return f"rgb({r},{g},{b})"