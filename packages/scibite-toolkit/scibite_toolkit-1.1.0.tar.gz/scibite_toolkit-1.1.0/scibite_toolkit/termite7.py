import requests
import logging
import pandas as pd
import re
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Console handler
                        logging.FileHandler('termite7_module.log', mode='w')  # File handler
                    ])

class Termite7RequestBuilder:
    """
    Class for creating TERMite 7 Requests
    """

    def __init__(self, timeout: int = 60, log_level: str = 'WARNING'):
        """
        Initialize the Termite7RequestBuilder.

        Parameters
        ----------
        timeout : int, optional
            The timeout for HTTP requests in seconds (default is 60 seconds).
        log_level : str, optional
            The logging level to use (default is 'WARNING').
            Accepts: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
        """
        self.session = requests.Session()
        self.url = ''
        self.file_input = None
        self.headers = {}
        self.verify_request = False
        self.timeout = timeout
        self.settings = {}

        level = getattr(logging, log_level.upper(), logging.WARNING)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

    def set_oauth2(self, client_id, username, password, verification=True):
        """
        Passes username and password for the TERMite 7 token API to generate an access token
        and adds it to the request header.

        Parameters
        ----------
        client_id : str
            The client ID to access the token API.
        username : str
            The TERMite 7 username.
        password : str
            The TERMite 7 password for the provided username.
        verification : bool, optional
            Whether to verify SSL certificate (default is True).
        """
        timeout = 10
        token_address = f"{self.url}/auth/realms/Scibite/protocol/openid-connect/token"

        # Log the token request details
        self.logger.info(f"Attempting to authenticate to {token_address} for user {username}")

        try:
            req = self.session.post(token_address,
                                    data={
                                        "grant_type": "password",
                                        "client_id": client_id,
                                        "username": username,
                                        "password": password
                                    },
                                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                                    timeout=timeout,
                                    verify=verification)  # Use the verification flag

            req.raise_for_status()  # Raise an HTTPError if the response was unsuccessful

            # Log the successful request
            self.logger.info("Authentication successful")

            access_token = req.json().get("access_token")
            if not access_token:
                # Log the error instead of just raising it
                self.logger.error("Failed to retrieve access token from the response")
                raise ValueError("Failed to retrieve access token")

            # Set headers and verification flag
            self.headers = {"Authorization": f"Bearer {access_token}"}
            self.verify_request = verification

            # Log token reception
            self.logger.info("Access token retrieved and set in headers")

        except requests.exceptions.Timeout:
            # Log timeout-specific errors
            self.logger.error(f"Request timed out after {timeout} seconds")
        except requests.exceptions.RequestException as e:
            # Log generic request-related errors
            self.logger.error(f"Failed to authenticate due to a request error: {e}")
        except ValueError as ve:
            # Log errors related to missing or invalid access tokens
            self.logger.error(f"Value error: {ve}")

    def set_url(self, url):
        """
        Set the URL of the TERMite 7 instance.

        Parameters
        ----------
        url : str
            The URL of the TERMite 7 instance to be hit.
        """
        # Log the URL being set
        self.logger.info(f"Setting TERMite 7 URL to {url}")

        # Remove any trailing slash from the URL and set it
        self.url = url.rstrip('/')

        # Log the final URL after processing
        self.logger.info(f"TERMite 7 URL set to {self.url}")

    def set_text(self, text):
        """
        Set the text to be annotated.

        Parameters
        ----------
        text : str or list of str
            The text or list of text to annotate.

        Raises
        ------
        ValueError
            If the input is not a string or a list of strings.

        Notes
        -----
        If a single string is provided, it will be wrapped in a list.
        If a list of strings is provided, it will be used as-is.
        """
        if isinstance(text, str):
            self.logger.info("Received a single string. Wrapping it in a list.")
            self.settings["text"] = [text]
        elif isinstance(text, list) and all(isinstance(item, str) for item in text):
            self.logger.info("Received a list of strings.")
            self.settings["text"] = text
        else:
            self.logger.error("Invalid input: 'text' should be a string or a list of strings.")
            raise ValueError("Input should be a string or a list of strings.")

    def set_subsume(self, subsume):
        """
        Set the subsume option for entity annotation.

        This method determines whether to prioritize and return the longest entity match
        when an entity is recognized against multiple vocabularies (VOCabs). Enabling this
        option ensures that if an entity has overlapping matches in different vocabularies,
        only the longest match is returned.

        Parameters
        ----------
        subsume : bool, int, or str
            The subsume option:
            - If True (or equivalent input), the longest entity match is taken when an entity matches more than one vocabulary.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_subsume(True)
        Enables subsume, so the longest entity match is selected.

        >>> set_subsume(0)
        Disables subsume using an integer input.

        >>> set_subsume("true")
        Enables subsume using a string input.
        """

        # Coerce input to boolean
        if isinstance(subsume, bool):
            pass  # already correct type
        elif isinstance(subsume, int) and subsume in (0, 1):
            subsume = bool(subsume)
        elif isinstance(subsume, str) and subsume.lower() in ("true", "false"):
            subsume = subsume.lower() == "true"
        else:
            # Log invalid input before raising an exception
            logging.error(f"Invalid input for subsume: {subsume}")
            raise ValueError(f"Invalid input for subsume: {subsume}")

        # Set the value in settings
        self.settings["subsume"] = subsume

        # Log the change
        logging.info(f"Subsume set to {subsume}")

    def set_entities(self, vocabulary):
        """
        Limit the types of entities to be annotated by specifying vocabularies (VOCabs).

        This method restricts the annotations to a subset of entities based on the provided
        vocabularies (VOCabs). The input is a comma-separated string of entity types, which
        will be converted into a list of uppercase VOCab IDs. Each entity type is validated
        against the pattern [A-Z0-9_]. If any entity does not match the valid pattern, a
        warning is logged.

        Parameters
        ----------
        vocabulary : str
            A comma-separated string of entity types to limit annotations to, e.g., 'DRUG,INDICATION'.
            Each entity type will be stripped of extra spaces and converted to uppercase.

        Raises
        ------
        ValueError
            If the input is not a string or is empty.

        Notes
        -----
        - Valid VOCab IDs must match the pattern [A-Z0-9_].
        - Invalid VOCab IDs will not be included in the final list, and a warning will be logged.

        Examples
        --------
        >>> set_entities('DRUG, INDICATION')
        Restricts the annotation to the entities 'DRUG' and 'INDICATION'.

        >>> set_entities('DRUG,Invalid!Entity')
        Logs a warning for 'Invalid!Entity' and only 'DRUG' will be used.
        """
        valid_pattern = re.compile(r'^[A-Z0-9_]+$')

        entities = [v.strip().upper() for v in vocabulary.split(",")]

        # Validate each entity and log a warning if the pattern is not matched
        valid_entities = []
        for entity in entities:
            if valid_pattern.match(entity):
                valid_entities.append(entity)
                self.logger.info(f"The vocabulary '{entity}' will be used.")
            else:
                self.logger.warning(f"The vocabulary '{entity}' is invalid. Must match pattern [A-Z0-9_].")

        self.settings["vocabulary"] = valid_entities

    def set_caseMatch(self, caseMatch):
        """
        Set the caseMatch option to enforce case-sensitive entity matching.

        This method determines whether entities must match case exactly during annotation.
        Enabling this option will ensure that synonym matches are case-sensitive, meaning
        entities will only be recognized if the case of the input text matches exactly.
        This option is optional and defaults to False.

        Parameters
        ----------
        caseMatch : bool, int, or str
            The caseMatch option:
            - If True (or equivalent input), entities must match case exactly.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_caseMatch(True)
        Enables case-sensitive matching for entity synonyms.

        >>> set_caseMatch(0)
        Disables case-sensitive matching using an integer input.

        >>> set_caseMatch("true")
        Enables case-sensitive matching using a string input.
        """

        # Coerce input to boolean
        if isinstance(caseMatch, bool):
            pass  # already correct type
        elif isinstance(caseMatch, int) and caseMatch in (0, 1):
            caseMatch = bool(caseMatch)
        elif isinstance(caseMatch, str) and caseMatch.lower() in ("true", "false"):
            caseMatch = caseMatch.lower() == "true"
        else:
            # Log invalid input before raising an exception
            logging.error(f"Invalid input for caseMatch: {caseMatch}")
            raise ValueError(f"Invalid input for caseMatch: {caseMatch}")

        # Set the value in settings
        self.settings["caseMatch"] = caseMatch

        # Log the change
        logging.info(f"caseMatch set to {caseMatch}")

    def set_rejectAmbig(self, rejectAmbig):
        """
        Set the rejectAmbig option to handle ambiguous entity matches.

        This method determines whether entities that have ambiguous hits should be rejected
        during annotation. Enabling this option can help filter out potentially inaccurate
        annotations by excluding ambiguous entity matches. This option is optional and
        defaults to False.

        Parameters
        ----------
        rejectAmbig : bool, int, or str
            The rejectAmbig option:
            - If True (or equivalent input), ambiguous entity hits are rejected.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_rejectAmbig(True)
        Enables rejection of ambiguous entity matches.

        >>> set_rejectAmbig(1)
        Enables rejection using an integer input.

        >>> set_rejectAmbig("false")
        Disables rejection using a string input.
        """

        # Coerce input to boolean
        if isinstance(rejectAmbig, bool):
            pass  # already correct type
        elif isinstance(rejectAmbig, int) and rejectAmbig in (0, 1):
            rejectAmbig = bool(rejectAmbig)
        elif isinstance(rejectAmbig, str) and rejectAmbig.lower() in ("true", "false"):
            rejectAmbig = rejectAmbig.lower() == "true"
        else:
            # Log invalid input before raising an exception
            logging.error(f"Invalid input for rejectAmbig: {rejectAmbig}")
            raise ValueError(f"Invalid input for rejectAmbig: {rejectAmbig}")

        # Set the value in settings
        self.settings["rejectAmbig"] = rejectAmbig

        # Log the change
        logging.info(f"rejectAmbig set to {rejectAmbig}")

    def set_boost(self, boost):
        """
        Set the boost option to modify ambiguity and subsyn behavior.

        This method enables or disables the boost option, which determines whether
        any ambiguity and subsyn settings are switched off, treating them as full hits.
        This can be useful when more aggressive matching is desired.

        Parameters
        ----------
        boost : bool, int, or str
            The boost option:
            - If True (or equivalent input), subsyns are recognized as full hits.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_boost(True)
        Enables boost, treating subsyns as full hits.

        >>> set_boost(1)
        Enables boost with an integer input.

        >>> set_boost("false")
        Disables boost using a string input.
        """

        # Coerce input to boolean
        if isinstance(boost, bool):
            pass  # already correct type
        elif isinstance(boost, int) and boost in (0, 1):
            boost = bool(boost)
        elif isinstance(boost, str) and boost.lower() in ("true", "false"):
            boost = boost.lower() == "true"
        else:
            # Log invalid input before raising an exception
            logging.error(f"Invalid input for boost: {boost}")
            raise ValueError(f"Invalid input for boost: {boost}")

        # Set the value in settings
        self.settings["boost"] = boost

        # Log the change
        logging.info(f"boost set to {boost}")

    def set_entityIds(self, entityIds):
        """
        Set the entityIds option to filter annotations by Entity IDs.

        This method filters results to only include annotations that belong to the
        provided list of Entity IDs.

        Parameters
        ----------
        entityIds : list of str
            A list of Entity IDs to filter annotations. Each element in the list must be a string.
            - If an empty list is provided, no filtering will be applied (all annotations will be included).

        Raises
        ------
        ValueError
            If the input is not a list or if any element in the list is not a string.

        Examples
        --------
        >>> set_entityIds(["D006801", "U0002048"])
        Sets the entityIds to ["D006801", "U0002048"] to filter annotations by those IDs.

        >>> set_entityIds([])
        Sets an empty list, meaning no filtering will be applied.
        """

        # Validate input
        if not isinstance(entityIds, list):
            logging.error(f"Invalid input for entityIds: Expected a list, got {type(entityIds).__name__}")
            raise ValueError(f"Invalid input for entityIds: Expected a list, got {type(entityIds).__name__}")

        if not all(isinstance(i, str) for i in entityIds):
            logging.error(f"Invalid input for entityIds: All elements must be strings. Input: {entityIds}")
            raise ValueError("Invalid input for entityIds: All elements must be strings.")

        if not entityIds:  # Optional: Handle empty list case
            logging.warning("entityIds list is empty. No filtering will be applied.")

        # Set the value in settings
        self.settings["entityIds"] = entityIds

        # Log the change
        logging.info(f"entityIds set to {entityIds}")

    def set_ancestors(self, ancestors):
        """
        Set the ancestors option for filtering annotations.

        This method filters results to only include annotations for entities that are
        descendants of one of the specified taxonomy nodes.

        Parameters
        ----------
        ancestors : list of str
            A list of entity IDs representing taxonomy nodes to filter annotations.
            Each element in the list must be a string.
            - If an empty list is provided, no filtering will be applied (all annotations included).

        Raises
        ------
        ValueError
            If the input is not a list or if any element in the list is not a string.

        Examples
        --------
        >>> set_ancestors(["NCIT$NCIT_C8278", "HGNCGENE$GROUP397"])
        Sets the ancestors to ["NCIT$NCIT_C8278", "HGNCGENE$GROUP397"].

        >>> set_ancestors([])
        Sets an empty list, meaning no filtering will be applied.
        """

        # Validate input
        if not isinstance(ancestors, list):
            logging.error(f"Invalid input for ancestors: Expected a list, got {type(ancestors).__name__}")
            raise ValueError(f"Invalid input for ancestors: Expected a list, got {type(ancestors).__name__}")

        if not all(isinstance(i, str) for i in ancestors):
            logging.error(f"Invalid input for ancestors: All elements must be strings. Input: {ancestors}")
            raise ValueError("Invalid input for ancestors: All elements must be strings.")

        if not ancestors:  # Optional: Handle empty list case
            logging.warning("ancestors list is empty. No filtering will be applied.")

        # Set the value in settings
        self.settings["ancestors"] = ancestors

        # Log the change
        logging.info(f"ancestors set to {ancestors}")

    def set_bytePositions(self, bytePositions):
        """
        Set the bytePositions option to include byte offsets for entity locations.

        This method determines whether byte positions (in addition to character positions)
        for entity mentions should be included in the results. Enabling this option allows
        the system to return both character and byte offsets, but it may incur a performance
        penalty due to the additional computation required to calculate byte positions.

        Parameters
        ----------
        bytePositions : bool, int, or str
            The bytePositions option:
            - If True (or equivalent input), byte positions are included.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Notes
        -----
        Enabling byte positions may affect performance, as additional processing is required
        to compute byte offsets. Consider whether byte positions are necessary for your use case.

        Examples
        --------
        >>> set_bytePositions(True)
        Enables byte positions for entity mentions.

        >>> set_bytePositions(0)
        Disables byte positions using an integer input.

        >>> set_bytePositions("true")
        Enables byte positions using a string input.
        """

        # Coerce input to boolean
        if isinstance(bytePositions, bool):
            pass  # already correct type
        elif isinstance(bytePositions, int) and bytePositions in (0, 1):
            bytePositions = bool(bytePositions)
        elif isinstance(bytePositions, str) and bytePositions.lower() in ("true", "false"):
            bytePositions = bytePositions.lower() == "true"
        else:
            # Log invalid input before raising an exception
            logging.error(f"Invalid input for bytePositions: {bytePositions}")
            raise ValueError(f"Invalid input for bytePositions: {bytePositions}")

        # Set the value in settings
        self.settings["bytePositions"] = bytePositions

        # Log the change
        logging.info(f"bytePositions set to {bytePositions}")

    def annotate_text(self, **kwargs):
        """
        Sends an array of text strings or a single string to the TERMite /v1/annotate API and returns the resulting JSON.

        Parameters
        ----------
        text : str or list of str, optional
            A single string or an array of strings to be annotated. If not provided, falls back to `self.settings['text']`.
        vocabulary : str, optional
            Vocabulary or set of terms to use for the annotation. If not provided, defaults to `self.settings['vocabulary']`.
        caseMatch : bool, optional
            Whether to enforce case sensitivity when matching terms. If not provided, defaults to `self.settings['caseMatch']`.
        rejectAmbig : bool, optional
            Whether to reject ambiguous matches (if a term has multiple meanings). Defaults to `self.settings['rejectAmbig']`.
        boost : str, optional
            Boost specific entities in the annotation results. Defaults to `self.settings['boost']`.
        entityIds : list of str, optional
            Specific entity IDs to be boosted or used for annotations. Defaults to `self.settings['entityIds']`.
        ancestors : bool, optional
            Whether to include ancestors of the matched entities in the result. Defaults to `self.settings['ancestors']`.
        subsume : bool, optional
            Whether to allow larger terms to subsume smaller ones during matching. Defaults to `self.settings['subsume']`.
        bytePositions : bool, optional
            If True, returns the byte positions of the matched entities in the original text. Defaults to `self.settings['bytePositions']`.

        Returns
        -------
        dict or None
            The JSON response from the TERMite API if the request is successful. If the request fails, returns None.

        Raises
        ------
        ValueError
            If no text is provided and `self.settings['text']` is also not set.

        Examples
        --------
        Annotate a single string:
        >>> annotate_text(text="COVID-19 is a disease caused by SARS-CoV-2.")

        Annotate multiple strings:
        >>> annotate_text(text=["COVID-19 is caused by SARS-CoV-2.", "Influenza is caused by the flu virus."],
                          vocabulary="INDICATION",
                          caseMatch=True)

        Notes
        -----
        The method logs and handles HTTP and request errors, such as timeouts or invalid responses. Be sure to configure
        `self.settings` appropriately for defaults.
        """
        text = kwargs.get('text', self.settings.get('text'))
        vocabulary = kwargs.get('vocabulary', self.settings.get('vocabulary'))
        caseMatch = kwargs.get('caseMatch', self.settings.get('caseMatch'))
        rejectAmbig = kwargs.get('rejectAmbig', self.settings.get('rejectAmbig'))
        boost = kwargs.get('boost', self.settings.get('boost'))
        entityIds = kwargs.get('entityIds', self.settings.get('entityIds'))
        ancestors = kwargs.get('ancestors', self.settings.get('ancestors'))
        subsume = kwargs.get('subsume', self.settings.get('subsume'))
        bytePositions = kwargs.get('bytePositions', self.settings.get('bytePositions'))

        if text is None:
            text = self.settings.get('text')
            if text is None:
                raise ValueError("No text provided, and self.settings['text'] is not set.")

        # If text is a string, convert it to a list
        if isinstance(text, str):
            self.logger.info("Received a single string. Converting it to a list.")
            text = [text]

        # Validate that text is now a list of strings
        if not isinstance(text, list) or not all(isinstance(item, str) for item in text):
            self.logger.error("Invalid input: 'text' should be a string or a list of strings.")
            return None

        # Prepare the request endpoint and parameters
        annotate_endpoint = f"{self.url}/api/termite/v1/annotate"
        params = {
            'text': text
        }

        if vocabulary is not None:
            params['vocabulary'] = vocabulary
            self.logger.info(f"Vocab config: {vocabulary}")

        if caseMatch is not None:
            params['caseMatch'] = caseMatch
            self.logger.info(f"caseMatch config: {caseMatch}")

        if rejectAmbig is not None:
            params['rejectAmbig'] = rejectAmbig
            self.logger.info(f"rejectAmbig config: {rejectAmbig}")

        if boost is not None:
            params['boost'] = boost
            self.logger.info(f"boost config: {boost}")

        if entityIds is not None:
            params['entityIds'] = entityIds
            self.logger.info(f"entityIds config: {entityIds}")

        if ancestors is not None:
            params['ancestors'] = ancestors
            self.logger.info(f"ancestors config: {ancestors}")

        if subsume is not None:
            params['subsume'] = subsume
            self.logger.info(f"Subsume: {subsume}")

        if bytePositions is not None:
            params['bytePositions'] = bytePositions
            self.logger.info(f"BytePositions: {bytePositions}")

        # Log the request details
        self.logger.info(f"Sending annotation request to {annotate_endpoint} with text data")

        try:
            # Make the GET request
            req = self.session.get(annotate_endpoint, params=params, headers=self.headers, timeout=self.timeout)
            req.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

            # Log successful request
            self.logger.info("Text annotation request successful")

            # Return the raw JSON response
            return req.json()

        except requests.exceptions.Timeout:
            self.logger.error(f"Request to {annotate_endpoint} timed out after {self.timeout} seconds")
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred while annotating text: {http_err}")
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred while annotating text: {req_err}")
        except ValueError:
            self.logger.error("Failed to parse response as JSON")

        return None

    def set_file(self, input_file_path):
        """
        Set the file to be annotated by TERMite.

        This method sets a file for annotation by specifying its file path. The file is opened
        in binary mode and stored in the settings. If multiple files of the same type need to
        be annotated at once, they should be placed in a zip archive and specified as the input.

        Parameters
        ----------
        input_file_path : str
            The file path to the file that will be sent to TERMite for annotation.
            This can also be a zip archive if multiple files are to be scanned.

        Raises
        ------
        FileNotFoundError
            If the specified file path does not exist or cannot be opened.

        Examples
        --------
        >>> set_file("/path/to/file.txt")
        Prepares the specified file for TERMite annotation.

        >>> set_file("/path/to/files.zip")
        Prepares a zip archive of files for TERMite annotation.
        """
        if not os.path.exists(input_file_path):
            logging.error(f"File not found: {input_file_path}")
            raise FileNotFoundError(f"File not found: {input_file_path}")

        file_name = os.path.basename(input_file_path)

        # Open the file outside of the 'with' block so it can be used later
        file_obj = open(input_file_path, 'rb')

        # Store the open file object in settings
        self.settings['file'] = {"file": (file_name, file_obj)}

        # Log the file setting
        logging.info(f"File {file_name} set for annotation.")

    def set_parserId(self, parserId):
        """
        Set the parser to use when annotating documents with TERMite 7.

        Parameters
        ----------
        parserId : str
            The ID of the parser to use, e.g. 'generic', or 'xml'.
        """

        # Remove any trailing slash from the URL and set it
        self.settings['parserId'] = parserId

        # Log the final URL after processing
        self.logger.info(f"parserId set to {self.settings['parserId']}")

    def annotate_document(self, **kwargs):
        """
        Sends a document or collection of documents to the TERMite /v1/annotate API and returns the resulting JSON.

        Parameters
        ----------
        file : binary
            A document or zip archive of documents. If not provided, falls back to `self.settings['file']`.
        parserId : str, optional
            The ID of the parser to use. Default is 'generic'.
        vocabulary : str, optional
            Vocabulary or set of terms to use for the annotation. If not provided, defaults to `self.settings['vocabulary']`.
        caseMatch : bool, optional
            Whether to enforce case sensitivity when matching terms. If not provided, defaults to `self.settings['caseMatch']`.
        rejectAmbig : bool, optional
            Whether to reject ambiguous matches (if a term has multiple meanings). Defaults to `self.settings['rejectAmbig']`.
        boost : str, optional
            Boost specific entities in the annotation results. Defaults to `self.settings['boost']`.
        entityIds : list of str, optional
            Specific entity IDs to be boosted or used for annotations. Defaults to `self.settings['entityIds']`.
        ancestors : bool, optional
            Whether to include ancestors of the matched entities in the result. Defaults to `self.settings['ancestors']`.
        subsume : bool, optional
            Whether to allow larger terms to subsume smaller ones during matching. Defaults to `self.settings['subsume']`.
        bytePositions : bool, optional
            If True, returns the byte positions of the matched entities in the original text. Defaults to `self.settings['bytePositions']`.

        Returns
        -------
        dict or None
            The JSON response from the TERMite API if the request is successful. If the request fails, returns None.

        Raises
        ------
        ValueError
            If no text is provided and `self.settings['file']` is also not set.

        Examples
        --------
        Annotate a single document:
        >>> annotate_document(file="")

        Annotate multiple strings:
        >>> annotate_text(text=["COVID-19 is caused by SARS-CoV-2.", "Influenza is caused by the flu virus."],
                          vocabulary="INDICATION",
                          caseMatch=True)

        Notes
        -----
        The method logs and handles HTTP and request errors, such as timeouts or invalid responses. Be sure to configure
        `self.settings` appropriately for defaults.
        """
        file = kwargs.get('file', self.settings.get('file'))
        parserId = kwargs.get('parserId', self.settings.get('parserId'))
        vocabulary = kwargs.get('vocabulary', self.settings.get('vocabulary'))
        caseMatch = kwargs.get('caseMatch', self.settings.get('caseMatch'))
        rejectAmbig = kwargs.get('rejectAmbig', self.settings.get('rejectAmbig'))
        boost = kwargs.get('boost', self.settings.get('boost'))
        entityIds = kwargs.get('entityIds', self.settings.get('entityIds'))
        ancestors = kwargs.get('ancestors', self.settings.get('ancestors'))
        subsume = kwargs.get('subsume', self.settings.get('subsume'))
        bytePositions = kwargs.get('bytePositions', self.settings.get('bytePositions'))



        # Prepare the request endpoint and parameters
        annotate_endpoint = f"{self.url}/api/termite/v1/annotate"
        params = {}

        if parserId is not None:
            params['parserId'] = parserId
            self.logger.info(f"parserId config: {parserId}")

        if vocabulary is not None:
            params['vocabulary'] = vocabulary
            self.logger.info(f"Vocab config: {vocabulary}")

        if caseMatch is not None:
            params['caseMatch'] = caseMatch
            self.logger.info(f"caseMatch config: {caseMatch}")

        if rejectAmbig is not None:
            params['rejectAmbig'] = rejectAmbig
            self.logger.info(f"rejectAmbig config: {rejectAmbig}")

        if boost is not None:
            params['boost'] = boost
            self.logger.info(f"boost config: {boost}")

        if entityIds is not None:
            params['entityIds'] = entityIds
            self.logger.info(f"entityIds config: {entityIds}")

        if ancestors is not None:
            params['ancestors'] = ancestors
            self.logger.info(f"ancestors config: {ancestors}")

        if subsume is not None:
            params['subsume'] = subsume
            self.logger.info(f"Subsume: {subsume}")

        if bytePositions is not None:
            params['bytePositions'] = bytePositions
            self.logger.info(f"BytePositions: {bytePositions}")

        # Log the request details
        self.logger.info(f"Sending annotation request to {annotate_endpoint} with binary data")

        try:
            # Make the POST request
            req = self.session.post(annotate_endpoint, params=params, files=file, headers=self.headers, timeout=self.timeout)
            req.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

            # Log successful request
            self.logger.info("Document annotation request successful")

            # Return the raw JSON response
            return req.json()

        except requests.exceptions.Timeout:
            self.logger.error(f"Request to {annotate_endpoint} timed out after {self.timeout} seconds")
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred while annotating document: {http_err}")
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error occurred while annotating document: {req_err}")
        except ValueError:
            self.logger.error("Failed to parse response as JSON")

        return None

