"""SciBite Search module from scibite-toolkit .

This module contains functionality to interact with the various APIs
provided by SciBite Search (mostly Search API, Jobs API and Answers API).

Example
-------
This is a small example of a workflow using
the SciBite Search module::

    from scibite_toolkit import scibite_search

    # First authenticate
    # Examples provided assume our SaaS-hosted instances
    ss_home = 'https://yourdomain-search.saas.scibite.com/'
    sbs_auth_url = "https://yourdomain.saas.scibite.com/"
    client_id = "yourclientid"
    client_secret ="yourclientsecret"
    s = scibite_search.SBSRequestBuilder()
    s.set_url(ss_home)
    s.set_auth_url(sbs_auth_url)
    s.set_oauth2(client_id,client_secret) 
    #Authentication will last according to what
    #was was set up when generating the client

    # Now you can use the request object
    # to search over documents
    # This will bring the top 100 docs that mention 
    # that indication and any drug in the title
    sample_query = 'title~INDICATION$D011565 AND DRUG$*'
    response = s.get_docs(query=sample_query,markup=True,limit=100)
    
"""

import json

import requests
import re
import os
import sys
import pprint
import pandas as pd


class SBSRequestBuilder:
    """Class for creating SciBite Search requests.
    
    Request Builder object contains all the methods/functions that actually require a working connection to a SciBite Search server
    
    """

    def __init__(self):
        """ Initialize a new SBSRequestBuilder instance with default values.

        Attributes
        ----------
        url : str
            The main endpoint URL for the request.
        auth_url : str
            The URL used for authentication.
        token_url : str
            Attribute to hold the token URL.
        payload : dict
            The default payload for requests, with output format and method.
        options : dict
            Additional options for the request.
        basic_auth : tuple
            Empty initialise of basic_auth
        verify_request : bool
            Whether to verify the SSL certificate in requests. Will be used for all requests launched from this object.
        """
        self.url = ""
        self.auth_url = ""
        self.token_url = ""
        self.payload = {"output": "json", "method": "texpress"}
        self.options = {}
        self.basic_auth = ()
        self.verify_request = True
        self.headers = {}

    def set_oauth2_legacy(self, client_id, username, password, verification=True):
        """Legacy method to authenticate in SciBite Search versions < 2.2

        Passes username and password for the Scibite Search token api
        It then uses these credentials to generate an access token and adds
        this to the request header.

        Parameters
        ----------
        client_id: str, mandatory
            client_id to access the token api.
        username: str, mandatory
            scibite search username.
        password: str, mandatory
            scibite search password for username above.
        verification: bool (True) or str, optional and True by default. 
        How to perform verification on the requests that this object will raise. 
        - If set to True, it will verify the SSL certificate of the requests using the default paths.
        - If set to a string, it will use that string as the path to a CA_BUNDLE file or directory with certificates of trusted CAs.
        This is useful for self-signed certificates or custom CA bundles.
        - It can't be set to False, as in that case it will not verify the SSL certificate and will be insecure.


        Raises
        ------
        RuntimeError
            If the authentication fails, it raises a RuntimeError with the error message from the response.
        """
        if verification is False:
            raise ValueError("SSL verification cannot be set to False for security reasons.")

        if self.token_url != "":
            token_address = self.token_url + "/auth/realms/Scibite/protocol/openid-connect/token"
        # SaaS set up uses a different url for authentication
        elif self.auth_url != "":
            token_address = self.auth_url + "/auth/realms/Scibite/protocol/openid-connect/token"
        else:
            token_address = self.url + "/auth/realms/Scibite/protocol/openid-connect/token"

        req = requests.post(token_address, data={"grant_type": "password", "client_id": client_id, "username": username,
                                                 "password": password},
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                            verify=verification)
        resp_json = req.json()
        if "access_token" not in resp_json:
            raise RuntimeError(f"Authentication failed (status code {req.status_code}): {resp_json}")
        access_token = resp_json["access_token"]
        self.headers = {"Authorization": "Bearer " + access_token}
        self.verify_request = verification

    def set_oauth2(self, client_id, client_secret, verification=True):
        """Method to authenticate on SciBite Search versions >= 2.2

        Passes client id and client secret for the Scibite Search token api.
        It then uses these credentials to generate an access token and adds
        this to the request header.

        Parameters
        ----------
        client_id : str, mandatory
            scibite search client_id to access the token api
        client_secret : str, mandatory
            scibite search client_secret to access the token api
        verification: bool (True) or str, optional and True by default. 
            How to perform verification on the requests that this object will raise. 
            - If set to True, it will verify the SSL certificate of the requests using the default paths.
            - If set to a string, it will use that string as the path to a CA_BUNDLE file or directory with certificates of trusted CAs.
            This is useful for self-signed certificates or custom CA bundles.
            - It can't be set to False, as in that case it will not verify the SSL certificate and will be insecure.

        Raises
        ------
        RuntimeError
            If the authentication fails, it raises a RuntimeError with the error message from the response.
        """
        if verification is False:
            raise ValueError("SSL verification cannot be set to False for security reasons.")

        if self.token_url != "":
            token_address = self.token_url + "/auth/realms/Scibite/protocol/openid-connect/token"
        # SaaS set up uses a different url for authentication
        elif self.auth_url != "":
            token_address = self.auth_url + "/auth/realms/Scibite/protocol/openid-connect/token"
        else:
            token_address = self.url + "/auth/realms/Scibite/protocol/openid-connect/token"

        req = requests.post(token_address, data={"grant_type": "client_credentials", "client_id": client_id,
                                                 "client_secret": client_secret},
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                            verify=verification)
        resp_json = req.json()
        if "access_token" not in resp_json:
            raise RuntimeError(f"Authentication failed (status code {req.status_code}): {resp_json}")
        access_token = resp_json["access_token"]
        self.headers = {"Authorization": "Bearer " + access_token}
        self.verify_request = verification

    def set_token_url(self, token_url):
        """Set the URL for the token API.

        Parameters
        ----------
        token_url : str
            URL for the token API
        """
        self.token_url = token_url.rstrip('/')

    def set_url(self, url):
        """Set the URL of the Scibite Search instance.

        Parameters
        ----------
        url: str
            the URL of the Scibite Search instance to be hit.

        """
        self.url = url.rstrip('/')

    def set_auth_url(self, auth_url):
        """Set the URL of the Scibite Search instance.

        Parameters
        ----------
        url
            the auth URL of the Scibite Search instance to be hit. For SaaS instances only, this is different to the search url
        """
        self.auth_url = auth_url.rstrip('/')

    def get_docs(self, query='', markup=True, limit=20, offset=0, additional_fields=[]):
        """Calls the GET documents endpoint from SciBite Search API
        
        For calling the get docs endpoint for searching and retrieval of documents in SciBite Search.

        :query: SSQL query
        :type query: string
        :markup: Whether annotated text should markup the entities
        :type markup: bool
        :limit: Limits the number of results
        :type limit: int
        :offset: The number of resources to skip before returning results. Used for implementing paging.
        :type offset: int
        :additional_fields: Additional document fields to output in the response
        :type additional_fields: list of strings. If ['*'] it will get all fields from that doc schema.

        Parameters
        ----------
        query : str, optional
            a valid SSQL query, by default ''
        markup : bool, optional
            wheter the annotated text from the document should be returned with markup, by default True
        limit : int, optional
            number of resources to retrieve, by default 20
        offset : int, optional
            used for pagination in combination with limit, by default 0
        additional_fields : list, optional
            Additional document fields to output in the response. If ['*'] it will get all fields from that doc schema, by default []

        Returns
        -------
        JSON
            the JSON response from the GET documents call
        """
        options = {"markup": markup, "limit": limit, "offset": offset}
        if query:
            options["queries"] = query
        if additional_fields:
            options["fields"] = additional_fields

        try:
            req = requests.get(self.url + "/api/search/v1/documents", params=options, headers=self.headers,
                               verify=self.verify_request)
            req.raise_for_status()
            return req.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except ValueError:
            print("Response content is not valid JSON.")
            return None

    def get_entities(self, suggest_prefix="", entity_ids=None, synonym_name="", limit=20, include_vocabularies=None):
        """This function allows calling the GET entities endpoint from the Search API.
        
        if entity_ids is None:
        Parameters
        ----------
        suggest_prefix : str, optional
            the label of the entity you want to search for, by default ""
        entity_ids : list of str, optional
            a list of entity IDs (strings) of the form VOCAB$ID0000, by default []
        synonym_name : str, optional
            the exact synonym of the entity you want to search for, by default ""
        limit : int, optional
            maximum number of entities to retrieve, by default 20
        include_vocabularies : list of str, optional
            list of VOCABs (strings) in which to search for the entity, by default []
            the exact synonym of the entity you want to search for, by default ""
        limit : int, optional
            maximum number of entities to retrieve, by default 20
        include_vocabularies : list, optional
            list of VOCABs in which to search for the entity, by default []

        Returns
        -------
        JSON
            the JSON response from the GET entities endpoint

        Raises
        ------
        ValueError
            If none of the 3 search options are set up.
        """
        options = {"limit": limit}
        if suggest_prefix:
            options["suggestPrefix"] = suggest_prefix
        else:
            if entity_ids:
                options["entityIds"] = entity_ids
            else:
                if synonym_name != '':
                    options["synonymName"] = synonym_name
                else:
                    raise ValueError('You need to specify at least one of the following: suggest_prefix, entity_ids, or synonym_name')
        if include_vocabularies:
            options["includeVocabularies"] = include_vocabularies

        req = requests.get(self.url + "/api/search/v1/entities", params=options, headers=self.headers,
                           verify=self.verify_request)
        return req.json()

    
    def get_entity_tree_nodes(self, entity_id='', taxonomy='', limit=20, offset=0):
        
        """
        Sends a GET request to the SciBite JobServer 'entity-tree-nodes' endpoint
        to retrieve entity taxonomy tree from entity id.

        Parameters
        ----------
        entity_id : str
            Entity ID, by default ''.
        taxonomy : str
            Entity TAXONOMY, by default ''.
        limit : int, optional
            number of resources to retrieve, by default 20
        offset : int, optional
            used for pagination in combination with limit, by default 0    

        Returns
        -------
        dict
            The JSON response from the endpoint.
        """

        options = {'limit': limit, 'offset': offset}
        if entity_id:
            options['entityId'] = entity_id
        if taxonomy:
            options['taxonomy'] = taxonomy
            
        req = requests.get(
            f'{self.url}/api/search/v1/entity-tree-nodes/',
            params=options,
            headers=self.headers,
            verify=self.verify_request
        )
        
        return req.json()
    
    
    def delete_document(self,document_id):

        """
        Sends a DELETE request to remove a document from SciBite Search by its ID.

        Parameters
        ----------
        document_id : str
            The unique SciBite Search ID of the document to delete.

        Returns
        -------
        int
            The HTTP status code of the DELETE request.
        """
        
        req = requests.delete(f"{self.url}/api/search/v1/documents/{document_id}",headers = self.headers)
        return req.status_code
    
    
    def get_document(self, document_id, query='', markup=True):
        """This function calls to the GET document endpoint to retrieve a specific document by its id.

        Parameters
        ----------
        document_id : str
            required, the id of the document to be retrieved
        query : str, optional
            an SSQL query to apply to the document, by default ''
        markup : bool, optional
            wheter the annotated text from the document should be returned with markup, by default True

        Returns
        -------
        JSON
            the JSON response from the endpoint
        """
        options = {"markup": markup}
        if query:
            options["queries"] = query

        req = requests.get(self.url + "/api/search/v1/documents/" + document_id, params=options, headers=self.headers,
                           verify=self.verify_request)
        return req.json()

    def get_sentences(self, query='', markup=True, limit=20, offset=0):
        """Calls the GET sentences endpoint to query the sentence-level index from SciBite Search.

        Parameters
        ----------
        query : str, optional
            SSQL query, by default ''
        markup : bool, optional
            wheter the annotated text from the document should be returned with markup, by default True
        limit : int, optional
            number of resources to retrieve, by default 20
        offset : int, optional
            number of resources to skip before returning. Used for implementing paging, by default 0

        Returns
        -------
        JSON
            the JSON response from the endpoint
        """
        options = {"markup": markup, "limit": limit, "offset": offset}
        if query:
            options["queries"] = query

        req = requests.get(self.url + "/api/search/v1/sentences/", params=options, headers=self.headers,
                           verify=self.verify_request)
        return req.json()

    def get_searchlogs(self, limit=20, offset=0):
        """Call the GET searchlogs endpoint of the search usage API.

        Parameters
        ----------
        limit : int, optional
            Number of resources to retrieve, by default 20.
        offset : int, optional
            Number of resources to skip before returning. Used for implementing paging, by default 0.

        Returns
        -------
        JSON or None
            The JSON response from the endpoint, or None if an error occurs.

        Notes
        -----
        If a 403 Forbidden response is received, a message is printed indicating lack of authorization,
        and suggesting to check if the client has admin rights.
        """
        options = {"limit": limit, "offset": offset}
        try:
            req = requests.get(
                self.url + "/api/search-usage/v1/searchlogs",
                params=options,
                headers=self.headers,
                verify=self.verify_request
            )
            if req.status_code == 403:
                print("Not authorised to access search logs. Please check if your client has admin rights.")
                return None
            req.raise_for_status()
            return req.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def get_aggregates(self, query='', vocabs=[], sentences=True, significant=False, limit=20, offset=0):
        """Function to call aggregations endpoints from the Search API
        
        This function hits either the document or sentence aggregates API endpoints and returns aggregate counts for the provided query.
        It wraps calls to 4 different endpoints, depending on whether hitting sentence or document index and whether significance score needs to be used for the aggregation.

        Parameters
        ----------
        query : str, optional
            SSQL query, by default ''
        vocabs : list, optional
            list of vocabularies to select the entity counts from, by default []
        sentences : bool, optional
            True for sentence aggregates, False for document, by default True
        significant : bool, optional
            If true it uses and sorts by significance score, if false only by count, by default False
        limit : int, optional
            number of resources to retrieve, by default 20
        offset : int, optional
            number of resources to skip before returning. Used for implementing paging, by default 0

        Returns
        -------
        JSON
            the JSON response from the endpoint
        """
        options = {"limit": limit, "offset": offset, "includeVocabularies": vocabs}
        if query:
            options["queries"] = query
        if sentences:
            if significant:
                req = requests.get(self.url + "/api/search/v1/sentence-aggregates/significant-entity", params=options,
                                   headers=self.headers, verify=self.verify_request)
            else:
                req = requests.get(self.url + "/api/search/v1/sentence-aggregates/entity", params=options,
                                   headers=self.headers, verify=self.verify_request)
        else:
            if significant:
                req = requests.get(self.url + "/api/search/v1/document-aggregates/significant-entity", params=options,
                                   headers=self.headers, verify=self.verify_request)
            else:
                req = requests.get(self.url + "/api/search/v1/document-aggregates/entity", params=options,
                                   headers=self.headers, verify=self.verify_request)
        return req.json()

    def get_pipelines(self, datasetId='', limit=20, offset=0):
        """This endpoint calls the jobs API to get the description of a pipeline.

        Parameters
        ----------
        datasetId: str, optional
            filtering for pipelines that fill that datasetId.
        limit: int, optional
            number of resources to retrieve.
        offset: int, optional
            used for pagination in conjuction with the limit.
        """
        # options = {'datasetId':datasetId,'limit':limit,'offset':offset}
        # not sure why in this case limit and offset should be sent like that instead of options?
        # pending to implement datasetId
        req = requests.get(
            self.url + "/jobserver/jobs/v1/ingest-pipelines?limit=" + str(limit) + "&offset=" + str(offset),
            headers=self.headers, verify=self.verify_request)
        return req.json()

    def get_pipeline_by_id(self, id=''):
        """This endpoint calls the jobs API to get the description of a pipeline

        Parameters
        ----------
        id: str, mandatory
            the SciBite Search uuid for the pipeline you want to retrieve
        """
        if id:
            options = {"id": id}
        else:
            raise ValueError('You need to provide a string id for the pipeline to be obtained')

        # You first need to get the identifier using another endpoint
        # This is a first naive implementation without considering paging
        pipelines = self.get_pipelines()
        pipelines = pipelines['data']
        for i, pipeline_object in enumerate(pipelines):
            if pipeline_object['name'] == id:
                uuid = pipeline_object['id']
                req = requests.get(self.url + "/jobserver/jobs/v1/ingest-pipelines/" + uuid, params=options,
                                   headers=self.headers, verify=self.verify_request)
                return req.json()
        print('No pipeline was found with such name')

    def document_schemas(self, json_body):
        """This endpoint posts a new document schema to a ScibiteSearch instance
        :json_body: a valid JSON containing the new document schema with the correct fields
        :type json_body: JSON string"""
        headers = self.headers
        headers['Content-type'] = 'application/json'
        requests.post(self.url + '/api/search/v1/document-schemas', json=json_body, headers=headers,
                      verify=self.verify_request)


