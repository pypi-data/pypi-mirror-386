from typing import Optional
from .base_api import ApiConfig, BaseApi
from .endpoints import (ProjectsApi, ResourcesApi, AnnotationsApi,
                        ChannelsApi, UsersApi, DatasetsInfoApi, ModelsApi,
                        AnnotationSetsApi
                        )
import datamint.configs
from datamint.exceptions import DatamintException


class Api:
    """Main API client that provides access to all endpoint handlers."""
    DEFAULT_SERVER_URL = 'https://api.datamint.io'
    DATAMINT_API_VENV_NAME = datamint.configs.ENV_VARS[datamint.configs.APIKEY_KEY]

    _API_MAP : dict[str, type[BaseApi]] = {
        'projects': ProjectsApi,
        'resources': ResourcesApi,
        'annotations': AnnotationsApi,
        'channels': ChannelsApi,
        'users': UsersApi,
        'datasets': DatasetsInfoApi,
        'models': ModelsApi,
        'annotationsets': AnnotationSetsApi,
    }

    def __init__(self,
                 server_url: str | None = None,
                 api_key: Optional[str] = None,
                 timeout: float = 60.0, max_retries: int = 2,
                 check_connection: bool = True) -> None:
        """Initialize the API client.

        Args:
            base_url: Base URL for the API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            client: Optional HTTP client instance
        """
        if server_url is None:
            server_url = datamint.configs.get_value(datamint.configs.APIURL_KEY)
            if server_url is None:
                server_url = Api.DEFAULT_SERVER_URL
        server_url = server_url.rstrip('/')
        if api_key is None:
            api_key = datamint.configs.get_value(datamint.configs.APIKEY_KEY)
            if api_key is None:
                msg = f"API key not provided! Use the environment variable " + \
                    f"{Api.DATAMINT_API_VENV_NAME} or pass it as an argument."
                raise DatamintException(msg)
        self.config = ApiConfig(
            server_url=server_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )
        self._client = None
        self._endpoints = {}
        if check_connection:
            self.check_connection()

    def check_connection(self):
        try:
            self.projects.get_list(limit=1)
        except Exception as e:
            raise DatamintException("Error connecting to the Datamint API." +
                                    f" Please check your api_key and/or other configurations. {e}")

    def _get_endpoint(self, name: str):
        if name not in self._endpoints:
            api_class = self._API_MAP[name]
            endpoint = api_class(self.config, self._client)
            # Inject this API instance into the endpoint so it can inject into entities
            endpoint._api_instance = self
            self._endpoints[name] = endpoint
        return self._endpoints[name]

    @property
    def projects(self) -> ProjectsApi:
        return self._get_endpoint('projects')

    @property
    def resources(self) -> ResourcesApi:
        return self._get_endpoint('resources')

    @property
    def annotations(self) -> AnnotationsApi:
        return self._get_endpoint('annotations')

    @property
    def channels(self) -> ChannelsApi:
        return self._get_endpoint('channels')

    @property
    def users(self) -> UsersApi:
        return self._get_endpoint('users')

    @property
    def _datasetsinfo(self) -> DatasetsInfoApi:
        """Internal property to access DatasetsInfoApi."""
        return self._get_endpoint('datasets')

    @property
    def models(self) -> ModelsApi:
        return self._get_endpoint('models')

    @property
    def annotationsets(self) -> AnnotationSetsApi:
        return self._get_endpoint('annotationsets')
