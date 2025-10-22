# Copyright (c) 2024-2025 Lucas Leão
# tinyshift - A small toolbox for mlops
# Licensed under the MIT License


from typing import List, Any, Optional
import pandas as pd
import numpy as np
import pickle
from itertools import product
from sklearn.base import BaseEstimator, TransformerMixin
from .encoder import TransactionEncoder
from scipy.stats import hypergeom


class TransactionAnalyzer(BaseEstimator, TransformerMixin):
    """
    TransactionAnalyzer for association rule mining and transaction pattern analysis.

    This class provides tools for analyzing transactional data, particularly for
    market basket analysis and association rule mining. It encodes transaction data
    into a one-hot format and calculates various association metrics for measuring
    the strength and direction of relationships between items.

    The analyzer is designed to work with transactional data where each transaction
    is a list of items.

    The analyzer supports multiple association metrics including:
    - Lift
    - Zhang's metric
    - Conviction
    - Confidence
    - Bayesian Confidence
    - Yule's Q coefficient
    - Hypergeometric p-value

    Attributes:
        encoder_ (TransactionEncoder): Encoder for transaction data
        columns_ (List[str]): Column names after encoding
        transactions_ (pd.DataFrame): Encoded transactions dataframe
    """

    def __init__(self) -> None:
        """Initialize TransactionAnalyzer.

        Attributes:
            encoder (TransactionEncoder): Encoder for transaction data
            columns_ (List[str]): Column names after encoding
            transactions (pd.DataFrame): Encoded transactions dataframe
        """
        self.encoder_: Optional[TransactionEncoder] = None
        self.columns_: Optional[List[str]] = None
        self.transactions_: Optional[pd.DataFrame] = None

    def fit(self, transactions: List[List[Any]]) -> "TransactionAnalyzer":
        """
        Fit the encoder to transactions and create encoded dataframe.

        Parameters
        ----------
            transactions : List of transactions where each transaction is a list of items

        Returns
        -------
            self: Fitted TransactionAnalyzer instance

        Raises
        -------
            ValueError: If transactions is empty or invalid
        """
        self.encoder_ = TransactionEncoder()
        self.encoder_.fit(transactions)
        self.columns_ = self.encoder_.columns_
        self.transactions_ = pd.DataFrame(
            self.encoder_.transform(transactions), columns=self.columns_
        )
        return self

    def transform(self, transactions: List[List[Any]]) -> np.ndarray:
        """Transform transactions to one-hot encoding."""
        if self.encoder_ is None:
            raise ValueError("Analyzer must be fitted before transforming data")
        return self.encoder_.transform(transactions)

    def fit_transform(self, transactions: List[List[Any]]) -> np.ndarray:
        """Fit and transform transactions."""
        self.fit(transactions)
        return self.transform(transactions)

    def save(self, filename: str) -> None:
        """Save analyzer to file using pickle."""
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filename: str) -> "TransactionAnalyzer":
        """Load analyzer from file."""
        with open(filename, "rb") as f:
            return pickle.load(f)

    def _get_support(self, items: pd.Series) -> float:
        """Calculate support for an itemset."""
        return items.mean()

    def _get_counts(self, items: pd.Series) -> int:
        """
        Get counts needed for various association measures.
        """
        return items.sum()

    def _get_series(
        self, antecedent: str, consequent: str
    ) -> tuple[pd.Series, pd.Series]:
        """
        Retrieve the encoded series for antecedent and consequent items.

        This internal method validates and returns the one-hot encoded series
        for both antecedent and consequent items from the fitted transactions.
        It serves as a helper method for all association metric calculations.

        Parameters
        ----------
        antecedent : str
            The antecedent item name as it appears in the encoded columns
        consequent : str
            The consequent item name as it appears in the encoded columns

        Returns
        -------
        tuple[pd.Series, pd.Series]
            A tuple containing two pandas Series:
            - antecedent_series: Boolean series indicating presence of antecedent
            - consequent_series: Boolean series indicating presence of consequent

        Raises
        ------
        ValueError
            If the analyzer has not been fitted (transactions_ is None)
        KeyError
            If either antecedent or consequent item is not found in the
            encoded transaction columns
        """
        if self.transactions_ is None:
            raise ValueError("Analyzer must be fitted before calculating the metric")

        try:
            antecedent_series = self.transactions_[antecedent]
            consequent_series = self.transactions_[consequent]
        except KeyError as e:
            raise KeyError(f"Item not found in encoded transactions: {e}")

        return antecedent_series, consequent_series

    def lift(self, antecedent: str, consequent: str) -> float:
        """
        Calculate lift metric for association rules.

        Lift measures how much more often antecedent and consequent occur together
        than expected if they were statistically independent.

        - lift = 1: items are independent
        - lift > 1: positive correlation (higher is better)
        - lift < 1: negative correlation

        Parameters
        ----------
        antecedent : str
            The antecedent item
        consequent : str
            The consequent item

        Returns
        -------
        float
            Lift value (≥ 0)
        """
        antecedent_series, consequent_series = self._get_series(antecedent, consequent)

        supportA = self._get_support(antecedent_series)
        supportC = self._get_support(consequent_series)
        supportAC = self._get_support(
            np.logical_and(antecedent_series, consequent_series)
        )

        if supportA == 0 or supportC == 0:
            return 0.0

        return supportAC / (supportA * supportC)

    def confidence(self, antecedent: str, consequent: str) -> float:
        """
        Calculate confidence metric for association rules.

        Confidence measures the probability that consequent occurs given that antecedent occurs.
        Values range from 0 to 1, where higher values indicate stronger rules.

        Parameters
        ----------
            antecedent : The antecedent item in the association rule
            consequent : The consequent item in the association rule

        Returns
        ----------
            float: Confidence value between 0 and 1

        Raises
        ----------
            ValueError: If analyzer has not been fitted
            KeyError: If either antecedent or consequent item is not found in encoded transactions
        """
        antecedent_series, consequent_series = self._get_series(antecedent, consequent)

        supportA = self._get_support(antecedent_series)
        supportAC = self._get_support(
            np.logical_and(antecedent_series, consequent_series)
        )

        if supportA == 0:
            return 0.0

        return supportAC / supportA

    def bayesian_confidence(self, antecedent: str, consequent: str) -> float:
        """
        Calculate Bayesian confidence with beta prior for association rules.

        This method computes a Bayesian estimate of confidence using a Beta(1,1) prior
        (equivalent to a uniform prior), which provides a smoothed estimate that is
        particularly useful when dealing with small sample sizes or sparse data.

        The Bayesian confidence is calculated as:
            (nXY + α) / (nX + α + β)
        where α = 1 and β = 1 for a uniform prior, giving:
            (nXY + 1) / (nX + 2)

        This approach prevents extreme confidence values (0 or 1) when dealing with
        limited data and provides more robust estimates, especially for rare items.

        Parameters
        ----------
        antecedent : str
            The antecedent item in the association rule
        consequent : str
            The consequent item in the association rule

        Returns
        -------
        float
            Bayesian confidence estimate between 0 and 1

        Raises
        ------
        ValueError
            If analyzer has not been fitted
        KeyError
            If either antecedent or consequent item is not found in encoded transactions
        """
        antecedent_series, consequent_series = self._get_series(antecedent, consequent)
        nX = self._get_counts(antecedent_series)
        nXY = self._get_counts(np.logical_and(antecedent_series, consequent_series))

        alpha = nXY + 1
        beta = nX - nXY + 1

        return alpha / (alpha + beta)

    def conviction(self, antecedent: str, consequent: str) -> float:
        """
        Calculate conviction metric for association rules.

        Conviction measures the degree of implication of a rule.
        It represents how often the rule would be incorrect if the items were independent.

        - conviction = 1 : items are independent
        - conviction > 1 : positive correlation (higher is better)
        - conviction → ∞ : perfect implication

        Parameters
        ----------
            antecedent : The antecedent item in the association rule
            consequent : The consequent item in the association rule

        Returns
        ----------
            float : Conviction metric value between 1 and ∞

        Raises:
            ValueError: If analyzer has not been fitted
            KeyError: If either antecedent or consequent item is not found in encoded transactions
        """
        antecedent_series, consequent_series = self._get_series(antecedent, consequent)

        supportA = self._get_support(antecedent_series)
        supportC = self._get_support(consequent_series)
        supportAC = self._get_support(
            np.logical_and(antecedent_series, consequent_series)
        )

        if supportA == 0:
            return np.nan

        if supportC == 1 or supportAC == supportA * supportC:
            return 1.0

        confidence = supportAC / supportA
        denominator = 1 - confidence

        if denominator == 0:
            return np.inf

        return (1 - supportC) / denominator

    def zhang_metric(self, antecedent: str, consequent: str) -> float:
        """
        Calculate Zhang's metric for association rule mining.

        Zhang's metric measures the strength of association between two items.
        Values range from -1 to 1, where positive values indicate positive association.

        Parameters
        ----------
            antecedent : The antecedent item in the association rule
            consequent : The consequent item in the association rule

        Returns
        ----------
            float : Zhang's metric value between -1 and 1

        Raises:
            ValueError: If analyzer has not been fitted
            KeyError: If either antecedent or consequent item is not found in encoded transactions
        """
        antecedent_series, consequent_series = self._get_series(antecedent, consequent)

        supportA = self._get_support(antecedent_series)
        supportC = self._get_support(consequent_series)
        supportAC = self._get_support(
            np.logical_and(antecedent_series, consequent_series)
        )

        numerator = supportAC - supportA * supportC
        denominator = max(supportAC * (1 - supportA), supportA * (supportC - supportAC))

        return numerator / denominator if denominator != 0 else 0.0

    def hypergeom(self, antecedent: str, consequent: str):
        """
        Calculate the hypergeometric p-value for the association rule.

        The p-value represents the probability of observing at least as many
        co-occurrences of antecedent and consequent as were actually observed,
        assuming they are independent.

        A lower p-value indicates stronger evidence against the null hypothesis
        of independence.

        Parameters
        ----------
        antecedent : str
            The antecedent item
        consequent : str
            The consequent item

        Returns
        -------
        float
            Hypergeometric p-value between 0 and 1
        """
        antecedent_series, consequent_series = self._get_series(antecedent, consequent)

        nX = self._get_counts(antecedent_series)
        nY = self._get_counts(consequent_series)
        nXY = self._get_counts(np.logical_and(antecedent_series, consequent_series))

        return hypergeom.sf(nXY - 1, len(self.transactions_), nY, nX)

    def yules_q(self, antecedent: str, consequent: str) -> float:
        """
        Calculate Yule's Q coefficient for association rules.

        Yule's Q is a measure of association between two binary variables based on
        the odds ratio. It ranges from -1 (perfect negative association) to +1
        (perfect positive association), with 0 indicating no association.

        Parameters
        ----------
            antecedent : The antecedent item in the association rule
            consequent : The consequent item in the association rule

        Returns
        ----------
            float : Yule's Q coefficient between -1 and 1

        Raises:
            ValueError: If analyzer has not been fitted
            KeyError: If either antecedent or consequent item is not found
        """

        antecedent_series, consequent_series = self._get_series(antecedent, consequent)

        nX = self._get_counts(antecedent_series)
        nY = self._get_counts(consequent_series)
        nXY = self._get_counts(np.logical_and(antecedent_series, consequent_series))

        odds_ratio = (nXY * (len(self.transactions_) - nX - nY + nXY)) / (
            (nX - nXY) * (nY - nXY)
        )

        return (odds_ratio - 1) / (odds_ratio + 1)

    def correlation_matrix(
        self,
        row_items: List[str],
        column_items: List[str],
        metric: str = "lift",
    ) -> pd.DataFrame:
        """
        Create a correlation matrix between row and column items using the desirable metric.

        Parameters
        -----------
        row_items : List[str]
            List of items to use as rows in the correlation matrix
        column_items : List[str]
            List of items to use as columns in the correlation matrix

        Returns
        --------
        pd.DataFrame
            Correlation matrix with row_items as index, column_items as columns,
            and metric values as cells

        Raises
        -------
        ValueError
            If analyzer has not been fitted
        """
        if self.transactions_ is None:
            raise ValueError(
                "Analyzer must be fitted before creating correlation matrix"
            )

        metric_mapping = {
            "lift": self.lift,
            "zhang": self.zhang_metric,
            "conviction": self.conviction,
            "confidence": self.confidence,
            "bayesian_confidence": self.bayesian_confidence,
            "yules_q": self.yules_q,
            "hypergeom": self.hypergeom,
        }

        callable_function = metric_mapping.get(metric, None)

        if not callable_function:
            raise ValueError(
                f"Unknown metric: '{metric}'. Available metrics: {metric_mapping.keys()}"
            )

        pairs = list(product(row_items, column_items))

        metric_values = [callable_function(row, columns) for row, columns in pairs]

        index = pd.MultiIndex.from_tuples(pairs)

        metric = pd.DataFrame(metric_values, index=index).unstack()

        metric.columns = metric.columns.droplevel()

        return metric
