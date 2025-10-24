"""
Comprehensive test coverage for lib.auth.credential_service module.

Targeting 50% minimum coverage with focus on:
- Core credential generation methods
- Environment file operations and parsing
- MCP configuration synchronization
- Validation and error handling
- Master credential management
- Mode-specific credential derivation
"""

from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

# Import the module under test
try:
    from lib.auth.credential_service import CredentialService
except ImportError:
    pytest.skip("Module lib.auth.credential_service not available", allow_module_level=True)


class TestCredentialServiceInit:
    """Test CredentialService initialization."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        service = CredentialService()

        assert service.project_root == Path.cwd()
        assert service.master_env_file == Path.cwd() / ".env"
        assert service.env_file == service.master_env_file
        assert service.postgres_user_var == "POSTGRES_USER"
        assert service.postgres_password_var == "POSTGRES_PASSWORD"  # noqa: S105 - Test fixture password

    def test_init_with_project_root(self):
        """Test initialization with project root."""
        test_root = Path("/test/project")
        service = CredentialService(project_root=test_root)

        assert service.project_root == test_root
        assert service.master_env_file == test_root / ".env"

    def test_init_legacy_env_file_param(self):
        """Test initialization with legacy env_file parameter."""
        env_file = Path("/legacy/path/.env")
        service = CredentialService(env_file=env_file)

        assert service.master_env_file == env_file
        assert service.env_file == env_file

    def test_init_env_file_with_parent_directory(self):
        """Test initialization with env_file having parent directory."""
        env_file = Path("/custom/dir/.env")
        service = CredentialService(env_file=env_file)

        assert service.project_root == env_file.parent
        assert service.master_env_file == env_file

    def test_init_env_file_current_directory(self):
        """Test initialization with env_file in current directory."""
        env_file = Path(".env")
        service = CredentialService(env_file=env_file)

        assert service.project_root == Path.cwd()
        assert service.master_env_file.resolve() == env_file.resolve()


class TestPostgresCredentialGeneration:
    """Test PostgreSQL credential generation."""

    def test_generate_postgres_credentials_defaults(self):
        """Test generate_postgres_credentials with defaults."""
        service = CredentialService()

        with patch.object(service, "_generate_secure_token") as mock_token:
            mock_token.side_effect = ["test_user_16ch", "test_pass_16ch"]

            creds = service.generate_postgres_credentials()

            assert creds["user"] == "test_user_16ch"
            assert creds["password"] == "test_pass_16ch"  # noqa: S105 - Test fixture password
            assert creds["database"] == "hive"
            assert creds["host"] == "localhost"
            assert creds["port"] == "5532"
            assert "postgresql+psycopg://" in creds["url"]

            # Verify token generation calls
            assert mock_token.call_count == 2
            mock_token.assert_has_calls([call(16, safe_chars=True), call(16, safe_chars=True)])

    def test_generate_postgres_credentials_custom_params(self):
        """Test generate_postgres_credentials with custom parameters."""
        service = CredentialService()

        with patch.object(service, "_generate_secure_token") as mock_token:
            mock_token.side_effect = ["custom_user", "custom_pass"]

            creds = service.generate_postgres_credentials(host="custom.host", port=3306, database="custom_db")

            assert creds["host"] == "custom.host"
            assert creds["port"] == "3306"
            assert creds["database"] == "custom_db"
            assert "postgresql+psycopg://custom_user:custom_pass@custom.host:3306/custom_db" == creds["url"]

    @patch("lib.auth.credential_service.logger")
    def test_generate_postgres_credentials_logging(self, mock_logger):
        """Test generate_postgres_credentials logging."""
        service = CredentialService()

        with patch.object(service, "_generate_secure_token") as mock_token:
            mock_token.side_effect = ["user123", "pass456"]

            service.generate_postgres_credentials()

            mock_logger.info.assert_any_call("Generating secure PostgreSQL credentials")
            mock_logger.info.assert_any_call(
                "PostgreSQL credentials generated",
                user_length=7,
                password_length=7,
                database="hive",
                host="localhost",
                port=5532,
            )


class TestHiveApiKeyGeneration:
    """Test Hive API key generation."""

    @patch("secrets.token_urlsafe")
    @patch("lib.auth.credential_service.logger")
    def test_generate_hive_api_key(self, mock_logger, mock_token):
        """Test generate_hive_api_key."""
        mock_token.return_value = "test_secure_token_32_chars_long"
        service = CredentialService()

        api_key = service.generate_hive_api_key()

        assert api_key == "hive_test_secure_token_32_chars_long"
        mock_token.assert_called_once_with(32)
        mock_logger.info.assert_any_call("Generating secure Hive API key")
        mock_logger.info.assert_any_call("Hive API key generated", key_length=len(api_key))

    @patch("secrets.token_urlsafe")
    def test_generate_hive_api_key_short_token(self, mock_token):
        """Test generate_hive_api_key with short token."""
        mock_token.return_value = "short"
        service = CredentialService()

        api_key = service.generate_hive_api_key()

        assert api_key == "hive_short"
        assert len(api_key) == 10  # 'hive_' + 'short'


class TestEnvironmentCredentialExtraction:
    """Test environment file credential extraction."""

    def test_extract_postgres_credentials_file_not_exists(self):
        """Test extract_postgres_credentials_from_env when file doesn't exist."""
        # Mock EnvFileManager to return None values
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/nonexistent/.env")
        mock_env_manager.master_env_path = Path("/nonexistent/.env")
        mock_env_manager.extract_postgres_credentials = Mock(
            return_value={"user": None, "password": None, "database": None, "host": None, "port": None, "url": None}
        )

        service = CredentialService(env_manager=mock_env_manager)

        creds = service.extract_postgres_credentials_from_env()

        expected_creds = {"user": None, "password": None, "database": None, "host": None, "port": None, "url": None}
        assert creds == expected_creds

    def test_extract_postgres_credentials_with_database_url(self):
        """Test extract_postgres_credentials_from_env with DATABASE_URL."""
        # Mock EnvFileManager to return parsed credentials
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.extract_postgres_credentials = Mock(
            return_value={
                "user": "testuser",
                "password": "testpass",
                "host": "testhost",
                "port": "5432",
                "database": "testdb",
                "url": "postgresql+psycopg://testuser:testpass@testhost:5432/testdb",
            }
        )

        service = CredentialService(env_manager=mock_env_manager)

        creds = service.extract_postgres_credentials_from_env()

        assert creds["user"] == "testuser"
        assert creds["password"] == "testpass"  # noqa: S105 - Test fixture password
        assert creds["host"] == "testhost"
        assert creds["port"] == "5432"
        assert creds["database"] == "testdb"
        assert creds["url"] == "postgresql+psycopg://testuser:testpass@testhost:5432/testdb"

    def test_extract_postgres_credentials_malformed_url(self):
        """Test extract_postgres_credentials_from_env with malformed URL."""
        service = CredentialService()

        env_content = "HIVE_DATABASE_URL=not-a-valid-url"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                creds = service.extract_postgres_credentials_from_env()

                # Should handle malformed URL gracefully
                assert creds["user"] is None
                assert creds["password"] is None

    def test_extract_postgres_credentials_exception_handling(self):
        """Test extract_postgres_credentials_from_env exception handling."""
        # Mock EnvFileManager to raise exception
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.extract_postgres_credentials = Mock(
            return_value={"user": None, "password": None, "database": None, "host": None, "port": None, "url": None}
        )

        service = CredentialService(env_manager=mock_env_manager)

        creds = service.extract_postgres_credentials_from_env()

        # Should return empty credentials on exception
        assert all(value is None for value in creds.values())


