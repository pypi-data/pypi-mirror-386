from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from codemie_tools.base.models import CodeMieToolConfig


class AzureDevOpsGitConfig(CodeMieToolConfig):
    """Configuration for Azure DevOps Git API access."""

    url: str = Field(
        default="https://dev.azure.com",
        description="Azure DevOps base URL",
        json_schema_extra={"placeholder": "https://dev.azure.com"}
    )

    organization: str = Field(
        description="Azure DevOps organization name",
        json_schema_extra={
            "placeholder": "my-organization",
            "help": "Found in your Azure DevOps URL: https://dev.azure.com/{organization}"
        }
    )

    project: Optional[str] = Field(
        default=None,
        description="Default Azure DevOps project name (optional, can be overridden per request)",
        json_schema_extra={
            "placeholder": "MyProject",
            "help": "Can be omitted if working with organization-level APIs or specified per request"
        }
    )

    token: str = Field(
        description="Azure DevOps Personal Access Token (PAT) with Git permissions",
        json_schema_extra={
            "sensitive": True,
            "help": "https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate"
        }
    )

    api_version: str = Field(
        default="7.1-preview.1",
        description="Azure DevOps REST API version",
        json_schema_extra={"placeholder": "7.1-preview.1"}
    )


class AzureDevOpsGitInput(BaseModel):
    """Input schema for Azure DevOps Git API requests."""

    query: Union[str, Dict[str, Any]] = Field(
        description="""
        JSON containing the Azure DevOps Git API request specification. Must be valid JSON with no comments allowed.

        Required JSON structure:
        {
            "method": "GET|POST|PUT|DELETE|PATCH",
            "url": "/_apis/git/...",
            "method_arguments": {request_parameters_or_body_data}
        }

        Optional with custom headers:
        {
            "method": "GET|POST|PUT|DELETE|PATCH",
            "url": "/_apis/git/...", 
            "method_arguments": {request_parameters_or_body_data},
            "custom_headers": {additional_http_headers}
        }

        Field Requirements:
        - method: HTTP method (GET, POST, PUT, DELETE, PATCH) - REQUIRED
        - url: Azure DevOps Git API endpoint starting with "/_apis/git/" (relative path) - REQUIRED
        - method_arguments: Object containing request parameters - REQUIRED (can be empty {})
        - custom_headers: Optional dictionary of additional HTTP headers - OPTIONAL

        Important Notes:
        - Azure DevOps Personal Access Token is automatically added for authentication
        - custom_headers cannot override authorization headers (protected for security)
        - GET requests: method_arguments sent as query parameters
        - POST/PUT/DELETE/PATCH requests: method_arguments sent as request body data
        - The entire query must pass json.loads() validation
        - API version defaults to configured value if not included in method_arguments

        Response Format:
        Returns AzureDevOpsGitOutput object with:
        - success: boolean indicating if request was successful
        - status_code: HTTP status code
        - method: HTTP method used
        - url: Full URL that was called
        - data: Response body (JSON object/array or text string)
        - error: Error message if request failed (null on success)

        Examples:
        List repositories: {"method": "GET", "url": "/_apis/git/repositories", "method_arguments": {"project": "MyProject"}}
        Get file contents: {"method": "GET", "url": "/_apis/git/repositories/{repositoryId}/items", "method_arguments": {"path": "/file.txt", "repositoryId": "repo-id"}}
        Create repository: {"method": "POST", "url": "/_apis/git/repositories", "method_arguments": {"name": "new-repo", "project": {"id": "project-id"}}}
        """
    )


class AzureDevOpsGitOutput(BaseModel):
    """Structured response from Azure DevOps Git API operations."""

    success: bool = Field(description="Whether the request was successful")
    status_code: int = Field(description="HTTP status code")
    method: str = Field(description="HTTP method used")
    url: str = Field(description="Full URL that was called")
    data: Union[Dict[str, Any], List[Any], str] = Field(
        description="Response body - JSON object/array or text string"
    )
    error: Optional[str] = Field(default=None, description="Error message if request failed")