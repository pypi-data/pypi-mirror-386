"""

The following function is available:

    * :func:`forecast_line_plot`

"""
#pylint: disable=too-many-lines, line-too-long, too-many-arguments, too-many-locals, too-many-branches, attribute-defined-outside-init
#pylint: disable=consider-using-f-string
#pylint: disable=dangerous-default-value
#pylint: disable=bare-except
import logging
import datetime
import pandas as pd

from hana_ml.algorithms.pal.tsa.utility import _cast_str_forecast_result
try:
    import plotly.graph_objs as go
except:
    pass
try:
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    from matplotlib.dates import DateFormatter
except:
    pass

logger = logging.getLogger(__name__) #pylint: disable=invalid-name

class Visualizer(object):
    """
    Base class for all visualizations.
    It stores the axes, size, title and other drawing parameters.
    Only for internal use, do not show it in the doc.

    Parameters
    ----------
    ax : matplotlib.Axes, optional
        The axes to use to plot the figure. Only for matplotlib plot.

        Default value : Current axes
    size : tuple of integers, optional
        (width, height) of the plot in dpi. Only for matplotlib plot.

        Default value: Current size of the plot
    cmap : plt.cm, optional
        The color map used in the plot. Only for matplotlib plot.

        Default value: plt.cm.Blues
    enable_plotly : bool, optional
        Use plotly instead of matplotlib.

        Defaults to True.
    fig : Figure, optional
        Plotly's figure. Only for plotly plot.

    """

    def __init__(self, ax=None, size=None, cmap=None,
                 enable_plotly=True, fig=None, no_fig=False, show_plotly=True): #pylint: disable=invalid-name
        if not enable_plotly:
            if not no_fig:
                self.set_ax(ax)
                self.set_cmap(cmap)
                self.set_size(size)
        self.enable_plotly = enable_plotly
        if fig:
            self.enable_plotly = True
            self.fig = fig
        else:
            self.fig = None
        if self.enable_plotly:
            self.show_plotly = show_plotly

    ##////////////////////////////////////////////////////////////////////
    ## Primary Visualizer Properties
    ##////////////////////////////////////////////////////////////////////
    @property
    def ax(self): #pylint: disable=invalid-name
        """
        Returns the matplotlib Axes where the Visualizer will draw.
        """
        return self._ax

    def set_ax(self, ax):
        """
        Sets the Axes
        """
        if ax is None:
            self._ax = plt.gca()
        else:
            self._ax = ax

    @property
    def size(self):
        """
        Returns the size of the plot in pixels.
        """
        return self._size

    def set_size(self, size):
        """
        Sets the size
        """
        if size is None:
            fig = plt.gcf()
        else:
            fig = plt.gcf()
            width, height = size
            fig.set_size_inches(width / fig.get_dpi(), height / fig.get_dpi())
        self._size = fig.get_size_inches()*fig.dpi

    @property
    def cmap(self):
        """
        Returns the color map being used for the plot.
        """
        return self._cmap

    def set_cmap(self, cmap):
        """
        Sets the colormap
        """
        try:
            if cmap is None:
                self._cmap = plt.cm.get_cmap('Blues')
            else:
                self._cmap = plt.cm.get_cmap(cmap)
        except AttributeError:
            if cmap is None:
                self._cmap = plt.get_cmap('Blues')
            else:
                self._cmap = plt.get_cmap(cmap)

    def reset(self):
        """
        Reset.
        """
        if self.enable_plotly:
            self.fig = None
        else:
            self._size = plt.gcf().get_size_inches()*plt.gcf().dpi
            self._ax = plt.gca()
            self._cmap = plt.cm.get_cmap('Blues')
        self.fig = None

