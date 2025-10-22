# Copyright (c) 2024-2025 Lucas Leão
# tinyshift - A small toolbox for mlops
# Licensed under the MIT License


from typing import Union, List, Tuple
import numpy as np
from scipy.signal import periodogram
from collections import Counter
import math
from .stats import trend_significance
from scipy import signal


def foreca(
    X: Union[np.ndarray, List[float]],
) -> float:
    """
    Calculate the Forecastable Component Analysis (ForeCA) omega index for a given signal.

    The omega index (ω) measures how forecastable a time series is, ranging from 0
    (completely noisy/unforecastable) to 1 (perfectly forecastable). It is based on
    the spectral entropy of the signal's power spectral density (PSD).

    Parameters
    ----------
    X : Union[np.ndarray, List[float]]
        Input 1D time series data for which to calculate the forecastability measure.
        The signal should be stationary for meaningful results.

    Returns
    -------
    float
        The omega forecastability index (ω), where:
        - ω ≈ 0: Signal is noise-like and not forecastable
        - ω ≈ 1: Signal has strong periodic components and is highly forecastable

    Notes
    -----
    The calculation involves:
    1. Computing the power spectral density (PSD) via periodogram
    2. Normalizing the PSD to sum to 1 (creating a probability distribution)
    3. Calculating the spectral entropy of this distribution
    4. Normalizing against maximum possible entropy
    5. Subtracting from 1 to get forecastability measure

    References
    ----------
    [1] Goerg (2013), "Forecastable Component Analysis" (JMLR)
    [2] Hyndman et al. (2015), "Large unusual observations in time series"
    [3] Manokhin (2025), "Mastering Modern Time Series Forecasting: The Complete Guide to
        Statistical, Machine Learning & Deep Learning Models in Python", Ch. 2.4.12
    """
    _, psd = periodogram(X)
    psd = psd / np.sum(psd)
    entropy = -np.sum(psd * np.log2(psd + 1e-12))
    max_entropy = np.log2(len(psd))
    omega = 1 - (entropy / max_entropy)
    return float(omega)


def adi_cv(
    X: Union[np.ndarray, List[float]],
) -> Tuple[float, float]:
    """
    Computes two key metrics for analyzing time series data: Average Demand Interval (ADI)
    and Coefficient of Variation (CV).

    1. Average Demand Interval (ADI): Indicates the average number of periods between nonzero values in a time series.
       - Higher ADI suggests more periods of zero or low values, indicating potential sparsity or infrequent activity.
       - ADI = n / n_nonzero, where n is the total number of periods and n_nonzero is the count of nonzero values.

    2. Coefficient of Variation (CV): The squared ratio of the standard deviation to the mean of the time series.
       - Provides a normalized measure of dispersion, allowing for comparison across different time series regardless of their scale.
       - Higher CV indicates greater variability relative to the mean.
       - CV = (std(X) / mean(X)) ** 2

    Parameters
    ----------
    X : array-like, shape (n_samples,)
        Time series data (e.g., demand, sales, or other metrics).

    Returns
    -------
    adi : float
        Average Demand Interval for the time series.
    cv : float
        Squared Coefficient of Variation for the time series.

    Notes
    -----
    - ADI thresholds:
        * Low ADI < 1.32 (frequent activity)
        * High ADI >= 1.32 (infrequent activity)
    - CV thresholds:
        * Low CV < 0.49 (low variability)
        * High CV >= 0.49 (high variability)
    - Classification of time series:
        * "Smooth":      Low ADI, Low CV — consistent activity, low variability, highly predictable.
        * "Intermittent":High ADI, Low CV — infrequent but regular activity, forecastable with specialized methods (e.g., Croston's, ADIDA, IMAPA).
        * "Erratic":     Low ADI, High CV — regular activity but high variability, high uncertainty.
        * "Lumpy":       High ADI, High CV — periods of inactivity followed by bursts, challenging to forecast.
    """
    X = np.asarray(X, dtype=np.float64)

    if X.ndim != 1:
        raise ValueError("Input data must be 1-dimensional")

    n = X.shape[0]
    n_nonzero = np.count_nonzero(X)
    adi = n / n_nonzero
    cv = (np.std(X) / np.mean(X)) ** 2

    return adi, cv


