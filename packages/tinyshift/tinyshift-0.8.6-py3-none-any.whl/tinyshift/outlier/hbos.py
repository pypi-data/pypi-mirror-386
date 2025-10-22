# Copyright (c) 2024-2025 Lucas Leão
# tinyshift - A small toolbox for mlops
# Licensed under the MIT License


import numpy as np
import pandas as pd
from sklearn.utils import check_array
from collections import Counter
from .base import BaseHistogramModel
from typing import Union


class HBOS(BaseHistogramModel):
    """
    HBOS (Histogram-based Outlier Score) is an unsupervised outlier detection algorithm that
    uses histograms to model the distribution of features and compute outlier scores.

    References
    ----------
    Goldstein, Markus & Dengel, Andreas. (2012). Histogram-based Outlier Score (HBOS): A fast Unsupervised Anomaly Detection Algorithm.
    https://www.researchgate.net/publication/231614824_Histogram-based_Outlier_Score_HBOS_A_fast_Unsupervised_Anomaly_Detection_Algorithm

    Notes
    -----
    - Higher HBOS scores indicate more anomalous observations
    - Works best when features are approximately independent
    - Very efficient for high-dimensional data
    """

    def __init__(
        self,
        dynamic_bins: bool = False,
    ):
        """
        Parameters
        ----------
        dynamic_bins : bool, optional
            If True, uses dynamic binning based on percentiles to create bins with approximately equal number  of samples.
            This can improve density estimation for skewed distributions. Default is False.
        """
        self.dynamic_bins = dynamic_bins
        super().__init__()

    def fit(
        self,
        X: np.ndarray,
        nbins: Union[int, str] = "auto",
    ) -> "HBOS":
        """
        Fit the HBOS model according to the given training data.

        Parameters
        ----------
        X : np.ndarray
            Training data, where `n_samples` is the number of samples and
            `n_features` is the number of features.
        nbins : Union[int, str], optional
            The number of bins or binning strategy for discretization.
            Options:
                Integer:
                    - Exact number of bins to use for all continuous features
                String options:
                    - 'auto': Minimum of 'sturges' and 'fd' estimators
                    - 'fd' (Freedman Diaconis): Robust to outliers
                    - 'doane': Improved Sturges for non-normal data
                    - 'scott': Less robust but computationally efficient
                    - 'stone': Information-theoretic approach
                    - 'rice': Simple size-based estimator
                    - 'sturges': Optimal for Gaussian data
                    - 'sqrt': Square root of data size
            - Default is 'auto'. Set to an integer for fixed binning. Set 10 to replicate original paper.
        Returns
        -------
        self : HBOS
            Fitted estimator.

        Notes
        -----
        - If `X` is a pandas Series or DataFrame, the data types and column names are stored.
        - For categorical features, relative frequencies are computed.
        - For continuous features, the data is discretized into bins and densities are computed.
        - The decision scores are computed and stored in `self.decision_scores_`.
        """
        self._extract_feature_info(X)

        X = check_array(X)
        _, self.n_features = X.shape

        for i in range(self.n_features):
            nbins = self._check_bins(X[:, i], nbins)

            if isinstance(self.feature_dtypes[i], pd.CategoricalDtype):
                value_counts = Counter(X[:, i])
                total_values = sum(value_counts.values())
                relative_frequencies = {
                    value: (count + 1) / (total_values + len(value_counts))
                    for value, count in value_counts.items()
                }
                self.feature_distributions.append(relative_frequencies)
            elif self.dynamic_bins:
                percentiles = np.percentile(X[:, i], q=np.linspace(0, 100, nbins + 1))
                bin_edges = np.unique(percentiles)
                densities, _ = np.histogram(X[:, i], bins=bin_edges, density=True)
                self.feature_distributions.append([densities, bin_edges])
            else:
                densities, bin_edges = np.histogram(X[:, i], bins=nbins, density=True)
                self.feature_distributions.append([densities, bin_edges])

        self.decision_scores_ = self.decision_function(X)
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute the decision function for the input data.
        """

        self._check_columns(X)

        X = check_array(X)
        outlier_scores = np.zeros(shape=(X.shape[0], self.n_features))

        for i in range(self.n_features):
            outlier_scores[:, i] = self._compute_outlier_score(X, i)

        return np.sum(outlier_scores, axis=1).ravel()
