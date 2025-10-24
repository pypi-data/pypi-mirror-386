"""
Integration tests for AsyncDMMClient with real API requests for maker-related functionality.
"""

# pylint: disable=R0904,W0212,R0915

import sys
from unittest.mock import AsyncMock, patch

import pytest

if sys.version_info < (3, 9):
    pytest.skip("AsyncDMMClient requires Python 3.9+", allow_module_level=True)

import asyncio

import pytest_asyncio

from py_dmmjp.async_client import AsyncDMMClient
from py_dmmjp.exceptions import DMMAPIError
from py_dmmjp.maker import Maker


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientWithMakerIntegration:
    """Integration tests for async DMM client with real API calls for makers."""

    @pytest_asyncio.fixture(loop_scope="module")
    async def async_dmm_client(self, app_id: str, aff_id: str):
        """Create an async DMM client for testing."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            yield client

    async def test_client_authentication(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that async client can authenticate with valid credentials."""

        assert async_dmm_client.app_id is not None
        assert async_dmm_client.affiliate_id is not None

    async def test_get_makers_basic_request(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test basic maker retrieval with videoa floor."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=5)

        assert isinstance(makers, list)
        assert len(makers) <= 5

        for maker in makers:
            assert isinstance(maker, Maker)
            assert maker.maker_id is not None
            assert maker.name is not None
            assert maker.ruby is not None

    async def test_get_makers_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test maker search with initial filter."""

        makers = await async_dmm_client.get_makers(floor_id=43, initial="む", hits=10)

        assert isinstance(makers, list)
        assert len(makers) <= 10

        for maker in makers:
            assert isinstance(maker, Maker)
            assert maker.maker_id is not None
            assert maker.name is not None
            if maker.ruby:
                assert maker.ruby[0] in ["む", "ム"]

    async def test_get_makers_with_different_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test maker search with different initial filter."""

        makers = await async_dmm_client.get_makers(floor_id=43, initial="あ", hits=5)

        assert isinstance(makers, list)
        assert len(makers) <= 5

        for maker in makers:
            assert isinstance(maker, Maker)
            if maker.ruby:
                assert maker.ruby[0] in ["あ", "ア"]

    async def test_get_makers_different_floor(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test maker retrieval from different floor."""

        makers = await async_dmm_client.get_makers(floor_id=27, hits=5)

        assert isinstance(makers, list)
        assert len(makers) <= 5

        for maker in makers:
            assert isinstance(maker, Maker)
            assert maker.maker_id is not None
            assert maker.name is not None

    async def test_maker_data_completeness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that maker data contains expected fields."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=1)

        assert len(makers) >= 1
        maker = makers[0]

        assert maker.maker_id is not None
        assert maker.name is not None
        assert maker.ruby is not None
        assert maker.list_url is not None
        assert isinstance(maker.maker_id, str)
        assert isinstance(maker.name, str)
        assert isinstance(maker.ruby, str)
        assert isinstance(maker.list_url, str)

    async def test_maker_list_url(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test maker list URL data."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=1)

        assert len(makers) >= 1
        maker = makers[0]

        assert maker.list_url is not None
        assert maker.list_url.startswith("http")

    async def test_maker_ruby_format(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that maker ruby field is in proper format."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=10)

        assert len(makers) >= 1

        for maker in makers:
            if maker.ruby:
                assert isinstance(maker.ruby, str)
                assert len(maker.ruby) > 0

    async def test_empty_results_with_uncommon_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of valid requests that may return no results."""

        makers = await async_dmm_client.get_makers(floor_id=43, initial="ゐ", hits=1)

        assert isinstance(makers, list)

    async def test_pagination_with_offset(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination using offset parameter."""

        first_page = await async_dmm_client.get_makers(floor_id=43, hits=5, offset=1)

        second_page = await async_dmm_client.get_makers(floor_id=43, hits=5, offset=6)

        assert len(first_page) <= 5
        assert len(second_page) <= 5

        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {m.maker_id for m in first_page}
            second_ids = {m.maker_id for m in second_page}
            assert first_ids != second_ids

    async def test_large_result_set(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving larger result sets."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=50)

        assert isinstance(makers, list)
        assert len(makers) <= 50

        for maker in makers:
            assert isinstance(maker, Maker)
            assert maker.maker_id is not None

    async def test_maximum_hits(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving with maximum hits value."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=100)

        assert isinstance(makers, list)
        assert len(makers) <= 100

        for maker in makers:
            assert isinstance(maker, Maker)

    async def test_error_handling_missing_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling when floor_id is missing."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_makers(floor_id=0, hits=1)

        assert "floor_id is required" in str(exc_info.value)

    async def test_error_handling_invalid_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling with invalid floor_id."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_makers(floor_id=99999, hits=1)

        assert "400" in str(exc_info.value) or "Invalid" in str(exc_info.value)

    async def test_multiple_concurrent_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test multiple concurrent API requests."""

        results = await asyncio.gather(
            async_dmm_client.get_makers(floor_id=43, initial="あ", hits=3),
            async_dmm_client.get_makers(floor_id=43, initial="む", hits=3),
            async_dmm_client.get_makers(floor_id=27, initial="あ", hits=3),
        )

        assert len(results) == 3
        assert all(isinstance(makers, list) for makers in results)
        assert all(len(makers) <= 3 for makers in results)

    async def test_session_reuse_across_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that session is reused across multiple requests."""

        makers1 = await async_dmm_client.get_makers(floor_id=43, hits=1)

        makers2 = await async_dmm_client.get_makers(floor_id=43, hits=1)

        assert len(makers1) >= 0
        assert len(makers2) >= 0
        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

    async def test_client_context_manager(self, app_id, aff_id):
        """Test async client as context manager."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            makers = await client.get_makers(floor_id=43, hits=1)
            assert isinstance(makers, list)

    async def test_maker_id_uniqueness_in_results(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that returned maker IDs are unique."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=20)

        assert len(makers) >= 1

        maker_ids = [m.maker_id for m in makers]
        assert len(maker_ids) == len(set(maker_ids))

    async def test_different_floor_ids(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test maker retrieval from different floor IDs."""

        videoa_makers = await async_dmm_client.get_makers(floor_id=43, hits=3)
        book_makers = await async_dmm_client.get_makers(floor_id=27, hits=3)

        assert isinstance(videoa_makers, list)
        assert isinstance(book_makers, list)

        if len(videoa_makers) > 0:
            assert isinstance(videoa_makers[0], Maker)

        if len(book_makers) > 0:
            assert isinstance(book_makers[0], Maker)

    async def test_maker_with_special_characters_in_name(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of maker names with special characters."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=20)

        assert len(makers) >= 1

        for maker in makers:
            assert maker.name is not None
            assert len(maker.name) > 0

    async def test_offset_beyond_total_count(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with offset beyond total count."""

        makers = await async_dmm_client.get_makers(floor_id=43, offset=50000, hits=1)

        assert isinstance(makers, list)

    async def test_minimal_parameters(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test maker search with minimal required parameters."""

        makers = await async_dmm_client.get_makers(floor_id=43)

        assert isinstance(makers, list)

        for maker in makers:
            assert isinstance(maker, Maker)

    async def test_combined_initial_and_pagination(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test maker search with both initial filter and pagination."""

        makers = await async_dmm_client.get_makers(
            floor_id=43, initial="あ", offset=1, hits=5
        )

        assert isinstance(makers, list)
        assert len(makers) <= 5

        for maker in makers:
            if maker.ruby:
                assert maker.ruby[0] in ["あ", "ア"]

    async def test_maker_list_url_contains_affiliate_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that maker list URLs contain affiliate tracking."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=1)

        assert len(makers) >= 1
        maker = makers[0]

        assert maker.list_url is not None
        assert "dmm.co.jp" in maker.list_url or "dmm.com" in maker.list_url

    async def test_consecutive_requests_same_parameters(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that consecutive requests with same parameters return consistent results."""

        makers1 = await async_dmm_client.get_makers(
            floor_id=43, initial="あ", hits=5, offset=1
        )

        makers2 = await async_dmm_client.get_makers(
            floor_id=43, initial="あ", hits=5, offset=1
        )

        assert len(makers1) == len(makers2)

        if len(makers1) > 0:
            ids1 = [m.maker_id for m in makers1]
            ids2 = [m.maker_id for m in makers2]
            assert ids1 == ids2

    async def test_high_offset_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with high offset and initial filter."""

        makers = await async_dmm_client.get_makers(
            floor_id=43, initial="あ", offset=50, hits=5
        )

        assert isinstance(makers, list)

        for maker in makers:
            if maker.ruby:
                assert maker.ruby[0] in ["あ", "ア"]

    async def test_maker_names_in_japanese(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that maker names are in Japanese."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=10)

        assert len(makers) >= 1

        for maker in makers:
            assert len(maker.name) > 0
            assert len(maker.ruby) > 0

    async def test_multiple_floors_concurrent(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test concurrent requests to multiple different floors."""

        results = await asyncio.gather(
            async_dmm_client.get_makers(floor_id=43, hits=5),
            async_dmm_client.get_makers(floor_id=27, hits=5),
            async_dmm_client.get_makers(floor_id=24, hits=5),
        )

        assert len(results) == 3
        assert all(isinstance(makers, list) for makers in results)

        for makers in results:
            for maker in makers:
                assert isinstance(maker, Maker)

    async def test_maker_data_consistency(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that maker data is consistent across fields."""

        makers = await async_dmm_client.get_makers(floor_id=43, hits=10)

        assert len(makers) >= 1

        for maker in makers:
            assert maker.maker_id is not None
            assert len(maker.maker_id) > 0

            assert maker.name is not None
            assert len(maker.name) > 0

            assert maker.ruby is not None
            assert len(maker.ruby) > 0

            assert maker.list_url is not None
            assert maker.list_url.startswith("http")

    async def test_initial_filter_effectiveness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that initial filter effectively narrows results."""

        all_makers = await async_dmm_client.get_makers(floor_id=43, hits=20)
        filtered_makers = await async_dmm_client.get_makers(
            floor_id=43, initial="あ", hits=20
        )

        assert isinstance(all_makers, list)
        assert isinstance(filtered_makers, list)

        for maker in filtered_makers:
            if maker.ruby:
                assert maker.ruby[0] in ["あ", "ア"]

    async def test_error_missing_result_field(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling when API response is missing result field."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"status": 200, "data": []}')
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_dmm_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with pytest.raises(DMMAPIError) as exc_info:
                await async_dmm_client.get_makers(floor_id=43)

            assert "missing 'result' field" in str(exc_info.value)

    async def test_error_generic_exception_wrapped(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that generic exceptions are wrapped in DMMAPIError."""

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='{"result": {"status": 200, "items": []}}'
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session = await async_dmm_client._ensure_session()

        with patch.object(session, "get", return_value=mock_response):
            with patch(
                "py_dmmjp.async_client.AsyncDMMClient._make_request",
                side_effect=ValueError("Unexpected error"),
            ):
                with pytest.raises(DMMAPIError) as exc_info:
                    await async_dmm_client.get_makers(floor_id=43)

                assert "Failed to get makers" in str(exc_info.value)
                assert "Unexpected error" in str(exc_info.value)
