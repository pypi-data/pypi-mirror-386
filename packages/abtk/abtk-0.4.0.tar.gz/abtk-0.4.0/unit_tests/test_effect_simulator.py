"""
Unit tests for effect simulators.

Tests for:
- AdditiveEffectSimulator
- MultiplicativeEffectSimulator
- BinaryEffectSimulator
- get_effect_simulator()
"""

import pytest
import numpy as np
from utils.effect_simulator import (
    AdditiveEffectSimulator,
    MultiplicativeEffectSimulator,
    BinaryEffectSimulator,
    get_effect_simulator
)


class TestAdditiveEffectSimulator:
    """Tests for additive effect simulator."""

    def test_basic_addition(self):
        """Basic additive effect should add constant to all values."""
        simulator = AdditiveEffectSimulator()
        data = np.array([100, 105, 98, 102])
        effect = 5.0

        result = simulator.apply_effect(data, effect)

        expected = np.array([105, 110, 103, 107])
        np.testing.assert_array_almost_equal(result, expected)

    def test_negative_effect(self):
        """Negative effect should decrease values."""
        simulator = AdditiveEffectSimulator()
        data = np.array([100, 105, 98, 102])
        effect = -10.0

        result = simulator.apply_effect(data, effect)

        expected = np.array([90, 95, 88, 92])
        np.testing.assert_array_almost_equal(result, expected)

    def test_zero_effect(self):
        """Zero effect should leave data unchanged."""
        simulator = AdditiveEffectSimulator()
        data = np.array([100, 105, 98, 102])
        effect = 0.0

        result = simulator.apply_effect(data, effect)

        np.testing.assert_array_almost_equal(result, data)

    def test_large_array(self):
        """Should work with large arrays."""
        simulator = AdditiveEffectSimulator()
        np.random.seed(42)
        data = np.random.normal(100, 20, 10000)
        effect = 10.0

        result = simulator.apply_effect(data, effect)

        # Mean should increase by exactly the effect
        assert abs(np.mean(result) - np.mean(data) - effect) < 0.01

    def test_preserves_shape(self):
        """Should preserve array shape."""
        simulator = AdditiveEffectSimulator()
        data = np.array([1, 2, 3, 4, 5])
        effect = 2.0

        result = simulator.apply_effect(data, effect)

        assert result.shape == data.shape

    def test_does_not_modify_input(self):
        """Should not modify input array."""
        simulator = AdditiveEffectSimulator()
        data = np.array([100, 105, 98, 102])
        original = data.copy()
        effect = 5.0

        simulator.apply_effect(data, effect)

        np.testing.assert_array_equal(data, original)


class TestMultiplicativeEffectSimulator:
    """Tests for multiplicative effect simulator."""

    def test_basic_multiplication(self):
        """Basic multiplicative effect should multiply by (1 + effect)."""
        simulator = MultiplicativeEffectSimulator()
        data = np.array([100, 200, 50])
        effect = 0.10  # 10% increase

        result = simulator.apply_effect(data, effect)

        expected = np.array([110, 220, 55])
        np.testing.assert_array_almost_equal(result, expected)

    def test_percentage_increase(self):
        """5% increase should multiply by 1.05."""
        simulator = MultiplicativeEffectSimulator()
        data = np.array([100, 105, 98, 102])
        effect = 0.05

        result = simulator.apply_effect(data, effect)

        expected = data * 1.05
        np.testing.assert_array_almost_equal(result, expected)

    def test_percentage_decrease(self):
        """Negative effect should decrease values proportionally."""
        simulator = MultiplicativeEffectSimulator()
        data = np.array([100, 200, 50])
        effect = -0.20  # 20% decrease

        result = simulator.apply_effect(data, effect)

        expected = np.array([80, 160, 40])
        np.testing.assert_array_almost_equal(result, expected)

    def test_zero_effect(self):
        """Zero effect should leave data unchanged."""
        simulator = MultiplicativeEffectSimulator()
        data = np.array([100, 105, 98, 102])
        effect = 0.0

        result = simulator.apply_effect(data, effect)

        np.testing.assert_array_almost_equal(result, data)

    def test_relative_change_preserved(self):
        """Mean should change by exactly the effect percentage."""
        simulator = MultiplicativeEffectSimulator()
        np.random.seed(42)
        data = np.random.normal(100, 20, 10000)
        effect = 0.05

        result = simulator.apply_effect(data, effect)

        relative_change = (np.mean(result) / np.mean(data)) - 1
        assert abs(relative_change - effect) < 0.001

    def test_proportional_to_baseline(self):
        """Effect should be proportional to baseline values."""
        simulator = MultiplicativeEffectSimulator()
        data = np.array([100, 200])  # Second is 2x first
        effect = 0.10

        result = simulator.apply_effect(data, effect)

        # Absolute change should be 2x larger for 2x larger value
        change1 = result[0] - data[0]
        change2 = result[1] - data[1]
        assert abs(change2 / change1 - 2.0) < 0.01

    def test_extreme_negative_effect(self):
        """Large negative effect should work (but be careful with -1.0)."""
        simulator = MultiplicativeEffectSimulator()
        data = np.array([100, 200, 50])
        effect = -0.90  # 90% decrease

        result = simulator.apply_effect(data, effect)

        expected = np.array([10, 20, 5])
        np.testing.assert_array_almost_equal(result, expected)

    def test_does_not_modify_input(self):
        """Should not modify input array."""
        simulator = MultiplicativeEffectSimulator()
        data = np.array([100, 105, 98, 102])
        original = data.copy()
        effect = 0.05

        simulator.apply_effect(data, effect)

        np.testing.assert_array_equal(data, original)


