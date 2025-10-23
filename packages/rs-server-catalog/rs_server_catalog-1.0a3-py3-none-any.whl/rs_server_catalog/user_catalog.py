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

# pylint: disable=C0302

"""A BaseHTTPMiddleware to handle the user multi catalog.

The stac-fastapi software doesn't handle multi catalog.
In the rs-server we need to handle user-based catalogs.

The rs-server uses only one catalog but the collections are prefixed by the user name.
The middleware is used to hide this mechanism.

The middleware:
* redirect the user-specific request to the common stac api endpoint
* modifies the request to add the user prefix in the collection name
* modifies the response to remove the user prefix in the collection name
* modifies the response to update the links.
"""

import copy
import getpass
import json
import os
import re
from typing import Any, cast
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import botocore
from fastapi import HTTPException
from pygeofilter.ast import Attribute, Equal, Like, Node
from pygeofilter.parsers.cql2_json import parse as parse_cql2_json
from pygeofilter.parsers.cql2_text import parse as parse_cql2_text
from rs_server_catalog import timestamps_extension
from rs_server_catalog.authentication_catalog import get_authorisation
from rs_server_catalog.landing_page import (
    add_prefix_link_landing_page,
    manage_landing_page,
)
from rs_server_catalog.user_handler import (
    adapt_links,
    adapt_object_links,
    add_user_prefix,
    filter_collections,
    get_user,
    reroute_url,
)
from rs_server_catalog.utils import (
    delete_s3_files,
    get_s3_filename_from_asset,
    get_s3_handler,
    get_temp_bucket_name,
    get_token_for_pagination,
    headers_minus_content_length,
    verify_existing_item_from_catalog,
)
from rs_server_common import settings as common_settings
from rs_server_common.authentication import oauth2
from rs_server_common.s3_storage_handler.s3_storage_config import (
    get_bucket_name_from_config,
)
from rs_server_common.s3_storage_handler.s3_storage_handler import (
    S3StorageHandler,
    TransferFromS3ToS3Config,
)
from rs_server_common.utils import utils2
from rs_server_common.utils.logging import Logging
from stac_fastapi.api.models import GeoJSONResponse
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.types.errors import NotFoundError
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_302_FOUND,
    HTTP_307_TEMPORARY_REDIRECT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from .user_handler import (
    CATALOG_COLLECTIONS,
    CATALOG_PREFIX,
    owner_id_and_collection_id,
)

PRESIGNED_URL_EXPIRATION_TIME = int(os.environ.get("RSPY_PRESIGNED_URL_EXPIRATION_TIME", "1800"))  # 30 minutes
DEFAULT_GEOM = {
    "type": "Polygon",
    "coordinates": [[[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]]],
}
DEFAULT_BBOX = (-180.0, -90.0, 180.0, 90.0)
QUERYABLES = "/queryables"
ALTERNATE_STRING = "alternate"
# pylint: disable=too-many-lines
logger = Logging.default(__name__)


def log_http_exception(*args, **kwargs) -> type[HTTPException]:
    """Log error and return an HTTP exception to be raised by the caller"""
    return utils2.log_http_exception(logger, *args, **kwargs)


