from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize, is_color_like

from .. import logging as logg
from .._settings import settings
from .._utils import _doc_params
from ._baseplot_class import BasePlot, _VarNames, doc_common_groupby_plot_args
from ._docs import doc_common_plot_args, doc_show_save_ax, doc_vboundnorm
from ._utils import _AxesSubplot, check_colornorm, make_grid_spec, savefig_or_show

if TYPE_CHECKING:
    from collections.abc import (
        Mapping,  # Special
        Sequence,  # ABCs
    )

    from anndata import AnnData


@_doc_params(common_plot_args=doc_common_plot_args)
class StackedViolin(BasePlot):
    """\
    Stacked violin plots.

    Makes a compact image composed of individual violin plots
    (from :func:`~seaborn.violinplot`) stacked on top of each other.
    Useful to visualize gene expression per cluster.

    Wraps :func:`seaborn.violinplot` for :class:`~anndata.AnnData`.

    Parameters
    ----------
    {common_plot_args}
    title
        Title for the figure
    stripplot
        Add a stripplot on top of the violin plot.
        See :func:`~seaborn.stripplot`.
    jitter
        Add jitter to the stripplot (only when stripplot is True)
        See :func:`~seaborn.stripplot`.
    size
        Size of the jitter points.
    order
        Order in which to show the categories. Note: if `dendrogram=True`
        the categories order will be given by the dendrogram and `order`
        will be ignored.
    scale
        The method used to scale the width of each violin.
        If 'width' (the default), each violin will have the same width.
        If 'area', each violin will have the same area.
        If 'count', a violin’s width corresponds to the number of observations.
    row_palette
        The row palette determines the colors to use for the stacked violins.
        The value should be a valid seaborn or matplotlib palette name
        (see :func:`~seaborn.color_palette`).
        Alternatively, a single color name or hex value can be passed,
        e.g. `'red'` or `'#cc33ff'`.
    standard_scale
        Whether or not to standardize a dimension between 0 and 1,
        meaning for each variable or observation,
        subtract the minimum and divide each by its maximum.
    swap_axes
         By default, the x axis contains `var_names` (e.g. genes) and the y axis
         the `groupby` categories. By setting `swap_axes` then x are the `groupby`
         categories and y the `var_names`. When swapping
         axes var_group_positions are no longer used
    kwds
        Are passed to :func:`~seaborn.violinplot`.


    See also
    --------
    :func:`~scanpy.pl.stacked_violin`: simpler way to call StackedViolin but with less
        options.
    :func:`~scanpy.pl.violin` and :func:`~scanpy.pl.rank_genes_groups_stacked_violin`:
        to plot marker genes identified using :func:`~scanpy.tl.rank_genes_groups`

    Examples
    -------

    >>> import scanpy as sc
    >>> adata = sc.datasets.pbmc68k_reduced()
    >>> markers = ['C1QA', 'PSAP', 'CD79A', 'CD79B', 'CST3', 'LYZ']
    >>> sc.pl.StackedViolin(adata, markers, groupby='bulk_labels', dendrogram=True)  # doctest: +ELLIPSIS
    <scanpy.plotting._stacked_violin.StackedViolin object at 0x...>

    Using var_names as dict:

    >>> markers = {{'T-cell': 'CD3D', 'B-cell': 'CD79A', 'myeloid': 'CST3'}}
    >>> sc.pl.StackedViolin(adata, markers, groupby='bulk_labels', dendrogram=True)  # doctest: +ELLIPSIS
    <scanpy.plotting._stacked_violin.StackedViolin object at 0x...>
    """

    DEFAULT_SAVE_PREFIX = "stacked_violin_"
    DEFAULT_COLOR_LEGEND_TITLE = "Median expression\nin group"

    DEFAULT_COLORMAP = "Blues"
    DEFAULT_STRIPPLOT = False
    DEFAULT_JITTER = False
    DEFAULT_JITTER_SIZE = 1
    DEFAULT_LINE_WIDTH = 0.2
    DEFAULT_ROW_PALETTE = None
    DEFAULT_SCALE = "width"
    DEFAULT_PLOT_YTICKLABELS = False
    DEFAULT_YLIM = None
    DEFAULT_PLOT_X_PADDING = 0.5  # a unit is the distance between two x-axis ticks
    DEFAULT_PLOT_Y_PADDING = 0.5  # a unit is the distance between two y-axis ticks

    # set by default the violin plot cut=0 to limit the extend
    # of the violin plot as this produces better plots that wont extend
    # to negative values for example. From seaborn.violin documentation:
    #
    # cut: Distance, in units of bandwidth size, to extend the density past
    # the extreme datapoints. Set to 0 to limit the violin range within
    # the range of the observed data (i.e., to have the same effect as
    # trim=True in ggplot.
    DEFAULT_CUT = 0

    # inner{“box”, “quartile”, “point”, “stick”, None} (Default seaborn: box)
    # Representation of the datapoints in the violin interior. If box, draw a
    # miniature boxplot. If quartiles, draw the quartiles of the distribution.
    # If point or stick, show each underlying datapoint. Using
    # None will draw unadorned violins.
    DEFAULT_INNER = None

    def __init__(
        self,
        adata: AnnData,
        var_names: _VarNames | Mapping[str, _VarNames],
        groupby: str | Sequence[str],
        use_raw: bool | None = None,
        log: bool = False,
        num_categories: int = 7,
        categories_order: Sequence[str] | None = None,
        title: str | None = None,
        figsize: tuple[float, float] | None = None,
        gene_symbols: str | None = None,
        var_group_positions: Sequence[tuple[int, int]] | None = None,
        var_group_labels: Sequence[str] | None = None,
        var_group_rotation: float | None = None,
        layer: str | None = None,
        standard_scale: Literal["var", "group"] = None,
        ax: _AxesSubplot | None = None,
        vmin: float | None = None,
        vmax: float | None = None,
        vcenter: float | None = None,
        norm: Normalize | None = None,
        **kwds,
    ):
        BasePlot.__init__(
            self,
            adata,
            var_names,
            groupby,
            use_raw=use_raw,
            log=log,
            num_categories=num_categories,
            categories_order=categories_order,
            title=title,
            figsize=figsize,
            gene_symbols=gene_symbols,
            var_group_positions=var_group_positions,
            var_group_labels=var_group_labels,
            var_group_rotation=var_group_rotation,
            layer=layer,
            ax=ax,
            vmin=vmin,
            vmax=vmax,
            vcenter=vcenter,
            norm=norm,
            **kwds,
        )

        if standard_scale == "obs":
            self.obs_tidy = self.obs_tidy.sub(self.obs_tidy.min(1), axis=0)
            self.obs_tidy = self.obs_tidy.div(self.obs_tidy.max(1), axis=0).fillna(0)
        elif standard_scale == "var":
            self.obs_tidy -= self.obs_tidy.min(0)
            self.obs_tidy = (self.obs_tidy / self.obs_tidy.max(0)).fillna(0)
        elif standard_scale is None:
            pass
        else:
            logg.warning("Unknown type for standard_scale, ignored")

        # Set default style parameters
        self.cmap = self.DEFAULT_COLORMAP
        self.row_palette = self.DEFAULT_ROW_PALETTE
        self.stripplot = self.DEFAULT_STRIPPLOT
        self.jitter = self.DEFAULT_JITTER
        self.jitter_size = self.DEFAULT_JITTER_SIZE
        self.plot_yticklabels = self.DEFAULT_PLOT_YTICKLABELS
        self.ylim = self.DEFAULT_YLIM
        self.plot_x_padding = self.DEFAULT_PLOT_X_PADDING
        self.plot_y_padding = self.DEFAULT_PLOT_Y_PADDING

        self.kwds.setdefault("cut", self.DEFAULT_CUT)
        self.kwds.setdefault("inner", self.DEFAULT_INNER)
        self.kwds.setdefault("linewidth", self.DEFAULT_LINE_WIDTH)
        self.kwds.setdefault("scale", self.DEFAULT_SCALE)

    def style(
        self,
        cmap: str | None = DEFAULT_COLORMAP,
        stripplot: bool | None = DEFAULT_STRIPPLOT,
        jitter: float | bool | None = DEFAULT_JITTER,
        jitter_size: int | None = DEFAULT_JITTER_SIZE,
        linewidth: float | None = DEFAULT_LINE_WIDTH,
        row_palette: str | None = DEFAULT_ROW_PALETTE,
        scale: Literal["area", "count", "width"] | None = DEFAULT_SCALE,
        yticklabels: bool | None = DEFAULT_PLOT_YTICKLABELS,
        ylim: tuple[float, float] | None = DEFAULT_YLIM,
        x_padding: float | None = DEFAULT_PLOT_X_PADDING,
        y_padding: float | None = DEFAULT_PLOT_Y_PADDING,
    ):
        r"""\
        Modifies plot visual parameters

        Parameters
        ----------
        cmap
            String denoting matplotlib color map.
        stripplot
            Add a stripplot on top of the violin plot.
            See :func:`~seaborn.stripplot`.
        jitter
            Add jitter to the stripplot (only when stripplot is True)
            See :func:`~seaborn.stripplot`.
        jitter_size
            Size of the jitter points.
        linewidth
            linewidth for the violin plots.
        row_palette
            The row palette determines the colors to use for the stacked violins.
            The value should be a valid seaborn or matplotlib palette name
            (see :func:`~seaborn.color_palette`).
            Alternatively, a single color name or hex value can be passed,
            e.g. `'red'` or `'#cc33ff'`.
        scale
            The method used to scale the width of each violin.
            If 'width' (the default), each violin will have the same width.
            If 'area', each violin will have the same area.
            If 'count', a violin’s width corresponds to the number of observations.
        yticklabels
            Set to true to view the y tick labels.
        ylim
            minimum and maximum values for the y-axis. If set. All rows will have
            the same y-axis range. Example: ylim=(0, 5)
        x_padding
            Space between the plot left/right borders and the violins. A unit
            is the distance between the x ticks.
        y_padding
            Space between the plot top/bottom borders and the violins. A unit is
            the distance between the y ticks.

        Returns
        -------
        :class:`~scanpy.pl.StackedViolin`

        Examples
        -------
        >>> import scanpy as sc
        >>> adata = sc.datasets.pbmc68k_reduced()
        >>> markers = ['C1QA', 'PSAP', 'CD79A', 'CD79B', 'CST3', 'LYZ']

        Change color map and turn off edges

        >>> sc.pl.StackedViolin(adata, markers, groupby='bulk_labels') \
        ...     .style(row_palette='Blues', linewidth=0).show()
        """

        # modify only values that had changed
        if cmap != self.cmap:
            self.cmap = cmap
        if row_palette != self.row_palette:
            self.row_palette = row_palette
            self.kwds["color"] = self.row_palette
        if stripplot != self.stripplot:
            self.stripplot = stripplot
        if jitter != self.jitter:
            self.jitter = jitter
        if jitter_size != self.jitter_size:
            self.jitter_size = jitter_size
        if yticklabels != self.plot_yticklabels:
            self.plot_yticklabels = yticklabels
            if self.plot_yticklabels:
                # space needs to be added to avoid overlapping
                # of labels and legend or dendrogram/totals.
                self.wspace = 0.3
            else:
                self.wspace = StackedViolin.DEFAULT_WSPACE
        if ylim != self.ylim:
            self.ylim = ylim
        if x_padding != self.plot_x_padding:
            self.plot_x_padding = x_padding
        if y_padding != self.plot_y_padding:
            self.plot_y_padding = y_padding
        if linewidth != self.kwds["linewidth"] and linewidth != self.DEFAULT_LINE_WIDTH:
            self.kwds["linewidth"] = linewidth
        if scale != self.kwds["scale"] and scale != self.DEFAULT_SCALE:
            self.kwds["scale"] = scale

        return self

    def _mainplot(self, ax):
        # to make the stacked violin plots, the
        # `ax` is subdivided horizontally and in each horizontal sub ax
        # a seaborn violin plot is added.

        # work on a copy of the dataframes. This is to avoid changes
        # on the original data frames after repetitive calls to the
        # StackedViolin object, for example once with swap_axes and other without
        _matrix = self.obs_tidy.copy()

        if self.var_names_idx_order is not None:
            _matrix = _matrix.iloc[:, self.var_names_idx_order]

        if self.categories_order is not None:
            _matrix.index = _matrix.index.reorder_categories(
                self.categories_order, ordered=True
            )

        # get mean values for color and transform to color values
        # using colormap
        _color_df = _matrix.groupby(level=0).median()
        if self.are_axes_swapped:
            _color_df = _color_df.T

        cmap = plt.get_cmap(self.kwds.get("cmap", self.cmap))
        if "cmap" in self.kwds:
            del self.kwds["cmap"]
        normalize = check_colornorm(
            self.vboundnorm.vmin,
            self.vboundnorm.vmax,
            self.vboundnorm.vcenter,
            self.vboundnorm.norm,
        )
        colormap_array = cmap(normalize(_color_df.values))
        x_spacer_size = self.plot_x_padding
        y_spacer_size = self.plot_y_padding
        self._make_rows_of_violinplots(
            ax, _matrix, colormap_array, _color_df, x_spacer_size, y_spacer_size
        )

        # turn on axis for `ax` as this is turned off
        # by make_grid_spec when the axis is subdivided earlier.
        ax.set_frame_on(True)
        ax.axis("on")
        ax.patch.set_alpha(0.0)

        # add tick labels
        ax.set_ylim(_color_df.shape[0] + y_spacer_size, -y_spacer_size)
        ax.set_xlim(-x_spacer_size, _color_df.shape[1] + x_spacer_size)

        # 0.5 to position the ticks on the center of the violins
        y_ticks = np.arange(_color_df.shape[0]) + 0.5
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(
            [_color_df.index[idx] for idx, _ in enumerate(y_ticks)], minor=False
        )

        # 0.5 to position the ticks on the center of the violins
        x_ticks = np.arange(_color_df.shape[1]) + 0.5
        ax.set_xticks(x_ticks)
        labels = _color_df.columns
        ax.set_xticklabels(labels, minor=False, ha="center")
        # rotate x tick labels if they are longer than 2 characters
        if max([len(x) for x in labels]) > 2:
            ax.tick_params(axis="x", labelrotation=90)
        ax.tick_params(axis="both", labelsize="small")
        ax.grid(False)

        return normalize

    def _make_rows_of_violinplots(
        self, ax, _matrix, colormap_array, _color_df, x_spacer_size, y_spacer_size
    ):
        import seaborn as sns  # Slow import, only import if called

        row_palette = self.kwds.get("color", self.row_palette)
        if "color" in self.kwds:
            del self.kwds["color"]
        if row_palette is not None:
            if is_color_like(row_palette):
                row_colors = [row_palette] * _color_df.shape[0]
            else:
                row_colors = sns.color_palette(row_palette, n_colors=_color_df.shape[0])
            # when row_palette is used, there is no need for a legend
            self.legends_width = 0.0
        else:
            row_colors = [None] * _color_df.shape[0]

        # All columns should have a unique name, yet, frequently
        # gene names are repeated in self.var_names,  otherwise the
        # violin plot will not distinguish those genes
        _matrix.columns = [f"{x}_{idx}" for idx, x in enumerate(_matrix.columns)]

        # transform the  dataframe into a dataframe having three columns:
        # the categories name (from groupby),
        # the gene name
        # the expression value
        # This format is convenient to aggregate per gene or per category
        # while making the violin plots.

        df = (
            pd.DataFrame(_matrix.stack(dropna=False))
            .reset_index()
            .rename(
                columns={
                    "level_1": "genes",
                    _matrix.index.name: "categories",
                    0: "values",
                }
            )
        )
        df["genes"] = (
            df["genes"].astype("category").cat.reorder_categories(_matrix.columns)
        )
        df["categories"] = (
            df["categories"]
            .astype("category")
            .cat.reorder_categories(_matrix.index.categories)
        )

        # the ax need to be subdivided
        # define a layout of nrows = len(categories) rows
        # each row is one violin plot.
        num_rows, num_cols = _color_df.shape
        height_ratios = [y_spacer_size] + [1] * num_rows + [y_spacer_size]
        width_ratios = [x_spacer_size] + [1] * num_cols + [x_spacer_size]

        fig, gs = make_grid_spec(
            ax,
            nrows=num_rows + 2,
            ncols=num_cols + 2,
            hspace=0.2 if self.plot_yticklabels else 0,
            wspace=0,
            height_ratios=height_ratios,
            width_ratios=width_ratios,
        )
        axs_list = []
        for idx, row_label in enumerate(_color_df.index):
            row_ax = fig.add_subplot(gs[idx + 1, 1:-1])
            axs_list.append(row_ax)

            if row_colors[idx] is None:
                palette_colors = colormap_array[idx, :]
            else:
                palette_colors = None

            if not self.are_axes_swapped:
                x = "genes"
                _df = df[df.categories == row_label]
            else:
                x = "categories"
                # because of the renamed matrix columns here
                # we need to use this instead of the 'row_label'
                # (in _color_df the values are not renamed as those
                # values will be used to label the ticks)
                _df = df[df.genes == _matrix.columns[idx]]

            row_ax = sns.violinplot(
                x=x,
                y="values",
                data=_df,
                orient="vertical",
                ax=row_ax,
                palette=palette_colors,
                color=row_colors[idx],
                **self.kwds,
            )

            if self.stripplot:
                row_ax = sns.stripplot(
                    x=x,
                    y="values",
                    data=_df,
                    jitter=self.jitter,
                    color="black",
                    size=self.jitter_size,
                    ax=row_ax,
                )

            self._setup_violin_axes_ticks(row_ax, num_cols)

    def _setup_violin_axes_ticks(self, row_ax, num_cols):
        """
        Configures each of the violin plot axes ticks like remove or add labels etc.

        """
        # remove the default seaborn grids because in such a compact
        # plot are unnecessary

        row_ax.grid(False)
        if self.ylim is not None:
            row_ax.set_ylim(self.ylim)
        if self.log:
            row_ax.set_yscale("log")

        if self.plot_yticklabels:
            for spine in ["top", "bottom", "left"]:
                row_ax.spines[spine].set_visible(False)

            # make line a bit ticker to see the extend of the yaxis in the
            # final plot
            row_ax.spines["right"].set_linewidth(1.5)
            row_ax.spines["right"].set_position(("data", num_cols))

            row_ax.tick_params(
                axis="y",
                left=False,
                right=True,
                labelright=True,
                labelleft=False,
                labelsize="x-small",
            )
            # use only the smallest and the largest y ticks
            # and align the firts label on top of the tick and
            # the second below the tick. This avoid overlapping
            # of nearby ticks
            import matplotlib.ticker as ticker

            # use MaxNLocator to set 2 ticks
            row_ax.yaxis.set_major_locator(
                ticker.MaxNLocator(nbins=2, steps=[1, 1.2, 10])
            )
            yticks = row_ax.get_yticks()
            row_ax.set_yticks([yticks[0], yticks[-1]])
            ticklabels = row_ax.get_yticklabels()
            ticklabels[0].set_va("bottom")
            ticklabels[-1].set_va("top")
        else:
            row_ax.axis("off")
            # remove labels
            row_ax.set_yticklabels([])
            row_ax.tick_params(axis="y", left=False, right=False)

        row_ax.set_ylabel("")

        row_ax.set_xlabel("")

        row_ax.set_xticklabels([])
        row_ax.tick_params(
            axis="x", bottom=False, top=False, labeltop=False, labelbottom=False
        )


