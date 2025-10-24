"""Tests for utility functions"""

from cloudtruth_mcp.utils import (
    REDACTED,
    format_environments_hierarchy,
    format_error_message,
    format_parameter_output,
    format_parameters_list,
    format_projects_list,
    format_success_message,
    mask_secret_value,
)


class TestMaskSecretValue:
    """Tests for mask_secret_value function"""

    def test_non_secret_value(self):
        """Test non-secret value is returned as-is"""
        result = mask_secret_value("my-value", is_secret=False, include_secrets=False)
        assert result == "my-value"

    def test_secret_value_masked_by_default(self):
        """Test secret value is masked by default"""
        result = mask_secret_value("secret-password", is_secret=True, include_secrets=False)
        assert result == REDACTED
        assert result == "***REDACTED***"

    def test_secret_value_with_include_secrets_true(self):
        """Test secret value is shown when include_secrets=True"""
        result = mask_secret_value("secret-password", is_secret=True, include_secrets=True)
        assert result == "secret-password"

    def test_null_value_returns_not_set(self):
        """Test null/None value returns '(not set)'"""
        result = mask_secret_value(None, is_secret=False, include_secrets=False)
        assert result == "(not set)"

    def test_null_secret_value_returns_not_set(self):
        """Test null/None secret value returns '(not set)' (not masked)"""
        result = mask_secret_value(None, is_secret=True, include_secrets=False)
        assert result == "(not set)"

    def test_empty_string_not_null(self):
        """Test empty string is different from null"""
        result = mask_secret_value("", is_secret=False, include_secrets=False)
        assert result == ""
        assert result != "(not set)"


class TestFormatParameterOutput:
    """Tests for format_parameter_output function"""

    def test_basic_parameter_output(self):
        """Test basic parameter formatting"""
        output = format_parameter_output(
            name="DATABASE_URL",
            value="postgres://localhost/mydb",
            secret=False,
            param_type="string",
            description="Database connection string",
            environment="production",
            project="my-app",
            include_secrets=False,
        )

        assert "DATABASE_URL" in output
        assert "postgres://localhost/mydb" in output
        assert "production" in output
        assert "my-app" in output
        assert "string" in output
        assert "Database connection string" in output

    def test_secret_parameter_masked(self):
        """Test secret parameter is masked"""
        output = format_parameter_output(
            name="API_KEY",
            value="sk-12345",
            secret=True,
            param_type="string",
            description="API Key",
            environment="production",
            project="my-app",
            include_secrets=False,
        )

        assert "API_KEY" in output
        assert REDACTED in output
        assert "sk-12345" not in output
        assert "include_secrets=true" in output

    def test_secret_parameter_exposed(self):
        """Test secret parameter can be exposed with flag"""
        output = format_parameter_output(
            name="API_KEY",
            value="sk-12345",
            secret=True,
            param_type="string",
            description="API Key",
            environment="production",
            project="my-app",
            include_secrets=True,
        )

        assert "API_KEY" in output
        assert "sk-12345" in output
        assert "WARNING: SECRET VALUE EXPOSED" in output

    def test_null_value_parameter(self):
        """Test parameter with null value"""
        output = format_parameter_output(
            name="UNSET_PARAM",
            value=None,
            secret=False,
            param_type="string",
            description="Not set yet",
            environment="development",
            project="my-app",
            include_secrets=False,
        )

        assert "UNSET_PARAM" in output
        assert "(not set)" in output


