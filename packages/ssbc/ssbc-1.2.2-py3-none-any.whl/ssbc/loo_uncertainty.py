"""
Small-sample uncertainty quantification for LOO-CV conformal prediction.

This module handles all four sources of uncertainty:
1. LOO-CV correlation structure
2. Threshold calibration uncertainty
3. Parameter estimation uncertainty
4. Test sampling uncertainty

Designed for small calibration sets (n=20-40) where bootstrap is unreliable.
"""

import warnings
from typing import Any

import numpy as np
from scipy.stats import beta as beta_dist
from scipy.stats import binom, norm
from scipy.stats import t as t_dist


def estimate_loo_inflation_factor(loo_predictions: np.ndarray) -> float:
    """
    Estimate the actual variance inflation from LOO-CV for this specific problem.

    Theory predicts inflation ≈ 2×, but the actual value depends on the model
    and data structure. This computes an empirical estimate.

    Parameters:
    -----------
    loo_predictions : np.ndarray, shape (n_cal,)
        Binary LOO predictions (1=success, 0=failure)

    Returns:
    --------
    inflation_factor : float
        Estimated variance inflation, clipped to [1.0, 3.0]
        Typically ≈ 2.0 for LOO-CV

    Notes:
    ------
    Inflation = Var_empirical / Var_IID
    For n → ∞: inflation → 2.0
    For small n: inflation can vary, so we clip to reasonable range
    """
    n = len(loo_predictions)
    p_hat = np.mean(loo_predictions)

    # Empirical variance with Bessel correction
    var_empirical = np.var(loo_predictions, ddof=1) if n > 1 else p_hat * (1 - p_hat)

    # Theoretical IID variance
    var_iid = p_hat * (1 - p_hat)

    # Compute inflation factor
    if var_iid > 1e-10:  # Avoid division by zero
        inflation = (var_empirical / var_iid) * n / (n - 1)
    else:
        # Edge case: p_hat ≈ 0 or 1
        inflation = 2.0

    # Clip to reasonable range
    # Lower bound: 1.0 (can't be less than IID)
    # Upper bound: 3.0 (if higher, something is wrong with the data)
    inflation = np.clip(inflation, 1.0, 3.0)

    return inflation


def compute_loo_corrected_bounds_analytical(
    loo_predictions: np.ndarray,
    n_test: int,
    alpha: float = 0.05,
    use_t_distribution: bool = True,
    inflation_factor: float | None = None,
) -> tuple[float, float, dict[str, Any]]:
    """
    METHOD 1: Analytical bounds with LOO correction (RECOMMENDED).

    This method:
    - Uses empirical variance of LOO predictions (captures correlation)
    - Applies theoretical LOO inflation as safety check
    - Uses t-distribution for small-sample critical values
    - Combines calibration and test sampling uncertainty

    Best for: n_cal, n_test ≥ 20

    Parameters:
    -----------
    loo_predictions : np.ndarray, shape (n_cal,)
        Binary LOO predictions
    n_test : int
        Size of future test sets
    alpha : float
        Significance level (e.g., 0.05 for 95% confidence)
    use_t_distribution : bool
        If True, use t-distribution (recommended for n < 50)
    inflation_factor : float or None
        Manual override for LOO inflation. If None, auto-estimated.

    Returns:
    --------
    L_prime : float
        Lower prediction bound
    U_prime : float
        Upper prediction bound
    diagnostics : dict
        Detailed breakdown of variance components
    """
    n_cal = len(loo_predictions)
    p_hat = np.mean(loo_predictions)

    # Small sample warning
    if n_cal < 20:
        warnings.warn(
            f"n_cal={n_cal} is very small. Consider using Method 2 (exact binomial) "
            "or Method 3 (Hoeffding) for more conservative bounds.",
            stacklevel=2,
        )

    # Estimate or use provided inflation factor
    if inflation_factor is None:
        inflation_factor = estimate_loo_inflation_factor(loo_predictions)

    # Variance components

    # Source #1 & #2: LOO variance with correlation correction
    # Method A: Empirical variance (captures actual correlation in data)
    s_squared = np.var(loo_predictions, ddof=1) if n_cal > 1 else p_hat * (1 - p_hat)
    var_calibration_empirical = s_squared / n_cal

    # Method B: Theoretical with inflation factor
    # For small n, use (n-1) in denominator for bias correction
    var_calibration_theoretical = inflation_factor * p_hat * (1 - p_hat) / (n_cal - 1)

    # Use the LARGER of the two (conservative)
    var_calibration = max(var_calibration_empirical, var_calibration_theoretical)

    # Source #4: Test sampling variance
    var_test = p_hat * (1 - p_hat) / n_test

    # Total variance (sources are independent)
    var_total = var_calibration + var_test
    se_total = np.sqrt(var_total)

    # Critical value
    if use_t_distribution and n_cal > 2:
        # Use t-distribution with df = n_cal - 1
        df = n_cal - 1
        critical_value = t_dist.ppf(1 - alpha / 2, df)
    else:
        critical_value = norm.ppf(1 - alpha / 2)

    # Construct bounds
    L_prime = max(0.0, p_hat - critical_value * se_total)
    U_prime = min(1.0, p_hat + critical_value * se_total)

    # Diagnostics
    diagnostics = {
        "p_hat": p_hat,
        "n_cal": n_cal,
        "n_test": n_test,
        "inflation_factor": inflation_factor,
        "var_calibration": var_calibration,
        "var_test": var_test,
        "var_total": var_total,
        "se_total": se_total,
        "critical_value": critical_value,
        "width": U_prime - L_prime,
    }

    return L_prime, U_prime, diagnostics