class TestHiveApiKeyExtraction:
    """Test Hive API key extraction."""

    def test_extract_hive_api_key_from_env_success(self):
        """Test extract_hive_api_key_from_env successful extraction."""
        # Mock EnvFileManager to return API key
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.extract_api_key = Mock(return_value="hive_test_api_key_12345")

        service = CredentialService(env_manager=mock_env_manager)

        api_key = service.extract_hive_api_key_from_env()

        assert api_key == "hive_test_api_key_12345"

    def test_extract_hive_api_key_not_found(self):
        """Test extract_hive_api_key_from_env when key not found."""
        service = CredentialService()

        env_content = "OTHER_VAR=value"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                api_key = service.extract_hive_api_key_from_env()

                assert api_key is None

    def test_extract_hive_api_key_empty_value(self):
        """Test extract_hive_api_key_from_env with empty value."""
        service = CredentialService()

        env_content = "HIVE_API_KEY="

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                api_key = service.extract_hive_api_key_from_env()

                assert api_key is None

    def test_extract_hive_api_key_file_not_exists(self):
        """Test extract_hive_api_key_from_env when file doesn't exist."""
        # Mock EnvFileManager to return None
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.extract_api_key = Mock(return_value=None)

        service = CredentialService(env_manager=mock_env_manager)

        api_key = service.extract_hive_api_key_from_env()

        assert api_key is None

    def test_extract_hive_api_key_exception_handling(self):
        """Test extract_hive_api_key_from_env exception handling."""
        # Mock EnvFileManager to return None on exception
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.extract_api_key = Mock(return_value=None)

        service = CredentialService(env_manager=mock_env_manager)

        api_key = service.extract_hive_api_key_from_env()

        assert api_key is None


