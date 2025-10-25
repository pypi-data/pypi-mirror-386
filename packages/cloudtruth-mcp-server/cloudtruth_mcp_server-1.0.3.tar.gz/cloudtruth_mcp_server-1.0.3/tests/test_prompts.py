"""Tests for prompts handler"""

from cloudtruth_mcp.prompts import PromptsHandler


class TestPromptsHandler:
    """Test prompt template generation"""

    def test_init(self):
        """Test handler initialization"""
        handler = PromptsHandler()
        assert handler is not None

    def test_list_prompts(self):
        """Test listing all available prompts"""
        handler = PromptsHandler()
        prompts = handler.list_prompts()

        assert len(prompts) == 4
        assert all("name" in p and "description" in p for p in prompts)
        prompt_names = [p["name"] for p in prompts]
        assert "cloudtruth-assistant" in prompt_names
        assert "retrieve-credentials" in prompt_names
        assert "build-config" in prompt_names
        assert "set-parameter-safely" in prompt_names

    def test_cloudtruth_assistant_prompt(self):
        """Test cloudtruth-assistant prompt"""
        handler = PromptsHandler()
        result = handler.get_prompt("cloudtruth-assistant")

        assert "description" in result
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        content = result["messages"][0]["content"]
        assert "SECURITY PRINCIPLES" in content
        assert "WORKFLOW GUIDELINES" in content
        assert "Protect secrets" in content
        assert "Environment safety" in content
        assert "CloudTruth" in content

    def test_retrieve_credentials_prompt_defaults(self):
        """Test retrieve-credentials prompt with default arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt("retrieve-credentials")

        assert "description" in result
        assert "messages" in result
        assert "database" in result["description"]
        content = result["messages"][0]["content"]
        assert "Security Guidelines" in content
        assert "include_secrets=false" in content
        assert "DB_HOST" in content
        assert "DB_PASSWORD" in content

    def test_retrieve_credentials_prompt_custom_service(self):
        """Test retrieve-credentials prompt with custom service"""
        handler = PromptsHandler()
        result = handler.get_prompt(
            "retrieve-credentials",
            {
                "service": "AWS",
                "project": "my-app",
                "environment": "production",
            },
        )

        assert "AWS" in result["description"]
        content = result["messages"][0]["content"]
        assert "my-app" in content
        assert "production" in content
        assert "AWS_ACCESS_KEY_ID" in content

    def test_build_config_prompt_defaults(self):
        """Test build-config prompt with default arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt("build-config")

        assert "description" in result
        assert "connection string" in result["description"]
        content = result["messages"][0]["content"]
        assert "Process:" in content
        assert "postgresql://" in content
        assert "DB_USER" in content

    def test_build_config_prompt_custom_type(self):
        """Test build-config prompt with custom config type"""
        handler = PromptsHandler()
        result = handler.get_prompt(
            "build-config",
            {
                "config_type": "YAML config",
                "service": "Redis",
                "project": "cache-service",
                "environment": "staging",
            },
        )

        assert "YAML config" in result["description"]
        assert "Redis" in result["description"]
        content = result["messages"][0]["content"]
        assert "cache-service" in content
        assert "staging" in content

    def test_set_parameter_safely_prompt_defaults(self):
        """Test set-parameter-safely prompt with default arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt("set-parameter-safely")

        assert "description" in result
        content = result["messages"][0]["content"]
        assert "CRITICAL SAFETY CHECKS" in content
        assert "Confirm environment" in content
        assert "catastrophic" in content
        assert "production" in content

    def test_set_parameter_safely_prompt_with_context(self):
        """Test set-parameter-safely prompt with full context"""
        handler = PromptsHandler()
        result = handler.get_prompt(
            "set-parameter-safely",
            {
                "parameter_name": "API_KEY",
                "project": "backend",
                "environment": "staging",
            },
        )

        content = result["messages"][0]["content"]
        assert "API_KEY" in content
        assert "backend" in content
        assert "staging" in content

    def test_unknown_prompt(self):
        """Test requesting an unknown prompt"""
        handler = PromptsHandler()
        result = handler.get_prompt("nonexistent-prompt")

        assert "description" in result
        assert "Unknown prompt" in result["description"]
        assert "messages" in result
        assert "not implemented" in result["messages"][0]["content"]
        assert "cloudtruth-assistant" in result["messages"][0]["content"]
        assert "retrieve-credentials" in result["messages"][0]["content"]
        assert "build-config" in result["messages"][0]["content"]
        assert "set-parameter-safely" in result["messages"][0]["content"]

    def test_prompt_with_none_arguments(self):
        """Test prompt with None arguments (should use defaults)"""
        handler = PromptsHandler()
        result = handler.get_prompt("retrieve-credentials", None)

        assert "description" in result
        assert "messages" in result
        # Should use defaults when None is passed
        assert "database" in result["description"]

    def test_prompt_with_empty_arguments(self):
        """Test prompt with empty dict arguments (should use defaults)"""
        handler = PromptsHandler()
        result = handler.get_prompt("set-parameter-safely", {})

        assert "description" in result
        assert "messages" in result
        # Should work with empty dict
        assert "CRITICAL SAFETY CHECKS" in result["messages"][0]["content"]

    def test_all_prompts_have_required_structure(self):
        """Test that all prompts return the required structure"""
        handler = PromptsHandler()
        prompt_names = [
            "cloudtruth-assistant",
            "retrieve-credentials",
            "build-config",
            "set-parameter-safely",
        ]

        for name in prompt_names:
            result = handler.get_prompt(name)

            # All prompts must have description and messages
            assert "description" in result, f"{name} missing description"
            assert "messages" in result, f"{name} missing messages"
            assert isinstance(result["messages"], list), f"{name} messages not a list"
            assert len(result["messages"]) > 0, f"{name} has no messages"

            # All messages must have role and content
            for msg in result["messages"]:
                assert "role" in msg, f"{name} message missing role"
                assert "content" in msg, f"{name} message missing content"
                assert msg["role"] == "user", f"{name} message role is not 'user'"
                assert isinstance(msg["content"], str), f"{name} content not a string"
                assert len(msg["content"]) > 0, f"{name} content is empty"

    def test_prompt_descriptions_are_descriptive(self):
        """Test that prompt descriptions are meaningful"""
        handler = PromptsHandler()

        # cloudtruth-assistant
        result = handler.get_prompt("cloudtruth-assistant")
        assert "cloudtruth" in result["description"].lower()

        # retrieve-credentials with service
        result = handler.get_prompt("retrieve-credentials", {"service": "postgres"})
        assert "postgres" in result["description"].lower()

        # build-config
        result = handler.get_prompt("build-config", {"service": "redis"})
        assert "redis" in result["description"].lower()

        # set-parameter-safely
        result = handler.get_prompt("set-parameter-safely")
        assert "set" in result["description"].lower() or "update" in result["description"].lower()
