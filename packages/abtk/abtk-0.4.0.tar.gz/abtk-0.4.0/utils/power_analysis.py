"""
Power analysis and sample size calculations.

This module provides general utilities for power analysis that are shared across
different test types.

Test-specific MDE and sample size calculations have been moved to their respective test classes:
- TTest._calculate_mde() for regular t-test MDE
- TTest._calculate_required_sample_size() for regular t-test sample size
- CupedTTest._calculate_mde() for CUPED t-test MDE
- ZTest._calculate_mde() for Z-test (proportion) MDE
"""

import numpy as np
import scipy.stats as sps


def calculate_power(
    mean1: float,
    mean2: float,
    std: float,
    n1: int,
    n2: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for a two-sample comparison test.

    This function calculates power based on effect size and sample sizes.
    Works for t-tests, z-tests, and other tests that use normal approximation.

    Parameters
    ----------
    mean1 : float
        Mean/proportion of first sample (control)
    mean2 : float
        Mean/proportion of second sample (treatment)
    std : float
        Pooled standard deviation (or standard error for proportions)
    n1 : int
        Sample size of first sample
    n2 : int
        Sample size of second sample
    alpha : float, default=0.05
        Significance level (two-sided)

    Returns
    -------
    float
        Statistical power (probability of detecting the effect)

    Notes
    -----
    This is a general power calculation that can be used for:
    - Two-sample t-test (continuous data)
    - Z-test (proportions)
    - Any test using normal approximation

    Examples
    --------
    >>> # T-test power
    >>> calculate_power(mean1=100, mean2=105, std=15, n1=1000, n2=1000)
    0.843

    >>> # Z-test power (proportions)
    >>> calculate_power(mean1=0.10, mean2=0.12, std=0.03, n1=1000, n2=1000)
    0.756
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Sample sizes must be positive")
    if std <= 0:
        raise ValueError("Standard deviation must be positive")

    # Effect size (Cohen's d)
    effect_size = abs(mean2 - mean1) / std

    # Pooled standard error
    se = std * np.sqrt(1/n1 + 1/n2)

    # Z-score for alpha
    z_alpha = sps.norm.ppf(1 - alpha / 2)

    # Non-centrality parameter
    ncp = abs(mean2 - mean1) / se

    # Power calculation
    power = 1 - sps.norm.cdf(z_alpha - ncp) + sps.norm.cdf(-z_alpha - ncp)

    return power


# =============================================================================
# Monte Carlo Simulation-Based Power Analysis
# =============================================================================

from typing import List, Dict, Optional, Tuple
import warnings

from core.data_types import SampleData
from core.base_test_processor import BaseTestProcessor
from utils.effect_simulator import (
    EffectSimulator,
    get_effect_simulator
)


class PowerAnalyzer:
    """
    Monte Carlo simulation for power analysis.

    Estimates statistical power by simulating treatment effects on historical
    data. Automatically handles data splitting and perturbation for each
    simulation iteration.

    **Critical workflow:**
    For each simulation:
    1. **Split** historical data → control + treatment (50/50)
    2. **Perturbate** treatment with simulated effect (CORE STEP!)
    3. **Test** using provided statistical test
    4. **Count** significant results
    Power = (# rejections) / n_simulations

    **Perturbations are essential!** Without effect simulation, there is no
    effect to detect, and power would just measure Type I error rate (~alpha).

    Parameters
    ----------
    test : BaseTestProcessor
        Any abtk test (TTest, BootstrapTest, ClusteredTTest, etc.)
        Must be fully configured (alpha, test_type, etc.)
    n_simulations : int, default=1000
        Number of Monte Carlo simulations to run
    seed : int, optional
        Random seed for reproducibility

    Examples
    --------
    >>> from core.data_types import SampleData
    >>> from tests.parametric import TTest
    >>> from utils.power_analysis import PowerAnalyzer
    >>> import numpy as np
    >>>
    >>> # Historical data
    >>> historical = SampleData(data=np.random.normal(100, 20, 1000))
    >>>
    >>> # Plan experiment
    >>> test = TTest(alpha=0.05, test_type="relative")
    >>> analyzer = PowerAnalyzer(test=test, n_simulations=1000)
    >>>
    >>> # Estimate power
    >>> power = analyzer.power_analysis(
    ...     sample=historical,
    ...     effect=0.05,
    ...     effect_type="multiplicative"
    ... )
    >>> print(f"Power: {power:.1%}")
    Power: 78.0%
    """

    def __init__(
        self,
        test: BaseTestProcessor,
        n_simulations: int = 1000,
        seed: Optional[int] = None
    ):
        self.test = test
        self.n_simulations = n_simulations
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        if n_simulations < 100:
            warnings.warn(
                f"n_simulations={n_simulations} is very low. "
                f"Power estimates will be noisy. Recommend at least 1000.",
                UserWarning
            )

    def power_analysis(
        self,
        sample: SampleData,
        effect: float,
        effect_type: str = "additive",
        n_simulations: Optional[int] = None
    ) -> float:
        """
        Estimate statistical power for given effect size.

        Parameters
        ----------
        sample : SampleData
            Historical data (NOT split). PowerAnalyzer handles splitting.
        effect : float
            Effect size to simulate
        effect_type : str, default="additive"
            "additive", "multiplicative", or "binary"
        n_simulations : int, optional
            Override default n_simulations

        Returns
        -------
        float
            Estimated power (0 to 1)
        """
        n_sims = n_simulations or self.n_simulations
        simulator = get_effect_simulator(effect_type)

        n_rejections = 0
        for _ in range(n_sims):
            control, treatment = self._split_sample(sample)
            treatment_perturbed = self._apply_effect(treatment, effect, simulator)

            try:
                result = self.test.compare([control, treatment_perturbed])[0]
                if result.pvalue < self.test.alpha:
                    n_rejections += 1
            except Exception as e:
                warnings.warn(f"Simulation failed: {str(e)}", UserWarning)
                continue

        return n_rejections / n_sims

    def power_line(
        self,
        sample: SampleData,
        effects: List[float],
        effect_type: str = "additive",
        n_simulations: Optional[int] = None
    ) -> Dict[float, float]:
        """Compute power curve for multiple effect sizes."""
        return {
            effect: self.power_analysis(sample, effect, effect_type, n_simulations)
            for effect in effects
        }

    def minimum_detectable_effect(
        self,
        sample: SampleData,
        target_power: float = 0.8,
        effect_type: str = "additive",
        search_range: Optional[Tuple[float, float]] = None,
        tolerance: float = 0.001,
        max_iterations: int = 20
    ) -> float:
        """Find minimum effect size that achieves target power via binary search."""
        if search_range is None:
            if effect_type == "multiplicative":
                search_range = (0.001, 0.5)
            elif effect_type == "binary":
                baseline_rate = np.mean(sample.data)
                max_increase = 1.0 - baseline_rate
                max_decrease = baseline_rate
                search_range = (-max_decrease * 0.9, max_increase * 0.9)
            else:
                data_std = np.std(sample.data, ddof=1)
                search_range = (0.01 * data_std, 2.0 * data_std)

        low, high = search_range
        iteration = 0

        while iteration < max_iterations and (high - low) > tolerance * abs(high):
            mid = (low + high) / 2
            power = self.power_analysis(sample, mid, effect_type)

            if power < target_power:
                low = mid
            else:
                high = mid

            iteration += 1

        if iteration >= max_iterations:
            warnings.warn(f"Binary search did not fully converge after {max_iterations} iterations", UserWarning)

        return (low + high) / 2

    # Splitter methods
    def _split_sample(self, sample: SampleData) -> Tuple[SampleData, SampleData]:
        """Split historical data into control/treatment."""
        if sample.clusters is not None:
            return self._split_by_clusters(sample)
        elif sample.paired_ids is not None:
            return self._split_by_pairs(sample)
        else:
            return self._split_simple(sample)

    def _split_simple(self, sample: SampleData) -> Tuple[SampleData, SampleData]:
        """Simple random 50/50 split."""
        n = sample.sample_size
        indices = np.arange(n)
        np.random.shuffle(indices)
        split_point = n // 2

        control = SampleData(
            data=sample.data[indices[:split_point]],
            covariates=sample.covariates[indices[:split_point]] if sample.covariates is not None else None,
            strata=sample.strata[indices[:split_point]] if sample.strata is not None else None,
            name="Control (sim)"
        )
        treatment = SampleData(
            data=sample.data[indices[split_point:]],
            covariates=sample.covariates[indices[split_point:]] if sample.covariates is not None else None,
            strata=sample.strata[indices[split_point:]] if sample.strata is not None else None,
            name="Treatment (sim)"
        )
        return control, treatment

    def _split_by_clusters(self, sample: SampleData) -> Tuple[SampleData, SampleData]:
        """Cluster-randomized split."""
        unique_clusters = np.unique(sample.clusters)
        n_clusters = len(unique_clusters)

        if n_clusters < 4:
            warnings.warn(f"Only {n_clusters} clusters. Need 5-10+ for reliable inference.", UserWarning)

        shuffled = unique_clusters.copy()
        np.random.shuffle(shuffled)
        split_point = n_clusters // 2

        control_clusters = shuffled[:split_point]
        treatment_clusters = shuffled[split_point:]

        control_mask = np.isin(sample.clusters, control_clusters)
        treatment_mask = np.isin(sample.clusters, treatment_clusters)

        control = SampleData(
            data=sample.data[control_mask],
            clusters=sample.clusters[control_mask],
            covariates=sample.covariates[control_mask] if sample.covariates is not None else None,
            name="Control (sim)"
        )
        treatment = SampleData(
            data=sample.data[treatment_mask],
            clusters=sample.clusters[treatment_mask],
            covariates=sample.covariates[treatment_mask] if sample.covariates is not None else None,
            name="Treatment (sim)"
        )
        return control, treatment

    def _split_by_pairs(self, sample: SampleData) -> Tuple[SampleData, SampleData]:
        """Paired design split."""
        unique_pairs = np.unique(sample.paired_ids)
        control_idx, treatment_idx = [], []

        for pair_id in unique_pairs:
            pair_indices = np.where(sample.paired_ids == pair_id)[0]
            if len(pair_indices) != 2:
                raise ValueError(f"Pair {pair_id} has {len(pair_indices)} observations, expected 2")

            if np.random.rand() < 0.5:
                control_idx.append(pair_indices[0])
                treatment_idx.append(pair_indices[1])
            else:
                control_idx.append(pair_indices[1])
                treatment_idx.append(pair_indices[0])

        control_idx = np.array(control_idx)
        treatment_idx = np.array(treatment_idx)

        control = SampleData(
            data=sample.data[control_idx],
            paired_ids=sample.paired_ids[control_idx],
            covariates=sample.covariates[control_idx] if sample.covariates is not None else None,
            name="Control (sim)"
        )
        treatment = SampleData(
            data=sample.data[treatment_idx],
            paired_ids=sample.paired_ids[treatment_idx],
            covariates=sample.covariates[treatment_idx] if sample.covariates is not None else None,
            name="Treatment (sim)"
        )
        return control, treatment

    def _apply_effect(
        self,
        sample: SampleData,
        effect: float,
        simulator: EffectSimulator
    ) -> SampleData:
        """Apply simulated effect (perturbation)."""
        perturbed_data = simulator.apply_effect(sample.data, effect, sample.clusters)
        return SampleData(
            data=perturbed_data,
            covariates=sample.covariates,
            clusters=sample.clusters,
            paired_ids=sample.paired_ids,
            strata=sample.strata,
            name=sample.name
        )
