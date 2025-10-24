"""Tool implementations"""

import json
import logging
from typing import Any, Dict, Optional

from .client import CloudTruthClient
from .errors import NotFoundError, ValidationError
from .models import ServerConfig
from .utils import (
    format_environments_hierarchy,
    format_error_message,
    format_parameter_output,
    format_parameters_list,
    format_projects_list,
    format_success_message,
    mask_secret_value,
)

logger = logging.getLogger(__name__)


class ToolsHandler:
    """Handles all MCP tool calls"""

    def __init__(self, client: CloudTruthClient, config: ServerConfig):
        self.client = client
        self.config = config

    async def list_projects(self, name_filter: Optional[str] = None) -> str:
        """List all accessible projects"""
        try:
            projects = await self.client.list_projects(name_filter=name_filter)

            projects_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "modified_at": p.modified_at.isoformat(),
                }
                for p in projects
            ]

            return format_projects_list(projects_data)

        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return format_error_message(e)

    async def create_project(
        self, name: str, description: str = "", parent_project: Optional[str] = None
    ) -> str:
        """Create a new project"""
        try:
            # Resolve parent project if specified
            depends_on = None
            if parent_project:
                parent = await self.client.get_project(parent_project)
                if not parent:
                    raise NotFoundError(f"Parent project not found: {parent_project}")
                depends_on = parent.url

            # Create project
            project = await self.client.create_project(name, description, depends_on)

            message = f"✓ Successfully created project '{name}'\n\n"
            message += f"Project ID: {project.id}\n"
            if description:
                message += f"Description: {description}\n"
            if parent_project:
                message += f"Parent Project: {parent_project}\n"
            message += f"Created: {project.created_at.isoformat()}\n"

            logger.info(f"Project created: {name}")

            return message

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return format_error_message(e)

    async def delete_project(self, project: str, force: bool = False) -> str:
        """Delete a project (requires empty project unless force=True)"""
        try:
            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Safety check: ensure project is empty unless force is True
            if not force:
                # Get default environment to check parameters
                default_env = None
                if self.config.default_environment:
                    default_env = await self.client.get_environment(self.config.default_environment)

                # Check if project has parameters
                params = await self.client.list_parameters(
                    proj.id, default_env.id if default_env else None
                )
                if params:
                    raise ValidationError(
                        f"Cannot delete project '{proj.name}': project contains {len(params)} parameter(s). "
                        f"Please delete all parameters first, or use force=True to override this safety check."
                    )

            # Delete project
            await self.client.delete_project(proj.id)

            message = f"✓ Successfully deleted project '{proj.name}'\n\n"
            message += f"Project ID: {proj.id}\n"
            if force:
                message += "⚠ Force deletion was used - all parameters were removed\n"

            logger.info(f"Project deleted: {proj.name}")

            return message

        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return format_error_message(e)

    async def list_environments(self, name_filter: Optional[str] = None) -> str:
        """List all environments with hierarchy"""
        try:
            environments = await self.client.list_environments()

            if name_filter:
                environments = [e for e in environments if name_filter.lower() in e.name.lower()]

            envs_data = [
                {
                    "id": e.id,
                    "name": e.name,
                    "description": e.description,
                    "parent": e.parent,
                    "url": e.url,
                }
                for e in environments
            ]

            return format_environments_hierarchy(envs_data)

        except Exception as e:
            logger.error(f"Error listing environments: {e}")
            return format_error_message(e)

    async def create_environment(
        self, name: str, description: str = "", parent_environment: Optional[str] = None
    ) -> str:
        """Create a new environment"""
        try:
            # Resolve parent environment if specified
            parent = None
            if parent_environment:
                parent_env = await self.client.get_environment(parent_environment)
                if not parent_env:
                    raise NotFoundError(f"Parent environment not found: {parent_environment}")
                parent = parent_env.url

            # Create environment
            environment = await self.client.create_environment(name, description, parent)

            message = f"✓ Successfully created environment '{name}'\n\n"
            message += f"Environment ID: {environment.id}\n"
            if description:
                message += f"Description: {description}\n"
            if parent_environment:
                message += f"Parent Environment: {parent_environment}\n"
            message += f"Created: {environment.created_at.isoformat()}\n"

            logger.info(f"Environment created: {name}")

            return message

        except Exception as e:
            logger.error(f"Error creating environment: {e}")
            return format_error_message(e)

    async def get_parameter(
        self,
        project: str,
        parameter_name: str,
        environment: Optional[str] = None,
        include_secrets: bool = False,
        as_of: Optional[str] = None,
    ) -> str:
        """Get a single parameter value"""
        try:
            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Resolve environment (use default if not specified)
            env_name = environment or self.config.default_environment or "default"
            env = await self.client.get_environment(env_name)
            if not env:
                raise NotFoundError(f"Environment not found: {env_name}")

            # Get parameter
            param = await self.client.get_parameter(proj.id, parameter_name, env.id)
            if not param:
                raise NotFoundError(
                    f"Parameter '{parameter_name}' not found in project '{project}'"
                )

            # Get parameter values
            values = await self.client.get_parameter_values(proj.id, param.id, env.id, tag=as_of)

            if not values:
                raise NotFoundError(
                    f"No value found for parameter '{parameter_name}' in environment '{env_name}'"
                )

            value_obj = values[0]

            return format_parameter_output(
                name=param.name,
                value=value_obj.value,
                secret=value_obj.secret,
                param_type=str(param.type.value),
                description=param.description,
                environment=env.name,
                project=proj.name,
                include_secrets=include_secrets,
            )

        except Exception as e:
            logger.error(f"Error getting parameter: {e}")
            return format_error_message(e)

    async def get_parameters(
        self,
        project: str,
        environment: Optional[str] = None,
        include_secrets: bool = False,
        name_prefix: Optional[str] = None,
        as_of: Optional[str] = None,
    ) -> str:
        """Get all parameters for a project/environment"""
        try:
            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Resolve environment
            env_name = environment or self.config.default_environment or "default"
            env = await self.client.get_environment(env_name)
            if not env:
                raise NotFoundError(f"Environment not found: {env_name}")

            # Get all parameters
            parameters = await self.client.list_parameters(proj.id, env.id)

            # Filter by prefix if specified
            if name_prefix:
                parameters = [p for p in parameters if p.name.startswith(name_prefix)]

            # Get values for each parameter
            params_data = []
            for param in parameters:
                values = await self.client.get_parameter_values(
                    proj.id, param.id, env.id, tag=as_of
                )
                if values:
                    value_obj = values[0]
                    params_data.append(
                        {
                            "name": param.name,
                            "value": value_obj.value,
                            "secret": value_obj.secret,
                            "type": str(param.type.value),
                            "description": param.description,
                        }
                    )

            return format_parameters_list(params_data, proj.name, env.name, include_secrets)

        except Exception as e:
            logger.error(f"Error getting parameters: {e}")
            return format_error_message(e)

    async def set_parameter(
        self,
        project: str,
        parameter_name: str,
        value: str,
        environment: Optional[str] = None,
        secret: bool = False,
        description: str = "",
    ) -> str:
        """Set or update a parameter value"""
        try:
            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Resolve environment
            env_name = environment or self.config.default_environment or "default"
            env = await self.client.get_environment(env_name)
            if not env:
                raise NotFoundError(f"Environment not found: {env_name}")

            # Check if parameter exists
            param = await self.client.get_parameter(proj.id, parameter_name)

            if param:
                # Update existing parameter
                await self.client.set_parameter_value(proj.id, param.id, env.id, value)
                message = format_success_message("updated", parameter_name, proj.name, env.name)
            else:
                # Create new parameter
                param = await self.client.create_parameter(
                    proj.id, parameter_name, value, env.id, secret, description
                )
                message = format_success_message("created", parameter_name, proj.name, env.name)
                message += "\n\nParameter created successfully."

            if secret:
                message += "\n\nParameter is marked as secret."

            message += "\n\nThe new value is now active and will be used by applications."

            # NEVER log the actual value
            logger.info(f"Parameter set: {parameter_name} in {proj.name}/{env.name}")

            return message

        except Exception as e:
            logger.error(f"Error setting parameter: {e}")
            return format_error_message(e)

    async def create_parameter(
        self,
        project: str,
        parameter_name: str,
        description: str = "",
        secret: bool = False,
        parameter_type: str = "string",
    ) -> str:
        """Create a new parameter definition"""
        try:
            # Validate parameter name
            if parameter_name.startswith("cloudtruth."):
                raise ValidationError(
                    "Parameter names cannot start with 'cloudtruth.' (reserved prefix)"
                )

            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Check if parameter already exists
            existing = await self.client.get_parameter(proj.id, parameter_name)
            if existing:
                return f"Error: Parameter '{parameter_name}' already exists in project '{project}'"

            # Get default environment for initial value
            env_name = self.config.default_environment or "default"
            env = await self.client.get_environment(env_name)
            if not env:
                raise NotFoundError(f"Environment not found: {env_name}")

            # Create parameter with empty value
            await self.client.create_parameter(
                proj.id, parameter_name, "", env.id, secret, description
            )

            message = (
                f" Successfully created parameter '{parameter_name}' in project '{project}'\n\n"
            )
            message += f"Type: {parameter_type}\n"
            if secret:
                message += "Marked as: Secret\n"
            if description:
                message += f"Description: {description}\n"

            message += "\nUse set_parameter to assign values for different environments."

            logger.info(f"Parameter created: {parameter_name} in {proj.name}")

            return message

        except Exception as e:
            logger.error(f"Error creating parameter: {e}")
            return format_error_message(e)

    async def delete_parameter(self, project: str, parameter_name: str) -> str:
        """Delete a parameter"""
        try:
            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Get parameter
            param = await self.client.get_parameter(proj.id, parameter_name)
            if not param:
                raise NotFoundError(
                    f"Parameter '{parameter_name}' not found in project '{project}'"
                )

            # Delete parameter
            await self.client.delete_parameter(proj.id, param.id)

            message = (
                f" Successfully deleted parameter '{parameter_name}' from project '{project}'\n\n"
            )
            message += "This parameter has been permanently removed from all environments."

            logger.info(f"Parameter deleted: {parameter_name} from {proj.name}")

            return message

        except Exception as e:
            logger.error(f"Error deleting parameter: {e}")
            return format_error_message(e)

    async def preview_template(
        self,
        project: str,
        template_body: str,
        environment: Optional[str] = None,
        as_of: Optional[str] = None,
    ) -> str:
        """Preview template rendering"""
        try:
            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Resolve environment
            env_name = environment or self.config.default_environment or "default"
            env = await self.client.get_environment(env_name)
            if not env:
                raise NotFoundError(f"Environment not found: {env_name}")

            # Preview template
            rendered = await self.client.preview_template(proj.id, env.id, template_body, tag=as_of)

            output = f"Template Preview (project='{proj.name}', environment='{env.name}'):\n\n"
            output += "=" * 60 + "\n"
            output += rendered
            output += "\n" + "=" * 60

            return output

        except Exception as e:
            logger.error(f"Error previewing template: {e}")
            return format_error_message(e)

    async def create_tag(self, environment: str, tag_name: str, description: str = "") -> str:
        """Create a point-in-time snapshot tag"""
        try:
            # Resolve environment
            env = await self.client.get_environment(environment)
            if not env:
                raise NotFoundError(f"Environment not found: {environment}")

            # Create tag
            tag = await self.client.create_tag(env.id, tag_name, description)

            message = f" Successfully created tag '{tag_name}' for environment '{env.name}'\n\n"
            message += f"Tag ID: {tag.id}\n"
            message += f"Timestamp: {tag.timestamp.isoformat()}\n"
            if description:
                message += f"Description: {description}\n"

            message += (
                "\nThis tag captures the current state of all parameters in this environment."
            )
            message += "\nUse as_of parameter with this tag name to query historical values."

            logger.info(f"Tag created: {tag_name} for environment {env.name}")

            return message

        except Exception as e:
            logger.error(f"Error creating tag: {e}")
            return format_error_message(e)

    async def export_parameters(
        self,
        project: str,
        environment: Optional[str] = None,
        format: str = "json",
        include_secrets: bool = False,
        name_prefix: Optional[str] = None,
    ) -> str:
        """Export parameters in various formats"""
        try:
            # Resolve project
            proj = await self.client.get_project(project)
            if not proj:
                raise NotFoundError(f"Project not found: {project}")

            # Resolve environment
            env_name = environment or self.config.default_environment or "default"
            env = await self.client.get_environment(env_name)
            if not env:
                raise NotFoundError(f"Environment not found: {env_name}")

            # Get all parameters
            parameters = await self.client.list_parameters(proj.id, env.id)

            # Filter by prefix if specified
            if name_prefix:
                parameters = [p for p in parameters if p.name.startswith(name_prefix)]

            # Get values for each parameter
            params_dict: Dict[str, Any] = {}
            for param in parameters:
                values = await self.client.get_parameter_values(proj.id, param.id, env.id)
                if values:
                    value_obj = values[0]
                    masked_value = mask_secret_value(
                        value_obj.value, value_obj.secret, include_secrets
                    )
                    params_dict[param.name] = masked_value

            # Format output based on requested format
            if format == "json":
                output = json.dumps(params_dict, indent=2)
            elif format == "dotenv" or format == "env":
                output = "\n".join([f"{k}={v}" for k, v in params_dict.items()])
            elif format == "yaml":
                output = "\n".join([f"{k}: {v}" for k, v in params_dict.items()])
            else:
                raise ValidationError(
                    f"Unsupported format: {format}. Supported: json, dotenv, yaml"
                )

            header = "# Export from CloudTruth\n"
            header += f"# Project: {proj.name}\n"
            header += f"# Environment: {env.name}\n"
            header += f"# Format: {format}\n"
            header += f"# Parameters: {len(params_dict)}\n\n"

            return header + output

        except Exception as e:
            logger.error(f"Error exporting parameters: {e}")
            return format_error_message(e)
