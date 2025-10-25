"""
Unit tests for PowerAnalyzer.

Tests for:
- PowerAnalyzer.power_analysis()
- PowerAnalyzer.power_line()
- PowerAnalyzer.minimum_detectable_effect()
- PowerAnalyzer._split_simple()
- PowerAnalyzer._split_by_clusters()
- PowerAnalyzer._split_by_pairs()
"""

import pytest
import numpy as np
import warnings
from core.data_types import SampleData
from tests.parametric import TTest, ClusteredTTest, PairedTTest
from tests.nonparametric import BootstrapTest, ClusteredBootstrapTest
from utils.power_analysis import PowerAnalyzer


class TestPowerAnalyzerInit:
    """Tests for PowerAnalyzer initialization."""

    def test_basic_initialization(self):
        """Should initialize with test and default parameters."""
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        assert analyzer.test == test
        assert analyzer.n_simulations == 1000
        assert analyzer.seed is None

    def test_custom_n_simulations(self):
        """Should accept custom n_simulations."""
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=500)

        assert analyzer.n_simulations == 500

    def test_seed_reproducibility(self):
        """Setting seed should make results reproducible."""
        test = TTest(alpha=0.05)
        sample = SampleData(data=np.random.normal(100, 20, 500))

        analyzer1 = PowerAnalyzer(test=test, n_simulations=100, seed=42)
        power1 = analyzer1.power_analysis(sample, effect=5.0, effect_type="additive")

        analyzer2 = PowerAnalyzer(test=test, n_simulations=100, seed=42)
        power2 = analyzer2.power_analysis(sample, effect=5.0, effect_type="additive")

        assert power1 == power2

    def test_warns_low_simulations(self):
        """Should warn if n_simulations is very low."""
        test = TTest(alpha=0.05)

        with pytest.warns(UserWarning, match="n_simulations.*very low"):
            PowerAnalyzer(test=test, n_simulations=50)


class TestPowerAnalysisBasic:
    """Basic tests for power_analysis() method."""

    def test_zero_effect_low_power(self):
        """Zero effect should give power ≈ alpha (Type I error rate)."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=500, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 1000))
        power = analyzer.power_analysis(sample, effect=0.0, effect_type="additive")

        # Power should be close to alpha (5%)
        assert 0.02 <= power <= 0.08

    def test_large_effect_high_power(self):
        """Large effect should give high power."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 1000))
        power = analyzer.power_analysis(sample, effect=20.0, effect_type="additive")

        # Very large effect → high power
        assert power > 0.9

    def test_power_increases_with_effect(self):
        """Power should increase monotonically with effect size."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))

        power_small = analyzer.power_analysis(sample, effect=3.0, effect_type="additive")
        power_medium = analyzer.power_analysis(sample, effect=7.0, effect_type="additive")
        power_large = analyzer.power_analysis(sample, effect=15.0, effect_type="additive")

        assert power_small < power_medium < power_large

    def test_power_increases_with_sample_size(self):
        """Power should increase with sample size."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

        effect = 5.0

        sample_small = SampleData(data=np.random.normal(100, 20, 200))
        sample_large = SampleData(data=np.random.normal(100, 20, 1000))

        power_small = analyzer.power_analysis(sample_small, effect=effect)
        power_large = analyzer.power_analysis(sample_large, effect=effect)

        assert power_large > power_small

    def test_override_n_simulations(self):
        """Should allow overriding n_simulations per call."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=1000, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))

        # Use fewer simulations for this call
        power = analyzer.power_analysis(
            sample,
            effect=5.0,
            effect_type="additive",
            n_simulations=50
        )

        assert 0.0 <= power <= 1.0


class TestPowerAnalysisEffectTypes:
    """Tests for different effect types."""

    def test_additive_effect(self):
        """Should work with additive effect."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))
        power = analyzer.power_analysis(sample, effect=8.0, effect_type="additive")

        assert 0.0 <= power <= 1.0

    def test_multiplicative_effect(self):
        """Should work with multiplicative effect."""
        np.random.seed(42)
        test = TTest(alpha=0.05, test_type="relative")
        analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))
        power = analyzer.power_analysis(sample, effect=0.08, effect_type="multiplicative")

        assert 0.0 <= power <= 1.0

    def test_binary_effect(self):
        """Should work with binary effect."""
        np.random.seed(42)
        from tests.parametric import ZTest
        test = ZTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

        # Binary data: conversion rate
        sample = SampleData(data=np.random.binomial(1, 0.10, 1000))
        power = analyzer.power_analysis(sample, effect=0.02, effect_type="binary")

        assert 0.0 <= power <= 1.0