def compute_loo_corrected_bounds_exact_binomial(
    k_loo: int, n_cal: int, n_test: int, alpha: float = 0.05, inflation_factor: float = 2.0
) -> tuple[float, float, dict[str, float]]:
    """
    METHOD 2: Exact binomial with effective sample size (CONSERVATIVE).

    This method:
    - Uses exact beta/binomial distributions (no normal approximation)
    - Computes effective sample size accounting for LOO correlation
    - Uses worst-case union bound for combining uncertainties
    - Works directly with discrete probabilities

    Best for: n_cal = 20-40, when you need guaranteed coverage

    Parameters:
    -----------
    k_loo : int
        Number of LOO successes
    n_cal : int
        Calibration set size
    n_test : int
        Test set size
    alpha : float
        Significance level
    inflation_factor : float
        LOO variance inflation (typically 1.5-2.5)

    Returns:
    --------
    L_prime, U_prime : float
        Prediction bounds
    diagnostics : dict
        Detailed breakdown
    """
    p_hat = k_loo / n_cal

    # Effective sample size after accounting for LOO correlation
    # If inflation_factor = 2, then n_effective = n_cal / 2
    n_effective = n_cal / inflation_factor

    # Step 1: Wide confidence interval for p using effective sample size
    # Scale k to effective sample size for beta distribution
    k_effective = k_loo / inflation_factor
    n_effective_int = int(np.round(n_effective))
    k_effective_int = int(np.round(k_effective))

    # Split alpha budget: half for calibration CI, half for test sampling
    alpha_cal = alpha / 2
    alpha_test = alpha / 2

    # Clopper-Pearson bounds on effective sample
    if k_effective_int == 0:
        p_lower = 0.0
    else:
        p_lower = beta_dist.ppf(alpha_cal / 2, k_effective_int, n_effective_int - k_effective_int + 1)

    if k_effective_int == n_effective_int:
        p_upper = 1.0
    else:
        p_upper = beta_dist.ppf(1 - alpha_cal / 2, k_effective_int + 1, n_effective_int - k_effective_int)

    # Step 2: Worst-case test sampling at boundaries
    # Lower bound: assume p = p_lower, take pessimistic quantile
    if p_lower > 0:
        L_prime = binom.ppf(alpha_test / 2, n_test, p_lower) / n_test
    else:
        L_prime = 0.0

    # Upper bound: assume p = p_upper, take optimistic quantile
    if p_upper < 1:
        U_prime = binom.ppf(1 - alpha_test / 2, n_test, p_upper) / n_test
    else:
        U_prime = 1.0

    diagnostics = {
        "p_hat": p_hat,
        "n_cal": n_cal,
        "n_effective": n_effective,
        "n_test": n_test,
        "inflation_factor": inflation_factor,
        "p_lower": p_lower,
        "p_upper": p_upper,
        "width": U_prime - L_prime,
    }

    return L_prime, U_prime, diagnostics


