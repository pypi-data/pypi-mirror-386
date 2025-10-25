"""
Effect simulation strategies for power analysis.

This module provides effect simulators that are the CORE of simulation-based
power analysis. Effect simulators apply simulated treatment effects to data,
which is the critical step that differentiates power analysis from Type I error
rate measurement.

Without effect simulation, there is no treatment effect to detect, and power
analysis would be meaningless.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Optional


class EffectSimulator(ABC):
    """
    Abstract base class for effect simulation strategies.

    Effect simulators are the HEART of simulation-based power analysis.
    They add the simulated treatment effect to the data, which is the only
    way to estimate power (probability of detecting an effect when it exists).

    Without perturbation, there is no effect, and power analysis would just
    measure Type I error rate (~alpha).

    Examples
    --------
    >>> # Create simulator
    >>> simulator = AdditiveEffectSimulator()
    >>>
    >>> # Apply effect to data
    >>> data = np.array([100, 105, 98, 102])
    >>> perturbed = simulator.apply_effect(data, effect=5.0)
    >>> perturbed
    array([105, 110, 103, 107])
    """

    @abstractmethod
    def apply_effect(
        self,
        data: np.ndarray,
        effect: float,
        clusters: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Apply simulated treatment effect to data.

        This is the CRITICAL step in simulation-based power analysis.
        Without this, there is no effect to detect, and power analysis
        would be meaningless.

        Parameters
        ----------
        data : np.ndarray
            Individual-level metric values (1D array)
        effect : float
            Effect size to apply
        clusters : np.ndarray, optional
            Cluster IDs for each observation (for cluster experiments)
            Currently unused, reserved for future heterogeneous effects

        Returns
        -------
        np.ndarray
            Data with effect applied (same shape as input)

        Notes
        -----
        Implementations should:
        - Use vectorized NumPy operations (no loops)
        - Return new array (don't modify input)
        - Preserve array shape
        """
        pass