def get_system_status(url, headers, fields='*'):
    """
    Fetches system Status from the TERMite API.

    Returns
    -------
    dict or None
        The JSON response containing the vocabularies if successful, None otherwise.
    """
    status_endpoint = f"{url}/api/termite/v1/status?fields={fields}"

    # Log the request URL
    logging.info(f"Fetching status from {status_endpoint}")

    try:
        timeout = 4
        req = requests.get(status_endpoint, headers=headers)
        req.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

        # Log successful retrieval
        logging.info("Status fetched successfully")

        return req.json()

    except requests.exceptions.HTTPError as http_err:
        # Log HTTP error with detailed information
        logging.error(f"HTTP error occurred while fetching vocabularies: {http_err}")
    except requests.exceptions.Timeout:
        # Log timeout error
        logging.error(f"Request to {status_endpoint} timed out")
    except requests.exceptions.RequestException as err:
        # Log general request-related errors
        logging.error(f"Request error occurred while fetching vocabularies: {err}")
    except ValueError:
        # Log JSON parsing errors
        logging.error("Failed to parse response as JSON")

def get_vocabs(url, headers):
    """
    Fetches vocabularies from the TERMite API.

    Returns
    -------
    dict or None
        The JSON response containing the vocabularies if successful, None otherwise.
    """
    vocabs_endpoint = f"{url}/api/termite/v1/vocabularies?hasCurrentVocabularyFile=true"

    # Log the request URL
    logging.info(f"Fetching vocabularies from {vocabs_endpoint}")

    try:
        req = requests.get(vocabs_endpoint, headers=headers)
        req.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

        # Log successful retrieval
        logging.info("Vocabularies fetched successfully")

        return req.json()

    except requests.exceptions.HTTPError as http_err:
        # Log HTTP error with detailed information
        logging.error(f"HTTP error occurred while fetching vocabularies: {http_err}")
    except requests.exceptions.Timeout:
        # Log timeout error
        logging.error(f"Request to {vocabs_endpoint} timed out")
    except requests.exceptions.RequestException as err:
        # Log general request-related errors
        logging.error(f"Request error occurred while fetching vocabularies: {err}")
    except ValueError:
        # Log JSON parsing errors
        logging.error("Failed to parse response as JSON")

    return None

