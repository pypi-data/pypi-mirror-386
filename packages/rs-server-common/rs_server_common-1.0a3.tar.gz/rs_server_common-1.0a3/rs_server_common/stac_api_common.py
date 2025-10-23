# Copyright 2024 CS Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-many-lines

"""Module to share common functionalities for validating / creating stac items"""
import asyncio
import copy
import json
import os
import re
import urllib.parse
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime as dt
from functools import lru_cache
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Literal,
    Optional,
    Self,
    TypeAlias,
)

import stac_pydantic
import yaml
from fastapi import HTTPException
from fastapi import Path as FPath
from fastapi import Query, Request, status
from fastapi.datastructures import QueryParams
from pydantic import BaseModel, Field, ValidationError
from rs_server_common import settings
from rs_server_common.rspy_models import Item, ItemCollection
from rs_server_common.stac_cql2 import temporal_op_query, temporal_operations
from rs_server_common.utils import utils2
from rs_server_common.utils.logging import Logging
from rs_server_common.utils.utils import (
    extract_eo_product,
    odata_to_stac,
    run_in_threads,
    validate_inputs_format,
)
from stac_fastapi.api.models import Limit
from stac_fastapi.extensions.core.filter.request import FilterLang
from stac_fastapi.types.search import str2bbox
from stac_pydantic.shared import BBox

# pylint: disable=attribute-defined-outside-init
logger = Logging.default(__name__)


def log_http_exception(*args, **kwargs) -> HTTPException:
    """Log error and return an HTTP exception to be raised by the caller"""
    return utils2.log_http_exception(logger, *args, **kwargs)


DEFAULT_STAC_VERSION = "1.0.0"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SEARCH_LIMIT = 10000  # max number of products returned by eodag

DATE_INTERVAL_KEYS = ["PublicationDate"]
COMMA_SEPARATED_LISTS_KEYS = ["platformSerialIdentifier", "platformShortName", "Satellite", "productType", "SessionId"]

# Type hints
CollectionType = Annotated[str, FPath(description="Collection ID", max_length=100)]
BBoxType = Annotated[
    Optional[str],
    Query(description="Bounding box (geospatial footprint or extent, four or six comma-separated numbers)."),
]
DateTimeType = Annotated[
    Optional[str],
    Query(description='Time interval e.g "2024-01-01T00:00:00Z/2024-01-02T23:59:59Z"'),
]
FilterType = Annotated[
    Optional[str],
    Query(
        alias="filter",
        description="""A CQL2 filter expression for filtering items.\n
Supports `CQL2` as defined in https://docs.ogc.org/is/21-065r2/21-065r2.html""",
        json_schema_extra={
            "example": "id='LC08_L1TP_060247_20180905_20180912_01_T1_L1TP' AND collection='landsat8_l1tp'",
        },
    ),
]
FilterLangType = Annotated[
    Optional[FilterLang],
    Query(
        alias="filter-lang",
        description="The CQL2 filter encoding that the 'filter' value uses.",
    ),
]
SortByType = Annotated[Optional[str], Query(description="Sort by +/-fieldName (ascending/descending)")]
LimitType = Annotated[
    Optional[Limit],
    Query(
        description="Limits the number of results that are included in each page of the response "
        "(between 1000 and 10_000)",
    ),
]
PageType = Annotated[Optional[str], Query(description="Page number to be displayed, defaults to first one.")]
ServiceRole: TypeAlias = Literal["auxip", "cadip", "prip"]


class Queryables(BaseModel):
    """
    BaseModel used to describe queryable holder.
    See: site-packages/pypgstac/migrations/pgstac.0.9.8.sql
    """

    id: str = Field("", alias="$id")
    type: str = Field("object")
    title: str = Field("STAC Queryables.")
    schema_url: str = Field("http://json-schema.org/draft-07/schema#", alias="$schema")  # type: ignore
    properties: dict[str, Any] = Field({})

    class Config:  # pylint: disable=too-few-public-methods
        """Used to overwrite BaseModel config and display aliases in model_dump."""

        populate_by_name = True


class QueryableField(BaseModel):
    """BaseModel used to describe queryable item."""

    type: str
    title: str
    format: str | None = None
    pattern: str | None = None
    description: str | None = None
    enum: list[str] | None = None


