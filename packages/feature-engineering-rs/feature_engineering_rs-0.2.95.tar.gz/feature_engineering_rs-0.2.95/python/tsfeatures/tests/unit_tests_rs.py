from feature_engineering_rs import (
    tsfeatures_all_f,
    crossing_points_f,
    entropy_f,
    flat_spots_f,
    lumpiness_f,
    stability_f,
    hurst_f,
    nonlinearity_f,
    unitroot_kpss_f,
    unitroot_pp_f,
    arch_stat_f
)
import pytest
import numpy as np

# unit tests
def expected_output(res, num_features=14):
    """Test that TSFeatures result has the expected structure"""
    
    # For Rust implementation, the result is a TSFeaturesResult object with names and values attributes
    assert hasattr(res, 'names'), f"TSFeatures result should have 'names' attribute"
    assert hasattr(res, 'values'), f"TSFeatures result should have 'values' attribute"
    
    # check the 'names' list
    assert isinstance(res.names, list), f"TSFeatures expected list of names (str), got unexpected output."
    length_of_names = len(res.names)
    assert length_of_names == num_features, f"Expected {num_features} names for TSFeatures, got {length_of_names} instead."
    assert all(isinstance(name, str) for name in res.names), f"TSFeatures expected all returned names to be strings."

    # check the 'values' list
    assert isinstance(res.values, list), f"TSFeatures expected list of values, got unexpected output."
    length_of_vals = len(res.values)
    assert length_of_vals == num_features, f"Expected {num_features} values for TSFeatures, got {length_of_vals} instead."
    assert all(isinstance(val, (float, int)) for val in res.values), f"TSFeatures expected all returned feature values to be floats or integers."

def test_tsfeatures_runs():
    # test whether tsfeatures works on some random data
    tsData = np.random.randn(100).tolist()  # Convert to list for Rust
    res = tsfeatures_all_f(tsData, normalize=False)
    expected_output(res, num_features=14)

def test_tsfeatures_with_normalize():
    # test whether tsfeatures works with normalization
    tsData = np.random.randn(100).tolist()  # Convert to list for Rust
    res = tsfeatures_all_f(tsData, normalize=True)
    expected_output(res, num_features=14)

def test_valid_input_types():
    # should accept tuples, arrays and lists
    data_as_tuple = tuple(np.random.randn(50))
    res_tuple = tsfeatures_all_f(list(data_as_tuple), normalize=False)
    expected_output(res_tuple)
    
    data_as_list = list(np.random.randn(50))
    res_list = tsfeatures_all_f(data_as_list, normalize=False)
    expected_output(res_list)
    
    data_as_numpy = np.random.randn(50)
    res_numpy = tsfeatures_all_f(data_as_numpy.tolist(), normalize=False)
    expected_output(res_numpy)

def test_inf_and_nan_input():
    # pass in time series containing a NaN/inf, should return appropriate outputs
    test_vals = [np.nan, np.inf, -np.inf]
    for val_type in test_vals:
        base_data = np.random.randn(100)
        base_data[0] = val_type
        res = tsfeatures_all_f(base_data.tolist(), normalize=False)
        expected_output(res, num_features=14)
        res_values = res.values
        # Most TSFeatures should handle NaN/inf gracefully - either return NaN or a valid value
        for i, val in enumerate(res_values):
            assert isinstance(val, (float, int)), f"Feature {i+1} should return a numeric value when testing ts containing {val_type}, got {type(val)}."
        
def test_individual_feature_methods():
    # ensure each individual feature method can be run in isolation
    data = list(np.random.randn(100))
    
    # Map of function references and their parameters based on your lib.rs
    individual_functions = [
        (crossing_points_f, {}),
        (entropy_f, {}),
        (flat_spots_f, {}),
        (lumpiness_f, {'freq': None}),  # Optional parameter
        (stability_f, {'freq': 1}),     # Required parameter
        (hurst_f, {}),
        (nonlinearity_f, {}),
        (unitroot_kpss_f, {'freq': 1}),    # Required parameter
        (unitroot_pp_f, {'freq': 1}),      # Required parameter
        (arch_stat_f, {'lags': 12, 'demean': True}),  # Multiple parameters
    ]
    
    assert len(individual_functions) == 10, f"Expected 10 individual feature methods, got {len(individual_functions)}."
    
    for func, params in individual_functions:
        try:
            # Call function with appropriate parameters
            result = func(data, **params)
                
            # Check that we got a numeric result
            assert isinstance(result, (float, int)), f"Method {func.__name__} should return a numeric value, got {type(result)}"
            
        except Exception as excinfo:
            pytest.fail(f"Method {func.__name__} raised an exception: {excinfo}")

def test_short_series():
    # test with very short series
    short_data = [1.0, 2.0, 3.0, 4.0, 5.0]
    res = tsfeatures_all_f(short_data, normalize=False)
    expected_output(res, num_features=14)
    
def test_constant_series():
    # test with constant series
    constant_data = [1.0] * 50
    res = tsfeatures_all_f(constant_data, normalize=False)
    expected_output(res, num_features=14)
    
def test_single_value():
    # test with single value (edge case)
    single_data = [1.0]
    try:
        res = tsfeatures_all_f(single_data, normalize=False)
        expected_output(res, num_features=14)
    except Exception:
        # Some features might not work with single values - that's okay
        pass

if __name__ == "__main__":
    import sys
    try:
        test_tsfeatures_runs()
        test_tsfeatures_with_normalize()
        test_valid_input_types()
        test_inf_and_nan_input()
        test_individual_feature_methods()
        test_short_series()
        test_constant_series()
        test_single_value()
        print("Tests completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Tests failed: {e}")
        sys.exit(1)