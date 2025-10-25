import logging

from google import genai
from google.genai.types import HttpOptions as GooogleHttpOptions

from dhenara.ai.providers.base import AIModelProviderClientBase
from dhenara.ai.providers.shared import APIProviderSharedFns
from dhenara.ai.types.genai.ai_model import AIModelAPIProviderEnum

from .formatter import GoogleFormatter

logger = logging.getLogger(__name__)


class GoogleAIClientBase(AIModelProviderClientBase):
    """Base class for all Google AI Clients"""

    formatter = GoogleFormatter

    def initialize(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def _get_client_params(self, api) -> tuple[str, dict]:
        """Common logic for both sync and async clients"""

        # _http_pars= self._get_client_http_params(api)
        _http_pars = {}
        timeout = int(self.config.timeout) * 1000 if self.config.timeout else None  # In milli seconds

        api_version = None  # Default in the SDK is `v1beta`
        if self.config.api_version_override:
            if self.config.api_version_override not in ["v1", "v1beta"]:
                raise ValueError(f"Unknonw API version {self.config.api_version_override}. Supported only v1 or v1bata")
            api_version = self.config.api_version_override

        if timeout or api_version:
            _http_pars["http_options"] = GooogleHttpOptions(
                timeout=timeout,
                api_version=api_version,
            )

        if api.provider == AIModelAPIProviderEnum.GOOGLE_AI:
            params = {
                "api_key": api.api_key,
                **_http_pars,
            }
            return "google_ai", params
        elif api.provider == AIModelAPIProviderEnum.GOOGLE_VERTEX_AI:
            client_params = APIProviderSharedFns.get_vertex_ai_credentials(api)
            params = {
                "vertexai": True,
                "credentials": client_params["credentials"],
                "project": client_params["project_id"],
                "location": client_params["location"],
                **_http_pars,
            }
            return "vertex_ai", params
        else:
            error_msg = f"Unsupported API provider {api.provider} for Google AI"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _setup_client_sync(self) -> genai.Client:
        """Get the appropriate sync Google AI client"""
        api = self.model_endpoint.api
        _client_type, params = self._get_client_params(api)
        return genai.Client(**params)

    async def _setup_client_async(self) -> genai.Client:
        """Get the appropriate async Google AI client"""
        api = self.model_endpoint.api
        _client_type, params = self._get_client_params(api)
        return genai.Client(**params).aio
