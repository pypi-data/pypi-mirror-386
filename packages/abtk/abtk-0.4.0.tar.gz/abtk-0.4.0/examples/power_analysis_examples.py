"""
Power Analysis Examples
========================

This file demonstrates how to use PowerAnalyzer for experiment planning.

PowerAnalyzer estimates statistical power through Monte Carlo simulation,
which works with ALL abtk tests (including Bootstrap and cluster tests).

Key use cases:
1. Estimate power for planned effect size
2. Calculate minimum detectable effect (MDE)
3. Generate power curves
4. Plan cluster-randomized experiments

All examples use 100% NumPy operations (no pandas).
"""

import numpy as np
from core.data_types import SampleData
from tests.parametric import TTest, ClusteredTTest, ZTest
from tests.nonparametric import BootstrapTest, ClusteredBootstrapTest
from utils.power_analysis import PowerAnalyzer


# =============================================================================
# Example 1: Basic Power Analysis with T-Test
# =============================================================================

def example_basic_power_analysis():
    """
    Estimate power for a planned A/B test.

    Question: "We plan to run an experiment with 1000 users per group.
               Can we detect a 5% revenue increase with 80% power?"
    """
    print("=" * 70)
    print("Example 1: Basic Power Analysis")
    print("=" * 70)

    # Historical data (last month's revenue)
    np.random.seed(42)
    historical_revenue = np.random.lognormal(mean=4.6, sigma=0.8, size=5000)

    sample = SampleData(
        data=historical_revenue,
        name="Historical Revenue"
    )

    print(f"Historical data: {len(sample.data)} observations")
    print(f"Mean revenue: ${np.mean(sample.data):.2f}")
    print(f"Std dev: ${np.std(sample.data, ddof=1):.2f}")
    print()

    # Configure test and analyzer
    test = TTest(alpha=0.05, test_type="relative")
    analyzer = PowerAnalyzer(test=test, n_simulations=1000, seed=42)

    # Estimate power for 5% relative increase
    power = analyzer.power_analysis(
        sample=sample,
        effect=0.05,  # 5% increase
        effect_type="multiplicative"
    )

    print(f"Planned effect: 5% revenue increase")
    print(f"Estimated power: {power:.1%}")
    print()

    if power >= 0.8:
        print("✓ Good! We have sufficient power (≥80%).")
    else:
        print("✗ Warning! Power is below 80%. Consider:")
        print("  - Increasing sample size")
        print("  - Running experiment longer")
        print("  - Using variance reduction (CUPED)")
    print()


# =============================================================================
# Example 2: Minimum Detectable Effect (MDE)
# =============================================================================

def example_mde_calculation():
    """
    Calculate MDE for a planned experiment.

    Question: "With 500 users per group, what's the smallest effect
               we can reliably detect (80% power)?"
    """
    print("=" * 70)
    print("Example 2: Minimum Detectable Effect (MDE)")
    print("=" * 70)

    # Historical data
    np.random.seed(42)
    historical_data = np.random.normal(loc=100, scale=25, size=500)

    sample = SampleData(data=historical_data, name="Historical")

    print(f"Sample size: {len(sample.data)} observations")
    print(f"Mean: {np.mean(sample.data):.2f}")
    print(f"Std dev: {np.std(sample.data, ddof=1):.2f}")
    print()

    # Configure test and analyzer
    test = TTest(alpha=0.05, test_type="relative")
    analyzer = PowerAnalyzer(test=test, n_simulations=500, seed=42)

    # Calculate MDE for 80% power
    mde = analyzer.minimum_detectable_effect(
        sample=sample,
        target_power=0.8,
        effect_type="multiplicative"
    )

    print(f"Target power: 80%")
    print(f"Minimum detectable effect: {mde:.1%}")
    print(f"(Can detect {mde:.1%} relative change or larger)")
    print()

    # Absolute MDE
    mean_value = np.mean(sample.data)
    absolute_mde = mean_value * mde
    print(f"In absolute terms: {absolute_mde:.2f} units")
    print()