class TestPowerLine:
    """Tests for power_line() method."""

    def test_basic_power_curve(self):
        """Should compute power for multiple effect sizes."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=100, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))
        effects = [2.0, 5.0, 10.0]

        power_curve = analyzer.power_line(sample, effects=effects, effect_type="additive")

        assert len(power_curve) == 3
        assert all(0.0 <= p <= 1.0 for p in power_curve.values())

    def test_power_curve_monotonic(self):
        """Power should increase with effect size."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=150, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))
        effects = [2.0, 5.0, 8.0, 12.0]

        power_curve = analyzer.power_line(sample, effects=effects)

        powers = [power_curve[e] for e in effects]
        # Power should generally increase (allow small fluctuations due to MC noise)
        assert powers[-1] > powers[0]

    def test_power_line_returns_dict(self):
        """Should return dictionary mapping effects to power."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=100, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))
        effects = [5.0, 10.0]

        power_curve = analyzer.power_line(sample, effects=effects)

        assert isinstance(power_curve, dict)
        assert 5.0 in power_curve
        assert 10.0 in power_curve


class TestMinimumDetectableEffect:
    """Tests for minimum_detectable_effect() method."""

    def test_basic_mde_calculation(self):
        """Should find MDE for target power."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=100, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))

        mde = analyzer.minimum_detectable_effect(
            sample,
            target_power=0.8,
            effect_type="additive"
        )

        # MDE should be positive
        assert mde > 0

    def test_mde_decreases_with_sample_size(self):
        """MDE should decrease with larger samples."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=80, seed=42)

        sample_small = SampleData(data=np.random.normal(100, 20, 200))
        sample_large = SampleData(data=np.random.normal(100, 20, 1000))

        mde_small = analyzer.minimum_detectable_effect(sample_small, target_power=0.8)
        mde_large = analyzer.minimum_detectable_effect(sample_large, target_power=0.8)

        assert mde_large < mde_small

    def test_mde_increases_with_target_power(self):
        """Higher target power should require larger MDE."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=80, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))

        mde_70 = analyzer.minimum_detectable_effect(sample, target_power=0.7)
        mde_90 = analyzer.minimum_detectable_effect(sample, target_power=0.9)

        assert mde_90 > mde_70

    def test_mde_multiplicative(self):
        """Should work with multiplicative effect type."""
        np.random.seed(42)
        test = TTest(alpha=0.05, test_type="relative")
        analyzer = PowerAnalyzer(test=test, n_simulations=80, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))

        mde = analyzer.minimum_detectable_effect(
            sample,
            target_power=0.8,
            effect_type="multiplicative"
        )

        # Multiplicative MDE should be between 0 and 1
        assert 0 < mde < 1

    def test_mde_binary(self):
        """Should work with binary effect type."""
        np.random.seed(42)
        from tests.parametric import ZTest
        test = ZTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=80, seed=42)

        sample = SampleData(data=np.random.binomial(1, 0.10, 500))

        mde = analyzer.minimum_detectable_effect(
            sample,
            target_power=0.8,
            effect_type="binary"
        )

        # Binary MDE should be reasonable
        baseline_rate = np.mean(sample.data)
        assert 0 < mde < (1 - baseline_rate)

    def test_custom_search_range(self):
        """Should accept custom search range."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))

        mde = analyzer.minimum_detectable_effect(
            sample,
            target_power=0.8,
            effect_type="additive",
            search_range=(1.0, 20.0)
        )

        assert 1.0 <= mde <= 20.0

    def test_warns_on_max_iterations(self):
        """Should warn if binary search doesn't converge."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mde = analyzer.minimum_detectable_effect(
                sample,
                target_power=0.8,
                max_iterations=2  # Very low → won't converge
            )
            # Should get warning about convergence
            assert len(w) >= 1


class TestSplitSimple:
    """Tests for _split_simple() method."""

    def test_splits_50_50(self):
        """Should split data approximately 50/50."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(data=np.arange(1000))
        control, treatment = analyzer._split_simple(sample)

        assert control.sample_size == 500
        assert treatment.sample_size == 500

    def test_splits_preserve_all_data(self):
        """Split samples should contain all original data."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(data=np.arange(100))
        control, treatment = analyzer._split_simple(sample)

        combined = np.concatenate([control.data, treatment.data])
        combined_sorted = np.sort(combined)
        original_sorted = np.sort(sample.data)

        np.testing.assert_array_equal(combined_sorted, original_sorted)

    def test_preserves_covariates(self):
        """Should preserve covariates in split."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.arange(100),
            covariates=np.arange(100) * 2
        )
        control, treatment = analyzer._split_simple(sample)

        assert control.covariates is not None
        assert treatment.covariates is not None
        assert len(control.covariates) == control.sample_size
        assert len(treatment.covariates) == treatment.sample_size

    def test_preserves_strata(self):
        """Should preserve strata in split."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.arange(100),
            strata=np.repeat([0, 1, 2, 3], 25)
        )
        control, treatment = analyzer._split_simple(sample)

        assert control.strata is not None
        assert treatment.strata is not None

    def test_randomizes_split(self):
        """Different seeds should give different splits."""
        test = TTest(alpha=0.05)
        sample = SampleData(data=np.arange(100))

        analyzer1 = PowerAnalyzer(test=test, seed=42)
        control1, _ = analyzer1._split_simple(sample)

        analyzer2 = PowerAnalyzer(test=test, seed=99)
        control2, _ = analyzer2._split_simple(sample)

        # Different random splits should have different data
        assert not np.array_equal(control1.data, control2.data)


