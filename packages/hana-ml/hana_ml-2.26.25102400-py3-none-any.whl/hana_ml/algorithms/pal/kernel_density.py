'''
This module contains PAL wrappers for kernel density estimation.

The following class is available:

    * :class:`KDE`
'''
#pylint:disable=too-many-lines, too-many-locals, ungrouped-imports, invalid-name
#pylint:disable=too-few-public-methods,too-many-instance-attributes
#pylint:disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
#pylint:disable=line-too-long, attribute-defined-outside-init
#pylint:disable=consider-using-f-string
import logging
import uuid
from hdbcli import dbapi
from hana_ml.ml_exceptions import FitIncompleteError
from hana_ml.ml_base import try_drop
from .pal_base import (
    PALBase,
    ParameterTable,
    ListOfStrings,
    pal_param_register,
    require_pal_usable
)
logger = logging.getLogger(__name__)

class KDE(PALBase):
    r"""
    Perform Kernel Density to analogue with histograms whereas getting rid of its defects.

    Parameters
    ----------

    thread_ratio : float, optional
        Adjusts the percentage of available threads to use, from 0 to 1. A value of 0 indicates the use of a single thread, while 1 implies the use of all possible current threads.
        Values outside the range will be ignored and this function heuristically determines the number of threads to use.

        Default to 0.0.
    leaf_size : int, optional
        Number of samples in a KD tree or Ball tree leaf node.

        Only Valid when ``algorithm`` is 'kd-tree' or 'ball-tree'.

        Default to 30.
    kernel : {'gaussian', 'tophat', 'epanechnikov', 'exponential', 'linear', 'cosine'}, optional
        Kernel function type.

        Default to 'gaussian'.
    method : {'brute_force', 'kd_tree', 'ball_tree'}, optional(deprecated)
        Searching method.

        Default to 'brute_force'
    algorithm : {'brute-force', 'kd-tree', 'ball-tree'}, optional
        Specifies the searching method.

        Default to 'brute-force'.
    bandwidth : float, optional
        Bandwidth used during density calculation. 0 means providing by optimizer inside, otherwise bandwidth is provided by end users.
        Only valid when data is one dimensional.

        Default to 0.
    distance_level : {'manhattan', 'euclidean', 'minkowski', 'chebyshev'}, optional
        Computes the distance between the train data and the test data point.

        Default to 'euclidean'.
    minkowski_power : float, optionl
        When you use the Minkowski distance, this parameter controls the value of power.
        Only valid when ``distance_level`` is 'minkowski'.

        Default to 3.0.
    rtol : float, optional
        The desired relative tolerance of the result.
        A larger tolerance generally leads to faster execution.

        Default to 1e-8.
    atol : float, optional
        The desired absolute tolerance of the result.
        A larger tolerance generally leads to faster execution.

        Default to 0.
    stat_info : bool, optional
        - False: STATISTIC table is empty
        - True: Statistic information is displayed in the STATISTIC table.

        Only valid when parameter selection is not specified.
    resampling_method : {'loocv'}, optional
        Specifies the resampling method for model evaluation / parameter selection,
        only 'loocv' is permitted. Note that ``evaluation_metric`` must be set together.

        No default value.
    evaluation_metric : {'nll'}, optional
        Specifies the evaluation metric for model evaluation / parameter selection,
        only 'nll' is supported.

        No default value.
    search_strategy : {'grid', 'random'}, optional
        Specifies the method to activate parameter selection.

        No default value.
    repeat_times : int, optional
        Specifies the number of repeat times for resampling.

        Default to 1.
    random_state : int, optional
        Specifies the seed for random generation. Use system time when 0 is specified.

        Default to 0.
    bandwidth_values : list, optional
        Specifies values of parameter ``bandwidth`` to be selected.

        Only valid when parameter selection is enabled.
    bandwidth_range : list, optional
        Specifies ranges of parameter ``bandwidth`` to be selected.

        Only valid when parameter selection is enabled.

    Attributes
    ----------
    stats_ : DataFrame
        Statistics. Available only when model evaluation / parameter selection is triggered.

    optim_param_ : DataFrame
        Optimal parameters selected.
        Available only when model evaluation/parameter selection is triggered.

    Examples
    --------
    >>> kde = KDE(leaf_size=10, method='kd_tree', bandwidth=0.68129, stat_info=True)
    >>> kde.fit(data=df_train, key='ID')
    >>> res, stats = kde.predict(data=df_pred, key='ID')
    >>> res.collect()
    >>> stats.collect()
    """
    def __init__(self,
                 thread_ratio=None,
                 leaf_size=None,
                 kernel=None,
                 method=None,
                 distance_level=None,
                 minkowski_power=None,
                 atol=None,
                 rtol=None,
                 bandwidth=None,
                 resampling_method=None,
                 evaluation_metric=None,
                 bandwidth_values=None,
                 bandwidth_range=None,
                 stat_info=None,
                 random_state=None,
                 search_strategy=None,
                 repeat_times=None,
                 algorithm=None):
        setattr(self, 'hanaml_parameters', pal_param_register())
        super(KDE, self).__init__()
        self.key = None
        self.features = None
        self._training_data = None
        self.resampling_method_map = {'loocv': 'loocv'}
        self.evaluation_metric_map = {'nll': 'NLL'}
        self.search_strategy_map = {'grid': 'grid', 'random': 'random'}
        self.kernel_map = {'gaussian': 0, 'tophat': 1, 'epanechnikov': 2,
                           'exponential': 3, 'linear': 4, 'cosine': 5}
        self.method_map = {'brute_force': 0, 'brute-force': 0,
                           'kd_tree': 1, 'kd-tree': 1,
                           'ball_tree': 2, 'ball-tree': 2}
        self.distance_level_map = {'manhattan': 1, 'euclidean': 2, 'minkowski': 3, 'chebyshev': 4}
        self.thread_ratio = self._arg('thread_ratio', thread_ratio, float)
        self.leaf_size = self._arg('leaf_size', leaf_size, int)
        self.kernel = self._arg('kernel', kernel, self.kernel_map)
        self.method = self._arg('method', method, self.method_map)
        self.algorithm = self._arg('algorithm', algorithm, self.method_map)
        self.distance_level = self._arg('distance_level', distance_level, self.distance_level_map)
        self.minkowski_power = self._arg('minkowski_power', minkowski_power, float)
        self.atol = self._arg('atol', atol, float)
        self.rtol = self._arg('rtol', rtol, float)
        self.resampling_method = self._arg('resampling_method', resampling_method, self.resampling_method_map)
        self.evaluation_metric = self._arg('evaluation_metric', evaluation_metric, self.evaluation_metric_map)
        self.bandwidth = self._arg('bandwidth', bandwidth, float)
        self.bandwidth_values = self._arg('bandwidth_values', bandwidth_values, list)
        self.bandwidth_range = self._arg('bandwidth_range', bandwidth_range, list)
        self.stat_info = self._arg('stat_info', stat_info, bool)
        self.repeat_times = self._arg('repeat_times', repeat_times, int)
        self.search_strategy = self._arg('search_strategy', search_strategy, self.search_strategy_map)
        self.random_state = self._arg('random_state', random_state, int)
        cv_count = 0
        for val in (self.resampling_method, self.evaluation_metric):
            if val is not None:
                cv_count += 1
        if cv_count not in (0, 2):
            msg = ("'resampling_method' and 'evaluation_metric' must be set together.")
            logger.error(msg)
            raise ValueError(msg)
        if self.resampling_method is None and self.search_strategy is not None:
            msg = ("'search_strategy' is invalid when resampling_method is not set.")
            logger.error(msg)
            raise ValueError(msg)
        if self.search_strategy is None:
            if self.bandwidth_values is not None:
                msg = ("'bandwidth_values' can only be specified "+
                       "when parameter selection is enabled.")
                logger.error(msg)
                raise ValueError(msg)
            if self.bandwidth_range is not None:
                msg = ("'bandwidth_range' can only be specified "+
                       "when parameter selection is enabled.")
                logger.error(msg)
                raise ValueError(msg)
        if self.search_strategy is not None:
            bandwidth_set_count = 0
            for bandwidth_set in (self.bandwidth, self.bandwidth_range, self.bandwidth_values):
                if bandwidth_set is not None:
                    bandwidth_set_count += 1
            if bandwidth_set_count > 1:
                msg = ("The following parameters cannot be specified together:" +
                       "'bandwidth', 'bandwidth_values', 'bandwidth_range'.")
                logger.error(msg)
                raise ValueError(msg)
            if self.bandwidth_values is not None:
                if not all(isinstance(t, (int, float)) for t in self.bandwidth_values):
                    msg = "Valid values of `bandwidth_values` must be a list of numerical values."
                    logger.error(msg)
                    raise TypeError(msg)

            if self.bandwidth_range is not None:
                rsz = [3] if self.search_strategy == 'grid'else [2, 3]
                if not len(self.bandwidth_range) in rsz or not all(isinstance(t, (int, float)) for t in self.bandwidth_range):
                    msg = ("The provided `bandwidth_range` is either not "+
                           "a list of numerical values, or it contains wrong number of values.")
                    logger.error(msg)
                    raise TypeError(msg)

    def fit(self, data, key, features=None):
        """
        If parameter selection / model evaluation is enabled, perform it.
        Otherwise, just setting the training dataset.

        Parameters
        ----------
        data : DataFrame
            Dataframe including the data of density distribution.
        key : str
            Name of the ID column.
        features : str/list of str, optional
            Name of the feature columns in the dataframe.

            Defaults to all non-key columns.

        Attributes
        ----------
        _training_data : DataFrame
            The training data for kernel density function fitting.
        """
        setattr(self, 'hanaml_fit_params', pal_param_register())
        setattr(self, 'training_data', data)
        conn = data.connection_context
        require_pal_usable(conn)
        self.key = self._arg('key', key, str, True)
        cols = data.columns
        cols.remove(self.key)
        if features is not None:
            if isinstance(features, str):
                features = [features]
            try:
                self.features = self._arg('features', features, ListOfStrings)#pylint: disable=undefined-variable
            except:
                msg = ("'features' must be list of string or string.")
                logger.error(msg)
                raise TypeError(msg)
        else:
            self.features = cols

        data_ = data[[self.key] + self.features]
        self._training_data = data_
        if self.resampling_method is not None:
            param_rows = [('THREAD_RATIO', None, self.thread_ratio, None),
                          ('BUCKET_SIZE', self.leaf_size, None, None),
                          ('KERNEL', self.kernel, None, None),
                          ('METHOD',
                           self.method if self.algorithm is None else self.algorithm,
                           None, None),
                          ('DISTANCE_LEVEL', self.distance_level, None, None),
                          ('MINKOWSKI_POWER', None, self.minkowski_power, None),
                          ('ABSOLUTE_RESULT_TOLERANCE', None, self.atol, None),
                          ('RELATIVE_RESULT_TOLERANCE', None, self.rtol, None),
                          ('RESAMPLING_METHOD', None, None, self.resampling_method),
                          ('EVALUATION_METRIC', None, None, self.evaluation_metric),
                          ('SEED', self.random_state, None, None),
                          ('REPEAT_TIMES', self.repeat_times, None, None),
                          ('PARAM_SEARCH_STRATEGY', None, None, self.search_strategy)]
            if self.bandwidth is not None:
                param_rows.extend([('BANDWIDTH', None, self.bandwidth, None)])
            if self.bandwidth_range is not None:
                val = str(self.bandwidth_range).replace('[', '[').replace(']', ']')
                param_rows.extend([('BANDWIDTH_RANGE', None, None, val)])
            if self.bandwidth_values is not None:
                val = str(self.bandwidth_values).replace('[', '{').replace(']', '}')
                param_rows.extend([('BANDWIDTH_VALUES', None, None, val)])
            unique_id = str(uuid.uuid1()).replace('-', '_').upper()
            tables = ['STATISTICS', 'OPTIMAL_PARAM']#pylint:disable=line-too-long
            tables = ["#PAL_KDE_CV_{}_TBL_{}_{}".format(tbl, self.id, unique_id) for tbl in tables]
            stats_tbl, optim_param_tbl = tables
            try:
                self._call_pal_auto(conn,
                                    'PAL_KDE_CV',
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
            self.stats_ = conn.table(stats_tbl)
            self.statistics_ = self.stats_
            self.optim_param_ = conn.table(optim_param_tbl)
            if(self.bandwidth_range is not None or self.bandwidth_values is not None):
                self.bandwidth = self.optim_param_.select('DOUBLE_VALUE').head().collect()['DOUBLE_VALUE'][0]

    def predict(self, data, key, features=None):
        """
        Apply kernel density analysis.

        Parameters
        ----------
        data : DataFrame
            Dataframe including the data of density prediction.
        key : str
            Column of IDs of the data points for density prediction.
        features : a list of str, optional
            Names of the feature columns.

            Defaults to all non-key columns.

        Returns
        -------
        DataFrame
          - Result data table, i.e. predicted log-density values on all points in ``data``.

          - Statistics information table which reflects the support of prediction points
            over all training points.
        """
        conn = data.connection_context
        require_pal_usable(conn)
        if getattr(self, '_training_data') is None:
            raise FitIncompleteError("training_data is None. Please call the fit() method first.")
        key = self._arg('key', key, str, True)
        cols = data.columns
        cols.remove(key)
        if features is not None:
            if isinstance(features, str):
                features = [features]
            try:
                features = self._arg('features', features, ListOfStrings)#pylint: disable=undefined-variable
            except:
                msg = ("'features' must be list of string or string.")
                logger.error(msg)
                raise TypeError(msg)
        else:
            features = cols
        if len(features) != len(self.features):
            msg = ("Selected feature column number in training data"+
                   " and prediction data must be the same.")
            logger.error(msg)
            raise ValueError(msg)
        data_ = data[[key] + features]
        param_rows = [('THREAD_RATIO', None, self.thread_ratio, None),
                      ('BUCKET_SIZE', self.leaf_size, None, None),
                      ('KERNEL', self.kernel, None, None),
                      ('METHOD', self.method, None, None),
                      ('DISTANCE_LEVEL', self.distance_level, None, None),
                      ('MINKOWSKI_POWER', None, self.minkowski_power, None),
                      ('ABSOLUTE_RESULT_TOLERANCE', None, self.atol, None),
                      ('RELATIVE_RESULT_TOLERANCE', None, self.rtol, None),
                      ('BANDWIDTH', None, self.bandwidth, None),
                      ('STAT_INFO', self.stat_info, None, None)]
        unique_id = str(uuid.uuid1()).replace('-', '_').upper()
        tables = ['RESULT', 'STATISTICS']
        tables = ["#PAL_KDE_{}_TBL_{}_{}".format(tbl, self.id, unique_id) for tbl in tables]
        try:
            self._call_pal_auto(conn,
                                'PAL_KDE',
                                self._training_data,
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
        return conn.table(tables[0]), conn.table(tables[1])