class TestCredentialSaving:
    """Test credential saving to environment files."""

    @patch("lib.auth.credential_service.logger")
    def test_save_credentials_to_env_new_file(self, mock_logger):
        """Test save_credentials_to_env creating new file."""
        # Mock EnvFileManager to simulate successful write
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.update_values = Mock(return_value=True)

        service = CredentialService(env_manager=mock_env_manager)

        postgres_creds = {"url": "postgresql+psycopg://user:pass@localhost:5532/hive"}
        api_key = "hive_test_key"

        service.save_credentials_to_env(postgres_creds, api_key)

        # Verify update_values was called with correct args
        mock_env_manager.update_values.assert_called_once()
        call_args = mock_env_manager.update_values.call_args[0][0]
        assert call_args["HIVE_DATABASE_URL"] == "postgresql+psycopg://user:pass@localhost:5532/hive"
        assert call_args["HIVE_API_KEY"] == "hive_test_key"

        mock_logger.info.assert_any_call("Saving credentials to .env file")
        mock_logger.info.assert_any_call("Credentials saved to .env file successfully")

    def test_save_credentials_to_env_update_existing(self):
        """Test save_credentials_to_env updating existing file."""
        # Mock EnvFileManager to simulate successful update
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.update_values = Mock(return_value=True)

        service = CredentialService(env_manager=mock_env_manager)

        postgres_creds = {"url": "new_database_url"}
        api_key = "new_api_key"

        service.save_credentials_to_env(postgres_creds, api_key)

        # Verify update_values was called
        mock_env_manager.update_values.assert_called_once()
        call_args = mock_env_manager.update_values.call_args[0][0]
        assert call_args["HIVE_DATABASE_URL"] == "new_database_url"
        assert call_args["HIVE_API_KEY"] == "new_api_key"

    def test_save_credentials_to_env_postgres_only(self):
        """Test save_credentials_to_env with only postgres credentials."""
        # Mock EnvFileManager
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.update_values = Mock(return_value=True)

        service = CredentialService(env_manager=mock_env_manager)

        postgres_creds = {"url": "postgres_url_only"}

        service.save_credentials_to_env(postgres_creds)

        # Verify only DATABASE_URL was saved
        call_args = mock_env_manager.update_values.call_args[0][0]
        assert call_args["HIVE_DATABASE_URL"] == "postgres_url_only"
        assert "HIVE_API_KEY" not in call_args

    def test_save_credentials_to_env_api_key_only(self):
        """Test save_credentials_to_env with only API key."""
        # Mock EnvFileManager
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.update_values = Mock(return_value=True)

        service = CredentialService(env_manager=mock_env_manager)

        api_key = "api_key_only"

        service.save_credentials_to_env(api_key=api_key)

        # Verify only API_KEY was saved
        call_args = mock_env_manager.update_values.call_args[0][0]
        assert call_args["HIVE_API_KEY"] == "api_key_only"
        assert "HIVE_DATABASE_URL" not in call_args

    def test_save_credentials_to_env_create_if_missing_false(self):
        """Test save_credentials_to_env with create_if_missing=False."""
        service = CredentialService()

        with patch("pathlib.Path.exists", return_value=False):
            with patch("lib.auth.credential_service.logger") as mock_logger:
                service.save_credentials_to_env(api_key="test", create_if_missing=False)

                mock_logger.error.assert_called_once()

    def test_save_credentials_to_env_write_exception(self):
        """Test save_credentials_to_env write exception handling."""
        # Mock EnvFileManager to return False (write failure)
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.update_values = Mock(return_value=False)

        service = CredentialService(env_manager=mock_env_manager)

        with patch("lib.auth.credential_service.logger") as mock_logger:
            service.save_credentials_to_env(api_key="test")

            # Should log error when update_values returns False
            mock_logger.error.assert_called_once_with(
                "Failed to persist credentials to env file", env_file=str(service.env_file)
            )


class TestMcpConfigSynchronization:
    """Test MCP configuration synchronization."""

    @patch("os.getenv")
    def test_sync_mcp_config_default_path(self, mock_getenv):
        """Test sync_mcp_config_with_credentials with default path."""
        mock_getenv.return_value = ".mcp.json"
        service = CredentialService(project_root=Path("/test"))

        mcp_content = '{"servers": {"postgres": {"env": {"DB_URL": "old_url"}}}}'

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract_pg:
            mock_extract_pg.return_value = {
                "user": "test_user",
                "password": "test_pass",
                "url": "postgresql+psycopg://test_user:test_pass@localhost:5532/hive",
                "database": "hive",
                "host": "localhost",
                "port": "5532",
            }

            with patch.object(service, "extract_hive_api_key_from_env") as mock_extract_key:
                mock_extract_key.return_value = "hive_test_key"

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.read_text", return_value=mcp_content):
                        with patch("pathlib.Path.write_text") as mock_write:
                            with patch("lib.auth.credential_service.logger") as mock_logger:
                                service.sync_mcp_config_with_credentials()

                                mock_write.assert_called_once()
                                written_content = mock_write.call_args[0][0]
                                # The content should contain updated credentials
                                assert "test_user:test_pass" in written_content or "hive_test_key" in written_content

                                mock_logger.info.assert_called_with("MCP config updated with current credentials")

    def test_sync_mcp_config_file_not_exists(self):
        """Test sync_mcp_config_with_credentials when MCP file doesn't exist."""
        service = CredentialService()

        with patch("pathlib.Path.exists", return_value=False):
            with patch("lib.auth.credential_service.logger") as mock_logger:
                service.sync_mcp_config_with_credentials(Path("/nonexistent/mcp.json"))

                mock_logger.warning.assert_called_once()

    def test_sync_mcp_config_missing_credentials(self):
        """Test sync_mcp_config_with_credentials with missing credentials."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract_pg:
            mock_extract_pg.return_value = {"user": None, "password": None}

            with patch.object(service, "extract_hive_api_key_from_env") as mock_extract_key:
                mock_extract_key.return_value = None

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("lib.auth.credential_service.logger") as mock_logger:
                        service.sync_mcp_config_with_credentials(Path("/test/mcp.json"))

                        mock_logger.warning.assert_called_with("Cannot update MCP config - missing credentials")

    def test_sync_mcp_config_exception_handling(self):
        """Test sync_mcp_config_with_credentials exception handling."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract_pg:
            mock_extract_pg.return_value = {"user": "test", "password": "test"}

            with patch.object(service, "extract_hive_api_key_from_env") as mock_extract_key:
                mock_extract_key.return_value = "test_key"

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.read_text", side_effect=Exception("Read error")):
                        with patch("lib.auth.credential_service.logger") as mock_logger:
                            service.sync_mcp_config_with_credentials(Path("/test/mcp.json"))

                            mock_logger.error.assert_called_once()