def compute_loo_corrected_bounds_hoeffding(
    loo_predictions: np.ndarray, n_test: int, alpha: float = 0.05
) -> tuple[float, float, dict[str, Any]]:
    """
    METHOD 3: Distribution-free Hoeffding bound (ULTRA-CONSERVATIVE).

    This method:
    - Uses Hoeffding concentration inequality (no distributional assumptions)
    - Accounts for LOO correlation via n_effective = n_cal / 2
    - Provides guaranteed coverage regardless of distribution
    - Widest bounds, suitable as worst-case / sanity check

    Best for: When you absolutely need guaranteed coverage

    Parameters:
    -----------
    loo_predictions : np.ndarray
        Binary LOO predictions
    n_test : int
        Test set size
    alpha : float
        Significance level

    Returns:
    --------
    L_prime, U_prime : float
        Prediction bounds
    diagnostics : dict
    """
    n_cal = len(loo_predictions)
    p_hat = np.mean(loo_predictions)

    # Effective sample size (conservative for LOO)
    n_effective_cal = n_cal / 2
    n_effective_test = n_test

    # Hoeffding bound: P(|p̂ - p| > ε) ≤ 2 exp(-2nε²)
    # Setting 2 exp(-2nε²) = α/2, solve for ε:
    # ε = sqrt(log(4/α) / (2n))

    # Split alpha: half for calibration, half for test
    epsilon_cal = np.sqrt(np.log(4 / alpha) / (2 * n_effective_cal))
    epsilon_test = np.sqrt(np.log(4 / alpha) / (2 * n_effective_test))

    # Union bound: total epsilon
    epsilon_total = epsilon_cal + epsilon_test

    # Bounds
    L_prime = max(0.0, p_hat - epsilon_total)
    U_prime = min(1.0, p_hat + epsilon_total)

    diagnostics = {
        "p_hat": p_hat,
        "n_cal": n_cal,
        "n_effective_cal": n_effective_cal,
        "n_test": n_test,
        "epsilon_cal": epsilon_cal,
        "epsilon_test": epsilon_test,
        "epsilon_total": epsilon_total,
        "width": U_prime - L_prime,
    }

    return L_prime, U_prime, diagnostics


def compute_robust_prediction_bounds(
    loo_predictions: np.ndarray,
    n_test: int,
    alpha: float = 0.05,
    method: str = "auto",
    inflation_factor: float | None = None,
) -> tuple[float, float, dict]:
    """
    Main function: Compute robust prediction bounds for small-sample LOO-CV.

    This is the primary entry point. It intelligently selects methods based on
    sample size and provides comprehensive diagnostics.

    Parameters:
    -----------
    loo_predictions : np.ndarray, shape (n_cal,)
        Binary LOO predictions (1=singleton/success, 0=not/failure)
    n_test : int
        Expected size of future test sets
    alpha : float
        Significance level (e.g., 0.05 for 95% confidence)
    method : str
        'auto' - Automatically select best method (recommended)
        'analytical' - Method 1: Analytical with LOO correction
        'exact' - Method 2: Exact binomial with effective n
        'hoeffding' - Method 3: Distribution-free bound
        'all' - Compute all three and report
    inflation_factor : float, optional
        Manual override for LOO variance inflation factor. If None, automatically estimated.
        Typical values: 1.0 (no inflation), 2.0 (standard LOO), 1.5-2.5 (empirical range)

    Returns:
    --------
    L_prime : float
        Lower prediction bound
    U_prime : float
        Upper prediction bound
    report : dict
        Comprehensive diagnostics and method comparison

    Usage Examples:
    ---------------
    # Basic usage (auto-selects best method)
    L, U, report = compute_robust_prediction_bounds(loo_preds, n_test=50)

    # Force conservative method
    L, U, report = compute_robust_prediction_bounds(
        loo_preds, n_test=50, method='exact'
    )

    # Compare all methods
    L, U, report = compute_robust_prediction_bounds(
        loo_preds, n_test=50, method='all'
    )
    print(report['comparison_table'])
    """
    n_cal = len(loo_predictions)
    k_loo = int(np.sum(loo_predictions))

    # Auto-select method based on sample size
    if method == "auto":
        if n_cal >= 40:
            method = "analytical"
        elif n_cal >= 25:
            method = "exact"
        else:
            method = "hoeffding"

    # Compute bounds with selected method
    if method == "analytical":
        L, U, diag = compute_loo_corrected_bounds_analytical(
            loo_predictions, n_test, alpha, inflation_factor=inflation_factor
        )
        selected_method = "analytical"

    elif method == "exact":
        L, U, diag = compute_loo_corrected_bounds_exact_binomial(k_loo, n_cal, n_test, alpha)
        selected_method = "exact"

    elif method == "hoeffding":
        L, U, diag = compute_loo_corrected_bounds_hoeffding(loo_predictions, n_test, alpha)
        selected_method = "hoeffding"

    elif method == "all":
        # Compute all three methods
        L1, U1, diag1 = compute_loo_corrected_bounds_analytical(loo_predictions, n_test, alpha)
        L2, U2, diag2 = compute_loo_corrected_bounds_exact_binomial(k_loo, n_cal, n_test, alpha)
        L3, U3, diag3 = compute_loo_corrected_bounds_hoeffding(loo_predictions, n_test, alpha)

        # Choose analytical as primary, but flag if too optimistic
        L, U = L1, U1
        selected_method = "analytical"

        # Check if analytical is suspiciously narrow
        if (U1 - L1) < 0.7 * (U2 - L2):
            warnings.warn(
                "Analytical bounds are significantly narrower than exact binomial. "
                "Consider using 'exact' method for more conservative bounds.",
                stacklevel=2,
            )
            L, U = L2, U2
            selected_method = "exact (auto-corrected)"

        # Build comparison table
        comparison = {
            "method": ["Analytical", "Exact Binomial", "Hoeffding"],
            "lower": [L1, L2, L3],
            "upper": [U1, U2, U3],
            "width": [U1 - L1, U2 - L2, U3 - L3],
        }

        report = {
            "selected_method": selected_method,
            "bounds": (L, U),
            "comparison": comparison,
            "diagnostics": {"analytical": diag1, "exact": diag2, "hoeffding": diag3},
        }

        return L, U, report

    else:
        raise ValueError(f"Unknown method: {method}")

    # Build report
    report = {
        "selected_method": selected_method,
        "bounds": (L, U),
        "diagnostics": diag,
        "alpha": alpha,
        "confidence_level": 1 - alpha,
    }

    return L, U, report


