"""Collection of Plotly-based charts for reporting results of MS²Rescore."""

import warnings
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

import mokapot
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots
import pyteomics.auxiliary
from psm_utils.psm_list import PSMList


class _ECDF:
    """
    Return the Empirical CDF of an array as a step function.

    Parameters
    ----------
    x : array_like
        Observations
    """

    def __init__(self, x):
        # Get ECDF
        x = np.array(x, copy=True)
        x.sort()
        nobs = len(x)
        y = np.linspace(1.0 / nobs, 1, nobs)

        # Make into step function
        _x = np.asarray(x)
        _y = np.asarray(y)

        if _x.shape != _y.shape:
            msg = "x and y do not have the same shape"
            raise ValueError(msg)
        if len(_x.shape) != 1:
            msg = "x and y must be 1-dimensional"
            raise ValueError(msg)

        self.x = np.r_[-np.inf, _x]
        self.y = np.r_[0.0, _y]
        self.n = self.x.shape[0]

    def __call__(self, time):
        tind = np.searchsorted(self.x, time, side="right") - 1
        return self.y[tind]


def score_histogram(psms: Union[PSMList, pd.DataFrame]) -> go.Figure:
    """
    Plot histogram of scores for a single PSM dataset.

    Parameters
    ----------
    psms
        PSMs to plot, as :py:class:`psm_utils.PSMList` or :py:class:`pandas.DataFrame` generated
        with :py:meth:`psm_utils.PSMList.to_dataframe`.

    """
    if isinstance(psms, PSMList):
        psm_df = psms.to_dataframe()
    else:
        psm_df = psms

    is_decoy = psm_df["is_decoy"].map({True: "decoy", False: "target"})

    fig = px.histogram(
        psm_df,
        x="score",
        color=is_decoy,
        barmode="overlay",
        histnorm="",
        labels={"is_decoy": "PSM type", "False": "target", "True": "decoy"},
        opacity=0.5,
    )

    # Get score thresholds
    if all(psm_df["qvalue"]):
        score_threshold = (
            psm_df[psm_df["qvalue"] <= 0.01]
            .sort_values("qvalue", ascending=False)["qvalue"]
            .iloc[0]
        )
        fig.add_vline(x=score_threshold, line_dash="dash", line_color="black")

    return fig


def pp_plot(psms: Union[PSMList, pd.DataFrame]) -> go.Figure:
    """
    Generate PP plot of target and decoy score distributions.

    Parameters
    ----------
    psms
        PSMs to plot, as :py:class:`psm_utils.PSMList` or :py:class:`pandas.DataFrame` generated
        with :py:meth:`psm_utils.PSMList.to_dataframe`.

    """
    if isinstance(psms, PSMList):
        psm_df = psms.to_dataframe()
    else:
        psm_df = psms

    n_decoys = np.count_nonzero(psm_df["is_decoy"])
    n_targets = len(psm_df) - n_decoys
    pi_zero = n_decoys / n_targets
    if n_decoys == 0:
        raise ValueError("No decoy PSMs found in PSM file.")
    target_scores = psm_df["score"][~psm_df["is_decoy"]]
    decoy_scores = psm_df["score"][psm_df["is_decoy"]]
    if len(psm_df) > 1000:
        target_scores_quantiles = psm_df["score"][~psm_df["is_decoy"]].quantile(
            np.linspace(0, 1, 1000)
        )
    else:
        target_scores_quantiles = target_scores
    target_ecdf = _ECDF(target_scores)(target_scores_quantiles)
    decoy_ecdf = _ECDF(decoy_scores)(target_scores_quantiles)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=decoy_ecdf,
            y=target_ecdf,
            mode="markers",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, pi_zero],
            mode="lines",
            line=go.scatter.Line(color="red"),
            showlegend=True,
            name="pi0",
        )
    )
    fig.update_layout(
        xaxis_title="Fdp",
        yaxis_title="Ftp",
        showlegend=False,
    )
    return fig


