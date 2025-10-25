# Frequently Asked Questions (FAQ)

## General Questions

### What is ABTK?

ABTK (A/B Testing Toolkit) is a Python library for statistical analysis of A/B tests. It provides 12 different statistical tests (including parametric, nonparametric, and cluster tests), variance reduction techniques (CUPED/ANCOVA), simulation-based power analysis, and utilities for rigorous A/B test analysis.

### Why use ABTK instead of scipy.stats?

ABTK provides:
- **Unified interface** - all tests return same `TestResult` format
- **Variance reduction** - CUPED and ANCOVA for increased sensitivity
- **Multiple comparisons correction** - built-in Bonferroni, Benjamini-Hochberg
- **Quantile analysis** - understand where effects occur in the distribution
- **A/B test specific** - designed specifically for experimentation workflows

### Is ABTK suitable for production?

ABTK is currently in alpha (v0.1.0). It's suitable for:
- ✅ Research and exploratory analysis
- ✅ Internal A/B test analysis
- ✅ Learning and education

For production use:
- Run unit tests: `pytest unit_tests/`
- Validate with your own simulations
- Review source code for your use case

---

## Test Selection

### How do I choose between T-Test and Bootstrap?

**Use T-Test if:**
- Data is approximately normal
- Want exact p-values
- Fast computation needed

**Use Bootstrap if:**
- Data is skewed or has outliers
- Non-normal distribution
- Small sample size (n < 30)
- Want robustness

### When should I use CUPED?

Use CUPED when:
- ✅ You have pre-experiment data (baseline metrics)
- ✅ Correlation between baseline and outcome > 0.5
- ✅ Want to reduce variance → narrower CI
- ✅ Want to detect smaller effects

