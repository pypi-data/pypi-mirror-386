"""Tiferet Monday Requests Proxy Settings"""

# *** imports

# ** core
from typing import (
    Dict,
    Any
)

# ** infra
from tiferet import raise_error
import requests

# *** constants

# ** constant: monday_api_version_header
MONDAY_API_VERSION_HEADER = 'API-Version'

# ** constant: monday_api_base_url
MONDAY_API_BASE_URL = 'https://api.monday.com/v2'

# * constant: complexity_budget_exhausted_error_code
COMPLEXITY_BUDGET_EXHAUSTED_ERROR_CODE = 'COMPLEXITY_BUDGET_EXHAUSTED'

# ** constant: monday_api_error_code
MONDAY_API_ERROR_CODE = 'MONDAY_API_ERROR'

# *** classes

# ** class monday_api_requests_proxy
class MondayApiRequestsProxy(object):
    """
    Proxy class for interacting with the Monday.com API.
    """

    # * attribute: api_key
    api_key: str

    # * init
    def __init__(self, monday_api_key: str):
        """
        Initializes the MondayApiProxy with the provided API key.

        :param monday_api_key: The API key for accessing the Monday.com API.
        :type monday_api_key: str
        """
        # Set the API key for the proxy.
        self.api_key = monday_api_key

    # * method: execute_query
    def execute_query(self, query: str, variables: Dict[str, Any] = {}, api_version: str = None, timeout: int = None, start_node = lambda data: data) -> Dict[str, Any]:
        """
        Executes a GraphQL query against the Monday.com API.

        :param api_key: The API key for accessing the Monday.com API.
        :type api_key: str
        :param query: The GraphQL query string.
        :type query: str
        :param variables: Variables to be used in the query.
        :type variables: Dict[str, Any]
        :param api_version: Optional API version to use.
        :type api_version: str
        :param timeout: Optional timeout for the request.
        :type timeout: int
        :param handle_response: Optional function to process the response data.
        :type handle_response: function
        :return: The response data from the API.
        :rtype: Dict[str, Any]
        """
        
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }

        # Add the API version to the headers if provided.
        if api_version:
            headers[MONDAY_API_VERSION_HEADER] = api_version

        # Execute the POST request to the Monday.com API.
        response = requests.post(
            url=MONDAY_API_BASE_URL,
            json={'query': query, 'variables': variables},
            headers=headers,
            timeout=timeout
        )
        
        # Handle and return the response data.
        return self.handle_response(
            response.json(),
            start_node=start_node
        )
    
    # * method: handle_response
    def handle_response(self, response: Dict[str, Any], start_node: lambda data: data) -> Any:
        """
        Handles the response from the Monday.com API.

        :param response: The response data from the API.
        :type response: Dict[str, Any]
        :param start_node: Optional function to process the start node of the response.
        :type start_node: function
        :return: The processed response data.
        :rtype: Any
        """
        # Check for errors in the response and raise an error if found.
        if 'errors' in response:
            
            # Retrieve the complexity limit error if present.
            complexity_limit_error = next((error for error in response['errors'] if self.is_complexity_budget_exhausted(error)), None)

            # Raise a monday API error if the error is not a complexity limit error.
            if not complexity_limit_error:
                raise_error.execute(MONDAY_API_ERROR_CODE, f'A Monday.com API error occurred: {str(response)}')

            # Raise a complexity budget exhausted error.
            raise_error.execute(
                COMPLEXITY_BUDGET_EXHAUSTED_ERROR_CODE, 
                str(response),
                complexity_limit_error.get('extensions', {}).get('retry_in_seconds', 60))
        
        # Return the start node of the response data.
        data = response.get('data', {})
        return start_node(data)
    
    # * method: is_complexity_budget_exhausted
    def is_complexity_budget_exhausted(self, error: Dict[str, Any]) -> bool:
        """
        Checks if the complexity budget has been exhausted based on the API response.

        :param response: The response data from the API.
        :type response: Dict[str, Any]
        :return: True if the complexity budget is exhausted, False otherwise.
        :rtype: bool
        """
        
        # Check if the error code matches the complexity budget exhausted code.
        return error.get('extensions', {}).get('code') == COMPLEXITY_BUDGET_EXHAUSTED_ERROR_CODE