class TestBinaryEffectSimulator:
    """Tests for binary effect simulator."""

    def test_basic_increase(self):
        """Should flip 0→1 to increase conversion rate."""
        simulator = BinaryEffectSimulator()
        np.random.seed(42)
        data = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1])  # 40% baseline
        effect = 0.20  # Increase by 20pp → 60%

        result = simulator.apply_effect(data, effect)

        assert np.mean(result) == 0.6

    def test_basic_decrease(self):
        """Should flip 1→0 to decrease conversion rate."""
        simulator = BinaryEffectSimulator()
        np.random.seed(42)
        data = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])  # 60% baseline
        effect = -0.20  # Decrease by 20pp → 40%

        result = simulator.apply_effect(data, effect)

        assert np.mean(result) == 0.4

    def test_zero_effect(self):
        """Zero effect should leave data unchanged."""
        simulator = BinaryEffectSimulator()
        data = np.array([0, 0, 0, 1, 1])
        effect = 0.0

        result = simulator.apply_effect(data, effect)

        np.testing.assert_array_equal(result, data)

    def test_tiny_effect_no_flips(self):
        """Very small effect that results in 0 flips should return copy."""
        simulator = BinaryEffectSimulator()
        data = np.array([0, 0, 0, 1, 1])  # n=5
        effect = 0.05  # 5% of 5 = 0.25 flips → rounds to 0

        result = simulator.apply_effect(data, effect)

        np.testing.assert_array_equal(result, data)

    def test_large_sample_effect(self):
        """Should work with large samples."""
        simulator = BinaryEffectSimulator()
        np.random.seed(42)
        data = np.random.binomial(1, 0.05, 1000)  # ~5% baseline
        baseline_rate = np.mean(data)
        effect = 0.02  # Increase by 2pp

        result = simulator.apply_effect(data, effect)

        final_rate = np.mean(result)
        assert abs(final_rate - baseline_rate - effect) < 0.005

    def test_validates_binary_data(self):
        """Should raise error for non-binary data."""
        simulator = BinaryEffectSimulator()
        data = np.array([0, 1, 2, 3])  # Contains non-binary values

        with pytest.raises(ValueError, match="binary data"):
            simulator.apply_effect(data, effect=0.1)

    def test_validates_impossible_increase(self):
        """Should raise error if not enough zeros to flip."""
        simulator = BinaryEffectSimulator()
        data = np.array([1, 1, 1, 1, 1])  # All ones
        effect = 0.20  # Can't increase from 100%

        with pytest.raises(ValueError, match="Cannot increase"):
            simulator.apply_effect(data, effect)

    def test_validates_impossible_decrease(self):
        """Should raise error if not enough ones to flip."""
        simulator = BinaryEffectSimulator()
        data = np.array([0, 0, 0, 0, 0])  # All zeros
        effect = -0.20  # Can't decrease from 0%

        with pytest.raises(ValueError, match="Cannot decrease"):
            simulator.apply_effect(data, effect)

    def test_edge_case_barely_possible_increase(self):
        """Should work when effect is just barely achievable."""
        simulator = BinaryEffectSimulator()
        np.random.seed(42)
        data = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])  # 10% baseline
        effect = 0.90  # Increase to 100% (flip all 9 zeros)

        result = simulator.apply_effect(data, effect)

        assert np.mean(result) == 1.0

    def test_edge_case_barely_possible_decrease(self):
        """Should work when effect is just barely achievable."""
        simulator = BinaryEffectSimulator()
        np.random.seed(42)
        data = np.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 1])  # 90% baseline
        effect = -0.90  # Decrease to 0% (flip all 9 ones)

        result = simulator.apply_effect(data, effect)

        assert np.mean(result) == 0.0

    def test_accepts_only_zeros_and_ones(self):
        """Should only accept arrays with 0 and 1 values."""
        simulator = BinaryEffectSimulator()

        # Valid: all zeros
        data_zeros = np.array([0, 0, 0, 0])
        result = simulator.apply_effect(data_zeros, effect=0.0)
        np.testing.assert_array_equal(result, data_zeros)

        # Valid: all ones
        data_ones = np.array([1, 1, 1, 1])
        result = simulator.apply_effect(data_ones, effect=0.0)
        np.testing.assert_array_equal(result, data_ones)

        # Invalid: contains 2
        data_invalid = np.array([0, 1, 2])
        with pytest.raises(ValueError, match="binary data"):
            simulator.apply_effect(data_invalid, effect=0.1)

    def test_does_not_modify_input(self):
        """Should not modify input array."""
        simulator = BinaryEffectSimulator()
        np.random.seed(42)
        data = np.array([0, 0, 0, 1, 1])
        original = data.copy()
        effect = 0.10

        simulator.apply_effect(data, effect)

        np.testing.assert_array_equal(data, original)

    def test_flips_correct_number(self):
        """Should flip exactly the right number of values."""
        simulator = BinaryEffectSimulator()
        np.random.seed(42)
        data = np.zeros(100)  # All zeros
        effect = 0.25  # Should flip 25 zeros → 25% conversion

        result = simulator.apply_effect(data, effect)

        assert np.sum(result) == 25


