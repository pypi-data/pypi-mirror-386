#pylint: disable=line-too-long, too-many-locals, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-statements, consider-using-in, invalid-name
#pylint: disable=inconsistent-return-statements, too-few-public-methods, unused-variable
#pylint: disable=useless-object-inheritance
#pylint: disable=consider-using-f-string
"""
This module handles generation of all AMDP(ABAP Managed Database Procedure) related artifacts based on the provided
consumption layer elements. Currently this is experimental code only.

The following class is available:

    * :class:`AMDPGenerator`

"""

import os
import re
from hana_ml.artifacts.generators.filewriter.abap import AMDPWriter
from hana_ml.artifacts.generators.amdp_parser import AMDPParser

from hana_ml.artifacts.config import ConfigConstants, ConfigHandler
from hana_ml.artifacts.utils import DirectoryHandler

from hana_ml.artifacts.generators.sql_processor import SqlProcessor



class AMDPGenerator(object):
    """
    This class provides AMDP(ABAP Managed Database Procedure) specific generation functionality. It also extends the config
    to cater for AMDP generation specific config.

 .. note::
    Supported hana-ml algorithm for AMDP: **UnifiedClassification**.


    Parameters
    ----------
    project_name : str
        Name of the project.

    version : str
        The version.

    connection_context : str
        The connection to the SAP HANA.

    outputdir : str
        The directory of output.


    Examples
    --------
    Let's assume we have a connection to SAP HANA called connection_context and a basic Random Decision Trees Classifier 'rfc' with training data 'diabetes_train_valid' and prediction data 'diabetes_test'.
    Remember that every model has to contain fit and predict logic, therefore the methods `fit()` and `predict()` have to be called at least once.

        >>> rfc_params = dict(n_estimators=5, split_threshold=0, max_depth=10)
        >>> rfc = UnifiedClassification(func="randomdecisiontree", **rfc_params)
        >>> rfc.fit(diabetes_train_valid,
                    key='ID',
                    label='CLASS',
                    categorical_variable=['CLASS'],
                    partition_method='stratified',
                    stratified_column='CLASS')
        >>> rfc.predict(diabetes_test.drop(cols=['CLASS']), key="ID")

    Then, generate abap managed database procedures (AMDP) artifact by creating an AMDPGenerator:

        >>> generator = AMDPGenerator(project_name="PIMA_DIAB", version="1", connection_context=connection_context, outputdir="out/")
        >>> generator.generate()

    The generate() process creates a .abap file on your local machine based on the work that was done previously. This .abap file contains the SQL logic wrapped in AMDPs you have created by interacting with the hana-ml package.

    """

    def __init__(self, project_name, version, connection_context, outputdir):
        self.directory_handler = DirectoryHandler()
        self.config = ConfigHandler.init_config(project_name, version, None, outputdir)
        sql_processor = SqlProcessor(self.config)
        sql_processor.parse_sql_trace(connection_context)
        self._extend_config()

    def _build_folder_structure(self):
        """
        Build up the folder structure. It is currenlty not a deep structure but just a subbfolder abap
        under the root output path.
        """
        # self._clean_folder_structure()
        # Create base directories
        self.directory_handler.create_directory(self.config.get_entry(ConfigConstants.CONFIG_KEY_OUTPUT_PATH_ABAP))

    def _clean_folder_structure(self):
        """
        Clean up physical folder structure.
        """
        path = self.config.get_entry(ConfigConstants.CONFIG_KEY_OUTPUT_PATH_ABAP)
        if os.path.exists(path):
            self.directory_handler.delete_directory_content(path)
            os.rmdir(path)

    def _extend_config(self):
        """
        Extend the config to cater for AMDP generation specific config.
        """
        output_path_amdp = os.path.join(self.config.get_entry(ConfigConstants.CONFIG_KEY_OUTPUT_PATH),
                                        ConfigConstants.ABAP_BASE_PATH)
        self.config.add_entry(ConfigConstants.CONFIG_KEY_OUTPUT_PATH_ABAP, output_path_amdp)

    def generate(self, training_dataset='', apply_dataset='', no_reason_features=3):
        """
        Generate artifacts by first building up the required folder structure for artifacts storage and then
        generating different required files.

        Parameters
        ----------
        training_dataset : str, optional
            Name of training dataset.

            Defaults to ''.
        apply_dataset : str, optional
            Name of apply dataset.

            Defaults to ''.
        no_reason_features : int, optional
            The number of features that contribute to the classification decision the most.
            This reason code information is to be displayed during the prediction phase.

            Defaults to 3.

        """
        self._build_folder_structure()

        amdp_writer = AMDPWriter(self.config)
        sql_key_sql = SqlProcessor.TRACE_KEY_SQL_PROCESSED
        error_message = ''
        sql_processed_cons_layer = self.config.get_entry(ConfigConstants.CONFIG_KEY_SQL_PROCESSED)[
            SqlProcessor.TRACE_KEY_CONSUMPTION_LAYER]
        # base layer also needed to construct the abap class as it contains both layers at once
        sql_processed_base_layer = self.config.get_entry(ConfigConstants.CONFIG_KEY_SQL_PROCESSED)[
            SqlProcessor.TRACE_KEY_BASE_LAYER]

        calls_grouped_by_algorithm = {}
        for element in sql_processed_cons_layer:
            if calls_grouped_by_algorithm.get(element['algo']) is None:
                calls_grouped_by_algorithm[element['algo']] = [element]
            else:
                calls_grouped_by_algorithm[element['algo']].append(element)
        for algo, classifier in calls_grouped_by_algorithm.items():
            # Support check
            if not any([supp_algo in algo.lower() for supp_algo in ConfigConstants.AMDP_SUPPORTED_ALGORITHMS]):
                error_message += 'Algorithm \'{}\' not yet supported for automated hemi generation'.format(algo)
                continue
            bodys, fit_input, predict_input, fit_output, predict_output = [], None, None, None, None
            for element in classifier:
                if not isinstance(element, dict):
                    continue  # ignore
                if element['groups'][0]['type'] in {'fit', 'predict'}:
                    if sql_key_sql in element:
                        if 'output' in element[sql_key_sql]:
                            for table in element[sql_key_sql]['output']:
                                if self.config.is_model_category(table['cat']) or self.config.is_fitted_category(
                                        table['cat']):
                                    if element['groups'][0]['type'] == 'predict':
                                        predict_output = table

                        if 'input' in element[sql_key_sql]:
                            for table in element[sql_key_sql]['input']:
                                if not self.config.is_model_category(table['cat']):
                                    if element['groups'][0]['type'] == 'fit':
                                        fit_input = table  # Only one output allowed in transformation context
                                    else:
                                        predict_input = table

                        if 'body' in element[sql_key_sql]:
                            item = element[sql_key_sql]['body'][0]  # Intermediate step for readability of next line
                            bodys.append(item[sql_key_sql].format(*item['sql_vars']))
                layer = sql_processed_base_layer[algo]
                if not isinstance(layer, dict):
                    error_message += 'No corresponding base layer found for algorithm:' + str(algo) + '\n'
                    break
                if 'fit' in layer.keys() and 'predict' in layer.keys() and \
                        'sql' in layer['fit'].keys() and 'sql' in layer['predict']:
                    fit_base = layer['fit']
                    predict_base = layer['predict']
                    fit_param_sql = self._extract_params_definition_from_sql(fit_base['sql'])
                    predict_param_sql = self._extract_params_definition_from_sql(predict_base['sql'])

                    pal_fit_sql = self._find_pal_function_from_sql(fit_base['sql'])
                    if 'synonyms' in fit_base.keys():
                        for synonym in fit_base['synonyms']:
                            pal_fit_sql = pal_fit_sql.replace(synonym['synonym'],
                                                              (synonym['schema'] + '.' if synonym['schema'] else '') +
                                                              synonym['object'])
                    pal_predict_sql = self._find_pal_function_from_sql(predict_base['sql'])
                    if 'synonyms' in predict_base.keys():
                        for synonym in predict_base['synonyms']:
                            pal_predict_sql = pal_predict_sql.replace(synonym['synonym'],
                                                                      (synonym['schema'] + '.' if synonym['schema'] else '') +
                                                                      synonym['object'])
                else:
                    error_message += 'Algorithm ' + str(algo) + ': Every model has to contain fit and predict ' \
                                                                'logic, therefore the methods `fit()` and ' \
                                                                '`predict()` have to be called at least once\n'
                    break
            else:
                last_column_name_in = re.findall("[A-Za-z0-9_]+(?= TYPE [A-Za-z0-9 ]+,\n$)", fit_input['abap_type'])
                first_column_name_in = re.findall("^.+(?= TYPE)", fit_input['abap_type'])
                if len(last_column_name_in) == 1 and len(first_column_name_in) == 1:
                    target_column = last_column_name_in[0]
                else:
                    error_message += 'Error in abap definition of table input structure and prediction result.\n'
                    continue

                # Create AMDP class name `Z_CL_` as naming-convention
                app_id = self.config.get_entry(ConfigConstants.CONFIG_KEY_PROJECT_NAME)
                amdp_name = 'Z_CL_' + app_id.upper() + '_' + self.config.get_entry(ConfigConstants.CONFIG_KEY_VERSION)

                replacements = AMDPParser.generate_replacements(amdp_name.lower(), training_dataset, apply_dataset, fit_input['table_type'], predict_output['table_type'], no_reason_features, fit_param_sql, predict_param_sql, target_column)

                amdp_writer.write_file(algo, amdp_name, replacements)
        if error_message != '':
            raise ValueError(error_message)

    @staticmethod
    def _extract_params_definition_from_sql(raw_sql):
        """
        Find the code snippet containing the parameter definition from the sql procedure

        Parameters
        ----------
        raw_sql : list
            a list of sql statements

        Returns
        -------
        List of sql statements each of them belonging to the param definition section
        """
        start_index, end_index = None, None
        for i, line in enumerate(raw_sql):
            if re.match("param_name\\[[1-9]+\\] := .+;", line) and not start_index:
                start_index = i
            if re.match("params = UNNEST(.+)", line):
                end_index = i
                break
        if start_index is None:
            start_index = end_index
        return raw_sql[start_index:end_index]

    @staticmethod
    def _find_pal_function_from_sql(raw_sql):
        """
        Extract the specific function call of the PAL function from the sql code. Nevertheless it only detects
        the synonyms that have to be resolved afterwards
        Parameters
        ----------
        raw_sql : list
            a list of sql statements

        Returns
        -------
        The procedure name synonym
        CALL "SYS_AFL.PAL_RANDOM_FORREST" (...) -> SYS_AFL.PAL_RANDOM_FORREST"
        """
        for line in raw_sql:
            calls = re.findall('CALL \"(.+)\".+,', line)
            if len(calls) > 0:
                return calls[0]