class TestSplitByClusters:
    """Tests for _split_by_clusters() method."""

    def test_splits_clusters_not_individuals(self):
        """Should split by clusters, preserving cluster membership."""
        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        # 10 clusters, 10 observations each
        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            clusters=np.repeat(range(10), 10)
        )

        control, treatment = analyzer._split_by_clusters(sample)

        # Each cluster should be fully in one group
        control_clusters = np.unique(control.clusters)
        treatment_clusters = np.unique(treatment.clusters)

        # No overlap between control and treatment clusters
        assert len(np.intersect1d(control_clusters, treatment_clusters)) == 0

    def test_splits_clusters_50_50(self):
        """Should split clusters approximately 50/50."""
        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            clusters=np.repeat(range(10), 10)
        )

        control, treatment = analyzer._split_by_clusters(sample)

        n_control_clusters = len(np.unique(control.clusters))
        n_treatment_clusters = len(np.unique(treatment.clusters))

        assert n_control_clusters == 5
        assert n_treatment_clusters == 5

    def test_preserves_all_clusters(self):
        """All original clusters should be in split."""
        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            clusters=np.repeat(range(10), 10)
        )

        control, treatment = analyzer._split_by_clusters(sample)

        original_clusters = set(sample.clusters)
        split_clusters = set(control.clusters) | set(treatment.clusters)

        assert original_clusters == split_clusters

    def test_warns_few_clusters(self):
        """Should warn when very few clusters."""
        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.random.normal(100, 20, 30),
            clusters=np.repeat(range(3), 10)  # Only 3 clusters
        )

        with pytest.warns(UserWarning, match="clusters.*reliable"):
            analyzer._split_by_clusters(sample)

    def test_preserves_covariates_with_clusters(self):
        """Should preserve covariates in cluster split."""
        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            clusters=np.repeat(range(10), 10),
            covariates=np.random.normal(50, 10, 100)
        )

        control, treatment = analyzer._split_by_clusters(sample)

        assert control.covariates is not None
        assert treatment.covariates is not None
        assert len(control.covariates) == control.sample_size


class TestSplitByPairs:
    """Tests for _split_by_pairs() method."""

    def test_splits_pairs_randomly(self):
        """Should randomly assign paired observations to groups."""
        np.random.seed(42)
        test = PairedTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        # 50 pairs (100 observations)
        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            paired_ids=np.repeat(range(50), 2)
        )

        control, treatment = analyzer._split_by_pairs(sample)

        # Should have 50 observations each (one from each pair)
        assert control.sample_size == 50
        assert treatment.sample_size == 50

    def test_preserves_pair_ids(self):
        """Should preserve pair IDs in split."""
        np.random.seed(42)
        test = PairedTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            paired_ids=np.repeat(range(50), 2)
        )

        control, treatment = analyzer._split_by_pairs(sample)

        assert control.paired_ids is not None
        assert treatment.paired_ids is not None

    def test_all_pairs_represented(self):
        """Each pair should contribute to both groups."""
        np.random.seed(42)
        test = PairedTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            paired_ids=np.repeat(range(50), 2)
        )

        control, treatment = analyzer._split_by_pairs(sample)

        # All pairs should be represented in both groups
        control_pairs = set(control.paired_ids)
        treatment_pairs = set(treatment.paired_ids)
        original_pairs = set(sample.paired_ids)

        assert control_pairs == original_pairs
        assert treatment_pairs == original_pairs

    def test_raises_on_invalid_pairs(self):
        """Should raise error if pairs don't have exactly 2 observations."""
        np.random.seed(42)
        test = PairedTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        # Invalid: pair 0 has 3 observations
        sample = SampleData(
            data=np.random.normal(100, 20, 9),
            paired_ids=np.array([0, 0, 0, 1, 1, 2, 2, 3, 3])
        )

        with pytest.raises(ValueError, match="expected 2"):
            analyzer._split_by_pairs(sample)