def fdr_plot(
    psms: Union[PSMList, pd.DataFrame],
    fdr_thresholds: Optional[List[float]] = None,
    log: bool = True,
) -> go.Figure:
    """
    Plot number of identifications in function of FDR threshold.

    Parameters
    ----------
    psms
        PSMs to plot, as :py:class:`psm_utils.PSMList` or :py:class:`pandas.DataFrame` generated
        with :py:meth:`psm_utils.PSMList.to_dataframe`.
    fdr_thresholds
        List of FDR thresholds to draw as vertical lines.
    log
        Whether to plot the x-axis on a log scale. Defaults to ``True``.

    """
    if isinstance(psms, PSMList):
        psm_df = psms.to_dataframe()
    else:
        psm_df = psms

    df = (
        psm_df[~psm_df["is_decoy"]]
        .reset_index(drop=True)
        .sort_values("qvalue", ascending=True)
        .copy()
    )
    df["count"] = (~df["is_decoy"]).cumsum()
    fig = px.line(
        df,
        x="qvalue",
        y="count",
        log_x=log,
        labels={"count": "Number of identified target PSMs", "qvalue": "FDR threshold"},
    )
    if fdr_thresholds:
        for threshold in fdr_thresholds:
            fig.add_vline(x=threshold, line_dash="dash", line_color="red")
    return fig


def score_scatter_plot(
    before: mokapot.LinearConfidence,
    after: mokapot.LinearConfidence,
    level: str = "psms",
    indexer: str = "index",
    fdr_threshold: float = 0.01,
) -> go.Figure:
    """
    Plot PSM scores before and after rescoring.

    Parameters
    ----------
    before
        Mokapot linear confidence results before rescoring.
    after
        Mokapot linear confidence results after rescoring.
    level
        Level of confidence estimates to plot. Must be one of "psms", "peptides", or "proteins".
    indexer
        Column with index for each PSM, peptide, or protein to use for merging data frames.

    """
    if not before or not after:
        figure = go.Figure()
        figure.add_annotation(
            text="No data available for comparison.",
            showarrow=False,
        )
        return figure

    # Restructure data
    merge_columns = [indexer, "mokapot score", "mokapot q-value", "mokapot PEP"]
    ce_psms_targets = pd.merge(
        left=before.confidence_estimates[level],
        right=after.confidence_estimates[level][merge_columns],
        on=indexer,
        suffixes=(" before", " after"),
    )
    ce_psms_decoys = pd.merge(
        left=before.decoy_confidence_estimates[level],
        right=after.decoy_confidence_estimates[level][merge_columns],
        on=indexer,
        suffixes=(" before", " after"),
    )
    ce_psms_targets["PSM type"] = "target"
    ce_psms_decoys["PSM type"] = "decoy"
    ce_psms = pd.concat([ce_psms_targets, ce_psms_decoys], axis=0)

    # Get score thresholds
    try:
        score_threshold_before = (
            ce_psms[ce_psms["mokapot q-value before"] <= fdr_threshold]
            .sort_values("mokapot q-value before", ascending=False)["mokapot score before"]
            .iloc[0]
        )
    except IndexError:  # No PSMs below threshold
        score_threshold_before = None
    try:
        score_threshold_after = (
            ce_psms[ce_psms["mokapot q-value after"] <= fdr_threshold]
            .sort_values("mokapot q-value after", ascending=False)["mokapot score after"]
            .iloc[0]
        )
    except IndexError:  # No PSMs below threshold
        score_threshold_after = None

    # Plot
    fig = px.scatter(
        data_frame=ce_psms,
        x="mokapot score before",
        y="mokapot score after",
        color="PSM type",
        marginal_x="histogram",
        marginal_y="histogram",
        opacity=0.1,
        labels={
            "mokapot score before": "PSM score (before rescoring)",
            "mokapot score after": "PSM score (after rescoring)",
        },
    )
    # draw FDR thresholds
    if score_threshold_before:
        fig.add_vline(x=score_threshold_before, line_dash="dash", row=1, col=1)
        fig.add_vline(x=score_threshold_before, line_dash="dash", row=2, col=1)
    if score_threshold_after:
        fig.add_hline(y=score_threshold_after, line_dash="dash", row=1, col=1)
        fig.add_hline(y=score_threshold_after, line_dash="dash", row=1, col=2)

    return fig