class SBSChat:
    """Class for handling SciBite Chat requests to the Answers API.

    """

    def __init__(self, instance_of_sbs):
        """Instantiation method for SBSChat object.

        Parameters
        ----------
        instance_of_sbs : SBSRequestBuilder
            An authenticated SBSRequestBuilder object.
        """
        self.conversation_id = ""
        self.SBS_instance = instance_of_sbs
        self.conversation_obj_list = []

    def start_conversation(self, question, num_candidates=10, filter_query='', rewrite_question=True):
        """Calls the post conversations endpoint from the Answers API. 
        
        Submit a question to start a new conversation for the authenticated user/client.
        The conversation objects will be saved to the class variable conversation_obj_list.

        Parameters
        ----------
        question : str, mandatory
            natural lenguage question to be submitted.
        num_candidates : int, optional
            number of documents to return to answer the question. Restricted by token limit, by default 10
        filter_query : str, optional
            SSQL query to filter documents returned to answer questions as needed, by default ''
            For example, you can filter documents that were published after 2022
            via "publish_date >= 2022-01-01"
        rewrite_question : bool, optional
            to indicate whether you want the system to rewrite the question, by default True
        """
        json_input_body = {
            "question": question,
            "candidates": num_candidates,
            "filterQuery": filter_query,
            "rewriteQuestion": rewrite_question
        }
        headers = self.SBS_instance.headers
        verify = self.SBS_instance.verify_request
        req = requests.post(self.SBS_instance.url + '/api/answer/v1/conversations', json=json_input_body,
                            verify=verify, headers=headers)

        self.conversation_obj_list = translate_resp_into_list(req)
        self.conversation_id = self.conversation_obj_list[0]['conversationId']

    def continue_conversation(self, question, num_candidates=10, filter_query='', rewrite_question=True,
                              conversation_id='', ):
        """Calls the post /conversations/{conversationId}/questions endpoint from the Answers API. 
        
        Given a conversation id (that was created by the authenticated user or client) 
        this method will submit a new question for that conversation. 
        The conversation objects will be saved to the class variable conversation_obj.list

        Parameters
        ----------
        question : str, mandatory
            natural lenguage question to be submitted.
        num_candidates : int, optional
            number of documents to return to answer the question. Restricted by token limit, by default 10
        filter_query : str, optional
            SSQL query to filter documents returned to answer questions as needed, by default ''
            For example, you can filter documents that were published after 2022
            via "publish_date >= 2022-01-01"
        rewrite_question : bool, optional
            to indicate whether you want the system to rewrite the question, by default True
        conversation_id : str, mandatory
            id of conversation you want to continue
        """
        json_input_body = {
            "question": question,
            "candidates": num_candidates,
            "filterQuery": filter_query,
            "rewriteQuestion": rewrite_question
        }
        if conversation_id != '':
            self.conversation_id = conversation_id
        headers = self.SBS_instance.headers
        verify = self.SBS_instance.verify_request

        req = requests.post(
            '{}/api/answer/v1/conversations/{}/questions'.format(self.SBS_instance.url, self.conversation_id),
            json=json_input_body, verify=verify, headers=headers)

        self.conversation_obj_list = translate_resp_into_list(req)
        self.conversation_id = self.conversation_obj_list[0]['conversationId']