def forecast_line_plot(pred_data, actual_data=None, confidence=None, ax=None, #pylint: disable=too-many-statements
                       figsize=None, max_xticklabels=10, marker=None, enable_plotly=True,
                       pred_option={'zorder': 3}, actual_option={'zorder':1, 'alpha': 0.1},
                       confidence_option={'zorder': 2, 'alpha': 0.2}):
    """
    Plot the prediction data for time series forecast or regression models.

    Parameters
    ----------
    pred_data : DataFrame
        The forecast data.

    actual_data : DataFrame, optional
        The actual data.

        Defaults to None.

    confidence : tuple of str, optional
        The column names of confidence bounds.

        Defaults to None.

    ax : matplotlib.Axes, optional
        The axes used to plot the figure. Only valid when matplotlib is used.

        Defaults to current axes.

    figsize : tuple, optional
        (width, height) of the figure.
        For matplotlib, the unit is inches, and for plotly, the unit is pixels.

        Defaults to (15, 12) when using matplotlib, auto when using plotly.

    max_xticklabels : int, optional
        The maximum number of xtick labels.

        Defaults to 10.

    marker: character, optional
        Type of maker on the plot.

        Default to None indicates no marker.

    enable_plotly : bool, optional
        Use plotly instead of matplotlib.

        Defaults to True.

    pred_option : dict, optional
        Matplotlib options for pred_data line plot.

        Defaults to {'zorder': 3}.

    actual_option : dict, optional
        Matplotlib options for actual_data line plot.

        Defaults to {'zorder': 1, 'alpha': 0.1}.

    confidence_option : dict, optional
        Matplotlib options for confidence area plot.

        Defaults to {'zorder': 2, 'alpha': 0.2}.

    Examples
    --------

    Assume we have a HANA dataframe df_additive which is divided into two dataframes : train_df and test_df.
    Create an 'AdditiveModelForecast' instance and invoke the fit() and predict() functions:

    >>> amf = AdditiveModelForecast()
    >>> amf.fit(data=train_df)
    >>> pred_data = amf.predict(data=test_df)

    Result:

    >>> pred_data.head(5).collect()
                    INDEX         YHAT   YHAT_LOWER   YHAT_UPPER
    0 2018-03-05 01:00:00  1001.524923  1000.606275  1002.436598
    1 2018-03-05 02:00:00  1001.160669  1000.256880  1002.080189
    2 2018-03-05 03:00:00  1000.534993   999.547425  1001.510575
    3 2018-03-05 04:00:00   999.802924   998.893403  1000.733298
    4 2018-03-05 05:00:00   999.101120   998.156421  1000.045716

    Visualize the forecast values:

    Matplotlib:

    >>> forecast_line_plot(pred_data=pred_data,
                           actual_data=df_additive,
                           confidence=("YHAT_LOWER", "YHAT_UPPER"),
                           max_xticklabels=10,
                           enable_plotly=False,
                           actual_option={'zorder': 1, 'alpha': 0.5})

    .. image:: image/line_plot.png
       :align: center
       :scale: 80 %

    Plotly:

    >>> forecast_line_plot(pred_data=pred_data,
                           actual_data=df_additive,
                           confidence=("YHAT_LOWER", "YHAT_UPPER"))

    .. image:: image/line_plotly.png
       :align: center
       :scale: 80 %


    """

    if pred_data.index is None:
        pred_data.set_index(pred_data.columns[0])
        logger.warning("As pred_data has no index, the first column is set as index.")
    pred_data = _cast_str_forecast_result(pred_data, pred_data.index)
    pred_data = pred_data.sort_index()

    if actual_data:
        if actual_data.index is None:
            actual_data.set_index(actual_data.columns[0])
            logger.warning("As actual_data has no index, the first column is set as index.")
        actual_data = _cast_str_forecast_result(actual_data, actual_data.index)
        actual_data = actual_data.sort_index()
        actual_columns = actual_data.columns

    if not enable_plotly: # Matplotlib
        if not figsize:
            figsize = (15, 12)
        pred_xticks = pred_data.select(pred_data.index).collect()[pred_data.index].to_list()
        xticks = pred_xticks
        if actual_data is not None:
            if actual_data.index is not None:
                actual_xticks = actual_data.select(actual_data.index).collect()[actual_data.index]\
                    .to_list()
                xticks = list(set(xticks + actual_xticks))
                xticks.sort()
        if ax is None:
            fig, ax = plt.subplots()
        fig.set_figheight(figsize[1])
        fig.set_figwidth(figsize[0])
        is_timestamp = isinstance(xticks[0], (pd.Timestamp, datetime.date))
        if is_timestamp:
            ax.xaxis.set_major_formatter(DateFormatter("%y-%m-%d %H:%M:%S"))
            ax.xaxis_date()
        ax.set_xticks(xticks)
        my_locator = ticker.MaxNLocator(max_xticklabels)
        ax.xaxis.set_major_locator(my_locator)
        if is_timestamp:
            fig.autofmt_xdate()
        pred_columns = pred_data.columns
        pred_columns.remove(pred_data.index)
        if confidence is not None:
            for item in confidence:
                pred_columns.remove(item)
        if marker:
            if 'marker' not in pred_option:
                pred_option['marker'] = marker
            if 'marker' not in actual_option:
                actual_option['marker'] = marker
        for col in pred_columns:
            ax.plot(pred_xticks, pred_data.select(col).collect()[col].to_list(), **pred_option)
        if actual_data:
            actual_columns.remove(actual_data.index)
            for col in actual_columns:
                ax.plot(actual_xticks,
                        actual_data.select(col).collect()[col].to_list(),
                        **actual_option)
        if confidence is not None:
            ax.fill_between(pred_xticks,
                            pred_data.select(confidence[0]).collect()[confidence[0]].to_list(),
                            pred_data.select(confidence[1]).collect()[confidence[1]].to_list(),
                            **confidence_option)
            if len(confidence) > 3:
                ax.fill_between(pred_xticks,
                                pred_data.select(confidence[2]).collect()[confidence[2]].to_list(),
                                pred_data.select(confidence[3]).collect()[confidence[3]].to_list(),
                                **confidence_option)

        legend_names = pred_columns
        if actual_data:
            if confidence:
                legend_names = legend_names + actual_columns + ['Confidence']
            else:
                legend_names = legend_names + actual_columns
        else:
            if confidence:
                legend_names = legend_names + ['Confidence']

        ax.legend(legend_names, loc='best', edgecolor='w')
        ax.grid()
        return ax
    else: # plotly
        if marker:
            marker = 'lines+markers'
        else:
            marker = 'lines'
        pred_columns = pred_data.columns
        pidx = pred_data.index
        pred_columns.remove(pred_data.index)
        pred_data = pred_data.collect()
        if not ax:
            fig = go.Figure()
        else:
            fig = ax
        if confidence:
            for i, col in enumerate(confidence):
                if i == 0:
                    fig.add_trace(
                        go.Scatter(
                            name=col,
                            x=pred_data[pidx],
                            y=pred_data[col],
                            mode='lines',
                            marker=dict(color="#444"),
                            line=dict(width=0),
                            showlegend=False
                        ))
                else:
                    fig.add_trace(
                        go.Scatter(
                            name=col,
                            x=pred_data[pidx],
                            y=pred_data[col],
                            mode='lines',
                            marker=dict(color="#444"),
                            line=dict(width=0),
                            fillcolor='rgba(68, 68, 68, 0.3)',
                            fill='tonexty',
                            showlegend=False
                        ))
        if confidence is not None:
            for item in confidence:
                pred_columns.remove(item)
        for col in pred_columns:
            fig.add_trace(
                go.Scatter(
                    name=col,
                    x=pred_data[pidx],
                    y=pred_data[col],
                    mode=marker,
                    line=dict(color='rgb(31, 119, 180)'),
                ))
        if actual_data:
            aidx = actual_data.index
            actual_columns.remove(actual_data.index)
            actual_data = actual_data.collect()

            for col in actual_columns:
                fig.add_trace(
                    go.Scatter(
                        name=col,
                        x=actual_data[aidx],
                        y=actual_data[col],
                        mode=marker,
                        line=dict(color='rgb(255, 153, 51)'),
                    ))
        fig.update_layout(hovermode="x")
        if figsize:
            fig.update_layout(autosize=False, width=figsize[0], height=figsize[1])
        fig.update_xaxes(nticks=max_xticklabels)
        return fig