def get_parsers(url, headers):
    """
    Fetch parsers from the TERMite API.

    This function sends a GET request to the TERMite API to fetch available parsers. It
    handles various exceptions such as timeouts, HTTP errors, and JSON parsing errors,
    logging relevant information for each error type. If the request is successful,
    the response is returned as a dictionary.

    Parameters
    ----------
    url : str
        The base URL of the TERMite API.
    headers : dict
        A dictionary containing the HTTP headers to include with the request.

    Returns
    -------
    dict or None
        The JSON response from the API containing the available parsers if successful,
        or None if there is an error or the response cannot be parsed as JSON.

    Raises
    ------
    requests.exceptions.RequestException
        If a network-related error occurs during the request, such as a timeout, connection error,
        or invalid response.
    ValueError
        If the response cannot be parsed as JSON.

    Notes
    -----
    - Logs the process of fetching parsers, including any errors that occur.
    - Ensures that request-related errors and parsing issues are handled and logged appropriately.

    Examples
    --------
    >>> get_parsers("http://example.com", {"Authorization": "Bearer token"})
    Fetches parsers from the specified TERMite API endpoint using the provided headers.
    """
    parsers_endpoint = f"{url}/api/termite/v1/parsers"

    # Log the start of the parser fetching process
    logging.info(f"Fetching parsers from {parsers_endpoint}")

    try:
        req = requests.get(parsers_endpoint, headers=headers)
        req.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

        # Log successful retrieval
        logging.info("Parsers fetched successfully")

        return req.json()

    except requests.exceptions.Timeout:
        # Log timeout-specific errors
        logging.error(f"Request to {parsers_endpoint} timed out")
    except requests.exceptions.HTTPError as http_err:
        # Log HTTP error with detailed information
        logging.error(f"HTTP error occurred while fetching parsers: {http_err}")
    except requests.exceptions.RequestException as err:
        # Log general request-related errors
        logging.error(f"Request error occurred while fetching parsers: {err}")
    except ValueError:
        # Log JSON parsing errors
        logging.error("Failed to parse response as JSON")

    return None

