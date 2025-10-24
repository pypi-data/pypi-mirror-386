from typing import Dict, Any, Union

from pydantic import BaseModel, Field, model_validator

from codemie_tools.base.models import CodeMieToolConfig, RequiredField


class AWSConfig(CodeMieToolConfig):
    """Configuration for AWS integration."""

    region: str = RequiredField(
        description="AWS region (e.g., us-east-1, eu-west-1)",
        json_schema_extra={"placeholder": "us-east-1"}
    )

    access_key_id: str = RequiredField(
        description="AWS Access Key ID for authentication",
        json_schema_extra={
            "placeholder": "AKIAIOSFODNN7EXAMPLE",
            "sensitive": True,
            "help": "https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html"
        }
    )

    secret_access_key: str = RequiredField(
        description="AWS Secret Access Key for authentication",
        json_schema_extra={
            "placeholder": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "sensitive": True,
            "help": "https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html"
        }
    )

    @model_validator(mode='before')
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Support legacy credential keys for backward compatibility."""
        # Map legacy keys to new keys
        if "aws_region" in values:
            values["region"] = values.pop("aws_region")
        if "aws_access_key_id" in values:
            values["access_key_id"] = values.pop("aws_access_key_id")
        if "aws_secret_access_key" in values:
            values["secret_access_key"] = values.pop("aws_secret_access_key")

        return values


class AWSInput(BaseModel):
    """Input schema for AWS tool operations."""

    query: Union[str, Dict[str, Any]] = Field(
        description="""
        JSON object containing AWS service operation details with the following structure:
        - 'service': AWS service name (e.g., 'ec2', 'iam', 's3', 'lambda')
        - 'method_name': The API method to call (e.g., 'describe_instances', 'list_buckets')
        - 'method_arguments': Dictionary of arguments for the method (can be empty {})

        Example: {"service": "iam", "method_name": "get_user", "method_arguments": {}}
        Example: {"service": "ec2", "method_name": "describe_instances", "method_arguments": {"InstanceIds": ["i-1234567890abcdef0"]}}

        Note: Must be valid JSON. No comments allowed.
        """
    )
