"""
Test cases for JSON parsing errors in DMMClient.
"""

# pylint: disable=protected-access, unused-argument, redefined-outer-name

import sys

import pytest

if sys.version_info < (3, 9):
    pytest.skip("AsyncDMMClient requires Python 3.9+", allow_module_level=True)

from unittest.mock import AsyncMock, patch

import pytest_asyncio

from py_dmmjp.async_client import AsyncDMMClient
from py_dmmjp.exceptions import DMMAPIError


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestDMMClientJSONErrors:
    """Test JSON parsing errors in DMMClient API methods."""

    @pytest_asyncio.fixture(loop_scope="module")
    async def async_client(self):
        """Create an async DMM client for testing."""

        async with AsyncDMMClient(
            api_key="test_key", affiliate_id="test_affiliate"
        ) as client:
            yield client

    async def test_invalid_json_on_get_products(self, async_client: AsyncDMMClient):
        """Test invalid JSON response on get_products raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="Not valid JSON {{{{")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_products(site="FANZA")

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_invalid_json_on_get_actresses(self, async_client: AsyncDMMClient):
        """Test invalid JSON response on get_actresses raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="Invalid JSON syntax")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_actresses(keyword="test")

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_invalid_json_on_get_floors(self, async_client: AsyncDMMClient):
        """Test invalid JSON response on get_floors raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value="{'invalid': 'json with single quotes'}"
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_floors()

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_invalid_json_on_get_genres(self, async_client: AsyncDMMClient):
        """Test invalid JSON response on get_genres raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="[incomplete array")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_genres(floor_id=43)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_invalid_json_on_get_makers(self, async_client: AsyncDMMClient):
        """Test invalid JSON response on get_makers raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"unclosed": "object"')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_makers(floor_id=43)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_invalid_json_on_get_series(self, async_client: AsyncDMMClient):
        """Test invalid JSON response on get_series raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="null,null,null")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_series(floor_id=27)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_invalid_json_on_get_authors(self, async_client: AsyncDMMClient):
        """Test invalid JSON response on get_authors raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="undefined")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_authors(floor_id=27)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_empty_response_text(self, async_client: AsyncDMMClient):
        """Test empty response text raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_products(site="FANZA")

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_malformed_unicode_in_json(self, async_client: AsyncDMMClient):
        """Test malformed Unicode in JSON raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"name": "\\uXXXX"}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_actresses()

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_json_with_trailing_comma(self, async_client: AsyncDMMClient):
        """Test JSON with trailing comma raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"result": {"status": 200,}}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_floors()

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_json_with_comments(self, async_client: AsyncDMMClient):
        """Test JSON with comments (invalid JSON) raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='{"result": /* comment */ {"status": 200}}'
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_genres(floor_id=43)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_exception_chaining_preserved(self, async_client: AsyncDMMClient):
        """Test that original ValueError is preserved in exception chain."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="Invalid JSON")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_products(site="FANZA")

            assert isinstance(exc_info.value.__cause__, ValueError)

    async def test_json_with_null_bytes(self, async_client: AsyncDMMClient):
        """Test JSON with null bytes raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"result": "value\x00with null"}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_makers(floor_id=43)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_multiple_json_objects(self, async_client: AsyncDMMClient):
        """Test multiple JSON objects in response raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='{"result": "first"}{"result": "second"}'
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_series(floor_id=27)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_json_with_unescaped_control_characters(
        self, async_client: AsyncDMMClient
    ):
        """Test JSON with unescaped control characters raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"result": "line1\nline2"}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_authors(floor_id=27)

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_json_error_on_get_product_by_cid(self, async_client: AsyncDMMClient):
        """Test invalid JSON on get_product_by_cid raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="Not JSON")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_product_by_cid(cid="test123", site="FANZA")

            assert "Error while formatting DMM Response" in str(exc_info.value)

    async def test_json_error_on_get_product_by_product_id(
        self, async_client: AsyncDMMClient
    ):
        """Test invalid JSON on get_product_by_product_id raises DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="{invalid}")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_client.get_product_by_product_id(
                    product_id="ABP-477", site="FANZA"
                )

            assert "Error while formatting DMM Response" in str(exc_info.value)