# =============================================================================
# Example 3: Power Curve
# =============================================================================

def example_power_curve():
    """
    Generate power curve to visualize power vs effect size.

    Useful for understanding the trade-off between effect size and power.
    """
    print("=" * 70)
    print("Example 3: Power Curve")
    print("=" * 70)

    # Historical data
    np.random.seed(42)
    historical_data = np.random.normal(loc=100, scale=20, size=800)
    sample = SampleData(data=historical_data)

    print(f"Sample size: {len(sample.data)}")
    print(f"Mean: {np.mean(sample.data):.2f}")
    print()

    # Configure test and analyzer
    test = TTest(alpha=0.05, test_type="relative")
    analyzer = PowerAnalyzer(test=test, n_simulations=300, seed=42)

    # Generate power curve for different effect sizes
    effects = [0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20]

    print("Effect Size  |  Power")
    print("-" * 25)

    power_curve = analyzer.power_line(
        sample=sample,
        effects=effects,
        effect_type="multiplicative"
    )

    for effect in effects:
        power = power_curve[effect]
        stars = "*" * int(power * 50)  # Visual representation
        print(f"  {effect:5.1%}      |  {power:5.1%}  {stars}")

    print()


# =============================================================================
# Example 4: Bootstrap Test (No Analytical MDE!)
# =============================================================================

def example_bootstrap_mde():
    """
    Calculate MDE for BootstrapTest.

    Bootstrap tests don't have analytical power formulas, so simulation-based
    MDE is THE ONLY OPTION.
    """
    print("=" * 70)
    print("Example 4: Bootstrap Test MDE (Simulation-Based)")
    print("=" * 70)

    # Skewed revenue data (bootstrap handles non-normal distributions)
    np.random.seed(42)
    historical_revenue = np.random.lognormal(mean=4.5, sigma=1.0, size=600)

    sample = SampleData(data=historical_revenue, name="Revenue")

    print(f"Sample size: {len(sample.data)}")
    print(f"Mean revenue: ${np.mean(sample.data):.2f}")
    print(f"Median revenue: ${np.median(sample.data):.2f}")
    print(f"Skewness: {np.mean((sample.data - np.mean(sample.data))**3) / np.std(sample.data)**3:.2f}")
    print("(Bootstrap is ideal for skewed data!)")
    print()

    # Configure Bootstrap test
    test = BootstrapTest(alpha=0.05, n_bootstrap=500, test_type="relative")
    analyzer = PowerAnalyzer(test=test, n_simulations=100, seed=42)

    print("Calculating MDE via simulation (this may take a moment)...")

    mde = analyzer.minimum_detectable_effect(
        sample=sample,
        target_power=0.8,
        effect_type="multiplicative",
        max_iterations=15
    )

    print(f"Minimum detectable effect: {mde:.1%}")
    print()
    print("Note: This MDE accounts for:")
    print("  - Non-normal distribution (skewness)")
    print("  - Bootstrap resampling variability")
    print("  - No parametric assumptions")
    print()


# =============================================================================
# Example 5: Cluster-Randomized Experiment
# =============================================================================