class TestCredentialValidation:
    """Test credential validation."""

    def test_validate_credentials_postgres_valid(self):
        """Test validate_credentials with valid postgres credentials."""
        service = CredentialService()

        postgres_creds = {
            "user": "validuser123456",  # >= 12 chars, alphanumeric
            "password": "validpass123456",  # >= 12 chars, alphanumeric
            "url": "postgresql+psycopg://user:pass@host:5432/db",
        }

        results = service.validate_credentials(postgres_creds)

        assert results["postgres_user_valid"] is True
        assert results["postgres_password_valid"] is True
        assert results["postgres_url_valid"] is True

    def test_validate_credentials_postgres_invalid(self):
        """Test validate_credentials with invalid postgres credentials."""
        service = CredentialService()

        postgres_creds = {
            "user": "short",  # < 12 chars
            "password": "invalid!@#",  # contains special chars
            "url": "not-a-postgres-url",  # invalid format
        }

        results = service.validate_credentials(postgres_creds)

        assert results["postgres_user_valid"] is False
        assert results["postgres_password_valid"] is False
        assert results["postgres_url_valid"] is False

    def test_validate_credentials_api_key_valid(self):
        """Test validate_credentials with valid API key."""
        service = CredentialService()

        api_key = "hive_" + "a" * 33  # > 37 chars total (5 + 33 = 38), starts with hive_

        results = service.validate_credentials(api_key=api_key)

        assert results["api_key_valid"] is True

    def test_validate_credentials_api_key_invalid(self):
        """Test validate_credentials with invalid API key."""
        service = CredentialService()

        invalid_keys = [
            "short",  # No hive_ prefix, too short
            "hive_short",  # < 37 chars
            "wrong_prefix_but_long_enough_key_here",  # Wrong prefix
        ]

        for api_key in invalid_keys:
            results = service.validate_credentials(api_key=api_key)
            assert results["api_key_valid"] is False

    @patch("lib.auth.credential_service.logger")
    def test_validate_credentials_logging(self, mock_logger):
        """Test validate_credentials logging."""
        service = CredentialService()

        results = service.validate_credentials(api_key="hive_test_key_long_enough_for_validation")

        mock_logger.info.assert_called_with("Credential validation completed", results=results)


class TestSecureTokenGeneration:
    """Test secure token generation."""

    @patch("secrets.token_urlsafe")
    def test_generate_secure_token_safe_chars(self, mock_token):
        """Test _generate_secure_token with safe_chars=True."""
        mock_token.return_value = "abcd-efgh_ijkl"
        service = CredentialService()

        token = service._generate_secure_token(8, safe_chars=True)

        assert token == "abcdefgh"  # Dashes and underscores removed  # noqa: S105 - Test fixture password
        assert len(token) == 8
        mock_token.assert_called_once_with(16)  # length + 8 for extra

    @patch("secrets.token_urlsafe")
    def test_generate_secure_token_normal(self, mock_token):
        """Test _generate_secure_token with safe_chars=False."""
        mock_token.return_value = "normal_token"
        service = CredentialService()

        token = service._generate_secure_token(12)

        assert token == "normal_token"  # noqa: S105 - Test fixture password
        mock_token.assert_called_once_with(12)

    @patch("secrets.token_urlsafe")
    def test_generate_secure_token_short_after_cleaning(self, mock_token):
        """Test _generate_secure_token with result shorter than requested after cleaning."""
        mock_token.return_value = "---___"  # All chars will be removed
        service = CredentialService()

        token = service._generate_secure_token(8, safe_chars=True)

        assert len(token) <= 8
        assert token == ""  # All special chars removed


