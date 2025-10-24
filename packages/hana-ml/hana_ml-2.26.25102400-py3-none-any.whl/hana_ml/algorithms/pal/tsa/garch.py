"""
This module contains the Python wrapper for GARCH model in PAL.

The following class are available:

    * :class:`GARCH`
"""
#pylint: disable=too-many-instance-attributes, too-few-public-methods, invalid-name, too-many-statements
#pylint: disable=too-many-lines, line-too-long, too-many-arguments, too-many-branches, attribute-defined-outside-init
#pylint: disable=simplifiable-if-statement, too-many-locals, bare-except
#pylint: disable=consider-using-f-string
#pylint: disable=broad-except
import logging
import uuid
from hdbcli import dbapi
from hana_ml.ml_exceptions import FitIncompleteError
from ..sqlgen import trace_sql
from .utility import _convert_index_from_timestamp_to_int, _is_index_int
from .utility import _get_forecast_starttime_and_timedelta
from ..pal_base import (
    PALBase,
    ParameterTable,
    pal_param_register,
    quotename,
    try_drop,
    require_pal_usable
)
logger = logging.getLogger(__name__)#pylint:disable=invalid-name

class GARCH(PALBase):
    r"""
    Generalized AutoRegressive Conditional Heteroskedasticity (GARCH) is a statistic model
    used to analysis variance of error (innovation or residual) term in time series.
    It is typically used in the analyzing of financial data, such as estimation of
    volatility of returns for stocks and bonds.

    GARCH assumes variance of error term is heteroskedastic which means it is not a constant value.
    In appearance, it tends to cluster. GARCH assumes variance of error term subjects to an
    autoregressive moving average(ARMA) pattern, in other words it is an average of past values.

    Assuming a time-series model:

    :math:`y_t = \mu_t + \varepsilon_t`

    where :math:`\mu_t` is called mean model(can be an ARMA model or just a constant value), it is
    :math:`\sigma_t^2 = var(\varepsilon_t|F_{t-1})` (i.e. the conditional variance of :math:`\varepsilon_t`)
    that causes the main interest, where :math:`F_{t-1}` stands for the information set known at time t-1.

    Then, a GARCH(p, q) model is defined as:

    :math:`\sigma_t^2 = \alpha_0+\sum_{i=1}^p\alpha_i\varepsilon_{t-i}^2+\sum_{j=1}^q\beta_j\sigma_{t-j}^2`,

    where :math:`\alpha_0 > 0` and :math:`\alpha_i \geq 0, \beta_j\geq 0, i \in [1, p], j \in [1, q].`

    In our procedure, it is assumed that :math:`\mu_t` has already been deducted from :math:`y_t`.
    So the input time-series is :math:`\varepsilon_t` only.

    Another assumption is :math:`P(\varepsilon_t | F_{t-1}) \sim N(0,\sigma_t^2)`,
    so model factors can be estimated with MLE.


    Parameters
    ----------
    p : int, optional
        Specifies the number of lagged error terms in GARCH model.

        Valid only when ``model_type`` is not "igarch".

        Defaults to 1.

    q : int, optional
        Specifies the number of lagged variance terms in GARCH model.

        Valid only when ``model_type`` is not "igarch".

        Defaults to 1.

    model_type : str, optional
        Specifies the variant of GARCH model.

        - 'garch' : the regular GARCH model.
        - 'igarch' : the `integrated` GARCH model.
        - 'tgarch' : the `threshold` GARCH model.
        - 'egarch' : the `exponential` GARCH model.

        Defaults to 'garch'.

    Attributes
    ----------
    model_ : DataFrame
        Model content.

    variance_ : DataFrame
        For storing the variance information of the training data, structured as follows:

           - 1st column : Same name and type as the index(timestamp) column in the training data.
           - 2nd column : VARIANCE, type DOUBLE, representing the conditional variance of residual term.
           - 3rd column : RESIDUAL, type DOUBLE, representing the residual value.

        set to None if GARCH model is not fitted.

    stats_ : DataFrame
        DataFrame for storing the related statistics in fitting GARCH model.

            - 1st column : STAT_NAME, type NVARCHAR(1000)
            - 2nd column : STAT_VALUE, type NVARCHAR(1000)

    Examples
    --------
    >>> df.collect()
        TIME  VAR1  VAR2 VAR3
    0      1     2  0.17    A
    1      2     2  0.19    A
    ...
    18    19     2  1.32    A
    19    20     2  1.10    A

    Setting up hyper-parameters and train the GARCH model using the input data:

    >>> gh = GARCH(p=1, q=1)
    >>> gh.fit(data=df, key='TIME', endog='VAR2')
    >>> gh.model_.collect()
       ROW_INDEX                                      MODEL_CONTENT
    0          0  {"garch":{"factors":[0.13309395260165602,1.060...

    Predicting future volatility of the given time-series data:

    >>> pred_res, _ = gh.predict(horizon=5)
    >>> pred_res.collect()
       STEP  VARIANCE RESIDUAL
    0     1  1.415806     None
    1     2  1.633979     None
    2     3  1.865262     None
    3     4  2.110445     None
    4     5  2.370360     None
    """
    model_type_map = {'garch':0, 'igarch':1, 'tgarch':2, 'egarch':3}
    def __init__(self,#pylint: disable=too-many-arguments
                 p=None,
                 q=None,
                 model_type=None):

        setattr(self, 'hanaml_parameters', pal_param_register())
        super(GARCH, self).__init__()
        self.p = self._arg('p', p, int)
        self.q = self._arg('q', q, int)
        self.model_type = self._arg('model_type', model_type,
                                    self.model_type_map)
        self.model_ = None
        self.variance_ = None
        self.stats_ = None
        self.statistics_ = self.stats_
        self.is_index_int = True

    @trace_sql
    def fit(self, data, key=None, endog=None, thread_ratio=None):
        r"""
        Fit the model to the training dataset.

        Parameters
        ----------
        data : DataFrame
            Input data for fitting a GARCH model.

            ``data`` should at least contain 2 columns described as follows:

                - An index column of INTEGER or TIMESTAMP/DATE/SECONDDATE type,
                  representing the time-order(i.e. timestamp).
                - An numerical column representing the values of time-series.

        key : str, optional
            Specifies the name of index column in ``data``.

            Mandatory if ``data`` is not indexed, or indexed by multiple columns.

            Defaults to the single index column of ``data`` if not provided.

        endog : str, optional
            Specifies the name of the columns holding values for time-series in ``data``.

            Cannot be the ``key`` column.

            Defaults to the last non-key column in ``data``.

        thread_ratio : float, optional
            Adjusts the percentage of available threads to use, from 0 to 1. A value of 0 indicates the use of a single thread, while 1 implies the use of all possible current threads.
            Values outside the range will be ignored and this function heuristically determines the number of threads to use.  Valid only when ``show_explainer`` is True.

            Defaults to -1.

        Returns
        -------
        A fitted object of class "GARCH".

        """
        conn = data.connection_context
        require_pal_usable(conn)
        setattr(self, 'hanaml_fit_params', pal_param_register())
        setattr(self, "training_data", data)
        self.conn_context = conn
        index = data.index
        key = self._arg('key', key, str, required=not isinstance(index, str))
        if isinstance(index, str):
            if key is not None and index != key:
                msg = "Discrepancy between the designated key column '{}' ".format(key) +\
                "and the designated index column '{}'.".format(index)
                logger.warning(msg)
        key = index if key is None else key
        cols = data.columns
        cols.remove(key)
        endog = self._arg('endog', endog, str)
        if endog is None:
            endog = cols[-1]
        thread_ratio = self._arg('thread_ratio', thread_ratio, float)
        data_ = data[[key, endog]]
        self.is_index_int = _is_index_int(data, key)
        if not self.is_index_int:
            data_ = _convert_index_from_timestamp_to_int(data_, key)
        try:
            self.forecast_start, self.timedelta = _get_forecast_starttime_and_timedelta(data, key, self.is_index_int)
        except Exception as err:
            logger.warning(err)
            pass
        unique_id = str(uuid.uuid1()).replace('-', '_').upper()
        tables = ['MODEL', 'VARIANCE', 'STATS']
        tables = ['#GARCH_{}_TBL_{}'.format(tbl, unique_id) for tbl in tables]
        model_tbl, variance_tbl, stats_tbl = tables
        param_rows = [('P', self.p, None, None),
                      ('Q', self.q, None, None),
                      ('MODEL_TYPE', self.model_type, None, None),
                      ('THREAD_RATIO', None, thread_ratio, None)]
        try:
            self._call_pal_auto(conn,
                                'PAL_GARCH',
                                data_,
                                ParameterTable().with_data(param_rows),
                                *tables)
        except dbapi.Error as db_err:
            logger.exception(str(db_err))
            try_drop(conn, tables)
            raise
        except Exception as db_err:
            logger.exception(str(db_err))
            try_drop(conn, tables)
            raise
        self.model_ = conn.table(model_tbl)
        self.variance_ = conn.table(variance_tbl)
        if not self.is_index_int:
            data = data.add_id('{}(INT)'.format(key), ref_col=key)
            self.variance_ = self.variance_.alias('L').join(data[[key, key + '(INT)']].alias('R'),
                                                            'L.%s=R.%s'%(quotename(key + ('(INT)')),
                                                                         quotename(key + ('(INT)'))),
                                                            select=[key,
                                                                    'VARIANCE',
                                                                    'RESIDUAL'])
        self.stats_ = conn.table(stats_tbl)
        self.statistics_ = self.stats_
        return self

    @trace_sql
    def predict(self, horizon=None):
        r"""
        Predicts variance of error terms in time series based on trained GARCH model.

        Parameters
        ----------
        horizon : int, optional
            Specifies the number of steps to be forecasted.

            Defaults to 1.

        Returns
        -------

        Two DataFrames

          - 1st DataFrame : the variance information.
          - 2nd DataFrame : statistics.
        """
        if getattr(self, 'model_') is None:
            raise FitIncompleteError()
        horizon = self._arg('horizon', horizon, int)
        param_rows = [('FORECAST_STEPS', horizon, None, None)]
        conn = self.model_.connection_context

        unique_id = str(uuid.uuid1()).replace('-', '_').upper()
        tables = ['VARIANCE', 'STATS']
        tables = ["#PAL_GARCH_FORECAST_{}_RESULT_TBL_{}_{}".format(tb,
                                                                   self.id,
                                                                   unique_id) for tb in tables]
        variance_tbl, stats_tbl = tables
        try:
            self._call_pal_auto(conn,
                                'PAL_GARCH_FORECAST',
                                self.model_,
                                ParameterTable().with_data(param_rows),
                                *tables)
        except dbapi.Error as db_err:
            logger.exception(str(db_err))
            try_drop(conn, tables)
            raise
        except Exception as db_err:
            logger.exception(str(db_err))
            try_drop(conn, tables)
            raise
        fct_ = conn.table(variance_tbl)
        if self.is_index_int:
            return fct_, conn.table(stats_tbl)
        fct_ = conn.sql("""
                        SELECT ADD_SECONDS('{0}', ({1} - 1) * {2}) AS {1},
                        {4},
                        {5}
                        FROM ({3})
                        """.format(self.forecast_start,
                                   quotename(fct_.columns[0]),
                                   self.timedelta,
                                   fct_.select_statement,
                                   quotename(fct_.columns[1]),
                                   quotename(fct_.columns[2])))
        return fct_, conn.table(stats_tbl)