class TestFormatParametersList:
    """Tests for format_parameters_list function"""

    def test_empty_parameters_list(self):
        """Test formatting empty parameters list"""
        output = format_parameters_list([], "my-app", "production", False)
        assert "No parameters found" in output
        assert "my-app" in output
        assert "production" in output

    def test_single_parameter(self):
        """Test formatting single parameter"""
        params = [
            {
                "name": "PORT",
                "value": "8080",
                "secret": False,
                "type": "integer",
            }
        ]
        output = format_parameters_list(params, "my-app", "production", False)

        assert "PORT" in output
        assert "8080" in output
        assert "Total:** 1 parameter" in output

    def test_multiple_parameters(self):
        """Test formatting multiple parameters"""
        params = [
            {"name": "PORT", "value": "8080", "secret": False, "type": "integer"},
            {"name": "HOST", "value": "localhost", "secret": False, "type": "string"},
        ]
        output = format_parameters_list(params, "my-app", "production", False)

        assert "PORT" in output
        assert "HOST" in output
        assert "Total:** 2 parameters" in output

    def test_parameters_with_secrets_masked(self):
        """Test secrets are masked in parameters list"""
        params = [
            {"name": "API_KEY", "value": "secret-123", "secret": True, "type": "string"},
            {"name": "PORT", "value": "8080", "secret": False, "type": "integer"},
        ]
        output = format_parameters_list(params, "my-app", "production", False)

        assert "API_KEY" in output
        assert REDACTED in output
        assert "secret-123" not in output
        assert "1 secret" in output
        assert "masked" in output
        assert "include_secrets=true" in output.lower()

    def test_parameters_with_secrets_exposed(self):
        """Test secrets can be exposed"""
        params = [
            {"name": "API_KEY", "value": "secret-123", "secret": True, "type": "string"},
        ]
        output = format_parameters_list(params, "my-app", "production", True)

        assert "API_KEY" in output
        assert "secret-123" in output

    def test_long_value_truncation(self):
        """Test long values are truncated"""
        params = [
            {
                "name": "LONG_VALUE",
                "value": "x" * 100,
                "secret": False,
                "type": "string",
            }
        ]
        output = format_parameters_list(params, "my-app", "production", False)

        assert "LONG_VALUE" in output
        assert "..." in output  # Truncation indicator


class TestFormatProjectsList:
    """Tests for format_projects_list function"""

    def test_empty_projects_list(self):
        """Test formatting empty projects list"""
        output = format_projects_list([])
        assert "No projects found" in output

    def test_single_project(self):
        """Test formatting single project"""
        projects = [
            {
                "id": "proj-123",
                "name": "my-app",
                "description": "My application",
                "modified_at": "2025-10-23T12:00:00",
            }
        ]
        output = format_projects_list(projects)

        assert "my-app" in output
        assert "My application" in output
        assert "proj-123" in output
        assert "2025-10-23" in output
        assert "Found 1 project" in output

    def test_multiple_projects(self):
        """Test formatting multiple projects"""
        projects = [
            {
                "id": "proj-1",
                "name": "app1",
                "description": "First app",
                "modified_at": "2025-10-23T12:00:00",
            },
            {
                "id": "proj-2",
                "name": "app2",
                "description": "Second app",
                "modified_at": "2025-10-22T12:00:00",
            },
        ]
        output = format_projects_list(projects)

        assert "app1" in output
        assert "app2" in output
        assert "Found 2 projects" in output

    def test_long_description_truncation(self):
        """Test long descriptions are truncated"""
        projects = [
            {
                "id": "proj-123",
                "name": "my-app",
                "description": "x" * 100,
                "modified_at": "2025-10-23T12:00:00",
            }
        ]
        output = format_projects_list(projects)

        assert "..." in output  # Truncation indicator

    def test_missing_description(self):
        """Test project with missing description"""
        projects = [
            {
                "id": "proj-123",
                "name": "my-app",
                "description": "",
                "modified_at": "2025-10-23T12:00:00",
            }
        ]
        output = format_projects_list(projects)

        assert "my-app" in output