def process_annotation_output(annotation_output):
    """
    Processes the annotation output and returns a pandas DataFrame with the entity id, name, publicUri, and number of occurrences.

    Parameters
    ----------
    annotation_output : dict
        The output from the TERMite annotation API.

    Returns
    -------
    pd.DataFrame
        A DataFrame listing entity id, name, publicUri, and number of occurrences.
    """
    included_entities = annotation_output.get("included", [])

    data = []

    for entity_group in included_entities:
        entities = entity_group.get("entities", [])
        for entity in entities:
            entity_id = entity.get("id", "N/A")
            entity_name = entity.get("name", "N/A")
            public_uri = entity.get("publicUri", "N/A")
            num_occurrences = len(entity.get("occurrences", []))
            occurrences = entity.get('occurrences', [{}])[0]
            start_byte = occurrences.get('startByte')
            start_char = occurrences.get('startChar')

            data.append({
                "Entity ID": entity_id,
                "Name": entity_name,
                "Public URI": public_uri,
                "Occurrences": num_occurrences,
                "FirstStartChar": start_char,
                "FirstStartByte": start_byte,
            })

    # Create DataFrame
    df = pd.DataFrame(data, columns=["Entity ID", "Name", "Public URI", "Occurrences", "FirstStartChar", "FirstStartByte"])

    return df

def get_runtime_options(url, headers):
    """
    Lists runtime options
    """
    rtos_endpoint = f"{url}/api/termite/v1/runtime-options"

    try:
        req = requests.get(rtos_endpoint, headers=headers)
        req.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

        logging.info(f"Successfully fetched runtime options from {rtos_endpoint}")
        return req.json()

    except requests.exceptions.Timeout:
        # Log timeout-specific errors
        logging.error(f"Request to {rtos_endpoint} timed out")
    except requests.exceptions.HTTPError as http_err:
        # Log HTTP error with detailed information
        logging.error(f"HTTP error occurred while fetching runtime options: {http_err}")
    except requests.exceptions.RequestException as err:
        # Log general request-related errors
        logging.error(f"Request error occurred while fetching runtime options: {err}")
    except ValueError:
        # Log JSON parsing errors
        logging.error("Failed to parse response as JSON")