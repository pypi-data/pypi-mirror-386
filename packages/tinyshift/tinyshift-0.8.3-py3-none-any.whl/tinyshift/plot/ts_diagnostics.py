# Copyright (c) 2024-2025 Lucas Leão
# tinyshift - A small toolbox for mlops
# Licensed under the MIT License


from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller, acf, pacf
from tinyshift.series import trend_significance
import plotly.subplots as sp
import plotly.express as px
import plotly.graph_objs as go
import numpy as np
from typing import Union, List, Optional
import pandas as pd
from statsmodels.tsa.seasonal import MSTL
import scipy.stats
from statsmodels.stats.diagnostic import het_arch


def seasonal_decompose(
    X: Union[np.ndarray, List[float], pd.Series],
    periods: int | List[int],
    ljung_lags: int = 10,
    height: int = 1200,
    width: int = 1300,
    fig_type: Optional[str] = None,
):
    """
    Performs seasonal decomposition of a time series using MSTL and plots the components.

    This function uses the MSTL (Multiple Seasonal-Trend decomposition using Loess) method
    from statsmodels to separate a time series into trend, seasonal, and residual components
    for a specific identifier. It calculates trend significance and performs the Ljung-Box
    test for residuals, displaying a summary in the plot.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame containing the time series data with columns for time,
        target values, and identifiers.
    periods : int or list of int
        Period(s) of the seasonal components. For multiple seasonality, provide
        a list of integers (e.g., [7, 365] for weekly and yearly patterns).
    identifier : str
        Unique identifier value to filter the DataFrame for decomposition.
        Must exist in the `id_col` column.
    time_col : str, default='ds'
        Name of the column containing time/date values.
    target_col : str, default='y'
        Name of the column containing the target variable to decompose.
    id_col : str, default='unique_id'
        Name of the column containing unique identifiers.
    height : int, default=1200
        Figure height in pixels.
    width : int, default=1300
        Figure width in pixels.
    ljung_lags : int, default=10
        Number of lags to use in the Ljung-Box test for residual autocorrelation.
    fig_type : str, optional
        Plotly figure output type. Passed to `fig.show()`.
        E.g.: 'json', 'html', 'notebook'.

    Returns
    -------
    plotly.graph_objects.Figure or None
        Returns the Plotly Figure object if `fig_type` is `None` or the result
        of the `fig.show(fig_type)` call.

    Raises
    ------
    TypeError
        If input is not a pandas DataFrame.
    ValueError
        If identifier is None or not found in the DataFrame.

    Notes
    -----
    The resulting plot contains subplots for each decomposition component plus a summary:
    - Each component from the MSTL decomposition (trend, seasonal patterns, residuals)
    - Summary panel showing trend significance (R² and p-value) and Ljung-Box test
      results for residual autocorrelation analysis.

    The MSTL method is particularly useful for time series with multiple seasonal patterns
    and provides robust decomposition even in the presence of outliers.
    """

    def convert_to_dataframe(result: MSTL) -> pd.Series:
        """
        Reconstructs the original time series from its MSTL decomposition components.

        Parameters
        ----------
        result : MSTL
            Fitted MSTL object containing the decomposition components.

        Returns
        -------
        pandas.Series
            Reconstructed time series obtained by summing the trend, seasonal, and residual components.
        """
        df = pd.DataFrame()
        df["data"] = result.observed
        df["trend"] = result.trend
        if isinstance(result.seasonal, pd.Series):
            df["seasonal"] = result.seasonal
        else:
            for seasonal_col in result.seasonal.columns:
                df[seasonal_col] = result.seasonal[seasonal_col]
        df["resid"] = result.resid

        return df

    index = X.index if hasattr(X, "index") else list(range(len(X)))

    if not isinstance(X, pd.Series):
        X = pd.Series(np.asarray(X, dtype=np.float64))

    colors = px.colors.qualitative.T10
    num_colors = len(colors)

    result = MSTL(X, periods=periods).fit()
    result = convert_to_dataframe(result)
    r_squared, p_value = trend_significance(X)
    trend_results = f"R²={r_squared:.4f}, p={p_value:.4f}"
    ljung_box = acorr_ljungbox(result.resid, lags=[ljung_lags])

    ljung_stat, p_value = (
        ljung_box["lb_stat"].values[0],
        ljung_box["lb_pvalue"].values[0],
    )
    ljung_box = f"Stats={ljung_stat:.4f}, p={p_value:.4f}"

    summary = "<br>".join(
        [
            f"<b>{k}</b>: {v}"
            for k, v in {
                "Trend Significance": trend_results,
                "Ljung-Box Test": ljung_box,
            }.items()
        ]
    )

    subplot_titles = []
    for col in result.columns:
        subplot_titles.extend([f"{col.capitalize()}"])
    subplot_titles.extend(["Summary"])

    fig = sp.make_subplots(
        rows=len(subplot_titles),
        cols=1,
        subplot_titles=subplot_titles,
    )

    for i, col in enumerate(result.columns):
        color = colors[(i - 1) % num_colors]
        fig.add_trace(
            go.Scatter(
                x=index,
                y=getattr(result, col),
                mode="lines",
                hovertemplate=f"{col.capitalize()}: " + "%{y}<extra></extra>",
                line=dict(color=color),
            ),
            row=i + 1,
            col=1,
        )

    fig.add_trace(
        go.Scatter(x=[0], y=[0], text=[summary], mode="text", showlegend=False),
        row=subplot_titles.index("Summary") + 1,
        col=1,
    )

    fig.update_xaxes(visible=False, row=subplot_titles.index("Summary") + 1, col=1)
    fig.update_yaxes(visible=False, row=subplot_titles.index("Summary") + 1, col=1)

    color = colors[(i - 1) % num_colors]

    fig.update_layout(
        title="Seasonal Decomposition",
        height=height,
        width=width,
        showlegend=False,
        hovermode="x",
    )

    return fig.show(fig_type)


