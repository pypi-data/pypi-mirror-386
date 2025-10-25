"""Tests for HttpClient in QaPyTest."""

import logging
from unittest.mock import MagicMock, patch

import httpx

from qapytest import HttpClient


class TestHttpClient:
    """Test cases for HttpClient functionality."""

    def test_http_client_initialization(self) -> None:
        """Test HttpClient initialization with default parameters."""
        client = HttpClient()
        assert isinstance(client, httpx.Client)
        assert client.base_url == ""
        assert str(client.timeout) == "Timeout(timeout=10.0)"

    def test_http_client_initialization_with_params(self) -> None:
        """Test HttpClient initialization with custom parameters."""
        base_url = "https://api.example.com"
        timeout = 30.0
        verify = False

        client = HttpClient(base_url=base_url, timeout=timeout, verify=verify)
        assert client.base_url == base_url
        assert str(client.timeout) == f"Timeout(timeout={timeout})"
        """Test that logger is properly configured."""
        client = HttpClient()
        assert hasattr(client, "_logger")
        assert client._logger.name == "HttpClient"  # noqa: SLF001

    def test_external_loggers_silenced(self) -> None:
        """Test that httpx and httpcore loggers are set to WARNING level."""
        HttpClient()

        httpx_logger = logging.getLogger("httpx")
        httpcore_logger = logging.getLogger("httpcore")

        assert httpx_logger.level == logging.WARNING
        assert httpcore_logger.level == logging.WARNING

    @patch("httpx.Client.request")
    def test_request_logging(self, mock_request: MagicMock) -> None:
        """Test that requests are properly logged."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/test"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.123
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"test": "data"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "info") as mock_info, patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("GET", "https://api.example.com/test")

            assert response == mock_response

            assert any("Sending HTTP" in str(call) for call in mock_info.call_args_list)
            mock_info.assert_any_call("Response status code: 200")
            mock_info.assert_any_call("Response time: 0.123 s")

            # Check that headers are logged in JSON format
            mock_debug.assert_any_call('Request headers: {"Content-Type": "application/json"}')
            mock_debug.assert_any_call('Request body (JSON): {"test": "data"}')
            mock_debug.assert_any_call('Response headers: {"Content-Type": "application/json"}')
            mock_debug.assert_any_call("Response body: <empty>")

    @patch("httpx.Client.get")
    def test_get_method_delegation(self, mock_get: MagicMock) -> None:
        """Test that GET method is properly delegated."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.url = "https://api.example.com/users"
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.request.headers = {}
        mock_response.request.content = b""
        mock_response.headers = {}
        mock_response.text = "[]"
        mock_get.return_value = mock_response

        client = HttpClient(base_url="https://api.example.com")
        response = client.get("/users")

        mock_get.assert_called_once_with("/users")
        assert response == mock_response

    @patch("httpx.Client.post")
    def test_post_method_delegation(self, mock_post: MagicMock) -> None:
        """Test that POST method is properly delegated."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.url = "https://api.example.com/users"
        mock_response.status_code = 201
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"name": "John"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"id": 1, "name": "John"}'
        mock_post.return_value = mock_response

        client = HttpClient(base_url="https://api.example.com")
        data = {"name": "John"}
        response = client.post("/users", json=data)

        mock_post.assert_called_once_with("/users", json=data)
        assert response == mock_response

    @patch("httpx.Client.request")
    def test_request_with_error_response(self, mock_request: MagicMock) -> None:
        """Test logging when request returns error status code."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/notfound"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 404
        mock_response.elapsed.total_seconds.return_value = 0.05
        mock_response.request.headers = {}
        mock_response.request.content = b""
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"error": "Not Found"}'
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            response = client.request("GET", "https://api.example.com/notfound")

            assert any("Sending HTTP" in str(call) for call in mock_info.call_args_list)
            mock_info.assert_any_call("Response status code: 404")
            assert response.status_code == 404

    def test_context_manager_support(self) -> None:
        """Test that HttpClient can be used as context manager."""
        with HttpClient(base_url="https://api.example.com") as client:
            assert isinstance(client, HttpClient)
            assert client.base_url == "https://api.example.com"

    @patch("httpx.Client.request")
    def test_custom_headers_in_request(self, mock_request: MagicMock) -> None:
        """Test that custom headers are properly handled."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/test"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.request.headers = {"Authorization": "Bearer token", "Custom": "value"}
        mock_response.request.content = b""
        mock_response.headers = {}
        mock_response.text = "OK"
        mock_request.return_value = mock_response

        client = HttpClient()
        headers = {"Authorization": "Bearer token", "Custom": "value"}

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            client.request("GET", "https://api.example.com/test", headers=headers)

            debug_calls = [str(call) for call in mock_debug.call_args_list]
            assert any("Request headers:" in call for call in debug_calls)
            headers_calls = [call for call in debug_calls if "Request headers:" in call]
            assert len(headers_calls) > 0
            headers_call = headers_calls[0]
            assert "Bear***MASKED***" in headers_call
            assert "Custom" in headers_call

    @patch("httpx.Client.request")
    def test_request_with_streaming_content(self, mock_request: MagicMock) -> None:
        """Test that streaming content (e.g., file uploads) is handled gracefully."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/upload"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 1.5
        mock_response.request.headers = {"Content-Type": "multipart/form-data"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"success": true}'

        mock_response.request.content = iter([b"chunk1", b"chunk2"])
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/upload")

            assert response == mock_response

            debug_calls = [str(call) for call in mock_debug.call_args_list]
            request_body_calls = [call for call in debug_calls if "Request body:" in call]
            assert len(request_body_calls) > 0
            request_body_call = request_body_calls[0]
            assert "streaming content" in request_body_call

    @patch("httpx.Client.request")
    def test_request_with_large_content_truncation(self, mock_request: MagicMock) -> None:
        """Test that large request/response bodies are truncated in logs."""
        large_request_body = b"x" * 2048
        large_response_body = "y" * 2048

        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/large"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 2.0
        mock_response.request.headers = {"Content-Type": "application/octet-stream"}
        mock_response.request.content = large_request_body
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = large_response_body
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/large")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]

            request_body_log = next((call for call in debug_calls if call.startswith("Request body:")), None)
            assert request_body_log is not None
            assert "binary/streaming content - not logged" in request_body_log

            response_body_log = next((call for call in debug_calls if call.startswith("Response body:")), None)
            assert response_body_log is not None
            assert "y" in response_body_log

    def test_sensitive_header_sanitization(self) -> None:
        """Test that sensitive headers are masked in logs."""
        client = HttpClient()

        headers = {
            "Authorization": "Bearer super_secret_token_12345",
            "X-API-Key": "api_key_67890",
            "Cookie": "session=abc123def456",
            "Content-Type": "application/json",
            "User-Agent": "TestAgent/1.0",
        }

        sanitized = client._sanitize_headers(headers)  # noqa: SLF001

        assert sanitized["Authorization"] == "Bear***MASKED***"
        assert sanitized["X-API-Key"] == "api_***MASKED***"
        assert sanitized["Cookie"] == "sess***MASKED***"

        assert sanitized["Content-Type"] == "application/json"
        assert sanitized["User-Agent"] == "TestAgent/1.0"

    def test_sensitive_header_sanitization_disabled(self) -> None:
        """Test that header sanitization can be disabled."""
        client = HttpClient(mask_sensitive_data=False)

        headers = {
            "Authorization": "Bearer super_secret_token_12345",
            "X-API-Key": "api_key_67890",
        }

        sanitized = client._sanitize_headers(headers)  # noqa: SLF001

        assert sanitized["Authorization"] == "Bearer super_secret_token_12345"
        assert sanitized["X-API-Key"] == "api_key_67890"

    def test_sensitive_json_content_sanitization(self) -> None:
        """Test that sensitive JSON fields are masked."""
        client = HttpClient()

        json_data = {"password": "secret123", "email": "user@example.com", "safe_field": "visible"}

        sanitized = client._mask_sensitive_json_fields(json_data)  # noqa: SLF001

        assert sanitized["password"] == "secr***MASKED***"  # noqa: S105
        assert sanitized["email"] == "user@example.com"
        assert sanitized["safe_field"] == "visible"

    def test_sensitive_text_pattern_sanitization(self) -> None:
        """Test that sensitive patterns in text are masked."""
        client = HttpClient()

        text_content = 'password=secret123 and api_key="abc123def" token: xyz789'

        sanitized = client._mask_sensitive_text_patterns(text_content)  # noqa: SLF001

        assert "***MASKED***" in sanitized
        assert "secret123" not in sanitized
        assert "abc123def" not in sanitized
        assert "xyz789" not in sanitized

    def test_custom_sensitive_headers(self) -> None:
        """Test that custom sensitive headers can be configured."""
        custom_sensitive = {"x-custom-secret", "special-header"}
        client = HttpClient(sensitive_headers=custom_sensitive)

        headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Secret": "very_secret",
            "Special-Header": "confidential",
        }

        sanitized = client._sanitize_headers(headers)  # noqa: SLF001

        # Default headers are always masked even with custom headers
        assert sanitized["Authorization"] == "Bear***MASKED***"
        assert sanitized["X-Custom-Secret"] == "very***MASKED***"
        assert sanitized["Special-Header"] == "conf***MASKED***"

    @patch("httpx.Client.request")
    def test_request_with_sensitive_data_logging(self, mock_request: MagicMock) -> None:
        """Test that sensitive data in real request/response is masked."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/login"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.request.headers = {
            "Authorization": "Bearer sensitive_token_123",
            "Content-Type": "application/json",
        }
        mock_response.request.content = b'{"password": "user_secret", "username": "testuser"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"token": "response_token_456", "user_id": 123}'
        mock_response.content = b'{"token": "response_token_456", "user_id": 123}'
        mock_response.json.return_value = {"token": "response_token_456", "user_id": 123}
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/login")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]

            request_headers_log = next((call for call in debug_calls if call.startswith("Request headers:")), None)
            assert request_headers_log is not None
            assert "Bear***MASKED***" in request_headers_log
            assert "sensitive_token_123" not in request_headers_log

            request_body_log = next((call for call in debug_calls if call.startswith("Request body (JSON):")), None)
            assert request_body_log is not None
            assert "***MASKED***" in request_body_log
            assert "user_secret" not in request_body_log

            response_body_log = next((call for call in debug_calls if call.startswith("Response body (JSON):")), None)
            assert response_body_log is not None
            assert "***MASKED***" in response_body_log
            assert "response_token_456" not in response_body_log

    @patch("httpx.Client.request")
    def test_url_parameter_sanitization(self, mock_request: MagicMock) -> None:
        """Test that sensitive URL parameters are masked in logs."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/data"
        from httpx import QueryParams

        mock_params = QueryParams([("access_token", "secret123"), ("api_key", "apikey456"), ("user_id", "789")])
        mock_url.params = mock_params
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"query": "test"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("GET", "https://api.example.com/data")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            params_log = next((call for call in debug_calls if call.startswith("Request query params:")), None)

            assert params_log is not None
            assert "***MASKED***" in params_log
            assert "user_id=789" in params_log
            assert "secret123" not in params_log
            assert "apikey456" not in params_log

    @patch("httpx.Client.request")
    def test_custom_sensitive_json_fields(self, mock_request: MagicMock) -> None:
        """Test that custom sensitive JSON fields configuration works."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/custom"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"custom_secret": "should_be_masked", "public_info": "visible"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"custom_secret": "should_be_masked", "public_info": "visible"}'
        mock_response.content = b'{"custom_secret": "should_be_masked", "public_info": "visible"}'
        mock_response.json.return_value = {"custom_secret": "should_be_masked", "public_info": "visible"}
        mock_request.return_value = mock_response

        client = HttpClient(sensitive_json_fields={"custom_secret"})

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/custom")

            assert response == mock_response

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]

            request_body_log = next((call for call in debug_calls if call.startswith("Request body (JSON):")), None)
            assert request_body_log is not None
            assert "***MASKED***" in request_body_log
            assert "should_be_masked" not in request_body_log
            assert "public_info" in request_body_log
            assert "visible" in request_body_log

            response_body_log = next((call for call in debug_calls if call.startswith("Response body (JSON):")), None)
            assert response_body_log is not None
            assert "***MASKED***" in response_body_log
            assert "should_be_masked" not in response_body_log


class TestHttpClientMethodsAndContentTypes:
    """Test various HTTP methods with different content types and scenarios.

    This test class comprehensively tests different HTTP methods (GET, POST, PUT, DELETE)
    with various request/response configurations:
    - With and without request body/parameters
    - With and without response body
    - Different Content-Type headers (JSON, text, XML, binary/streaming)
    - Different HTTP status codes including errors
    - Verification of logging functionality
    - Access to status codes, headers, and response bodies
    """

    @patch("httpx.Client.request")
    def test_get_request_without_params(self, mock_request: MagicMock) -> None:
        """Test GET request without parameters."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/users"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.15
        mock_response.request.headers = {"Accept": "application/json"}
        mock_response.request.content = b""
        mock_response.request.method = "GET"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"users": []}'
        mock_response.content = b'{"users": []}'
        mock_response.json.return_value = {"users": []}
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "info") as mock_info, patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("GET", "https://api.example.com/users")

            # Verify response data
            assert response == mock_response
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "application/json"
            assert response.json() == {"users": []}

            # Verify logging
            assert any("Sending HTTP [GET] request to:" in str(call) for call in mock_info.call_args_list)
            mock_info.assert_any_call("Response status code: 200")
            mock_info.assert_any_call("Response time: 0.150 s")

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            assert any("Request headers:" in call for call in debug_calls)
            assert any("Request body: <empty>" in call for call in debug_calls)
            assert any("Response body (JSON):" in call for call in debug_calls)

    @patch("httpx.Client.request")
    def test_get_request_with_query_params(self, mock_request: MagicMock) -> None:
        """Test GET request with query parameters."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/users"
        from httpx import QueryParams

        mock_params = QueryParams([("limit", "10"), ("page", "1")])
        mock_url.params = mock_params
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.12
        mock_response.request.headers = {"Accept": "application/json"}
        mock_response.request.content = b""
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"users": [{"id": 1}], "total": 1}'
        mock_response.content = b'{"users": [{"id": 1}], "total": 1}'
        mock_response.json.return_value = {"users": [{"id": 1}], "total": 1}
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.get("https://api.example.com/users", params={"limit": 10, "page": 1})

            assert response.status_code == 200
            assert "users" in response.json()

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            params_log = next((call for call in debug_calls if call.startswith("Request query params:")), None)
            assert params_log is not None
            assert "limit=10" in params_log
            assert "page=1" in params_log

    @patch("httpx.Client.request")
    def test_post_request_with_json_body(self, mock_request: MagicMock) -> None:
        """Test POST request with JSON body."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/users"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 201
        mock_response.elapsed.total_seconds.return_value = 0.25
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"name": "John Doe", "email": "john@example.com"}'
        mock_response.request.method = "POST"
        mock_response.headers = {"Content-Type": "application/json", "Location": "/users/123"}
        mock_response.text = '{"id": 123, "name": "John Doe", "email": "john@example.com"}'
        mock_response.content = b'{"id": 123, "name": "John Doe", "email": "john@example.com"}'
        mock_response.json.return_value = {"id": 123, "name": "John Doe", "email": "john@example.com"}
        mock_request.return_value = mock_response

        client = HttpClient()
        user_data = {"name": "John Doe", "email": "john@example.com"}

        with patch.object(client._logger, "info") as mock_info, patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/users", json=user_data)

            # Verify response data
            assert response.status_code == 201
            assert response.headers["Location"] == "/users/123"
            assert response.json()["id"] == 123

            # Verify logging
            mock_info.assert_any_call("Response status code: 201")

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            request_body_log = next((call for call in debug_calls if call.startswith("Request body (JSON):")), None)
            assert request_body_log is not None
            assert "John Doe" in request_body_log

            response_body_log = next((call for call in debug_calls if call.startswith("Response body (JSON):")), None)
            assert response_body_log is not None
            assert "John Doe" in response_body_log

    @patch("httpx.Client.request")
    def test_post_request_with_form_data(self, mock_request: MagicMock) -> None:
        """Test POST request with form data."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/form"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.18
        mock_response.request.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        mock_response.request.content = b"username=testuser&password=secret123"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Form submitted successfully"
        mock_response.content = b"Form submitted successfully"
        mock_request.return_value = mock_response

        client = HttpClient()
        form_data = {"username": "testuser", "password": "secret123"}

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("POST", "https://api.example.com/form", data=form_data)

            assert response.status_code == 200
            assert "successfully" in response.text

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            request_body_log = next(
                (call for call in debug_calls if call.startswith("Request body (raw bytes):")),
                None,
            )
            assert request_body_log is not None

    @patch("httpx.Client.request")
    def test_put_request_with_json_update(self, mock_request: MagicMock) -> None:
        """Test PUT request for updating resource with JSON."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/users/123"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.22
        mock_response.request.headers = {"Content-Type": "application/json"}
        mock_response.request.content = b'{"name": "John Smith", "email": "johnsmith@example.com"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = (
            '{"id": 123, "name": "John Smith", "email": "johnsmith@example.com", "updated_at": "2025-09-25T10:00:00Z"}'
        )
        mock_response.content = (
            b'{"id": 123, "name": "John Smith", "email": "johnsmith@example.com", "updated_at": "2025-09-25T10:00:00Z"}'
        )
        mock_response.json.return_value = {
            "id": 123,
            "name": "John Smith",
            "email": "johnsmith@example.com",
            "updated_at": "2025-09-25T10:00:00Z",
        }
        mock_request.return_value = mock_response

        client = HttpClient()
        update_data = {"name": "John Smith", "email": "johnsmith@example.com"}

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            response = client.request("PUT", "https://api.example.com/users/123", json=update_data)

            assert response.status_code == 200
            assert response.json()["name"] == "John Smith"
            assert "updated_at" in response.json()

            mock_info.assert_any_call("Response status code: 200")

    @patch("httpx.Client.request")
    def test_put_request_without_body(self, mock_request: MagicMock) -> None:
        """Test PUT request without request body."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/users/123/activate"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 204
        mock_response.elapsed.total_seconds.return_value = 0.08
        mock_response.request.headers = {"Accept": "application/json"}
        mock_response.request.content = b""
        mock_response.headers = {}
        mock_response.text = ""
        mock_response.content = b""
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("PUT", "https://api.example.com/users/123/activate")

            assert response.status_code == 204
            assert response.text == ""

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            assert any("Request body: <empty>" in call for call in debug_calls)
            assert any("Response body: <empty>" in call for call in debug_calls)

    @patch("httpx.Client.request")
    def test_delete_request_without_body(self, mock_request: MagicMock) -> None:
        """Test DELETE request without body."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/users/123"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 204
        mock_response.elapsed.total_seconds.return_value = 0.12
        mock_response.request.headers = {}
        mock_response.request.content = b""
        mock_response.headers = {}
        mock_response.text = ""
        mock_response.content = b""
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
            response = client.request("DELETE", "https://api.example.com/users/123")

            assert response.status_code == 204
            assert response.text == ""

            mock_info.assert_any_call("Response status code: 204")

    @patch("httpx.Client.request")
    def test_delete_request_with_json_response(self, mock_request: MagicMock) -> None:
        """Test DELETE request that returns JSON response."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/users/123"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.15
        mock_response.request.headers = {"Accept": "application/json"}
        mock_response.request.content = b""
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"message": "User deleted successfully", "deleted_id": 123}'
        mock_response.content = b'{"message": "User deleted successfully", "deleted_id": 123}'
        mock_response.json.return_value = {"message": "User deleted successfully", "deleted_id": 123}
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.request("DELETE", "https://api.example.com/users/123")

            assert response.status_code == 200
            assert response.json()["deleted_id"] == 123

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            response_body_log = next((call for call in debug_calls if call.startswith("Response body (JSON):")), None)
            assert response_body_log is not None
            assert "User deleted successfully" in response_body_log

    @patch("httpx.Client.request")
    def test_request_with_text_content_type(self, mock_request: MagicMock) -> None:
        """Test request with plain text content type."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/text"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_response.request.headers = {"Content-Type": "text/plain"}
        mock_response.request.content = b"This is plain text request"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Response in plain text format"
        mock_response.content = b"Response in plain text format"
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.post(
                "https://api.example.com/text",
                content="This is plain text request",
                headers={"Content-Type": "text/plain"},
            )

            assert response.status_code == 200
            assert "plain text format" in response.text

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            request_body_log = next((call for call in debug_calls if call.startswith("Request body (text):")), None)
            assert request_body_log is not None
            assert "plain text request" in request_body_log

            response_body_log = next((call for call in debug_calls if call.startswith("Response body (text):")), None)
            assert response_body_log is not None
            assert "plain text format" in response_body_log

    @patch("httpx.Client.request")
    def test_request_with_xml_content_type(self, mock_request: MagicMock) -> None:
        """Test request with XML content type."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/xml"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.13
        mock_response.request.headers = {"Content-Type": "application/xml"}
        mock_response.request.content = b"<user><name>John</name></user>"
        mock_response.headers = {"Content-Type": "application/xml"}
        mock_response.text = "<response><status>success</status></response>"
        mock_response.content = b"<response><status>success</status></response>"
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.post(
                "https://api.example.com/xml",
                content="<user><name>John</name></user>",
                headers={"Content-Type": "application/xml"},
            )

            assert response.status_code == 200
            assert "<status>success</status>" in response.text

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            request_body_log = next((call for call in debug_calls if call.startswith("Request body (text):")), None)
            assert request_body_log is not None
            assert "<user><name>John</name></user>" in request_body_log

    @patch("httpx.Client.request")
    def test_request_with_binary_streaming_content(self, mock_request: MagicMock) -> None:
        """Test request with binary/streaming content type."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/upload"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.45
        mock_response.request.headers = {"Content-Type": "application/octet-stream"}
        mock_response.request.content = b"binary data content"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"uploaded": true, "size": 19}'
        mock_response.content = b'{"uploaded": true, "size": 19}'
        mock_response.json.return_value = {"uploaded": True, "size": 19}
        mock_request.return_value = mock_response

        client = HttpClient()

        with patch.object(client._logger, "debug") as mock_debug:  # noqa: SLF001
            response = client.post(
                "https://api.example.com/upload",
                content=b"binary data content",
                headers={"Content-Type": "application/octet-stream"},
            )

            assert response.status_code == 200
            assert response.json()["uploaded"] is True

            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            request_body_log = next((call for call in debug_calls if call.startswith("Request body:")), None)
            assert request_body_log is not None
            assert "binary/streaming content - not logged" in request_body_log

    @patch("httpx.Client.request")
    def test_request_error_responses_different_status_codes(self, mock_request: MagicMock) -> None:
        """Test various HTTP error status codes."""
        error_scenarios = [
            (400, "Bad Request", "Invalid request parameters"),
            (401, "Unauthorized", "Authentication required"),
            (403, "Forbidden", "Access denied"),
            (404, "Not Found", "Resource not found"),
            (500, "Internal Server Error", "Server error occurred"),
        ]

        client = HttpClient()

        for status_code, _status_text, error_message in error_scenarios:
            mock_response = MagicMock(spec=httpx.Response)
            mock_url = MagicMock()
            mock_url.scheme = "https"
            mock_url.host = "api.example.com"
            mock_url.path = f"/error/{status_code}"
            mock_url.params = None
            mock_response.url = mock_url
            mock_response.status_code = status_code
            mock_response.elapsed.total_seconds.return_value = 0.05
            mock_response.request.headers = {"Accept": "application/json"}
            mock_response.request.content = b""
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.text = f'{{"error": "{error_message}", "status": {status_code}}}'
            mock_response.content = f'{{"error": "{error_message}", "status": {status_code}}}'.encode()
            mock_response.json.return_value = {"error": error_message, "status": status_code}
            mock_request.return_value = mock_response

            with patch.object(client._logger, "info") as mock_info:  # noqa: SLF001
                response = client.request("GET", f"https://api.example.com/error/{status_code}")

                assert response.status_code == status_code
                assert response.json()["error"] == error_message

                mock_info.assert_any_call(f"Response status code: {status_code}")

    @patch("httpx.Client.request")
    def test_request_with_custom_headers_access(self, mock_request: MagicMock) -> None:
        """Test access to request and response headers."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_url = MagicMock()
        mock_url.scheme = "https"
        mock_url.host = "api.example.com"
        mock_url.path = "/headers"
        mock_url.params = None
        mock_response.url = mock_url
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.11
        mock_response.request.headers = {
            "Authorization": "Bearer test-token",
            "User-Agent": "TestClient/1.0",
            "Content-Type": "application/json",
            "X-Custom-Header": "custom-value",
        }
        mock_response.request.content = b'{"test": "data"}'
        mock_response.headers = {
            "Content-Type": "application/json",
            "X-Rate-Limit": "1000",
            "X-Response-Time": "110ms",
            "Cache-Control": "no-cache",
        }
        mock_response.text = '{"message": "Headers received"}'
        mock_response.content = b'{"message": "Headers received"}'
        mock_response.json.return_value = {"message": "Headers received"}
        mock_request.return_value = mock_response

        client = HttpClient()
        custom_headers = {
            "Authorization": "Bearer test-token",
            "User-Agent": "TestClient/1.0",
            "X-Custom-Header": "custom-value",
        }

        response = client.request(
            "POST",
            "https://api.example.com/headers",
            json={"test": "data"},
            headers=custom_headers,
        )

        # Test access to response properties
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["X-Rate-Limit"] == "1000"
        assert response.headers["X-Response-Time"] == "110ms"
        assert response.headers["Cache-Control"] == "no-cache"
        assert response.json()["message"] == "Headers received"

        # Test that we can access request headers through mock
        assert "Authorization" in response.request.headers
        assert "User-Agent" in response.request.headers