def fdr_plot_comparison(
    before: mokapot.LinearConfidence,
    after: mokapot.LinearConfidence,
    level: str = "psms",
    indexer: str = "index",
) -> go.Figure:
    """
    Plot number of identifications in function of FDR threshold before/after rescoring.

    Parameters
    ----------
    before
        Mokapot linear confidence results before rescoring.
    after
        Mokapot linear confidence results after rescoring.
    level
        Level of confidence estimates to plot. Must be one of "psms", "peptides", or "proteins".
    indexer
        Column with index for each PSM, peptide, or protein to use for merging dataframes.

    """
    if not before or not after:
        figure = go.Figure()
        figure.add_annotation(
            text="No data available for comparison.",
            showarrow=False,
        )
        return figure

    # Prepare data
    ce_psms_targets_melted = (
        pd.merge(
            left=before.confidence_estimates[level],
            right=after.confidence_estimates[level][
                [indexer, "mokapot score", "mokapot q-value", "mokapot PEP"]
            ],
            on=indexer,
            suffixes=(" before", " after"),
        )
        .rename(
            columns={
                "mokapot q-value before": "before rescoring",
                "mokapot q-value after": "after rescoring",
            }
        )
        .melt(
            id_vars=["index", "peptide", "is_target"],
            value_vars=["before rescoring", "after rescoring"],
            var_name="before/after",
            value_name="q-value",
        )
    )

    # Plot
    fig = px.ecdf(
        data_frame=ce_psms_targets_melted,
        x="q-value",
        color="before/after",
        log_x=True,
        ecdfnorm=None,
        labels={
            "q-value": "FDR threshold",
            "before/after": "",
        },
        color_discrete_map={
            "before rescoring": "#316395",
            "after rescoring": "#319545",
        },
    )
    fig.add_vline(x=0.01, line_dash="dash", line_color="black")
    fig.update_layout(yaxis_title="Identified PSMs")
    return fig


def identification_overlap(
    before: mokapot.LinearConfidence,
    after: mokapot.LinearConfidence,
) -> go.Figure:
    """
    Plot stacked bar charts of removed, retained, and gained PSMs, peptides, and proteins.

    Parameters
    ----------
    before
        Mokapot linear confidence results before rescoring.
    after
        Mokapot linear confidence results after rescoring.

    """
    if not before or not after:
        figure = go.Figure()
        figure.add_annotation(
            text="No data available for comparison.",
            showarrow=False,
        )
        return figure

    levels = before.levels  # ["psms", "peptides", "proteins"] if all available
    indexers = ["index", "peptide", "mokapot protein group"]

    overlap_data = defaultdict(dict)
    for level, indexer in zip(levels, indexers):
        df_before = before.confidence_estimates[level]
        df_after = after.confidence_estimates[level]
        if df_before is None and df_after is None:
            continue

        set_before = set(df_before[df_before["mokapot q-value"] <= 0.01][indexer])
        set_after = set(df_after[df_after["mokapot q-value"] <= 0.01][indexer])

        overlap_data["removed"][level] = -len(set_before - set_after)
        overlap_data["retained"][level] = len(set_after.intersection(set_before))
        overlap_data["gained"][level] = len(set_after - set_before)

    colors = ["#953331", "#316395", "#319545"]
    fig = plotly.subplots.make_subplots(rows=3, cols=1)

    for i, level in enumerate(levels):
        for (item, data), color in zip(overlap_data.items(), colors):
            if level not in data:
                continue
            fig.add_trace(
                go.Bar(
                    y=["protein groups" if level == "proteins" else level],
                    x=[data[level]],
                    marker={"color": color},
                    orientation="h",
                    name=item,
                    showlegend=True if i == 0 else False,
                ),
                row=i + 1,
                col=1,
            )
    fig.update_layout(barmode="relative")

    return fig


def feature_weights(
    feature_weights: pd.DataFrame, color_discrete_map: Optional[Dict[str, str]] = None
) -> go.Figure:
    """
    Plot bar chart of feature weights.

    Parameters
    ----------
    feature_weights
        Data frame with columns ``feature``, ``feature_generator``, and ``weight``.
    color_discrete_map
        Mapping of feature generator names to colors for plotting.

    """
    bar_data = (
        feature_weights.groupby(["feature", "feature_generator"])
        .median(numeric_only=True)
        .abs()
        .sort_values("weight")
        .reset_index()
    )

    return px.bar(
        data_frame=bar_data,
        x="weight",
        y="feature",
        color="feature_generator",
        orientation="h",
        hover_name="feature",
        title="Absolute median weights by feature",
        labels={
            "weight": "Absolute median weight",
            "feature_generator": "Feature generator",
            "feature": "Feature",
        },
        color_discrete_map=color_discrete_map,
    )


def feature_weights_by_generator(
    feature_weights: pd.DataFrame, color_discrete_map: Optional[Dict[str, str]] = None
) -> go.Figure:
    """
    Plot bar chart of feature weights, summed by feature generator.

    Parameters
    ----------
    feature_weights
        Data frame with columns "feature", "feature_generator", and "weight".
    color_discrete_map
        Mapping of feature generator names to colors for plotting.

    """
    bar_data = (
        feature_weights.groupby(["feature", "feature_generator"])
        .median()
        .abs()
        .reset_index()
        .groupby("feature_generator")
        .sum(numeric_only=True)
        .reset_index()
        .sort_values("weight")
    )

    return px.bar(
        data_frame=bar_data,
        x="weight",
        y="feature_generator",
        color="feature_generator",
        orientation="h",
        hover_name="feature_generator",
        title="Absolute median weights, summed by feature generator",
        labels={
            "weight": "Absolute median weight",
            "feature_generator": "Feature generator",
            "feature": "Feature",
        },
        color_discrete_map=color_discrete_map,
    )