@dataclass
class MockPgstac(ABC):  # pylint: disable=too-many-instance-attributes
    """
    Mock a pgstac database for the services (auxip, cadip, ...) that use stac_fastapi but don't need a database.
    """

    # Set by stac-fastapi
    request: Request = Request(scope={"type": "http"})
    readwrite: Literal["r", "w"] | None = None

    service: ServiceRole | None = None

    # auxip or cadip function
    all_collections: Callable[[], list[dict]] = lambda: []
    select_config: Callable[[str], dict] = lambda _id: {}
    stac_to_odata: Callable[[dict], dict] = lambda _d: {}
    map_mission: Callable[[Any | None, Any | None], str | tuple | None] = lambda _p, _c: None
    temporal_mapping: dict[str, str] | None = None

    # Is the service auxip or cadip ?
    auxip: bool = False
    cadip: bool = False
    prip: bool = False

    # Current page
    page: int = 1

    # Number of results per page
    limit: int = 0

    def __post_init__(self):
        self.auxip = self.service == "auxip"
        self.cadip = self.service == "cadip"
        self.prip = self.service == "prip"

    @classmethod
    @asynccontextmanager
    async def get_connection(cls, request: Request, readwrite: Literal["r", "w"] = "r") -> AsyncIterator[Self]:
        """Return a class instance"""
        yield cls(request, readwrite)

    @dataclass
    class ReadPool:
        """Used to mock the readpool function."""

        # Outer MockPgstac class type
        outer_cls: type["MockPgstac"]

        @asynccontextmanager
        async def acquire(self) -> AsyncIterator["MockPgstac"]:
            """Return an outer class instance"""
            yield self.outer_cls()

    @classmethod
    def readpool(cls):
        """Mock the readpool function."""
        return cls.ReadPool(cls)

    # pylint: disable=too-many-branches
    def get_queryables(
        self,
        collection_id: str | None = None,
    ) -> dict[str, QueryableField]:
        """Function to list all available queryables for CADIP session search."""

        # Note: the queryables contain stac keys
        queryables = {}
        # If the collection has a product type field hard-coded with a single value,
        # the user cannot query on it.
        # TODO: factorize this code for all query parameters.
        if self.auxip:
            can_query = True
            if collection_id and (collection := self.select_config(collection_id)):
                value = collection.get("query", {}).get("productType", "")
                if value and ("," not in value):
                    can_query = False
            if can_query:
                for queryable_name, queryable_data in get_adgs_queryables().items():
                    queryables.update({queryable_name: QueryableField(**queryable_data)})

            return queryables

        if self.prip:
            for queryable_name, queryable_data in get_prip_queryables().items():
                queryables.update({queryable_name: QueryableField(**queryable_data)})
            return queryables

        # Idem for satellite or platform
        can_query = True
        if collection_id and (collection := self.select_config(collection_id)):
            query_dict = collection.get("query") or {}
            for field in "platformSerialIdentifier", "platformShortName", "Satellite":
                value = query_dict.get(field) or ""
                if value and ("," not in value):
                    can_query = False
                    break

        if can_query:
            for queryable_name, queryable_data in get_cadip_queryables().items():
                queryables.update({queryable_name: QueryableField(**queryable_data)})

        return queryables

    async def fetchval(self, query, *args, column=0, timeout=None):  # pylint: disable=unused-argument
        """Run a query and return a value in the first row.

        Args:
            query (str): Query text.
            args: Query arguments.
            column (int): Numeric index within the record of the value to return (defaults to 0).
            timeout (timeout): Optional timeout value in seconds. If not specified, defaults to the value of
            ``command_timeout`` argument to the ``Connection`` instance constructor.

        Returns: The value of the specified column of the first record,
        or None if no records were returned by the query.
        """
        query = query.strip()

        # From stac_fastapi.pgstac.core.CoreCrudClient::all_collections
        if query == "SELECT * FROM all_collections();":
            return filter_allowed_collections(self.all_collections(), self.service, self.request)

        # From stac_fastapi.pgstac.core.CoreCrudClient::get_collection
        if query == "SELECT * FROM get_collection($1::text);":

            # Find the collection which id == the input collection_id
            collection_id = args[0]
            collection = self.select_config(collection_id)
            if not collection:
                raise log_http_exception(
                    status.HTTP_404_NOT_FOUND,
                    f"Unknown {self.service} collection: {collection_id!r}",
                )

            # Convert into stac object (to ensure validity) then back to dict
            collection.setdefault("stac_version", DEFAULT_STAC_VERSION)
            return create_collection(collection).model_dump()

        # from stac_fastapi.pgstac.extensions.filter.FiltersClient::get_queryables
        # args[0] contains the collection_id, if any.
        if query == "SELECT * FROM get_queryables($1::text);":
            return Queryables(properties=self.get_queryables(args[0] if args else None)).model_dump(  # type: ignore
                by_alias=True,
            )

        # from stac_fastapi.pgstac.core.CoreCrudClient::_search_base
        if query == "SELECT * FROM search($1::text::jsonb);":
            params = json.loads(args[0]) if args else {}
            return await self.search(params)

        raise log_http_exception(status.HTTP_501_NOT_IMPLEMENTED, f"Not implemented PostgreSQL query: {query!r}")

    async def search(self, params: dict) -> dict[str, Any]:
        """
        Search products using filters coming from the STAC FastAPI PgSTAC /search endpoints.
        """
        if self.request is None:
            raise AssertionError("Request should be defined")

        # Read the POST request json body, if any.
        # Note: this must be done from an async function.
        try:
            post_json_body = await self.request.json()
        except json.JSONDecodeError:
            post_json_body = {}

        # Do the search in a synchronized thread so we don't block the main thread,
        # see: https://stackoverflow.com/a/71517830
        return await asyncio.to_thread(self.sync_search, params, post_json_body)

    def sync_search(  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        self,
        params: dict,
        post_json_body: dict,
    ) -> dict[str, Any]:
        """Synchronized search."""

        logger.debug(f"sync_search with params: {params}")

        #
        # Step 1: read input params

        stac_params: dict[str, Any] = {}

        def format_dict(field: dict):
            """Used for error handling."""
            return json.dumps(field, indent=0).replace("\n", "").replace('"', "'")

        # Read the pagination query parameters from the GET or POST request URL.
        # They can be set either as standard parameters or as "token" parameters.
        # The token values have higher priority.
        for as_token in [False, True]:
            query_params: dict | QueryParams = self.request.query_params
            if as_token:
                token = query_params.get("token")  # for GET
                if not token:
                    try:
                        token = post_json_body.get("token")  # for POST
                    except json.JSONDecodeError:
                        pass
                if not token:
                    continue

                # Remove the prev: or next: prefix and parse the string
                token = token.removeprefix("prev:").removeprefix("next:")
                query_params = urllib.parse.parse_qs(token)

            # Merge pagination parameters into input params.
            # Convert lists with one element into this single value.
            for key, values in query_params.items():
                if key not in ("limit", "page", "sortby"):
                    continue
                if isinstance(values, list) and (len(values) == 1):
                    params[key] = values[0]
                else:
                    params[key] = values

        # Collections to search
        collection_ids: list[str] = [collection.strip() for collection in params.pop("collections", [])]

        # IDs to search
        ids = params.pop("ids", None)

        # The cadip session ids are set in parameter or in the request state
        # by the /collections/{collection_id}/items/{session_id} endpoint
        if self.cadip:
            if not ids:
                try:
                    ids = self.request.state.session_id
                except AttributeError:
                    pass

        # Save the auxip product names or cadip session ids
        if isinstance(ids, list):
            stac_params["id"] = [id.strip() for id in ids]
        elif isinstance(ids, str):
            stac_params["id"] = ids.strip()  # type: ignore

        # Page number
        page = params.pop("page", None)
        if page:
            try:
                self.page = int(page)
                if self.page < 1:
                    raise ValueError
            except ValueError as exc:
                raise log_http_exception(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Invalid page value: {page!r}",
                ) from exc

        # Number of results per page
        limit = params.pop("limit", None)
        if limit:
            try:
                self.limit = int(limit)
                if self.limit < 1:
                    raise ValueError
            except ValueError as exc:
                raise log_http_exception(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Invalid limit value: {limit!r}",
                ) from exc

        # Default limit value
        else:
            self.limit = 1000

        # Sort results
        sortby_param = params.pop("sortby", None)
        if isinstance(sortby_param, str):
            self.sortby = sortby_param
        elif isinstance(sortby_param, list):
            if len(sortby_param) > 1:
                raise log_http_exception(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    f"Only one 'sortby' search parameter is allowed: {sortby_param!r}",
                )
            if sortby_param:
                sortby_dict = sortby_param[0]
                self.sortby = "+" if sortby_dict["direction"] == "asc" else "-"
                self.sortby += sortby_dict["field"]

        # datetime interval = PublicationDate
        datetime = params.pop("datetime", None)
        if datetime:
            try:
                validate_inputs_format(datetime, raise_errors=True)
                if self.auxip:
                    stac_params["created"] = datetime
                elif self.cadip or self.prip:
                    stac_params["published"] = datetime
            except HTTPException as exception:
                raise log_http_exception(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    f"Invalid datetime interval: {datetime!r}. "
                    "Expected format is either: 'YYYY-MM-DDThh:mm:ssZ', 'YYYY-MM-DDThh:mm:ssZ/YYYY-MM-DDThh:mm:ssZ', "
                    "'YYYY-MM-DDThh:mm:ssZ/..' or '../YYYY-MM-DDThh:mm:ssZ'",
                ) from exception

        #
        # Read query and/or CQL filter

        # Only the queryable properties are allowed
        allowed_properties = sorted(self.get_queryables().keys())

        def read_property(prop: str, value: Any):
            """Read a query or CQL filter property"""
            nonlocal stac_params  # noqa: F824
            if prop not in allowed_properties:
                raise log_http_exception(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    f"Invalid query or CQL property: {prop!r}, " f"allowed properties are: {allowed_properties}",
                )
            if isinstance(value, dict):
                value = value.get("property")
            if isinstance(value, str):
                value = value.strip()
            stac_params[prop] = value

        # helper: GeoJSON -> WKT (used by POST 'intersects' and CQL2 JSON)
        def _geojson_to_wkt(geom: dict) -> str:
            # supports Polygon
            t = geom.get("type")
            if str(t).lower() != "polygon":
                raise log_http_exception(422, f"Unsupported geometry type {t}. Only Polygon is supported (SRID=4326).")
            ring = geom["coordinates"][0]  # type: ignore[index]
            if ring and ring[0] != ring[-1]:
                ring = ring + [ring[0]]
            return "POLYGON((" + ", ".join(f"{x} {y}" for x, y in ring) + "))"

        def read_cql(filt: dict):
            """Use a recursive function to read all CQL filter levels"""
            if not filt:
                return
            op: str = filt.get("op")  # type: ignore
            args = filt.get("args", [])

            # ADD: CQL2-JSON op: {"op":"intersects","args":[{"property":"geometry"}, <geom>]}
            if op and op.lower() == "intersects":
                if len(args) != 2:
                    raise log_http_exception(
                        status.HTTP_422_UNPROCESSABLE_CONTENT,
                        f"Invalid intersects: {format_dict(filt)}",
                    )
                geom = args[1]
                if isinstance(geom, dict):
                    if not geom.get("type") or geom.get("coordinates") is None:
                        raise log_http_exception(422, "Geometry must include 'type' and 'coordinates'.")
                    stac_params["intersects"] = _geojson_to_wkt(geom)
                else:
                    stac_params["intersects"] = str(geom).strip("'\"")
                return

            # Read a single property
            if op == "=":
                if (len(args) != 2) or not (prop := args[0].get("property")):
                    raise log_http_exception(
                        status.HTTP_422_UNPROCESSABLE_CONTENT,
                        f"Invalid CQL2 filter: {format_dict(filt)}",
                    )
                value = args[1]
                read_property(prop, value)
                return

            # Read temporal operators
            if op in temporal_operations:
                temporal_query: str = temporal_op_query(op, args, self.temporal_mapping)
                logger.debug(f"Temporal operator {op} with args {args} -> {temporal_query}")
                stac_params[op] = temporal_query
                return

            # Else we are reading several properties
            if op != "and":
                raise log_http_exception(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    f"Invalid CQL2 filter, only '=', 'and' and temporal operators are allowed, got '{op}': {format_dict(filt)}",  # noqa: E501 # pylint: disable=line-too-long
                )
            for sub_filter in args:
                read_cql(sub_filter)

        def read_query(query_arg: str | None):
            """Used to read query parameter cql2-text filter."""
            if not query_arg:
                return
            # If there are more filters defined and joined by AND keyword, process each one and update stac_params.
            if re.search(r"\bAND\b", query_arg, re.IGNORECASE):  # only AND for now.
                conditions = [c.strip() for c in re.split(r"\bAND\b", query_arg, flags=re.IGNORECASE)]
                for condition in conditions:
                    read_query(condition)
                return

            # Handle '='
            if "=" in query_arg:
                kv = query_arg.split("=")
                # Extract prop and check if it's in the queryables.
                if (prop := kv[0].strip()) not in allowed_properties:
                    raise log_http_exception(
                        status.HTTP_422_UNPROCESSABLE_CONTENT,
                        f"Invalid query filter property: {prop!r}, allowed properties are: {allowed_properties}",
                    )
                value = str(kv[1]).strip("'\"")
                check_input_type(self.get_queryables(), prop, value)
                # Update stac params
                stac_params[prop] = value  # type: ignore
            # Handle CQL2 temporal operators
            elif match := re.search(
                r"\b(" + "|".join(map(re.escape, temporal_operations.keys())) + r")\b",
                query_arg,
                re.IGNORECASE,
            ):
                op = match.group(1).lower()
                logger.debug(f"Temporal operator detected: {op} -> {stac_params[op]}")
            else:
                raise log_http_exception(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    "Invalid query filter, only '=' and temporal operators are allowed, got: " + query_arg,
                )

        read_cql(params.pop("filter", {}))
        read_query(self.request.query_params.get("filter"))
        # Read the query
        query = params.pop("query", {})
        for prop, operator in query.items():
            if (len(operator) != 1) or not (value := operator.get("eq")):
                raise log_http_exception(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    f"Invalid query: {{{prop!r}: {format_dict(operator)}}}"
                    ", only {'<property>': {'eq': <value>}} is allowed",
                )
            read_property(prop, value)

        # map stac platform/constellation values to odata values...
        mission = self.map_mission(stac_params.get("platform"), stac_params.get("constellation"))
        # ... still saved with stac keys for now
        if self.auxip:
            stac_params["constellation"], stac_params["platform"] = mission  # type: ignore
        if self.cadip:
            stac_params["platform"] = mission  # type: ignore

        # Discard these search parameters
        params.pop("bbox", None)
        params.pop("conf", None)
        params.pop("filter-lang", None)

        # Discard the "fields" parameter only if its "include" and "exclude" properties are empty
        fields = params.get("fields", {})
        if not fields.get("include") and not fields.get("exclude"):
            params.pop("fields", None)

        # If search parameters remain, they are not implemented
        if params:
            raise log_http_exception(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Unimplemented search parameters: {format_dict(params)}",
            )

        #
        # Step 2: do the search

        # Convert search params from STAC keys to OData keys
        odata_params: dict = self.stac_to_odata(stac_params)
        logger.debug(f"STAC/OData parameters mapping: {stac_params} => {odata_params}")

        # Only keep the authorized collections
        allowed: list[dict] = filter_allowed_collections(self.all_collections(), self.service, self.request)
        allowed_ids: set[str] = {collection["id"] for collection in allowed}
        all_results: list[Sequence[Item] | Exception] = (
            self.search_collections_by_station(list(allowed_ids.intersection(collection_ids)), odata_params, True)
            if collection_ids
            else self.search_collections_by_station(list(allowed_ids), odata_params, False)
        )

        # Return results as a dict
        return self.build_response_payload(self.aggregate_items_from_results(all_results))

    def search_collections_by_station(
        self,
        collection_ids: list[str],
        odata_params: dict,
        aggregate_search_params: bool = True,
    ) -> list[Sequence[Item] | Exception]:
        """
        Performs a search for items across multiple stations, grouped by their collection configurations.

        This method groups collections by their associated station, optionally merges and aggregates
        OData search parameters per station, and executes the searches in parallel threads.
        If multiple collections belong to the same station, and `aggregate_search_params` is True,
        their queries are merged to reduce the number of calls.

        Args:
            collection_ids (list[str]): List of collection identifiers to search within.
            odata_params (dict): User-defined OData search parameters to apply to all stations.
            aggregate_search_params (bool, optional): If True, merge search parameters for collections
                of the same station. Defaults to True.

        Returns:
            list[Sequence[Item] | Exception]: A list of either successful item results or raised exceptions,
            one per station.
        """
        # Group collections by station
        collections_by_station: dict[str, list[dict]] = defaultdict(list)
        for collection in (self.select_config(collection_id) for collection_id in collection_ids):
            collections_by_station[collection["station"]].append(collection)

        odata_params_by_station: dict[str, dict] = {}
        for station, station_collections in collections_by_station.items():
            if aggregate_search_params:
                # Aggregates all search params for this station to make a single call
                odata_merged = odata_params.copy()
                empty_selection = False
                for collection in station_collections:
                    # Some OData search params are hardcoded in the collection configuration
                    odata_hardcoded = collection.get("query") or {}

                    # Merge the user input params with the hardcoded params (which have higher priority)
                    odata_merged, empty_selection = self.merge_odata_params(odata_hardcoded, odata_merged)
                    if empty_selection:
                        logger.warning("Key conflict resolution lead to empty selection, skipping search to {station}")
                        break
                if not empty_selection:
                    odata_params_by_station[station] = odata_merged
            else:
                # Do the same search for all stations
                odata_params_by_station[station] = odata_params.copy()

        # Search all stations in parallel threads
        return run_in_threads(
            self.perform_search_in_station,
            (
                (
                    station,
                    station_odata_params,
                    lambda odata_entity, station=station: self.determine_collection(
                        odata_entity,
                        collections_by_station[station],
                    ),
                    self.filter_items_without_collection,
                )
                for station, station_odata_params in odata_params_by_station.items()
            ),
        )

    def determine_collection(self, odata_entity: dict, collections: list[dict]) -> str | None:
        """
        Determines the matching collection ID for a given OData entity.

        This method iterates over a list of collection configurations and checks
        which one the OData entity satisfies based on the collection's query criteria.
        Returns the first matching collection ID or None if no match is found.

        Args:
            odata_entity (dict): The OData entity to evaluate.
            collections (list[dict]): A list of collection configurations,
            each potentially containing query criteria.

        Returns:
            str | None: The ID of the first matching collection, or None if no match is found.
        """
        for collection in collections:
            if self.is_entity_matching_all_criteria(odata_entity, collection.get("query") or {}):
                return collection["id"]
        return None

    def is_entity_matching_all_criteria(self, odata_entity: dict, query: dict) -> bool:
        """
        Evaluates whether an OData entity matches all criteria defined in a query.

        The query may contain various types of filters including:
        - Fixed dates or date intervals (keys in DATE_INTERVAL_KEYS)
        - Comma-separated list values (keys in COMMA_SEPARATED_LISTS_KEYS)
        - Exact value matches

        The function logs whether each criterion was matched or not, and returns False
        as soon as a mismatch is detected. If all criteria are matched, it returns True.

        Args:
            odata_entity (dict): The OData entity to validate.
            query (dict): A dictionary of filter criteria.

        Returns:
            bool: True if all criteria are matched by the entity, False otherwise.
        """

        def match(odata_entity: dict, crit_type: str, key: str, value: str):
            logger.debug(f"Entity {odata_entity} matches {crit_type} criteria {key}={value}")

        def nomatch(odata_entity: dict, crit_type: str, key: str, value: str):
            if os.getenv("PYTHONDEBUG", "False").lower() in ("1", "true", "yes"):
                logger.debug(f"Entity {odata_entity} does not match {crit_type} criteria {key}={value}")
            return False

        for crit_key, crit_val in query.items():
            if crit_key not in ("top", "skip", "orderby"):
                value = odata_entity.get(crit_key, None)
                if crit_key in DATE_INTERVAL_KEYS:
                    date = dt.fromisoformat(value) if value else None
                    fixed, start, stop = validate_inputs_format(crit_val, raise_errors=False)
                    if fixed and date != fixed:
                        return nomatch(odata_entity, "fixed date", crit_key, crit_val)
                    if start and stop and not start <= date <= stop:
                        return nomatch(odata_entity, "closed interval", crit_key, crit_val)
                    if (start and date < start) or (stop and date > stop):
                        return nomatch(odata_entity, "open interval", crit_key, crit_val)
                    match(odata_entity, "date", crit_key, crit_val)
                elif crit_key in COMMA_SEPARATED_LISTS_KEYS:
                    iterable = crit_val if isinstance(crit_val, list) else crit_val.split(",")
                    if value is None or value.strip().lower() not in {v.strip().lower() for v in iterable}:
                        return nomatch(odata_entity, "list", crit_key, crit_val)
                    match(odata_entity, "list", crit_key, crit_val)
                elif crit_val != odata_entity.get(crit_key, None):
                    return nomatch(odata_entity, "generic", crit_key, crit_val)
                else:
                    match(odata_entity, "generic", crit_key, crit_val)
        return True

    def filter_items_without_collection(self, items: list[Item]) -> None:
        """
        Removes items from the list that do not have a 'collection' field.

        Args:
            items (list[Item]): The list of items to filter (modified in place).
        """

        def has_collection(item):
            if not item.collection:
                logger.warning(f"Filter item without collection: {item}")
                return False
            return True

        items[:] = [item for item in items if has_collection(item)]

    def aggregate_items_from_results(self, all_results) -> ItemCollection:
        """
        Aggregates items from a list of results, filtering out exceptions and ensuring unique items by ID.

        If all results are exceptions (i.e., no valid items), the first exception is raised.

        Args:
            all_results (Iterable[Sequence[Item] | Exception]): A list of either sequences of items or exceptions.

        Returns:
            ItemCollection: A collection containing all unique items combined into a STAC ItemCollection.

        Raises:
            Exception: The first exception encountered if no valid items are present.
        """
        # Get items and exceptions from result
        all_items = {}
        all_exceptions = []
        for result in all_results:
            if isinstance(result, Exception):
                all_exceptions.append(result)
            else:  # item list
                for item in result:
                    all_items[item.id] = item

        # Raise first exception if we have no items and at least one exception
        if (not all_items) and all_exceptions:
            raise all_exceptions[0]

        # Return results as a dict
        return ItemCollection(features=list(all_items.values()), type="FeatureCollection")

    def build_response_payload(self, data: ItemCollection) -> dict[str, Any]:
        """
        Builds the search response payload by handling pagination and CADIP asset processing.

        This method adapts the response structure based on the request path (e.g., `/search`)
        and applies additional processing for CADIP-specific data when needed.

        Args:
            data (ItemCollection): The item collection returned from aggregate_items_from_results.

        Returns:
            dict[str, Any]: A dictionary-formatted payload ready for response, potentially including pagination links
            and enriched asset information for CADIP sessions.
        """
        if "/search" in self.request.url.path:
            # Do the custom pagination only for search endpoints, for others let eodag handle on station side.
            dict_data: dict[str, Any] = self.paginate(data)
        else:
            dict_data = data.model_dump()

        # In cadip, we retrieved the sessions data.
        # We need to fill their assets with the session files data.
        if self.cadip:
            dict_data = self.process_files(dict_data)

        # Handle pagination links.
        if len(dict_data["features"]) == self.limit:
            # Create next page if the current one reaches limit
            dict_data["next"] = f"page={self.page + 1}"
        if self.page > 1:
            dict_data["prev"] = f"page={self.page - 1}"

        return dict_data

    def paginate(self, item_collection: ItemCollection) -> dict[str, Any]:
        """Method used to apply pagination options after /search result were aggregated."""

        paginated_item_collection: ItemCollection = sort_feature_collection(item_collection, self.sortby)
        return ItemCollection(
            features=paginated_item_collection.features[
                self.limit * (self.page - 1) : self.limit * self.page  # noqa: E203
            ],
            type=paginated_item_collection.type,
        ).model_dump()

    def merge_odata_params(self, odata_hardcoded: dict, odata_params: dict) -> tuple[dict, bool]:
        """
        Merges hardcoded and user-provided OData parameters with conflict resolution logic.

        Hardcoded parameters take precedence in the merge. If a parameter exists in both sources,
        conflicts are resolved based on the parameter type:
        - For date intervals (e.g., "PublicationDate"), the intersection is computed.
        - For comma-separated lists (e.g., "platformShortName", "productType"), the common values are retained.

        Args:
            odata_hardcoded (dict): Hardcoded parameters defined in the collection configuration.
            odata_params (dict): OData parameters provided by the user.

        Returns:
            tuple[dict, bool]: A tuple containing the merged OData parameters and a boolean flag indicating
            whether the result of the merge leads to an empty selection (e.g., no intersecting values).
        """
        # Merge the user input params with the hardcoded params (which have higher priority)
        odata_merged = {**odata_params, **odata_hardcoded}
        empty_selection = False

        # Handle conflicts, i.e. for each key that is defined in both params
        for key in sorted(set(odata_params) & set(odata_hardcoded)):
            key_empty_selection = False
            # Date intervals
            if key in DATE_INTERVAL_KEYS:
                odata_merged[key], key_empty_selection = self.resolve_date_interval_conflict(
                    odata_params[key],
                    odata_hardcoded[key],
                )
            # Comma-separated lists
            elif key in COMMA_SEPARATED_LISTS_KEYS:
                odata_merged[key], key_empty_selection = self.resolve_comma_separated_list_conflict(
                    odata_params[key],
                    odata_hardcoded[key],
                )
            else:
                logger.warning(f"No conflict resolution performed for key {key}")
            if key_empty_selection:
                empty_selection = True

        return odata_merged, empty_selection

    def resolve_date_interval_conflict(self, value1: str, value2: str) -> tuple[str, bool]:
        """
        Resolves a conflict between two date interval strings by computing their intersection.

        Args:
            value1 (str): The first date interval in ISO 8601 format.
            value2 (str): The second date interval in ISO 8601 format.

        Returns:
            tuple[str, bool]: A tuple containing the intersected date interval as a string,
                and a boolean indicating whether the selection is empty (True if no overlap).
        """
        logger.debug(f"Resolving date interval conflict resolution between {value1} and {value2}")

        # Read both start and stop dates
        _, start1, stop1 = validate_inputs_format(value1, raise_errors=True)
        _, start2, stop2 = validate_inputs_format(value2, raise_errors=True)

        # Calculate the intersection
        start = max(start1, start2)
        stop = min(stop1, stop2)

        return f"{start.strftime(DATETIME_FORMAT)}/{stop.strftime(DATETIME_FORMAT)}", start >= stop

    def resolve_comma_separated_list_conflict(self, value1: Any, value2: Any) -> tuple[Any, bool]:
        """
        Resolves a conflict between two comma-separated lists by computing their intersection.

        Args:
            value1 (Any): The first list, or a comma-separated string representing it.
            value2 (Any): The second list, or a comma-separated string representing it.

        Returns:
            tuple[Any, bool]: A tuple containing the intersected list as a comma-separated string,
            and a boolean indicating whether the result is empty (True if no intersection).
        """
        logger.debug(f"Resolving comma-separated list conflict resolution between {value1} and {value2}")

        intersection = None

        # If one is empty or None, this means "keep everything".
        # So keep the intersection = the other list.
        if not value1:
            intersection = value2
        elif not value2:
            intersection = value1

        # Else, split by comma and keep the intersection.
        # If no intersection, then the selection is empty.
        else:
            for i, value in enumerate((value1, value2)):
                iterable = value if isinstance(value, list) else value.split(",")
                s = {v.strip() for v in iterable}
                intersection = intersection.intersection(s) if i else s  # type: ignore
            intersection = ", ".join(intersection) if intersection else None
            logger.debug(f"comma-separated list conflict resolution result: {intersection}")

        return intersection, not intersection

    def perform_search_in_station(
        self,
        station: str,
        odata_params: dict,
        collection_provider: Callable[[dict], str | None],
        postprocess: Callable[[list[Item]], None],
    ) -> list[Item]:
        """
        Performs a paginated search for items from a given station.

        This method handles pagination automatically by fetching subsequent pages
        if the number of results equals the search limit.
        Applies a postprocessing function to the final list of items before returning.

        Args:
            station (str): The station to search in.
            odata_params (dict): The OData query parameters to use for filtering the results.
            collection_provider (Callable[[dict], str | None]): Function that determines STAC collection
                                                                for a given OData entity
            postprocess (Callable[[list[Item]], None]): Function to modify the list of items.

        Returns:
            Sequence[Item]: A list of STAC items matching the search criteria, postprocessed.
        """
        # limit and page values used by the search function
        search_limit = self.limit
        search_page = self.page

        # Don't forward limit value for /search endpoints
        # just use maximum to gather all possible results, page is always 1
        if "/search" in self.request.url.path:
            search_limit = self.limit * self.page
            search_page = 1

        # Do the search for this station
        logger.debug(f"Searching to {station} station with OData parameters {odata_params}")
        features = self.process_search(station, odata_params, collection_provider, search_limit, search_page).features

        # If search return maximum number of elements, increase page and process next elements
        if len(features) == SEARCH_LIMIT:
            while True:
                search_page += 1
                next_features = self.process_search(
                    station,
                    odata_params,
                    collection_provider,
                    search_limit,
                    search_page,
                ).features
                features.extend(next_features)  # type: ignore
                # Extend current features.
                # Break the loop when result is less the maximum possible, meaning there is no next page.
                if len(next_features) < SEARCH_LIMIT:
                    break
            search_page = 1

        logger.debug(f"Items found before post-processing: {len(features)}")
        postprocess(features)
        logger.debug(f"Items kept after post-processing: {len(features)}")
        return features

    @abstractmethod
    def process_search(
        self,
        station: str,
        odata_params: dict,
        collection_provider: Callable[[dict], str | None],
        limit: int,
        page: int,
    ) -> ItemCollection:
        """Do the search for the given collection and OData parameters."""

    def process_asset_search(
        self,
        station: str,
        session_features: list[Item],
    ):
        """
        Implemented only by cadip.
        Search cadip files for each input cadip session and their associated station.
        Update input session assets with their associated files.
        """
        raise NotImplementedError

    def process_files(self, empty_sessions_data: dict) -> dict:
        """
        Implemented only by cadip.
        Search cadip files for each input cadip session. Update the sessions data with their files data.
        """
        raise NotImplementedError