def retrieve_conversation(conversation_id, sbs_request_builder_class):
    """Retrieve a cached conversation by its id.

    Parameters
    ----------
    conversation_id : str
        unique identifier for the conversation
    sbs_request_builder_class : SBSRequestBuilder Object
        object with the server set up

    Returns
    -------
    JSON
        JSON response from the conversation
    """
    url = sbs_request_builder_class.url
    headers = sbs_request_builder_class.headers
    verify = sbs_request_builder_class.verify_request
    req = requests.get('{}/api/answer/v1/conversations/{}'.format(url, conversation_id), headers=headers, verify=verify)
    try:
        if req.ok:
            return req.json()
        else:
            print('Error with input. ', req.text)
    except ValueError:
        print('No conversation found for logged in user with that conversation id. ', conversation_id)


def get_candidates(sbs_request_builder_class, question,filter_queries=[],strategy='SIMPLE', limit=20, markup=False, sort=[],fields=[]):
    """Wrapper for the get candidates endpoint from the Answers API.
    
    Parameters
    ----------
    sbs_request_builder_class : SBSRequestBuilder Object
        object with the server set up
    question : str, mandatory
        natural lenguage question to be submitted.
    filter_queries : list, optional
        list of str containing additional SSQL filters to perform on top of the question. Not used for relevance scoring., by default []
    strategy : str, optional
        Strategy to translate NL to SSQL. Defaults to 'SIMPLE'. Can also be 'OPENAI'
    limit : int, optional
        Maximum number of document candidates returned. Defaults to 20. Maximum value is 1000.
    markup : bool, optional
        wheter the annotated text from the document should be returned with markup, by default True
    sort : list, optional
        Set of sortable fields from the documents to use for ordering the pulled documents
    fields : list, optional
        Set of fields of the document to return, by default []

    Returns
    -------
    JSON
        the JSON response from the endpoint
    """
    # TODO: add all options from the endpoint in swagger
    # TODO: figure out sorting and strategy well
    options = {"textQuestion": question, "strategy": strategy, "limit": limit, "markup": markup}
    if fields!=[]:
        options["fields"]=fields
    if sort!=[]:
        options["sort"]=sort
    if filter_queries!=[]:
        options['filterQueries']=filter_queries
    

    req = requests.get(sbs_request_builder_class.url + "/api/answer/v1/candidates", params=options,
                       headers=sbs_request_builder_class.headers, verify=sbs_request_builder_class.verify_request)

    return req.json()



