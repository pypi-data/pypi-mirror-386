from typing import Literal

import anndata as ad
import matplotlib.colors
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import seaborn as sns
from matplotlib.cm import ScalarMappable
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.stats import zscore

from dotools_py.logger import logger
from dotools_py.tl import rank_genes_groups
from dotools_py.get import mean_expr
from dotools_py.utils import convert_path, sanitize_anndata


def make_grid_spec(
    ax_or_figsize,
    *,
    nrows: int,
    ncols: int,
    wspace: float = None,
    hspace: float = None,
    width_ratios: float | list = None,
    height_ratios: float | list = None,
):
    # Taken from Scanpy
    kw = {"wspace": wspace, "hspace": hspace, "width_ratios": width_ratios, "height_ratios": height_ratios}

    if isinstance(ax_or_figsize, tuple):
        fig = plt.figure(figsize=ax_or_figsize)
        return fig, gridspec.GridSpec(nrows, ncols, **kw)
    else:
        ax = ax_or_figsize
        ax.axis("off")
        ax.set_frame_on(False)
        ax.set_xticks([])
        ax.set_yticks([])
        return ax.figure, ax.get_subplotspec().subgridspec(nrows, ncols, **kw)


def check_colornorm(vmin = None, vmax = None, vcenter = None, norm = None):
    from matplotlib.colors import Normalize

    try:
        from matplotlib.colors import TwoSlopeNorm as DivNorm
    except ImportError:
        # matplotlib<3.2
        from matplotlib.colors import DivergingNorm as DivNorm

    if norm is not None:
        if (vmin is not None) or (vmax is not None) or (vcenter is not None):
            raise ValueError("Passing both norm and vmin/vmax/vcenter is not allowed.")
    else:
        if vcenter is not None:
            norm = DivNorm(vmin=vmin, vmax=vmax, vcenter=vcenter)
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)

    return norm


def square_color(rgba: list) -> str:
    """Determine if the background is dark or clear and return black or white.

    :param rgba: list with rgba values
    :return: black or white
    """
    r, g, b = rgba[:3]  # ignore alpha
    # Convert from 0 to 1 float to 0–255 int
    r, g, b = [int(c * 255) for c in (r, g, b)]
    # Use brightness heuristic
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "black" if brightness > 128 else "white"


def small_squares(ax: plt.Axes, pos: list, color: list, size: float = 1, linewidth: float = 0.8, zorder: int = 20) -> None:
    """Add small squares.

    :param ax: matplotlib axis
    :param pos: list of positions
    :param color: list of colors
    :param size:  size of the square
    :param linewidth: linewith of the square
    :param zorder: location of the square
    :return: None
    """
    for idx, xy in enumerate(pos):
        x, y = xy
        margin = (1 - size) / 2
        rect = patches.Rectangle(
            (y + margin, x + margin),
            size,
            size,
            linewidth=linewidth,
            edgecolor=color[idx],
            facecolor="none",
            zorder=zorder,
        )
        if zorder == 0:
            rect.set_alpha(0)  # Hide square if they should be in the back, for the dotplot
        ax.add_patch(rect)
    return None


