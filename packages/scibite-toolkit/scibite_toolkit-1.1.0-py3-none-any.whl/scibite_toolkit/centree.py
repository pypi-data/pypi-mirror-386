"""CENtree module from scibite-toolkit .

This module contains functionality to interact with the APIs
provided by CENTree.

Example
-------
This is a small example of a workflow using
the CENTree module::

    from scibite_toolkit import centree

    # Prepare the request object
    # You can obtain your token via your user setting's in the UI or programatically
    crb = centree.CentreeRequestBuilder(log_level='CRITICAL')
    crb.set_url(centree_url=your_server_url)
    crb.set_token(token=token)

    # Now you can use the request object to call over the CENTree API methods
    # For example, to search for classes:
    response = crb.search_classes(query='lung')

    

"""


import requests
import logging

# Get the logger for this module
logger = logging.getLogger(__name__)

class CentreeRequestBuilder:
    """
    Class for creating CENtree Requests.
    """

    def __init__(self, timeout: int = 10, verification: bool = True, log_level: str = "INFO"):
        """
        Initialize the CentreeRequestBuilder.

        Parameters
        ----------
        timeout : int, optional
            The timeout for HTTP requests in seconds (default is 10 seconds).
        verification : bool, optional
            Whether to verify SSL certificates (default is True).
        log_level : str, optional
            Logging level (default is "INFO"). Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
        """
        self.centree_url = ''
        self.headers = {}
        self.session = requests.Session()
        self.timeout = timeout
        self.verification = verification

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level.upper())
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def set_url(self, centree_url: str):
        """
        Set the URL of the CENtree instance.

        Parameters
        ----------
        centree_url : str
            The URL of the CENtree instance to be hit.

        Examples
        --------
        >>> crb.set_url("https://mycentree.company.com")
        """
        self.centree_url = centree_url.rstrip('/')
        self.logger.info(f"Set CENtree URL to {self.centree_url}")

    def set_authentication(self, username: str, password: str, remember_me: bool = True):
        """
        Authenticates with the CENtree token API using username and password, generates an access token,
        and sets the request header.

        Parameters
        ----------
        username : str
            The username for authentication.
        password : str
            The password for authentication.
        remember_me : bool, optional
            Whether to remember the user (default is True).

        Examples
        --------
        >>> crb.set_authentication("user", "pass")
        """
        authenticate_url = f"{self.centree_url}/api/authenticate"

        try:
            token_response = self.session.post(
                authenticate_url,
                json={
                    "rememberMe": remember_me,
                    "username": username,
                    "password": password,
                },
                headers={"Content-Type": "application/json"},
                verify=self.verification,
                timeout=self.timeout
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("id_token")

            if not access_token:
                raise ValueError("Access token not found in the response.")

            self.headers = {"Authorization": f"Bearer {access_token}"}
            self.logger.info("Authentication successful")

        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err

    def set_token(self, token: str):
        """
        Set an authentication token directly, without requiring username/password authentication.

        Parameters
        ----------
        token : str
            The authentication token.

        Examples
        --------
        >>> crb.set_token("your_existing_token")
        """
        if not token or not isinstance(token, str):
            raise ValueError("Invalid token: Token must be a non-empty string.")

        self.headers = {"Authorization": f"Bearer {token}"}
        self.logger.info("Token authentication set successfully.")

    def set_oauth2(self, client_id, client_secret):
        """
        Authenticates with the CENtree API using a clientID and secret, generates an access token,
        and sets the request header. For use in SaaS deployments.

        Parameters
        ----------
        client_id : str
            The username for authentication.
        client_secret : str
            The password for authentication.

        Examples
        --------
        >>> crb.set_oauth2("client_id", "client_secret")
        """

        token_url = f"{self.centree_url}/auth/realms/Scibite/protocol/openid-connect/token"

        try:
            token_response = self.session.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=self.verification,
                timeout=self.timeout
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")

            if not access_token:
                raise ValueError("Access token not found in the response.")

            self.headers = {"Authorization": f"Bearer {access_token}"}
            self.logger.info("Authentication successful")

        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err

    def search_classes_by_primary_id(self, class_primary_id, ontology_list=None):
        """
        Perform search across ontologies for classes whose primary id equals the supplied string.

        Parameters
        ----------
        class_primary_id : str
            The primary ID to search for (required).
        ontology_list : list of str, optional
            list of ontology IDs to filter the search for (optional).
        
        Returns
        -------
        dict
            The JSON response from the search endpoint.

        Raises
        ------
        requests.exceptions.SSLError
            If an SSL error occurs during the request.
        requests.exceptions.HTTPError
            If an HTTP error occurs during the request.
        requests.exceptions.RequestException
            If a general request exception occurs.
        Exception
            For any other exceptions that may occur.
        """

        params = {'q': class_primary_id}
    
        if ontology_list:
            params['ontology'] = ontology_list

        search_endpoint = f"{self.centree_url}/api/search/primaryId"

        try:
            response = self.session.get(
                search_endpoint,
                params=params,
                headers=self.headers,
                verify=self.verification,
                timeout=self.timeout
            )
            response.raise_for_status()
            self.logger.info(f"Search for primary ID '{class_primary_id}' successful")
            return response.json()

        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err

    def get_paths_from_root(self,class_primary_id='', ontology_id='', children_relation_max_size=50, maximum_number_of_paths=100):
        """
        Retrieve all paths from the root node to a specified class in a given ontology.

        Parameters
        ----------
        class_primary_id : str, optional
            The primary ID of the class for which to retrieve paths from the root. Default is an empty string.
        ontology_id : str, optional
            The ontology ID in which to search for the class. Default is an empty string.
        children_relation_max_size : int, optional
            The maximum number of children relations to consider at each node. Default is 50.
        maximum_number_of_paths : int, optional
            The maximum number of paths to return. Default is 100.

        Returns
        -------
        dict
            The JSON response containing the paths from the root to the specified class.

        Raises
        ------
        requests.exceptions.SSLError
            If an SSL error occurs during the request.
        requests.exceptions.HTTPError
            If an HTTP error occurs during the request.
        requests.exceptions.RequestException
            If a general request exception occurs.
        Exception
            For any other exceptions that may occur.
        """
        endpoint = f"{self.centree_url}/api/ontologies/{ontology_id}/classes/paths-from-root/simple"

        # Form the query parameters
        params = {
            "classPrimaryId": class_primary_id,
            "childrenRelationMaxSize": children_relation_max_size,
            "maximumNumberOfPaths": maximum_number_of_paths
        }

        try:
            response = self.session.get(endpoint,params=params,headers=self.headers,verify=self.verification,timeout=self.timeout)
            response.raise_for_status()
            self.logger.info("Get path from root request successful")
            return response.json()

        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err

    def search_classes(self, query: str, ontology_list: list = None, exact: bool = False, obsolete: bool = False, page_from: int = 0, page_size: int = 10) -> dict:

        """
        Search classes in CENtree ontologies.

        Parameters
        ----------
        query : str
            The search query.
        ontology_list : list, optional
            list of ontology IDs to filter the search for (optional).
        exact : bool, optional
            Whether to perform an exact search (default is False).
        obsolete : bool, optional
            Whether to include obsolete classes (default is False).
        page_from : int, optional
            The starting page number (default is 0).
        page_size : int, optional
            The number of results per page (default is 10).

        Returns
        -------
        dict
            The JSON response from the search endpoint.

        Examples
        --------
        >>> result = crb.search_classes("diabetes")
        """
        if ontology_list is None:
            ontology_list = []

        params = {
            "q": query,
            "ontology": ontology_list,
            "from": page_from,
            "size": page_size
        }

        # Clean up params dictionary to remove None values
        params = {k: v for k, v in params.items() if v is not None}

        # Construct the endpoint URL
        endpoint_suffix = ''
        if obsolete:
            endpoint_suffix += '/obsolete'
        if exact:
            endpoint_suffix += '/exact'

        search_endpoint = f"{self.centree_url}/api/search{endpoint_suffix}"

        try:
            response = self.session.get(
                search_endpoint,
                params=params,
                headers=self.headers,
                verify=self.verification,
                timeout=self.timeout
            )
            response.raise_for_status()
            self.logger.info("Search request successful")
            return response.json()

        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err
        
    def get_classes(self, ontology_id, size=10):
        """Get classes for a specific ontology.

        Parameters
        ----------
        ontology_id : str
            The ontology ID.
        size : int, optional
            The number of classes to retrieve, by default 10.
        """
        classes_endpoint = f"{self.centree_url}/api/ontologies/{ontology_id}/classes"
        params = {'size': size}
        try:
            response = self.session.get(
                classes_endpoint,
                params=params,
                headers=self.headers,
                verify=self.verification,
                timeout=self.timeout
            )
            response.raise_for_status()
            self.logger.info("Get request successful")
            return response.json()

        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err


    def filter_classes(self, classes, annotation_property):
        """
        Filters and returns only those classes that have the specified annotation property.

        Args:
            classes (dict or list): The classes data as returned from the API.
            annotation_property (str): The annotation property key to filter by.

        Returns:
            list: Filtered list of classes containing the annotation property.
        """
        # Handle if classes is a dict with 'elements' key (as per actual API response)
        if isinstance(classes, dict) and 'elements' in classes:
            class_list = classes['elements']
        else:
            class_list = classes

        self.logger.info(f"Number of classes before filtering: {len(class_list)}")

        filtered = []
        for cls in class_list:
            property_values = cls.get('propertyValues', [])
            matching_property = next((pv for pv in property_values if pv.get('name') == annotation_property and pv.get('value')), None)
            if matching_property:
                filtered.append({
                    'id': cls.get('id'),
                    'primaryID': cls.get('primaryID'),
                    'primaryLabel': cls.get('primaryLabel'),
                    'property': {
                        'name': matching_property.get('name'),
                        'iri': matching_property.get('iri'),
                        'value': matching_property.get('value')
                    }
                })

        self.logger.info(f"Number of classes after filtering: {len(filtered)}")
        return filtered

    def create_deletion_transaction(self, ontology_id, class_id, property_iri, property_value, transaction_id=None):
        delete_endpoint = f"{self.centree_url}/api/ontologies/{ontology_id}/classes/{class_id}/properties"
        payload = {"propertyIri": property_iri, "propertyValue": property_value}
        if transaction_id:
            payload["transactionId"] = transaction_id
        try:
            response = self.session.delete(delete_endpoint, json=payload, headers=self.headers, verify=self.verification, timeout=self.timeout)
            response.raise_for_status()
            self.logger.info("Delete request successful, transaction created")
            return response.json().get('transactionId')
        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err

    def commit_deletion_transaction(self, ontology_id, transaction_id):
        commit_endpoint = f"{self.centree_url}/api/ontologies/{ontology_id}/edits/transactions/{transaction_id}/commit"
        try:
            response = self.session.post(commit_endpoint, headers=self.headers)
            response.raise_for_status()
            self.logger.info("Commit request successful")
        except requests.exceptions.SSLError as ssl_err:
            self.logger.error(f"SSL error occurred:  {ssl_err}")
            raise ssl_err
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            raise err
