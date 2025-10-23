"""
Data models for credential management - independent of Pantheon platform.
"""

from typing import Any

from pydantic import BaseModel, Field

from .decorators import external


@external
class ConnectionIdentifier(BaseModel):
    """Connection identifier model."""

    connection_id: str | None = Field(default=None, description="Connection id from Application Platform")
    credential_id: str | None = Field(default=None, description="Credential id from Application Platform")
    organization_id: str | None = Field(default=None, description="Organization id from Application Platform")
    user_id: str | None = Field(default=None, description="User id from Application Platform")


@external
class Connection(BaseModel):
    """Represents a set of credentials for connecting to an external service"""

    connection_id: str = Field(description="Connection id from Application Platform")
    summary: str = Field(description="Human-readable description of this connection")


@external
class ActionConnectionsMapping(BaseModel):
    """Defines an action and its available connections"""

    action_name: str
    connections: list[Connection] = []


class AutonomousAgentConfig(BaseModel):
    """Defines a list of actions and their available connections"""

    actions_list: list[ActionConnectionsMapping]


class Credential(BaseModel):
    """Credential model."""

    id: str = Field(description="Unique identifier for the credential")
    name: str = Field(description="Human-readable name for the credential")
    type: str = Field(description="Type of credential (e.g., COUPA)")
    body: dict[str, Any] | None = Field(default=None, description="Credential data")


class CredentialsResponse(BaseModel):
    """Response model for credentials list."""

    data: list[Credential] | None = Field(default_factory=list, description="List of credentials, can be empty or null")


class CreatedCredential(BaseModel):
    """Response model for created credential."""

    id: str = Field(description="Unique identifier for the created credential")
    name: str = Field(description="Human-readable name for the credential")
    type: str = Field(description="Type of credential")