def heatmap(
    adata: ad.AnnData,
    group_by: str | list,
    features: str | list,
    groups_order: list = None,
    z_score: Literal["var", "group"] = None,  # x_axis is the group_by
    path: str = None,
    filename: str = "Heatmap.svg",
    layer: str = None,
    swap_axes: bool = True,
    cmap: str = "Reds",
    title: str = None,
    title_fontprop: dict = None,
    clustering_method: str = "complete",
    clustering_metric: str = "euclidean",
    cluster_x_axis: bool = False,
    cluster_y_axis: bool = False,
    axs: plt.Axes | None = None,
    figsize: tuple = (5, 6),
    linewidth: float = 0.1,
    ticks_fontdict: dict = None,
    xticks_rotation: int = None,
    yticks_rotation: int = None,
    vmin: float = 0.0,
    vcenter: float = None,
    vmax: float = None,
    legend_title: str = "LogMean(nUMI)\nin group",
    add_stats: bool = False,
    df_pvals: pd.DataFrame = None,
    stats_x_size: float = None,
    square_x_size: dict = None,
    test: Literal["wilcoxon", "t-test"] = "wilcoxon",
    correction_method: Literal["benjamini-hochberg", "bonferroni"] = "benjamini-hochberg",
    pval_cutoff: float = 0.05,
    log2fc_cutoff: float = 0.0,
    square: bool = True,
    show: bool = True,
    logcounts: bool = True,
    **kargs,
) -> dict | None:
    """Heatmap of the mean expression of genes across a groups.

    Generate a heatmap of showing the average nUMI for a set of genes in different groups. Differential gene
    expression analysis between the different groups can be performed.

    :param adata: annotated data matrix.
    :param group_by: obs column name with categorical values.
    :param features: continuous value in var_names or obs.
    :param groups_order: order for the categories in group_by
    :param z_score: apply z-score transformation.
    :param path: path to save the plot
    :param filename: name of the file.
    :param layer: layer to use.
    :param swap_axes: whether to swap the axes or not.
    :param cmap: colormap.
    :param title: title for the main plot.
    :param title_fontprop: font properties for the title (e.g., 'weight' and 'size').
    :param clustering_method: clustering method to use when hierarchically clustering the x and y-axis.
    :param clustering_metric: metric to use when hierarchically clustering the x and y-axis.
    :param cluster_x_axis: hierarchically clustering the x-axis.
    :param cluster_y_axis: hierarchically clustering the y-axis.
    :param axs: matplotlib axis.
    :param figsize: figure size.
    :param linewidth: linewidth for the border of cells.
    :param ticks_fontdict: font properties for the x and y ticks (e.g.,  'weight' and 'size').
    :param xticks_rotation: rotation of the x-ticks.
    :param yticks_rotation: rotations of the y-ticks.
    :param vmin: minimum value.
    :param vcenter: center value.
    :param vmax: maximum value.
    :param legend_title: title for the colorbar.
    :param add_stats: add statistical annotation. Will add a square with an '*' in the center if the expression is significantly different in a group with respect to the others.
    :param df_pvals: dataframe with the pvals. Should be gene x group or group x gene in case of swap_axes is False.
    :param stats_x_size: scaling factor to control the size of the asterisk.
    :param square_x_size: size and thickness of the square.
    :param test: test to use for test for significance.
    :param correction_method: multiple correction method to use.
    :param pval_cutoff: cutoff for the p-value.
    :param log2fc_cutoff: minimum cutoff for the log2FC.
    :param square: whether to make the cell square or not.
    :param show: if set to false return a dictionary with the axis.
    :param logcounts: whether the input is logcounts or not.
    :param kargs: additional arguments pass to `sns.heatmap() <https://seaborn.pydata.org/generated/seaborn.heatmap.html>`_.
    :return: Depending on ``show``, returns the plot if set to `True` or a dictionary with the axes.

    Example
    -------

    .. plot::
        :context: close-figs

        import dotools_py as do
        adata = do.dt.example_10x_processed()
        do.pl.heatmap(adata, 'annotation', ['CD4', 'CD79A'], add_stats=True)

    """
    # Checks
    sanitize_anndata(adata)
    features = [features] if isinstance(features, str) else features
    features = features if isinstance(features, list) else list(features)
    missing = [g for g in features if g not in adata.var_names]
    assert len(missing) == 0, f'{missing} features missing in the object'

    # Get Data for the Heatmap
    if all(item in list(adata.var_names) for item in features):
        if logcounts:
            df = mean_expr(
                adata, group_by=group_by, features=features, layer=layer, out_format="wide"
            )  # genes x groups (genes are the index)
        else:
            raise Exception("Not implemented, specified var_name value but logcounts is set to False")
    elif all(item in list(adata.obs.columns) for item in features):
        df = adata.obs[[group_by] + features].groupby(group_by).agg("mean")
    else:
        raise Exception("Provide features either var_names or obs.columns")

    # Hierarchical clustering
    new_index = (
        df.index[
            dendrogram(linkage(df.values, method=clustering_method, metric=clustering_metric), no_plot=True)["leaves"]
        ]
        if cluster_x_axis
        else features
    )

    new_columns = groups_order if groups_order is not None else list(df.columns)

    new_column = (
        df.columns[
            dendrogram(linkage(df.T.values, method=clustering_method, metric=clustering_metric), no_plot=True)["leaves"]
        ]
        if cluster_y_axis
        else new_columns
    )

    df = df.reindex(index=new_index, columns=new_column)

    # Layout
    if swap_axes:
        df = df.T

    # Compute Statistics
    annot_pvals = None
    if add_stats:
        if df_pvals is None:
            if all(item in list(adata.var_names) for item in features):
                rank_genes_groups(adata, groupby=group_by, method=test, tie_correct=True, corr_method=correction_method)
                table = sc.get.rank_genes_groups_df(
                    adata, group=None, pval_cutoff=pval_cutoff, log2fc_min=log2fc_cutoff
                )
                table_filt = table[table["names"].isin(features)]
            elif all(item in list(adata.obs.columns) for item in features):
                raise Exception('Not Implemented')
                # TODO Fix Bug
                tdf = adata.obs[[group_by] + features]
                tdata = ad.AnnData(tdf.iloc[:, 1:].values, obs=pd.DataFrame(tdf[group_by]), var=list(tdf.columns)[1:])
                tdata.var_names = tdata.var[0].copy()
                rank_genes_groups(
                    tdata,
                    groupby=group_by,
                    method=test,
                    tie_correct=True,
                    corr_method=correction_method,
                    logcounts=False,
                )
                table = sc.get.rank_genes_groups_df(
                    tdata, group=None, pval_cutoff=pval_cutoff, log2fc_min=log2fc_cutoff
                )
                table_filt = table[table["names"].isin(features)]

            # Dataframe with gene x groups with the pvals
            table_filt["group"] = table_filt["group"].str.replace("-", "_")  # Correction used in get_expr()
            df_pvals = pd.DataFrame([], index=df.index, columns=df.columns)
            for idx, row in table_filt.iterrows():
                if row["group"] in list(df.index):
                    df_pvals.loc[row["group"], row["names"]] = row["pvals_adj"]
                else:
                    df_pvals.loc[row["names"], row["group"]] = row["pvals_adj"]
            df_pvals[df_pvals.isna()] = 1
        else:
            if list(df.index)[0] in list(df_pvals.index):
                pass
            else:
                df_pvals = df_pvals.T
        # Replace pvals < 0.05 with an X
        annot_pvals = df_pvals.applymap(lambda x: "*" if x < pval_cutoff else "")

    # Data Transformation
    if z_score is not None:
        if z_score == "var":
            if features[0] in list(df.index):
                axis = 0
            else:
                axis = 1
        elif z_score == "group":
            if features[0] in list(df.index):
                axis = 1
            else:
                axis = 0
        else:
            raise Exception(f'{z_score} not a valid key for z_score, use "var" or "group"')

        df = df.apply(zscore, axis=axis, result_type="expand")  # z_score over the genes
        if cmap == "Reds":
            logger.warn(
                "Z-score set to True, but the cmap is Reds, setting to RdBu_r"
            )  # Make sure to use divergent colormap
            cmap = "RdBu_r"
        if legend_title == "LogMean(nUMI)\nin group":
            legend_title = "Z-score"
        vmin, vcenter, vmax = round(df.min().min() * 20) / 20, 0.0, None

    # ------ Arguments for the layout -------------
    width, height = figsize if figsize is not None else (None, None)
    legends_width_spacer = 0.7 / width
    mainplot_width = width - (1.5 + 0)
    if height is None:
        height = len(adata.obs[group_by].cat.categories) * 0.37
        width = len(features) * len(adata.obs[group_by].cat.categories) * 0.37 + 0.8

    min_figure_height = max([0.35, height])
    cbar_legend_height = min_figure_height * 0.08
    sig_legend = min_figure_height * 0.27
    spacer_height = min_figure_height * 0.3
    height_ratios = [
        height - sig_legend - cbar_legend_height - spacer_height,
        sig_legend,
        spacer_height,
        cbar_legend_height,
    ]

    textprops = {} if ticks_fontdict is None else ticks_fontdict
    textprops = {"weight": textprops.get("weight", "bold"), "size": textprops.get("size", 13)}
    tick_weight = textprops["weight"]
    tick_size = textprops["size"]

    title_fontprop = {} if title_fontprop is None else title_fontprop
    title_fontprop = {"weight": title_fontprop.get("weight", "bold"), "size": title_fontprop.get("size", 15)}
    # Parameters for colorbar
    vmin = 0.0 if vmin is None else vmin
    vmax = round(df.max().max() * 20) / 20 if vmax is None else vmax  # Normalise to round to 5 or 0
    colormap = plt.get_cmap(cmap)
    normalize = check_colornorm(vmin=vmin, vmax=vmax, vcenter=vcenter)
    mappable = ScalarMappable(norm=normalize, cmap=colormap)
    mean_flat = df.T.values.flatten()
    color = colormap(normalize(mean_flat))
    color = [square_color(c) for c in color]

    # Parameter for stats
    square_x_size = {} if square_x_size is None else square_x_size
    square_x_size = {"width": square_x_size.get("weight", 1), "size": square_x_size.get("size", 0.8)}
    # stats_x_size = max(np.sqrt(height * width), 14) if stats_x_size is None else stats_x_size
    stats_x_size = min(width / df.shape[1], height / df.shape[1]) * 10 if stats_x_size is None else min(width / df.shape[1], height / df.shape[1]) * stats_x_size

    # Save the axis
    return_ax_dict = {}
    # ---------------------------------------

    # Generate figure
    fig, gs = make_grid_spec(
        axs or (width, height), nrows=1, ncols=2, wspace=legends_width_spacer, width_ratios=[mainplot_width + 0, 1.5]
    )
    main_ax = fig.add_subplot(gs[0])
    legend_ax = fig.add_subplot(gs[1])

    fig, legend_gs = make_grid_spec(legend_ax, nrows=4, ncols=1, height_ratios=height_ratios)
    color_legend_ax = fig.add_subplot(legend_gs[3])
    if add_stats:
        sig_ax = fig.add_subplot(legend_gs[2])

    # Add Main Plot
    hm = sns.heatmap(
        data=df,
        cmap=cmap,
        ax=main_ax,
        linewidths=linewidth,
        cbar=False,
        annot_kws={"color": "black", "size": stats_x_size, "ha": "center", "va": "center", "fontfamily":'DejaVu Sans Mono'},
        annot=annot_pvals,
        fmt="s",
        square=square,
        **kargs,
    )

    # Add Legend
    matplotlib.colorbar.Colorbar(color_legend_ax, mappable=mappable, orientation="horizontal")
    color_legend_ax.set_title(legend_title, fontsize="small", fontweight="bold")
    color_legend_ax.xaxis.set_tick_params(labelsize="small")
    return_ax_dict["legend_ax"] = color_legend_ax

    # Significance Legend
    if add_stats:
        x, y = 0, 0.5
        sig_ax.scatter(x, y, s=500, facecolors="none", edgecolors="black", marker="s")
        sig_ax.text(x, y, "*", fontsize=18, ha="center", va="center", color="black", fontfamily='DejaVu Sans Mono')
        sig_ax.text(x + 0.03, y, "FDR < 0.05", fontsize=12, va="center", fontweight="bold")
        sig_ax.set_xlim(x - 0.02, x + 0.1)
        sig_ax.set_title("Significance", fontsize="small", fontweight="bold")
        plt.gca().set_aspect("equal")
        sig_ax.axis("off")  # Hide axes for clean display
        return_ax_dict["signifiance_ax"] = sig_ax

    # Modify layout from main plot
    hm.spines[["top", "right", "bottom", "left"]].set_visible(True)
    hm.set_xlabel("")
    hm.set_ylabel("")

    rotation_props_x, rotation_props_y = {"rotation": None}, {"rotation": None}
    rotation_props_x = (
        {"rotation": xticks_rotation, "va": "top", "ha": "right"} if xticks_rotation is not None else rotation_props_x
    )
    rotation_props_y = (
        {"rotation": yticks_rotation, "va": "top", "ha": "right"} if yticks_rotation is not None else rotation_props_y
    )
    hm.set_xticklabels(hm.get_xticklabels(), fontdict={"weight": tick_weight, "size": tick_size}, **rotation_props_x)
    hm.set_yticklabels(hm.get_yticklabels(), fontdict={"weight": tick_weight, "size": tick_size}, **rotation_props_y)
    hm.set_title(title, **title_fontprop)
    return_ax_dict["mainplot_ax"] = hm

    # Add Square around the Xs
    if add_stats:
        df_x = pd.DataFrame([], index=df.index, columns=df.columns)
        df_x[df_x.isna()] = "black"
        df_x = df.map(lambda x: square_color(colormap(normalize(x))))
        pos_rows, pos_cols = np.where(df_pvals < 0.05)
        pos = list(zip(pos_rows, pos_cols, strict=False))
        colors = [df_x.iloc[row, col] for row, col in pos]

        small_squares(
            hm,
            color=colors,
            pos=pos,
            size=square_x_size["size"],
            linewidth=square_x_size["width"],
        )

        # Now set colors manually on each annotation text base on the background
        for text, color in zip(hm.texts, df_x.values.flatten(), strict=False):
            text.set_color(color)

    if path is not None:
        plt.savefig(convert_path(path) / filename, bbox_inches="tight")
    if show:
        return plt.show()
    else:
        return return_ax_dict