def example_cluster_power_analysis():
    """
    Power analysis for cluster-randomized experiments (geo tests, store tests).

    Question: "We're running a geo experiment with 20 cities.
               Can we detect a 10% increase with 80% power?"
    """
    print("=" * 70)
    print("Example 5: Cluster-Randomized Experiment (Geo Test)")
    print("=" * 70)

    # Historical data: 20 cities, 50 users per city
    np.random.seed(42)

    # Generate clustered data (users within cities are correlated)
    n_clusters = 20
    cluster_size = 50

    data = []
    clusters = []

    for cluster_id in range(n_clusters):
        # Each city has its own baseline
        city_baseline = np.random.normal(100, 15)

        # Users within city are correlated
        city_data = city_baseline + np.random.normal(0, 10, cluster_size)

        data.extend(city_data)
        clusters.extend([cluster_id] * cluster_size)

    sample = SampleData(
        data=np.array(data),
        clusters=np.array(clusters),
        name="Historical (20 cities)"
    )

    print(f"Total observations: {len(sample.data)}")
    print(f"Number of clusters: {len(np.unique(sample.clusters))}")
    print(f"Avg cluster size: {len(sample.data) / len(np.unique(sample.clusters)):.0f}")
    print()

    # Calculate ICC to see clustering effect
    from utils.cluster_utils import calculate_icc
    icc = calculate_icc(sample.data, sample.clusters)
    print(f"Intra-Class Correlation (ICC): {icc:.3f}")
    print("(ICC > 0 means observations within clusters are correlated)")
    print()

    # Configure cluster test
    test = ClusteredTTest(alpha=0.05, test_type="relative", min_clusters=5)
    analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

    # Estimate power for 10% increase
    power = analyzer.power_analysis(
        sample=sample,
        effect=0.10,
        effect_type="multiplicative"
    )

    print(f"Planned effect: 10% increase")
    print(f"Estimated power: {power:.1%}")
    print()

    if power >= 0.8:
        print("✓ Sufficient power for cluster experiment!")
    else:
        print("✗ Warning! Low power for cluster experiment.")
        print("  - Clustering reduces effective sample size")
        print("  - Consider adding more clusters (not more users per cluster!)")
    print()


# =============================================================================
# Example 6: Clustered Bootstrap (Most Flexible!)
# =============================================================================

def example_clustered_bootstrap_mde():
    """
    MDE for clustered bootstrap test.

    Clustered bootstrap combines:
    - Cluster-robust inference
    - No distributional assumptions
    - Custom statistics

    Perfect for complex geo experiments with non-normal metrics.
    """
    print("=" * 70)
    print("Example 6: Clustered Bootstrap MDE")
    print("=" * 70)

    # Store-level experiment with skewed revenue
    np.random.seed(42)

    n_stores = 15
    customers_per_store = 40

    data = []
    clusters = []

    for store_id in range(n_stores):
        # Each store has different baseline (skewed)
        store_baseline = np.random.lognormal(4.5, 0.3)

        # Customers within store
        store_data = store_baseline * np.random.lognormal(0, 0.5, customers_per_store)

        data.extend(store_data)
        clusters.extend([store_id] * customers_per_store)

    sample = SampleData(
        data=np.array(data),
        clusters=np.array(clusters),
        name="Store Revenue"
    )

    print(f"Total observations: {len(sample.data)}")
    print(f"Number of stores: {len(np.unique(sample.clusters))}")
    print(f"Mean revenue: ${np.mean(sample.data):.2f}")
    print(f"Median revenue: ${np.median(sample.data):.2f}")
    print()

    # Configure clustered bootstrap
    test = ClusteredBootstrapTest(
        alpha=0.05,
        n_bootstrap=500,
        test_type="relative",
        min_clusters=5
    )
    analyzer = PowerAnalyzer(test=test, n_simulations=80, seed=42)

    print("Calculating MDE for clustered bootstrap...")
    print("(This handles both clustering AND skewness)")
    print()

    mde = analyzer.minimum_detectable_effect(
        sample=sample,
        target_power=0.8,
        effect_type="multiplicative",
        max_iterations=12
    )

    print(f"Minimum detectable effect: {mde:.1%}")
    print()
    print("This MDE accounts for:")
    print("  ✓ Store-level clustering")
    print("  ✓ Non-normal revenue distribution")
    print("  ✓ Bootstrap resampling variability")
    print()


# =============================================================================
# Example 7: Binary Metrics (Conversion Rate)
# =============================================================================