def stationarity_check(
    df: Union[pd.DataFrame, pd.Series],
    height: int = 1200,
    width: int = 1300,
    nlags: int = 30,
    fig_type: Optional[str] = None,
):
    """
    Creates interactive ACF and PACF plots with ADF test results for multiple series.

    This function generates a comprehensive diagnostic visualization to assess the
    stationarity and autocorrelation structure of multiple time series in a single panel.
    The plot includes the series itself, its autocorrelation function (ACF) and partial
    autocorrelation function (PACF), and a summary of the Augmented Dickey-Fuller (ADF)
    test results.

    Parameters
    ----------
    df : pandas.DataFrame, pandas.Series, or list
        Input data containing the time series. Can be:
        - DataFrame: Multiple columns will be analyzed
        - Series: Will be converted to single-column DataFrame
    height : int, default=1200
        Figure height in pixels.
    width : int, default=1300
        Figure width in pixels.
    nlags : int, default=30
        Number of lags to include in ACF and PACF calculations.
        Default is 30 or half the length of the series, whichever is smaller.
    fig_type : str, optional
        Plotly figure output type. Passed to `fig.show()`.
        E.g.: 'json', 'html', 'notebook'.

    Returns
    -------
    plotly.graph_objects.Figure or None
        Returns the Plotly Figure object if `fig_type` is `None` or the result
        of the `fig.show(fig_type)` call.

    Notes
    -----
    Confidence bands are shown on ACF and PACF plots at ±1.96/√N level.
    """
    nlags = min(nlags, (len(df) // 2) - 1)

    if isinstance(df, pd.Series):
        series_name = df.name if df.name is not None else "Value"
        df = df.to_frame(name=series_name)

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Input must be a pandas Series, pandas DataFrame, or a list (of lists)."
        )

    N = len(df.columns)
    colors = px.colors.qualitative.T10
    num_colors = len(colors)

    def create_acf_pacf_traces(X, nlags=30, color=None):
        """
        Helper function to create ACF and PACF traces with confidence intervals.
        """

        N = len(X)
        conf = 1.96 / np.sqrt(N)
        acf_vals = acf(X, nlags=nlags)
        pacf_vals = pacf(X, nlags=nlags, method="yw")

        acf_bar = go.Bar(
            x=list(range(len(acf_vals))),
            y=acf_vals,
            marker_color=color,
            name="ACF",
        )
        pacf_bar = go.Bar(
            x=list(range(len(pacf_vals))),
            y=pacf_vals,
            marker_color=color,
            name="PACF",
        )

        band_upper = go.Scatter(
            x=list(range(nlags + 1)),
            y=[conf] * (nlags + 1),
            mode="lines",
            line=dict(color="gray", dash="dash"),
            showlegend=False,
            name="Confidence Band",
        )
        band_lower = go.Scatter(
            x=list(range(nlags + 1)),
            y=[-conf] * (nlags + 1),
            mode="lines",
            line=dict(color="gray", dash="dash"),
            showlegend=False,
            name="Confidence Band",
        )

        return acf_bar, pacf_bar, band_upper, band_lower

    subplot_titles = []
    for var in df.columns:
        subplot_titles.extend([f"Series ({var})", f"ACF ({var})", f"PACF ({var})"])
    subplot_titles.extend(["ADF Results Summary", "", ""])

    fig = sp.make_subplots(rows=N + 1, cols=3, subplot_titles=subplot_titles)

    adf_results = {}

    for i, var in enumerate(df.columns, start=1):
        X = df[var].dropna()
        adf_stat, p_value = adfuller(X)[:2]
        adf_results[var] = f"ADF={adf_stat:.2f}, p={p_value:.4f}"
        color = colors[(i - 1) % num_colors]

        fig.add_trace(
            go.Scatter(
                x=X.index,
                y=X,
                mode="lines",
                name="Series",
                showlegend=False,
                line=dict(color=color),
            ),
            row=i,
            col=1,
        )

        acf_values, pacf_values, conf_up, conf_lo = create_acf_pacf_traces(
            X,
            color=color,
            nlags=nlags,
        )

        fig.add_trace(acf_values, row=i, col=2)
        fig.add_trace(pacf_values, row=i, col=3)
        fig.add_trace(conf_up, row=i, col=2)
        fig.add_trace(conf_lo, row=i, col=2)
        fig.add_trace(conf_up, row=i, col=3)
        fig.add_trace(conf_lo, row=i, col=3)

    adf_text = "<br>".join([f"<b>{k}</b>: {v}" for k, v in adf_results.items()])

    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            text=[adf_text],
            mode="text",
            showlegend=False,
            name="Summary",
            hoverinfo="skip",
        ),
        row=N + 1,
        col=1,
    )

    fig.update_layout(
        title="ACF/PACF with ADF Summary",
        height=height,
        width=width,
        showlegend=False,
    )

    for row in range(1, N + 1):
        fig.update_xaxes(title_text="Index", row=row, col=1)
        fig.update_yaxes(title_text="Value", row=row, col=1)
        fig.update_xaxes(title_text="Lag", row=row, col=2)
        fig.update_xaxes(title_text="Lag", row=row, col=3)
        fig.update_yaxes(title_text="ACF", row=row, col=2)
        fig.update_yaxes(title_text="PACF", row=row, col=3)

    fig.update_xaxes(visible=False, row=N + 1, col=1)
    fig.update_yaxes(visible=False, row=N + 1, col=1)

    return fig.show(fig_type)