class TestGetEffectSimulator:
    """Tests for effect simulator factory function."""

    def test_get_additive(self):
        """Should return AdditiveEffectSimulator."""
        simulator = get_effect_simulator("additive")
        assert isinstance(simulator, AdditiveEffectSimulator)

    def test_get_multiplicative(self):
        """Should return MultiplicativeEffectSimulator."""
        simulator = get_effect_simulator("multiplicative")
        assert isinstance(simulator, MultiplicativeEffectSimulator)

    def test_get_binary(self):
        """Should return BinaryEffectSimulator."""
        simulator = get_effect_simulator("binary")
        assert isinstance(simulator, BinaryEffectSimulator)

    def test_invalid_type(self):
        """Should raise error for unknown effect type."""
        with pytest.raises(ValueError, match="Unknown effect_type"):
            get_effect_simulator("unknown")

    def test_case_sensitive(self):
        """Effect type should be case-sensitive."""
        with pytest.raises(ValueError):
            get_effect_simulator("Additive")

        with pytest.raises(ValueError):
            get_effect_simulator("MULTIPLICATIVE")

    def test_returns_new_instance(self):
        """Should return new instances (not singletons)."""
        sim1 = get_effect_simulator("additive")
        sim2 = get_effect_simulator("additive")

        # Same type but different instances
        assert isinstance(sim1, AdditiveEffectSimulator)
        assert isinstance(sim2, AdditiveEffectSimulator)
        assert sim1 is not sim2


class TestEffectSimulatorsIntegration:
    """Integration tests comparing effect simulators."""

    def test_additive_vs_multiplicative_small_effect(self):
        """For small effects on large values, additive and multiplicative differ."""
        np.random.seed(42)
        data = np.random.normal(1000, 100, 1000)

        additive_sim = AdditiveEffectSimulator()
        mult_sim = MultiplicativeEffectSimulator()

        # 5 unit increase (additive)
        result_add = additive_sim.apply_effect(data, effect=5.0)

        # 0.5% increase (multiplicative) ≈ 5 units on mean=1000
        result_mult = mult_sim.apply_effect(data, effect=0.005)

        # Both should increase mean by ~5
        assert abs(np.mean(result_add) - np.mean(data) - 5.0) < 0.1
        assert abs(np.mean(result_mult) - np.mean(data) - 5.0) < 1.0

    def test_all_simulators_preserve_array_size(self):
        """All simulators should preserve array size."""
        np.random.seed(42)
        data_continuous = np.random.normal(100, 20, 500)
        data_binary = np.random.binomial(1, 0.3, 500)

        add_sim = AdditiveEffectSimulator()
        mult_sim = MultiplicativeEffectSimulator()
        bin_sim = BinaryEffectSimulator()

        result_add = add_sim.apply_effect(data_continuous, effect=5.0)
        result_mult = mult_sim.apply_effect(data_continuous, effect=0.05)
        result_bin = bin_sim.apply_effect(data_binary, effect=0.05)

        assert len(result_add) == 500
        assert len(result_mult) == 500
        assert len(result_bin) == 500

    def test_all_simulators_accept_clusters_parameter(self):
        """All simulators should accept clusters parameter (for future use)."""
        data = np.array([100, 105, 98, 102])
        clusters = np.array([1, 1, 2, 2])

        add_sim = AdditiveEffectSimulator()
        mult_sim = MultiplicativeEffectSimulator()

        # Should not raise error (even if clusters are currently unused)
        result_add = add_sim.apply_effect(data, effect=5.0, clusters=clusters)
        result_mult = mult_sim.apply_effect(data, effect=0.05, clusters=clusters)

        assert len(result_add) == 4
        assert len(result_mult) == 4