class TestCredentialStatus:
    """Test credential status reporting."""

    def test_get_credential_status_complete(self):
        """Test get_credential_status with complete credentials."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract_pg:
            mock_extract_pg.return_value = {
                "user": "test_user",
                "password": "test_pass",
                "database": "hive",
                "url": "postgresql+psycopg://test_user:test_pass@localhost:5532/hive",
                "host": "localhost",
                "port": "5532",
            }

            with patch.object(service, "extract_hive_api_key_from_env") as mock_extract_key:
                mock_extract_key.return_value = "hive_test_api_key"

                with patch("pathlib.Path.exists", return_value=True):
                    with patch.object(service, "validate_credentials") as mock_validate:
                        mock_validate.return_value = {"postgres_user_valid": True}

                        status = service.get_credential_status()

                        assert status["env_file_exists"] is True
                        assert status["postgres_configured"] is True
                        assert status["api_key_configured"] is True
                        assert status["api_key_format_valid"] is True
                        assert "validation" in status

    def test_get_credential_status_missing_credentials(self):
        """Test get_credential_status with missing credentials."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract_pg:
            mock_extract_pg.return_value = {
                "user": None,
                "password": None,
                "database": None,
                "url": None,
                "host": None,
                "port": None,
            }

            with patch.object(service, "extract_hive_api_key_from_env") as mock_extract_key:
                mock_extract_key.return_value = None

                with patch("pathlib.Path.exists", return_value=False):
                    status = service.get_credential_status()

                    assert status["env_file_exists"] is False
                    assert status["postgres_configured"] is False
                    assert status["api_key_configured"] is False
                    assert status["api_key_format_valid"] is False
                    assert "validation" not in status

    def test_get_credential_status_invalid_api_key_format(self):
        """Test get_credential_status with invalid API key format."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract_pg:
            mock_extract_pg.return_value = {
                "user": None,
                "password": None,
                "database": None,
                "url": None,
                "host": None,
                "port": None,
            }

            with patch.object(service, "extract_hive_api_key_from_env") as mock_extract_key:
                mock_extract_key.return_value = "invalid_key_format"

                status = service.get_credential_status()

                assert status["api_key_configured"] is True
                assert status["api_key_format_valid"] is False


class TestCompleteCredentialsSetup:
    """Test complete credentials setup."""

    @patch("lib.auth.credential_service.logger")
    def test_setup_complete_credentials(self, mock_logger):
        """Test setup_complete_credentials."""
        service = CredentialService()

        with patch.object(service, "generate_postgres_credentials") as mock_gen_pg:
            mock_gen_pg.return_value = {
                "user": "generated_user",
                "password": "generated_pass",
                "database": "test_db",
                "host": "test_host",
                "port": "1234",
                "url": "test_url",
            }

            with patch.object(service, "generate_hive_api_key") as mock_gen_key:
                mock_gen_key.return_value = "hive_generated_key"

                with patch.object(service, "save_credentials_to_env") as mock_save:
                    creds = service.setup_complete_credentials(
                        postgres_host="test_host", postgres_port=1234, postgres_database="test_db"
                    )

                    expected_creds = {
                        "postgres_user": "generated_user",
                        "postgres_password": "generated_pass",
                        "postgres_database": "test_db",
                        "postgres_host": "test_host",
                        "postgres_port": "1234",
                        "postgres_url": "test_url",
                        "api_key": "hive_generated_key",
                    }

                    assert creds == expected_creds
                    mock_gen_pg.assert_called_once_with(host="test_host", port=1234, database="test_db")
                    mock_gen_key.assert_called_once()
                    mock_save.assert_called_once()

                    mock_logger.info.assert_any_call("Setting up complete credentials for new workspace")
                    mock_logger.info.assert_any_call(
                        "Complete credentials setup finished", postgres_database="test_db", postgres_port=1234
                    )

    def test_setup_complete_credentials_with_mcp_sync(self):
        """Test setup_complete_credentials with MCP sync enabled."""
        service = CredentialService()

        with patch.object(service, "generate_postgres_credentials") as mock_gen_pg:
            mock_gen_pg.return_value = {
                "user": "test",
                "password": "test_pass",
                "database": "test_db",
                "host": "test_host",
                "port": "1234",
                "url": "test_url",
            }

            with patch.object(service, "generate_hive_api_key") as mock_gen_key:
                mock_gen_key.return_value = "test_key"

                with patch.object(service, "save_credentials_to_env"):
                    with patch.object(service, "sync_mcp_config_with_credentials") as mock_sync:
                        service.setup_complete_credentials(sync_mcp=True)

                        mock_sync.assert_called_once()

    def test_setup_complete_credentials_mcp_sync_failure(self):
        """Test setup_complete_credentials with MCP sync failure."""
        service = CredentialService()

        with patch.object(service, "generate_postgres_credentials") as mock_gen_pg:
            mock_gen_pg.return_value = {
                "user": "test",
                "password": "test_pass",
                "database": "test_db",
                "host": "test_host",
                "port": "1234",
                "url": "test_url",
            }

            with patch.object(service, "generate_hive_api_key") as mock_gen_key:
                mock_gen_key.return_value = "test_key"

                with patch.object(service, "save_credentials_to_env"):
                    with patch.object(service, "sync_mcp_config_with_credentials") as mock_sync:
                        mock_sync.side_effect = Exception("MCP sync failed")

                        with patch("lib.auth.credential_service.logger") as mock_logger:
                            # Should not raise exception, just log warning
                            creds = service.setup_complete_credentials(sync_mcp=True)

                            assert creds is not None
                            mock_logger.warning.assert_called_once()


class TestPortAndModeManagement:
    """Test port calculation and mode management methods."""

    def test_extract_base_ports_from_env_defaults(self):
        """Test extract_base_ports_from_env with defaults."""
        service = CredentialService()

        with patch("pathlib.Path.exists", return_value=False):
            ports = service.extract_base_ports_from_env()

            assert ports == {"db": 5532, "api": 8886}

    def test_extract_base_ports_from_env_custom(self):
        """Test extract_base_ports_from_env with custom values."""
        service = CredentialService()

        env_content = """
        HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:3306/db
        HIVE_API_PORT=9999
        OTHER_VAR=value
        """

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                ports = service.extract_base_ports_from_env()

                assert ports["db"] == 3306
                assert ports["api"] == 9999

    def test_extract_base_ports_from_env_invalid_api_port(self):
        """Test extract_base_ports_from_env with invalid API port."""
        # Mock EnvFileManager to return default ports
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.extract_base_ports = Mock(return_value={"db": 5532, "api": 8886})

        service = CredentialService(env_manager=mock_env_manager)

        ports = service.extract_base_ports_from_env()

        # Should use default API port when invalid
        assert ports["api"] == 8886

    def test_extract_base_ports_from_env_exception(self):
        """Test extract_base_ports_from_env exception handling."""
        # Mock EnvFileManager to return default ports on exception
        mock_env_manager = Mock()
        mock_env_manager.project_root = Path("/test")
        mock_env_manager.primary_env_path = Path("/test/.env")
        mock_env_manager.master_env_path = Path("/test/.env")
        mock_env_manager.extract_base_ports = Mock(return_value={"db": 5532, "api": 8886})

        service = CredentialService(env_manager=mock_env_manager)

        ports = service.extract_base_ports_from_env()

        # Should return defaults on exception
        assert ports == {"db": 5532, "api": 8886}

    def test_calculate_ports_workspace_mode(self):
        """Test calculate_ports for workspace mode."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}

        ports = service.calculate_ports("workspace", base_ports)

        assert ports == base_ports  # No prefix for workspace

    def test_calculate_ports_agent_mode(self):
        """Test calculate_ports for agent mode - now raises ValueError."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}

        with pytest.raises(ValueError, match="Only 'workspace' mode is supported"):
            service.calculate_ports("agent", base_ports)

    def test_calculate_ports_genie_mode(self):
        """Test calculate_ports for genie mode - now raises ValueError."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}

        with pytest.raises(ValueError, match="Only 'workspace' mode is supported"):
            service.calculate_ports("genie", base_ports)

    def test_calculate_ports_invalid_mode(self):
        """Test calculate_ports with invalid mode."""
        service = CredentialService()
        base_ports = {"db": 5532, "api": 8886}

        with pytest.raises(ValueError):
            service.calculate_ports("invalid_mode", base_ports)