def ms2pip_correlation(
    features: pd.DataFrame,
    is_decoy: Union[pd.Series, np.ndarray],
    qvalue: Union[pd.Series, np.ndarray],
) -> go.Figure:
    """
    Plot MS²PIP correlation for target PSMs with q-value <= 0.01.

    Parameters
    ----------
    features
        Data frame with features. Must contain the column ``spec_pearson_norm``.
    is_decoy
        Boolean array indicating whether each PSM is a decoy.
    qvalue
        Array of q-values for each PSM.

    """
    data = features["spec_pearson_norm"][(qvalue < 0.01) & (~is_decoy)]
    fig = px.histogram(
        x=data,
        labels={"x": "Pearson correlation"},
    )
    # Draw vertical line at median
    fig.add_vline(
        x=data.median(),
        line_width=3,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Median: {data.median():.2f}",
        annotation_position="top left",
    )
    return fig


def calculate_feature_qvalues(
    features: pd.DataFrame,
    is_decoy: pd.Series,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate q-values and ECDF AUC for all rescoring features.

    Q-values are calculated for each feature as if it was directly used PSM score. For each q-value
    distribution, the ECDF AUC is calculated as a measure of overall individual performance of the
    feature.

    As it is not known whether higher or lower values are better for each feature, q-values are
    calculated for both the original and reversed scores. The q-values and ECDF AUC are returned
    for the calculation with the highest ECDF AUC.

    Parameters
    ----------
    features
        Data frame with features. Must contain the column ``spec_pearson_norm``.
    is_decoy
        Boolean array indicating whether each PSM is a decoy.

    Returns
    -------
    feature_qvalues
        Wide-form data frame with q-values for each feature.
    feature_ecdf_auc
        Long-form data frame with ECDF AUC for each feature.

    """
    feature_qvalues = dict()
    feature_ecdf_auc = dict()
    for fname in features:
        # Calculate q-values for reversed and non-reversed scores
        q_values = []
        for reverse in [False, True]:
            with warnings.catch_warnings():  # Ignore divide by zero warning
                warnings.simplefilter("ignore", category=RuntimeWarning)
                q_values.append(
                    pyteomics.auxiliary.qvalues(
                        features,
                        key=fname,
                        is_decoy=is_decoy,
                        remove_decoy=True,
                        reverse=reverse,
                        full_output=False,
                    )["q"]
                )

        # Calculate ECDF AUC as measure of overall individual performance of feature
        ecdf_aucs = [np.trapz(y=np.max(q) - np.sort(q)) for q in q_values]

        # Select and save q-value calculation with best AUC (score reversed or not)
        idx_best = np.argmax(ecdf_aucs)
        feature_qvalues[fname] = q_values[idx_best]
        feature_ecdf_auc[fname] = ecdf_aucs[idx_best]

    # Restructure as data frames
    feature_qvalues = pd.DataFrame(feature_qvalues)
    feature_ecdf_auc = (
        pd.DataFrame([feature_ecdf_auc])
        .transpose()
        .reset_index()
        .rename(columns={"index": "feature", 0: "ecdf_auc"})
    )

    return feature_qvalues, feature_ecdf_auc


def feature_ecdf_auc_bar(
    feature_ecdf_auc: pd.DataFrame, color_discrete_map: Optional[Dict[str, str]] = None
) -> go.Figure:
    """
    Plot bar chart of feature q-value ECDF AUCs.

    Parameters
    ----------
    feature_ecdf_auc
        Data frame with columns ``feature``, ``feature_generator``, and ``ecdf_auc``.
    color_discrete_map
        Mapping of feature generator names to colors for plotting.

    """
    return px.bar(
        data_frame=feature_ecdf_auc.sort_values("ecdf_auc", ascending=True),
        x="ecdf_auc",
        y="feature",
        color="feature_generator",
        orientation="h",
        hover_name="feature",
        labels={
            "ecdf_auc": "Q-value ECDF AUC",
            "feature_generator": "Feature generator",
            "feature": "Feature",
        },
        color_discrete_map=color_discrete_map,
    )