class AdditiveEffectSimulator(EffectSimulator):
    """
    Additive effect: data + effect

    Use for metrics where effect is an absolute change:
    - Revenue: $100 → $105 (effect = +5)
    - Session duration: 10min → 12min (effect = +2)
    - Page views: 5 → 6 (effect = +1)

    Formula
    -------
    Y_new = Y_old + effect

    Examples
    --------
    >>> simulator = AdditiveEffectSimulator()
    >>> data = np.array([100, 105, 98, 102])
    >>> perturbed = simulator.apply_effect(data, effect=5.0)
    >>> perturbed
    array([105, 110, 103, 107])

    >>> # Works with any array size
    >>> large_data = np.random.normal(100, 20, 1000)
    >>> perturbed = simulator.apply_effect(large_data, effect=10.0)
    >>> np.mean(perturbed) - np.mean(large_data)
    10.0

    Notes
    -----
    - Fast: vectorized NumPy operation
    - No assumptions about data distribution
    - Effect is same for all observations
    """

    def apply_effect(
        self,
        data: np.ndarray,
        effect: float,
        clusters: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Add constant effect to all observations."""
        return data + effect


class MultiplicativeEffectSimulator(EffectSimulator):
    """
    Multiplicative effect: data * (1 + effect)

    Use for metrics where effect is a relative change:
    - Revenue: $100 → $105 (effect = 0.05 = 5% increase)
    - CTR: 5% → 5.25% (effect = 0.05 = 5% relative increase)
    - Conversion: 10% → 11% (effect = 0.10 = 10% relative increase)

    Formula
    -------
    Y_new = Y_old × (1 + effect)

    Examples
    --------
    >>> simulator = MultiplicativeEffectSimulator()
    >>> data = np.array([100, 105, 98, 102])
    >>> perturbed = simulator.apply_effect(data, effect=0.05)
    >>> perturbed
    array([105.  , 110.25, 102.9 , 107.1 ])

    >>> # 5% increase
    >>> np.mean(perturbed) / np.mean(data) - 1
    0.05

    >>> # Works with negative effects (decreases)
    >>> perturbed_neg = simulator.apply_effect(data, effect=-0.10)
    >>> perturbed_neg
    array([90. , 94.5, 88.2, 91.8])

    Notes
    -----
    - Fast: vectorized NumPy operation
    - Effect is proportional to baseline value
    - Positive effect > 0: increase
    - Negative effect < 0: decrease
    - Effect = -1.0 means 100% decrease (all zeros) - use with caution!
    """

    def apply_effect(
        self,
        data: np.ndarray,
        effect: float,
        clusters: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Multiply data by (1 + effect)."""
        return data * (1 + effect)


class BinaryEffectSimulator(EffectSimulator):
    """
    Binary effect: flip 0→1 or 1→0 to achieve target effect

    Use for binary metrics (conversions, clicks, purchases):
    - Conversion rate: 5% → 6% (effect = 0.01 = +1 percentage point)
    - Click-through rate: 10% → 11% (effect = 0.01 = +1pp)
    - Purchase rate: 3% → 4% (effect = 0.01 = +1pp)

    Effect is interpreted as absolute change in proportion of 1s.
    - Positive effect: flip 0→1 (increase conversions)
    - Negative effect: flip 1→0 (decrease conversions)

    Formula
    -------
    n_flips = |effect| × n_observations
    If effect > 0: randomly flip n_flips zeros to ones
    If effect < 0: randomly flip n_flips ones to zeros

    Examples
    --------
    >>> simulator = BinaryEffectSimulator()
    >>> np.random.seed(42)
    >>>
    >>> # Baseline 33% conversion rate
    >>> data = np.array([0, 0, 0, 0, 1, 1])
    >>> baseline_rate = np.mean(data)
    >>> baseline_rate
    0.3333...

    >>> # Increase by 17pp → 50% final rate
    >>> perturbed = simulator.apply_effect(data, effect=0.17)
    >>> np.mean(perturbed)
    0.5

    >>> # Decrease by 17pp → 17% final rate
    >>> perturbed_neg = simulator.apply_effect(data, effect=-0.17)
    >>> np.mean(perturbed_neg)
    0.1666...

    >>> # Large dataset: 1000 users, 5% baseline
    >>> np.random.seed(42)
    >>> large_data = np.random.binomial(1, 0.05, 1000)
    >>> np.mean(large_data)
    0.043
    >>>
    >>> # Increase by 2pp
    >>> perturbed_large = simulator.apply_effect(large_data, effect=0.02)
    >>> np.mean(perturbed_large)
    0.063  # ~6.3% (increased from 4.3%)

    Raises
    ------
    ValueError
        If data is not binary (only 0 and 1 allowed)
        If effect is impossible (e.g., increase when all are 1)

    Notes
    -----
    - Validates that data is binary (0 and 1 only)
    - Effect must be achievable:
      - To increase: need enough zeros to flip
      - To decrease: need enough ones to flip
    - Uses random sampling (reproducible with np.random.seed)
    """

    def apply_effect(
        self,
        data: np.ndarray,
        effect: float,
        clusters: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Flip binary values to achieve target effect.

        Parameters
        ----------
        data : np.ndarray
            Binary data (only 0 and 1)
        effect : float
            Change in proportion of 1s
            - Positive: increase conversions (flip 0→1)
            - Negative: decrease conversions (flip 1→0)
        clusters : np.ndarray, optional
            Not used for binary simulator

        Returns
        -------
        np.ndarray
            Perturbed binary data

        Raises
        ------
        ValueError
            If data is not binary or if effect is impossible
        """
        # Validate binary data
        unique_vals = np.unique(data)
        if not np.all(np.isin(unique_vals, [0, 1])):
            raise ValueError(
                f"BinaryEffectSimulator requires binary data (0 and 1 only). "
                f"Found unique values: {unique_vals}. "
                f"For continuous metrics, use AdditiveEffectSimulator or "
                f"MultiplicativeEffectSimulator."
            )

        # Calculate number of flips needed
        n_total = len(data)
        n_to_flip = int(abs(effect) * n_total)

        # No flips needed if effect is tiny
        if n_to_flip == 0:
            return data.copy()

        result = data.copy()

        if effect > 0:
            # Increase conversions: flip 0 → 1
            zeros_idx = np.where(data == 0)[0]
            if len(zeros_idx) < n_to_flip:
                raise ValueError(
                    f"Cannot increase conversion rate by {effect:.2%}: "
                    f"only {len(zeros_idx)} non-converters available "
                    f"(need to flip {n_to_flip} to achieve effect). "
                    f"Current conversion rate: {np.mean(data):.2%}. "
                    f"Maximum possible increase: {len(zeros_idx)/n_total:.2%} "
                    f"(converting all non-converters)."
                )
            flip_idx = np.random.choice(zeros_idx, size=n_to_flip, replace=False)
            result[flip_idx] = 1

        elif effect < 0:
            # Decrease conversions: flip 1 → 0
            ones_idx = np.where(data == 1)[0]
            if len(ones_idx) < n_to_flip:
                raise ValueError(
                    f"Cannot decrease conversion rate by {effect:.2%}: "
                    f"only {len(ones_idx)} converters available "
                    f"(need to flip {n_to_flip} to achieve effect). "
                    f"Current conversion rate: {np.mean(data):.2%}. "
                    f"Maximum possible decrease: {len(ones_idx)/n_total:.2%} "
                    f"(removing all converters)."
                )
            flip_idx = np.random.choice(ones_idx, size=n_to_flip, replace=False)
            result[flip_idx] = 0

        return result


# Mapping for easy access
EFFECT_SIMULATORS = {
    "additive": AdditiveEffectSimulator,
    "multiplicative": MultiplicativeEffectSimulator,
    "binary": BinaryEffectSimulator,
}


def get_effect_simulator(effect_type: str) -> EffectSimulator:
    """
    Get effect simulator by name.

    Parameters
    ----------
    effect_type : str
        Type of effect: "additive", "multiplicative", or "binary"

    Returns
    -------
    EffectSimulator
        Initialized effect simulator

    Raises
    ------
    ValueError
        If effect_type is not recognized

    Examples
    --------
    >>> simulator = get_effect_simulator("additive")
    >>> isinstance(simulator, AdditiveEffectSimulator)
    True

    >>> simulator = get_effect_simulator("multiplicative")
    >>> isinstance(simulator, MultiplicativeEffectSimulator)
    True

    >>> simulator = get_effect_simulator("binary")
    >>> isinstance(simulator, BinaryEffectSimulator)
    True

    >>> get_effect_simulator("unknown")
    Traceback (most recent call last):
    ...
    ValueError: Unknown effect_type: 'unknown'. Must be one of: additive, multiplicative, binary
    """
    if effect_type not in EFFECT_SIMULATORS:
        raise ValueError(
            f"Unknown effect_type: '{effect_type}'. "
            f"Must be one of: {', '.join(EFFECT_SIMULATORS.keys())}"
        )

    return EFFECT_SIMULATORS[effect_type]()