def create_collection(collection: dict) -> stac_pydantic.Collection:
    """Used to create stac_pydantic Model Collection based on given collection data."""
    try:
        return stac_pydantic.Collection(type="Collection", **collection)
    except ValidationError as exc:
        raise log_http_exception(
            detail=f"Unable to create stac_pydantic.Collection, {repr(exc.errors())}",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        ) from exc


def handle_exceptions(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator used to wrapp all endpoints that can raise KeyErrors / ValidationErrors
    while creating/validating items.
    """

    @contextmanager
    def wrapping_logic(*_args, **_kwargs):
        try:
            yield
        except KeyError as exc:
            logger.error(f"KeyError caught in {func.__name__}")
            raise log_http_exception(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Cannot create STAC Collection -> Missing {exc}",
            ) from exc
        except ValidationError as exc:
            logger.error(f"ValidationError caught in {func.__name__}")
            raise log_http_exception(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Parameters validation error: {exc}",
            ) from exc

    # Decorator for both sync and async functions
    return utils2.decorate_sync_async(wrapping_logic, func)


def filter_allowed_collections(all_collections: list[dict], role: ServiceRole | None, request: Request) -> list[dict]:
    """Filters collections based on user roles and permissions.

    This function returns only the collections that a user is allowed to read based on their
    assigned roles in Keycloak. If the application is running in local mode, all collections
    are returned without filtering.

    Parameters:
        all_collections (list[dict]): A list of all available collections, where each collection
                                       is represented as a dictionary.
        role (str): The role of the user requesting access to the collections, which is used to
                    build the required authorization key for filtering collections.
        request (Request): The request object, which contains user authentication roles
                           available through `request.state.auth_roles`.

    Returns:
        list[dict]: list of filtered collections that the user is allowed to access.
              The structure of the returned objects is as follows:
              - type (str): The type of the STAC object, which is always "Object".
              - links (list): A list of links associated with the STAC object (currently empty).
              - collections (list[dict]): A list of filtered collections, where each collection
                                           is a dictionary representation of a STAC collection.

    Logging:
        Debug-level logging is used to log the IDs of collections the user is allowed to
        access and the query parameters generated for each allowed collection. Errors during
        collection creation are also logged.

    Raises:
        HTTPException: If a collection configuration is incomplete or invalid, an
                       HTTPException is raised with status code 422. Other exceptions
                       are propagated as-is.
    """
    # No authentication: select all collections
    if settings.LOCAL_MODE:
        filtered_collections = all_collections

    else:
        # Read the user roles defined in KeyCloak
        try:
            auth_roles = request.state.auth_roles or []
        except AttributeError:
            auth_roles = []

        # Only keep the collections that are associated to a station that the user has access to
        filtered_collections = [
            collection for collection in all_collections if f"rs_{role}_{collection['station']}_read" in auth_roles
        ]

    logger.debug(f"User allowed collections: {[collection['id'] for collection in filtered_collections]}")

    # Foreach allowed collection, create links and append to response.
    stac_collections: list[dict] = []
    for config in filtered_collections:
        config.setdefault("stac_version", DEFAULT_STAC_VERSION)
        try:
            collection: stac_pydantic.Collection = create_collection(config)
            logger.info(f"Loaded STAC collection '{collection.id}'")
            stac_collections.append(collection.model_dump())

        # If a collection is incomplete in the configuration file, log the error and proceed
        except HTTPException as exception:
            if exception.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
                logger.error(exception)
            else:
                raise
    return stac_collections


@lru_cache
def get_cadip_queryables() -> dict:
    """Function used to read and interpret from cadip_queryables.yaml"""
    with open(Path(__file__).parent.parent / "config" / "cadip_queryables.yaml", encoding="utf-8") as cf:
        return yaml.safe_load(cf)


@lru_cache
def get_adgs_queryables() -> dict:
    """Function used to read and interpret from adgs_queryables.yaml"""
    with open(Path(__file__).parent.parent / "config" / "adgs_queryables.yaml", encoding="utf-8") as cf:
        return yaml.safe_load(cf)


@lru_cache
def get_prip_queryables() -> dict:
    """Function used to read and interpret from prip_queryables.yaml"""
    with open(Path(__file__).parent.parent / "config" / "prip_queryables.yaml", encoding="utf-8") as cf:
        return yaml.safe_load(cf)


def create_stac_collection(
    products: list[Any],
    feature_template: dict,
    stac_mapper: dict,
    collection_provider: Callable[[dict], str | None] | None = None,
) -> ItemCollection:
    """
    Creates a STAC feature collection based on a given template for a list of EOProducts.

    Args:
        products (List[EOProduct]): A list of EOProducts to create STAC features for.
        feature_template (dict): The template for generating STAC features.
        stac_mapper (dict): The mapping dictionary for converting EOProduct data to STAC properties.
        collection_provider (Callable[[dict], str | None]): optional function that determines STAC collection
                                                            for a given OData entity

    Returns:
        dict: The STAC feature collection containing features for each EOProduct.
    """
    items: list = []

    for product in products:
        product_data = extract_eo_product(product, stac_mapper)
        feature_tmp = odata_to_stac(copy.deepcopy(feature_template), product_data, stac_mapper, collection_provider)
        try:
            item = Item(**feature_tmp)
            item.stac_extensions = [str(se) for se in item.stac_extensions]  # type: ignore
            items.append(item)
        except ValidationError as e:
            logger.error(f"STAC validation error for {feature_tmp} (STAC conversion of {product_data}): {e}")
            continue
    return ItemCollection(features=items, type="FeatureCollection")


def sort_feature_collection(item_collection: ItemCollection, sortby: str) -> ItemCollection:
    """
    Sorts the features in the collection by a specified attribute.

    The sort order can be reversed by prepending the attribute name with a "-" (e.g., "-date").
    If the attribute is not found, it falls back to sorting by a default field.

    Args:
        item_collection (stac_pydantic.ItemCollection): The collection of items to sort.
        sortby (str): The attribute by which to sort. If prefixed with "-", the sort order is descending.

    Returns:
        stac_pydantic.ItemCollection: A new collection sorted by the specified attribute.
    """
    # Force default sorting even if the input is invalid, don't block the return collection because of sorting.
    sortby = sortby.strip("'\"")
    direction, attribute = sortby[:1], sortby[1:]

    # From STAC API Sort extension:
    # Implementers may choose to require fields in Item Properties to be prefixed with properties. or not,
    # or support use of both the prefixed and non-prefixed name, e.g., properties.datetime or datetime

    # Try to sort by 'properties' first, then fallback to the 'feature' itself
    def get_sort_key(item):
        # Check if the attribute exists in properties, else use item directly
        if hasattr(item.properties, attribute.replace("properties.", "")):
            return getattr(item.properties, attribute.replace("properties.", ""))
        if hasattr(item, attribute):
            return getattr(item, attribute)
        # Otherwise, check if the attribute exists in any asset
        for asset in item.assets.values():
            if hasattr(asset, attribute):
                return getattr(asset, attribute)
        raise AttributeError(f"Attribute '{attribute}' not found in item")

    # Sort the features
    try:
        sorted_items = sorted(item_collection.features, key=get_sort_key, reverse=direction == "-")
    except AttributeError as e:
        raise log_http_exception(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid attribute '{attribute}' for sorting: {str(e)},",
        ) from e
    return ItemCollection(features=sorted_items, type=item_collection.type)


def check_input_type(field_info, key, input_value):
    """Function to check query parameters types agains default queryables."""
    expected_type = field_info[key].type  # Get the expected type as a string

    # Map expected type to actual Python types
    type_mapping = {
        "string": lambda input: isinstance(input, str),
        "integer": lambda input: input.isdigit(),
        "bool": lambda input_value: input_value.lower() in [True, False, 1, 0, "true", "false", "1", "0"],
        "datetime": check_datetime_input,  # Adding support for datetime
    }

    if not type_mapping.get(expected_type)(input_value):  # type: ignore
        raise log_http_exception(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Invalid CQL2 filter value",
        )


def check_datetime_input(input_value: Any) -> bool:
    """Used to check if a parameter is a datetime-like string"""
    try:
        dt.fromisoformat(input_value)  # ISO 8601 format check
        return True
    except ValueError:
        return False


def check_bbox_input(input_value: str | None) -> BBox | None:
    """validate bbox for STAC API compliance"""
    if input_value:
        try:
            return str2bbox(input_value)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise log_http_exception(status.HTTP_400_BAD_REQUEST, str(e)) from e
    return None


def split_multiple_values(input_value: str) -> list[str] | str:
    """
    Splits a comma-separated string into a list of trimmed strings.

    If the input string contains commas, it is split on each comma and each resulting
    substring is stripped of leading and trailing whitespace. If no comma is found,
    the original string is returned unchanged.

    Args:
        input_value (str): The input string to process.

    Returns:
        list[str] | str: A list of trimmed strings if the input contains commas,
                         otherwise the original string.
    """
    return [s.strip() for s in input_value.split(",")] if "," in input_value else input_value
