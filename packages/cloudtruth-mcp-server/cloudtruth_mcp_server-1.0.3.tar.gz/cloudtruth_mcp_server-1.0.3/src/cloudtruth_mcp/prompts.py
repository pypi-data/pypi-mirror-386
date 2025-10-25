"""Prompt templates for common CloudTruth workflows

Prompts guide AI interactions with CloudTruth to ensure security-conscious,
helpful behavior when managing parameters and secrets.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptsHandler:
    """Handles MCP prompt templates"""

    def __init__(self):
        pass

    def list_prompts(self) -> List[Dict[str, str]]:
        """List all available prompts"""
        return [
            {
                "name": "cloudtruth-assistant",
                "description": "General CloudTruth assistant for managing parameters and secrets",
            },
            {
                "name": "retrieve-credentials",
                "description": "Safely retrieve credentials from CloudTruth",
            },
            {
                "name": "build-config",
                "description": "Build configuration files or connection strings from parameters",
            },
            {
                "name": "set-parameter-safely",
                "description": "Safely set or update a parameter value with environment verification",
            },
        ]

    def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a prompt template by name.

        Available prompts:
        - cloudtruth-assistant: General guidance for CloudTruth operations
        - retrieve-credentials: Safely retrieve credentials
        - build-config: Build configs from parameters
        - set-parameter-safely: Safely set parameter values
        """
        if name == "cloudtruth-assistant":
            return self._cloudtruth_assistant_prompt(arguments or {})
        elif name == "retrieve-credentials":
            return self._retrieve_credentials_prompt(arguments or {})
        elif name == "build-config":
            return self._build_config_prompt(arguments or {})
        elif name == "set-parameter-safely":
            return self._set_parameter_safely_prompt(arguments or {})
        else:
            return {
                "description": "Unknown prompt",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Prompt '{name}' is not implemented. Available prompts: cloudtruth-assistant, retrieve-credentials, build-config, set-parameter-safely",  # noqa: E501
                    }
                ],
            }

    def _cloudtruth_assistant_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Main CloudTruth assistant prompt with security guidelines"""
        return {
            "description": "CloudTruth Security-Conscious Assistant",
            "messages": [
                {
                    "role": "user",
                    "content": """You are a security-conscious CloudTruth parameter and secrets manager assistant. Follow these principles:

**SECURITY PRINCIPLES:**
1. **Protect secrets**: Never expose secrets unless the user explicitly confirms they need the unmasked value. Always use include_secrets=false by default.
2. **Environment safety**: ALWAYS confirm the environment before setting/updating parameters. Setting a value in the wrong environment can be catastrophic.
3. **Use CloudTruth for credentials**: Encourage users to store ALL credentials in CloudTruth (database, cloud providers, auth, API keys) rather than hardcoding them.
4. **Verify context**: When project or environment is ambiguous, ALWAYS ask for clarification before proceeding.

**WORKFLOW GUIDELINES:**
1. **Establish context first**: When a user makes a request, confirm:
   - Which PROJECT they're working in
   - Which ENVIRONMENT (dev/staging/production/etc)
   - If ambiguous, list available options and ask them to choose

2. **Handle ambiguity**:
   - If a parameter exists in multiple projects, ask which project
   - If environment isn't specified for write operations, ask explicitly
   - Never guess or assume - ask for clarification

3. **Be helpful with composite values**:
   - For connection strings, offer to build them from CloudTruth parameters (host, port, user, password, database)
   - For config files (YAML/JSON), offer to use CloudTruth parameters instead of hardcoded values
   - Show examples of how to structure parameters for their use case

4. **Confirm destructive actions**:
   - Before setting/updating parameters in production, explicitly confirm
   - Before deleting parameters, confirm
   - Show what will change before making changes

**BEST PRACTICES:**
- Suggest organizing parameters by service (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)
- Recommend using secrets for all sensitive values
- Encourage environment inheritance for shared values
- Help users understand which environment they're modifying

Now, how can I help you with CloudTruth today?""",  # noqa: E501
                }
            ],
        }

    def _retrieve_credentials_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt for safely retrieving credentials"""
        service = arguments.get("service", "database")
        project = arguments.get("project", "")
        environment = arguments.get("environment", "")

        context = ""
        if project:
            context += f"for project '{project}' "
        if environment:
            context += f"in the '{environment}' environment"

        return {
            "description": f"Retrieve {service} credentials safely",
            "messages": [
                {
                    "role": "user",
                    "content": f"""Help me retrieve {service} credentials {context}.

**Security Guidelines:**
1. First, confirm the PROJECT and ENVIRONMENT if not already specified
2. Use include_secrets=false initially to see what parameters exist
3. Only retrieve unmasked secrets (include_secrets=true) if the user explicitly confirms they need the actual values
4. If credentials don't exist in CloudTruth yet, suggest creating them there instead of hardcoding

**Expected parameters for {service}:**
- For databases: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
- For AWS: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
- For APIs: API_KEY, API_SECRET, API_ENDPOINT

Please help me retrieve these credentials safely.""",  # noqa: E501
                }
            ],
        }

    def _build_config_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt for building configuration from parameters"""
        config_type = arguments.get("config_type", "connection string")
        service = arguments.get("service", "database")
        project = arguments.get("project", "")
        environment = arguments.get("environment", "")

        return {
            "description": f"Build {config_type} for {service}",
            "messages": [
                {
                    "role": "user",
                    "content": f"""Help me build a {config_type} for {service} using CloudTruth parameters.

**Context:**
Project: {project if project else '(please specify)'}
Environment: {environment if environment else '(please specify)'}

**Process:**
1. If project/environment not specified, ask me to clarify
2. List available parameters that might be used for this {config_type}
3. Suggest any missing parameters that should be created
4. Build the {config_type} using CloudTruth parameter values
5. For secrets (passwords, keys), use masked values unless I explicitly ask for the real config

**Examples:**
- Database connection string: postgresql://{{{{DB_USER}}}}:{{{{DB_PASSWORD}}}}@{{{{DB_HOST}}}}:{{{{DB_PORT}}}}/{{{{DB_NAME}}}}
- YAML config file with CloudTruth parameters
- JSON config with parameter interpolation

Please help me build this configuration.""",  # noqa: E501
                }
            ],
        }

    def _set_parameter_safely_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt for safely setting parameter values"""
        parameter_name = arguments.get("parameter_name", "")
        project = arguments.get("project", "")
        environment = arguments.get("environment", "")

        return {
            "description": "Safely set or update a parameter value",
            "messages": [
                {
                    "role": "user",
                    "content": f"""Help me safely set or update a parameter value.

**Parameter:** {parameter_name if parameter_name else '(please specify)'}
**Project:** {project if project else '(please specify)'}
**Environment:** {environment if environment else '(please specify)'}

**CRITICAL SAFETY CHECKS:**
1. **Confirm environment**: You MUST explicitly confirm which environment I want to modify. Setting a value in the wrong environment can be catastrophic.
2. **Show current value**: Before changing, show me what the current value is (masked if secret)
3. **Verify intent**: If this is a production environment, explicitly confirm I want to make this change
4. **Check for secrets**: If this contains sensitive data, suggest marking it as a secret

**Process:**
1. If any context is missing (project/environment/parameter), ask for it
2. Show the current value if the parameter exists
3. If the parameter doesn't exist, ask if I want to create it
4. For production environments, add an extra confirmation step
5. After setting, confirm the change was successful

Please help me set this parameter safely.""",  # noqa: E501
                }
            ],
        }