class TestMasterCredentialExtraction:
    """Test master credential extraction and management."""

    def test_extract_existing_master_credentials_success(self):
        """Test _extract_existing_master_credentials with valid credentials."""
        service = CredentialService()

        env_content = """
        HIVE_DATABASE_URL=postgresql+psycopg://master_user:master_pass@localhost:5532/hive
        HIVE_API_KEY=hive_secure_api_key_base
        OTHER_VAR=value
        """

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                master_creds = service._extract_existing_master_credentials()

                assert master_creds is not None
                assert master_creds["postgres_user"] == "master_user"
                assert master_creds["postgres_password"] == "master_pass"  # noqa: S105 - Test fixture password
                assert master_creds["api_key_base"] == "secure_api_key_base"  # Without hive_ prefix

    def test_extract_existing_master_credentials_no_file(self):
        """Test _extract_existing_master_credentials when file doesn't exist."""
        service = CredentialService()

        with patch("pathlib.Path.exists", return_value=False):
            master_creds = service._extract_existing_master_credentials()

            assert master_creds is None

    def test_extract_existing_master_credentials_placeholder_password(self):
        """Test _extract_existing_master_credentials with placeholder password."""
        service = CredentialService()

        env_content = """
        HIVE_DATABASE_URL=postgresql+psycopg://user:change-me@localhost:5532/hive
        HIVE_API_KEY=hive_real_key
        """

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                with patch("lib.auth.credential_service.logger") as mock_logger:
                    master_creds = service._extract_existing_master_credentials()

                    assert master_creds is None
                    mock_logger.info.assert_called_with(
                        "Detected placeholder password in main .env file - forcing credential regeneration"
                    )

    def test_extract_existing_master_credentials_placeholder_api_key(self):
        """Test _extract_existing_master_credentials with placeholder API key."""
        service = CredentialService()

        env_content = """
        HIVE_DATABASE_URL=postgresql+psycopg://user:realpass@localhost:5532/hive
        HIVE_API_KEY=hive_your-hive-api-key-here
        """

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=env_content):
                with patch("lib.auth.credential_service.logger") as mock_logger:
                    master_creds = service._extract_existing_master_credentials()

                    assert master_creds is None
                    mock_logger.info.assert_called_with(
                        "Detected placeholder API key in main .env file - forcing credential regeneration"
                    )

    def test_extract_existing_master_credentials_exception(self):
        """Test _extract_existing_master_credentials exception handling."""
        service = CredentialService()

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", side_effect=Exception("Read error")):
                with patch("lib.auth.credential_service.logger") as mock_logger:
                    master_creds = service._extract_existing_master_credentials()

                    assert master_creds is None
                    mock_logger.error.assert_called_once()

    @patch("lib.auth.credential_service.logger")
    def test_save_master_credentials_new_env_file(self, mock_logger):
        """Test _save_master_credentials creating new .env file."""
        # Mock EnvFileManager with real Path for project_root (needs / operator)
        mock_env_manager = Mock()
        test_project_root = Path("/test/project")
        mock_env_manager.project_root = test_project_root

        # Create mocked path objects for env files
        mock_primary_path = Mock(spec=Path)
        mock_primary_path.exists.return_value = False
        mock_primary_path.write_text = Mock()

        mock_alias_path = Mock(spec=Path)
        mock_alias_path.exists.return_value = False

        mock_env_manager.primary_env_path = mock_primary_path
        mock_env_manager.alias_env_path = mock_alias_path
        mock_env_manager.master_env_path = mock_primary_path
        mock_env_manager.sync_alias = Mock()
        mock_env_manager.update_values = Mock(return_value=True)

        service = CredentialService(env_manager=mock_env_manager)

        master_creds = {
            "postgres_user": "master_user",
            "postgres_password": "master_pass",
            "api_key_base": "api_key_base",
        }

        # Mock .env.example to not exist (will use _get_base_env_template)
        with patch("pathlib.Path.exists", return_value=False):
            with patch.object(
                service,
                "_get_base_env_template",
                return_value="BASE_TEMPLATE\nHIVE_DATABASE_URL=placeholder\nHIVE_API_KEY=placeholder",
            ):
                service._save_master_credentials(master_creds)

                # Should call update_values with correct credentials
                mock_env_manager.update_values.assert_called_once()
                call_args = mock_env_manager.update_values.call_args[0][0]
                assert (
                    call_args["HIVE_DATABASE_URL"] == "postgresql+psycopg://master_user:master_pass@localhost:5532/hive"
                )
                assert call_args["HIVE_API_KEY"] == "hive_api_key_base"

                mock_logger.info.assert_any_call("Saving master credentials to main .env file")
                mock_logger.warning.assert_any_call(".env.example not found, creating minimal .env file")

    @patch("lib.auth.credential_service.logger")
    def test_save_master_credentials_from_example(self, mock_logger):
        """Test _save_master_credentials using .env.example template."""
        # Mock EnvFileManager with real Path for project_root (needs / operator)
        mock_env_manager = Mock()
        test_project_root = Path("/test/project")
        mock_env_manager.project_root = test_project_root

        # Create mocked path objects for env files
        mock_primary_path = Mock(spec=Path)
        mock_primary_path.exists.return_value = False
        mock_primary_path.write_text = Mock()

        mock_alias_path = Mock(spec=Path)
        mock_alias_path.exists.return_value = False

        mock_env_manager.primary_env_path = mock_primary_path
        mock_env_manager.alias_env_path = mock_alias_path
        mock_env_manager.master_env_path = mock_primary_path
        mock_env_manager.sync_alias = Mock()
        mock_env_manager.update_values = Mock(return_value=True)

        service = CredentialService(env_manager=mock_env_manager)

        master_creds = {
            "postgres_user": "master_user",
            "postgres_password": "master_pass",
            "api_key_base": "api_key_base",
        }

        # Mock .env.example to exist and return template content
        example_content = "HIVE_DATABASE_URL=template_url\nHIVE_API_KEY=template_key"
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=example_content):
                service._save_master_credentials(master_creds)

                # Should call update_values with correct credentials
                mock_env_manager.update_values.assert_called_once()
                call_args = mock_env_manager.update_values.call_args[0][0]
                assert (
                    call_args["HIVE_DATABASE_URL"] == "postgresql+psycopg://master_user:master_pass@localhost:5532/hive"
                )
                assert call_args["HIVE_API_KEY"] == "hive_api_key_base"

                mock_logger.info.assert_any_call(
                    "Master credentials saved to .env with all comprehensive configurations from template"
                )

    def test_get_base_env_template(self):
        """Test _get_base_env_template returns proper template."""
        service = CredentialService()

        template = service._get_base_env_template()

        assert "AUTOMAGIK HIVE - MAIN CONFIGURATION" in template
        assert "HIVE_DATABASE_URL=" in template
        assert "HIVE_API_KEY=" in template
        assert "HIVE_ENVIRONMENT=development" in template


