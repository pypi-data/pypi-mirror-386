"""Data models for CloudTruth MCP Server"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ServerConfig(BaseModel):
    """Server configuration loaded from JSON file"""

    api_key: str = Field(..., min_length=10, pattern=r"^[a-zA-Z0-9.]+$")
    api_base_url: str = Field(default="https://api.cloudtruth.io")
    default_project: Optional[str] = None
    default_environment: Optional[str] = None
    cache_ttl_seconds: int = Field(default=300, ge=0, le=3600)
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    max_retries: int = Field(default=3, ge=0, le=10)

    @field_validator("api_base_url")
    @classmethod
    def validate_https(cls, v: HttpUrl) -> HttpUrl:
        """Ensure API URL uses HTTPS"""
        if not str(v).startswith("https://"):
            raise ValueError("api_base_url must use HTTPS")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "api_key": "your-api-key-here",
                "api_base_url": "https://api.cloudtruth.io",
                "default_project": "my-app",
                "default_environment": "development",
                "cache_ttl_seconds": 300,
                "log_level": "INFO",
            }
        }
    }


class ParameterType(str, Enum):
    """Parameter type enumeration"""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class Organization(BaseModel):
    """CloudTruth Organization"""

    id: str
    url: str
    name: str
    created_at: datetime
    modified_at: datetime


class Project(BaseModel):
    """CloudTruth Project"""

    id: str
    url: str
    name: str
    description: str
    depends_on: Optional[str] = None  # Parent project ID
    access_controlled: bool = False
    role: Optional[str] = None  # "owner", "admin", "contributor", "viewer"
    created_at: datetime
    modified_at: datetime


class Environment(BaseModel):
    """CloudTruth Environment"""

    id: str
    url: str
    name: str
    description: str
    parent: Optional[str] = None  # Parent environment URL
    children: List[str] = []  # Child environment URLs
    access_controlled: bool = False
    role: Optional[str] = None
    created_at: datetime
    modified_at: datetime


class Parameter(BaseModel):
    """CloudTruth Parameter"""

    id: str
    url: str
    name: str
    description: str
    secret: bool
    type: ParameterType
    rules: List[Dict[str, Any]] = []
    project: str  # Project URL
    values: Optional[Dict[str, Any]] = None  # env_id -> value object mapping
    created_at: datetime
    modified_at: datetime


class Value(BaseModel):
    """CloudTruth Parameter Value"""

    id: str
    url: str
    environment: str  # Environment URL
    environment_name: str
    earliest_tag: Optional[str] = None
    parameter: str  # Parameter URL
    external: bool = False
    external_fqn: Optional[str] = None
    internal_value: Optional[str] = None  # Raw value (can be null if not set)
    interpolated: bool = False
    value: Optional[str] = None  # Resolved value (use this! can be null if not set)
    evaluated: bool = False
    secret: bool = False
    dynamic: bool = False
    dynamic_error: Optional[str] = None
    dynamic_fqn: Optional[str] = None
    dynamic_filter: Optional[str] = None
    created_at: datetime
    modified_at: datetime


class Tag(BaseModel):
    """CloudTruth Environment Tag"""

    id: str
    url: str
    name: str
    description: str
    timestamp: datetime
    environment: str  # Environment URL
    created_at: datetime
    modified_at: datetime


class TemplatePreviewRequest(BaseModel):
    """Template preview request"""

    environment: str  # Environment ID
    body: str  # Template body with {{PARAM}} placeholders


class TemplatePreviewResponse(BaseModel):
    """Template preview response"""

    body: str  # Rendered template


# MCP Response Models


class TextContent(BaseModel):
    """Text content block"""

    type: Literal["text"] = "text"
    text: str


class ToolResponse(BaseModel):
    """MCP tool response"""

    content: List[Union[TextContent]]
    isError: bool = False  # noqa: N815 - MCP protocol field


class ResourceContent(BaseModel):
    """Resource content"""

    uri: str
    mimeType: str = "application/json"  # noqa: N815 - MCP protocol field
    text: str


class ResourceResponse(BaseModel):
    """MCP resource response"""

    contents: List[ResourceContent]


class PromptMessage(BaseModel):
    """Prompt message"""

    role: Literal["user", "assistant"] = "user"
    content: Union[str, List[Dict[str, Any]]]


class PromptResponse(BaseModel):
    """MCP prompt response"""

    description: Optional[str] = None
    messages: List[PromptMessage]


# Cache Models

T = TypeVar("T")


class CacheEntry(BaseModel, Generic[T]):
    """Generic cache entry with TTL"""

    key: str
    value: T
    created_at: datetime
    ttl_seconds: int

    @property
    def expires_at(self) -> datetime:
        return self.created_at + timedelta(seconds=self.ttl_seconds)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def age_seconds(self) -> float:
        return (datetime.utcnow() - self.created_at).total_seconds()


class CacheStats(BaseModel):
    """Cache statistics"""

    total_entries: int
    total_hits: int
    total_misses: int
    hit_rate: float  # hits / (hits + misses)
    total_size_bytes: int
    oldest_entry_age_seconds: float
    newest_entry_age_seconds: float
