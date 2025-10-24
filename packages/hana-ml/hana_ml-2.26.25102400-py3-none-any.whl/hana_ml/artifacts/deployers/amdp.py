#pylint: disable=line-too-long, too-many-arguments, too-many-locals, unused-argument, bare-except, invalid-name, unused-variable
#pylint: disable=logging-format-interpolation, too-many-branches, too-many-statements, inconsistent-return-statements
#pylint: disable=no-else-raise, useless-object-inheritance, unspecified-encoding

"""
This module provides AMDP related functionality.

The following class is available:

    * :class:`AMDPDeployer`
    * :func:`gen_pass_key`

"""

#pylint: disable=unreachable, no-member
#pylint: disable=consider-using-f-string
import logging
import os
import json
from xml.etree import ElementTree
import time
import getpass
import sqlite3
import requests
import urllib3

# check if cryptography has been installed, if not install it and reload the module
try:
    from cryptography.fernet import Fernet
except ImportError:
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    from cryptography.fernet import Fernet

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

def gen_pass_key(url, user, passwd=None):
    """
    This function provides a way to encrypt user name and password,
    and then returns the key for future access.

    Parameters
    ----------
    url : str
        The url of backend/frontend.
    user : str
        User name.
    passwd : str
        Password.

    Returns
    -------
        pass_key
    """
    if passwd is None:
        while True:
            passwd = getpass.getpass("Password : ")
            if passwd is not None:
                break
    pass_key = Fernet.generate_key()
    coded_pwd = Fernet(pass_key).encrypt(passwd.encode())
    conn = sqlite3.connect('pass_key.db')
    cur = conn.cursor() # The database will be saved in the location where your 'py' file is saved
    cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='SECURE_STORE' ''')
    #if the count < 1, then table doesn't exist
    if cur.fetchone()[0] < 1:
        cur.execute('''CREATE TABLE SECURE_STORE
             (url text, user text, encrypted_pwd blob)''')
    cur.execute(''' SELECT count(*) FROM SECURE_STORE WHERE url='{}' AND user='{}' '''.format(url, user))
    if cur.fetchone()[0] < 1:
        sql = ''' INSERT INTO SECURE_STORE(url, user, encrypted_pwd)
                  VALUES(?, ?, ?) '''
        cur.execute(sql, (url, user, coded_pwd))
    else:
        sql = ''' UPDATE SECURE_STORE
              SET encrypted_pwd=?
              WHERE url=? AND user=?'''
        cur.execute(sql, (coded_pwd, url, user))
    conn.commit()
    return bytes(url, 'utf-8') + b" " + bytes(user, 'utf-8') + b" " + pass_key

def _fetch_encrypted_pwd(url, user):
    conn = sqlite3.connect('pass_key.db')
    cur = conn.cursor()
    cur.execute(''' SELECT encrypted_pwd FROM SECURE_STORE WHERE url='{}' AND user='{}' '''.format(url, user))
    fetch = cur.fetchone()[0]
    conn.commit()
    return fetch

def _decode_pwd(pass_key, encrypted_pwd):
    return Fernet(pass_key).decrypt(encrypted_pwd).decode()

class AMDPDeployer(object):
    """
    This class provides AMDP deployer related functionality.
    After you create an AMDPGenerator to establish a corresponding AMDP class, then you can create an AMDPDeployer to upload such class into the ISLM framework by creating an intelligent scenario.

 .. note::
    Supported hana-ml algorithm for AMDP: **UnifiedClassification**.

    Apart of the standard developer authorizations, you need to get the **SAP_INTNW_ISLM** role for deployers related functions.

    Parameters
    ----------
    backend_url : str
        The url of backend.

    backend_auth : str or tuple
        The authentication information of backend which contain user name and password.

    frontend_url : str
        The url of frontend.

    frontend_auth : str or tuple
        The authentication information of frontend which contain user name and password.

    backend_key : bytes, optional
        If backend_key has been generated, it can be used instead of password.

        Defaults to None.
    frontend_key : bytes, optional
        If frontend_key has been generated, it can be used instead of password.

        Defaults to None.
    url : str
        The url.
    auth : str or tuple
        The authentication information of backend and frontend which contain user name and password.
    user_key : bytes, optional
        If user key has been generated, it can be used instead of password.

        Defaults to None.

    Examples
    --------
    After you use an AMDPGenerator to generate a .abap file, you can now take the generated code in the 'outputdir' and deploy it
    to SAP S/4HANA or any ABAP stack with ISLM for that matter. All you need is to provide the .abap file, and some basic parameters
    for the ISLM registration.

    >>> deployer = AMDPDeployer(backend_url=backend_url,
                                backend_auth=(backend_user,
                                              backend_password),
                                frontend_url=frontend_url,
                                frontend_auth=(frontend_user,
                                               frontend_password))
    >>> guid = deployer.deploy(fp="XXX.abap",
                               model_name="MODEL_01",
                               catalog="$TMP",
                               scenario_name="DEMO_CUSTOM01",
                               scenario_description="Hello S/4 demo!",
                               scenario_type="CLASSIFICATION",
                               force_overwrite=True,
                               master_system="ER9",
                               transport_request="$TMP",
                               sap_client='000')

    After the deployment is competed, you can see an intelligent scenario in the 'Intelligent Scenarios' Fiori app of the ISLM framework.
    This scenario has a name specified during the deployment step.

        """

    def __init__(self, backend_url=None, backend_auth=None, frontend_url=None, frontend_auth=None, backend_key=None, frontend_key=None, url=None, auth=None, user_key=None):
        _backend_auth = backend_auth
        _frontend_auth = frontend_auth
        if url:
            backend_url = url
        if auth:
            if isinstance(auth, str):
                backend_auth = auth
            else:
                _backend_auth = auth
        if frontend_url is None:
            frontend_url = backend_url
        if user_key:
            backend_key = user_key
        if backend_key:
            splited_res = backend_key.split(b' ', maxsplit=2)
            backend_url = splited_res[0].decode()
            backend_auth = splited_res[1].decode()
            backend_coded_pwd = _fetch_encrypted_pwd(backend_url, backend_auth)
            backend_pwd = _decode_pwd(splited_res[2], backend_coded_pwd)
            _backend_auth = (backend_auth, backend_pwd)
            if user_key:
                frontend_url = backend_url
                _frontend_auth = (backend_auth, backend_pwd)
        if frontend_key:
            splited_res = backend_key.split(b' ', maxsplit=2)
            frontend_url = splited_res[0].decode()
            frontend_auth = splited_res[1].decode()
            frontend_coded_pwd = _fetch_encrypted_pwd(frontend_url, frontend_auth)
            frontend_pwd = _decode_pwd(splited_res[2], frontend_coded_pwd)
            _frontend_auth = (frontend_auth, frontend_pwd)

        if frontend_auth:
            if isinstance(backend_auth, str) and (backend_key is None):
                while True:
                    backend_pwd = getpass.getpass("Backend User : %s Password : " % backend_auth)
                    if backend_pwd is not None:
                        break
                _backend_auth = (backend_auth, backend_pwd)
            if isinstance(frontend_auth, str) and (frontend_key is None):
                while True:
                    frontend_pwd = getpass.getpass("Frontend User : %s Password : " % frontend_auth)
                    if frontend_pwd is not None:
                        break
                _frontend_auth = (frontend_auth, frontend_pwd)
        else:
            if isinstance(backend_auth, str) and (backend_key is None):
                while True:
                    backend_pwd = getpass.getpass("User : %s Password : " % backend_auth)
                    if backend_pwd is not None:
                        break
                _backend_auth = (backend_auth, backend_pwd)
                _frontend_auth = (backend_auth, backend_pwd)
        self.backend_url = backend_url
        self.__backend_auth = _backend_auth
        if frontend_auth is None:
            frontend_auth = _backend_auth
        self.frontend_url = frontend_url
        self.__frontend_auth = _frontend_auth

        self.islm_url = frontend_url + "/sap/opu/odata/SAP/ISLM_IS_SRV"
        self.islm_train_url = frontend_url + "/sap/opu/odata/SAP/ISLM_REPOSITORY_SRV"
        self.adt_url = backend_url + "/sap/bc/adt"

    @staticmethod
    def _get_session(url, auth):
        sess = requests.Session()
        sess.auth = auth
        response = sess.get(url, headers={
            "x-csrf-token": "fetch"
        }, verify=False)
        #if response.status_code != 200:
        #    response.raise_for_status()
        csrf_token = response.headers['x-csrf-token']
        return sess, csrf_token

    @staticmethod
    def _get_headers(x_csrf_token, content_type="application/json", accept="application/json", **kwargs):
        headers = {
            "x-csrf-token": x_csrf_token,
            "Content-type": content_type,
            "Accept": accept
        }

        for key in kwargs:
            headers[key] = kwargs[key]
        return headers

    @staticmethod
    def _parse_json_error_message(error_message):
        try:
            json_val = json.loads(error_message)["error"]["message"]["value"]
        except ValueError as e:
            return error_message
        return json_val

    @staticmethod
    def _parse_xml_error_message(error_message):
        return ElementTree.fromstring(error_message).find('message').text

    def deploy(self, fp, model_name, catalog, scenario_name, scenario_type,
               class_description=None, scenario_description=None, force_overwrite=False,
               master_system="ER9", transport_request="$TMP",
               sap_client='000'):

        """
        The deploy method is to deploy an AMDP class into SAP S/4HANA with Intelligent Scenario Lifecycle Management (ISLM).

        Parameters
        ----------
        fp : str
            Name of the abap file to be opened.

        model_name : str
            Name of the model.

        catalog : str
            Name of the catalog.

        scenario_name : str
            Name of the intelligent scenario.

        scenario_type : str
            Type of the intelligent scenario.

        class_description : str, optional
            Description of the class.

            Defaults to None.

        scenario_description : str, optional
            Description of the intelligent scenario.

            Defaults to None.

        force_overwrite : bool, optional
            Whether to overwrite the class if class already exists.

            Defaults to False.

        master_system : str, optional
            Name of the master system.
            Please enter the name of master system you are working on.

            Defaults to "ER9".

        transport_request : str, optional
            Name of the package.
            Please enter the name of package you are working on.

            Defaults to '$TMP'.

        sap_client : str, optional
            The client of SAP.
            Please enter the name of client you are using.

            Defaults to '000'.

        Returns
        -------
        GUID (Globally Unique Identifier).

        Examples
        --------

        Create an AMDPDeployer object:

        >>> deployer = AMDPDeployer(backend_url=backend_url,
                                    backend_auth=(backend_user,
                                                  backend_password),
                                    frontend_url=frontend_url,
                                    frontend_auth=(frontend_user,
                                                   frontend_password))

        Deploy:

        >>> guid = deployer.deploy(fp="XXX.abap",
                                   model_name=model_name,
                                   catalog="XXX",
                                   scenario_name=scenario_name,
                                   scenario_description=scenario_description,
                                   scenario_type=scenario_type,
                                   force_overwrite=True,
                                   master_system="ER9",
                                   transport_request="$TMP",
                                   sap_client='000')
        """

        with open(fp, 'r') as file:
            abap_class_code = file.read()
        name = os.path.basename(file.name).replace(".abap", "")
        abap_class_code = self.format(abap_class_code, master_system)

        self.deploy_class(class_name=name,
                          abap_class_code=abap_class_code,
                          class_description=class_description,
                          master_system=master_system,
                          force_overwrite=force_overwrite,
                          transport_request=transport_request)
        time.sleep(20)
        if force_overwrite:
            self.delete_islm(scenario_name, sap_client)
        guid = self.register_islm(name, model_name, catalog, scenario_name, scenario_type, scenario_description,
                                  sap_client)
        return guid

    def deploy_class(self, class_name, abap_class_code, class_description=None, master_system="ER9",
                     force_overwrite=False, transport_request='$TMP'):
        """
        Deploy the class.

        Note that all request data in this class is kept in XML because it allows for an easier development in combination
        with the SAP ABAP Development Tools (ADT, Eclipse). In the communication log that can be viewed in the
        IDE everything is done in XML -> easier translation to this method.

        Parameters
        ----------
        class_name : str
            Name of the class.

        abap_class_code : str
            Code of SAP ABAP class.

        class_description : str, optional
            Description of the class.

            Defaults to None.

        master_system : str, optional
            Name of master system.
            Please enter the name of master system you are working on.

            Defaults to "ER9".

        force_overwrite : bool, optional
            whether to overwrite the class if class already exists.

            Defaults to False.

        transport_request : str, optional
            Name of the package.
            Please enter the name of package you are working on.

            Defaults to '$TMP'.


        """
        logger.info("Deploying class..")
        if class_description is None or class_description == '':
            class_description = "HEMI compatible class for predictive scenario"

        stateless_session, sl_csrf_token = AMDPDeployer._get_session(self.adt_url + "/oo/classes", self.__backend_auth)
        stateful_session, sf_csrf_token = AMDPDeployer._get_session(self.adt_url + "/oo/classes", self.__backend_auth)

        message = ElementTree.parse(
            os.path.join(os.path.dirname(__file__), 'template', 'ABAP_Create_Class_TEMPLATE.xml'))
        root = message.getroot()

        sap_adt_core = "{http://www.sap.com/adt/core}"

        root.attrib[sap_adt_core + "name"] = class_name
        root.attrib[sap_adt_core + "description"] = class_description
        root.attrib[sap_adt_core + "masterSystem"] = master_system
        # Set transport request
        root.findall('*')[0].attrib[sap_adt_core + 'name'] = transport_request
        # Set responsible person to user
        root.attrib[sap_adt_core + "responsible"] = self.__backend_auth[0]

        logger.debug("Creating new, empty class.")
        response = stateless_session.post(
            url=self.adt_url + "/oo/classes",
            headers=self._get_headers(sl_csrf_token, content_type="application/xml"),
            data=ElementTree.tostring(root),
            verify=False)

        # If class already exists
        if response.status_code != 200 and not force_overwrite:
            stateless_session.close()
            stateful_session.close()
            message = self._parse_xml_error_message(response.text)
            raise ValueError("Error when creating class: " + message)

        logger.debug("Acquiring lock on class.")
        response = stateful_session.post(
            url=self.adt_url + "/oo/classes/{}?_action=LOCK&accessMode=MODIFY".format(class_name),
            headers={
                "Accept": "application/vnd.sap.as+xml;charset=UTF-8;dataname=com.sap.adt.lock.result;q=0.8, " +
                          "application/vnd.sap.as+xml;charset=UTF-8;dataname=com.sap.adt.lock.result2;q=0.9",
                "Content-type": "application/xml",
                "X-sap-adt-profiling": "server-time",
                "x-csrf-token": sf_csrf_token,
                "X-sap-adt-sessiontype": "stateful"
            },
            data=ElementTree.tostring(root),
            verify=False)

        if response.status_code != 200:
            stateless_session.close()
            stateful_session.close()
            message = self._parse_xml_error_message(response.text)
            raise ValueError("Error when acquiring lock on class: " + message)

        lock_handle = ElementTree.fromstring(response.text).find(
            "{http://www.sap.com/abapxml}values/DATA/LOCK_HANDLE").text

        logger.debug("Inserting source code into class.")
        response = stateless_session.put(
            url=self.adt_url + "/oo/classes/{}/source/main?lockHandle={}".format(class_name, lock_handle),
            headers={
                "X-sap-adt-profiling": "server-time",
                "x-csrf-token": sl_csrf_token,
                "Content-type": "text/plain; charset=utf-8",
                "Accept": "text/plain",
            },
            data=abap_class_code.encode('utf-8'),
            verify=False)

        if response.status_code != 200:
            message = self._parse_xml_error_message(response.text)
            stateful_session.post(
                url=self.adt_url + "/oo/classes/{}?_action=UNLOCK&lockHandle={}".format(class_name, lock_handle),
                headers=self._get_headers(sf_csrf_token),
                verify=False)
            stateless_session.close()
            stateful_session.close()
            raise ValueError("Error when inserting source code into class: " + message)

        message = ElementTree.parse(
            os.path.join(os.path.dirname(__file__), 'template', 'ABAP_Activate_Class_TEMPLATE.xml'))
        root = message.getroot()
        root.find(sap_adt_core + "objectReference").attrib[sap_adt_core + "uri"] = \
            "/sap/bc/adt/oo/classes/{}".format(class_name.lower())
        root.find(sap_adt_core + "objectReference").attrib[sap_adt_core + "name"] = class_name

        logger.debug("Unlocking class.")
        response = stateful_session.post(
            url=self.adt_url + "/oo/classes/{}?_action=UNLOCK&lockHandle={}".format(class_name, lock_handle),
            headers=self._get_headers(sf_csrf_token),
            verify=False)

        if response.status_code != 200:
            stateless_session.close()
            stateful_session.close()
            message = self._parse_xml_error_message(response.text)
            raise ValueError("Error when unlocking class: " + message)

        logger.debug("Activating class.")
        response = stateless_session.post(
            url=self.adt_url + "/activation?method=activate&preauditRequested=true",
            headers=self._get_headers(sl_csrf_token),
            data=ElementTree.tostring(root),
            verify=False)

        if response.status_code != 200:
            stateless_session.close()
            stateful_session.close()
            message = self._parse_xml_error_message(response.text)
            raise ValueError("Error when activation class: " + message)

        stateless_session.close()
        stateful_session.close()

    def register_islm(self, class_name, model_name, catalog, scenario_name, scenario_type, scenario_description,
                      sap_client):
        """
        Register in Intelligent Scenario Lifecycle Management (ISLM).

        Parameters
        ----------
        class_name : str
            Name of the class.

        model_name : str
            Name of the model.

        catalog : str
            Name of the catalog.

        scenario_name : str
            Name of the intelligent scenario.

        scenario_type : str
            Type of the intelligent scenario.

        scenario_description : str
            Description of the intelligent scenario.

        sap_client : str
            The client of SAP.

        """
        sess, csrf_token = AMDPDeployer._get_session(self.islm_url, self.__frontend_auth)

        json_content = {
            "Name": scenario_name,
            "Description": scenario_description,
            "ScenarioType": scenario_type,
            "Models": [{
                "Name": model_name,
                "Definition": json.dumps({
                    "Hemi": {
                        "Class": class_name,
                        "ModelType": scenario_type
                    }
                }),
                "ModelType": scenario_type,
                "EntityDetails": [{
                    "Key": "adapter",
                    "Value": "UMML4HANA/SQL"
                }]
            }],
            "ScenarioTech": "EMBEDDED",
            "ObjectName": "",
            "Extensible": True
        }
        tries = 0
        while True:
            tries += 1
            response = sess.post(self.islm_url + "/Catalogs('{}')/IntelligentScenarios?sap-client={}".format(catalog,
                                                                                                             sap_client),
                                 headers=self._get_headers(csrf_token),
                                 data=json.dumps(json_content),
                                 verify=False)
            if response.status_code != 201:
                time.sleep(10)
                if tries >= 4:
                    message = self._parse_json_error_message(response.text)
                    sess.close()
                    raise ValueError("Could not register scenario in ISLM: " + message)
            else:
                break
        sess.close()
        return json.loads(response.text)['d']['GUID']

    def get_is_information_from_islm(self, scenario_name, sap_client):
        """
        Get Intelligent Scenario Lifecycle Management (ISLM) information.

        Parameters
        ----------
        scenario_name : str
            Name of the intelligent scenario.

        sap_client : str
            The client of SAP.

        """
        sess, csrf_token = AMDPDeployer._get_session(self.islm_url, self.__frontend_auth)

        response = sess.get(
            self.islm_url + "/IntelligentScenarios?$filter=%20Name%20eq%20%27{}%27&sap-client={}&$format=json".
            format(scenario_name, sap_client),
            headers=self._get_headers(csrf_token),
            auth=self.__frontend_auth)

        if response.status_code != 200:
            message = self._parse_json_error_message(response.text)
            sess.close()
            raise ValueError("Could not get predictive scenario information from ISLM: " + message)

        # Only copy over relevant parts
        content = json.loads(response.text)['d']['results']
        if len(content) < 1:
            sess.close()
            logger.warning("No scenario found with name: {}".format(scenario_name))
            return None
        content = content[0]
        info = {
            "Name": content["Name"],
            "Description": content["Description"],
            "ParentGUID": content["ParentGUID"],
            "Signature": content["Signature"],
            "Bindings": content["Bindings"],
            "GUID": content["GUID"]
        }

        # Check for empty values
        if info["Description"] is None:
            info["Description"] = ""
        sess.close()
        return info

    def publish_islm(self, scenario_name, train_cds=None, apply_cds=None, sap_client='000'):
        """
        Publish the scenario in the Intelligent Scenario Lifecycle Management (ISLM).

        Parameters
        ----------
        scenario_name : str
            Name of the intelligent scenario.

        train_cds : str, optional
            SAP ABAP Core Data Services (CDS) View for training.

            Defaults to None.

        apply_cds : str, optinal
            SAP ABAP Core Data Services (CDS) View for applying.

            Defaults to None.

        sap_client : str, optional
            The client of SAP.
            Please enter the name of client you are using.

            Defaults to '000'.

        """
        raise AttributeError
        sess, csrf_token = AMDPDeployer._get_session(self.islm_url, self.__frontend_auth)

        info = self.get_is_information_from_islm(scenario_name, sap_client)
        if info is None:
            sess.close()
            return None

        bindings = json.loads(info["Bindings"])
        if train_cds is not None:
            bindings["Inputs"].append({
                "Name": "[Train]IT_DATA",
                "Reference": train_cds
            })
        if apply_cds is not None:
            bindings["Inputs"].append({
                "Name": "[Apply]IT_DATA",
                "Reference": apply_cds
            })

        bindings = json.dumps(bindings)

        info["Bindings"] = bindings
        response = sess.put(
            self.islm_url + "/IntelligentScenarios(%27{}%27)?sap-client={}".format(info['GUID'], sap_client),
            headers=self._get_headers(csrf_token),
            data=json.dumps(info))

        if response.status_code != 204:
            message = self._parse_json_error_message(response.text)
            sess.close()
            raise ValueError("Could not change predictive scenario data bindings in ISLM: " + message)

        info = self.get_is_information_from_islm(scenario_name, sap_client)
        if info is None:
            sess.close()
            return None

        target_column_name = ''
        signature = json.loads(info['Signature'])
        for column in signature['Inputs'][0]['Structure']:
            if column['Type'] == 'Target':
                target_column_name = column['Name']
        for column in signature['Outputs'][0]['Structure']:
            if column['Storage']['DataElement'] == '':
                column['Storage']['DataElement'] = train_cds + '-' + target_column_name
        info['Signature'] = json.dumps(signature)
        response = sess.put(
            self.islm_url + "/IntelligentScenarios(%27{}%27)?sap-client={}".format(info['GUID'], sap_client),
            headers=self._get_headers(csrf_token),
            data=json.dumps(info))

        if response.status_code != 204:
            message = self._parse_json_error_message(response.text)
            sess.close()
            raise ValueError("Could not change predictive scenario data bindings in ISLM: " + message)

        response = sess.post(
            self.islm_url + "/Finalise?sap-client={}&GUID=%27{}%27&Transport=%27%27".format(sap_client, info['GUID']),
            headers=self._get_headers(csrf_token))

        if response.status_code != 200:
            message = self._parse_json_error_message(response.text)
            sess.close()
            raise ValueError("Could not finalise predictive scenario in ISLM: " + message)
        else:
            sess.close()
        return info

    def train_islm(self, model_name, model_description, scenario_name, sap_client):
        """
        Train the model in Intelligent Scenario Lifecycle Management (ISLM).

        Parameters
        ----------
        model_name : str
            Name of the model.

        model_description : str
            Description of the model.

        scenario_name : str
            Name of the scenario.

        sap_client : str
            The client of SAP.

        """
        raise AttributeError
        info = self.get_is_information_from_islm(scenario_name, sap_client)
        if info is None:
            return

        sess, csrf_token = AMDPDeployer._get_session(self.islm_url, self.__frontend_auth)

        # Get the guid corresponding to the ModelingContext of the PS
        response = sess.get(self.islm_train_url + "/ModelingContexts?sap-client={}&$filter=Parent%20eq%20%27{}%27".
                            format(sap_client, scenario_name),
                            headers=self._get_headers(csrf_token))
        if response.status_code != 200:
            sess.close()
            raise Exception(response.text)
        else:
            try:
                guid = response.json()['d']['results'][0]['GUID']
            except (KeyError, IndexError, ValueError):
                raise Exception("Malformed json response")

        # Get the guid of the concrete Model
        response = sess.get(self.islm_train_url + "/Models?sap-client={}&$filter=Parent%20eq%20%27{}%27&$format=json".
                            format(sap_client, guid),
                            headers=self._get_headers(csrf_token))

        if response.status_code != 200:
            sess.close()
            raise Exception(response.text)
        else:
            try:
                guid = response.json()['d']['results'][0]['GUID']
            except (KeyError, IndexError, ValueError):
                sess.close()
                raise Exception("Malformed json response")
        if model_description is None:
            model_description = "Modelversion trained with {}".format(model_name)
        # Construct the model json to create the task for training
        model = {
            "Name": model_name,
            "Description": model_description,
            "TaskType": "Train",
            "ParentGUID": scenario_name,
            "Bindings": info["Bindings"],
            "ReferenceGUID": guid
        }

        time.sleep(30)
        response = sess.post(
            self.islm_train_url + "/Tasks?sap-client={}".format(sap_client),
            headers=self._get_headers(csrf_token),
            data=json.dumps(model))

        if response.status_code != 201:
            sess.close()
            raise Exception(response.text)
        additional_info = None
        while additional_info is None:
            time.sleep(10)
            response = sess.get(self.islm_train_url + "/ModelVersions?sap-client={}&$filter=Parent%20eq%20%27{}%27&$format=json".
                                format(sap_client, guid),
                                headers=self._get_headers(csrf_token))
            if response.status_code != 200:
                sess.close()
                raise Exception(response.text)
            else:
                try:
                    version = response.json()['d']['results'][0]
                    if version['Status'] == 'ready':
                        additional_info = version['AdditionalInfo']
                    elif version['Status'] == 'error':
                        raise Exception("Training error")
                except (KeyError, IndexError, ValueError):
                    raise Exception("Malformed json response")
        sess.close()
        try:
            return json.loads(additional_info)
        except:
            return additional_info

    def delete_islm(self, scenario_name, sap_client):
        """
        Delete the scenario in Intelligent Scenario Lifecycle Management (ISLM).

        Parameters
        ----------
        scenario_name : str
            Name of the intelligent scenario.

        sap_client : str
            The client of SAP.


        """
        info = self.get_is_information_from_islm(scenario_name, sap_client)
        if info is None:
            return

        sess, csrf_token = AMDPDeployer._get_session(self.islm_url, self.__frontend_auth)
        response = sess.delete(self.islm_url +
                               "/IntelligentScenarios('{}')?sap-client={}".format(info['GUID'], sap_client, ),
                               headers=self._get_headers(csrf_token))
        if response.status_code != 204:
            sess.close()
            raise Exception(response.text)
        sess.close()

    def format(self, abap_class_code, master_system):
        """
        Format from AMDP session.

        Parameters
        ----------
        abap_class_code : str
            Code of SAP ABAP class.

        master_system : str
            Name of master system.

        """
        sess, csrf_token = AMDPDeployer._get_session(self.adt_url + '/abapsource/prettyprinter', self.__backend_auth)
        response = sess.post(self.adt_url + '/abapsource/prettyprinter',
                             headers=self._get_headers(csrf_token,
                                                       'text/plain',
                                                       'text/plain'),
                             data=abap_class_code.encode('utf-8'))
        # if response.status_code != 200:
        #     sess.close()
        #     raise Exception(response.text)
        sess.close()
        return response.text
