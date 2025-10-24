"""
src/geocodio/client.py
High‑level synchronous client for the Geocodio API.
"""

from __future__ import annotations

import logging
import os
from typing import List, Union, Dict, Tuple, Optional

import httpx

from geocodio._version import __version__

# Set up logger early to capture all logs
logger = logging.getLogger("geocodio")

# flake8: noqa: F401
from geocodio.models import (
    GeocodingResponse, GeocodingResult, AddressComponents,
    Location, GeocodioFields, Timezone, CongressionalDistrict,
    CensusData, ACSSurveyData, StateLegislativeDistrict, SchoolDistrict,
    Demographics, Economics, Families, Housing, Social,
    FederalRiding, ProvincialRiding, StatisticsCanadaData, ListResponse, PaginatedResponse
)
from geocodio.exceptions import InvalidRequestError, AuthenticationError, GeocodioServerError, BadRequestError


class Geocodio:
    BASE_PATH = "/v1.9"  # keep in sync with Geocodio's current version
    DEFAULT_SINGLE_TIMEOUT = 5.0
    DEFAULT_BATCH_TIMEOUT = 1800.0  # 30 minutes
    LIST_API_TIMEOUT = 60.0
    USER_AGENT = f"geocodio-library-python/{__version__}"

    @staticmethod
    def get_status_exception_mappings() -> Dict[
        int, type[BadRequestError | InvalidRequestError | AuthenticationError | GeocodioServerError]
    ]:
        """
        Returns a list of status code to exception mappings.
        This is used to map HTTP status codes to specific exceptions.
        """
        return {
            400: BadRequestError,
            422: InvalidRequestError,
            403: AuthenticationError,
            500: GeocodioServerError,
        }

    def __init__(
        self,
        api_key: Optional[str] = None,
        hostname: str = "api.geocod.io",
        single_timeout: Optional[float] = None,
        batch_timeout: Optional[float] = None,
        list_timeout: Optional[float] = None,
    ):
        self.api_key: str = api_key or os.getenv("GEOCODIO_API_KEY", "")
        if not self.api_key:
            raise AuthenticationError(
                detail="No API key supplied and GEOCODIO_API_KEY is not set."
            )
        self.hostname = hostname.rstrip("/")
        self.single_timeout = single_timeout or self.DEFAULT_SINGLE_TIMEOUT
        self.batch_timeout = batch_timeout or self.DEFAULT_BATCH_TIMEOUT
        self.list_timeout = list_timeout or self.LIST_API_TIMEOUT
        self._http = httpx.Client(base_url=f"https://{self.hostname}")

    # ──────────────────────────────────────────────────────────────────────────
    # Public methods
    # ──────────────────────────────────────────────────────────────────────────

    def geocode(
            self,
            address: Union[
                str, Dict[str, str], List[Union[str, Dict[str, str]]], Dict[str, Union[str, Dict[str, str]]]],
            fields: Optional[List[str]] = None,
            limit: Optional[int] = None,
            country: Optional[str] = None,
    ) -> GeocodingResponse:
        params: Dict[str, Union[str, int]] = {}
        if fields:
            params["fields"] = ",".join(fields)
        if limit:
            params["limit"] = int(limit)
        if country:
            params["country"] = country

        endpoint: str
        data: Union[List, Dict] | None

        # Handle different input types
        if isinstance(address, dict) and not any(isinstance(v, dict) for v in address.values()):
            # Single structured address
            endpoint = f"{self.BASE_PATH}/geocode"
            # Map our parameter names to API parameter names
            param_map = {
                "street": "street",
                "street2": "street2",
                "city": "city",
                "county": "county",
                "state": "state",
                "postal_code": "postal_code",
                "country": "country",
            }
            # Only include parameters that are present in the input
            for key, value in address.items():
                if key in param_map and value:
                    params[param_map[key]] = value
            data = None
        elif isinstance(address, list):
            # Batch addresses - send list directly
            endpoint = f"{self.BASE_PATH}/geocode"
            data = address
        elif isinstance(address, dict) and any(isinstance(v, dict) for v in address.values()):
            # Batch addresses with custom keys
            endpoint = f"{self.BASE_PATH}/geocode"
            data = {"addresses": list(address.values()), "keys": list(address.keys())}
        else:
            # Single address string
            endpoint = f"{self.BASE_PATH}/geocode"
            params["q"] = address
            data = None

        timeout = self.batch_timeout if data else self.single_timeout
        response = self._request("POST" if data else "GET", endpoint, params, json=data, timeout=timeout)
        return self._parse_geocoding_response(response.json())

    def reverse(
            self,
            coordinate: Union[str, Tuple[float, float], List[Union[str, Tuple[float, float]]]],
            fields: Optional[List[str]] = None,
            limit: Optional[int] = None,
    ) -> GeocodingResponse:
        params: Dict[str, Union[str, int]] = {}
        if fields:
            params["fields"] = ",".join(fields)
        if limit:
            params["limit"] = int(limit)

        endpoint: str
        data: Union[List[str], None]

        # Batch vs single coordinate
        if isinstance(coordinate, list):
            endpoint = f"{self.BASE_PATH}/reverse"
            coords_as_strings = []
            for coord in coordinate:
                if isinstance(coord, tuple):
                    coords_as_strings.append(f"{coord[0]},{coord[1]}")
                else:
                    coords_as_strings.append(coord)
            data = coords_as_strings
        else:
            endpoint = f"{self.BASE_PATH}/reverse"
            if isinstance(coordinate, tuple):
                params["q"] = f"{coordinate[0]},{coordinate[1]}"
            else:
                params["q"] = coordinate  # "lat,lng"
            data = None

        timeout = self.batch_timeout if data else self.single_timeout
        response = self._request("POST" if data else "GET", endpoint, params, json=data, timeout=timeout)
        return self._parse_geocoding_response(response.json())

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _request(
            self,
            method: str,
            endpoint: str,
            params: Optional[dict] = None,
            json: Optional[dict] = None,
            files: Optional[dict] = None,
            timeout: Optional[float] = None,
    ) -> httpx.Response:
        logger.debug(f"Making Request: {method} {endpoint}")
        logger.debug(f"Params: {params}")
        logger.debug(f"JSON body: {json}")
        logger.debug(f"Files: {files}")

        if timeout is None:
            timeout = self.single_timeout
        
        # Set up authorization and user-agent headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": self.USER_AGENT
        }
        
        logger.debug(f"Using timeout: {timeout}s")
        resp = self._http.request(method, endpoint, params=params, json=json, files=files, headers=headers, timeout=timeout)

        logger.debug(f"Response status code: {resp.status_code}")
        logger.debug(f"Response headers: {resp.headers}")
        logger.debug(f"Response body: {resp.content}")

        resp = self._handle_error_response(resp)

        return resp

    def _handle_error_response(self, resp) -> httpx.Response:
        if resp.status_code < 400:
            logger.debug("No error in response, returning normally.")
            return resp

        exception_mappings = self.get_status_exception_mappings()
        # dump the type and content of the exception mappings for debugging
        logger.error(f"Error response: {resp.status_code} - {resp.text}")
        if resp.status_code in exception_mappings:
            exception_class = exception_mappings[resp.status_code]
            raise exception_class(resp.text)
        else:
            raise GeocodioServerError(f"Unrecognized status code {resp.status_code}: {resp.text}")

    def _parse_geocoding_response(self, response_json: dict) -> GeocodingResponse:
        logger.debug(f"Raw response: {response_json}")

        # Handle batch response format
        if "results" in response_json and isinstance(response_json["results"], list) and response_json[
            "results"] and "response" in response_json["results"][0]:
            results = [
                GeocodingResult(
                    address_components=AddressComponents.from_api(res["response"]["results"][0]["address_components"]),
                    formatted_address=res["response"]["results"][0]["formatted_address"],
                    location=Location(**res["response"]["results"][0]["location"]),
                    accuracy=res["response"]["results"][0].get("accuracy", 0.0),
                    accuracy_type=res["response"]["results"][0].get("accuracy_type", ""),
                    source=res["response"]["results"][0].get("source", ""),
                    fields=self._parse_fields(res["response"]["results"][0].get("fields")),
                )
                for res in response_json["results"]
            ]
            return GeocodingResponse(input=response_json.get("input", {}), results=results)

        # Handle single response format
        results = [
            GeocodingResult(
                address_components=AddressComponents.from_api(res["address_components"]),
                formatted_address=res["formatted_address"],
                location=Location(**res["location"]),
                accuracy=res.get("accuracy", 0.0),
                accuracy_type=res.get("accuracy_type", ""),
                source=res.get("source", ""),
                fields=self._parse_fields(res.get("fields")),
            )
            for res in response_json.get("results", [])
        ]
        return GeocodingResponse(input=response_json.get("input", {}), results=results)

    # ──────────────────────────────────────────────────────────────────────────
    # List API methods
    # ──────────────────────────────────────────────────────────────────────────

    DIRECTION_FORWARD = "forward"
    DIRECTION_REVERSE = "reverse"

    def create_list(
            self,
            file: Optional[str] = None,
            filename: Optional[str] = None,
            direction: str = DIRECTION_FORWARD,
            format_: Optional[str] = "{{A}}",
            callback_url: Optional[str] = None,
            fields: list[str] | None = None
    ) -> ListResponse:
        """
        Create a new geocoding list.

        Args:
            file: The file content as a string. Required.
            filename: The name of the file. Defaults to "file.csv".
            direction: The direction of geocoding. Either "forward" or "reverse". Defaults to "forward".
            format_: The format string for the output. Defaults to "{{A}}".
            callback_url: Optional URL to call when processing is complete.
            fields: Optional list of fields to include in the response. Valid fields include:
                   - census2010, census2020, census2023
                   - cd, cd113-cd119 (congressional districts)
                   - stateleg, stateleg-next (state legislative districts)
                   - school (school districts)
                   - timezone
                   - acs, acs-demographics, acs-economics, acs-families, acs-housing, acs-social
                   - riding, provriding, provriding-next (Canadian data)
                   - statcan (Statistics Canada data)
                   - zip4 (ZIP+4 data)
                   - ffiec (FFIEC data, beta)

        Returns:
            A ListResponse object containing the created list information.

        Raises:
            ValueError: If file is not provided.
            InvalidRequestError: If the API request is invalid.
            AuthenticationError: If the API key is invalid.
            GeocodioServerError: If the server encounters an error.
        """
        params: Dict[str, Union[str, int]] = {}
        endpoint = f"{self.BASE_PATH}/lists"

        if not file:
            raise ValueError("File data is required to create a list.")
        filename = filename or "file.csv"
        files = {
            "file": (filename, file),
        }
        if direction:
            params["direction"] = direction
        if format_:
            params["format"] = format_
        if callback_url:
            params["callback"] = callback_url
        if fields:
            # Join fields with commas as required by the API
            params["fields"] = ",".join(fields)

        response = self._request("POST", endpoint, params, files=files, timeout=self.list_timeout)
        logger.debug(f"Response content: {response.text}")
        return self._parse_list_response(response.json(), response=response)

    def get_lists(self) -> PaginatedResponse:
        """
        Retrieve all lists.

        Returns:
            A ListResponse object containing all lists.
        """
        params: Dict[str, Union[str, int]] = {}
        endpoint = f"{self.BASE_PATH}/lists"

        response = self._request("GET", endpoint, params, timeout=self.list_timeout)
        pagination_info = response.json()

        logger.debug(f"Pagination info: {pagination_info}")

        response_lists = []
        for list_item in pagination_info.get("data", []):
            logger.debug(f"List item: {list_item}")
            response_lists.append(self._parse_list_response(list_item, response=response))

        return PaginatedResponse(
            data=response_lists,
            current_page=pagination_info.get("current_page", 1),
            from_=pagination_info.get("from", 0),
            to=pagination_info.get("to", 0),
            path=pagination_info.get("path", ""),
            per_page=pagination_info.get("per_page", 10),
            first_page_url=pagination_info.get("first_page_url"),
            next_page_url=pagination_info.get("next_page_url"),
            prev_page_url=pagination_info.get("prev_page_url")
        )

    def get_list(self, list_id: str) -> ListResponse:
        """
        Retrieve a list by ID.

        Args:
            list_id: The ID of the list to retrieve.

        Returns:
            A ListResponse object containing the retrieved list.
        """
        params: Dict[str, Union[str, int]] = {}
        endpoint = f"{self.BASE_PATH}/lists/{list_id}"

        response = self._request("GET", endpoint, params, timeout=self.list_timeout)
        return self._parse_list_response(response.json(), response=response)

    def delete_list(self, list_id: str) -> None:
        """
        Delete a list.

        Args:
            list_id: The ID of the list to delete.
        """
        params: Dict[str, Union[str, int]] = {}
        endpoint = f"{self.BASE_PATH}/lists/{list_id}"

        self._request("DELETE", endpoint, params, timeout=self.list_timeout)

    @staticmethod
    def _parse_list_response(response_json: dict, response: httpx.Response = None) -> ListResponse:
        """
        Parse a response from the List API.

        Args:
            response_json: The JSON response from the List API.

        Returns:
            A ListResponse object.
        """
        logger.debug(f"{response_json}")
        return ListResponse(
            id=response_json.get("id"),
            file=response_json.get("file"),
            status=response_json.get("status"),
            download_url=response_json.get("download_url"),
            expires_at=response_json.get("expires_at"),
            http_response=response,
        )

    def _parse_fields(self, fields_data: dict | None) -> GeocodioFields | None:
        if not fields_data:
            return None

        timezone = (
            Timezone.from_api(fields_data["timezone"])
            if "timezone" in fields_data else None
        )
        congressional_districts = None
        if "cd" in fields_data:
            congressional_districts = [
                CongressionalDistrict.from_api(cd)
                for cd in fields_data["cd"]
            ]
        elif "congressional_districts" in fields_data:
            congressional_districts = [
                CongressionalDistrict.from_api(cd)
                for cd in fields_data["congressional_districts"]
            ]

        state_legislative_districts = None
        if "stateleg" in fields_data:
            state_legislative_districts = [
                StateLegislativeDistrict.from_api(district)
                for district in fields_data["stateleg"]
            ]

        state_legislative_districts_next = None
        if "stateleg-next" in fields_data:
            state_legislative_districts_next = [
                StateLegislativeDistrict.from_api(district)
                for district in fields_data["stateleg-next"]
            ]

        school_districts = None
        if "school" in fields_data:
            school_districts = [
                SchoolDistrict.from_api(district)
                for district in fields_data["school"]
            ]

        # Dynamically parse all census fields (e.g., census2010, census2020, census2024, etc.)
        # This supports any census year returned by the API
        from dataclasses import fields as dataclass_fields
        valid_field_names = {f.name for f in dataclass_fields(GeocodioFields)}

        census_fields = {}
        for key in fields_data:
            if key.startswith("census") and key[6:].isdigit():  # e.g., "census2024"
                # Only include if it's a defined field in GeocodioFields
                if key in valid_field_names:
                    census_fields[key] = CensusData.from_api(fields_data[key])

        acs = (
            ACSSurveyData.from_api(fields_data["acs"])
            if "acs" in fields_data else None
        )

        demographics = (
            Demographics.from_api(fields_data["acs-demographics"])
            if "acs-demographics" in fields_data else None
        )

        economics = (
            Economics.from_api(fields_data["acs-economics"])
            if "acs-economics" in fields_data else None
        )

        families = (
            Families.from_api(fields_data["acs-families"])
            if "acs-families" in fields_data else None
        )

        housing = (
            Housing.from_api(fields_data["acs-housing"])
            if "acs-housing" in fields_data else None
        )

        social = (
            Social.from_api(fields_data["acs-social"])
            if "acs-social" in fields_data else None
        )

        # Canadian fields
        riding = (
            FederalRiding.from_api(fields_data["riding"])
            if "riding" in fields_data else None
        )

        provriding = (
            ProvincialRiding.from_api(fields_data["provriding"])
            if "provriding" in fields_data else None
        )

        provriding_next = (
            ProvincialRiding.from_api(fields_data["provriding-next"])
            if "provriding-next" in fields_data else None
        )

        statcan = (
            StatisticsCanadaData.from_api(fields_data["statcan"])
            if "statcan" in fields_data else None
        )

        return GeocodioFields(
            timezone=timezone,
            congressional_districts=congressional_districts,
            state_legislative_districts=state_legislative_districts,
            state_legislative_districts_next=state_legislative_districts_next,
            school_districts=school_districts,
            acs=acs,
            demographics=demographics,
            economics=economics,
            families=families,
            housing=housing,
            social=social,
            riding=riding,
            provriding=provriding,
            provriding_next=provriding_next,
            statcan=statcan,
            **census_fields,  # Dynamically include all census year fields
        )

    # @TODO add a "keep_trying" parameter to download() to keep trying until the list is processed.
    def download(self, list_id: str, filename: Optional[str] = None) -> str | bytes:
        """
        This will generate/retrieve the fully geocoded list as a CSV file, and either return the content as bytes
        or save the file to disk with the provided filename.

        Args:
            list_id: The ID of the list to download.
            filename: filename to assign to the file (optional). If provided, the content will be saved to this file.

        Returns:
            The content of the file as a Bytes object, or the full file path string if filename is provided.
        Raises:
            GeocodioServerError if the list is still processing or another error occurs.
        """
        params = {}
        endpoint = f"{self.BASE_PATH}/lists/{list_id}/download"

        response: httpx.Response = self._request("GET", endpoint, params, timeout=self.list_timeout)
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                error = response.json()
                logger.error(f"Error downloading list {list_id}: {error}")
                raise GeocodioServerError(error.get("message", "Failed to download list."))
            except Exception as e:
                logger.error(f"Failed to parse error message from response: {response.text}", exc_info=True)
                raise GeocodioServerError("Failed to download list and could not parse error message.") from e
        else:
            if filename:
                # If a filename is provided, save the response content to a file of that name=
                # get the absolute path of the file
                if not os.path.isabs(filename):
                    filename = os.path.abspath(filename)
                # Ensure the directory exists
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                logger.debug(f"Saving list {list_id} to {filename}")

                # do not check if the file exists, just overwrite it
                if os.path.exists(filename):
                    logger.debug(f"File {filename} already exists; it will be overwritten.")

                try:
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    logger.info(f"List {list_id} downloaded and saved to {filename}")
                    return filename  # Return the full path of the saved file
                except IOError as e:
                    logger.error(f"Failed to save list {list_id} to {filename}: {e}", exc_info=True)
                    raise GeocodioServerError(f"Failed to save list: {e}")
            else:  # return the bytes content directly
                return response.content