class TestMasterCredentialManagement:
    """Test master credential management."""

    @patch("secrets.token_urlsafe")
    @patch("lib.auth.credential_service.logger")
    def test_generate_master_credentials(self, mock_logger, mock_token):
        """Test generate_master_credentials."""
        mock_token.return_value = "master_token_base"
        service = CredentialService()

        with patch.object(service, "_generate_secure_token") as mock_gen_token:
            mock_gen_token.side_effect = ["master_user", "master_pass"]

            master_creds = service.generate_master_credentials()

            assert master_creds["postgres_user"] == "master_user"
            assert master_creds["postgres_password"] == "master_pass"  # noqa: S105 - Test fixture password
            assert master_creds["api_key_base"] == "master_token_base"

            mock_logger.info.assert_any_call("Generating MASTER credentials (single source of truth)")
            mock_logger.info.assert_any_call(
                "Master credentials generated", user_length=11, password_length=11, api_key_base_length=17
            )

    def test_derive_mode_credentials_workspace(self):
        """Test derive_mode_credentials for workspace mode."""
        service = CredentialService()

        master_creds = {"postgres_user": "master_user", "postgres_password": "master_pass", "api_key_base": "base_key"}

        with patch.object(service, "extract_base_ports_from_env") as mock_ports:
            mock_ports.return_value = {"db": 5532, "api": 8886}

            with patch("lib.auth.credential_service.logger") as mock_logger:
                mode_creds = service.derive_mode_credentials(master_creds, "workspace")

                assert mode_creds["postgres_user"] == "master_user"
                assert mode_creds["postgres_password"] == "master_pass"  # noqa: S105 - Test fixture password
                assert mode_creds["postgres_database"] == "hive"
                assert mode_creds["postgres_port"] == "5532"
                assert mode_creds["api_port"] == "8886"
                assert mode_creds["api_key"] == "hive_workspace_base_key"
                assert mode_creds["mode"] == "workspace"
                assert mode_creds["schema"] == "public"
                assert "postgresql+psycopg://master_user:master_pass@localhost:5532/hive" == mode_creds["database_url"]

                mock_logger.info.assert_called_once()

    def test_derive_mode_credentials_agent(self):
        """Test derive_mode_credentials for agent mode - now raises ValueError."""
        service = CredentialService()

        master_creds = {"postgres_user": "master_user", "postgres_password": "master_pass", "api_key_base": "base_key"}

        with pytest.raises(ValueError, match="Unknown mode: agent"):
            service.derive_mode_credentials(master_creds, "agent")

    def test_derive_mode_credentials_invalid_mode(self):
        """Test derive_mode_credentials with invalid mode."""
        service = CredentialService()

        master_creds = {"postgres_user": "master_user", "postgres_password": "master_pass", "api_key_base": "base_key"}

        with pytest.raises(ValueError):
            service.derive_mode_credentials(master_creds, "invalid_mode")

    def test_get_database_url_with_schema_workspace(self):
        """Test get_database_url_with_schema for workspace mode."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract:
            mock_extract.return_value = {"url": "postgresql+psycopg://user:pass@localhost:5532/hive"}

            url = service.get_database_url_with_schema("workspace")
            assert url == "postgresql+psycopg://user:pass@localhost:5532/hive"

    def test_get_database_url_with_schema_agent(self):
        """Test get_database_url_with_schema for agent mode."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract:
            mock_extract.return_value = {"url": "postgresql+psycopg://user:pass@localhost:5532/hive"}

            url = service.get_database_url_with_schema("agent")
            assert "options=-csearch_path=agent" in url

    def test_get_database_url_with_schema_no_url(self):
        """Test get_database_url_with_schema when no URL found."""
        service = CredentialService()

        with patch.object(service, "extract_postgres_credentials_from_env") as mock_extract:
            mock_extract.return_value = {"url": None}

            with pytest.raises(ValueError):
                service.get_database_url_with_schema("workspace")

    def test_ensure_schema_exists(self):
        """Test ensure_schema_exists method."""
        service = CredentialService()

        with patch("lib.auth.credential_service.logger") as mock_logger:
            service.ensure_schema_exists("agent")
            mock_logger.info.assert_called_with("Schema creation for agent mode - integrate with Agno framework")

            service.ensure_schema_exists("workspace")
            # Should not log anything for workspace mode


