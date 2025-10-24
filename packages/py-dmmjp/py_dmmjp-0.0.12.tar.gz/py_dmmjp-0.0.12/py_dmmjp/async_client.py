"""
Async client class for the py-dmm library.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Literal, Optional, cast

if sys.version_info < (3, 9):  # pragma: no cover
    raise ImportError(
        f"AsyncDMMClient requires Python 3.9 or above. "
        f"Your current Python version is {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}."
    )

import aiohttp
from aiohttp import ClientTimeout

from .actress import Actress, ActressSearchParams, ActressSearchResponse
from .author import Author, AuthorSearchParams, AuthorSearchResponse
from .exceptions import DMMAPIError, DMMAuthError, DMMError
from .floor import FloorListResponse, Site
from .genre import Genre, GenreSearchParams, GenreSearchResponse
from .maker import Maker, MakerSearchParams, MakerSearchResponse
from .product import Product, ProductSearchParams
from .series import Series, SeriesSearchParams, SeriesSearchResponse

try:
    from typing import Unpack
except ImportError:  # pragma: no cover
    from typing_extensions import Unpack


class AsyncDMMClient:
    """
    An async client for interacting with the DMM API.
    """

    def __init__(
        self,
        api_key: str,
        affiliate_id: str,
        timeout: int = 10,
    ) -> None:
        """
        Initialize the async DMM client.

        Args:
            api_key: Your DMM API key for authentication.
            affiliate_id: Your DMM affiliate ID.
            timeout: Request timeout in seconds.

        Raises:
            DMMAuthError: If the API key is invalid or missing.
        """

        if (
            not api_key
            or not api_key.strip()
            or not affiliate_id
            or not affiliate_id.strip()
        ):
            raise DMMAuthError("API_KEY and AFFILIATE_KEY are required")

        self._api_key = api_key
        self._affiliate_id = affiliate_id
        self._base_url = "https://api.dmm.com/affiliate/v3"
        self._timeout = timeout
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """
        Ensure that a session exists, creating one if necessary.

        Returns:
            aiohttp.ClientSession: The active session.
        """

        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(
                headers=self._headers, timeout=timeout
            )

        return self._session

    def _prepare_params(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare request parameters by adding authentication details.

        Args:
            params: Original query parameters.

        Returns:
            Updated query parameters with authentication details.
        """

        if params is None:
            params = {}

        params["api_id"] = self._api_key
        params["affiliate_id"] = self._affiliate_id
        params["output"] = "json"

        return params

    def _load_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Load JSON data from the response text.

        Args:
            response_text: The raw response text from the API.
        Returns:
            JSON data as a dictionary.
        """

        try:
            return cast(Dict[str, Any], json.loads(response_text))
        except ValueError as e:
            raise DMMAPIError("Error while formatting DMM Response") from e

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async request to the DMM API.

        Args:
            endpoint: API endpoint to call.
            params: Query parameters to include.

        Returns:
            JSON response data.

        Raises:
            DMMAPIError: If the API request fails.
            DMMAuthError: If authentication fails.
        """

        url = f"{self._base_url}{endpoint}"
        prep_params = self._prepare_params(params)
        session = await self._ensure_session()

        try:
            async with session.get(url, params=prep_params) as response:
                print(await response.text())
                response_text = await response.text()

                if response.status == 401:
                    raise DMMAuthError("Invalid API key or authentication failed")

                if response.status == 403:
                    raise DMMAuthError(
                        "Access forbidden - check your API key permissions"
                    )

                if response.status >= 400:
                    raise DMMAPIError(
                        f"HTTP {response.status}: {response_text}",
                        status_code=response.status,
                        response_data=response_text,
                    )

                return self._load_json_from_response(response_text)

        except aiohttp.ServerTimeoutError as e:
            raise DMMAPIError("Request timed out") from e
        except aiohttp.ClientConnectionError as e:
            raise DMMAPIError("Connection error occurred") from e
        except aiohttp.ClientError as e:
            raise DMMAPIError(f"Request failed: {str(e)}") from e

    @property
    def app_id(self) -> str:
        """
        Get the API key used by the client.

        Returns:
            The API key as a string.
        """

        return self._api_key

    @property
    def affiliate_id(self) -> str:
        """
        Get the affiliate ID used by the client.

        Returns:
            The affiliate ID as a string.
        """
        return self._affiliate_id

    async def get_products(
        self,
        **kwargs: Unpack[ProductSearchParams],
    ) -> List[Product]:
        """
        Retrieve product information from the DMM API asynchronously.

        This method fetches products from the DMM API and returns a simple list
        of Product objects, handling the API response internally.

        Args:
            site: Site to search. Either "FANZA" for adult content or "DMM.com" for general content.
            service: Service code that the products can be retrieved from.
            floor: Floor code that the products can be retrieved from.
            keyword: Search keyword. Can be title, actress name, product ID, maker ID, etc.
            hits: Number of results to return. Default is 20, maximum is 100.
            offset: Starting position for results. Default is 1, maximum is 50000.
            sort: Sort order for results.
            cid: Product ID (content_id) for specific product lookup.
            article: Filter categories for refined search.
            article_id: Filter IDs corresponding to article categories.
            gte_date: Release date filter (from) in ISO8601 format.
            lte_date: Release date filter (to) in ISO8601 format.
            mono_stock: Stock filter for retail services.
            **kwargs: Additional product search parameters.

        Returns:
            List[Product]: List of Product objects containing product information.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        params: Dict[str, Any] = {}
        params.update(kwargs)

        try:
            response_data = await self._make_request("/ItemList", params)

            if "result" not in response_data:
                raise DMMAPIError("Invalid API response: missing 'result' field")

            result = response_data["result"]
            items = result.get("items", [])
            products = [Product.from_dict(item) for item in items]

            return products

        except Exception as e:
            if isinstance(e, (DMMError, DMMAPIError, DMMAuthError)):
                raise

            raise DMMAPIError(f"Failed to get products: {str(e)}") from e

    async def get_product_by_cid(
        self, cid: str, site: Literal["FANZA", "DMM.com"]
    ) -> Optional[Product]:
        """
        Retrieve a single product by its content ID (cid) asynchronously.

        Args:
            cid: The content ID of the product to retrieve.
            site: Site to search. Either "FANZA" for adult content or "DMM.com" for general content.

        Returns:
            Optional[Product]: The Product object if found, otherwise None.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        products = await self.get_products(site=site, cid=cid, hits=1)

        return products[0] if products else None

    async def get_product_by_product_id(
        self, product_id: str, site: Literal["FANZA", "DMM.com"]
    ) -> Optional[Product]:
        """
        Retrieve a single product by its product ID asynchronously.

        Args:
            product_id: The product ID of the product to retrieve.
            site: Site to search.

        Returns:
            Optional[Product]: The Product object if found, otherwise None.
        """

        def __predicate(p: Product) -> bool:
            if p.maker_product:
                if p.maker_product.lower() == product_id.lower():
                    return True

                if "-" in p.maker_product:
                    prefix, suffix = p.maker_product.split("-", 1)

                    if len(suffix) == 2:
                        new_maker_product = f"{prefix}-0{suffix}"

                        return new_maker_product.lower() == product_id.lower()

            return False

        products = await self.get_products(site=site, keyword=product_id)
        product = next((p for p in products if __predicate(p)), None)

        return product

    async def get_floors(self) -> List[Site]:
        """
        Retrieve the floor list from the DMM API asynchronously.

        Returns:
            List[Site]: List of Site objects containing floor information.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        try:
            response_data = await self._make_request("/FloorList")

            if "result" not in response_data:
                raise DMMAPIError("Invalid API response: missing 'result' field")

            floor_response = FloorListResponse.from_dict(response_data)
            sites = floor_response.result.sites

            return sites

        except Exception as e:
            if isinstance(e, (DMMError, DMMAPIError, DMMAuthError)):
                raise

            raise DMMAPIError(f"Failed to get floors: {str(e)}") from e

    async def get_actresses(
        self,
        **kwargs: Unpack[ActressSearchParams],
    ) -> List[Actress]:
        """
        Retrieve actress information from the DMM API asynchronously.

        Args:
            initial: Specify 50-sound in UTF-8.
            actress_id: Specific actress ID to retrieve.
            keyword: Search keyword in UTF-8.
            gte_bust: Bust measurement equal or greater than (cm).
            lte_bust: Bust measurement equal or less than (cm).
            gte_waist: Waist measurement equal or greater than (cm).
            lte_waist: Waist measurement equal or less than (cm).
            gte_hip: Hip measurement equal or greater than (cm).
            lte_hip: Hip measurement equal or less than (cm).
            gte_height: Height equal or greater than (cm).
            lte_height: Height equal or less than (cm).
            gte_birthday: Birthday filter (from) in YYYY-MM-DD format.
            lte_birthday: Birthday filter (to) in YYYY-MM-DD format.
            hits: Number of results to return.
            offset: Starting position for results.
            sort: Sort order.
            **kwargs: Additional actress search parameters.

        Returns:
            List[Actress]: List of Actress objects containing actress information.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        params: Dict[str, Any] = {}
        params.update(kwargs)

        try:
            response_data = await self._make_request("/ActressSearch", params)

            if "result" not in response_data:
                raise DMMAPIError("Invalid API response: missing 'result' field")

            actress_response = ActressSearchResponse.from_dict(response_data)

            return actress_response.actresses

        except Exception as e:
            if isinstance(e, (DMMError, DMMAPIError, DMMAuthError)):
                raise

            raise DMMAPIError(f"Failed to get actresses: {str(e)}") from e

    async def get_genres(
        self, floor_id: int, **kwargs: Unpack["GenreSearchParams"]
    ) -> List["Genre"]:
        """
        Retrieve genre information from the DMM API asynchronously.

        Args:
            floor_id: Floor ID available from Floor Search API (required).
            initial: Specify 50-sound in UTF-8.
            hits: Number of results to return.
            offset: Search start position.
            **kwargs: Additional genre search parameters.

        Returns:
            List[Genre]: List of Genre objects containing genre information.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        if not floor_id or not isinstance(floor_id, int):
            raise DMMAPIError("floor_id is required and must be a non-zero integer")

        params: Dict[str, Any] = {"floor_id": floor_id}
        params.update(kwargs)

        try:
            response_data = await self._make_request("/GenreSearch", params)

            if "result" not in response_data:
                raise DMMAPIError("Invalid API response: missing 'result' field")

            genre_response = GenreSearchResponse.from_dict(response_data)
            return genre_response.genres

        except Exception as e:
            if isinstance(e, (DMMError, DMMAPIError, DMMAuthError)):
                raise

            raise DMMAPIError(f"Failed to get genres: {str(e)}") from e

    async def get_makers(
        self, floor_id: int, **kwargs: Unpack[MakerSearchParams]
    ) -> List[Maker]:
        """
        Retrieve maker information from the DMM API asynchronously.

        Args:
            floor_id: Floor ID available from Floor Search API (required).
            initial: Specify 50-sound in UTF-8.
            hits: Number of results to return.
            offset: Search start position.
            **kwargs: Additional maker search parameters.

        Returns:
            List[Maker]: List of Maker objects containing maker information.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        if not floor_id or not isinstance(floor_id, int):
            raise DMMAPIError("floor_id is required and must be a non-zero integer")

        params: Dict[str, Any] = {"floor_id": floor_id}
        params.update(kwargs)

        try:
            response_data = await self._make_request("/MakerSearch", params)

            if "result" not in response_data:
                raise DMMAPIError("Invalid API response: missing 'result' field")

            maker_response = MakerSearchResponse.from_dict(response_data)

            return maker_response.makers

        except Exception as e:
            if isinstance(e, (DMMError, DMMAPIError, DMMAuthError)):
                raise

            raise DMMAPIError(f"Failed to get makers: {str(e)}") from e

    async def get_series(
        self, floor_id: int, **kwargs: Unpack["SeriesSearchParams"]
    ) -> List["Series"]:
        """
        Retrieve series information from the DMM API asynchronously.

        Args:
            floor_id: Floor ID available from Floor Search API (required).
            initial: Specify 50-sound in UTF-8.
            hits: Number of results to return.
            offset: Search start position.
            **kwargs: Additional series search parameters.

        Returns:
            List[Series]: List of Series objects containing series information.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        if not floor_id or not isinstance(floor_id, int):
            raise DMMAPIError("floor_id is required and must be a non-zero integer")

        params: Dict[str, Any] = {"floor_id": floor_id}
        params.update(kwargs)

        try:
            response_data = await self._make_request("/SeriesSearch", params)

            if "result" not in response_data:
                raise DMMAPIError("Invalid API response: missing 'result' field")

            series_response = SeriesSearchResponse.from_dict(response_data)

            return series_response.series

        except Exception as e:
            if isinstance(e, (DMMError, DMMAPIError, DMMAuthError)):
                raise

            raise DMMAPIError(f"Failed to get series: {str(e)}") from e

    async def get_authors(
        self, floor_id: int, **kwargs: Unpack[AuthorSearchParams]
    ) -> List[Author]:
        """
        Retrieve author information from the DMM API asynchronously.

        Args:
            floor_id: Floor ID available from Floor Search API (required).
            initial: Specify author name phonetic reading in UTF-8.
            hits: Number of results to return.
            offset: Search start position.
            **kwargs: Additional author search parameters.

        Returns:
            List[Author]: List of Author objects containing author information.

        Raises:
            DMMAPIError: If the API request fails or returns an error.
            DMMAuthError: If authentication fails or API key is invalid.
        """

        if not floor_id or not isinstance(floor_id, int):
            raise DMMAPIError("floor_id is required and must be a non-zero integer")

        params: Dict[str, Any] = {"floor_id": floor_id}
        params.update(kwargs)

        try:
            response_data = await self._make_request("/AuthorSearch", params)

            if "result" not in response_data:
                raise DMMAPIError("Invalid API response: missing 'result' field")

            author_response = AuthorSearchResponse.from_dict(response_data)

            return author_response.authors

        except Exception as e:
            if isinstance(e, (DMMError, DMMAPIError, DMMAuthError)):
                raise

            raise DMMAPIError(f"Failed to get authors: {str(e)}") from e

    async def close(self) -> None:
        """
        Explicitly close the HTTP session.
        """

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def __del__(self) -> None:
        """
        Destructor to clean up session if not properly closed.
        """

        if hasattr(self, "_session") and self._session and not self._session.closed:
            try:
                loop = asyncio.get_event_loop()

                if loop.is_running():
                    loop.create_task(self._session.close())
                else:
                    loop.run_until_complete(self._session.close())
            except Exception as e:
                raise DMMAPIError("Error occurred while closing the session") from e

    async def __aenter__(self) -> "AsyncDMMClient":
        """
        Async context manager entry.

        Returns:
            AsyncDMMClient: The client instance for use in the context.
        """

        await self._ensure_session()

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Async context manager exit.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """

        await self.close()
