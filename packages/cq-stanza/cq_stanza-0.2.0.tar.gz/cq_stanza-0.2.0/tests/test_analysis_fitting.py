import numpy as np
import pytest

from stanza.analysis.fitting import (
    PinchoffFitResult,
    _compute_initial_params,
    _compute_parameter_bounds,
    _map_index_to_voltage,
    derivative_extrema_indices,
    fit_pinchoff_parameters,
    pinchoff_curve,
)
from stanza.analysis.preprocessing import normalize


class TestPinchoffCurve:
    def test_basic_output(self):
        x = np.linspace(-10, 10, 100)
        y = pinchoff_curve(x, 1.0, 1.0, 1.0)
        assert np.all(y >= 0.0)
        assert np.all(y <= 2.0)

    def test_amplitude_scaling(self):
        x = np.array([0.0])
        y1 = pinchoff_curve(x, 1.0, 1.0, 0.0)
        y2 = pinchoff_curve(x, 2.0, 1.0, 0.0)
        assert y2[0] == pytest.approx(2 * y1[0])

    def test_offset_effect(self):
        x = np.array([0.0])
        y1 = pinchoff_curve(x, 1.0, 1.0, 0.0)
        y2 = pinchoff_curve(x, 1.0, 1.0, 2.0)
        assert y2[0] > y1[0]


class TestDerivativeExtremaIndices:
    def test_basic_ordering(self):
        x = np.linspace(-10, 10, 100)
        y = pinchoff_curve(x, 1.0, 1.0, 1.0)
        transition_v_ind, conducting_v_ind, pinchoff_v_ind = derivative_extrema_indices(
            x, y
        )
        assert pinchoff_v_ind < transition_v_ind < conducting_v_ind
        assert y[pinchoff_v_ind] < y[transition_v_ind] < y[conducting_v_ind]

    def test_negative_amplitude(self):
        x = np.linspace(-10, 10, 100)
        y = pinchoff_curve(x, 1.0, -1.0, 1.0)
        transition_v_ind, conducting_v_ind, pinchoff_v_ind = derivative_extrema_indices(
            x, y
        )
        assert conducting_v_ind < transition_v_ind < pinchoff_v_ind
        assert y[conducting_v_ind] > y[transition_v_ind] > y[pinchoff_v_ind]

    def test_returns_integers(self):
        x = np.linspace(-10, 10, 50)
        y = pinchoff_curve(x, 1.0, 1.0, 1.0)
        result = derivative_extrema_indices(x, y)
        assert all(isinstance(idx, int) for idx in result)

    def test_inverted_current_assignment(self):
        x = np.linspace(0, 1, 100)
        y_norm = normalize(pinchoff_curve(np.linspace(-2, 2, 100), -0.5, 2.0, -1.0))
        transition_v_ind, conducting_v_ind, pinchoff_v_ind = derivative_extrema_indices(
            x, y_norm
        )
        assert y_norm[pinchoff_v_ind] < y_norm[conducting_v_ind]

    def test_decreasing_curve_else_branch(self):
        x = np.linspace(0, 1, 100)
        y = 1.0 - pinchoff_curve(x, 1.0, 1.0, -0.5)
        transition_v_ind, conducting_v_ind, pinchoff_v_ind = derivative_extrema_indices(
            x, y
        )
        assert y[pinchoff_v_ind] < y[conducting_v_ind]


class TestComputeInitialParams:
    def test_normalized_data(self):
        v_norm = np.linspace(0, 1, 100)
        i_norm = np.linspace(0, 1, 100)
        params = _compute_initial_params(v_norm, i_norm)
        assert len(params) == 3
        assert params[0] > 0  # amplitude
        assert params[1] > 0  # slope

    def test_constant_arrays(self):
        v_norm = np.ones(100)
        i_norm = np.ones(100)
        params = _compute_initial_params(v_norm, i_norm)
        assert len(params) == 3
        assert params[0] == 0.5  # i_range/2 when ptp=1.0