def get_conversations(sbs_request_builder_class):
    """Wrapper for the get conversations endpoint from the Answers API.
    
    Will return all conversations for the logged-in user of the SBS instance.
    If the logged-in user is a client (used in API calls), endpoint will return all conversations made by that client.
    Must pass an already authenticated SBS request builder class - no authentication is done in this method.

    @param sbs_request_builder_class: already authenticated instance of SBSRequestBuilder Class
    @return: list<dict> of conversations made by logged-in user

    Parameters
    ----------
    sbs_request_builder_class : SBSRequestBuilder Object
        object with the server set up

    Returns
    -------
    JSON
        the JSON data response from the endpoint
    """
    url = sbs_request_builder_class.url
    headers = sbs_request_builder_class.headers
    verify = sbs_request_builder_class.verify_request
    req = requests.get('{}/api/answer/v1/conversations'.format(url), headers=headers, verify=verify)

    conversations = req.json()['data']
    return conversations


def translate_resp_into_list(resp):
    """Splits the triple response into 3 JSON components

    """
    resp_text = resp.text
    try:
        # Split the API response into individual JSON strings
        json_strings = resp_text.split('\n')

        # Remove empty strings
        json_strings = [s for s in json_strings if s.strip()]

        # Parse each JSON string into a Python dictionary
        list_convo_objs = [json.loads(s[len('data:'):]) for s in json_strings]

        return list_convo_objs
    except:
        print('Error in response from SBS Chat.', resp_text)



