"""Utility functions"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Secret masking constant
REDACTED = "***REDACTED***"


def mask_secret_value(value: Optional[str], is_secret: bool, include_secrets: bool = False) -> str:
    """
    Mask secret values unless explicitly requested.

    CRITICAL SECURITY FUNCTION - DO NOT MODIFY WITHOUT REVIEW

    Args:
        value: The parameter value (can be None if not set)
        is_secret: Whether the parameter is marked as secret
        include_secrets: Whether to include unmasked secrets

    Returns:
        Either the original value, REDACTED string, or "(not set)" for None
    """
    # Handle null/unset values
    if value is None:
        return "(not set)"

    if is_secret and not include_secrets:
        return REDACTED

    if is_secret and include_secrets:
        # Log secret access for audit trail
        logger.info(
            "SECRET_ACCESS",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "action": "secret_value_accessed",
            },
        )

    return value


def format_parameter_output(
    name: str,
    value: Optional[str],
    secret: bool,
    param_type: str,
    description: str,
    environment: str,
    project: str,
    include_secrets: bool = False,
) -> str:
    """Format parameter for display"""
    masked_value = mask_secret_value(value, secret, include_secrets)

    output = f"Parameter: {name}\n"
    output += f"Project: {project}\n"
    output += f"Environment: {environment}\n"
    output += f"Type: {param_type}\n"

    if secret:
        output += "Secret: Yes\n"
        if include_secrets:
            output += "WARNING: SECRET VALUE EXPOSED\n"
        output += f"Value: {masked_value}\n"
    else:
        output += f"Value: {masked_value}\n"

    if description:
        output += f"\nDescription: {description}\n"

    if secret and not include_secrets:
        output += "\nNote: Value is masked because it's marked as secret. Use include_secrets=true to view."

    return output


def format_parameters_list(
    parameters: list[Dict[str, Any]],
    project: str,
    environment: str,
    include_secrets: bool = False,
) -> str:
    """Format list of parameters as markdown table"""
    if not parameters:
        return f"No parameters found for project '{project}' in environment '{environment}'"

    secret_count = 0
    masked_count = 0

    # Count secrets
    for param in parameters:
        if param.get("secret", False):
            secret_count += 1
            if not include_secrets:
                masked_count += 1

    output = f"## Parameters for project '{project}' in environment '{environment}'\n\n"
    output += f"**Total:** {len(parameters)} parameter{'s' if len(parameters) != 1 else ''}"
    if masked_count > 0:
        output += f" • **{masked_count} secret{'s' if masked_count != 1 else ''} masked** 🔒"
    output += "\n\n"

    # Create markdown table
    output += "| Name | Value | Type | Secret |\n"
    output += "|------|-------|------|--------|\n"

    for param in parameters:
        name = param["name"]
        value = param["value"]
        secret = param.get("secret", False)
        param_type = param.get("type", "string")

        masked_value = mask_secret_value(value, secret, include_secrets)

        # Format value based on type
        if param_type == "string":
            formatted_value = f'`"{masked_value}"`'
        else:
            formatted_value = f"`{masked_value}`"

        # Truncate long values
        if len(formatted_value) > 50:
            formatted_value = formatted_value[:47] + "...`"

        secret_indicator = "🔒 Yes" if secret else "No"

        output += f"| **{name}** | {formatted_value} | {param_type} | {secret_indicator} |\n"

    if masked_count > 0:
        output += "\n> 💡 **Tip:** Use `include_secrets=true` to view unmasked secret values.\n"

    return output


def format_projects_list(projects: list[Dict[str, Any]]) -> str:
    """Format list of projects as markdown table"""
    if not projects:
        return "No projects found"

    output = f"## Found {len(projects)} project{'s' if len(projects) != 1 else ''}\n\n"

    # Create markdown table
    output += "| Name | Description | ID | Modified |\n"
    output += "|------|-------------|----|---------|\n"

    for proj in projects:
        name = proj["name"]
        description = proj.get("description", "")[:50]  # Truncate long descriptions
        if len(proj.get("description", "")) > 50:
            description += "..."
        project_id = proj["id"]
        modified = proj.get("modified_at", "")[:10] if proj.get("modified_at") else "N/A"

        output += f"| **{name}** | {description} | `{project_id}` | {modified} |\n"

    return output


def format_environments_hierarchy(environments: list[Dict[str, Any]]) -> str:
    """Format environments as markdown table with hierarchy"""
    if not environments:
        return "No environments found"

    output = f"## Found {len(environments)} environment{'s' if len(environments) != 1 else ''}\n\n"

    # Create markdown table
    output += "| Name | Description | Parent | ID |\n"
    output += "|------|-------------|--------|----|" + "\n"

    # Build hierarchy map for display
    env_map = {env["url"]: env for env in environments}

    # Sort by hierarchy depth (roots first)
    def get_depth(env: Dict[str, Any]) -> int:
        depth = 0
        current = env
        while current.get("parent"):
            depth += 1
            parent_url = current["parent"]
            current = env_map.get(parent_url, {})
            if not current:
                break
        return depth

    sorted_envs = sorted(environments, key=get_depth)

    for env in sorted_envs:
        name = env["name"]
        # Show flat table without indentation
        display_name = f"**{name}**"

        description = env.get("description", "")[:40]  # Truncate long descriptions
        if len(env.get("description", "")) > 40:
            description += "..."

        parent_name = ""
        if env.get("parent"):
            parent_env = env_map.get(env["parent"])
            if parent_env:
                parent_name = parent_env["name"]

        env_id = env["id"]

        output += f"| {display_name} | {description} | {parent_name} | `{env_id}` |\n"

    return output


def format_success_message(action: str, parameter_name: str, project: str, environment: str) -> str:
    """Format success message for parameter operations"""
    return (
        f"Successfully {action} parameter '{parameter_name}' "
        f"in project '{project}' for environment '{environment}'"
    )


def format_error_message(error: Exception) -> str:
    """Format error message for display"""
    from .errors import sanitize_error_message

    return f"Error: {sanitize_error_message(str(error))}"
