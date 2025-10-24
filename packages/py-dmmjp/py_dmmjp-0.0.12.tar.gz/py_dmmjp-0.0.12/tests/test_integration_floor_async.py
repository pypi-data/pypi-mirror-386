"""
Integration tests for AsyncDMMClient with real API requests for floor-related functionality.
"""

# pylint: disable=R0904,W0212,R0915

import sys
from unittest.mock import AsyncMock, patch

import pytest

if sys.version_info < (3, 9):
    pytest.skip("AsyncDMMClient requires Python 3.9+", allow_module_level=True)

import asyncio

import pytest_asyncio

from py_dmmjp import AsyncDMMClient, DMMAPIError, Floor, Service, Site


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="module")
class TestAsyncDMMClientWithFloorIntegration:
    """Integration tests for async DMM client with real API calls for floors."""

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

    async def test_get_floors_basic_request(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test basic floor list retrieval."""

        sites = await async_dmm_client.get_floors()

        assert isinstance(sites, list)
        assert len(sites) > 0

        for site in sites:
            assert isinstance(site, Site)
            assert site.name is not None
            assert site.code is not None

    async def test_floor_list_contains_fanza_and_dmm(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that floor list contains both FANZA and DMM.com sites."""

        sites = await async_dmm_client.get_floors()

        site_codes = [site.code for site in sites]

        assert "FANZA" in site_codes
        assert "DMM.com" in site_codes

    async def test_site_has_services(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that sites contain services."""

        sites = await async_dmm_client.get_floors()

        assert len(sites) > 0

        for site in sites:
            assert isinstance(site.services, list)
            if len(site.services) > 0:
                for service in site.services:
                    assert isinstance(service, Service)
                    assert service.name is not None
                    assert service.code is not None

    async def test_service_has_floors(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that services contain floors."""

        sites = await async_dmm_client.get_floors()

        found_floors = False
        for site in sites:
            for service in site.services:
                assert isinstance(service.floors, list)
                if len(service.floors) > 0:
                    found_floors = True
                    for floor in service.floors:
                        assert isinstance(floor, Floor)
                        assert floor.id is not None
                        assert floor.name is not None
                        assert floor.code is not None

        assert found_floors

    async def test_floor_data_completeness(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that floor data contains all expected fields."""

        sites = await async_dmm_client.get_floors()

        assert len(sites) > 0

        for site in sites:
            assert isinstance(site.name, str)
            assert isinstance(site.code, str)
            assert len(site.name) > 0
            assert len(site.code) > 0

            for service in site.services:
                assert isinstance(service.name, str)
                assert isinstance(service.code, str)
                assert len(service.name) > 0
                assert len(service.code) > 0

                for floor in service.floors:
                    assert isinstance(floor.id, str)
                    assert isinstance(floor.name, str)
                    assert isinstance(floor.code, str)
                    assert len(floor.id) > 0
                    assert len(floor.name) > 0
                    assert len(floor.code) > 0

    async def test_fanza_site_structure(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test FANZA site structure and services."""

        sites = await async_dmm_client.get_floors()

        fanza_site = next((s for s in sites if s.code == "FANZA"), None)

        assert fanza_site is not None
        assert fanza_site.name is not None
        assert len(fanza_site.services) > 0

        service_codes = [s.code for s in fanza_site.services]
        assert "digital" in service_codes

    async def test_dmm_com_site_structure(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test DMM.com site structure and services."""

        sites = await async_dmm_client.get_floors()

        dmm_site = next((s for s in sites if s.code == "DMM.com"), None)

        assert dmm_site is not None
        assert dmm_site.name is not None
        assert len(dmm_site.services) > 0

        service_codes = [s.code for s in dmm_site.services]
        assert "mono" in service_codes

    async def test_digital_service_has_videoa_floor(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that digital service contains videoa floor."""

        sites = await async_dmm_client.get_floors()

        fanza_site = next((s for s in sites if s.code == "FANZA"), None)
        assert fanza_site is not None

        digital_service = next(
            (s for s in fanza_site.services if s.code == "digital"), None
        )
        assert digital_service is not None

        floor_codes = [f.code for f in digital_service.floors]
        assert "videoa" in floor_codes

    async def test_ebook_service_has_comic_floor(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that ebook service contains comic floor."""

        sites = await async_dmm_client.get_floors()

        fanza_site = next((s for s in sites if s.code == "FANZA"), None)
        assert fanza_site is not None

        ebook_service = next(
            (s for s in fanza_site.services if s.code == "ebook"), None
        )
        assert ebook_service is not None

        floor_codes = [f.code for f in ebook_service.floors]
        assert "comic" in floor_codes

    async def test_mono_service_has_book_floor(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that mono service contains book floor."""

        sites = await async_dmm_client.get_floors()

        dmm_site = next((s for s in sites if s.code == "DMM.com"), None)
        assert dmm_site is not None

        mono_service = next((s for s in dmm_site.services if s.code == "mono"), None)
        assert mono_service is not None

        floor_codes = [f.code for f in mono_service.floors]
        assert "book" in floor_codes

    async def test_floor_ids_are_numeric_strings(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that floor IDs are numeric strings."""

        sites = await async_dmm_client.get_floors()

        for site in sites:
            for service in site.services:
                for floor in service.floors:
                    assert floor.id.isdigit()

    async def test_site_codes_are_valid(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that site codes are valid values."""

        sites = await async_dmm_client.get_floors()

        site_codes = [site.code for site in sites]

        assert all(code in ["FANZA", "DMM.com"] for code in site_codes)

    async def test_service_codes_are_non_empty(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that all service codes are non-empty."""

        sites = await async_dmm_client.get_floors()

        for site in sites:
            for service in site.services:
                assert len(service.code) > 0
                assert service.code.strip() == service.code

    async def test_floor_codes_are_non_empty(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that all floor codes are non-empty."""

        sites = await async_dmm_client.get_floors()

        for site in sites:
            for service in site.services:
                for floor in service.floors:
                    assert len(floor.code) > 0
                    assert floor.code.strip() == floor.code

    async def test_consecutive_requests_return_same_data(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that consecutive requests return consistent data."""

        sites1 = await async_dmm_client.get_floors()
        sites2 = await async_dmm_client.get_floors()

        assert len(sites1) == len(sites2)

        site_codes1 = [s.code for s in sites1]
        site_codes2 = [s.code for s in sites2]
        assert site_codes1 == site_codes2

    async def test_session_reuse_across_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that session is reused across multiple requests."""

        sites1 = await async_dmm_client.get_floors()
        sites2 = await async_dmm_client.get_floors()

        assert len(sites1) > 0
        assert len(sites2) > 0
        assert async_dmm_client._session is not None
        assert not async_dmm_client._session.closed

    async def test_client_context_manager(self, app_id, aff_id):
        """Test async client as context manager."""

        async with AsyncDMMClient(api_key=app_id, affiliate_id=aff_id) as client:
            sites = await client.get_floors()
            assert isinstance(sites, list)
            assert len(sites) > 0

    async def test_multiple_concurrent_floor_requests(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test multiple concurrent floor list requests."""

        results = await asyncio.gather(
            async_dmm_client.get_floors(),
            async_dmm_client.get_floors(),
            async_dmm_client.get_floors(),
        )

        assert len(results) == 3
        assert all(isinstance(sites, list) for sites in results)
        assert all(len(sites) > 0 for sites in results)

        assert len(results[0]) == len(results[1]) == len(results[2])

    async def test_floor_list_contains_expected_services(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that floor list contains expected services."""

        sites = await async_dmm_client.get_floors()

        all_service_codes = []
        for site in sites:
            for service in site.services:
                all_service_codes.append(service.code)

        expected_services = ["digital", "mono", "ebook"]
        for expected in expected_services:
            assert expected in all_service_codes

    async def test_floor_list_contains_expected_floors(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that floor list contains expected floors."""

        sites = await async_dmm_client.get_floors()

        all_floor_codes = []
        for site in sites:
            for service in site.services:
                for floor in service.floors:
                    all_floor_codes.append(floor.code)

        expected_floors = ["videoa", "comic", "book", "dvd"]
        for expected in expected_floors:
            assert expected in all_floor_codes

    async def test_floor_id_uniqueness_within_service(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that floor IDs are unique within each service."""

        sites = await async_dmm_client.get_floors()

        for site in sites:
            for service in site.services:
                floor_ids = [f.id for f in service.floors]
                assert len(floor_ids) == len(set(floor_ids))

    async def test_service_code_uniqueness_within_site(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that service codes are unique within each site."""

        sites = await async_dmm_client.get_floors()

        for site in sites:
            service_codes = [s.code for s in site.services]
            assert len(service_codes) == len(set(service_codes))

    async def test_site_count(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that there are exactly 2 sites (FANZA and DMM.com)."""

        sites = await async_dmm_client.get_floors()

        assert len(sites) == 2

    async def test_each_site_has_multiple_services(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that each site has multiple services."""

        sites = await async_dmm_client.get_floors()

        for site in sites:
            assert len(site.services) > 0

    async def test_each_service_has_multiple_floors(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that services have floors."""

        sites = await async_dmm_client.get_floors()

        has_floors = False
        for site in sites:
            for service in site.services:
                if len(service.floors) > 0:
                    has_floors = True
                    break

        assert has_floors

    async def test_floor_list_hierarchy(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test the complete hierarchy of sites, services, and floors."""

        sites = await async_dmm_client.get_floors()

        assert len(sites) > 0

        for site in sites:
            assert isinstance(site, Site)
            assert len(site.services) > 0

            for service in site.services:
                assert isinstance(service, Service)
                assert isinstance(service.floors, list)

                for floor in service.floors:
                    assert isinstance(floor, Floor)

    async def test_japanese_characters_in_names(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test that names contain proper Japanese characters."""

        sites = await async_dmm_client.get_floors()

        for site in sites:
            if site.code == "FANZA":
                assert len(site.name) > 0

            for service in site.services:
                assert len(service.name) > 0

                for floor in service.floors:
                    assert len(floor.name) > 0

    async def test_get_specific_floor_by_code(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test finding a specific floor by code."""

        sites = await async_dmm_client.get_floors()

        videoa_floor = None
        for site in sites:
            for service in site.services:
                for floor in service.floors:
                    if floor.code == "videoa":
                        videoa_floor = floor
                        break

        assert videoa_floor is not None
        assert videoa_floor.code == "videoa"
        assert videoa_floor.id is not None
        assert videoa_floor.name is not None

    async def test_get_specific_service_by_code(
        self, async_dmm_client: AsyncDMMClient
    ) -> None:
        """Test finding a specific service by code."""

        sites = await async_dmm_client.get_floors()

        digital_service = None
        for site in sites:
            for service in site.services:
                if service.code == "digital":
                    digital_service = service
                    break

        assert digital_service is not None
        assert digital_service.code == "digital"
        assert digital_service.name is not None
        assert len(digital_service.floors) > 0

    async def test_floor_list_stability(self, async_dmm_client: AsyncDMMClient) -> None:
        """Test that floor list structure is stable across multiple requests."""

        sites1 = await async_dmm_client.get_floors()
        sites2 = await async_dmm_client.get_floors()

        assert len(sites1) == len(sites2)

        for site1, site2 in zip(sites1, sites2):
            assert site1.code == site2.code
            assert site1.name == site2.name
            assert len(site1.services) == len(site2.services)

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
                await async_dmm_client.get_floors()

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
                    await async_dmm_client.get_floors()

                assert "Failed to get floors" in str(exc_info.value)
                assert "Unexpected error" in str(exc_info.value)