class TestPowerAnalyzerWithDifferentTests:
    """Integration tests with different test types."""

    def test_with_ttest(self):
        """Should work with TTest."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=100, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 500))
        power = analyzer.power_analysis(sample, effect=8.0)

        assert 0.0 <= power <= 1.0

    def test_with_bootstrap(self):
        """Should work with BootstrapTest."""
        np.random.seed(42)
        test = BootstrapTest(alpha=0.05, n_bootstrap=100)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 300))
        power = analyzer.power_analysis(sample, effect=10.0)

        assert 0.0 <= power <= 1.0

    def test_with_clustered_ttest(self):
        """Should work with ClusteredTTest."""
        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05, min_clusters=3)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(
            data=np.random.normal(100, 20, 200),
            clusters=np.repeat(range(10), 20)
        )
        power = analyzer.power_analysis(sample, effect=10.0)

        assert 0.0 <= power <= 1.0

    def test_with_clustered_bootstrap(self):
        """Should work with ClusteredBootstrapTest."""
        np.random.seed(42)
        test = ClusteredBootstrapTest(alpha=0.05, n_bootstrap=100, min_clusters=3)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(
            data=np.random.normal(100, 20, 200),
            clusters=np.repeat(range(10), 20)
        )
        power = analyzer.power_analysis(sample, effect=10.0)

        assert 0.0 <= power <= 1.0

    def test_mde_for_bootstrap(self):
        """MDE calculation is especially useful for Bootstrap (no analytical formula)."""
        np.random.seed(42)
        test = BootstrapTest(alpha=0.05, n_bootstrap=100)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 400))

        mde = analyzer.minimum_detectable_effect(
            sample,
            target_power=0.8,
            effect_type="additive",
            max_iterations=10
        )

        assert mde > 0


class TestSplitterSelection:
    """Tests for automatic splitter selection based on sample type."""

    def test_selects_cluster_splitter(self):
        """Should use cluster splitter when sample has clusters."""
        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            clusters=np.repeat(range(10), 10)
        )

        control, treatment = analyzer._split_sample(sample)

        # Should preserve cluster membership
        control_clusters = set(control.clusters)
        treatment_clusters = set(treatment.clusters)
        assert len(control_clusters & treatment_clusters) == 0

    def test_selects_paired_splitter(self):
        """Should use paired splitter when sample has paired_ids."""
        np.random.seed(42)
        test = PairedTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(
            data=np.random.normal(100, 20, 100),
            paired_ids=np.repeat(range(50), 2)
        )

        control, treatment = analyzer._split_sample(sample)

        # Should have 50 observations each (one from each pair)
        assert control.sample_size == 50
        assert treatment.sample_size == 50

    def test_selects_simple_splitter(self):
        """Should use simple splitter for regular samples."""
        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test, n_simulations=50, seed=42)

        sample = SampleData(data=np.random.normal(100, 20, 100))

        control, treatment = analyzer._split_sample(sample)

        # Should split 50/50
        assert control.sample_size == 50
        assert treatment.sample_size == 50


class TestApplyEffect:
    """Tests for _apply_effect() method."""

    def test_applies_additive_effect(self):
        """Should apply additive effect correctly."""
        from utils.effect_simulator import AdditiveEffectSimulator

        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(data=np.array([100, 105, 98, 102]))
        simulator = AdditiveEffectSimulator()

        perturbed = analyzer._apply_effect(sample, effect=5.0, simulator=simulator)

        expected = np.array([105, 110, 103, 107])
        np.testing.assert_array_almost_equal(perturbed.data, expected)

    def test_preserves_sample_metadata(self):
        """Should preserve covariates, clusters, etc."""
        from utils.effect_simulator import AdditiveEffectSimulator

        np.random.seed(42)
        test = ClusteredTTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.array([100, 105, 98, 102]),
            clusters=np.array([1, 1, 2, 2]),
            covariates=np.array([50, 52, 48, 51]),
            name="Test"
        )
        simulator = AdditiveEffectSimulator()

        perturbed = analyzer._apply_effect(sample, effect=5.0, simulator=simulator)

        # Metadata should be preserved
        np.testing.assert_array_equal(perturbed.clusters, sample.clusters)
        np.testing.assert_array_equal(perturbed.covariates, sample.covariates)
        assert perturbed.name == sample.name

    def test_only_data_changed(self):
        """Only data should change, everything else preserved."""
        from utils.effect_simulator import MultiplicativeEffectSimulator

        np.random.seed(42)
        test = TTest(alpha=0.05)
        analyzer = PowerAnalyzer(test=test)

        sample = SampleData(
            data=np.array([100, 200]),
            covariates=np.array([50, 60])
        )
        simulator = MultiplicativeEffectSimulator()

        perturbed = analyzer._apply_effect(sample, effect=0.10, simulator=simulator)

        # Data changed
        assert not np.array_equal(perturbed.data, sample.data)

        # Covariates unchanged
        np.testing.assert_array_equal(perturbed.covariates, sample.covariates)