def excel_to_json(input_excel_file, output_json_file):
    """Converts a table from excel into a JSON file

    Parameters
    ----------
    input_excel_file : str
        filepath to an existing excel format file
    output_json_file : str
        desired output filepath for the JSON that will be written
    """
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(input_excel_file)
    # Convert DataFrame to JSON
    json_data = df.to_json(orient='records')
    # Write JSON data to a file
    with open(output_json_file, 'w') as json_file:
        json_file.write(json_data)


def remove_markup_sbs(string_marked_up):
    """Function that given a marked up string it cleans it up and leave only the text.

    Parameters
    ----------
    string_marked_up : str
        the marked up string

    Returns
    -------
    str
        the clean-of-mark-up string
    """
    try:
        pattern_all_markup = re.compile(r'\[([^\]]+)\]\(([^\$]+)\$([^\)]+)\)')
        clean_string = re.sub(pattern_all_markup, lambda match: match.group(1), string_marked_up)
        return clean_string
    except:
        print('Error in the marked up string', string_marked_up)


def extract_bracketed_words(input_string):
    """Function to extract all the words between brackets in the input string.

    Parameters
    ----------
    input_string : str
        An input string.

    Returns
    -------
    list
        a list containing all of the words that were found between brackets
    """
    return re.findall(r'\[([^]]*)\]', input_string)


