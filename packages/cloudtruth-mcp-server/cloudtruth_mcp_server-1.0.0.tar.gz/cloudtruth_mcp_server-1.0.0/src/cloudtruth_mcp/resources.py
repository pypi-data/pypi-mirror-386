"""Resource handlers for MCP resources

Resources provide URI-based access to CloudTruth data.
This is a placeholder for Phase 7 - Resources are optional for basic functionality.
"""

import json
import logging
from urllib.parse import urlparse

from .client import CloudTruthClient

logger = logging.getLogger(__name__)


class ResourcesHandler:
    """Handles MCP resource requests"""

    def __init__(self, client: CloudTruthClient):
        self.client = client

    async def read_resource(self, uri: str) -> str:
        """
        Read a resource by URI.

        Supported URIs:
        - cloudtruth://projects
        - cloudtruth://environments
        - cloudtruth://projects/{project_id}/parameters
        """
        parsed = urlparse(uri)

        if parsed.path == "/projects" or parsed.path == "projects":
            return await self._read_projects_resource()
        elif parsed.path == "/environments" or parsed.path == "environments":
            return await self._read_environments_resource()
        else:
            return json.dumps(
                {
                    "error": "Unsupported resource URI",
                    "uri": uri,
                    "message": "Resources are partially implemented. Use tools for full functionality.",
                }
            )

    async def _read_projects_resource(self) -> str:
        """Read projects resource"""
        try:
            projects = await self.client.list_projects()

            projects_data = [
                {"id": p.id, "name": p.name, "description": p.description} for p in projects
            ]

            result = {"projects": projects_data, "total_count": len(projects)}

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error reading projects resource: {e}")
            return json.dumps({"error": str(e)})

    async def _read_environments_resource(self) -> str:
        """Read environments resource"""
        try:
            environments = await self.client.list_environments()

            envs_data = [
                {
                    "id": e.id,
                    "name": e.name,
                    "description": e.description,
                    "parent": e.parent,
                }
                for e in environments
            ]

            result = {"environments": envs_data, "total_count": len(environments)}

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error reading environments resource: {e}")
            return json.dumps({"error": str(e)})
