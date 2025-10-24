"""CloudTruth API client"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from .cache import CacheManager, get_ttl_for_category, make_cache_key
from .models import Environment, Parameter, Project, ServerConfig, Tag, Value

logger = logging.getLogger(__name__)


class CloudTruthClient:
    """Async client for CloudTruth API"""

    def __init__(self, config: ServerConfig, cache: Optional[CacheManager] = None):
        self.config = config
        self.base_url = str(config.api_base_url).rstrip("/") + "/api/v1/"
        self.cache = cache or CacheManager()
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Api-Key {config.api_key}",
                "Accept": "application/json",
                "User-Agent": "cloudtruth-mcp-server/1.0.0",
            },
            timeout=httpx.Timeout(config.timeout_seconds),
            verify=True,  # ALWAYS enforce certificate validation
        )

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = urljoin(self.base_url, endpoint)

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Retry on transient errors
                if e.response.status_code in [429, 500, 502, 503]:
                    if attempt < self.config.max_retries - 1:
                        delay = 2**attempt  # Exponential backoff
                        logger.warning(f"HTTP {e.response.status_code}, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                raise
            except httpx.RequestError as e:
                if attempt < self.config.max_retries - 1:
                    delay = 2**attempt
                    logger.warning(f"Request error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                raise

        raise Exception("Max retries exceeded")

    async def list_projects(self, name_filter: Optional[str] = None) -> List[Project]:
        """List all projects"""
        # Create cache key
        cache_key = make_cache_key("projects", name_filter or "all")

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from API
        params: Dict[str, str] = {}
        if name_filter:
            params["name__icontains"] = name_filter

        data = await self._request("GET", "projects/", params=params)
        projects = [Project(**item) for item in data["results"]]

        # Cache the result
        ttl = get_ttl_for_category("projects")
        self.cache.set(cache_key, projects, ttl)

        return projects

    async def create_project(
        self, name: str, description: str = "", depends_on: Optional[str] = None
    ) -> Project:
        """Create a new project"""
        payload: Dict[str, Any] = {
            "name": name,
            "description": description,
        }
        if depends_on:
            payload["depends_on"] = depends_on

        data = await self._request("POST", "projects/", json=payload)

        # Invalidate projects cache
        self.cache.invalidate_pattern("projects:")

        return Project(**data)

    async def delete_project(self, project_id: str) -> None:
        """Delete a project"""
        await self._request("DELETE", f"projects/{project_id}/")

        # Invalidate projects cache
        self.cache.invalidate_pattern("projects:")

    async def get_project(self, project_name_or_id: str) -> Optional[Project]:
        """Get project by name or ID"""
        # Try by name first
        projects = await self.list_projects(name_filter=project_name_or_id)
        for proj in projects:
            if proj.name == project_name_or_id or proj.id == project_name_or_id:
                return proj
        return None

    async def list_environments(self) -> List[Environment]:
        """List all environments"""
        # Create cache key
        cache_key = make_cache_key("environments", "all")

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from API
        data = await self._request("GET", "environments/")
        environments = [Environment(**item) for item in data["results"]]

        # Cache the result
        ttl = get_ttl_for_category("environments")
        self.cache.set(cache_key, environments, ttl)

        return environments

    async def create_environment(
        self, name: str, description: str = "", parent: Optional[str] = None
    ) -> Environment:
        """Create a new environment"""
        payload: Dict[str, Any] = {
            "name": name,
            "description": description,
        }
        if parent:
            payload["parent"] = parent

        data = await self._request("POST", "environments/", json=payload)

        # Invalidate environments cache
        self.cache.invalidate_pattern("environments:")

        return Environment(**data)

    async def get_environment(self, env_name_or_id: str) -> Optional[Environment]:
        """Get environment by name or ID"""
        envs = await self.list_environments()
        for env in envs:
            if env.name == env_name_or_id or env.id == env_name_or_id:
                return env
        return None

    async def list_parameters(
        self, project_id: str, environment_id: Optional[str] = None
    ) -> List[Parameter]:
        """List all parameters for a project"""
        params: Dict[str, str] = {}
        if environment_id:
            params["environment"] = environment_id

        data = await self._request("GET", f"projects/{project_id}/parameters/", params=params)
        return [Parameter(**item) for item in data["results"]]

    async def get_parameter(
        self, project_id: str, param_name: str, environment_id: Optional[str] = None
    ) -> Optional[Parameter]:
        """Get parameter by name"""
        params: Dict[str, str] = {"name": param_name}
        if environment_id:
            params["environment"] = environment_id

        data = await self._request("GET", f"projects/{project_id}/parameters/", params=params)

        if data["results"]:
            return Parameter(**data["results"][0])
        return None

    async def get_parameter_values(
        self,
        project_id: str,
        parameter_id: str,
        environment_id: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Value]:
        """Get parameter values"""
        # Create cache key
        cache_key = make_cache_key(
            "parameter_value", project_id, parameter_id, environment_id or "all", tag or "latest"
        )

        # Try cache first (only if not using point-in-time query)
        if tag is None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # Fetch from API
        params: Dict[str, str] = {}
        if environment_id:
            params["environment"] = environment_id
        if tag:
            params["tag"] = tag

        data = await self._request(
            "GET",
            f"projects/{project_id}/parameters/{parameter_id}/values/",
            params=params,
        )
        values = [Value(**item) for item in data["results"]]

        # Cache the result (only if not using point-in-time query)
        if tag is None:
            ttl = get_ttl_for_category("parameter_value")
            self.cache.set(cache_key, values, ttl)

        return values

    async def set_parameter_value(
        self,
        project_id: str,
        parameter_id: str,
        environment_id: str,
        value: str,
    ) -> Value:
        """Set parameter value for an environment"""
        payload = {"value": value}
        data = await self._request(
            "PATCH",
            f"projects/{project_id}/parameters/{parameter_id}/values/{environment_id}/",
            json=payload,
        )

        # Invalidate cache for this parameter
        self.cache.invalidate_pattern(f"parameter_value:{project_id}:{parameter_id}")
        # Also invalidate template cache since parameter changed
        self.cache.invalidate_pattern(f"template:{project_id}")

        return Value(**data)

    async def create_parameter(
        self,
        project_id: str,
        name: str,
        value: str,
        environment_id: str,
        secret: bool = False,
        description: str = "",
    ) -> Parameter:
        """Create a new parameter"""
        payload = {
            "name": name,
            "description": description,
            "secret": secret,
            "values": {environment_id: value},
        }
        data = await self._request("POST", f"projects/{project_id}/parameters/", json=payload)
        return Parameter(**data)

    async def delete_parameter(self, project_id: str, parameter_id: str) -> None:
        """Delete a parameter"""
        await self._request("DELETE", f"projects/{project_id}/parameters/{parameter_id}/")

        # Invalidate cache for this parameter
        self.cache.invalidate_pattern(f"parameter_value:{project_id}:{parameter_id}")
        # Also invalidate template cache since parameter removed
        self.cache.invalidate_pattern(f"template:{project_id}")

    async def preview_template(
        self, project_id: str, environment_id: str, body: str, tag: Optional[str] = None
    ) -> str:
        """Preview template rendering"""
        # Create cache key based on template body hash
        import hashlib

        body_hash = hashlib.md5(body.encode()).hexdigest()[:16]
        cache_key = make_cache_key(
            "template", project_id, environment_id, body_hash, tag or "latest"
        )

        # Try cache first (only if not using point-in-time query)
        if tag is None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # Render template via API
        payload: Dict[str, Any] = {"environment": environment_id, "body": body}
        if tag:
            payload["tag"] = tag

        data = await self._request("POST", f"projects/{project_id}/template-preview/", json=payload)
        rendered = data["body"]

        # Cache the result (only if not using point-in-time query)
        if tag is None:
            ttl = get_ttl_for_category("template")
            self.cache.set(cache_key, rendered, ttl)

        return rendered

    async def create_tag(self, environment_id: str, name: str, description: str = "") -> Tag:
        """Create a tag (point-in-time snapshot)"""
        payload = {"name": name, "description": description}
        data = await self._request("POST", f"environments/{environment_id}/tags/", json=payload)
        return Tag(**data)

    async def list_tags(self, environment_id: str) -> List[Tag]:
        """List tags for an environment"""
        data = await self._request("GET", f"environments/{environment_id}/tags/")
        return [Tag(**item) for item in data["results"]]

    async def close(self) -> None:
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self) -> "CloudTruthClient":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()