def findall_iter(sub, string):
    """Function to call string method find in an iterative manner. 

    Parameters
    ----------
    sub : str
        The string where to find.
    string : str
        The substring to match.
    """
    def next_index(length):
        index = 0 - length
        while True:
            index = string.find(sub, index + length)
            yield index

    return iter(next_index(len(sub)).__next__, -1)


# NOTE CM: need to make sure this can deal with multiple instances of the same string
def find_positions(main_string, words):
    """Finds the relative positions of the words in the main string.

    Parameters
    ----------
    main_string : str
        The string where those words are found.
    words : list
        The list of words for which we want to find the position.

    Returns
    -------
    list
        A list of lists, in which each element has the following structure:
        [word, (start_pos, end_pos)]
    """
    unique_words = set(words)
    positions = []
    for word in unique_words:
        return_findall = findall_iter(word, main_string)
        for instance_found in return_findall:
            start_pos = instance_found
            end_pos = start_pos + len(word)
            positions.append([word, (start_pos, end_pos)])
    return positions


def get_hit_positions_markup_sbs(string_marked_up, string_clean):
    """Function to get the hit positions from a string that contains SciBite Search markup annotations.

    Parameters
    ----------
    string_marked_up : str
        The string with markup.
    string_clean : str
        The string without markup.

    Returns
    -------
    list
        a list of dictionaries following the structure:
        {'term': str, 'type': str, 'id': str,
         'start': int, 'end': int}
    """
    pattern_hit_markup = re.compile(r'\[([^\]]+)\]\(_hit_term=([^\$]+)\$([^\)]+)\)')
    list_hit_words = []
    for match in pattern_hit_markup.finditer(string_marked_up):
        # extract word
        word_hit = match.group(1)
        # extract VOCAB
        vocab_hit = match.group(2)
        # Extract whole IDs matching
        term_id = match.group(3)
        # span
        # range_position = match.span()
        list_hit_words.append((word_hit, vocab_hit, term_id))

    # Get the bracketed words and their positions
    all_bracketed_words = extract_bracketed_words(string_marked_up)

    bracketed_words = []
    entity_dict = {}
    for ele in list_hit_words:
        if ele[0] in all_bracketed_words:
            bracketed_words.append(ele)
            entity_dict[ele[0]] = ele
    flat_bracketed_words = [word[0] for word in bracketed_words]
    positions = []
    positions = find_positions(string_clean, flat_bracketed_words)
    # print("Bracketed Words:", bracketed_words)
    # print("Bracketed Words flat:", flat_bracketed_words)
    # print("Positions in String2:", positions)
    # print('Entity dict',entity_dict)

    response_positions = []
    for i, pos in enumerate(positions):
        new_range = [pos[1][0], pos[1][1]]
        newpos = {'term': entity_dict[pos[0]][0], 'type': entity_dict[pos[0]][1], 'id': entity_dict[pos[0]][2],
                  'start': new_range[0], 'end': new_range[1]}
        response_positions.append(newpos)
    return response_positions