class UserCatalog:  # pylint: disable=too-many-public-methods
    """The user catalog middleware handler."""

    client: CoreCrudClient

    def __init__(self, client: CoreCrudClient):
        """Constructor, called from the middleware"""
        # TODO: the s3_handler member should not exist anymore
        # it should be retrieved with utils.get_s3_handler when needed
        # To be checked later for a complete removal
        self.s3_handler: S3StorageHandler = None
        # end of TODO
        self.request_ids: dict[Any, Any] = {}
        self.client = client
        self.s3_files_to_be_deleted: list[str] = []

    def clear_catalog_bucket(self, content: dict):
        """Used to clear specific files from catalog bucket."""
        if not self.s3_handler:
            return
        for asset in content.get("assets", {}):
            # Retrieve bucket name from config using what's in content
            item_owner = content["properties"].get("owner", "*")
            item_collection = content.get("collection", "*").removeprefix(f"{item_owner}_")
            item_eopf_type = content["properties"].get("eopf:type", "*")
            bucket_name = get_bucket_name_from_config(item_owner, item_collection, item_eopf_type)
            # For catalog bucket, data is already stored into href field (from an asset)
            file_key = content["assets"][asset]["href"]
            if not int(os.environ.get("RSPY_LOCAL_CATALOG_MODE", 0)):  # don't delete files if we are in local mode
                self.s3_handler.delete_file_from_s3(bucket_name, file_key)

    async def get_item_from_collection(self, request: Request):
        """Get an item from the collection.

        Args:
            request (Request): The request object.

        Returns:
            Optional[Dict]: The item from the collection if found, else None.
        """
        item_id = self.request_ids["item_id"]
        collection_id = f"{self.request_ids['owner_id']}_{self.request_ids['collection_ids'][0]}"
        try:
            item = await self.client.get_item(item_id=item_id, collection_id=collection_id, request=request)
            return item
        except NotFoundError:
            logger.info(f"The item '{item_id}' does not exist in collection '{collection_id}'")
            return None
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception(f"Exception: {e}")
            raise log_http_exception(
                detail=f"Exception when trying to get the item {item_id} from the collection '{collection_id}'",
                status_code=HTTP_400_BAD_REQUEST,
            ) from e

    def check_s3_key(self, item: dict, asset_name: str, s3_key):
        """Check if the given S3 key exists and matches the expected path.

        Args:
            item (dict): The item from the catalog (if it does exist) containing the asset.
            asset_name (str): The name of the asset to check.
            s3_key (str): The S3 key path to check against.

        Returns:
            bool: True if the S3 key is valid and exists, otherwise False.
            NOTE: Don't mind if we have RSPY_LOCAL_CATALOG_MODE set to ON (meaning self.s3_handler is None)

        Raises:
            HTTPException: If the s3_handler is not available, if S3 paths cannot be retrieved,
                        if the S3 paths do not match, or if there is an error checking the key.
        """
        if not item or not self.s3_handler:
            return False, -1
        # update an item
        existing_asset = item["assets"].get(asset_name)
        if not existing_asset:
            return False, -1

        # check if the new s3_href is the same as the existing one
        try:
            item_s3_path = existing_asset["href"]
        except KeyError as exc:
            raise log_http_exception(
                detail=f"Failed to get the s3 path for the asset {asset_name}",
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            ) from exc
        if item_s3_path != s3_key:
            raise log_http_exception(
                detail=(
                    f"Received an updated path for the asset {asset_name} of item {item['id']}. "
                    f"The current path is {item_s3_path}, and the new path is {s3_key}. "
                    "However, changing an existing path of an asset is not allowed."
                ),
                status_code=HTTP_400_BAD_REQUEST,
            )
        s3_key_array = s3_key.split("/")
        bucket = s3_key_array[2]
        key_path = "/".join(s3_key_array[3:])

        # check the presence of the key
        try:
            s3_key_exists, size = self.s3_handler.check_s3_key_on_bucket(bucket, key_path)
            if not s3_key_exists:
                raise log_http_exception(
                    detail=f"The s3 key {s3_key} should exist on the bucket, but it couldn't be checked",
                    status_code=HTTP_400_BAD_REQUEST,
                )
            return True, size
        except RuntimeError as rte:
            raise log_http_exception(
                detail=f"When checking the presence of the {s3_key} key, an error has been raised: {rte}",
                status_code=HTTP_400_BAD_REQUEST,
            ) from rte

    def s3_bucket_handling(self, bucket_name: str, files_s3_key: list[str], item: dict, request: Request) -> None:
        """Handle the transfer and deletion of files in S3 buckets.

        Args:
            files_s3_key (list[str]): List of S3 keys for the files to be transfered.
            item (dict): The catalog item from which all the remaining assets should be deleted.
            request (Request): The request object, used to determine the request method.

        Raises:
            HTTPException: If there are errors during the S3 transfer or deletion process.
        """
        if not self.s3_handler or not files_s3_key:
            logger.debug(f"s3_bucket_handling: nothing to do: {self.s3_handler} | {files_s3_key}")
            return

        try:
            # get the temporary bucket name, there should be one only in the set
            temp_bucket_name = get_temp_bucket_name(files_s3_key)
            # now, remove the s3://temp_bucket_name for each s3_key
            for idx, s3_key in enumerate(files_s3_key):
                # build the list with files to be deleted from the temporary bucket
                self.s3_files_to_be_deleted.append(s3_key)
                files_s3_key[idx] = s3_key.replace(f"s3://{temp_bucket_name}", "")

            err_message = f"Failed to transfer file(s) from '{temp_bucket_name}' bucket to \
'{bucket_name}' catalog bucket!"
            config = TransferFromS3ToS3Config(
                files_s3_key,
                temp_bucket_name,
                bucket_name,
                copy_only=True,
                max_retries=3,
            )

            failed_files = self.s3_handler.transfer_from_s3_to_s3(config)

            if failed_files:
                self.s3_files_to_be_deleted.clear()
                raise log_http_exception(
                    detail=f"{err_message} {failed_files}",
                    status_code=HTTP_400_BAD_REQUEST,
                )
            # For a PUT request, all new assets are transferred (as described above).
            # Any asset that already exists in the catalog from a previous POST request
            # but is not included in the current request will be deleted.
            # In the case of a PATCH request (not yet implemented), no assets should be deleted.
            if item and request.method == "PUT":
                for asset in item["assets"]:
                    self.s3_files_to_be_deleted.append(item["assets"][asset]["href"])
        except KeyError as kerr:
            self.s3_files_to_be_deleted.clear()
            raise log_http_exception(
                detail=f"{err_message} Failed to find S3 credentials.",
                status_code=HTTP_400_BAD_REQUEST,
            ) from kerr
        except RuntimeError as rte:
            raise log_http_exception(detail=f"{err_message} Reason: {rte}", status_code=HTTP_400_BAD_REQUEST) from rte

    def update_stac_item_publication(  # pylint: disable=too-many-locals,too-many-branches,too-many-nested-blocks
        self,
        content: dict,
        request: Request,
        item: dict,
    ) -> dict:
        """Update the JSON body of a feature push to the catalog.

        Args:
            content (dict): The content to update.
            request (Request): The HTTP request object.
            item (dict): The item from the catalog (if exists) to update.

        Returns:
            dict: The updated content.

        Raises:
            HTTPException: If there are errors in processing the request, such as missing collection name,
                        invalid S3 bucket, or failed file transfers.
        """
        if not int(os.environ.get("RSPY_LOCAL_CATALOG_MODE", 0)):  # don't move files if we are in local mode
            self.s3_handler = get_s3_handler()

        collection_ids = self.request_ids.get("collection_ids", [])
        user = self.request_ids.get("owner_id")
        logger.debug(f"Update item for user: {user}")
        if not isinstance(collection_ids, list) or not collection_ids or not user:
            raise log_http_exception(
                detail="Failed to get the user or the name of the collection!",
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            )
        collection_id = collection_ids[0]
        verify_existing_item_from_catalog(request.method, item, content.get("id", "Unknown"), f"{user}_{collection_id}")

        item_eopf_type = content["properties"].get("eopf:type", "*")
        bucket_name = get_bucket_name_from_config(user, collection_id, item_eopf_type)

        files_s3_key = []
        # 1 - update assets href
        for asset in content["assets"]:
            s3_filename, alternate_field = get_s3_filename_from_asset(content["assets"][asset])
            if alternate_field:
                if not item:
                    # the asset should be already in the catalog from a previous POST/PUT request
                    raise log_http_exception(
                        detail=(f"The item that contains asset '{asset}' does not exist in the catalog but it should "),
                        status_code=HTTP_400_BAD_REQUEST,
                    )
            # else:
            # if alternate_key is missing, it indicates the request originates from the staging process.
            # In this case, the file should not be deleted from the temp bucket — it's already stored in the
            # final catalog bucket, so no action is needed.

            logger.debug(f"HTTP request add/update asset: {s3_filename!r}")
            fid = s3_filename.rsplit("/", maxsplit=1)[-1]
            if fid != asset:
                raise log_http_exception(
                    detail=(
                        f"Invalid structure for the asset '{asset}'. The name of the asset "
                        f"should be the filename, that is {fid} "
                    ),
                    status_code=HTTP_400_BAD_REQUEST,
                )
            # 2 - update alternate href to define catalog s3 bucket
            try:
                old_bucket_arr = s3_filename.split("/")
                old_bucket = old_bucket_arr[2]
                old_bucket_arr[2] = bucket_name
                s3_key = "/".join(old_bucket_arr)
                # Check if the S3 key exists
                s3_key_exists, _ = self.check_s3_key(item, asset, s3_key)
                if not s3_key_exists:
                    # update the S3 path to use the catalog bucket
                    # add also the file:size and file:local_path fields
                    content["assets"][asset].update({"href": s3_key, "file:local_path": "/".join(old_bucket_arr[-2:])})
                    # update the 'href' key with the download link and create the alternate field
                    https_link = f"https://{request.url.netloc}/catalog/\
collections/{user}:{collection_id}/items/{self.request_ids['item_id']}/download/{asset}"
                    content["assets"][asset].update({ALTERNATE_STRING: {"https": {"href": https_link}}})

                    # copy the key only if it isn't already in the final catalog bucket
                    # (don't do anything if in local mode)
                    if not int(os.environ.get("RSPY_LOCAL_CATALOG_MODE", 0)):
                        s3_key_exists, size = self.s3_handler.check_s3_key_on_bucket(
                            bucket_name,
                            "/".join(old_bucket_arr[3:]),
                        )
                        if not s3_key_exists:
                            files_s3_key.append(s3_filename)
                            if "file:size" not in content["assets"][asset]:
                                _, size = self.s3_handler.check_s3_key_on_bucket(
                                    old_bucket,
                                    "/".join(old_bucket_arr[3:]),
                                )
                        if "file:size" not in content["assets"][asset] and size != -1:
                            content["assets"][asset]["file:size"] = size
                        logger.debug(f"file:size = {size}")

                elif request.method == "PUT":
                    # remove the asset from the item, all assets that remain shall
                    # be deleted from the catalog s3 bucket later on
                    item["assets"].pop(asset)
            except (IndexError, AttributeError, KeyError, RuntimeError) as exc:
                raise log_http_exception(
                    detail=f"Failed to handle the s3 level. Reason: {exc}",
                    status_code=HTTP_400_BAD_REQUEST,
                ) from exc

        # 3 - include new stac extensions if not present
        for new_stac_extension in [
            "https://home.rs-python.eu/ownership-stac-extension/v1.1.0/schema.json",
            "https://stac-extensions.github.io/alternate-assets/v1.1.0/schema.json",
            "https://stac-extensions.github.io/file/v2.1.0/schema.json",
        ]:
            if new_stac_extension not in content["stac_extensions"]:
                content["stac_extensions"].append(new_stac_extension)

        # 4 - bucket handling
        self.s3_bucket_handling(bucket_name, files_s3_key, item, request)

        # 5 - add owner data
        content["properties"].update({"owner": user})
        content.update({"collection": f"{user}_{collection_id}"})
        return content

    def generate_presigned_url(self, content, path):
        """This function is used to generate a time-limited download url"""
        # Assume that pgstac already selected the correct asset id
        # just check type, generate and return url
        path_splitted = path.split("/")
        asset_id = path_splitted[-1]
        item_id = path_splitted[-3]
        # Retrieve bucket name from config using what's in content
        item_owner = content["properties"].get("owner", "*")
        item_collection = content.get("collection", "*").removeprefix(f"{item_owner}_")
        item_eopf_type = content["properties"].get("eopf:type", "*")
        bucket_name = get_bucket_name_from_config(item_owner, item_collection, item_eopf_type)
        try:
            s3_path = (
                content["assets"][asset_id]["href"]
                .replace(
                    f"s3://{bucket_name}",
                    "",
                )
                .lstrip("/")
            )
        except KeyError:
            return f"Failed to find asset named '{asset_id}' from item '{item_id}'", HTTP_404_NOT_FOUND
        try:
            s3_handler = get_s3_handler()
            if not s3_handler:
                raise log_http_exception(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to find s3 credentials",
                )
            response = s3_handler.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": s3_path},
                ExpiresIn=PRESIGNED_URL_EXPIRATION_TIME,
            )
        except botocore.exceptions.ClientError:
            return "Failed to generate presigned url", HTTP_400_BAD_REQUEST
        return response, HTTP_302_FOUND

    def find_owner_id(self, cql2_ast: Node) -> str:
        """Browse an abstract syntax tree (AST) to find the owner_id.
        Then return it.

        Args:
            cql2_ast (_type_): The AST

        Returns:
            str: The owner_id
        """
        res = ""
        if hasattr(cql2_ast, "lhs"):
            if isinstance(cql2_ast.lhs, Attribute) and cql2_ast.lhs.name == "owner":
                if isinstance(cql2_ast, Like):
                    res = cql2_ast.pattern
                elif isinstance(cql2_ast, Equal):
                    res = cql2_ast.rhs
            elif left := self.find_owner_id(cql2_ast.lhs):
                res = left
            elif hasattr(cql2_ast, "rhs"):
                if right := self.find_owner_id(cql2_ast.rhs):
                    res = right
        return res

    async def collection_exists(self, request: Request, collection_id: str) -> bool:
        """Check if the collection exists.

        Returns:
            bool: True if the collection exists, False otherwise
        """
        try:
            await self.client.get_collection(collection_id, request)
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Collection %s not found: %s", collection_id, e)
            return False

    async def manage_search_request(  # pylint: disable=too-many-statements,too-many-branches
        self,
        request: Request,
    ) -> Request | JSONResponse:
        """find the user in the filter parameter and add it to the
        collection name.

        Args:
            request Request: the client request.

        Returns:
            Request: the new request with the collection name updated.
        """
        # ---------- POST requests
        if request.method == "POST":
            content = await request.json()

            # Management of priority for the assignation of the owner_id
            if not self.request_ids["owner_id"]:
                filters = parse_cql2_json(content["filter"]) if "filter" in content else None
                self.request_ids["owner_id"] = (
                    (self.find_owner_id(filters) if filters else None)
                    or content.get("owner")
                    or get_user(self.request_ids["owner_id"], self.request_ids["user_login"])
                )

            # Add filter-lang option to the content if it doesn't already exist
            if "filter" in content:
                filter_lang = {"filter-lang": content.get("filter-lang", "cql2-json")}
                stac_filter = content.pop("filter")
                content = {
                    **content,
                    **filter_lang,
                    "filter": stac_filter,
                }  # The "filter_lang" field has to be placed BEFORE the filter.

            # ----- Call /catalog/search with POST method endpoint
            if "collections" in content:
                # Check if each collection exist with their raw name, if not concatenate owner_id to the collection name
                for i, collection in enumerate(content["collections"]):
                    if not await self.collection_exists(request, collection):
                        content["collections"][i] = f"{self.request_ids['owner_id']}_{collection}"
                        logger.debug(f"Using collection name: {content['collections'][i]}")

                self.request_ids["collection_ids"] = content["collections"]
                request = self.override_request_body(request, content)

        # ---------- GET requests
        elif request.method == "GET":
            # Get dictionary of query parameters
            query_params_dict = dict(request.query_params)

            # Update owner_id if it is not already defined from path parameters
            if not self.request_ids["owner_id"]:
                self.request_ids["owner_id"] = (
                    (
                        self.find_owner_id(parse_cql2_text(query_params_dict["filter"]))
                        if "filter" in query_params_dict
                        else ""
                    )
                    or query_params_dict.get("owner")
                    or get_user(self.request_ids["owner_id"], self.request_ids["user_login"])
                )

            # ----- Catch endpoint catalog/search + query parameters (e.g. /search?ids=S3_OLC&collections=titi)
            if "collections" in query_params_dict:
                coll_list = query_params_dict["collections"].split(",")

                # Check if each collection exist with their raw name, if not concatenate owner_id to the collection name
                for i, collection in enumerate(coll_list):
                    if not await self.collection_exists(request, collection):
                        coll_list[i] = f"{self.request_ids['owner_id']}_{collection}"

                self.request_ids["collection_ids"] = coll_list
                query_params_dict["collections"] = ",".join(coll_list)
                request = self.override_request_query_string(request, query_params_dict)

        # Check that the collection from the request exists
        for collection in self.request_ids["collection_ids"]:
            if not await self.collection_exists(request, collection):
                raise log_http_exception(status_code=HTTP_404_NOT_FOUND, detail=f"Collection {collection} not found.")

        # Check authorisation in cluster mode
        if common_settings.CLUSTER_MODE and not get_authorisation(
            self.request_ids["collection_ids"],
            self.request_ids["auth_roles"],
            "read",
            self.request_ids["owner_id"],
            self.request_ids["user_login"],
        ):
            raise log_http_exception(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized access.")
        return request

    async def manage_search_response(self, request: Request, response: StreamingResponse) -> GeoJSONResponse:
        """The '/catalog/search' endpoint doesn't give the information of the owner_id and collection_ids.
        to get these values, this function try to search them into the search query. If successful,
        updates the response content by removing the owner_id from the collection_ids and adapt all links.
        If not successful, does nothing and return the response.

        Args:
            response (StreamingResponse): The response from the rs server.
            request (Request): The request from the client.

        Returns:
            GeoJSONResponse: The updated response.
        """
        filters: Node | None = None
        if request.method == "GET":
            query = parse_qs(request.url.query)
            if "filter" in query:
                qs_filter = query["filter"][0]
                filters = parse_cql2_text(qs_filter)
        elif request.method == "POST":
            query = await request.json()
            if "filter" in query:
                qs_filter_json = query["filter"]
                filters = parse_cql2_json(qs_filter_json)

        try:
            owner_id = self.find_owner_id(filters)
        except AttributeError:
            owner_id = ""
        if owner_id:
            self.request_ids["owner_id"] = owner_id

        # Remove owner_id from the collection name
        if "collections" in query:
            # Extract owner_id from the name of the first collection in the list
            self.request_ids["owner_id"] = self.request_ids["collection_ids"][0].split("_")[0]
            self.request_ids["collection_ids"] = [
                coll.removeprefix(f"{self.request_ids['owner_id']}_") for coll in query["collections"][0].split(",")
            ]
        body = [chunk async for chunk in response.body_iterator]
        dec_content = b"".join(map(lambda x: x if isinstance(x, bytes) else x.encode(), body)).decode()  # type: ignore
        content = json.loads(dec_content)
        content = adapt_links(content, "features")
        for collection_id in self.request_ids["collection_ids"]:
            content = adapt_links(content, "features", self.request_ids["owner_id"], collection_id)

        # Add the stac authentication extension
        await self.add_authentication_extension(content)

        return GeoJSONResponse(content, response.status_code, headers_minus_content_length(response))

    async def manage_put_post_request(  # pylint: disable=too-many-statements,too-many-return-statements,too-many-branches  # noqa: E501
        self,
        request: Request,
    ) -> Request | JSONResponse:
        """Adapt the request body for the STAC endpoint.

        Args:
            request (Request): The Client request to be updated.

        Returns:
            Request: The request updated.
        """
        try:
            original_content = await request.json()
            content = copy.deepcopy(original_content)
            if not self.request_ids["owner_id"]:
                self.request_ids["owner_id"] = get_user(None, self.request_ids["user_login"])
            # If item is not geolocated, add a default one to comply pgstac format.
            if (  # If we are in cluster mode and the user_login is not authorized
                # to put/post returns a HTTP_401_UNAUTHORIZED status.
                common_settings.CLUSTER_MODE
                and not get_authorisation(
                    self.request_ids["collection_ids"],
                    self.request_ids["auth_roles"],
                    "write",
                    self.request_ids["owner_id"],
                    self.request_ids["user_login"],
                )
            ):
                raise log_http_exception(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized access.")

            if len(self.request_ids["collection_ids"]) > 1:
                raise log_http_exception(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Cannot create or update more than one collection !",
                )

            if len(self.request_ids["collection_ids"]) == 0:
                raise log_http_exception(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Cannot create or update -> no collection specified !",
                )

            collection = self.request_ids["collection_ids"][0]
            if (
                request.scope["path"] == CATALOG_COLLECTIONS  # POST collection
                or request.scope["path"]
                == CATALOG_COLLECTIONS + f"/{self.request_ids['owner_id']}_{collection}"  # PUT collection
            ):
                # Manage a collection creation. The apikey user should be the same as the owner
                # field in the body request. In other words, an apikey user cannot create a
                # collection owned by another user.
                # We don't care for local mode, any user may create / delete collection owned by another user
                if common_settings.CLUSTER_MODE and self.request_ids["owner_id"] != self.request_ids["user_login"]:
                    error = f"The '{self.request_ids['user_login']}' user cannot create a \
collection owned by the '{self.request_ids['owner_id']}' user. Additionally, modifying the 'owner' \
field is not permitted also."
                    raise log_http_exception(status_code=HTTP_401_UNAUTHORIZED, detail=error)
                content["id"] = owner_id_and_collection_id(self.request_ids["owner_id"], content["id"])
                if not content.get("owner"):
                    content["owner"] = self.request_ids["owner_id"]
                logger.debug(f"Handling for collection {content['id']}")
                # TODO update the links also?

            # The following section handles the request to create/update an item
            elif "/items" in request.scope["path"]:
                # first check if the collection exists
                if not await self.collection_exists(request, f"{self.request_ids['owner_id']}_{collection}"):
                    raise log_http_exception(
                        status_code=HTTP_404_NOT_FOUND,
                        detail=f"Collection {collection} does not exist.",
                    )

                # try to get the item if it is already part from the collection
                item = await self.get_item_from_collection(request)

                content = self.update_stac_item_publication(content, request, item)

                if content:
                    if request.method == "POST":
                        content = timestamps_extension.set_timestamps_for_creation(content)
                        content = timestamps_extension.set_timestamps_for_insertion(content)
                    else:  # PUT
                        published = expires = ""
                        if item and item.get("properties"):
                            published = item["properties"].get("published", "")
                            expires = item["properties"].get("expires", "")
                        if not published and not expires:
                            raise log_http_exception(
                                status_code=HTTP_400_BAD_REQUEST,
                                detail=f"Item {content['id']} not found.",
                            )
                        content = timestamps_extension.set_timestamps_for_update(
                            content,
                            original_published=published,
                            original_expires=expires,
                        )
                    # If item doesn't contain a geometry/bbox, just fill with a default one.
                    if not content.get("geometry", None):
                        content["geometry"] = DEFAULT_GEOM
                    if not content.get("bbox", None):
                        content["bbox"] = DEFAULT_BBOX
                if hasattr(content, "status_code"):
                    return content

            # update request body if needed
            if content != original_content:
                request = self.override_request_body(request, content)

            return request  # pylint: disable=protected-access
        except KeyError as kerr_msg:
            raise log_http_exception(
                detail=f"Missing key in request body! {kerr_msg}",
                status_code=HTTP_400_BAD_REQUEST,
            ) from kerr_msg

    def override_request_body(self, request: Request, content: Any) -> Request:
        """Update request body (better find the function that updates the body maybe?)"""
        request._body = json.dumps(content).encode("utf-8")  # pylint: disable=protected-access
        logger.debug("new request body: %s", request._body)  # pylint: disable=protected-access
        return request

    def override_request_query_string(self, request: Request, query_params: dict) -> Request:
        """Update request query string"""
        request.scope["query_string"] = urlencode(query_params, doseq=True).encode("utf-8")
        logger.debug("new request query_string: %s", request.scope["query_string"])
        return request

    def manage_all_collections(self, collections: dict, auth_roles: list, user_login: str) -> list[dict]:
        """Return the list of all collections accessible by the user calling it.

        Args:
            collections (dict): List of all collections.
            auth_roles (list): List of roles of the api-key.
            user_login (str): The api-key owner.

        Returns:
            dict: The list of all collections accessible by the user.
        """
        catalog_read_right_pattern = (
            r"rs_catalog_(?P<owner_id>.*(?=:)):(?P<collection_id>.+)_(?P<right_type>read|write|download)(?=$)"
        )
        accessible_collections = []

        # Filter roles for read access
        read_roles = [role for role in auth_roles if re.match(catalog_read_right_pattern, role)]

        for role in read_roles:
            if match := re.match(catalog_read_right_pattern, role):
                groups = match.groupdict()
                if groups["right_type"] == "read":
                    owner_id = groups["owner_id"]
                    collection_id = groups["collection_id"]
                    accessible_collections.extend(
                        filter_collections(
                            collections,
                            f"{owner_id}_" if collection_id == "*" else f"{owner_id}_{collection_id}",
                        ),
                    )

        accessible_collections.extend(filter_collections(collections, user_login))
        return sorted(accessible_collections, key=lambda c: c["id"])

    def update_links_for_all_collections(self, collections: list[dict]) -> list[dict]:
        """Update the links for the endpoint /catalog/collections.

        Args:
            collections (list[dict]): all the collections to be updated.

        Returns:
            list[dict]: all the collections after the links updated.
        """
        for collection in collections:
            owner_id = collection["owner"]
            collection_id = collection["id"].removeprefix(f"{owner_id}_")
            for link in collection["links"]:
                link_parser = urlparse(link["href"])
                new_path = add_user_prefix(link_parser.path, owner_id, collection_id)
                link["href"] = link_parser._replace(path=new_path).geturl()
        return collections

    def update_stac_catalog_metadata(self, metadata: dict):
        """Update the metadata fields from a catalog

        Args:
            metadata (dict): The metadata that has to be updated. The fields id, title,
                            description and stac_version are to be updated, by using the env vars which have
                            to be set before starting the app/pod. The existing values are used if
                            the env vars are not found
        """
        if metadata.get("type") == "Catalog":
            for key in ["id", "title", "description", "stac_version"]:
                if key in metadata:
                    metadata[key] = os.environ.get(f"CATALOG_METADATA_{key.upper()}", metadata[key])

    async def manage_get_response(
        self,
        request: Request,
        response: StreamingResponse,
    ) -> Response | JSONResponse:
        """Remove the user name from objects and adapt all links.

        Args:
            request (Request): The client request.
            response (Response | StreamingResponse): The response from the rs-catalog.
        Returns:
            Response: The response updated.
        """
        # Load content of the response as a dictionary
        body = [chunk async for chunk in response.body_iterator]
        dec_content = b"".join(map(lambda x: x if isinstance(x, bytes) else x.encode(), body)).decode()  # type: ignore
        content = await self.manage_get_response_content(request, dec_content) if dec_content else None
        media_type = "application/geo+json" if "/items" in request.scope["path"] else None
        return JSONResponse(content, response.status_code, headers_minus_content_length(response), media_type)

    async def manage_get_response_content(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        self,
        request: Request,
        dec_content: str,
    ) -> Any:
        """Manage content of GET responses with a body

        Args:
            request (Request): The client request.
            dec_content (str): The decoded json content
        Returns:
            Any: the response content
        """
        content = json.loads(dec_content)
        self.update_stac_catalog_metadata(content)
        auth_roles = []
        user_login = ""

        if content.get("geometry") == DEFAULT_GEOM:
            content["geometry"] = None
        if content.get("bbox") == DEFAULT_BBOX:
            content["bbox"] = None

        if common_settings.CLUSTER_MODE:  # Get the list of access and the user_login calling the endpoint.
            auth_roles = request.state.auth_roles
            user_login = request.state.user_login

        # Manage local landing page of the catalog
        if request.scope["path"] in (CATALOG_PREFIX, CATALOG_PREFIX + "/"):
            if common_settings.CLUSTER_MODE:  # /catalog
                content = manage_landing_page(auth_roles, user_login, content)
            regex_catalog = CATALOG_COLLECTIONS + r"/(?P<owner_id>.+?)_(?P<collection_id>.*)"
            for link in content["links"]:
                link_parser = urlparse(link["href"])

                if match := re.match(regex_catalog, link_parser.path):
                    groups = match.groupdict()
                    new_path = add_user_prefix(link_parser.path, groups["owner_id"], groups["collection_id"])
                    link["href"] = link_parser._replace(path=new_path).geturl()
            url = request.url._url  # pylint: disable=protected-access
            url = url[: len(url) - len(request.url.path)]
            content = add_prefix_link_landing_page(content, url)

            # patch the catalog landing page with "rel": "child" link for each collection
            # limit must be explicitely set, otherwise the default pgstac limit of 10 is used
            collections_resp = await self.client.all_collections(request=request, limit=1000)
            collections = self.manage_all_collections(collections_resp.get("collections", []), auth_roles, user_login)
            base_url = (
                next((link["href"] for link in content["links"] if link.get("rel") == "self"), "").rstrip("/") + "/"
            )

            for collection in collections:
                collection_id = (
                    collection["id"].removeprefix(f"{collection['owner']}_")
                    if collection["owner"]
                    else collection["id"]
                )
                content["links"].append(
                    {
                        "rel": "child",
                        "type": "application/json",
                        "title": collection.get("title") or collection_id,
                        "href": urljoin(base_url, f"collections/{collection['owner']}:{collection_id}"),
                    },
                )

        elif request.scope["path"] == CATALOG_COLLECTIONS:  # /catalog/collections
            content["collections"] = self.manage_all_collections(
                content["collections"],
                auth_roles,
                user_login,
            )
            content["collections"] = self.update_links_for_all_collections(content["collections"])

        # If we are in cluster mode and the user_login is not authorized
        # to this endpoint returns a HTTP_401_UNAUTHORIZED status.
        elif (
            common_settings.CLUSTER_MODE
            and self.request_ids["collection_ids"]
            and self.request_ids["owner_id"]
            and not get_authorisation(
                self.request_ids["collection_ids"],
                auth_roles,
                "read",
                self.request_ids["owner_id"],
                user_login,
            )
            # I don't know why but the STAC browser doesn't send authentication for the queryables endpoint.
            # So allow this endpoint without authentication in this specific case.
            and not (common_settings.request_from_stacbrowser(request) and request.url.path.endswith(QUERYABLES))
        ):
            raise log_http_exception(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized access.")
        elif (
            "/collections" in request.scope["path"] and "/items" not in request.scope["path"]
        ):  # /catalog/collections/owner_id:collection_id
            content = adapt_object_links(content, self.request_ids["owner_id"])
        elif (
            "/items" in request.scope["path"] and not self.request_ids["item_id"]
        ):  # /catalog/owner_id/collections/collection_id/items
            content = adapt_links(
                content,
                "features",
                self.request_ids["owner_id"],
                self.request_ids["collection_ids"][0],
            )
        elif self.request_ids["item_id"]:  # /catalog/owner_id/collections/collection_id/items/item_id
            content = adapt_object_links(content, self.request_ids["owner_id"])
        else:
            logger.debug(f"No link adaptation performed for {request.scope}")

        # Add the stac authentication extension
        await self.add_authentication_extension(content)
        return content

    async def manage_download_response(
        self,
        request: Request,
        response: StreamingResponse,
    ) -> JSONResponse | RedirectResponse:
        """
        Manage download response and handle requests that should generate a presigned URL.

        Args:
            request (starlette.requests.Request): The request object.
            response (starlette.responses.StreamingResponse): The response object received.

        Returns:
            JSONResponse: Returns a JSONResponse object containing either the presigned URL or
            the response content with the appropriate status code.
        """
        user_login = ""
        auth_roles = []
        if common_settings.CLUSTER_MODE:  # Get the list of access and the user_login calling the endpoint.
            auth_roles = request.state.auth_roles
            user_login = request.state.user_login
        if (  # If we are in cluster mode and the user_login is not authorized
            # to this endpoint returns a HTTP_401_UNAUTHORIZED status.
            common_settings.CLUSTER_MODE
            and self.request_ids["collection_ids"]
            and self.request_ids["owner_id"]
            and not get_authorisation(
                self.request_ids["collection_ids"],
                auth_roles,
                "download",
                self.request_ids["owner_id"],
                user_login,
            )
        ):
            raise log_http_exception(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized access.")
        body = [chunk async for chunk in response.body_iterator]
        content = json.loads(b"".join(body).decode())  # type:ignore
        if content.get("code", True) != "NotFoundError":
            # Only generate presigned url if the item is found
            content, code = self.generate_presigned_url(content, request.url.path)
            if code == HTTP_302_FOUND:
                return RedirectResponse(url=content, status_code=code)
            return JSONResponse(content, code, headers_minus_content_length(response))
        return JSONResponse(content, response.status_code, headers_minus_content_length(response))

    async def manage_put_post_response(self, request: Request, response: StreamingResponse):
        """
        Manage put or post responses.

        Args:
            response (starlette.responses.StreamingResponse): The response object received.

        Returns:
            JSONResponse: Returns a JSONResponse object containing the response content
            with the appropriate status code.

        Raises:
            HTTPException: If there is an error while clearing the temporary bucket,
            raises an HTTPException with a status code of 400 and detailed information.
            If there is a generic exception, raises an HTTPException with a status code
            of 400 and a generic bad request detail.
        """
        try:
            user = self.request_ids["owner_id"]
            body = [chunk async for chunk in response.body_iterator]
            response_content = json.loads(b"".join(body).decode())  # type: ignore
            # Don't display geometry and bbox for default case since it was added just for compliance.
            if request.scope["path"] == CATALOG_COLLECTIONS:
                response_content = adapt_object_links(response_content, self.request_ids["owner_id"])
            elif (
                request.scope["path"]
                == CATALOG_COLLECTIONS
                + f"/{user}_{self.request_ids['collection_ids'][0]}/items/{self.request_ids['item_id']}"
            ):
                response_content = adapt_object_links(response_content, self.request_ids["owner_id"])
                if response_content.get("geometry") == DEFAULT_GEOM:
                    response_content["geometry"] = None
                if response_content.get("bbox") == DEFAULT_BBOX:
                    response_content["bbox"] = None
            delete_s3_files(self.s3_files_to_be_deleted)
            self.s3_files_to_be_deleted.clear()
        except RuntimeError as exc:
            raise log_http_exception(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to clean temporary bucket: {exc}",
            ) from exc
        except Exception as exc:  # pylint: disable=broad-except
            raise log_http_exception(status_code=HTTP_400_BAD_REQUEST, detail=f"Bad request: {exc}") from exc
        media_type = "application/geo+json" if "/items" in request.scope["path"] else None
        return JSONResponse(response_content, response.status_code, headers_minus_content_length(response), media_type)

    async def manage_delete_response(self, response: StreamingResponse, user: str) -> Response:
        """Change the name of the deleted collection by removing owner_id.

        Args:
            response (StreamingResponse): The client response.
            user (str): The owner id.

        Returns:
            JSONResponse: The new response with the updated collection name.
        """
        body = [chunk async for chunk in response.body_iterator]
        response_content = json.loads(b"".join(body).decode())  # type:ignore
        if "deleted collection" in response_content:
            response_content["deleted collection"] = response_content["deleted collection"].removeprefix(f"{user}_")
        # delete the s3 files as well
        delete_s3_files(self.s3_files_to_be_deleted)
        self.s3_files_to_be_deleted.clear()
        return JSONResponse(response_content, HTTP_200_OK, headers_minus_content_length(response))

    async def build_filelist_to_be_deleted(self, request):
        """Build the list of the s3 files that will be deleted if the request is successfull"""
        for ci in self.request_ids["collection_ids"]:
            collection_id = f"{self.request_ids['owner_id']}_{ci}"
            items = []
            try:
                if "/items" not in request.scope["path"]:
                    # this is the case for delete endpoint /collections/<collection_name>
                    # use pagination, otherwise a maximum of the default limit (10) items is returned
                    # NOTE: Unable to use the pagination from pgstac client. Temporary, use a limit of 100
                    token = None
                    while True:
                        items_collection = await self.client.item_collection(
                            request=request,
                            collection_id=collection_id,
                            limit=100,
                            token=token,
                        )
                        items.extend(items_collection.get("features", []))
                        # Check if there's a next token for pagination
                        token = get_token_for_pagination(items_collection)

                        if not token:
                            # No more pages left, break the loop
                            break
                else:
                    # this is the case for delete endpoint /collections/<collection_name>/items/<item_name>
                    item = await self.client.get_item(
                        item_id=self.request_ids["item_id"],
                        collection_id=collection_id,
                        request=request,
                    )
                    items = [item]
            except NotFoundError as nfe:
                logger.error(f"Failed to find the requested object to be deleted. {nfe}")
                return
            except KeyError as e:
                logger.error(f"Failed to build the list of items to be deleted due to missing key: {e}")
                return
            logger.debug(f"Found {len(items)} items: {items}")
            try:
                for item in items:
                    assets = item.get("assets", {})
                    for _, asset_info in assets.items():
                        s3_href = asset_info.get("href")
                        if s3_href:
                            self.s3_files_to_be_deleted.append(s3_href)
            except KeyError as e:
                logger.error(
                    f"Failed to build the list of S3 files to be deleted due to missing key in dictionary: {e}",
                )
                return
            logger.info(
                "Successfully built the list of S3 files to be deleted. "
                f"There are {len(self.s3_files_to_be_deleted)} files to be deleted",
            )

    async def manage_delete_request(self, request: Request):
        """Check if the deletion is allowed.

        Args:
            request (Request): The client request.

        Raises:
            HTTPException: If the user is not authenticated.

        Returns:
            bool: Return True if the deletion is allowed, False otherwise.
        """
        user_login = getpass.getuser()
        auth_roles = []
        if common_settings.CLUSTER_MODE:  # Get the list of access and the user_login calling the endpoint.
            auth_roles = request.state.auth_roles
            user_login = request.state.user_login
        if (  # If we are in cluster mode and the user_login is not authorized
            # to this endpoint returns a HTTP_401_UNAUTHORIZED status.
            common_settings.CLUSTER_MODE
            and self.request_ids["collection_ids"]
            and self.request_ids["owner_id"]
            and not get_authorisation(
                self.request_ids["collection_ids"],
                auth_roles,
                "write",
                self.request_ids["owner_id"],
                user_login,
            )
        ):
            return False
        # we don't care for local mode, any user may create / delete collection owned by another user
        if common_settings.CLUSTER_MODE and self.request_ids["owner_id"] != user_login:
            # Manage a collection deletion. The apikey user (or local user if in local mode)
            # should be the same as the owner field in the body request. In other words, the
            # apikey user cannot delete a collection owned by another user
            logger.error(
                f"The '{user_login}' user cannot delete a \
collection or an item from a collection owned by the '{self.request_ids['owner_id']}' user",
            )
            return False
        await self.build_filelist_to_be_deleted(request)
        return True

    async def dispatch(  # pylint: disable=too-many-branches
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        Redirect the user catalog specific endpoint and adapt the response content.

        Args:
            request (Request): Initial request
            call_next: next call to apply

        Returns:
            response (Response): Response to the current request
        """
        request_body = None if request.method not in ["PATCH", "POST", "PUT"] else await request.json()
        auth_roles = user_login = owner_id = None

        # ---------- Management of  authentification (retrieve user_login + default owner_id)
        if common_settings.CLUSTER_MODE:  # Get the list of access and the user_login calling the endpoint.
            try:
                auth_roles = request.state.auth_roles
                user_login = request.state.user_login
            # Case of endpoints that do not call the authenticate function
            # Get the the user_login calling the endpoint. If this is not set (the authentication.authenticate function
            # is not called), the local user shall be used (later on, in rereoute_url)
            # The common_settings.CLUSTER_MODE may not be used because for some endpoints like /api
            # the authenticate is not called even if common_settings.CLUSTER_MODE is True. Thus, the presence of
            # user_login has to be checked instead
            except (NameError, AttributeError):
                auth_roles = []
                user_login = get_user(None, None)  # Get default local or cluster user
        elif common_settings.LOCAL_MODE:
            user_login = get_user(None, None)
        owner_id = ""  # Default owner_id is empty
        logger.debug(
            f"Received {request.method} from '{user_login}' | {request.url.path}?{request.query_params}",
        )

        # ---------- Request rerouting
        # Dictionary to easily access main data from the request
        self.request_ids = {
            "auth_roles": auth_roles,
            "user_login": user_login,
            "owner_id": owner_id,
            "collection_ids": [],
            "item_id": "",
        }
        reroute_url(request, self.request_ids)
        if not request.scope["path"]:  # Invalid endpoint
            raise log_http_exception(status_code=HTTP_400_BAD_REQUEST, detail="Invalid endpoint.")
        logger.debug(f"path = {request.scope['path']} | requests_ids = {self.request_ids}")

        # Ensure that user_login is not null after rerouting
        if not self.request_ids["user_login"]:
            raise log_http_exception(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="user_login is not defined !",
            )

        # ---------- Body data recovery
        # Recover user and collection id with the ones provided in the request body
        # (if the corresponding parameters have not been recovered from the url)
        # This is available in POST/PUT/PATCH methods only
        if request_body:
            # Edit owner_id with the corresponding body content if exist
            if not self.request_ids["owner_id"]:
                self.request_ids["owner_id"] = request_body.get("owner")
            # received a POST/PUT/PATCH for a STAC item or
            # a STAC collection is created
            if len(self.request_ids["collection_ids"]) == 0:
                collections = request_body.get("collections") or request_body.get("id")
                if collections:
                    self.request_ids["collection_ids"] = collections if isinstance(collections, list) else [collections]

            if not self.request_ids["item_id"] and request_body.get("type") == "Feature":
                self.request_ids["item_id"] = request_body.get("id")

        # ---------- Apply specific changes for each endpoint

        if request.method in ("POST", "PUT") and "/search" not in request.scope["path"]:
            # URL: POST / PUT: '/catalog/collections/{USER}:{COLLECTION}'
            # or '/catalog/collections/{USER}:{COLLECTION}/items'
            request_or_response = await self.manage_put_post_request(request)
            if hasattr(request_or_response, "status_code"):  # Unauthorized
                return cast(Response, request_or_response)
            request = request_or_response

        elif request.method == "DELETE":
            if not await self.manage_delete_request(request):
                raise log_http_exception(status_code=HTTP_401_UNAUTHORIZED, detail="Deletion not allowed.")

        elif "/search" in request.scope["path"]:
            # URL: GET: '/catalog/search'
            request_or_response = await self.manage_search_request(request)
            if hasattr(request_or_response, "status_code"):  # Unauthorized
                return cast(Response, request_or_response)
            request = request_or_response

        elif request.method == "GET" and request.scope["path"] == CATALOG_COLLECTIONS:
            # override default pgstac limit of 10 items if not explicitely set
            if "limit" not in request.query_params:
                request = self.override_request_query_string(request, {**request.query_params, "limit": 1000})

        response = await call_next(request)
        return await self.manage_responses(request, cast(StreamingResponse, response))

    async def manage_responses(
        self,
        request: Request,
        streaming_response: StreamingResponse,
    ) -> Response:
        """Manage responses after dispatch"""

        # Don't forward responses that fail.
        # NOTE: the 30x (redirect responses) are used by the oauth2 authentication.
        status_code = streaming_response.status_code
        if status_code not in (HTTP_200_OK, HTTP_201_CREATED, HTTP_302_FOUND, HTTP_307_TEMPORARY_REDIRECT):

            # Read the body. WARNING: after this, the body cannot be read a second time.
            body = [chunk async for chunk in streaming_response.body_iterator]
            response_content = json.loads(b"".join(body).decode())  # type:ignore
            logger.debug("response: %d - %s", streaming_response.status_code, response_content)
            self.clear_catalog_bucket(response_content)

            # GET: '/catalog/queryables' when no collections in the catalog
            if (
                request.method == "GET"
                and request.scope["path"] == CATALOG_PREFIX + QUERYABLES
                and not self.request_ids["collection_ids"]
                and response_content["code"] == "NotFoundError"
            ):
                # Return empty list of properties and additionalProperties set to true on /catalog/queryables
                # when there are no collections in catalog.
                return JSONResponse(
                    {
                        "$id": f"{request.url}",
                        "type": "object",
                        "title": "STAC Queryables.",
                        "$schema": "https://json-schema.org/draft-07/schema#",
                        "properties": {},
                        "additionalProperties": True,
                    },
                    HTTP_200_OK,
                    headers_minus_content_length(streaming_response),
                )

            # Return a regular JSON response instead of StreamingResponse because the body cannot be read again.
            return JSONResponse(response_content, status_code, headers_minus_content_length(streaming_response))

        # Handle responses
        response: Response = streaming_response
        if request.scope["path"] == CATALOG_PREFIX + "/search":
            # GET: '/catalog/search'
            response = await self.manage_search_response(request, streaming_response)
        elif request.method == "GET" and "/download" in request.url.path:
            # URL: GET: '/catalog/collections/{USER}:{COLLECTION}/items/{FEATURE_ID}/download/{ASSET_TYPE}
            response = await self.manage_download_response(request, streaming_response)
        elif request.method == "GET" and (
            self.request_ids["owner_id"]
            or request.scope["path"] in [CATALOG_PREFIX, CATALOG_PREFIX + "/", CATALOG_COLLECTIONS, QUERYABLES]
        ):
            # URL: GET: '/catalog/collections/{USER}:{COLLECTION}'
            # URL: GET: '/catalog/'
            # URL: GET: '/catalog/collections
            response = await self.manage_get_response(request, streaming_response)
        elif request.method in ["POST", "PUT"] and self.request_ids["owner_id"]:
            # URL: POST / PUT: '/catalog/collections/{USER}:{COLLECTION}'
            # or '/catalog/collections/{USER}:{COLLECTION}/items'
            response = await self.manage_put_post_response(request, streaming_response)
        elif request.method == "DELETE" and self.request_ids["owner_id"]:
            response = await self.manage_delete_response(streaming_response, self.request_ids["owner_id"])

        return response

    async def add_authentication_extension(self, content: dict):
        """Add the stac authentication extension, see: https://github.com/stac-extensions/authentication"""

        # Only on cluster mode
        if not common_settings.CLUSTER_MODE:
            return

        # Read environment variables
        oidc_endpoint = os.environ["OIDC_ENDPOINT"]
        oidc_realm = os.environ["OIDC_REALM"]
        oidc_metadata_url = f"{oidc_endpoint}/realms/{oidc_realm}/.well-known/openid-configuration"

        # Add the STAC extension at the root
        extensions = content.setdefault("stac_extensions", [])
        url = "https://stac-extensions.github.io/authentication/v1.1.0/schema.json"
        if url not in extensions:
            extensions.append(url)

        # Add the authentication schemes under the root or "properties" (for the items)
        parent = content
        if content.get("type") == "Feature":
            parent = content.setdefault("properties", {})
        oidc = await oauth2.KEYCLOAK.load_server_metadata()
        parent.setdefault("auth:schemes", {}).update(
            {
                "apikey": {
                    "type": "apiKey",
                    "description": f"API key generated using {os.environ['RSPY_UAC_HOMEPAGE']}"  # link to /docs
                    # add anchor to the "new api key" endpoint
                    "#/Manage%20API%20keys/get_new_api_key_auth_api_key_new_get",
                    "name": "x-api-key",
                    "in": "header",
                },
                "openid": {
                    "type": "openIdConnect",
                    "description": "OpenID Connect",
                    "openIdConnectUrl": oidc_metadata_url,
                },
                "oauth2": {
                    "type": "oauth2",
                    "description": "OAuth2+PKCE Authorization Code Flow",
                    "flows": {
                        "authorizationCode": {
                            "authorizationUrl": oidc["authorization_endpoint"],
                            "tokenUrl": oidc["token_endpoint"],
                            "scopes": {},
                        },
                    },
                },
                "s3": {
                    "type": "s3",
                    "description": "S3",
                },
            },
        )

        # Add the authentication reference to each link and asset
        for link in content.get("links", []):
            link["auth:refs"] = ["apikey", "openid", "oauth2"]
        for asset in list(content.get("assets", {}).values()):
            asset["auth:refs"] = ["s3"]
            if ALTERNATE_STRING in asset:
                asset[ALTERNATE_STRING].update({"auth:refs": ["apikey", "openid", "oauth2"]})
        # Add the extension to the response root and to nested collections, items, ...
        # Do recursive calls to all nested fields, if defined
        for nested_field in ["collections", "features"]:
            for nested_content in content.get(nested_field, []):
                await self.add_authentication_extension(nested_content)
