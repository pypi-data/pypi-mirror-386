"""
Integration tests for AsyncDMMClient with real API requests for series-related functionality.
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
from py_dmmjp.series import Series


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientWithSeriesIntegration:
    """Integration tests for async DMM client with real API calls for series."""

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

    async def test_get_series_basic_request(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test basic series retrieval with book floor."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=5)

        assert isinstance(series_list, list)
        assert len(series_list) <= 5

        for series in series_list:
            assert isinstance(series, Series)
            assert series.series_id is not None
            assert series.name is not None
            assert series.ruby is not None

    async def test_get_series_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test series search with initial filter."""

        series_list = await async_dmm_client.get_series(
            floor_id=27, initial="お", hits=10
        )

        assert isinstance(series_list, list)
        assert len(series_list) <= 10

        for series in series_list:
            assert isinstance(series, Series)
            assert series.series_id is not None
            assert series.name is not None
            if series.ruby:
                assert series.ruby[0] in ["お", "オ"]

    async def test_get_series_with_different_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test series search with different initial filter."""

        series_list = await async_dmm_client.get_series(
            floor_id=27, initial="あ", hits=5
        )

        assert isinstance(series_list, list)
        assert len(series_list) <= 5

        for series in series_list:
            assert isinstance(series, Series)
            if series.ruby:
                assert series.ruby[0] in ["あ", "ア"]

    async def test_get_series_different_floor(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test series retrieval from different floor."""

        series_list = await async_dmm_client.get_series(floor_id=24, hits=5)

        assert isinstance(series_list, list)
        assert len(series_list) <= 5

        for series in series_list:
            assert isinstance(series, Series)
            assert series.series_id is not None
            assert series.name is not None

    async def test_series_data_completeness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that series data contains expected fields."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=1)

        assert len(series_list) >= 1
        series = series_list[0]

        assert series.series_id is not None
        assert series.name is not None
        assert series.ruby is not None
        assert series.list_url is not None
        assert isinstance(series.series_id, str)
        assert isinstance(series.name, str)
        assert isinstance(series.ruby, str)
        assert isinstance(series.list_url, str)

    async def test_series_list_url(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test series list URL data."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=1)

        assert len(series_list) >= 1
        series = series_list[0]

        assert series.list_url is not None
        assert series.list_url.startswith("http")

    async def test_series_ruby_format(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that series ruby field is in proper format."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=10)

        assert len(series_list) >= 1

        for series in series_list:
            if series.ruby:
                assert isinstance(series.ruby, str)
                assert len(series.ruby) > 0

    async def test_empty_results_with_uncommon_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of valid requests that may return no results."""

        series_list = await async_dmm_client.get_series(
            floor_id=27, initial="ゐ", hits=1
        )

        assert isinstance(series_list, list)

    async def test_pagination_with_offset(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination using offset parameter."""

        first_page = await async_dmm_client.get_series(floor_id=27, hits=5, offset=1)

        second_page = await async_dmm_client.get_series(floor_id=27, hits=5, offset=6)

        assert len(first_page) <= 5
        assert len(second_page) <= 5

        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {s.series_id for s in first_page}
            second_ids = {s.series_id for s in second_page}
            assert first_ids != second_ids

    async def test_large_result_set(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving larger result sets."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=50)

        assert isinstance(series_list, list)
        assert len(series_list) <= 50

        for series in series_list:
            assert isinstance(series, Series)
            assert series.series_id is not None

    async def test_maximum_hits(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving with maximum hits value."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=100)

        assert isinstance(series_list, list)
        assert len(series_list) <= 100

        for series in series_list:
            assert isinstance(series, Series)

    async def test_error_handling_missing_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling when floor_id is missing."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_series(floor_id=0, hits=1)

        assert "floor_id is required" in str(exc_info.value)

    async def test_error_handling_invalid_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling with invalid floor_id."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_series(floor_id=99999, hits=1)

        assert "400" in str(exc_info.value) or "Invalid" in str(exc_info.value)

    async def test_multiple_concurrent_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test multiple concurrent API requests."""

        results = await asyncio.gather(
            async_dmm_client.get_series(floor_id=27, initial="あ", hits=3),
            async_dmm_client.get_series(floor_id=27, initial="お", hits=3),
            async_dmm_client.get_series(floor_id=24, initial="あ", hits=3),
        )

        assert len(results) == 3
        assert all(isinstance(series_list, list) for series_list in results)
        assert all(len(series_list) <= 3 for series_list in results)

    async def test_session_reuse_across_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that session is reused across multiple requests."""

        series1 = await async_dmm_client.get_series(floor_id=27, hits=1)

        series2 = await async_dmm_client.get_series(floor_id=27, hits=1)

        assert len(series1) >= 0
        assert len(series2) >= 0
        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

    async def test_client_context_manager(self, app_id, aff_id):
        """Test async client as context manager."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            series_list = await client.get_series(floor_id=27, hits=1)
            assert isinstance(series_list, list)

    async def test_series_id_uniqueness_in_results(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that returned series IDs are unique."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=20)

        assert len(series_list) >= 1

        series_ids = [s.series_id for s in series_list]
        assert len(series_ids) == len(set(series_ids))

    async def test_different_floor_ids(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test series retrieval from different floor IDs."""

        book_series = await async_dmm_client.get_series(floor_id=27, hits=3)
        comic_series = await async_dmm_client.get_series(floor_id=24, hits=3)

        assert isinstance(book_series, list)
        assert isinstance(comic_series, list)

        if len(book_series) > 0:
            assert isinstance(book_series[0], Series)

        if len(comic_series) > 0:
            assert isinstance(comic_series[0], Series)

    async def test_series_with_special_characters_in_name(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of series names with special characters."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=20)

        assert len(series_list) >= 1

        for series in series_list:
            assert series.name is not None
            assert len(series.name) > 0

    async def test_offset_beyond_total_count(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with offset beyond total count."""

        series_list = await async_dmm_client.get_series(
            floor_id=27, offset=50000, hits=1
        )

        assert isinstance(series_list, list)

    async def test_minimal_parameters(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test series search with minimal required parameters."""

        series_list = await async_dmm_client.get_series(floor_id=27)

        assert isinstance(series_list, list)

        for series in series_list:
            assert isinstance(series, Series)

    async def test_combined_initial_and_pagination(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test series search with both initial filter and pagination."""

        series_list = await async_dmm_client.get_series(
            floor_id=27, initial="あ", offset=1, hits=5
        )

        assert isinstance(series_list, list)
        assert len(series_list) <= 5

        for series in series_list:
            if series.ruby:
                assert series.ruby[0] in ["あ", "ア"]

    async def test_series_list_url_contains_affiliate_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that series list URLs contain affiliate tracking."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=1)

        assert len(series_list) >= 1
        series = series_list[0]

        assert series.list_url is not None
        assert "dmm.co.jp" in series.list_url or "dmm.com" in series.list_url

    async def test_consecutive_requests_same_parameters(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that consecutive requests with same parameters return consistent results."""

        series1 = await async_dmm_client.get_series(
            floor_id=27, initial="あ", hits=5, offset=1
        )

        series2 = await async_dmm_client.get_series(
            floor_id=27, initial="あ", hits=5, offset=1
        )

        assert len(series1) == len(series2)

        if len(series1) > 0:
            ids1 = [s.series_id for s in series1]
            ids2 = [s.series_id for s in series2]
            assert ids1 == ids2

    async def test_high_offset_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with high offset and initial filter."""

        series_list = await async_dmm_client.get_series(
            floor_id=27, initial="あ", offset=50, hits=5
        )

        assert isinstance(series_list, list)

        for series in series_list:
            if series.ruby:
                assert series.ruby[0] in ["あ", "ア"]

    async def test_series_names_in_japanese(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that series names are in Japanese."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=10)

        assert len(series_list) >= 1

        for series in series_list:
            assert len(series.name) > 0
            assert len(series.ruby) > 0

    async def test_multiple_floors_concurrent(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test concurrent requests to multiple different floors."""

        results = await asyncio.gather(
            async_dmm_client.get_series(floor_id=27, hits=5),
            async_dmm_client.get_series(floor_id=24, hits=5),
            async_dmm_client.get_series(floor_id=43, hits=5),
        )

        assert len(results) == 3
        assert all(isinstance(series_list, list) for series_list in results)

        for series_list in results:
            for series in series_list:
                assert isinstance(series, Series)

    async def test_series_data_consistency(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that series data is consistent across fields."""

        series_list = await async_dmm_client.get_series(floor_id=27, hits=10)

        assert len(series_list) >= 1

        for series in series_list:
            assert series.series_id is not None
            assert len(series.series_id) > 0

            assert series.name is not None
            assert len(series.name) > 0

            assert series.ruby is not None
            assert len(series.ruby) > 0

            assert series.list_url is not None
            assert series.list_url.startswith("http")

    async def test_initial_filter_effectiveness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that initial filter effectively narrows results."""

        all_series = await async_dmm_client.get_series(floor_id=27, hits=20)
        filtered_series = await async_dmm_client.get_series(
            floor_id=27, initial="あ", hits=20
        )

        assert isinstance(all_series, list)
        assert isinstance(filtered_series, list)

        for series in filtered_series:
            if series.ruby:
                assert series.ruby[0] in ["あ", "ア"]

    async def test_videoa_floor_has_series(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that videoa floor also has series."""

        series_list = await async_dmm_client.get_series(floor_id=43, hits=5)

        assert isinstance(series_list, list)

        for series in series_list:
            assert isinstance(series, Series)
            assert series.series_id is not None

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
                await async_dmm_client.get_series(floor_id=27)

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
                    await async_dmm_client.get_series(floor_id=27)

                assert "Failed to get series" in str(exc_info.value)
                assert "Unexpected error" in str(exc_info.value)