@_doc_params(
    show_save_ax=doc_show_save_ax,
    common_plot_args=doc_common_plot_args,
    groupby_plots_args=doc_common_groupby_plot_args,
    vminmax=doc_vboundnorm,
)
def stacked_violin(
    adata: AnnData,
    var_names: _VarNames | Mapping[str, _VarNames],
    groupby: str | Sequence[str],
    log: bool = False,
    use_raw: bool | None = None,
    num_categories: int = 7,
    title: str | None = None,
    colorbar_title: str | None = StackedViolin.DEFAULT_COLOR_LEGEND_TITLE,
    figsize: tuple[float, float] | None = None,
    dendrogram: bool | str = False,
    gene_symbols: str | None = None,
    var_group_positions: Sequence[tuple[int, int]] | None = None,
    var_group_labels: Sequence[str] | None = None,
    standard_scale: Literal["var", "obs"] | None = None,
    var_group_rotation: float | None = None,
    layer: str | None = None,
    stripplot: bool = StackedViolin.DEFAULT_STRIPPLOT,
    jitter: float | bool = StackedViolin.DEFAULT_JITTER,
    size: int = StackedViolin.DEFAULT_JITTER_SIZE,
    scale: Literal["area", "count", "width"] = StackedViolin.DEFAULT_SCALE,
    yticklabels: bool | None = StackedViolin.DEFAULT_PLOT_YTICKLABELS,
    order: Sequence[str] | None = None,
    swap_axes: bool = False,
    show: bool | None = None,
    save: bool | str | None = None,
    return_fig: bool | None = False,
    row_palette: str | None = StackedViolin.DEFAULT_ROW_PALETTE,
    cmap: str | None = StackedViolin.DEFAULT_COLORMAP,
    ax: _AxesSubplot | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    vcenter: float | None = None,
    norm: Normalize | None = None,
    **kwds,
) -> StackedViolin | dict | None:
    """\
    Stacked violin plots.

    Makes a compact image composed of individual violin plots
    (from :func:`~seaborn.violinplot`) stacked on top of each other.
    Useful to visualize gene expression per cluster.

    Wraps :func:`seaborn.violinplot` for :class:`~anndata.AnnData`.

    This function provides a convenient interface to the
    :class:`~scanpy.pl.StackedViolin` class. If you need more flexibility,
    you should use :class:`~scanpy.pl.StackedViolin` directly.

    Parameters
    ----------
    {common_plot_args}
    {groupby_plots_args}
    stripplot
        Add a stripplot on top of the violin plot.
        See :func:`~seaborn.stripplot`.
    jitter
        Add jitter to the stripplot (only when stripplot is True)
        See :func:`~seaborn.stripplot`.
    size
        Size of the jitter points.
    order
        Order in which to show the categories. Note: if `dendrogram=True`
        the categories order will be given by the dendrogram and `order`
        will be ignored.
    scale
        The method used to scale the width of each violin.
        If 'width' (the default), each violin will have the same width.
        If 'area', each violin will have the same area.
        If 'count', a violin’s width corresponds to the number of observations.
    yticklabels
        Set to true to view the y tick labels.
    row_palette
        Be default, median values are mapped to the violin color using a
        color map (see `cmap` argument). Alternatively, a 'row_palette` can
        be given to color each violin plot row using a different colors.
        The value should be a valid seaborn or matplotlib palette name
        (see :func:`~seaborn.color_palette`).
        Alternatively, a single color name or hex value can be passed,
        e.g. `'red'` or `'#cc33ff'`.
    {show_save_ax}
    {vminmax}
    kwds
        Are passed to :func:`~seaborn.violinplot`.

    Returns
    -------
    If `return_fig` is `True`, returns a :class:`~scanpy.pl.StackedViolin` object,
    else if `show` is false, return axes dict

    See also
    --------
    :class:`~scanpy.pl.StackedViolin`: The StackedViolin class can be used to to control
        several visual parameters not available in this function.
    :func:`~scanpy.pl.rank_genes_groups_stacked_violin` to plot marker genes identified
        using the :func:`~scanpy.tl.rank_genes_groups` function.

    Examples
    -------

    Visualization of violin plots of a few genes grouped by the category `bulk_labels`:

    .. plot::
        :context: close-figs

        import scanpy as sc
        adata = sc.datasets.pbmc68k_reduced()
        markers = ['C1QA', 'PSAP', 'CD79A', 'CD79B', 'CST3', 'LYZ']
        sc.pl.stacked_violin(adata, markers, groupby='bulk_labels', dendrogram=True)

    Same visualization but passing var_names as dict, which adds a grouping of
    the genes on top of the image:

    .. plot::
        :context: close-figs

        markers = {{'T-cell': 'CD3D', 'B-cell': 'CD79A', 'myeloid': 'CST3'}}
        sc.pl.stacked_violin(adata, markers, groupby='bulk_labels', dendrogram=True)

    Get StackedViolin object for fine tuning

    .. plot::
        :context: close-figs

        vp = sc.pl.stacked_violin(adata, markers, 'bulk_labels', return_fig=True)
        vp.add_totals().style(ylim=(0,5)).show()

    The axes used can be obtained using the get_axes() method:

    .. code-block:: python

        axes_dict = vp.get_axes()
        print(axes_dict)

    """

    vp = StackedViolin(
        adata,
        var_names,
        groupby=groupby,
        use_raw=use_raw,
        log=log,
        num_categories=num_categories,
        standard_scale=standard_scale,
        title=title,
        figsize=figsize,
        gene_symbols=gene_symbols,
        var_group_positions=var_group_positions,
        var_group_labels=var_group_labels,
        var_group_rotation=var_group_rotation,
        layer=layer,
        ax=ax,
        vmin=vmin,
        vmax=vmax,
        vcenter=vcenter,
        norm=norm,
        **kwds,
    )

    if dendrogram:
        vp.add_dendrogram(dendrogram_key=dendrogram)
    if swap_axes:
        vp.swap_axes()
    vp = vp.style(
        cmap=cmap,
        stripplot=stripplot,
        jitter=jitter,
        jitter_size=size,
        row_palette=row_palette,
        scale=kwds.get("scale", scale),
        yticklabels=yticklabels,
        linewidth=kwds.get("linewidth", StackedViolin.DEFAULT_LINE_WIDTH),
    ).legend(title=colorbar_title)
    if return_fig:
        return vp
    else:
        vp.make_figure()
        savefig_or_show(StackedViolin.DEFAULT_SAVE_PREFIX, show=show, save=save)
        show = settings.autoshow if show is None else show
        if not show:
            return vp.get_axes()