class TestComputeParameterBounds:
    def test_basic_bounds(self):
        v_norm = np.linspace(0, 1, 100)
        i_norm = np.linspace(0, 1, 100)
        lower, upper = _compute_parameter_bounds(v_norm, i_norm)
        assert len(lower) == 3
        assert len(upper) == 3
        assert np.all(lower < upper)

    def test_invalid_bounds_fallback(self):
        v_norm = np.array([0.5, 0.5])
        i_norm = np.array([0.5, 0.5])
        lower, upper = _compute_parameter_bounds(v_norm, i_norm)
        assert np.all(lower < upper)

    def test_amplitude_bounds_positive(self):
        v_norm = np.linspace(0, 1, 100)
        i_norm = np.linspace(0, 1, 100)
        lower, upper = _compute_parameter_bounds(v_norm, i_norm)
        assert lower[0] > 0

    def test_extreme_values_trigger_defaults(self):
        v_norm = np.array([0.0, 1e6])
        i_norm = np.array([0.0, 1.0])
        lower, upper = _compute_parameter_bounds(v_norm, i_norm)
        assert np.all(lower < upper)
        v_range = 1e6
        max_abs_b = min(20.0 / v_range, 100.0)
        assert lower[1] == pytest.approx(-max_abs_b)
        assert upper[1] == pytest.approx(max_abs_b)

    def test_invalid_bounds_use_defaults(self):
        v_norm = np.array([-10.0, -10.0])
        i_norm = np.array([0.0, 1.0])
        lower, upper = _compute_parameter_bounds(v_norm, i_norm)
        assert np.all(lower < upper)
        v_min, v_max = v_norm.min(), v_norm.max()
        assert v_min == v_max
        a_bounds = (max(0.01 * 1.0, 1e-8), max(2.0 * 1.0, 1.0))
        assert a_bounds[0] < a_bounds[1]


class TestMapIndexToVoltage:
    def test_valid_index(self):
        voltages = np.array([1.0, 2.0, 3.0])
        assert _map_index_to_voltage(0, voltages) == 1.0
        assert _map_index_to_voltage(1, voltages) == 2.0
        assert _map_index_to_voltage(2, voltages) == 3.0

    def test_out_of_bounds_index(self):
        voltages = np.array([1.0, 2.0, 3.0])
        assert _map_index_to_voltage(3, voltages) is None
        assert _map_index_to_voltage(10, voltages) is None


class TestPinchoffFitResult:
    def test_fit_curve_method(self):
        voltages = np.linspace(-2, 2, 100)
        currents = pinchoff_curve(voltages, 0.5, 2.0, -1.0)
        result = fit_pinchoff_parameters(voltages, currents)
        fitted_currents = result.fit_curve(voltages)
        assert len(fitted_currents) == len(voltages)
        assert isinstance(fitted_currents, np.ndarray)
        rmse = np.sqrt(np.mean((currents - fitted_currents) ** 2))
        assert rmse < 0.01

    def test_fit_curve_normalization_bounds(self):
        voltages = np.linspace(-2, 2, 100)
        currents = pinchoff_curve(voltages, 0.5, 2.0, -1.0)
        result = fit_pinchoff_parameters(voltages, currents)
        assert result.v_min == voltages.min()
        assert result.v_max == voltages.max()
        assert result.i_min < result.i_max


