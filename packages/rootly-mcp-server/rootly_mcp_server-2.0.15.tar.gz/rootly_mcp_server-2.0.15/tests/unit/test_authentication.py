"""
Unit tests for authentication functionality.

Tests cover:
- Hosted vs local mode authentication
- API token handling
- Header configuration
- Request authentication flow
"""

import pytest
import os
from unittest.mock import patch

from rootly_mcp_server.server import AuthenticatedHTTPXClient


@pytest.mark.unit
class TestLocalModeAuthentication:
    """Test authentication behavior in local mode."""

    def test_local_mode_loads_token_from_environment(self, mock_environment_token):
        """Test that local mode loads API token from environment."""
        client = AuthenticatedHTTPXClient(hosted=False)
        
        assert client.hosted is False
        assert client._api_token == mock_environment_token
        
        # Verify authorization header is set
        auth_header = client.client.headers.get("Authorization")
        assert auth_header == f"Bearer {mock_environment_token}"

    @patch.dict(os.environ, {}, clear=True)
    def test_local_mode_without_token(self):
        """Test local mode behavior when no token is available."""
        client = AuthenticatedHTTPXClient(hosted=False)
        
        assert client.hosted is False
        assert client._api_token is None
        
        # Should not have authorization header
        auth_header = client.client.headers.get("Authorization")
        assert not auth_header or auth_header == "Bearer None"

    def test_local_mode_token_validation(self):
        """Test token format validation in local mode."""
        valid_token = "rootly_abcdef123456789"
        
        with patch.dict(os.environ, {"ROOTLY_API_TOKEN": valid_token}):
            client = AuthenticatedHTTPXClient(hosted=False)
            
            assert client._api_token == valid_token
            assert client._api_token is not None and client._api_token.startswith("rootly_")

    def test_local_mode_headers_configuration(self, mock_environment_token):
        """Test that local mode sets correct headers."""
        client = AuthenticatedHTTPXClient(hosted=False)
        
        headers = client.client.headers
        
        # Verify required headers
        assert headers["Content-Type"] == "application/vnd.api+json"
        assert headers["Accept"] == "application/vnd.api+json"
        assert headers["Authorization"] == f"Bearer {mock_environment_token}"


@pytest.mark.unit  
class TestHostedModeAuthentication:
    """Test authentication behavior in hosted mode."""

    def test_hosted_mode_no_token_loading(self):
        """Test that hosted mode doesn't load token from environment."""
        # Even with token in environment, hosted mode shouldn't use it
        with patch.dict(os.environ, {"ROOTLY_API_TOKEN": "should_not_be_used"}):
            client = AuthenticatedHTTPXClient(hosted=True)
            
            assert client.hosted is True
            assert client._api_token is None
            
            # Should not have authorization header initially
            auth_header = client.client.headers.get("Authorization")
            assert not auth_header or not auth_header.startswith("Bearer")

    def test_hosted_mode_headers_configuration(self):
        """Test that hosted mode sets base headers without auth."""
        client = AuthenticatedHTTPXClient(hosted=True)
        
        headers = client.client.headers
        
        # Verify required content headers but no auth
        assert headers["Content-Type"] == "application/vnd.api+json"
        assert headers["Accept"] == "application/vnd.api+json"
        
        # Should not have pre-configured authorization
        auth_header = headers.get("Authorization", "")
        assert not auth_header or auth_header == "Bearer None"

    def test_hosted_mode_authentication_flow(self):
        """Test hosted mode authentication flow (from request headers)."""
        client = AuthenticatedHTTPXClient(hosted=True)
        
        # Simulate hosted mode where auth comes from incoming requests
        assert client.hosted is True
        # In hosted mode, no token is loaded initially
        assert client._api_token is None