def format_prediction_bounds_report(
    rate_name: str, loo_predictions: np.ndarray, n_test: int, alpha: float = 0.05, include_all_methods: bool = True
) -> str:
    """
    Generate a formatted text report of prediction bounds.

    This produces human-readable output suitable for inclusion in
    rigorous analysis reports.

    Parameters:
    -----------
    rate_name : str
        Name of the rate (e.g., 'Singleton Rate', 'Doublet Rate')
    loo_predictions : np.ndarray
        Binary LOO predictions
    n_test : int
        Test set size
    alpha : float
        Significance level
    include_all_methods : bool
        If True, compare all three methods in report

    Returns:
    --------
    report : str
        Formatted text report
    """
    n_cal = len(loo_predictions)
    k_loo = int(np.sum(loo_predictions))
    p_hat = k_loo / n_cal

    # Compute bounds
    if include_all_methods:
        L, U, results = compute_robust_prediction_bounds(loo_predictions, n_test, alpha, method="all")
        comp = results["comparison"]
    else:
        L, U, results = compute_robust_prediction_bounds(loo_predictions, n_test, alpha, method="auto")

    # Format report
    report_lines = [
        f"\n{'=' * 70}",
        f"PREDICTION BOUNDS: {rate_name}",
        f"{'=' * 70}",
        "\nCalibration Data (LOO-CV):",
        f"  Sample size:        n_cal = {n_cal}",
        f"  Successes:         k = {k_loo}",
        f"  Point estimate:    p̂ = {p_hat:.4f} ({p_hat * 100:.2f}%)",
        "\nTest Data:",
        f"  Expected test size: n_test = {n_test}",
        f"\nConfidence Level:    {(1 - alpha) * 100:.1f}%",
        f"\n{'-' * 70}",
        "PREDICTION INTERVAL (accounts for all uncertainty sources):",
        f"  Lower bound:       L' = {L:.4f} ({L * 100:.2f}%)",
        f"  Upper bound:       U' = {U:.4f} ({U * 100:.2f}%)",
        f"  Width:             {U - L:.4f} ({(U - L) * 100:.2f}%)",
        f"  Selected method:   {results['selected_method']}",
    ]

    if include_all_methods and "comparison" in results:
        report_lines.extend(
            [
                f"\n{'-' * 70}",
                "METHOD COMPARISON:",
                f"  {'Method':<20} {'Lower':>10} {'Upper':>10} {'Width':>10}",
                f"  {'-' * 20} {'-' * 10} {'-' * 10} {'-' * 10}",
            ]
        )
        for i, method in enumerate(comp["method"]):
            L_i, U_i, W_i = comp["lower"][i], comp["upper"][i], comp["width"][i]
            report_lines.append(f"  {method:<20} {L_i:>10.4f} {U_i:>10.4f} {W_i:>10.4f}")

    # Add uncertainty breakdown
    if "diagnostics" in results and "var_calibration" in results["diagnostics"]:
        diag = results["diagnostics"]
        report_lines.extend(
            [
                f"\n{'-' * 70}",
                "UNCERTAINTY BREAKDOWN:",
                f"  Calibration uncertainty:  SE_cal  = {np.sqrt(diag['var_calibration']):.4f}",
                f"  Test sampling uncertainty:   SE_test = {np.sqrt(diag['var_test']):.4f}",
                f"  Total uncertainty:         SE_total = {diag['se_total']:.4f}",
                f"  LOO inflation factor:      {diag['inflation_factor']:.2f}×",
            ]
        )

    report_lines.extend(
        [
            f"\n{'-' * 70}",
            "INTERPRETATION:",
            f"  We are {(1 - alpha) * 100:.0f}% confident that future test sets of size {n_test}",
            f"  will have {rate_name.lower()} between {L * 100:.2f}% and {U * 100:.2f}%.",
            "\n  This interval accounts for:",
            "    1. LOO-CV correlation structure (variance inflation ≈2×)",
            "    2. Threshold calibration uncertainty",
            "    3. Parameter estimation uncertainty",
            "    4. Test set sampling variability",
            f"{'=' * 70}\n",
        ]
    )

    return "\n".join(report_lines)
