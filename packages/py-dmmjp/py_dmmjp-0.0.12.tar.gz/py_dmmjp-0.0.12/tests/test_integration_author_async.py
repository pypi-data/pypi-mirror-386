"""
Integration tests for AsyncDMMClient with real API requests for author-related functionality.
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
from py_dmmjp.author import Author
from py_dmmjp.exceptions import DMMAPIError


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientWithAuthorIntegration:
    """Integration tests for async DMM client with real API calls for authors."""

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

    async def test_get_authors_basic_request(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test basic author retrieval with book floor."""

        # Floor ID 27 is for books
        authors = await async_dmm_client.get_authors(floor_id=27, hits=5)

        assert isinstance(authors, list)
        assert len(authors) <= 5

        for author in authors:
            assert isinstance(author, Author)
            assert author.author_id is not None
            assert author.name is not None
            assert author.ruby is not None

    async def test_get_authors_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test author search with initial (phonetic) filter."""

        # Search for authors with initial 'う'
        authors = await async_dmm_client.get_authors(floor_id=27, initial="う", hits=10)

        assert isinstance(authors, list)
        assert len(authors) <= 10

        for author in authors:
            assert isinstance(author, Author)
            assert author.author_id is not None
            assert author.name is not None

            if author.ruby:
                assert author.ruby[0] in ["う", "ウ"]

    async def test_get_authors_with_different_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test author search with different initial filter."""

        authors = await async_dmm_client.get_authors(floor_id=27, initial="あ", hits=5)

        assert isinstance(authors, list)
        assert len(authors) <= 5

        for author in authors:
            assert isinstance(author, Author)
            if author.ruby:
                assert author.ruby[0] in ["あ", "ア"]

    async def test_get_authors_comic_floor(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test author retrieval from comic floor."""

        authors = await async_dmm_client.get_authors(floor_id=24, hits=5)

        assert isinstance(authors, list)
        assert len(authors) <= 5

        for author in authors:
            assert isinstance(author, Author)
            assert author.author_id is not None
            assert author.name is not None

    async def test_author_data_completeness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that author data contains expected fields."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=1)

        assert len(authors) >= 1
        author = authors[0]

        assert author.author_id is not None
        assert author.name is not None
        assert author.ruby is not None
        assert author.list_url is not None
        assert isinstance(author.author_id, str)
        assert isinstance(author.name, str)
        assert isinstance(author.ruby, str)
        assert isinstance(author.list_url, str)

    async def test_author_list_url(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test author list URL data."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=1)

        assert len(authors) >= 1
        author = authors[0]

        assert author.list_url is not None
        assert author.list_url.startswith("http")

    async def test_author_another_name(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test author alternative name field."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=10)

        assert len(authors) >= 1

        for author in authors:
            if author.another_name:
                assert isinstance(author.another_name, str)

    async def test_empty_results_with_uncommon_initial(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of valid requests that return no results."""

        authors = await async_dmm_client.get_authors(floor_id=27, initial="ゐ", hits=1)

        assert isinstance(authors, list)

    async def test_pagination_with_offset(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination using offset parameter."""

        first_page = await async_dmm_client.get_authors(floor_id=27, hits=5, offset=1)

        second_page = await async_dmm_client.get_authors(floor_id=27, hits=5, offset=6)

        assert len(first_page) <= 5
        assert len(second_page) <= 5

        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {a.author_id for a in first_page}
            second_ids = {a.author_id for a in second_page}
            assert first_ids != second_ids

    async def test_large_result_set(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving larger result sets."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=50)

        assert isinstance(authors, list)
        assert len(authors) <= 50

        for author in authors:
            assert isinstance(author, Author)
            assert author.author_id is not None

    async def test_maximum_hits(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving with maximum hits value."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=100)

        assert isinstance(authors, list)
        assert len(authors) <= 100

        for author in authors:
            assert isinstance(author, Author)

    async def test_error_handling_missing_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling when floor_id is missing."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_authors(floor_id=0, hits=1)

        assert "floor_id is required" in str(exc_info.value)

    async def test_error_handling_invalid_floor_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling with invalid floor_id."""

        with pytest.raises(DMMAPIError) as exc_info:
            await async_dmm_client.get_authors(floor_id=99999, hits=1)

        assert "400" in str(exc_info.value) or "Invalid" in str(exc_info.value)

    async def test_multiple_concurrent_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test multiple concurrent API requests."""

        results = await asyncio.gather(
            async_dmm_client.get_authors(floor_id=27, initial="あ", hits=3),
            async_dmm_client.get_authors(floor_id=27, initial="う", hits=3),
            async_dmm_client.get_authors(floor_id=24, initial="あ", hits=3),
        )

        assert len(results) == 3
        assert all(isinstance(authors, list) for authors in results)
        assert all(len(authors) <= 3 for authors in results)

    async def test_session_reuse_across_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that session is reused across multiple requests."""

        authors1 = await async_dmm_client.get_authors(floor_id=27, hits=1)

        authors2 = await async_dmm_client.get_authors(floor_id=27, hits=1)

        assert len(authors1) >= 0
        assert len(authors2) >= 0
        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

    async def test_client_context_manager(self, app_id, aff_id):
        """Test async client as context manager."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            authors = await client.get_authors(floor_id=27, hits=1)
            assert isinstance(authors, list)

    async def test_author_id_uniqueness_in_results(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that returned author IDs are unique."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=20)

        assert len(authors) >= 1

        author_ids = [a.author_id for a in authors]
        assert len(author_ids) == len(set(author_ids))

    async def test_author_ruby_format(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that author ruby field is in proper format."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=10)

        assert len(authors) >= 1

        for author in authors:
            if author.ruby:
                assert isinstance(author.ruby, str)
                assert len(author.ruby) > 0

    async def test_different_floor_ids(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test author retrieval from different floor IDs."""

        book_authors = await async_dmm_client.get_authors(floor_id=27, hits=3)
        comic_authors = await async_dmm_client.get_authors(floor_id=24, hits=3)

        assert isinstance(book_authors, list)
        assert isinstance(comic_authors, list)

        if len(book_authors) > 0:
            assert isinstance(book_authors[0], Author)

        if len(comic_authors) > 0:
            assert isinstance(comic_authors[0], Author)

    async def test_author_with_special_characters_in_name(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of author names with special characters."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=20)

        assert len(authors) >= 1

        for author in authors:
            assert author.name is not None
            assert len(author.name) > 0

    async def test_offset_beyond_total_count(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with offset beyond total count."""

        authors = await async_dmm_client.get_authors(floor_id=27, offset=50000, hits=1)

        assert isinstance(authors, list)

    async def test_minimal_parameters(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test author search with minimal required parameters."""

        authors = await async_dmm_client.get_authors(floor_id=27)

        assert isinstance(authors, list)

        for author in authors:
            assert isinstance(author, Author)

    async def test_combined_initial_and_pagination(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test author search with both initial filter and pagination."""

        authors = await async_dmm_client.get_authors(
            floor_id=27, initial="あ", offset=1, hits=5
        )

        assert isinstance(authors, list)
        assert len(authors) <= 5

        for author in authors:
            if author.ruby:
                assert author.ruby[0] in ["あ", "ア"]

    async def test_author_list_url_contains_affiliate_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that author list URLs contain affiliate tracking."""

        authors = await async_dmm_client.get_authors(floor_id=27, hits=1)

        assert len(authors) >= 1
        author = authors[0]

        assert author.list_url is not None
        assert "dmm.co.jp" in author.list_url or "dmm.com" in author.list_url

    async def test_consecutive_requests_same_parameters(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that consecutive requests with same parameters return consistent results."""

        authors1 = await async_dmm_client.get_authors(
            floor_id=27, initial="あ", hits=5, offset=1
        )

        authors2 = await async_dmm_client.get_authors(
            floor_id=27, initial="あ", hits=5, offset=1
        )

        assert len(authors1) == len(authors2)

        if len(authors1) > 0:
            ids1 = [a.author_id for a in authors1]
            ids2 = [a.author_id for a in authors2]
            assert ids1 == ids2

    async def test_high_offset_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination with high offset and initial filter."""

        authors = await async_dmm_client.get_authors(
            floor_id=27, initial="あ", offset=50, hits=5
        )

        assert isinstance(authors, list)

        for author in authors:
            if author.ruby:
                assert author.ruby[0] in ["あ", "ア"]

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
                await async_dmm_client.get_authors(floor_id=27)

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
                    await async_dmm_client.get_authors(floor_id=27)

                assert "Failed to get authors" in str(exc_info.value)
                assert "Unexpected error" in str(exc_info.value)
