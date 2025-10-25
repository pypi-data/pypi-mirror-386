import httpx
import logging

logger = logging.getLogger(__name__)
# The default httpx logging level is INFO which spams the logs
# when otherwise trying to log script messages.
logger_httpx = logging.getLogger("httpx")
logger_httpx.setLevel(logging.WARNING)

class SessionManager:
    """
    Manages HTTP sessions and authentication for API requests to the Koordinates platform.

    Provides methods for making authenticated GET and POST requests, automatically injecting
    the API key into request headers and handling common HTTP errors.
    """

    def __init__(self, api_key: str, api_url: str, service_url: str, wfs_url: str):
        """
        Initializes the SessionManager with API credentials and endpoint URLs.

        Parameters:
            api_key (str): The API key for authentication.
            api_url (str): The base URL for the API.
            service_url (str): The base URL for service endpoints.
            wfs_url (str): The base URL for WFS endpoints.
        """
        self.api_key = api_key
        self.headers = {"Authorization": f"key {self.api_key}"}
        self.api_url = api_url
        self.service_url = service_url
        self.wfs_url = wfs_url

    def get(self, url: str, params: dict = None) -> dict:
        """
        Makes a synchronous GET request to the specified URL with the provided parameters.
        Injects the API key into the request headers.

        Parameters:
            url (str): The URL to send the GET request to.
            params (dict, optional): Query parameters to include in the request. Defaults to None.

        Returns:
            dict: The JSON-decoded response from the server.

        Raises:
            BadRequest: If the request fails with a 400 status code.
            ServerError: For other HTTP errors or request exceptions.
        """

        logger.debug(f"Making kserver GET request to {url} with params {params}")
        try:
            response = httpx.get(url, headers=self.headers, params=params, timeout=30)
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise ServerError(str(exc)) from exc

        if response.status_code == 400:
            raise BadRequest(response.text)
        response.raise_for_status()
        return response.json()

    def post(self, url, data=None, json=None, **kwargs):
        """
        Makes a synchronous POST request to the specified URL with the provided data or JSON.
        Injects the API key into the request headers.

        Parameters:
            url (str): The URL to send the POST request to.
            data (dict, optional): Form data to include in the request. Defaults to None.
            json (dict, optional): JSON data to include in the request. Defaults to None.

        Returns:
            dict: The JSON-decoded response from the server.

        Raises:
            BadRequest: If the request fails with a 400 status code.
            ServerError: For other HTTP errors or request exceptions.
        """

        logger.debug(f"Making kserver POST request to {url} with data {data} and json {json}")
        try:
            response = httpx.post(url, headers=self.headers, data=data, json=json, **kwargs)
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise ServerError(str(exc)) from exc

        if response.status_code == 400:
            raise BadRequest(response.text)
        response.raise_for_status()
        return response.json()

    def __repr__(self):
        return (
            f"SessionManager(api_url={self.api_url!r}, service_url={self.service_url!r}, "
            f"wfs_url={self.wfs_url!r}, api_key={'***' if self.api_key else None})"
        )

    def __str__(self):
        return (
            f"SessionManager for API: {self.api_url}, Service: {self.service_url}, WFS: {self.wfs_url}"
        )