def example_binary_metrics():
    """
    Power analysis for binary metrics (conversions, clicks, purchases).

    Question: "We have 3% baseline conversion. Can we detect a
               1 percentage point increase (3% → 4%)?"
    """
    print("=" * 70)
    print("Example 7: Binary Metrics (Conversion Rate)")
    print("=" * 70)

    # Historical conversion data (binary: 0 or 1)
    np.random.seed(42)
    baseline_rate = 0.03
    n_users = 2000

    historical_conversions = np.random.binomial(1, baseline_rate, n_users)

    sample = SampleData(
        data=historical_conversions,
        name="Conversions"
    )

    observed_rate = np.mean(sample.data)
    print(f"Sample size: {len(sample.data)} users")
    print(f"Baseline conversion rate: {observed_rate:.1%}")
    print(f"Conversions: {int(np.sum(sample.data))} / {n_users}")
    print()

    # Configure Z-test for proportions
    test = ZTest(alpha=0.05)
    analyzer = PowerAnalyzer(test=test, n_simulations=300, seed=42)

    # Test power for 1 percentage point increase (3% → 4%)
    effect = 0.01  # Absolute increase in proportion

    power = analyzer.power_analysis(
        sample=sample,
        effect=effect,
        effect_type="binary"  # Binary simulator flips 0→1 or 1→0
    )

    print(f"Planned effect: +{effect:.1%} (3% → 4%)")
    print(f"Estimated power: {power:.1%}")
    print()

    if power >= 0.8:
        print("✓ Sufficient power to detect 1pp increase")
    else:
        print("✗ Need more users to detect this small increase")
    print()

    # Calculate MDE
    print("What IS the minimum detectable effect?")

    mde = analyzer.minimum_detectable_effect(
        sample=sample,
        target_power=0.8,
        effect_type="binary"
    )

    print(f"MDE: {mde:.2%} (from {observed_rate:.1%} to {observed_rate + mde:.1%})")
    print()


# =============================================================================
# Example 8: Comparing Sample Sizes
# =============================================================================

def example_sample_size_comparison():
    """
    Compare power across different sample sizes.

    Question: "How many users do we need for 80% power?"
    """
    print("=" * 70)
    print("Example 8: Sample Size Comparison")
    print("=" * 70)

    # Historical data pool
    np.random.seed(42)
    historical_pool = np.random.normal(loc=100, scale=20, size=5000)

    # Target effect
    target_effect = 0.05  # 5% relative increase

    # Test different sample sizes
    sample_sizes = [200, 500, 1000, 2000, 3000]

    test = TTest(alpha=0.05, test_type="relative")

    print(f"Target effect: {target_effect:.0%} relative increase")
    print(f"Alpha: {test.alpha}")
    print()
    print("Sample Size  |  Estimated Power")
    print("-" * 40)

    for n in sample_sizes:
        # Use subset of historical data
        sample = SampleData(data=historical_pool[:n])

        analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)
        power = analyzer.power_analysis(
            sample=sample,
            effect=target_effect,
            effect_type="multiplicative"
        )

        marker = "✓" if power >= 0.8 else " "
        print(f"  {n:5d}      |    {power:5.1%}        {marker}")

    print()
    print("✓ = Achieves 80% power")
    print()


# =============================================================================
# Run All Examples
# =============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "POWER ANALYSIS EXAMPLES" + " " * 30 + "║")
    print("║" + " " * 15 + "Monte Carlo Simulation" + " " * 31 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    example_basic_power_analysis()
    print("\n")

    example_mde_calculation()
    print("\n")

    example_power_curve()
    print("\n")

    example_bootstrap_mde()
    print("\n")

    example_cluster_power_analysis()
    print("\n")

    example_clustered_bootstrap_mde()
    print("\n")

    example_binary_metrics()
    print("\n")

    example_sample_size_comparison()
    print("\n")

    print("=" * 70)
    print("All examples completed!")
    print()
    print("Key takeaways:")
    print("  1. PowerAnalyzer works with ALL abtk tests")
    print("  2. Simulation-based MDE is essential for Bootstrap & Cluster tests")
    print("  3. Effect types: additive (absolute), multiplicative (%), binary (0/1)")
    print("  4. Splitters automatically handle simple/cluster/paired designs")
    print("  5. 100% NumPy - no pandas required!")
    print("=" * 70)