def residual_check(
    df: Union[pd.DataFrame, pd.Series],
    height: int = 1200,
    width: int = 1300,
    nlags: int = 10,
    fig_type: Optional[str] = None,
):
    """
    Creates diagnostic plots for residual analysis including histogram, QQ-plot, and Ljung-Box test.

    This function generates a comprehensive residual diagnostic visualization to assess
    the distribution properties and autocorrelation structure of residuals from time series
    models. The plot includes the residual series itself, histogram, QQ-plot against normal
    distribution, and a summary of the Ljung-Box test results.

    Parameters
    ----------
    df : pandas.DataFrame, pandas.Series
        Input data containing the residual series. Can be:
        - DataFrame: Multiple columns will be analyzed as separate residual series
        - Series: Will be converted to single-column DataFrame
    height : int, default=1200
        Figure height in pixels.
    width : int, default=1300
        Figure width in pixels.
    nlags : int, default=10
        Number of lags to use in the Ljung-Box test for residual autocorrelation and ARCH test for heteroscedasticity.
        Default is set to 10 or 1/5th of the length of the series, whichever is smaller. (Rob J Hyndman rule of thumb for lag selection non-seasonal time series.)
    fig_type : str, optional
        Plotly figure output type. Passed to `fig.show()`.
        E.g.: 'json', 'html', 'notebook'.

    Returns
    -------
    plotly.graph_objects.Figure or None
        Returns the Plotly Figure object if `fig_type` is `None` or the result
        of the `fig.show(fig_type)` call.

    Notes
    -----
    Confidence bands are shown on ACF and PACF plots at ±1.96/√N level.
    """
    nlags = min(10, len(df) // 5)

    if isinstance(df, pd.Series):
        series_name = df.name if df.name is not None else "Value"
        df = df.to_frame(name=series_name)

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Input must be a pandas Series, pandas DataFrame, or a list (of lists)."
        )

    N = len(df.columns)
    colors = px.colors.qualitative.T10
    num_colors = len(colors)

    subplot_titles = []
    for var in df.columns:
        subplot_titles.extend(
            [f"Series ({var})", f"Histogram ({var})", f"QQ-Plot ({var})"]
        )
    subplot_titles.extend(["Ljung-Box Results Summary", "ARCH Results Summary", ""])

    fig = sp.make_subplots(rows=N + 1, cols=3, subplot_titles=subplot_titles)

    ljung_box_results = {}
    arch_results = {}

    for i, var in enumerate(df.columns, start=1):
        X = df[var].dropna()
        lb_stat, p_value = acorr_ljungbox(X, lags=[nlags], return_df=True).iloc[0]
        ljung_box_results[var] = f"LB={lb_stat:.2f}, p={p_value:.4f}"
        arch_stat, p_value = het_arch(X, nlags=nlags)[:2]
        arch_results[var] = f"ARCH={arch_stat:.2f}, p={p_value:.4f}"
        color = colors[(i - 1) % num_colors]

        fig.add_trace(
            go.Scatter(
                x=X.index,
                y=X,
                mode="lines",
                name="Series",
                showlegend=False,
                line=dict(color=color),
            ),
            row=i,
            col=1,
        )

        fig.add_trace(
            go.Histogram(
                x=X,
                marker_color=color,
                showlegend=False,
                opacity=0.7,
                name="Histogram",
            ),
            row=i,
            col=2,
        )

        (osm, osr), (slope, intercept, _) = scipy.stats.probplot(
            X, dist="norm", plot=None
        )

        qq_trace_points = go.Scatter(
            x=osm,
            y=osr,
            mode="markers",
            name="QQ-Plot",
            marker=dict(color="#1f77b4"),
            showlegend=False,
        )
        fig.add_trace(qq_trace_points, row=i, col=3)

        x_line = np.array([osm.min(), osm.max()])
        y_line = slope * x_line + intercept

        qq_trace_line = go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            name="Theoretical Line (Normal)",
            line=dict(color="red", dash="dash"),
            opacity=0.7,
            showlegend=False,
        )
        fig.add_trace(qq_trace_line, row=i, col=3)

    ljung_box_text = "<br>".join(
        [f"<b>{k}</b>: {v}" for k, v in ljung_box_results.items()]
    )
    arch_results_text = "<br>".join(
        [f"<b>{k}</b>: {v}" for k, v in arch_results.items()]
    )

    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            text=[ljung_box_text],
            mode="text",
            showlegend=False,
            name="Summary",
            hoverinfo="skip",
        ),
        row=N + 1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            text=[arch_results_text],
            mode="text",
            showlegend=False,
            name="Summary",
            hoverinfo="skip",
        ),
        row=N + 1,
        col=2,
    )

    for row in range(1, N + 1):
        fig.update_xaxes(title_text="Index", row=row, col=1)
        fig.update_yaxes(title_text="Value", row=row, col=1)
        fig.update_xaxes(title_text="Residual", row=row, col=2)
        fig.update_yaxes(title_text="Frequency", row=row, col=2)
        fig.update_xaxes(title_text="Theorical Quantiles", row=row, col=3)
        fig.update_yaxes(title_text="Ordered Values", row=row, col=3)

    fig.update_xaxes(visible=False, row=N + 1, col=1)
    fig.update_yaxes(visible=False, row=N + 1, col=1)
    fig.update_xaxes(visible=False, row=N + 1, col=2)
    fig.update_yaxes(visible=False, row=N + 1, col=2)

    fig.update_layout(
        title="Histogram/QQ-Plot with Ljung-Box Summary",
        height=height,
        width=width,
        showlegend=False,
    )

    return fig.show(fig_type)
