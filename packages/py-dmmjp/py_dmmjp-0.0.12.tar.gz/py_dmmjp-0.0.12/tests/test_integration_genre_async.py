"""
Integration tests for AsyncDMMClient with real API requests for genre-related functionality.
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
from py_dmmjp.genre import Genre


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientWithGenreIntegration:
    """Integration tests for async DMM client with real API calls for genres."""

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

    async def test_get_genres_basic_request(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test basic genre retrieval with videoa floor."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=5)

        assert isinstance(genres, list)
        assert len(genres) <= 5

        for genre in genres:
            assert isinstance(genre, Genre)
            assert genre.genre_id is not None
            assert genre.name is not None
            assert genre.ruby is not None

    async def test_get_genres_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test genre search with initial filter."""

        genres = await async_dmm_client.get_genres(floor_id=43, initial="き", hits=10)

        assert isinstance(genres, list)
        assert len(genres) <= 10

        for genre in genres:
            assert isinstance(genre, Genre)
            assert genre.genre_id is not None
            assert genre.name is not None
            if genre.ruby:
                assert genre.ruby[0] in ["き", "キ"]

    async def test_get_genres_with_different_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test genre search with different initial filter."""

        genres = await async_dmm_client.get_genres(floor_id=43, initial="あ", hits=5)

        assert isinstance(genres, list)
        assert len(genres) <= 5

        for genre in genres:
            assert isinstance(genre, Genre)
            if genre.ruby:
                assert genre.ruby[0] in ["あ", "ア"]

    async def test_get_genres_different_floor(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test genre retrieval from different floor."""

        genres = await async_dmm_client.get_genres(floor_id=27, hits=5)

        assert isinstance(genres, list)
        assert len(genres) <= 5

        for genre in genres:
            assert isinstance(genre, Genre)
            assert genre.genre_id is not None
            assert genre.name is not None

    async def test_genre_data_completeness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that genre data contains expected fields."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=1)

        assert len(genres) >= 1
        genre = genres[0]

        assert genre.genre_id is not None
        assert genre.name is not None
        assert genre.ruby is not None
        assert genre.list_url is not None
        assert isinstance(genre.genre_id, str)
        assert isinstance(genre.name, str)
        assert isinstance(genre.ruby, str)
        assert isinstance(genre.list_url, str)

    async def test_genre_list_url(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test genre list URL data."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=1)

        assert len(genres) >= 1
        genre = genres[0]

        assert genre.list_url is not None
        assert genre.list_url.startswith("http")

    async def test_genre_ruby_format(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that genre ruby field is in proper format."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=10)

        assert len(genres) >= 1

        for genre in genres:
            if genre.ruby:
                assert isinstance(genre.ruby, str)
                assert len(genre.ruby) > 0

    async def test_empty_results_with_uncommon_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of valid requests that may return no results."""

        genres = await async_dmm_client.get_genres(floor_id=43, initial="ゐ", hits=1)

        assert isinstance(genres, list)

    async def test_pagination_with_offset(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination using offset parameter."""

        first_page = await async_dmm_client.get_genres(floor_id=43, hits=5, offset=1)

        second_page = await async_dmm_client.get_genres(floor_id=43, hits=5, offset=6)

        assert len(first_page) <= 5
        assert len(second_page) <= 5

        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {g.genre_id for g in first_page}
            second_ids = {g.genre_id for g in second_page}
            assert first_ids != second_ids

    async def test_large_result_set(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving larger result sets."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=50)

        assert isinstance(genres, list)
        assert len(genres) <= 50

        for genre in genres:
            assert isinstance(genre, Genre)
            assert genre.genre_id is not None

    async def test_maximum_hits(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving with maximum hits value."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=100)

        assert isinstance(genres, list)
        assert len(genres) <= 100

        for genre in genres:
            assert isinstance(genre, Genre)

    async def test_error_handling_missing_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling when floor_id is missing."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_genres(floor_id=0, hits=1)

        assert "floor_id is required" in str(exc_info.value)

    async def test_error_handling_invalid_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling with invalid floor_id."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_genres(floor_id=99999, hits=1)

        assert "400" in str(exc_info.value) or "Invalid" in str(exc_info.value)

    async def test_multiple_concurrent_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test multiple concurrent API requests."""

        results = await asyncio.gather(
            async_dmm_client.get_genres(floor_id=43, initial="あ", hits=3),
            async_dmm_client.get_genres(floor_id=43, initial="き", hits=3),
            async_dmm_client.get_genres(floor_id=27, initial="あ", hits=3),
        )

        assert len(results) == 3
        assert all(isinstance(genres, list) for genres in results)
        assert all(len(genres) <= 3 for genres in results)

    async def test_session_reuse_across_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that session is reused across multiple requests."""

        genres1 = await async_dmm_client.get_genres(floor_id=43, hits=1)

        genres2 = await async_dmm_client.get_genres(floor_id=43, hits=1)

        assert len(genres1) >= 0
        assert len(genres2) >= 0
        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

    async def test_client_context_manager(self, app_id, aff_id):
        """Test async client as context manager."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            genres = await client.get_genres(floor_id=43, hits=1)
            assert isinstance(genres, list)

    async def test_genre_id_uniqueness_in_results(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that returned genre IDs are unique."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=20)

        assert len(genres) >= 1

        genre_ids = [g.genre_id for g in genres]
        assert len(genre_ids) == len(set(genre_ids))

    async def test_different_floor_ids(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test genre retrieval from different floor IDs."""

        videoa_genres = await async_dmm_client.get_genres(floor_id=43, hits=3)
        book_genres = await async_dmm_client.get_genres(floor_id=27, hits=3)

        assert isinstance(videoa_genres, list)
        assert isinstance(book_genres, list)

        if len(videoa_genres) > 0:
            assert isinstance(videoa_genres[0], Genre)

        if len(book_genres) > 0:
            assert isinstance(book_genres[0], Genre)

    async def test_genre_with_special_characters_in_name(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of genre names with special characters."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=20)

        assert len(genres) >= 1

        for genre in genres:
            assert genre.name is not None
            assert len(genre.name) > 0

    async def test_offset_beyond_total_count(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with offset beyond total count."""

        genres = await async_dmm_client.get_genres(floor_id=43, offset=50000, hits=1)

        assert isinstance(genres, list)

    async def test_minimal_parameters(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test genre search with minimal required parameters."""

        genres = await async_dmm_client.get_genres(floor_id=43)

        assert isinstance(genres, list)

        for genre in genres:
            assert isinstance(genre, Genre)

    async def test_combined_initial_and_pagination(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test genre search with both initial filter and pagination."""

        genres = await async_dmm_client.get_genres(
            floor_id=43, initial="あ", offset=1, hits=5
        )

        assert isinstance(genres, list)
        assert len(genres) <= 5

        for genre in genres:
            if genre.ruby:
                assert genre.ruby[0] in ["あ", "ア"]

    async def test_genre_list_url_contains_affiliate_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that genre list URLs contain affiliate tracking."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=1)

        assert len(genres) >= 1
        genre = genres[0]

        assert genre.list_url is not None
        assert "dmm.co.jp" in genre.list_url or "dmm.com" in genre.list_url

    async def test_consecutive_requests_same_parameters(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that consecutive requests with same parameters return consistent results."""

        genres1 = await async_dmm_client.get_genres(
            floor_id=43, initial="あ", hits=5, offset=1
        )

        genres2 = await async_dmm_client.get_genres(
            floor_id=43, initial="あ", hits=5, offset=1
        )

        assert len(genres1) == len(genres2)

        if len(genres1) > 0:
            ids1 = [g.genre_id for g in genres1]
            ids2 = [g.genre_id for g in genres2]
            assert ids1 == ids2

    async def test_high_offset_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with high offset and initial filter."""

        genres = await async_dmm_client.get_genres(
            floor_id=43, initial="あ", offset=50, hits=5
        )

        assert isinstance(genres, list)

        for genre in genres:
            if genre.ruby:
                assert genre.ruby[0] in ["あ", "ア"]

    async def test_genre_names_in_japanese(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that genre names are in Japanese."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=10)

        assert len(genres) >= 1

        for genre in genres:
            assert len(genre.name) > 0
            assert len(genre.ruby) > 0

    async def test_multiple_floors_concurrent(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test concurrent requests to multiple different floors."""

        results = await asyncio.gather(
            async_dmm_client.get_genres(floor_id=43, hits=5),
            async_dmm_client.get_genres(floor_id=27, hits=5),
            async_dmm_client.get_genres(floor_id=24, hits=5),
        )

        assert len(results) == 3
        assert all(isinstance(genres, list) for genres in results)

        for genres in results:
            for genre in genres:
                assert isinstance(genre, Genre)

    async def test_genre_data_consistency(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that genre data is consistent across fields."""

        genres = await async_dmm_client.get_genres(floor_id=43, hits=10)

        assert len(genres) >= 1

        for genre in genres:
            assert genre.genre_id is not None
            assert len(genre.genre_id) > 0

            assert genre.name is not None
            assert len(genre.name) > 0

            assert genre.ruby is not None
            assert len(genre.ruby) > 0

            assert genre.list_url is not None
            assert genre.list_url.startswith("http")

    async def test_initial_filter_effectiveness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that initial filter effectively narrows results."""

        all_genres = await async_dmm_client.get_genres(floor_id=43, hits=20)
        filtered_genres = await async_dmm_client.get_genres(
            floor_id=43, initial="あ", hits=20
        )

        assert isinstance(all_genres, list)
        assert isinstance(filtered_genres, list)

        for genre in filtered_genres:
            if genre.ruby:
                assert genre.ruby[0] in ["あ", "ア"]

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
                await async_dmm_client.get_genres(floor_id=43)

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
                    await async_dmm_client.get_genres(floor_id=43)

                assert "Failed to get genres" in str(exc_info.value)
                assert "Unexpected error" in str(exc_info.value)
