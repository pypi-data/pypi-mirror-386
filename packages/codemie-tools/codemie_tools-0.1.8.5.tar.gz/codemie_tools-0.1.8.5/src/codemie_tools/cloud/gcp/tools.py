import json
from typing import Type, Union, Dict, Any, Optional, List

from langchain_core.tools import ToolException
from pydantic import BaseModel, model_validator

from codemie_tools.base.codemie_tool import CodeMieTool
from ...base.utils import parse_and_escape_args
from .models import GCPConfig, GCPInput
from .tools_vars import GCP_TOOL
from .gcp_client import GCPClient


class GenericGCPTool(CodeMieTool):
    """Generic tool for interacting with Google Cloud Platform REST API."""

    config: GCPConfig
    client: Optional[GCPClient] = None
    project_id: Optional[str] = None
    name: str = GCP_TOOL.name
    description: str = GCP_TOOL.description
    args_schema: Type[BaseModel] = GCPInput

    @model_validator(mode='after')
    def initialize_client(self) -> 'GenericGCPTool':
        """Initialize the GCP client with configuration."""
        self.client = GCPClient(service_account_key=self.config.service_account_key)

        # Extract project_id for description
        try:
            sa_info = json.loads(self.config.service_account_key)
            self.project_id = sa_info.get("project_id", "unknown")
        except Exception:
            self.project_id = "unknown"

        return self

    @staticmethod
    def _validate_inputs(method: str, scopes: List[str], url: str) -> None:
        """Validate the required inputs for a GCP API request."""
        if not url:
            raise ToolException("URL is required for GCP API requests")
    
        if not method:
            raise ToolException("HTTP method is required for GCP API requests")
    
        if not scopes or len(scopes) == 0:
            raise ToolException(
                "At least one OAuth scope is required for GCP API requests. "
                "Common scope: https://www.googleapis.com/auth/cloud-platform"
            )
    
    def execute(
        self,
        method: str,
        scopes: List[str],
        url: str,
        optional_args: Optional[Union[str, Dict[str, Any]]] = None
    ) -> str:
        """
        Execute a GCP REST API request.
    
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            scopes: List of OAuth 2.0 scopes for authentication
            url: Full URL for the GCP API request
            optional_args: Optional JSON object with request parameters
    
        Returns:
            str: Response from GCP API
    
        Raises:
            ToolException: If operation fails
        """
        try:
            # Validate required inputs
            self._validate_inputs(method, scopes, url)

            # Parse optional arguments
            parsed_args = parse_and_escape_args(optional_args, item_type="optional_args")

            # Make the request
            return self.client.request(
                method=method,
                scopes=scopes,
                url=url,
                optional_args=parsed_args
            )
    
        except ToolException:
            raise
        except Exception as e:
            raise ToolException(f"GCP tool execution failed: {str(e)}")

    def _healthcheck(self):
        """
        Check if GCP service is accessible.
        Raises an exception if the service is not accessible.
        """
        self.client.health_check()