class TestFitPinchoffParameters:
    def test_basic_fit(self):
        voltages = np.linspace(-10, 10, 100)
        currents = pinchoff_curve(voltages, 1.0, 1.0, 1.0)
        result = fit_pinchoff_parameters(voltages, currents)
        assert isinstance(result, PinchoffFitResult)
        assert result.v_cut_off is not None
        assert result.v_transition is not None
        assert result.v_saturation is not None
        assert result.popt is not None
        assert result.pcov is not None

    def test_fit_with_noise(self):
        voltages = np.linspace(-10, 10, 100)
        currents = pinchoff_curve(voltages, 1.0, 1.0, 1.0)
        noisy_currents = currents + np.random.normal(0, 0.01, len(currents))
        result = fit_pinchoff_parameters(voltages, noisy_currents)
        assert result.v_cut_off is not None

    def test_fit_parameter_shapes(self):
        voltages = np.linspace(-10, 10, 100)
        currents = pinchoff_curve(voltages, 1.0, 1.0, 1.0)
        result = fit_pinchoff_parameters(voltages, currents)
        assert len(result.popt) == 3
        assert result.pcov.shape == (3, 3)

    def test_custom_sigma(self):
        voltages = np.linspace(-10, 10, 100)
        currents = pinchoff_curve(voltages, 1.0, 1.0, 1.0)
        result = fit_pinchoff_parameters(voltages, currents, sigma=0.05)
        assert result.v_cut_off is not None

    def test_edge_case_out_of_bounds_index(self):
        voltages = np.linspace(-10, 10, 10)
        currents = pinchoff_curve(voltages, 1.0, 1.0, 1.0)
        result = fit_pinchoff_parameters(voltages, currents)
        assert hasattr(result, "v_cut_off")
        assert hasattr(result, "v_transition")
        assert hasattr(result, "v_saturation")

    def test_very_flat_curve(self):
        """Test fitting with very flat curve (minimal slope)."""
        voltages = np.linspace(-10, 10, 100)
        currents = pinchoff_curve(voltages, 0.01, 0.05, 0.0)
        result = fit_pinchoff_parameters(voltages, currents)

        fitted_currents = result.fit_curve(voltages)
        rmse = np.sqrt(np.mean((currents - fitted_currents) ** 2))
        assert rmse < 0.1

    def test_extreme_amplitude_ratio_large(self):
        """Test with very large current amplitude."""
        voltages = np.linspace(-2, 2, 100)
        currents = pinchoff_curve(voltages, 1000.0, 2.0, -1.0)
        result = fit_pinchoff_parameters(voltages, currents)

        fitted_currents = result.fit_curve(voltages)
        relative_error = np.abs((currents - fitted_currents) / currents.max())
        assert np.mean(relative_error) < 0.05

    def test_extreme_amplitude_ratio_small(self):
        """Test with very small current amplitude."""
        voltages = np.linspace(-2, 2, 100)
        currents = pinchoff_curve(voltages, 1e-9, 2.0, -1.0)
        result = fit_pinchoff_parameters(voltages, currents)

        assert result.v_cut_off is not None
        assert result.i_min < result.i_max
        fitted_currents = result.fit_curve(voltages)
        assert fitted_currents.min() >= 0

    def test_very_small_voltage_range(self):
        """Test with very narrow voltage range."""
        voltages = np.linspace(0.0, 0.01, 100)
        currents = pinchoff_curve(voltages * 100, 0.5, 2.0, -1.0)
        result = fit_pinchoff_parameters(voltages, currents)

        assert result.v_cut_off is not None
        assert result.v_min < result.v_max

    def test_inverted_curve_comprehensive(self):
        """Test inverted curve (current decreases with voltage)."""
        voltages = np.linspace(-2, 2, 100)
        currents = pinchoff_curve(voltages, 0.5, -2.0, 1.0)
        result = fit_pinchoff_parameters(voltages, currents)

        assert result.v_cut_off is not None
        assert result.v_transition is not None
        assert result.v_saturation is not None
        assert result.v_cut_off > result.v_saturation

    def test_very_steep_curve(self):
        """Test with very steep transition."""
        voltages = np.linspace(-2, 2, 200)
        currents = pinchoff_curve(voltages, 1.0, 20.0, 0.0)
        result = fit_pinchoff_parameters(voltages, currents, sigma=1.0)

        assert result.v_cut_off is not None
        assert abs(result.v_saturation - result.v_cut_off) < 1.0

    def test_poor_fit_detection(self):
        """Test that a very poor fit can be detected via high residuals."""
        voltages = np.linspace(-10, 10, 100)
        currents = np.sin(voltages) + 2.0
        result = fit_pinchoff_parameters(voltages, currents)

        fitted_currents = result.fit_curve(voltages)
        rmse = np.sqrt(np.mean((currents - fitted_currents) ** 2))
        relative_rmse = rmse / (currents.max() - currents.min())

        assert relative_rmse > 0.1, "Expected poor fit to have high RMSE"

        param_uncertainties = np.sqrt(np.diag(result.pcov))
        assert np.any(param_uncertainties > 0.5), (
            "Expected high parameter uncertainties"
        )

    def test_constant_current(self):
        """Test with completely flat current (no pinchoff behavior)."""
        voltages = np.linspace(-10, 10, 100)
        currents = np.ones_like(voltages) * 5.0
        result = fit_pinchoff_parameters(voltages, currents)

        assert result.v_cut_off is not None
        assert result.popt is not None

    def test_non_monotonic_data(self):
        """Test with oscillating/non-monotonic data."""
        voltages = np.linspace(-5, 5, 100)
        base_curve = pinchoff_curve(voltages, 1.0, 1.5, 0.0)
        currents = base_curve + 0.1 * np.sin(voltages * 3)
        result = fit_pinchoff_parameters(voltages, currents, sigma=3.0)

        assert result.v_cut_off is not None
        fitted_currents = result.fit_curve(voltages)

        fit_variation = np.std(np.diff(fitted_currents))
        data_variation = np.std(np.diff(currents))
        assert fit_variation < data_variation

    def test_extreme_voltage_range(self):
        """Test with very large voltage range."""
        voltages = np.linspace(-1000, 1000, 200)
        currents = pinchoff_curve(voltages / 1000, 0.5, 2.0, -1.0)
        result = fit_pinchoff_parameters(voltages, currents)
        assert result.v_cut_off is not None
        assert result.v_min == voltages.min()
        assert result.v_max == voltages.max()

    def test_asymmetric_voltage_range(self):
        """Test with voltage range not centered at zero."""
        voltages = np.linspace(10, 30, 100)
        currents = pinchoff_curve((voltages - 20) / 10, 0.5, 2.0, -1.0)
        result = fit_pinchoff_parameters(voltages, currents)

        assert result.v_cut_off is not None
        assert voltages.min() <= result.v_cut_off <= voltages.max()

    def test_fit_quality_good_fit(self):
        """Test that a good fit has low residuals and reasonable covariance."""
        voltages = np.linspace(-2, 2, 100)
        true_params = [0.5, 2.0, -1.0]
        currents = pinchoff_curve(voltages, *true_params)
        noisy_currents = currents + np.random.normal(0, 0.001, len(currents))
        result = fit_pinchoff_parameters(voltages, noisy_currents)

        fitted_currents = result.fit_curve(voltages)
        rmse = np.sqrt(np.mean((noisy_currents - fitted_currents) ** 2))
        relative_rmse = rmse / (noisy_currents.max() - noisy_currents.min())

        assert relative_rmse < 0.01, (
            f"Expected good fit but got relative RMSE: {relative_rmse}"
        )

        param_uncertainties = np.sqrt(np.diag(result.pcov))
        assert np.all(param_uncertainties < 0.1), "Expected low parameter uncertainties"


class TestNormalize:
    def test_basic_normalization(self):
        a = np.array([0, 5, 10])
        result = normalize(a)
        assert result[0] == 0.0
        assert result[-1] == 1.0
        assert np.all((result >= 0) & (result <= 1))

    def test_constant_array(self):
        a = np.array([5, 5, 5])
        result = normalize(a)
        assert np.all(result == 0.0)

    def test_negative_values(self):
        a = np.array([-10, 0, 10])
        result = normalize(a)
        assert result[0] == 0.0
        assert result[-1] == 1.0

    def test_single_element(self):
        a = np.array([42])
        result = normalize(a)
        assert result[0] == 0.0

    def test_preserves_order(self):
        a = np.array([1, 3, 2, 5, 4])
        result = normalize(a)
        assert result[0] < result[1]
        assert result[1] > result[2]
        assert result[2] < result[3]

    def test_float_dtype(self):
        a = np.array([1, 2, 3])
        result = normalize(a)
        assert result.dtype == float