def translate_get_docs_response(response_to_process):
    """Transforms a get_docs response in JSON.
    
    This function takes a marked up json response from the get_docs endpoint from SciBite Search and generates, for
    every field that is annotated text, a marked up version, a clean version, and a dictionary with information about the
    hit positions

    Parameters
    ----------
    response_to_process : str
        JSON response from the get_docs endpoint

    Returns
    -------
    str
        The processed JSON response
    """
    # NOTE CLAUDIA: this is now hardcoding fields to skip because either are not text or are not annotated text
    # the best practice would be to be able to make a difference depending on doc schema and also get that live from
    # an up-do-date instance, taking only fields that are marked as annotated text
    fields_to_skip = ['schema_id', 'native_id', 'dataset_id', 'dataset', 'owner',
                      'source_uri', 'ingest_date', 'publish_date', 'job_execution_id',
                      'provenance', 'authors', 'entity_ids', 'vocabulary_codes',
                      'journal_volume', 'last_author', 'journal_issue', 'journal_issue_abbreviation',
                      'journal_iso_abbreviation', 'affiliations', 'issn', 'first_author',
                      'language', 'date_revised', 'journal_title', 'id', 'doi', '_links', '_score', '_snippets',
                      'org_duns', 'project_uri', 'org_state', 'core_project_number', 'org_zip_code',
                      'full_project_number',
                      'fiscal_year', 'support_year', 'secondary_outcomes', 'phase', 'primary_outcomes',
                      'number_of_arms',
                      'funding', 'location_countries', 'lead_sponsor', 'sponsors', 'enrollment',
                      'study_design', 'date_completed', 'org_study_id', 'study_type', 'study_first_submitted',
                      'eudract_id',
                      'program_officer_name', 'study_section', 'budget_end', 'study_section_name',
                      'total_cost', 'investigators', 'project_start', 'project_end', 'foa_number', 'budget_start',
                      'award_notice_date',
                      'is_fda_regulated_drug', 'corresponding_author', 'has_expanded_access', 'locations',
                      'other_outcomes', 'secondary_ids', 'references','mesh_headings','entity_frequency']
    # nested ones that we need to consider and are currently ignoring
    # all the outcomes ones
    list_nested = ['eligibility', 'arm_groups', 'interventions']
    list_nested_skip = ['minimum_age', 'type', 'study_pop', 'sampling_method', 'gender', 'healthy_volunteers',
                        'maximum_age', 'intervention_type', 'other_names', 'intervention_name']
    processed_response = []
    for i, doc in enumerate(response_to_process):
        new_doc_dict = {}
        fields_available = doc.keys()
        for j, field in enumerate(fields_available):
            if field not in fields_to_skip:
                if field in list_nested:
                    if field not in ['arm_groups', 'interventions']:
                        try:
                            keys_in_field = doc[field].keys()
                        except:
                            print('Error in field', field)
                        for sec_key in keys_in_field:
                            new_doc_dict[field] = {}
                            if sec_key not in list_nested_skip:
                                new_doc_dict[field][sec_key + '_marked_up'] = doc[field][sec_key]
                                try:
                                    clean_string = remove_markup_sbs(doc[field][sec_key])
                                except:
                                    print('Error in ', sec_key)
                                    print(doc[field][sec_key])
                                new_doc_dict[field][sec_key + '_clean'] = clean_string
                                response_positions = get_hit_positions_markup_sbs(doc[field][sec_key], clean_string)
                                new_doc_dict[field][sec_key + '_hits'] = response_positions
                        else:
                            new_doc_dict[field][sec_key] = doc[field][sec_key]
                    else:
                        # arm group case is a list
                        new_arm_list = []
                        for ind, ag in enumerate(doc[field]):
                            new_arm_dict = {}
                            for key_ag in ag.keys():
                                if key_ag not in list_nested_skip:
                                    try:
                                        clean_string = remove_markup_sbs(doc[field][ind][key_ag])
                                    except:
                                        print('Error in ', key_ag)
                                        print(doc[field][ind][key_ag])
                                    new_arm_dict[key_ag + '_marked_up'] = doc[field][ind][key_ag]
                                    new_arm_dict[key_ag + '_clean'] = clean_string
                                    # Now get the positions of those hits
                                    response_positions = get_hit_positions_markup_sbs(doc[field][ind][key_ag],
                                                                                      clean_string)
                                    new_arm_dict[key_ag + '_hits'] = response_positions
                                else:
                                    new_arm_dict[key_ag] = doc[field][ind][key_ag]
                            new_arm_list.append(new_arm_dict)
                        new_doc_dict[field] = new_arm_list
                else:
                    try:
                        clean_string = remove_markup_sbs(doc[field])
                        new_doc_dict[field + '_marked_up'] = doc[field]
                        new_doc_dict[field + '_clean'] = clean_string
                        # Now get the positions of those hits
                        response_positions = get_hit_positions_markup_sbs(doc[field], clean_string)
                        new_doc_dict[field + '_hits'] = response_positions
                    except:
                        print('\n Error in ' + field + ' field: ')
                        print(doc[field])
            else:
                new_doc_dict[field] = doc[field]
        processed_response.append(new_doc_dict)
    return processed_response


