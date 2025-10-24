"""
Test cases for HTTP error handling in AsyncDMMClient.
"""

# pylint: disable=protected-access, unused-argument

import sys

import pytest

if sys.version_info < (3, 9):
    pytest.skip("AsyncDMMClient requires Python 3.9+", allow_module_level=True)

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest_asyncio

from py_dmmjp.async_client import AsyncDMMClient
from py_dmmjp.exceptions import DMMAPIError, DMMAuthError


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientHTTPErrors:
    """Test HTTP error handling in AsyncDMMClient API methods."""

    @pytest_asyncio.fixture(loop_scope="module")
    async def async_client(self, app_id: str, aff_id: str):
        """Create an async DMM client for testing."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            yield client

    async def test_401_unauthorized_error(self, async_client: AsyncDMMClient):
        """Test 401 Unauthorized error raises DMMAuthError."""

        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAuthError) as exc_info:
                await async_client.get_products(site="FANZA")

            assert "Invalid API key or authentication failed" in str(exc_info.value)

    async def test_403_forbidden_error(self, async_client: AsyncDMMClient):
        """Test 403 Forbidden error raises DMMAuthError."""

        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.text = AsyncMock(return_value="Forbidden")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAuthError) as exc_info:
                await async_client.get_actresses()

            assert "Access forbidden - check your API key permissions" in str(
                exc_info.value
            )

    async def test_404_not_found_error(self, async_client: AsyncDMMClient):
        """Test 404 Not Found error raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Not Found")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_floors()

            assert "HTTP 404" in str(exc_info.value)

    async def test_500_internal_server_error(self, async_client: AsyncDMMClient):
        """Test 500 Internal Server Error raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_genres(floor_id=43)

            assert "HTTP 500" in str(exc_info.value)

    async def test_502_bad_gateway_error(self, async_client: AsyncDMMClient):
        """Test 502 Bad Gateway error raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 502
        mock_response.text = AsyncMock(return_value="Bad Gateway")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_makers(floor_id=43)

            assert "HTTP 502" in str(exc_info.value)

    async def test_503_service_unavailable_error(self, async_client: AsyncDMMClient):
        """Test 503 Service Unavailable error raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 503
        mock_response.text = AsyncMock(return_value="Service Unavailable")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_series(floor_id=27)

            assert "HTTP 503" in str(exc_info.value)

    async def test_400_bad_request_error(self, async_client: AsyncDMMClient):
        """Test 400 Bad Request error raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_authors(floor_id=27)

            assert "HTTP 400" in str(exc_info.value)

    async def test_429_too_many_requests_error(self, async_client: AsyncDMMClient):
        """Test 429 Too Many Requests error raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value="Too Many Requests")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_products(site="FANZA")

            assert "HTTP 429" in str(exc_info.value)

    async def test_timeout_error(self, async_client: AsyncDMMClient):
        """Test timeout error raises DMMAPIError."""

        session = await async_client._ensure_session()

        mock_cm = AsyncMock()
        mock_cm.__aenter__.side_effect = aiohttp.ServerTimeoutError()

        with patch.object(session, "get", return_value=mock_cm):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_products(site="FANZA")

            assert "Request timed out" in str(exc_info.value)

    async def test_connection_error(self, async_client: AsyncDMMClient):
        """Test connection error raises DMMAPIError."""

        session = await async_client._ensure_session()

        mock_cm = AsyncMock()
        mock_cm.__aenter__.side_effect = aiohttp.ClientConnectionError()

        with patch.object(session, "get", return_value=mock_cm):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_actresses()

            assert "Connection error occurred" in str(exc_info.value)

    async def test_client_error(self, async_client: AsyncDMMClient):
        """Test generic client error raises DMMAPIError."""

        session = await async_client._ensure_session()

        mock_cm = AsyncMock()
        mock_cm.__aenter__.side_effect = aiohttp.ClientError("Generic client error")

        with patch.object(session, "get", return_value=mock_cm):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_floors()

            assert "Request failed" in str(exc_info.value)

    async def test_401_on_get_product_by_cid(self, async_client: AsyncDMMClient):
        """Test 401 error on get_product_by_cid raises DMMAuthError."""

        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAuthError) as exc_info:
                await async_client.get_product_by_cid(cid="test123", site="FANZA")

            assert "Invalid API key or authentication failed" in str(exc_info.value)

    async def test_403_on_get_product_by_product_id(self, async_client: AsyncDMMClient):
        """Test 403 error on get_product_by_product_id raises DMMAuthError."""

        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.text = AsyncMock(return_value="Forbidden")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAuthError) as exc_info:
                await async_client.get_product_by_product_id(
                    product_id="ABP-477", site="FANZA"
                )

            assert "Access forbidden" in str(exc_info.value)

    async def test_status_code_in_error_message(self, async_client: AsyncDMMClient):
        """Test that status code is included in error message."""

        mock_response = AsyncMock()
        mock_response.status = 418
        mock_response.text = AsyncMock(return_value="I'm a teapot")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_genres(floor_id=43)

            assert "HTTP 418" in str(exc_info.value)
            assert exc_info.value.status_code == 418

    async def test_response_data_in_error(self, async_client: AsyncDMMClient):
        """Test that response data is included in error."""

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='{"error": "Invalid parameter"}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_makers(floor_id=43)

            assert exc_info.value.response_data == '{"error": "Invalid parameter"}'

    async def test_multiple_401_errors(self, async_client: AsyncDMMClient):
        """Test multiple consecutive 401 errors."""

        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAuthError):
                await async_client.get_products(site="FANZA")

            with pytest.raises(DMMAuthError):
                await async_client.get_actresses()

            with pytest.raises(DMMAuthError):
                await async_client.get_floors()

    async def test_timeout_on_different_methods(self, async_client: AsyncDMMClient):
        """Test timeout errors across different API methods."""

        session = await async_client._ensure_session()

        mock_cm = AsyncMock()
        mock_cm.__aenter__.side_effect = aiohttp.ServerTimeoutError()

        with patch.object(session, "get", return_value=mock_cm):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_genres(floor_id=43)
            assert "Request timed out" in str(exc_info.value)

            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_makers(floor_id=43)
            assert "Request timed out" in str(exc_info.value)

            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_series(floor_id=27)
            assert "Request timed out" in str(exc_info.value)