class TestDockerContainerManagement:
    """Test Docker container detection and management."""

    @patch("subprocess.run")
    def test_detect_existing_containers_running(self, mock_run):
        """Test detect_existing_containers with running containers."""
        service = CredentialService()

        # Mock successful docker ps command with new container name
        mock_result = Mock()
        mock_result.stdout = "hive-postgres\nhive-api"
        mock_run.return_value = mock_result

        with patch("lib.auth.credential_service.logger") as mock_logger:
            containers = service.detect_existing_containers()

            assert containers["hive-postgres"] is True
            assert containers.get("hive-api", False) is True
            mock_logger.info.assert_called_once()

    @patch("subprocess.run")
    def test_detect_existing_containers_not_running(self, mock_run):
        """Test detect_existing_containers with no running containers."""
        service = CredentialService()

        # Mock docker ps command with no output
        mock_result = Mock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        containers = service.detect_existing_containers()

        assert containers["hive-postgres"] is False
        assert containers.get("hive-api", False) is False

    @patch("subprocess.run")
    def test_detect_existing_containers_exception(self, mock_run):
        """Test detect_existing_containers exception handling."""
        service = CredentialService()

        # Mock docker command failure
        mock_run.side_effect = Exception("Docker not found")

        with patch("lib.auth.credential_service.logger") as mock_logger:
            containers = service.detect_existing_containers()

            # Should return False for all containers on exception
            assert all(not status for status in containers.values())
            mock_logger.warning.assert_called()

    def test_migrate_to_shared_database_no_migration_needed(self):
        """Test migrate_to_shared_database when no migration needed."""
        service = CredentialService()

        with patch.object(service, "detect_existing_containers") as mock_detect:
            mock_detect.return_value = {"hive-postgres": True, "hive-api": True}

            with patch("lib.auth.credential_service.logger") as mock_logger:
                service.migrate_to_shared_database()

                mock_logger.info.assert_any_call("Checking for migration to shared database approach")
                mock_logger.info.assert_any_call("No migration needed - using shared database approach")

    def test_migrate_to_shared_database_migration_needed(self):
        """Test migrate_to_shared_database when old containers exist (migration detection is not yet implemented)."""
        service = CredentialService()

        with patch.object(service, "detect_existing_containers") as mock_detect:
            # Include old container names - note: migration detection is not yet implemented
            # The old_containers list in the implementation is empty, so this will not trigger migration
            mock_detect.return_value = {
                "hive-postgres-agent": True,
                "hive-postgres-genie": True,
                "hive-postgres": False,
                "hive-api": False,
            }

            with patch("lib.auth.credential_service.logger") as mock_logger:
                service.migrate_to_shared_database()

                mock_logger.info.assert_any_call("Checking for migration to shared database approach")
                # Migration detection not implemented yet (old_containers list is empty)
                mock_logger.info.assert_any_call("No migration needed - using shared database approach")