def translate_get_sentences_response(response):
    """Transforms a get_sentences response in JSON.
    
    This function takes a marked up json response from the get_sentences endpoint from SciBite Search and generates, for
    content field, a marked up version, a clean version, and a dictionary with information about the
    hit positions

    Parameters
    ----------
    response_to_process : str
        JSON response from the get_sentences endpoint

    Returns
    -------
    str
        The processed JSON response
    """
    processed_response = []
    for i, sent in enumerate(response):
        new_sent_dict = {}
        fields_available = sent.keys()
        # The only marked up content in sentences is the content field
        clean_string = remove_markup_sbs(sent['content'])
        new_sent_dict['content_marked_up'] = sent['content']
        new_sent_dict['content_clean'] = clean_string
        # Now get the positions of those hits
        response_positions = get_hit_positions_markup_sbs(sent['content'], clean_string)
        new_sent_dict['content_hits'] = response_positions
        # now add the remaining fields
        for field in fields_available:
            if field != 'content':
                new_sent_dict[field] = sent[field]
        processed_response.append(new_sent_dict)
    return processed_response


def process_s3_pipeline_log(sbs_ingestion_log):
    """Function to process the SciBite Search log of an S3 ingestion pipeline

    Parameters
    ----------
    sbs_ingestion_log : str
        the filepath to the log

    Returns
    -------
    list
        a list with the exception types and numbers
    """
    list_exceptions = []
    list_size_errors = []
    fichilog = open(sbs_ingestion_log, 'r')
    log_lines = fichilog.readlines()
    pattern_pipeline_exception = re.compile('PipelineException')
    pattern_encryption_dictionary = re.compile('PDF contains an encryption dictionary')
    pattern_invalid_entity = re.compile('Invalid Entity')  # typical with measure vocab
    pattern_end_of_file = re.compile('End-of-File')
    pattern_large_file = re.compile('File too large to process')
    for i, line in enumerate(log_lines):
        if pattern_pipeline_exception.search(line):
            # Check if encryption error
            if pattern_encryption_dictionary.search(line):
                type_error = 'encryption'
            # Check if entity invalid error
            elif pattern_invalid_entity.search(line):
                type_error = 'invalid_entity'
            elif pattern_end_of_file.search(line):
                type_error = 'end_of_file'
            elif pattern_large_file.search(line):
                type_error = 'file_too_large'
                size = line.split(' ')[-2]
                list_size_errors.append(size)
            # Now save into the list
            split_line = log_lines[i - 1].split(',')
            provenance_error = os.path.basename((split_line[-1].split('='))[-1].split('}')[0])
            list_exceptions.append((type_error, provenance_error))
    sorted_list_exceptions = sorted(list_exceptions)
    unique_list = set(sorted_list_exceptions)
    total = len(unique_list)
    # for instance_exception in unique_list:
    #       print(instance_exception[0]+','+instance_exception[1])
    # print('\nTotal number of unique exceptions is ',total)
    if len(list_size_errors) >= 1:
        largest_file = max(list_size_errors)
        # print('\nThe largest file of the set is '+largest_file+' MB long')
    return list_exceptions

def extract_entities(content):
    """Function to process the SciBite Search hits and extarct entities

    Parameters
    ----------
    content: str
        Marked up string coming from data['content']

    Returns
    -------
    JSON
        list of JSON of extarced entities and their types and ids
    """
    # Regular expression to match markups
    hit_pattern = r'\[([^\[\]]+)\]\(_hit_term=([^\)]+)\)'

    # Dictionary to store markups
    markups = {}

    # Find and process markups
    matches = list(re.finditer(hit_pattern, content))
    i = 0
    while i < len(matches):
        match = matches[i]
        word, markup = match.groups()
        start, end = match.span()

        # Check if the next match is consecutive
        if i + 1 < len(matches):
            next_match = matches[i + 1]
            next_word, next_markup = next_match.groups()
            next_start, next_end = next_match.span()

            if end == next_start - 1:  # Check if they are consecutive phrases
                word = f"{word} {next_word}"
                markup = f"{markup}&{next_markup}"
                end = next_end
                i += 1  # Skip the next match

        markup_type = markup.split('$', 1)

        if markup_type: #hits from vocabs
            if '&' in markup:
                markup_parts = markup.split('&')
                markup = [item for item in markup_parts]
                markups[word] = markup
            else: #hits from phrase search
                markups[word] = [markup]

        i += 1

    # Prepare the output JSON
    hits_json = {}
    hits_json.update(markups)

    return hits_json
