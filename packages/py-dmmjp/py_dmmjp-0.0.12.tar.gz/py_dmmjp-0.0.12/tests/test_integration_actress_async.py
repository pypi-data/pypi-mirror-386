"""
Integration tests for AsyncDMMClient with real API requests for actress-related functionality.
"""

# pylint: disable=R0904,W0212,R0915

import sys
from unittest.mock import AsyncMock, patch

import pytest

if sys.version_info < (3, 9):
    pytest.skip("AsyncDMMClient requires Python 3.9+", allow_module_level=True)

import asyncio

import pytest_asyncio

from py_dmmjp import Actress, AsyncDMMClient, DMMAPIError


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientWithActressIntegration:
    """Integration tests for async DMM client with real API calls for actresses."""

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

    async def test_get_actresses_basic_request(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test basic actress retrieval."""

        actresses = await async_dmm_client.get_actresses(hits=5)

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)
            assert actress.id is not None
            assert actress.name is not None

    async def test_get_actresses_with_keyword_search(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress search with keyword."""

        actresses = await async_dmm_client.get_actresses(keyword="あさみ", hits=5)

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)
            assert actress.id is not None
            assert actress.name is not None

    async def test_get_actresses_with_initial_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress search with initial (50-sound) filter."""

        actresses = await async_dmm_client.get_actresses(initial="あ", hits=10)

        assert isinstance(actresses, list)
        assert len(actresses) <= 10

        for actress in actresses:
            assert isinstance(actress, Actress)
            assert actress.id is not None
            assert actress.name is not None
            if actress.ruby:
                assert actress.ruby[0] in ["あ", "ア"]

    async def test_get_actresses_with_bust_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress search with bust measurement filters."""

        actresses = await async_dmm_client.get_actresses(
            gte_bust=90, lte_bust=100, hits=5
        )

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)
            if actress.bust is not None:
                assert 90 <= actress.bust <= 100

    async def test_get_actresses_with_height_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress search with height filters."""

        actresses = await async_dmm_client.get_actresses(
            gte_height=160, lte_height=170, hits=5
        )

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)
            if actress.height is not None:
                assert 160 <= actress.height <= 170

    async def test_get_actresses_with_waist_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress search with waist measurement filters."""

        actresses = await async_dmm_client.get_actresses(
            gte_waist=55, lte_waist=65, hits=5
        )

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)
            if actress.waist is not None:
                assert 55 <= actress.waist <= 65

    async def test_get_actresses_with_hip_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress search with hip measurement filters."""

        actresses = await async_dmm_client.get_actresses(gte_hip=85, lte_hip=95, hits=5)

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)
            if actress.hip is not None:
                assert 85 <= actress.hip <= 95

    async def test_get_actresses_with_birthday_filter(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress search with birthday filters."""

        actresses = await async_dmm_client.get_actresses(
            gte_birthday="1990-01-01", lte_birthday="1995-12-31", hits=5
        )

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)
            if actress.birthday:
                assert "1990" <= actress.birthday[:4] <= "1995"

    async def test_get_actresses_with_sorting_by_name(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress retrieval with name sorting."""

        actresses = await async_dmm_client.get_actresses(sort="name", hits=5)

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        for actress in actresses:
            assert isinstance(actress, Actress)

    async def test_get_actresses_with_sorting_by_bust(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress retrieval with bust sorting (descending)."""

        actresses = await async_dmm_client.get_actresses(sort="-bust", hits=5)

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        busts = [a.bust for a in actresses if a.bust is not None]
        if len(busts) >= 2:
            assert busts == sorted(busts, reverse=True)

    async def test_get_actresses_with_sorting_by_height(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress retrieval with height sorting (ascending)."""

        actresses = await async_dmm_client.get_actresses(sort="height", hits=5)

        assert isinstance(actresses, list)
        assert len(actresses) <= 5

        heights = [a.height for a in actresses if a.height is not None]
        if len(heights) >= 2:
            assert heights == sorted(heights)

    async def test_actress_data_completeness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that actress data contains expected fields."""

        actresses = await async_dmm_client.get_actresses(keyword="麻美ゆま", hits=1)

        assert len(actresses) >= 1
        actress = actresses[0]

        assert actress.id is not None
        assert actress.name is not None
        assert isinstance(actress.id, int)
        assert isinstance(actress.name, str)

    async def test_actress_measurements_data(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress measurements data."""

        actresses = await async_dmm_client.get_actresses(keyword="麻美ゆま", hits=1)

        assert len(actresses) >= 1
        actress = actresses[0]

        if actress.bust is not None:
            assert isinstance(actress.bust, int)
            assert actress.bust > 0

        if actress.waist is not None:
            assert isinstance(actress.waist, int)
            assert actress.waist > 0

        if actress.hip is not None:
            assert isinstance(actress.hip, int)
            assert actress.hip > 0

        if actress.height is not None:
            assert isinstance(actress.height, int)
            assert actress.height > 0

    async def test_actress_image_urls(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test actress image URL data."""

        actresses = await async_dmm_client.get_actresses(keyword="麻美ゆま", hits=1)

        assert len(actresses) >= 1
        actress = actresses[0]

        if actress.image_url is not None:
            assert (
                actress.image_url.small is not None
                or actress.image_url.large is not None
            )

            if actress.image_url.small:
                assert actress.image_url.small.startswith("http")

            if actress.image_url.large:
                assert actress.image_url.large.startswith("http")

    async def test_actress_list_urls(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test actress content list URLs."""

        actresses = await async_dmm_client.get_actresses(keyword="麻美ゆま", hits=1)

        assert len(actresses) >= 1
        actress = actresses[0]

        if actress.list_url is not None:
            if actress.list_url.digital:
                assert actress.list_url.digital.startswith("http")

            if actress.list_url.monthly:
                assert actress.list_url.monthly.startswith("http")

            if actress.list_url.mono:
                assert actress.list_url.mono.startswith("http")

    async def test_actress_personal_info(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test actress personal information fields."""

        actresses = await async_dmm_client.get_actresses(keyword="麻美ゆま", hits=1)

        assert len(actresses) >= 1
        actress = actresses[0]

        if actress.ruby is not None:
            assert isinstance(actress.ruby, str)

        if actress.cup is not None:
            assert isinstance(actress.cup, str)

        if actress.birthday is not None:
            assert isinstance(actress.birthday, str)
            assert len(actress.birthday) == 10

        if actress.blood_type is not None:
            assert isinstance(actress.blood_type, str)

        if actress.hobby is not None:
            assert isinstance(actress.hobby, str)

        if actress.prefectures is not None:
            assert isinstance(actress.prefectures, str)

    async def test_empty_results_valid_request(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test handling of valid requests that return no results."""

        actresses = await async_dmm_client.get_actresses(
            keyword="xyznomatchkeyword12345", hits=1
        )

        assert isinstance(actresses, list)
        assert len(actresses) == 0

    async def test_pagination_with_offset(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test pagination using offset parameter."""

        first_page = await async_dmm_client.get_actresses(hits=5, offset=1)

        second_page = await async_dmm_client.get_actresses(hits=5, offset=6)

        assert len(first_page) <= 5
        assert len(second_page) <= 5

        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {a.id for a in first_page}
            second_ids = {a.id for a in second_page}
            assert first_ids != second_ids

    async def test_get_actress_by_id(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving a specific actress by ID."""

        actresses = await async_dmm_client.get_actresses(actress_id=15365, hits=1)

        assert len(actresses) >= 1
        actress = actresses[0]

        assert actress.id == 15365
        assert actress.name == "麻美ゆま"
        assert actress.ruby == "あさみゆま"

        if actress.bust is not None:
            assert actress.bust == 96

        if actress.cup is not None:
            assert actress.cup == "H"

        if actress.waist is not None:
            assert actress.waist == 58

        if actress.hip is not None:
            assert actress.hip == 88

        if actress.height is not None:
            assert actress.height == 158

        if actress.birthday is not None:
            assert actress.birthday == "1987-03-24"

        if actress.blood_type is not None:
            assert actress.blood_type == "AB"

    async def test_get_actress_with_nonexistent_id(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test retrieving an actress with non-existent ID."""

        actresses = await async_dmm_client.get_actresses(actress_id=999999999, hits=1)

        assert isinstance(actresses, list)
        assert len(actresses) == 0

    async def test_combined_filters(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test actress search with multiple combined filters."""

        actresses = await async_dmm_client.get_actresses(
            initial="あ",
            gte_bust=85,
            lte_bust=100,
            gte_height=155,
            lte_height=165,
            hits=3,
            sort="-bust",
        )

        assert isinstance(actresses, list)
        assert len(actresses) <= 3

        for actress in actresses:
            assert isinstance(actress, Actress)
            if actress.ruby:
                assert actress.ruby[0] in ["あ", "ア"]
            if actress.bust is not None:
                assert 85 <= actress.bust <= 100
            if actress.height is not None:
                assert 155 <= actress.height <= 165

    async def test_multiple_concurrent_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test multiple concurrent API requests."""

        results = await asyncio.gather(
            async_dmm_client.get_actresses(initial="あ", hits=3),
            async_dmm_client.get_actresses(initial="か", hits=3),
            async_dmm_client.get_actresses(initial="さ", hits=3),
        )

        assert len(results) == 3
        assert all(isinstance(actresses, list) for actresses in results)
        assert all(len(actresses) <= 3 for actresses in results)

    async def test_session_reuse_across_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that session is reused across multiple requests."""

        actresses1 = await async_dmm_client.get_actresses(hits=1)

        actresses2 = await async_dmm_client.get_actresses(hits=1)

        assert len(actresses1) >= 0
        assert len(actresses2) >= 0
        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

    async def test_client_context_manager(self, app_id, aff_id):
        """Test async client as context manager."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            actresses = await client.get_actresses(hits=1)
            assert isinstance(actresses, list)

    async def test_large_result_set(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test retrieving larger result sets."""

        actresses = await async_dmm_client.get_actresses(hits=50)

        assert isinstance(actresses, list)
        assert len(actresses) <= 50

        for actress in actresses:
            assert isinstance(actress, Actress)
            assert actress.id is not None

    async def test_actress_sorting_variations(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test different sorting options."""

        actresses_asc = await async_dmm_client.get_actresses(sort="id", hits=5)
        assert isinstance(actresses_asc, list)

        actresses_desc = await async_dmm_client.get_actresses(sort="-id", hits=5)
        assert isinstance(actresses_desc, list)

        if len(actresses_asc) > 0 and len(actresses_desc) > 0:
            ids_asc = [a.id for a in actresses_asc]
            ids_desc = [a.id for a in actresses_desc]
            assert ids_asc == sorted(ids_asc)
            assert ids_desc == sorted(ids_desc, reverse=True)

    async def test_error_handling_with_invalid_parameters(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test error handling with potentially invalid parameters."""

        actresses = await async_dmm_client.get_actresses(offset=99999, hits=1)
        assert isinstance(actresses, list)

    async def test_actress_with_complete_profile(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test retrieving an actress known to have complete profile data."""

        actresses = await async_dmm_client.get_actresses(actress_id=15365, hits=1)

        assert len(actresses) >= 1
        actress = actresses[0]

        assert actress.id == 15365
        assert actress.name is not None
        assert actress.ruby is not None
        assert actress.bust is not None
        assert actress.cup is not None
        assert actress.waist is not None
        assert actress.hip is not None
        assert actress.height is not None
        assert actress.birthday is not None
        assert actress.blood_type is not None
        assert actress.image_url is not None
        assert actress.list_url is not None

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
                await async_dmm_client.get_actresses(keyword="test")

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
                    await async_dmm_client.get_actresses(keyword="test")

                assert "Failed to get actresses" in str(exc_info.value)
                assert "Unexpected error" in str(exc_info.value)