def sample_entropy(
    X: Union[np.ndarray, List[float]],
    m: int = 1,
    tolerance: float = None,
    detrend: bool = False,
) -> np.ndarray:
    """
    Compute the Sample Entropy (SampEn) of a 1D time series.

    Sample Entropy is a measure of complexity or irregularity in a time series.
    It quantifies the likelihood that similar patterns in the data will not be followed by additional similar patterns.

    Parameters
    ----------
    X : array-like, shape (n_samples,)
        1D time series data.
    m : int
        Length of sequences to be compared (embedding dimension).
    tolerance : float, optional (default=None)
        Tolerance for accepting matches. If None, it is set to 0.1 * std(X).
    Returns
    -------
    sampen : float
        The Sample Entropy of the time series. Returns np.nan if A or B is zero.
    References
    ----------
    - Richman, J. S., & Moorman, J. R. (2000). Physiological time-series analysis using approximate entropy and sample entropy. American Journal of Physiology-Heart and Circulatory Physiology, 278(6), H2039-H2049.
    - Lake, D. E., Richman, J. S., Griffin, M. P., & Moorman, J. R. (2002). Sample entropy analysis of neonatal heart rate variability. American Journal of Physiology-Regulatory, Integrative and Comparative Physiology, 283(3), R789-R797.
    Notes
    -----
    - SampEn is less biased than Approximate Entropy (ApEn) and does not count self-matches.
    - Higher SampEn values indicate more complexity and irregularity in the time series.
    - Employs Chebyshev distance (maximum norm) for pattern comparison
    - The function assumes the input time series is 1-dimensional.
    - The function uses the Chebyshev distance (maximum norm) for comparing sequences.
    - If either A or B is zero, SampEn is undefined and np.nan is returned.
    """

    X = np.asarray(X, dtype=np.float64)

    if X.ndim != 1:
        raise ValueError("Input data must be 1-dimensional")

    if detrend:
        r_squared, p_value = trend_significance(X)
        if r_squared > 0.3 and p_value < 0.05:
            X = signal.detrend(X, type="linear")
        else:
            X = signal.detrend(X, type="constant")

    n = X.shape[0]

    if tolerance is None:
        tolerance = 0.2 * np.std(X)

    if m < 1:
        raise ValueError("m must be a positive integer")

    if tolerance <= 0:
        raise ValueError("tolerance must be a positive float")

    if m > n:
        raise ValueError("m must be less or equal to length of the time series")

    Xm = np.array([X[i : i + m] for i in range(n - m)])

    Xm1 = np.array([X[i : i + m + 1] for i in range(n - m - 1)])

    def count_matches(X_templates, tol):
        """
        Count the number of matching template pairs within the given tolerance. Chebyshev distance is used.

        Parameters
        ----------
        X_templates : ndarray, shape (N, m) or (N, m+1)
            Array of template vectors.
        tol : float
            Tolerance for accepting matches.
        Returns
        -------
        count : int
            Number of matching template pairs.
        """

        count = 0
        N = len(X_templates)
        for i in range(N):
            diff = np.abs(X_templates[i] - X_templates[i + 1 :])
            max_diff = np.max(diff, axis=1)
            count += np.sum(max_diff < tol)
        return count

    B = count_matches(Xm, tolerance)

    A = count_matches(Xm1, tolerance)

    if A > 0 and B > 0:
        sampen = -np.log(A / B)
    else:
        sampen = np.nan

    return sampen


def stability_index(
    X: Union[np.ndarray, List[float]],
    m: int = 1,
    tolerance=None,
    detrend: bool = False,
) -> float:
    """
    Calculate the Stability Index based on Sample Entropy (SampEn).

    This function measures the temporal stability and regularity of a time series by
    inverting the Sample Entropy. It quantifies how consistent the values and patterns
    are over time, considering both magnitude and sequential relationships.

    The stability is computed as: 1 / exp(SampEn), where higher values indicate
    more stable and predictable behavior.

    Parameters
    ----------
    X : Union[np.ndarray, List[float]]
        The time series data (e.g., prices, returns, measurements).
    m : int, optional, default=1
        The embedding dimension (length of sequences to compare).
    tolerance : float, optional, default=None
        The similarity criterion for matching patterns. If None, defaults to 0.2 * std(X).
    detrend : bool, optional, default=False
        Whether to detrend the series before calculating entropy.

    Returns
    -------
    float
        The Stability Index, where:
        - Values close to 1: High stability/regularity (consistent patterns)
        - Values close to 0: Low stability/regularity (irregular/complex behavior)

    Notes
    -----
    - Uses Sample Entropy which considers actual value magnitudes and distances
    - Higher tolerance allows more variation in "similar" patterns
    - Complementary to ordinal-based measures like theoretical_limit()
    """
    hrate = sample_entropy(X, m=m, tolerance=tolerance, detrend=detrend)
    return 1 / np.exp(hrate)


