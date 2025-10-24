"""
This module contains Python wrappers for SAP HANA PAL hierarchical forecast algorithm.'

The following classes are available:

    * :class:`Hierarchical_Forecast`
"""
#pylint: disable=too-many-lines, too-many-instance-attributes
#pylint: disable=line-too-long, too-many-arguments, attribute-defined-outside-init
#pylint: disable=invalid-name, too-many-locals, too-few-public-methods, too-many-statements
#pylint: disable=relative-beyond-top-level
#pylint: disable=consider-using-f-string
import logging
import uuid
from hdbcli import dbapi
from ..pal_base import (
    PALBase,
    ParameterTable,
    try_drop,
    require_pal_usable,
    pal_param_register
)
logger = logging.getLogger(__name__)

class Hierarchical_Forecast(PALBase):
    r"""
    Hierarchical forecast algorithm forecast across the hierarchy (that is, ensuring the forecasts sum appropriately across the levels).

    Parameters
    ----------

    method : {'optimal_combination', 'bottom_up', 'top_down'}, optional
        Method for reconciling forecasts across hierarchy.

        Default to 'optimal_combination'.

    weights : {'ordinary_least_squares', 'minimum_trace', 'weighted_least_squares'}, optional
        Only valid when parameter method is 'optimal_combination'.

        Default to 'ordinary_least_squares'.

    Attributes
    ----------
    result_ : DataFrame
        Forecast result.

    stats_ : DataFrame
        Statistics.

    Examples
    --------
    Input DataFrames:

    >>> orig_df.collect().head(5)
        Series  TimeStamp   Original  Residual
    0    Total       1992  48.748080  0.058252
    1    Total       1993  49.480469  0.236069
    2    Total       1994  49.932384 -0.044405
    3    Total       1995  50.240702 -0.188002
    4    Total       1996  50.608464 -0.128558

    >>> pred_df.collect().head(5)
        Series  TimeStamp          VALUE
    0    Total       1993      54.711279
    1    Total       1994      54.207598
    2    Total       1995      54.703918
    3    Total       1996      55.200238
    4    Total       1997      55.696558

    >>> stru_df.collect().head(5)
       Index   Series    NUM
    0      1    Total      2
    1      2        A      3
    2      3        B      2
    3      4       AA      0
    4      5       AB      0

    Create a Hierarchical_Forecast instance:

    >>> hr = Hierarchical_Forecast(method='optimal_combination',
                                   weights='minimum_trace')

    Perform fit_predict():

    >>> stats_tbl, result_tbl = hr.fit_predict(orig_data=orig_df,
                                               pred_data=pred_df,
                                               stru_data=stru_df)

    Output:

    >>> result_tbl.collect().head(5)
        Series   TimeStamp      VALUE
    0    Total        1993  48.862705
    1    Total        1994  54.255631
    2    Total        1995  54.663688
    3    Total        1996  55.192436
    4    Total        1997  55.719965

    """
    method_list = {'optimal_combination': 0,
                   'bottom_up': 1,
                   'top_down': 2}
    weights_list = {'ordinary_least_squares': 0,
                    'minimum_trace': 1,
                    'weighted_least_squares': 2}
    # pylint: disable=
    def __init__(self,
                 method=None,
                 weights=None):
        setattr(self, 'hanaml_parameters', pal_param_register())
        super(Hierarchical_Forecast, self).__init__()

        if method is not None and method not in self.method_list:
            msg = ('The value of method can only be chosen among {}!'.format(sorted(list(self.method_list.keys()))))
            logger.error(msg)
            raise ValueError(msg)
        self.method = self._arg('method', method, self.method_list)
        if self.method is None:
            self.method = self.method_list['optimal_combination']

        if weights is not None:
            if method is not None and method != 'optimal_combination':
                msg = ('The value of weights is valid only when method is set to optimal_combination!')
                logger.error(msg)
                raise ValueError(msg)
            if weights not in self.weights_list:
                msg = ('The value of weights can only be chosen among {}!'
                       .format(sorted(list(self.weights_list.keys()))))
                logger.error(msg)
                raise ValueError(msg)
        self.weights = self._arg('weights', weights, self.weights_list)
        if self.weights is None:
            self.weights = self.weights_list['ordinary_least_squares']

    def fit_predict(self, orig_data, pred_data, stru_data, orig_name=None, orig_key=None, orig_endog=None,
                    orig_residual=None, pred_name=None, pred_key=None, pred_endog=None):
        """
        Apply hierarchical forecast to the input DataFrames.

        Parameters
        ----------
        orig_data : DataFrame
            DataFrame of original data.

        pred_data : DataFrame
            DataFrame of predictive data.

        stru_data : DataFrame
            DataFrame of structure data.

        orig_name : str, optional
            Name of the time series name column.

        orig_key : str, optional
            Name of the time stamp column.

        orig_endog : str, optional
            Name of the raw data column.

        orig_residual : str, optional
            Name of the residual value column.

        pred_name : str, optional
            Name of time series name column.

        pred_key : str, optional
            Name of the time stamp column.

        pred_endog : str, optional
            Name of the predictive raw data column.
        """
        conn = orig_data.connection_context
        require_pal_usable(conn)
        setattr(self, 'hanaml_fit_params', pal_param_register())
        unique_id = str(uuid.uuid1()).replace('-', '_').upper()
        outputs = ['RESULT_DATA', 'STATISTICS']
        outputs = ['#PAL_HIERARCHICAL_FORECAST_{}_TBL_{}_{}'
                   .format(name, self.id, unique_id) for name in outputs]
        result_tbl, stats_tbl = outputs

        param_rows = [
            ('METHOD', self.method, None, None),
            ('WEIGHTS', self.weights, None, None)]
        orig_attributes = [["orig_name", self._arg('orig_name', orig_name, str)],
                           ["orig_key", self._arg('orig_key', orig_key, str)],
                           ["orig_endog", self._arg('orig_endog', orig_endog, str)],
                           ["orig_residual", self._arg('orig_residual', orig_residual, str)]]

        pred_attributes = [["pred_name", self._arg('pred_name', pred_name, str)],
                           ["pred_key", self._arg('pred_key', pred_key, str)],
                           ["pred_endog", self._arg('pred_endog', pred_endog, str)]]

        orig_cols = _collect_columns(orig_data, 4, orig_attributes)
        pred_cols = _collect_columns(pred_data, 3, pred_attributes)
        orig_data = orig_data[orig_cols]
        pred_data = pred_data[pred_cols]

        try:
            self._call_pal_auto(conn,
                                "PAL_HIERARCHICAL_FORECAST",
                                orig_data,
                                pred_data,
                                stru_data,
                                ParameterTable().with_data(param_rows),
                                result_tbl,
                                stats_tbl)
        except dbapi.Error as db_err:
            logger.exception(str(db_err))
            try_drop(conn, result_tbl)
            try_drop(conn, stats_tbl)
            raise
        except Exception as db_err:
            logger.exception(str(db_err))
            try_drop(conn, result_tbl)
            try_drop(conn, stats_tbl)
            raise
        return conn.table(stats_tbl), conn.table(result_tbl)

def _collect_columns(data_frame, col_count, col_attrs=None):
    """
    Collect data from indicated col_attrs of data_frame, with at least clo_count columns.
    """
    cols = data_frame.columns
    if len(cols) < col_count:
        msg = ("Input data should contain at least {} columns.".format(col_count))
        logger.error(msg)
        raise ValueError(msg)
    fin_cols = []
    for index, col_attr in enumerate(col_attrs):
        if col_attr[1] is None:
            fin_cols.append(cols[index])
        elif col_attr[1] not in cols:
            msg = ('Invalid column name \'{}\', should be selected among {}!'
                   .format(col_attr[1], cols))
            logger.error(msg)
            raise ValueError(msg)
        else:
            fin_cols.append(col_attr[1])

    if len(set(fin_cols)) < col_count:
        msg = "Duplicated column names detected among {}!".format(fin_cols)
        logger.error(msg)
        raise ValueError(msg)
    return fin_cols