Don't use CUPED when:
- ❌ No historical data available
- ❌ Correlation < 0.3 (won't help)
- ❌ Historical data is unreliable/biased

### CUPED vs ANCOVA - what's the difference?

| Feature | CUPED | ANCOVA |
|---------|-------|--------|
| **Covariates** | 1 covariate | Multiple covariates |
| **Method** | Linear adjustment | Regression adjustment |
| **Interactions** | No | Yes (optional check) |
| **Diagnostics** | No | Yes (VIF, normality, etc.) |
| **Use when** | Simple variance reduction | Complex, need diagnostics |

### What's the difference between Paired T-Test and CUPED?

**Paired T-Test:**
- Matched pairs design (match users BEFORE randomization)
- Removes between-subject variability
- Requires paired_ids
- Analyzes differences within pairs

**CUPED:**
- Independent randomization (standard A/B)
- Adjusts for baseline using covariates
- Removes correlation with baseline
- Works on original observations

---

## Data Preparation

### What format should my data be in?

Use `SampleData` for continuous metrics:
```python
from core.data_types import SampleData

sample = SampleData(
    data=[100, 110, 95, 105],         # Required: metric values
    covariates=[90, 100, 85, 95],     # Optional: for variance reduction
    strata=['A', 'A', 'B', 'B'],      # Optional: for stratified bootstrap
    paired_ids=[1, 2, 3, 4],          # Optional: for paired tests
    name="Control"
)
```

Use `ProportionData` for binary metrics:
```python
from core.data_types import ProportionData

sample = ProportionData(
    successes=450,    # Number of successes (clicks, conversions)
    trials=1000,      # Total trials (impressions, users)
    name="Control"
)
```

### How do I handle missing data?

ABTK does not handle missing data automatically. You should:

1. **Remove users with missing values** (complete case analysis)
2. **Impute missing values** before passing to ABTK
3. **Use only users with complete data**

Example:
```python
import pandas as pd

# Option 1: Drop missing
df_clean = df.dropna(subset=['metric', 'covariate'])

# Option 2: Mean imputation
df['covariate'].fillna(df['covariate'].mean(), inplace=True)

# Create SampleData
sample = SampleData(
    data=df_clean['metric'].values,
    covariates=df_clean['covariate'].values
)
```

### Can I use pandas DataFrame directly?

**Yes!** Use the DataFrame helper utilities (recommended for beginners):

```python
import pandas as pd
from utils.dataframe_helpers import sample_data_from_dataframe

# For continuous metrics (revenue, time, etc.)
df = pd.DataFrame({
    'group': ['control', 'control', 'treatment', 'treatment'],
    'revenue': [100, 110, 105, 115],
    'baseline_revenue': [90, 100, 92, 102]
})

samples = sample_data_from_dataframe(
    df,
    group_col='group',
    metric_col='revenue',
    covariate_cols='baseline_revenue'  # Optional
)

# samples is a list of SampleData objects ready to use!
test = TTest()
results = test.compare(samples)
```

For proportions (CTR, CVR):
```python
from utils.dataframe_helpers import proportion_data_from_dataframe

# Format 1: Aggregated data
df_agg = pd.DataFrame({
    'group': ['control', 'treatment'],
    'clicks': [450, 520],
    'impressions': [10000, 10000]
})

samples = proportion_data_from_dataframe(
    df_agg,
    group_col='group',
    successes_col='clicks',
    trials_col='impressions'
)

# Format 2: Raw binary data (0/1 per user)
df_raw = pd.DataFrame({
    'group': ['control'] * 100 + ['treatment'] * 100,
    'clicked': [0, 1, 0, 0, 1, ...]  # Individual clicks
})

samples = proportion_data_from_dataframe(
    df_raw,
    group_col='group',
    binary_col='clicked'
)
```

**Alternative: Manual conversion** (for advanced users):

```python
df_control = df[df['group'] == 'control']
df_treatment = df[df['group'] == 'treatment']

control = SampleData(
    data=df_control['revenue'].values,           # .values converts to numpy
    covariates=df_control['baseline'].values,
    name="Control"
)
```

---

## Interpretation

### What does "effect" mean?

**Relative effect** (default, `test_type="relative"`):
- Percentage change
- `effect=0.05` means 5% increase
- `effect=-0.03` means 3% decrease
- Easier to interpret across different scales

**Absolute effect** (`test_type="absolute"`):
- Raw difference in units
- `effect=5.5` means +5.5 units (e.g., $5.50)
- Depends on scale of metric

### How do I interpret the confidence interval?

The 95% CI represents the range where the true effect likely lies.

Example:
```
Effect: 5.5%
95% CI: [0.8%, 10.2%]
```

Interpretation:
- Best estimate: 5.5% lift
- We're 95% confident true effect is between 0.8% and 10.2%
- Since CI doesn't include 0, effect is significant

**Decision making:**
- If CI contains 0 → not significant (could be no effect)
- If CI all positive → significant positive effect
- If CI all negative → significant negative effect

### What's the difference between pvalue and reject?

```python
result.pvalue   # 0.023 (2.3% chance of seeing this if no real effect)
result.reject   # True (significant at alpha=0.05)
```

- **pvalue**: Probability of seeing effect this large if null hypothesis true
- **reject**: Binary decision (is pvalue < alpha?)

Rule of thumb:
- pvalue < 0.05 → significant (reject null)
- pvalue ≥ 0.05 → not significant (fail to reject null)

---

## Experiment Planning

### How do I calculate sample size / MDE?

ABTK provides **two approaches** for experiment planning:

**1. Analytical (fast, exact formulas):**
```python
from utils.sample_size_calculator import calculate_mde_ttest, calculate_sample_size_ttest

# What can I detect with 1000 users?
mde = calculate_mde_ttest(mean=100, std=20, n=1000)
print(f"Can detect {mde:.2%} effect")  # 3.5%

# How many users to detect 5% effect?
n = calculate_sample_size_ttest(mean=100, std=20, mde=0.05)
print(f"Need {n:,} users per group")  # 1,571
```

**2. Simulation-based (for Bootstrap and cluster tests):**
```python
from utils.power_analysis import PowerAnalyzer
from tests.nonparametric import BootstrapTest

test = BootstrapTest(alpha=0.05, n_bootstrap=500, test_type="relative")
analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

# Calculate MDE (ONLY option for Bootstrap!)
mde = analyzer.minimum_detectable_effect(
    sample=historical_data,
    target_power=0.8,
    effect_type="multiplicative"
)
```

**See [Experiment Planning Guide](user-guide/experiment-planning.md) for complete details.**

### When should I use simulation vs analytical?

| Scenario | Use Analytical | Use Simulation |
|----------|----------------|----------------|
| TTest planning | ✅ Fast (~instant) | ⚠️ Slower (~10 sec) |
| ZTest planning | ✅ Fast | ⚠️ Slower |
| CUPED planning | ✅ If correlation known | ⚠️ Slower |
| **BootstrapTest** | ❌ No formula exists | ✅ **ONLY option** |
| **ClusteredBootstrapTest** | ❌ No formula exists | ✅ **ONLY option** |
| Cluster tests | ⚠️ Need ICC estimate | ✅ Easier, automatic |
| Quick "what-if" | ✅ Instant | ❌ Too slow |

**Rule of thumb:**
- Use **analytical** for TTest/CUPED/ZTest (faster)
- Use **simulation** for Bootstrap and cluster tests (ONLY option)

### How long does PowerAnalyzer simulation take?

Depends on test type and number of simulations:

| Configuration | Time |
|---------------|------|
| TTest, 1000 simulations | ~10 seconds |
| BootstrapTest (n_bootstrap=500), 100 simulations | ~30 seconds |
| BootstrapTest (n_bootstrap=500), 1000 simulations | ~5 minutes |

**Tip:** Start with 100-200 simulations for exploration, then use 1000 for final planning.

### Can PowerAnalyzer handle cluster experiments?

**Yes!** PowerAnalyzer automatically handles clustering:

```python
from tests.parametric import ClusteredTTest

# Historical data with cluster IDs
sample = SampleData(
    data=revenue_data,
    clusters=city_ids  # Cluster IDs (geo test, store test, etc.)
)

test = ClusteredTTest(alpha=0.05, test_type="relative")
analyzer = PowerAnalyzer(test=test, n_simulations=200, seed=42)

# Estimate power (splitter handles clustering automatically!)
power = analyzer.power_analysis(
    sample=sample,
    effect=0.10,  # 10% increase
    effect_type="multiplicative"
)
```

**Advantages over analytical:**
- No manual ICC estimation needed
- No design effect calculation
- Handles unbalanced clusters automatically
- Works with ClusteredBootstrapTest (no analytical formula!)

### What's the difference between effect types in PowerAnalyzer?

| Effect Type | Formula | Use Case | Example |
|-------------|---------|----------|---------|
| **multiplicative** | `Y × (1 + effect)` | Relative changes (%) | Revenue: $100 → $105 (effect=0.05) |
| **additive** | `Y + effect` | Absolute changes | Time: 10min → 12min (effect=2) |
| **binary** | Flip 0→1 or 1→0 | Conversion rates | CVR: 5% → 6% (effect=0.01) |

**Use `"multiplicative"` for most cases** (relative changes like "5% lift")

### Why do I need historical data for PowerAnalyzer?

PowerAnalyzer splits historical data to simulate the experiment:
1. Split data → control + treatment
2. Add effect to treatment (perturbation)
3. Run test
4. Repeat 1000 times → estimate power

**Without historical data:**
- Use analytical approach (`sample_size_calculator`)
- Or use industry estimates to create synthetic data

### How accurate is simulation vs analytical?

For tests with analytical formulas (TTest, ZTest), simulation converges to analytical:

```python
# Analytical: 3.5% MDE
mde_analytical = calculate_mde_ttest(mean=100, std=20, n=1000)

# Simulation: ~3.5% MDE (with high n_simulations)
analyzer = PowerAnalyzer(test=TTest(), n_simulations=5000, seed=42)
mde_simulation = analyzer.minimum_detectable_effect(...)

# Difference < 0.5% (Monte Carlo error)
```

**For Bootstrap tests:** Simulation is the ONLY option!

---

## Multiple Comparisons

### When do I need multiple comparisons correction?

Correct when testing multiple hypotheses:

**Need correction:**
- ✅ A vs B, A vs C, A vs D (3 tests)
- ✅ Testing multiple metrics on same data
- ✅ Sequential testing (peeking)

**Don't need correction:**
- ❌ Single comparison (A vs B)
- ❌ Pre-planned single hypothesis

### Which correction method should I use?

| Method | Type | When to Use |
|--------|------|-------------|
| **Bonferroni** | FWER | Conservative, few tests (< 10) |
| **Holm** | FWER | Better than Bonferroni, still conservative |
| **Benjamini-Hochberg** | FDR | Exploratory analysis, many tests |

```python
from utils.corrections import adjust_pvalues

# Conservative (FWER control)
adjusted = adjust_pvalues(results, method="bonferroni")

# Less conservative (FDR control)
adjusted = adjust_pvalues(results, method="benjamini-hochberg")
```

**For detailed explanation of all methods, see [Multiple Comparisons Guide](user-guide/multiple-comparisons.md).**

---

## Performance

### How many bootstrap samples should I use?

**For quick checks:**
```python
n_samples=1000  # Fast, less accurate
```

**For production/reports:**
```python
n_samples=10000  # Recommended, accurate
```

**For publication:**
```python
n_samples=100000  # Very accurate, slow
```

Rule of thumb: More samples = more accurate, but slower.

### How can I speed up bootstrap tests?

1. **Reduce n_samples** (for quick checks)
2. **Use parametric tests** (TTest faster than Bootstrap)
3. **Disable validation** in ANCOVA:
```python
test = AncovaTest(validate_assumptions=False)  # AncovaTest also available as OLSTest
```

---

## Errors and Troubleshooting

### Error: "Sample size too small"

**Cause**: Not enough observations for the test

**Solution**:
- T-Test: Need n ≥ 2 per group
- ANCOVA: Need n ≥ 10 * (number of covariates + 2)
- Bootstrap: Need n ≥ 10 per group (prefer n ≥ 30)

### Error: "Samples must have covariates"

**Cause**: Using CUPED/ANCOVA without covariates

**Solution**: Provide covariates or use different test
```python
# Add covariates
sample = SampleData(
    data=[...],
    covariates=[...],  # Add this!
    name="Control"
)

# Or use test without covariates
test = TTest()  # Instead of CupedTTest
```

### Error: "Correlation below minimum"

**Cause**: CUPED requires correlation > min_correlation (default 0.5)

**Solution**:
```python
# Option 1: Lower threshold (not recommended)
test = CupedTTest(min_correlation=0.3)

# Option 2: Use regular TTest (better if low correlation)
test = TTest()
```

### Warning: "Bootstrap distribution not normal"

**Cause**: Bootstrap distribution is non-normal

**Impact**: P-values and CIs are still valid (that's the point of bootstrap!)

**Action**: No action needed, this is expected for non-normal data

---

## Advanced Topics

### Can I use custom statistics (median, quantiles)?

Yes! Bootstrap tests support any statistic:

```python
import numpy as np
from tests.nonparametric import BootstrapTest

# Median instead of mean
test = BootstrapTest(
    alpha=0.05,
    stat_func=np.median,  # Custom statistic
    n_samples=10000
)

# 90th percentile
test = BootstrapTest(
    stat_func=lambda x: np.percentile(x, 90)
)
```

### How do I analyze effects at different quantiles?

Use `QuantileAnalyzer`:

```python
from tests.nonparametric import BootstrapTest
from utils.quantile_analysis import QuantileAnalyzer

bootstrap = BootstrapTest(alpha=0.05, n_samples=10000)
analyzer = QuantileAnalyzer(
    test=bootstrap,
    quantiles=[0.25, 0.5, 0.75, 0.9, 0.95]
)

results = analyzer.compare([control, treatment])
```

See [Quantile Analysis Guide](user-guide/quantile-analysis.md) for details.

### Can I get the effect distribution?

Yes, for parametric tests:

```python
test = TTest(return_effect_distribution=True)
results = test.compare([control, treatment])

result = results[0]
dist = result.effect_distribution  # scipy.stats distribution object

# Use it for custom calculations
prob_positive = 1 - dist.cdf(0)  # P(effect > 0)
```

---

## Contributing

### How can I add a new test?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guide.

Quick steps:
1. Inherit from `BaseTestProcessor`
2. Implement `compare()` and `compare_samples()` methods
3. Add docstrings and examples
4. Add unit tests in `unit_tests/`
5. Update documentation

### How do I report a bug?

1. Check if it's already reported: [GitHub Issues](https://github.com/yourusername/abtk/issues)
2. Create minimal reproducible example
3. Submit issue with:
   - Code to reproduce
   - Expected behavior
   - Actual behavior
   - Environment (Python version, OS)

---

## Still Have Questions?

- **Documentation**: Browse [User Guides](user-guide/) for detailed topics
- **Examples**: See [Examples](examples/) for real-world use cases
- **Issues**: Ask on [GitHub Issues](https://github.com/yourusername/abtk/issues)