def permutation_entropy(
    X: Union[np.ndarray, List[float]],
    m: int = 3,
    delay: int = 1,
    normalize=True,
):
    """
    Calculate the Permutation Entropy of a time series.

    Parameters
    ----------
        X : array-like, shape (n_samples,)
            Time series data (e.g., closing prices).
        m : int, optional (default=3)
            The embedding dimension (length of the pattern).
        delay : int, optional (default=1)
            The time delay (spacing between elements in the pattern).
        normalize : bool, optional (default=False)
            If True, normalize the entropy to the range [0, 1].

    Returns
    -------
    float
        The Permutation Entropy of the time series.

    Notes
    -----
    - The Permutation Entropy quantifies the complexity of a time series based on the order relations between values.
    - It is calculated by mapping the time series to a sequence of ordinal patterns and computing the
    Shannon entropy of the distribution of these patterns.
    - Higher values indicate more complexity and randomness in the time series.
    - The function preserves the length of the input series.
    """
    X = np.asarray(X, dtype=np.float64)

    if X.ndim != 1:
        raise ValueError("Input data must be 1-dimensional")
    if m < 2:
        raise ValueError("m must be at least 2")
    if delay < 1:
        raise ValueError("delay must be at least 1")
    if len(X) < (m - 1) * delay + 1:
        raise ValueError("Time series is too short for the given m and delay")

    N = X.shape[0] - delay * (m - 1)
    window_indices = [np.arange(i, i + delay * m, delay) for i in range(N)]
    X = np.argsort(X[window_indices], axis=1)
    patterns = Counter(map(tuple, X))
    probs = {k: v / sum(patterns.values()) for k, v in patterns.items()}
    probs = np.array(list(probs.values()))
    pe = -np.sum(probs * np.log2(probs))
    return pe / np.log2(math.factorial(m)) if normalize else pe


def theoretical_limit(
    X: Union[np.ndarray, List[float]],
    m: int = 3,
    delay: int = 1,
) -> float:
    """
    Calculates the theoretical upper limit of predictability (Πmax) for a time series based on ordinal patterns.

    This function computes the maximum achievable predictability by analyzing the structural
    complexity of ordinal patterns in the time series, independent of magnitude. It uses
    normalized Permutation Entropy: Πmax = 1 - PE_norm.

    The theoretical limit represents the upper bound of predictability that any forecasting
    method could achieve if it perfectly captured all ordinal patterns in the data, ignoring
    actual value magnitudes.

    Parameters
    ----------
    X : Union[np.ndarray, List[float]]
        The time series data.
    m : int, optional, default=3
        The embedding dimension (length of ordinal patterns to analyze).
    delay : int, optional, default=1
        The delay (spacing between elements in patterns).

    Returns
    -------
    float
        The theoretical predictability limit (Πmax) for the time series, ranging from 0 to 1:
        - 0: Completely random ordinal patterns (maximum complexity)
        - 1: Perfectly regular ordinal patterns (minimum complexity)

    Notes
    -----
    - This is a **theoretical upper bound** based solely on ordinal structure of the series
    - The measure ignores magnitudes, focusing only on directional patterns
    - Higher values indicate more regular/predictable ordinal behavior
    - Serves as a benchmark for comparing actual forecasting performance
    - Based on Permutation Entropy theory and information-theoretic limits

    References
    ----------
    [1] Bandt, C., & Pompe, B. (2002). Permutation entropy: a natural complexity
        measure for time series. Physical review letters, 88(17), 174102.
    [2] Song, C., Qu, Z., Blumm, N., & Barabási, A. L. (2010). Limits of
        predictability in human mobility. Science, 327(5968), 1018-1021.
    """
    pe = permutation_entropy(X, m=m, delay=delay, normalize=True)

    return 1 - pe
