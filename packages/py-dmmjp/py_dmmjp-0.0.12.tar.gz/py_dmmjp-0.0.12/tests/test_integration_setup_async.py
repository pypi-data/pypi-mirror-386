"""
Integration tests for AsyncDMMClient with real API requests.
"""

# pylint: disable=R0904,W0212,R0915

import os
import sys

import pytest
from dotenv import load_dotenv

if sys.version_info < (3, 9):

    pytest.skip("AsyncDMMClient requires Python 3.9+", allow_module_level=True)

import asyncio
from unittest.mock import MagicMock, patch

import pytest_asyncio

from py_dmmjp.async_client import AsyncDMMClient
from py_dmmjp.exceptions import DMMAuthError


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientAuthenticationErrors:
    """Test authentication error scenarios for async client."""

    async def test_invalid_api_key(self):
        """Test async client with invalid API key."""

        with pytest.raises(DMMAuthError):
            AsyncDMMClient(api_key="", affiliate_id="valid_id")

    async def test_invalid_affiliate_id(self):
        """Test async client with invalid affiliate ID."""

        with pytest.raises(DMMAuthError):
            AsyncDMMClient(api_key="valid_key", affiliate_id="")

    async def test_both_invalid_credentials(self):
        """Test async client with both invalid credentials."""

        with pytest.raises(DMMAuthError):
            AsyncDMMClient(api_key="", affiliate_id="")


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientEnvironmentVariables:
    """Test environment variable handling for async client."""

    async def test_env_file_support(self):
        """Test loading credentials from .env file."""

        original_dir = os.getcwd()
        try:
            load_dotenv()

            app_id = os.getenv("APP_ID")
            aff_id = os.getenv("AFF_ID")

            assert app_id is not None
            assert aff_id is not None

        finally:
            os.chdir(original_dir)

    async def test_environment_variable_precedence(self):
        """Test that environment variables are properly loaded."""

        app_id = os.getenv("APP_ID")
        aff_id = os.getenv("AFF_ID")

        if app_id and aff_id:
            async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
                assert client.app_id == app_id
                assert client.affiliate_id == aff_id
        else:
            pytest.skip("Environment variables APP_ID and AFF_ID not set")


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientContextManager:
    """Test async context manager functionality."""

    async def test_context_manager_entry_and_exit(self):
        """Test that async context manager properly initializes and cleans up."""

        app_id = os.getenv("APP_ID")
        aff_id = os.getenv("AFF_ID")

        if not app_id or not aff_id:
            pytest.skip("Environment variables APP_ID and AFF_ID not set")

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            assert client._session is not None
            assert not client._session.closed

        assert client._session is None or client._session.closed

    async def test_multiple_context_manager_usage(self):
        """Test that client can be used multiple times with context manager."""

        app_id = os.getenv("APP_ID")
        aff_id = os.getenv("AFF_ID")

        if not app_id or not aff_id:
            pytest.skip("Environment variables APP_ID and AFF_ID not set")

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client1:
            assert client1._session is not None

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client2:
            assert client2._session is not None


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientSessionManagement:
    """Test session management for async client."""

    @pytest_asyncio.fixture(loop_scope="module")
    async def async_dmm_client(self, app_id: str, aff_id: str):
        """Create an async DMM client for testing."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            yield client

    async def test_session_creation(self, async_dmm_client: AsyncDMMClient):
        """Test that session is created lazily."""

        assert async_dmm_client._session is not None

        await async_dmm_client._ensure_session()
        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

        await async_dmm_client.close()

    async def test_uninitialized_session_close(self, async_dmm_client: AsyncDMMClient):
        """Test closing session before initialization raises error."""

        assert async_dmm_client._session is not None

        await async_dmm_client.close()
        assert async_dmm_client._session is None

    async def test_uninitialized_session_delete(self, async_dmm_client: AsyncDMMClient):
        """Test deleting session before initialization raises error."""

        assert async_dmm_client._session is not None
        session = async_dmm_client._session

        await async_dmm_client.close()
        del async_dmm_client

        assert session.closed

    async def test_session_reuse(self, async_dmm_client: AsyncDMMClient):
        """Test that session is reused across multiple requests."""

        async with async_dmm_client as client:
            session1 = await client._ensure_session()
            session2 = await client._ensure_session()

            assert session1 is session2

    async def test_explicit_close(self, async_dmm_client: AsyncDMMClient):
        """Test explicit session closing."""

        await async_dmm_client._ensure_session()

        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

        await async_dmm_client.close()
        assert async_dmm_client._session is None or async_dmm_client._session.closed


@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientDestructor:
    """Test destructor behavior for async client."""

    async def test_destructor_closes_session_when_loop_running(self):
        """Test that destructor properly closes session when event loop is running."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")
        await client._ensure_session()

        assert client._session is not None
        assert not client._session.closed

        session = client._session

        del client
        await asyncio.sleep(0.1)

        assert session.closed

    async def test_destructor_with_uninitialized_session(self):
        """Test that destructor handles uninitialized session gracefully."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")

        assert client._session is None

        del client

    async def test_destructor_with_already_closed_session(self):
        """Test that destructor handles already closed session gracefully."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")
        await client._ensure_session()

        assert client._session is not None

        await client.close()
        assert client._session is None or client._session.closed

        del client

    async def test_destructor_with_missing_session_attribute(self):
        """Test that destructor handles missing _session attribute due to hasattr check."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")

        delattr(client, "_session")

        del client

    async def test_destructor_with_session_attribute_but_none(self):
        """Test that destructor handles _session being None."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")

        assert client._session is None

        del client

    async def test_destructor_hasattr_prevents_attribute_error(self):
        """Test that hasattr check in destructor prevents AttributeError."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")

        if hasattr(client, "_session"):
            delattr(client, "_session")

        try:
            del client
            assert True
        except AttributeError:
            pytest.fail("Destructor raised AttributeError despite hasattr check")

    async def test_destructor_uses_run_until_complete_when_loop_not_running(self):
        """Test that destructor uses loop.run_until_complete when loop.is_running() is False."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")
        await client._ensure_session()

        session = client._session
        assert session is not None

        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False

        run_until_complete_called = []

        def mock_run_until_complete(coro):
            run_until_complete_called.append(True)
            coro.close()

        mock_loop.run_until_complete = mock_run_until_complete

        with patch("asyncio.get_event_loop", return_value=mock_loop):
            del client

        assert (
            len(run_until_complete_called) == 1
        ), "loop.run_until_complete should be called when loop is not running"

        if not session.closed:
            await session.close()

    @pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
    async def test_destructor_exception_with_get_event_loop_failure(self):
        """Test that destructor catches exceptions when asyncio.get_event_loop() fails."""

        client = AsyncDMMClient(api_key="test_key", affiliate_id="test_affiliate")
        await client._ensure_session()

        session = client._session
        assert session is not None

        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            del client