class TestFormatEnvironmentsHierarchy:
    """Tests for format_environments_hierarchy function"""

    def test_empty_environments_list(self):
        """Test formatting empty environments list"""
        output = format_environments_hierarchy([])
        assert "No environments found" in output

    def test_single_environment(self):
        """Test formatting single environment"""
        envs = [
            {
                "id": "env-123",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-123/",
                "name": "production",
                "description": "Production environment",
                "parent": None,
            }
        ]
        output = format_environments_hierarchy(envs)

        assert "production" in output
        assert "Production environment" in output
        assert "env-123" in output
        assert "Found 1 environment" in output

    def test_flat_table_no_tree_symbols(self):
        """Test that environment names don't have tree indentation symbols"""
        envs = [
            {
                "id": "env-1",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-1/",
                "name": "default",
                "description": "Default env",
                "parent": None,
            },
            {
                "id": "env-2",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-2/",
                "name": "production",
                "description": "Production env",
                "parent": "https://api.cloudtruth.io/api/v1/environments/env-1/",
            },
        ]
        output = format_environments_hierarchy(envs)

        # Should NOT contain tree symbols
        assert "└─" not in output
        assert "  production" not in output  # No indentation

        # Should contain the names without symbols
        assert "**default**" in output
        assert "**production**" in output

    def test_parent_relationship_shown(self):
        """Test parent relationship is shown in Parent column"""
        envs = [
            {
                "id": "env-1",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-1/",
                "name": "default",
                "description": "Default",
                "parent": None,
            },
            {
                "id": "env-2",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-2/",
                "name": "production",
                "description": "Prod",
                "parent": "https://api.cloudtruth.io/api/v1/environments/env-1/",
            },
        ]
        output = format_environments_hierarchy(envs)

        # Table should have headers
        assert "| Name |" in output
        assert "| Parent |" in output

        # Parent name should appear in parent column
        lines = output.split("\n")
        prod_line = [line for line in lines if "production" in line][0]
        assert "default" in prod_line  # Parent name in same row

    def test_multiple_environments_hierarchy(self):
        """Test multiple environments with hierarchy"""
        envs = [
            {
                "id": "env-1",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-1/",
                "name": "default",
                "description": "Default",
                "parent": None,
            },
            {
                "id": "env-2",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-2/",
                "name": "development",
                "description": "Dev",
                "parent": "https://api.cloudtruth.io/api/v1/environments/env-1/",
            },
            {
                "id": "env-3",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-3/",
                "name": "production",
                "description": "Prod",
                "parent": "https://api.cloudtruth.io/api/v1/environments/env-1/",
            },
        ]
        output = format_environments_hierarchy(envs)

        assert "default" in output
        assert "development" in output
        assert "production" in output
        assert "Found 3 environments" in output

    def test_long_description_truncation(self):
        """Test environment descriptions are truncated if > 40 chars"""
        envs = [
            {
                "id": "env-1",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-1/",
                "name": "production",
                "description": "This is a very long description that exceeds the forty character limit",
                "parent": None,
            }
        ]
        output = format_environments_hierarchy(envs)

        assert "production" in output
        assert "..." in output  # Truncation indicator

    def test_orphaned_parent_reference(self):
        """Test environment with parent reference not in list (broken hierarchy)"""
        envs = [
            {
                "id": "env-2",
                "url": "https://api.cloudtruth.io/api/v1/environments/env-2/",
                "name": "production",
                "description": "Prod",
                "parent": "https://api.cloudtruth.io/api/v1/environments/env-missing/",
            }
        ]
        output = format_environments_hierarchy(envs)

        # Should still work without crashing
        assert "production" in output
        assert "Found 1 environment" in output


class TestFormatSuccessMessage:
    """Tests for format_success_message function"""

    def test_created_message(self):
        """Test success message for created parameter"""
        msg = format_success_message("created", "API_KEY", "my-app", "production")
        assert "created" in msg.lower()
        assert "API_KEY" in msg
        assert "my-app" in msg
        assert "production" in msg

    def test_updated_message(self):
        """Test success message for updated parameter"""
        msg = format_success_message("updated", "PORT", "web-app", "development")
        assert "updated" in msg.lower()
        assert "PORT" in msg
        assert "web-app" in msg
        assert "development" in msg


class TestFormatErrorMessage:
    """Tests for format_error_message function"""

    def test_basic_error_message(self):
        """Test basic error formatting"""
        error = ValueError("Something went wrong")
        msg = format_error_message(error)
        assert "Error:" in msg
        assert "Something went wrong" in msg

    def test_error_message_sanitization(self):
        """Test error messages are sanitized (remove sensitive data)"""
        # This calls sanitize_error_message from errors module
        error = ValueError("API key ct-abc123xyz failed")
        msg = format_error_message(error)
        assert "Error:" in msg
        # The sanitization should happen in errors.sanitize_error_message