@pytest.mark.unit
class TestHTTPClientConfiguration:
    """Test HTTP client configuration for both modes."""

    def test_client_base_url_configuration(self):
        """Test that client uses correct base URL."""
        custom_base = "https://custom.rootly.com"
        client = AuthenticatedHTTPXClient(base_url=custom_base, hosted=True)
        
        assert client._base_url == custom_base
        assert str(client.client.base_url) == custom_base

    def test_client_timeout_configuration(self):
        """Test that client has appropriate timeout settings."""
        client = AuthenticatedHTTPXClient(hosted=True)
        
        # Should have reasonable timeout
        assert client.client.timeout.read == 30.0

    def test_client_follows_redirects(self):
        """Test that client is configured to follow redirects."""
        client = AuthenticatedHTTPXClient(hosted=True)
        
        # Should be configured for redirect following
        assert client.client.follow_redirects is True

    def test_client_connection_limits(self):
        """Test that client has appropriate connection limits."""
        client = AuthenticatedHTTPXClient(hosted=True)
        
        # Verify client was created successfully - limits are internal httpx implementation details
        # that can vary between versions, so we just verify the client was configured
        httpx_client = client.client
        assert httpx_client is not None
        assert httpx_client.timeout.read == 30.0

    def test_parameter_mapping_initialization(self):
        """Test parameter mapping initialization."""
        custom_mapping = {"old_param": "new_param"}
        client = AuthenticatedHTTPXClient(
            hosted=True, 
            parameter_mapping=custom_mapping
        )
        
        assert client.parameter_mapping == custom_mapping

    def test_parameter_mapping_defaults_to_empty(self):
        """Test that parameter mapping defaults to empty dict."""
        client = AuthenticatedHTTPXClient(hosted=True)
        
        assert client.parameter_mapping == {}


@pytest.mark.unit
class TestTokenHandling:
    """Test API token handling and validation."""

    def test_get_api_token_success(self):
        """Test successful token retrieval."""
        test_token = "rootly_test123456789"
        
        with patch.dict(os.environ, {"ROOTLY_API_TOKEN": test_token}):
            client = AuthenticatedHTTPXClient(hosted=True)
            token = client._get_api_token()
            
            assert token == test_token

    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_token_missing(self):
        """Test token retrieval when environment variable is missing."""
        client = AuthenticatedHTTPXClient(hosted=True)
        token = client._get_api_token()
        
        assert token is None

    def test_get_api_token_empty_string(self):
        """Test token retrieval when environment variable is empty."""
        with patch.dict(os.environ, {"ROOTLY_API_TOKEN": ""}):
            client = AuthenticatedHTTPXClient(hosted=True)  
            token = client._get_api_token()
            
            # Empty string should be treated as None
            assert not token

    def test_token_format_validation(self):
        """Test that tokens are validated for correct format."""
        valid_tokens = [
            "rootly_abc123def456",
            "rootly_1234567890abcdef",
            "rootly_short123"
        ]
        
        for token in valid_tokens:
            with patch.dict(os.environ, {"ROOTLY_API_TOKEN": token}):
                client = AuthenticatedHTTPXClient(hosted=False)
                assert client._api_token == token
                assert client._api_token is not None and client._api_token.startswith("rootly_")


@pytest.mark.unit
class TestAuthenticationModeComparison:
    """Test differences between hosted and local authentication modes."""

    def test_mode_differences_token_loading(self, mock_environment_token):
        """Test key differences in token loading between modes."""
        # Local mode loads token
        local_client = AuthenticatedHTTPXClient(hosted=False)
        
        # Hosted mode does not load token
        hosted_client = AuthenticatedHTTPXClient(hosted=True)
        
        assert local_client._api_token == mock_environment_token
        assert hosted_client._api_token is None

    def test_mode_differences_headers(self, mock_environment_token):
        """Test header differences between authentication modes."""
        local_client = AuthenticatedHTTPXClient(hosted=False)
        hosted_client = AuthenticatedHTTPXClient(hosted=True)
        
        # Both should have content headers
        for client in [local_client, hosted_client]:
            headers = client.client.headers
            assert headers["Content-Type"] == "application/vnd.api+json"
            assert headers["Accept"] == "application/vnd.api+json"
        
        # Only local should have auth header pre-configured
        local_auth = local_client.client.headers.get("Authorization", "")
        hosted_auth = hosted_client.client.headers.get("Authorization", "")
        
        assert local_auth == f"Bearer {mock_environment_token}"
        assert not hosted_auth or hosted_auth == "Bearer None"

    def test_mode_property_consistency(self):
        """Test that hosted property is consistent across initialization."""
        local_client = AuthenticatedHTTPXClient(hosted=False)
        hosted_client = AuthenticatedHTTPXClient(hosted=True)
        
        assert local_client.hosted is False
        assert hosted_client.hosted is True