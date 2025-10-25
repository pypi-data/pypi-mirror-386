"""Tests for prompts handler"""

from cloudtruth_mcp.prompts import PromptsHandler


class TestPromptsHandler:
    """Test prompt template generation"""

    def test_init(self):
        """Test handler initialization"""
        handler = PromptsHandler()
        assert handler is not None

    def test_get_credentials_prompt_defaults(self):
        """Test get-credentials prompt with default arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt("get-credentials")

        assert "description" in result
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert "database" in result["description"]
        assert "development" in result["description"]
        assert "get_parameters" in result["messages"][0]["content"]
        assert "include_secrets=true" in result["messages"][0]["content"]

    def test_get_credentials_prompt_custom_args(self):
        """Test get-credentials prompt with custom arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt(
            "get-credentials",
            {
                "service_type": "redis",
                "environment": "staging",
                "project": "my-app",
            },
        )

        assert "redis" in result["description"]
        assert "staging" in result["description"]
        assert "redis credentials" in result["messages"][0]["content"]
        assert "staging environment" in result["messages"][0]["content"]
        assert "project my-app" in result["messages"][0]["content"]

    def test_setup_environment_prompt_defaults(self):
        """Test setup-environment prompt with default arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt("setup-environment")

        assert "description" in result
        assert "messages" in result
        assert "new-environment" in result["description"]
        assert "new-environment" in result["messages"][0]["content"]
        assert "development" in result["messages"][0]["content"]
        assert "default" in result["messages"][0]["content"]

    def test_setup_environment_prompt_custom_args(self):
        """Test setup-environment prompt with custom arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt(
            "setup-environment",
            {
                "environment": "qa",
                "parent_environment": "staging",
                "project": "web-api",
            },
        )

        assert "qa" in result["description"]
        assert "qa" in result["messages"][0]["content"]
        assert "staging" in result["messages"][0]["content"]
        assert "web-api" in result["messages"][0]["content"]

    def test_compare_environments_prompt_defaults(self):
        """Test compare-environments prompt with default arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt("compare-environments")

        assert "description" in result
        assert "messages" in result
        assert "staging" in result["description"]
        assert "production" in result["description"]
        assert "compare the parameters" in result["messages"][0]["content"]
        assert "different" in result["messages"][0]["content"]

    def test_compare_environments_prompt_custom_args(self):
        """Test compare-environments prompt with custom arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt(
            "compare-environments",
            {
                "environment1": "dev",
                "environment2": "qa",
                "project": "mobile-app",
            },
        )

        assert "dev" in result["description"]
        assert "qa" in result["description"]
        assert "dev" in result["messages"][0]["content"]
        assert "qa" in result["messages"][0]["content"]
        assert "mobile-app" in result["messages"][0]["content"]

    def test_update_secret_prompt_defaults(self):
        """Test update-secret prompt with default arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt("update-secret")

        assert "description" in result
        assert "messages" in result
        assert "SECRET_KEY" in result["description"]
        assert "SECRET_KEY" in result["messages"][0]["content"]
        assert "production" in result["messages"][0]["content"]
        assert "update it safely" in result["messages"][0]["content"]

    def test_update_secret_prompt_custom_args(self):
        """Test update-secret prompt with custom arguments"""
        handler = PromptsHandler()
        result = handler.get_prompt(
            "update-secret",
            {
                "parameter_name": "DB_PASSWORD",
                "environment": "staging",
                "project": "api-service",
            },
        )

        assert "DB_PASSWORD" in result["description"]
        assert "DB_PASSWORD" in result["messages"][0]["content"]
        assert "staging" in result["messages"][0]["content"]
        assert "api-service" in result["messages"][0]["content"]

    def test_unknown_prompt(self):
        """Test requesting an unknown prompt"""
        handler = PromptsHandler()
        result = handler.get_prompt("nonexistent-prompt")

        assert "description" in result
        assert "Unknown prompt" in result["description"]
        assert "messages" in result
        assert "not implemented" in result["messages"][0]["content"]
        assert "get-credentials" in result["messages"][0]["content"]
        assert "setup-environment" in result["messages"][0]["content"]
        assert "compare-environments" in result["messages"][0]["content"]
        assert "update-secret" in result["messages"][0]["content"]

    def test_prompt_with_none_arguments(self):
        """Test prompt with None arguments (should use defaults)"""
        handler = PromptsHandler()
        result = handler.get_prompt("get-credentials", None)

        assert "description" in result
        assert "messages" in result
        # Should use defaults when None is passed
        assert "database" in result["description"]
        assert "development" in result["description"]

    def test_prompt_with_empty_arguments(self):
        """Test prompt with empty dict arguments (should use defaults)"""
        handler = PromptsHandler()
        result = handler.get_prompt("update-secret", {})

        assert "description" in result
        assert "messages" in result
        # Should use defaults when empty dict is passed
        assert "SECRET_KEY" in result["description"]
        assert "production" in result["messages"][0]["content"]

    def test_all_prompts_have_required_structure(self):
        """Test that all prompts return the required structure"""
        handler = PromptsHandler()
        prompt_names = [
            "get-credentials",
            "setup-environment",
            "compare-environments",
            "update-secret",
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

        # get-credentials
        result = handler.get_prompt("get-credentials", {"service_type": "postgres"})
        assert "postgres" in result["description"].lower()

        # setup-environment
        result = handler.get_prompt("setup-environment", {"environment": "test-env"})
        assert "test-env" in result["description"].lower()

        # compare-environments
        result = handler.get_prompt(
            "compare-environments", {"environment1": "env1", "environment2": "env2"}
        )
        assert "env1" in result["description"].lower()
        assert "env2" in result["description"].lower()

        # update-secret
        result = handler.get_prompt("update-secret", {"parameter_name": "API_KEY"})
        assert "api_key" in result["description"].lower()
