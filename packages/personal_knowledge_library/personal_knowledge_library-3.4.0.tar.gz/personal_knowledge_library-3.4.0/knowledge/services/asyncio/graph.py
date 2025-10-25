# -*- coding: utf-8 -*-
# Copyright © 2024-present Wacom. All rights reserved.
import asyncio
import gzip
import json
import logging
import os
import urllib
from pathlib import Path
from typing import Any, Optional, List, Dict, Tuple
from urllib.parse import urlparse

import aiohttp
import orjson

from knowledge.base.entity import (
    DATA_PROPERTIES_TAG,
    TYPE_TAG,
    URI_TAG,
    LABELS_TAG,
    IS_MAIN_TAG,
    RELATIONS_TAG,
    LOCALE_TAG,
    EntityStatus,
    Label,
    URIS_TAG,
    FORCE_TAG,
    VISIBILITY_TAG,
    RELATION_TAG,
    TEXT_TAG,
)
from knowledge.base.language import LocaleCode, EN_US
from knowledge.base.ontology import (
    DataProperty,
    OntologyPropertyReference,
    ThingObject,
    OntologyClassReference,
    ObjectProperty,
)
from knowledge.base.response import JobStatus, ErrorLogResponse, NewEntityUrisResponse
from knowledge.nel.base import KnowledgeGraphEntity, EntityType, KnowledgeSource, EntitySource
from knowledge.services import AUTHORIZATION_HEADER_FLAG, IS_OWNER_PARAM, IndexType
from knowledge.services import (
    SUBJECT_URI,
    RELATION_URI,
    OBJECT_URI,
    LANGUAGE_PARAMETER,
    LIMIT,
    LISTING,
    TOTAL_COUNT,
    SEARCH_TERM,
    TYPES_PARAMETER,
    APPLICATION_JSON_HEADER,
    SUBJECT,
    OBJECT,
    PREDICATE,
    LIMIT_PARAMETER,
    ESTIMATE_COUNT,
    TARGET,
    ACTIVATION_TAG,
    SEARCH_PATTERN_PARAMETER,
    LITERAL_PARAMETER,
    VALUE,
    NEXT_PAGE_ID_TAG,
    ENTITIES_TAG,
    RESULT_TAG,
    EXACT_MATCH,
)
from knowledge.services.asyncio.base import AsyncServiceAPIClient, handle_error
from knowledge.services.base import (
    WacomServiceAPIClient,
    WacomServiceException,
    USER_AGENT_HEADER_FLAG,
    CONTENT_TYPE_HEADER_FLAG,
    DEFAULT_TIMEOUT,
    format_exception,
)
from knowledge.services.graph import Visibility, SearchPattern, MIME_TYPE
from knowledge.services.helper import split_updates, entity_payload


# -------------------------------------------- Service API Client ------------------------------------------------------
class AsyncWacomKnowledgeService(AsyncServiceAPIClient):
    """
    AsyncWacomKnowledgeService
    ---------------------
    Client for the Semantic Ink Private knowledge system.

    Operations for entities:
        - Creation of entities
        - Update of entities
        - Deletion of entities
        - Listing of entities

    Parameters
    ----------
    application_name: str
        Name of the application
    service_url: str
        URL of the service
    service_endpoint: str
        Base endpoint
    """

    USER_ENDPOINT: str = "user"
    ENTITY_ENDPOINT: str = "entity"
    ENTITY_BULK_ENDPOINT: str = "entity/bulk"
    ENTITY_IMAGE_ENDPOINT: str = "entity/image/"
    ACTIVATIONS_ENDPOINT: str = "entity/activations"
    LISTING_ENDPOINT: str = "entity/types"
    NAMED_ENTITY_LINKING_ENDPOINT: str = "nel/text"
    RELATION_ENDPOINT: str = "entity/{}/relation"
    RELATIONS_ENDPOINT: str = "entity/{}/relations"
    SEARCH_LABELS_ENDPOINT: str = "semantic-search/labels"
    SEARCH_TYPES_ENDPOINT: str = "semantic-search/types"
    SEARCH_LITERALS_ENDPOINT: str = "semantic-search/literal"
    SEARCH_DESCRIPTION_ENDPOINT: str = "semantic-search/description"
    SEARCH_RELATION_ENDPOINT: str = "semantic-search/relation"
    ONTOLOGY_UPDATE_ENDPOINT: str = "ontology-update"
    IMPORT_ENTITIES_ENDPOINT: str = "import"
    IMPORT_ERROR_LOG_ENDPOINT: str = "import/errorlog"
    MAX_NUMBER_URIS: int = 40

    def __init__(
        self,
        application_name: str,
        service_url: str = WacomServiceAPIClient.SERVICE_URL,
        service_endpoint: str = "graph/v1",
        graceful_shutdown: bool = False,
    ):
        super().__init__(
            application_name=application_name,
            service_url=service_url,
            service_endpoint=service_endpoint,
            graceful_shutdown=graceful_shutdown,
        )

    async def entity(self, uri: str, auth_key: Optional[str] = None) -> ThingObject:
        """
        Retrieve entity information from personal knowledge, using the  URI as identifier.

        **Remark:** Object properties (relations) must be requested separately.

        Parameters
        ----------
        uri: str
            URI of entity
        auth_key: Optional[str]
            Use a different auth key than the one from the client

        Returns
        -------
        thing: ThingObject
            Entities with is type URI, description, an image/icon, and tags (labels).

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code or the entity is not found in the knowledge graph
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{uri}"
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(url, headers=headers, verify_ssl=self.verify_calls) as response:
                if response.ok:
                    e: Dict[str, Any] = await response.json()
                    pref_label: List[Label] = []
                    aliases: List[Label] = []
                    # Extract labels and alias
                    for label in e[LABELS_TAG]:
                        if label[IS_MAIN_TAG]:  # Labels
                            pref_label.append(Label.create_from_dict(label))
                        else:  # Alias
                            aliases.append(Label.create_from_dict(label))
                else:
                    raise await handle_error(
                        f"Retrieving of entity content failed. URI:={uri}.", response, headers=headers
                    )
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)
        # Create ThingObject
        thing: ThingObject = ThingObject.from_dict(e)
        return thing

    async def entities(
        self,
        uris: List[str],
        locale: Optional[LocaleCode] = None,
        auth_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> List[ThingObject]:
        """
        Retrieve entities information from personal knowledge, using the  URI as identifier.

        **Remark:** Object properties (relations) must be requested separately.

        Parameters
        ----------
        uris: List[str]
            List of URIs of the entities
        locale: LocaleCode
            ISO-3166 Country Codes and ISO-639 Language Codes in the format <language_code>_<country>, e.g., en_US.
        auth_key: Optional[str]
            Use a different auth key than the one from the client
        timeout: int
            Timeout in seconds. Default: 10 seconds.

        Returns
        -------
        things: List[ThingObject]
            Entities with is type URI, description, an image/icon, and tags (labels).

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code or the entity is not found in the knowledge graph
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/"
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        things: List[ThingObject] = []

        async with AsyncServiceAPIClient.__async_session__() as session:
            for chunk in range(0, len(uris), AsyncWacomKnowledgeService.MAX_NUMBER_URIS):
                subset = uris[chunk : chunk + AsyncWacomKnowledgeService.MAX_NUMBER_URIS]
                params: Dict[str, Any] = {URIS_TAG: subset}
                if locale:
                    params[LOCALE_TAG] = locale
                async with session.get(
                    url, headers=headers, params=params, timeout=timeout, verify_ssl=self.verify_calls
                ) as response:
                    if response.ok:
                        entities: List[Dict[str, Any]] = await response.json()
                        for e in entities:
                            thing: ThingObject = ThingObject.from_dict(e)
                            things.append(thing)
                    else:
                        raise await handle_error(
                            f"Retrieving of entities content failed. List of URIs: {uris}.", response, headers=headers
                        )
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)
        # Create ThingObject
        return things

    async def set_entity_image_local(self, entity_uri: str, path: Path, auth_key: Optional[str] = None) -> str:
        """Setting the image of the entity.
        The image is stored locally.

        Parameters
        ----------
        entity_uri: str
           URI of the entity.
        path: Path
           The path of image.
        auth_key: Optional[str] [default:=None]
           Auth key from user if not set, the client auth key will be used

        Returns
        -------
        image_id: str
           ID of uploaded image

        Raises
        ------
        WacomServiceException
           If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        with path.open("rb") as fp:
            image_bytes: bytes = fp.read()
            file_name: str = str(path.absolute())
            _, file_extension = os.path.splitext(file_name.lower())
            mime_type = MIME_TYPE[file_extension]
            return await self.set_entity_image(entity_uri, image_bytes, file_name, mime_type, auth_key=auth_key)

    async def set_entity_image_url(
        self,
        entity_uri: str,
        image_url: str,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        auth_key: Optional[str] = None,
    ) -> str:
        """Setting the image of the entity.
        The image for the URL is downloaded and then pushed to the backend.

        Parameters
        ----------
        auth_key: str
            Auth key from user
        entity_uri: str
            URI of the entity.
        image_url: str
            URL of the image.
        file_name: str [default:=None]
            Name of  the file. If None the name is extracted from URL.
        mime_type: str [default:=None]
            Mime type.
        auth_key: Optional[str] [default:=None]
            Auth key from user if not set, the client auth key will be used

        Returns
        -------
        image_id: str
            ID of uploaded image

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        async with AsyncServiceAPIClient.__async_session__() as session:
            headers: Dict[str, str] = {USER_AGENT_HEADER_FLAG: self.user_agent}
            async with session.get(image_url, headers=headers, verify_ssl=self.verify_calls) as response:
                if response.ok:
                    image_bytes: bytes = await response.content.read()
                    file_name: str = image_url if file_name is None else file_name
                    if mime_type is None:
                        _, file_extension = os.path.splitext(file_name.lower())
                        if file_extension not in MIME_TYPE:
                            raise WacomServiceException(
                                "Creation of entity image failed. Mime-type cannot be "
                                "identified or is not supported."
                            )
                        mime_type = MIME_TYPE[file_extension]

                    return await self.set_entity_image(entity_uri, image_bytes, file_name, mime_type, auth_key=auth_key)
            raise await handle_error(f"Creation of entity image failed. URI:={entity_uri}.", response, headers=headers)

    async def set_entity_image(
        self,
        entity_uri: str,
        image_byte: bytes,
        file_name: str = "icon.jpg",
        mime_type: str = "image/jpeg",
        auth_key: Optional[str] = None,
    ) -> str:
        """Setting the image of the entity.
        The image for the URL is downloaded and then pushed to the backend.

        Parameters
        ----------
        entity_uri: str
            URI of the entity.
        image_byte: bytes
            Binary encoded image.
        file_name: str [default:=None]
            Name of  the file. If None the name is extracted from URL.
        mime_type: str [default:=None]
            Mime type.
        auth_key: Optional[str] [default:=None]
            Auth key from user if not set, the client auth key will be used
        Returns
        -------
        image_id: str
            ID of uploaded image

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        headers: dict = {AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        data: aiohttp.FormData = aiohttp.FormData()
        data.add_field("file", image_byte, filename=file_name, content_type=mime_type)
        url: str = f"{self.service_base_url}{self.ENTITY_IMAGE_ENDPOINT}{urllib.parse.quote(entity_uri)}"
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.patch(
                url, headers=headers, data=data, timeout=DEFAULT_TIMEOUT, verify_ssl=self.verify_calls
            ) as response:
                if response.ok:
                    image_id: str = (await response.json(loads=orjson.loads))["imageId"]
                else:
                    raise await handle_error(
                        f"Creation of entity image failed. URI:={entity_uri}.", response, headers=headers
                    )
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)
        return image_id

    async def delete_entities(self, uris: List[str], force: bool = False, auth_key: Optional[str] = None):
        """
        Delete a list of entities.

        Parameters
        ----------
        uris: List[str]
            List of URI of entities. **Remark:** More than 100 entities are not possible in one request
        force: bool
            Force deletion process
        auth_key: Optional[str]
            Use a different auth key than the one from the client

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        ValueError
            If more than 100 entities are given
        """
        if len(uris) > 100:
            raise ValueError("Please delete less than 100 entities.")
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}"
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        params: Dict[str, Any] = {URIS_TAG: uris, FORCE_TAG: str(force)}
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers, params=params, verify_ssl=self.verify_calls) as response:
                if not response.ok:
                    raise await handle_error(
                        "Deletion of entities failed.", response, parameters=params, headers=headers
                    )
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)

    async def delete_entity(self, uri: str, force: bool = False, auth_key: Optional[str] = None):
        """
        Deletes an entity.

        Parameters
        ----------
        uri: str
            URI of entity
        force: bool
            Force deletion process
        auth_key: Optional[str]
            Use a different auth key than the one from the client

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{uri}"
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.delete(
                url, headers=headers, params={FORCE_TAG: str(force)}, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error(f"Deletion of entity failed. URI:={uri}.", response, headers=headers)
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)

    async def exists(self, uri: str) -> bool:
        """
        Check if entity exists in knowledge graph.

        Parameters
        ----------
        uri: str -
            URI for entity

        Returns
        -------
        flag: bool
            Flag if entity does exist
        """
        try:
            obj: ThingObject = await self.entity(uri)
            return obj is not None
        except WacomServiceException:
            return False

    @staticmethod
    async def __entity__(entity: ThingObject):
        return entity_payload(entity)

    async def create_entity_bulk(
        self,
        entities: List[ThingObject],
        batch_size: int = 10,
        ignore_images: bool = False,
        auth_key: Optional[str] = None,
    ) -> List[ThingObject]:
        """
        Creates entity in graph.

        Parameters
        ----------
        entities: List[ThingObject]
            Entities
        batch_size: int
            Batch size
        ignore_images: bool
            Do not automatically upload images
        auth_key: Optional[str]
            If auth key is not set, the client auth key will be used.

        Returns
        -------
        uris: List[ThingObject]
            List of ThingObjects with URI

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_BULK_ENDPOINT}"
        # Header info
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            CONTENT_TYPE_HEADER_FLAG: APPLICATION_JSON_HEADER,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        payload: List[Dict[str, Any]] = [await AsyncWacomKnowledgeService.__entity__(e) for e in entities]
        async with AsyncServiceAPIClient.__async_session__() as session:
            for bulk_idx in range(0, len(entities), batch_size):
                bulk = payload[bulk_idx : bulk_idx + batch_size]

                async with session.post(url, json=bulk, headers=headers, verify_ssl=self.verify_calls) as response:
                    if response.ok:
                        response_dict: Dict[str, Any] = await response.json(loads=orjson.loads)
                        for idx, uri in enumerate(response_dict[URIS_TAG]):
                            entities[bulk_idx + idx].uri = uri
                            if (
                                entities[bulk_idx + idx].image is not None
                                and entities[bulk_idx + idx].image != ""
                                and not ignore_images
                            ):
                                try:
                                    await self.set_entity_image_url(
                                        uri, entities[bulk_idx + idx].image, auth_key=auth_key
                                    )
                                except WacomServiceException as we:
                                    logging.error(
                                        f"Failed to upload image for entity {uri}. " f"{format_exception(we)}"
                                    )
                            entities[bulk_idx + idx].uri = response_dict[URIS_TAG][idx]
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)
        return entities

    async def create_entity(
        self, entity: ThingObject, auth_key: Optional[str] = None, ignore_image: bool = False
    ) -> str:
        """
        Creates entity in graph.

        Parameters
        ----------
        entity: ThingObject
            Entities object that needs to be created
        auth_key: Optional[str]
            Use a different auth key than the one from the client
        ignore_image: bool
            Ignore image.

        Returns
        -------
        uri: str
            URI of entity

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}"
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        # Header info
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            CONTENT_TYPE_HEADER_FLAG: APPLICATION_JSON_HEADER,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        payload: Dict[str, Any] = await AsyncWacomKnowledgeService.__entity__(entity)
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.post(url, json=payload, headers=headers, verify_ssl=self.verify_calls) as response:
                if response.ok and not ignore_image:
                    uri: str = (await response.json(loads=orjson.loads))[URI_TAG]
                    # Set image
                    if entity.image is not None and entity.image.startswith("file:"):
                        p = urlparse(entity.image)
                        await self.set_entity_image_local(uri, Path(p.path), auth_key=auth_key)
                    elif entity.image is not None and entity.image != "":
                        await self.set_entity_image_url(uri, entity.image, auth_key=auth_key)
                if not response.ok:
                    # Handle error
                    raise await handle_error("Creation of entity failed.", response, payload=payload, headers=headers)
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)
        return uri

    async def import_entities(
        self, entities: List[ThingObject], auth_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
    ) -> str:
        """Import entities to the graph.

        Parameters
        ----------
        entities: List[ThingObject]
            List of entities to import.
        auth_key: Optional[str] = None
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        job_id: str
            ID of the job

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        ndjson_lines: List[str] = []
        for obj in entities:
            data_dict = obj.__import_format_dict__()
            ndjson_lines.append(json.dumps(data_dict))  # Convert each dict to a JSON string

        ndjson_content = "\n".join(ndjson_lines)  # Join JSON strings with newline

        # Compress the NDJSON string to a gzip byte array
        compressed_data: bytes = gzip.compress(ndjson_content.encode("utf-8"))
        url: str = f"{self.service_base_url}{self.IMPORT_ENTITIES_ENDPOINT}"
        data: aiohttp.FormData = aiohttp.FormData()
        data.add_field("file", compressed_data, filename="import.njson.gz", content_type="application/x-gzip")
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.post(
                url, headers=headers, data=data, timeout=timeout, verify_ssl=self.verify_calls
            ) as response:
                if response.ok:
                    structure: Dict[str, Any] = await response.json(loads=orjson.loads)
                    return structure["jobId"]
                raise await handle_error("Import endpoint returns an error.", response)

    async def import_entities_from_file(
        self, file_path: Path, auth_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
    ) -> str:
        """Import entities from a file to the graph.

        Parameters
        ----------
        file_path: Path
            Path to the file containing entities in NDJSON format.
        auth_key: Optional[str] = None
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        job_id: str
            ID of the job

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        FileNotFoundError
            If the file path does not exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        with file_path.open("rb") as file:
            # Compress the NDJSON string to a gzip byte array
            compressed_data: bytes = file.read()
            data: aiohttp.FormData = aiohttp.FormData()
            data.add_field("file", compressed_data, filename="import.njson.gz", content_type="application/x-gzip")
            url: str = f"{self.service_base_url}{self.IMPORT_ENTITIES_ENDPOINT}"
            async with AsyncServiceAPIClient.__async_session__() as session:
                async with session.post(
                    url, headers=headers, data=data, timeout=timeout, verify_ssl=self.verify_calls
                ) as response:
                    if response.ok:
                        structure: Dict[str, Any] = await response.json(loads=orjson.loads)
                        return structure["jobId"]
                    raise await handle_error("Import endpoint returns an error.", response)

    async def job_status(
        self, job_id: str, auth_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
    ) -> JobStatus:
        """
        Retrieve the status of the job.

        Parameters
        ----------
        job_id: str
            ID of the job
        auth_key: Optional[str] = None
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        job_status: JobStatus
            Status of the job
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        url: str = f"{self.service_base_url}{self.IMPORT_ENTITIES_ENDPOINT}/{job_id}"
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(url, headers=headers, timeout=timeout, verify_ssl=self.verify_calls) as response:
                if response.ok:
                    structure: Dict[str, Any] = await response.json(loads=orjson.loads)
                    return JobStatus.from_dict(structure)
                raise await handle_error(f"Retrieving job status for {job_id} failed.", response, headers=headers)

    async def import_error_log(
        self,
        job_id: str,
        auth_key: Optional[str] = None,
        next_page_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> ErrorLogResponse:
        """
        Retrieve the error log of the job.

        Parameters
        ----------
        job_id: str
            ID of the job
        next_page_id: Optional[str] = None
            ID of the next page within pagination.
        auth_key: Optional[str] = None
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        error: ErrorLogResponse
            Error log of the job
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        url: str = f"{self.service_base_url}{self.IMPORT_ERROR_LOG_ENDPOINT}/{job_id}"
        params: Dict[str, str] = {NEXT_PAGE_ID_TAG: next_page_id} if next_page_id else {}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url, headers=headers, params=params, timeout=timeout, verify_ssl=self.verify_calls
            ) as response:
                if response.ok:
                    structure: Dict[str, Any] = await response.json(loads=orjson.loads)
                    return ErrorLogResponse.from_dict(structure)
                raise await handle_error(f"Retrieving job status for {job_id} failed.", response)

    async def import_new_uris(
        self,
        job_id: str,
        auth_key: Optional[str] = None,
        next_page_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> NewEntityUrisResponse:
        """
        Retrieve the new entity uris from the job.

        Parameters
        ----------
        job_id: str
            ID of the job
        next_page_id: Optional[str] = None
            ID of the next page within pagination.
        auth_key: Optional[str] = None
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        response: NewEntityUrisResponse
            New entity uris of the job.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        url: str = f"{self.service_base_url}{self.IMPORT_ENTITIES_ENDPOINT}/{job_id}/new-entities"
        params: Dict[str, str] = {NEXT_PAGE_ID_TAG: next_page_id} if next_page_id else {}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url, headers=headers, params=params, timeout=timeout, verify_ssl=self.verify_calls
            ) as response:
                if response.ok:
                    structure: Dict[str, Any] = await response.json(loads=orjson.loads)
                    return NewEntityUrisResponse.from_dict(structure)
                raise await handle_error(f"Retrieving job status for {job_id} failed.", response)

    async def update_entity(self, entity: ThingObject, auth_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Updates entity in graph.

        Parameters
        ----------
        entity: ThingObject
            entity object
        auth_key: Optional[str]
            Use a different auth key than the one from the client
        timeout: int
            Timeout in seconds. Default: 10 seconds.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        uri: str = entity.uri
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{uri}"
        # Header info
        headers: dict = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            CONTENT_TYPE_HEADER_FLAG: APPLICATION_JSON_HEADER,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        payload: Dict[str, Any] = await AsyncWacomKnowledgeService.__entity__(entity)
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.patch(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
                verify_ssl=self.verify_calls,
            ) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Update of entity failed. URI:={uri}.", response, payload=payload, headers=headers
                    )
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)

    async def add_entity_indexes(
        self,
        entity_uri: str,
        targets: List[IndexType],
        auth_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[IndexType, Any]:
        """
        Updates index targets of an entity. The index targets can be set to "NEL", "ElasticSearch", "VectorSearchWord",
        or "VectorSearchDocument".
        If the target is already set for the entity, there will be no changes.

        Parameters
        ----------
        entity_uri: str
            URI of entity
        targets: List[Literal["NEL", "ElasticSearch", "VectorSearchWord", "VectorSearchDocument"]]
            List of indexing targets
        auth_key: Optional[str]
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        update_status: Dict[str, Any]
            Status per target (depending on the targets of entity and the ones set in the request). If the entity
            already has the target set, the status will be "Target already exists" for that target,
            otherwise it will be "UPSERT".

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{entity_uri}/indexes"
        # Header info
        headers: dict = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            CONTENT_TYPE_HEADER_FLAG: APPLICATION_JSON_HEADER,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.patch(
                url, json=targets, headers=headers, timeout=timeout, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Update of entity indexes failed. URI:={entity_uri}.",
                        response,
                        payload={"targets": targets},
                        headers=headers,
                    )
                response_dict: Dict[str, Any] = await response.json(loads=orjson.loads)
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)
        return response_dict

    async def remove_entity_indexes(
        self,
        entity_uri: str,
        targets: List[IndexType],
        auth_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[IndexType, Any]:
        """
        Deletes the search index for a given entity.

        Parameters
        ----------
        entity_uri: str
            URI of entity
        targets: List[Literal["NEL", "ElasticSearch", "VectorSearchWord", "VectorSearchDocument"]]
            List of indexing targets
        auth_key: Optional[str]
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        update_status: Dict[str, Any]
            Status per target (depending on the targets of entity and the ones set in the request), e.g.,
            response will only contain {"NEL: "DELETE"}, if NEL is the only target in the request.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{entity_uri}/indexes"
        # Header info
        headers: dict = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            CONTENT_TYPE_HEADER_FLAG: APPLICATION_JSON_HEADER,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.delete(
                url, json=targets, headers=headers, timeout=timeout, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Deletion of entity indexes failed. URI:={entity_uri}.",
                        response,
                        payload={"targets": targets},
                        headers=headers,
                    )
                response_dict: Dict[str, Any] = await response.json(loads=orjson.loads)
        await asyncio.sleep(0.25 if self.use_graceful_shutdown else 0.0)
        return response_dict

    async def relations(
        self, uri: str, auth_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
    ) -> Dict[OntologyPropertyReference, ObjectProperty]:
        """
        Retrieve the relations (object properties) of an entity.

        Parameters
        ----------
        uri: str
            Entities URI of the source

        auth_key: Optional[str]
            Use a different auth key than the one from the client

        timeout: int
            Request timeout in seconds (default: 60 seconds)

        Returns
        -------
        relations: Dict[OntologyPropertyReference, ObjectProperty]
            All relations a dict

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = (
            f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{urllib.parse.quote(uri)}"
            f"/relations"
        )
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(url, headers=headers, verify_ssl=self.verify_calls, timeout=timeout) as response:
                if response.ok:
                    rel: list = (await response.json(loads=orjson.loads)).get(RELATIONS_TAG)
                else:
                    raise await handle_error(f"Retrieving of relations failed. URI:={uri}.", response, headers=headers)
        # Graceful shutdown to close the session and file descriptor
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return ObjectProperty.create_from_list(rel)

    async def labels(self, uri: str, locale: LocaleCode = EN_US, auth_key: Optional[str] = None) -> List[Label]:
        """
        Extract list labels of entity.

        Parameters
        ----------
        uri: str
            Entities URI of the source
        locale: str
            ISO-3166 Country Codes and ISO-639 Language Codes in the format <language_code>_<country>, e.g., en_US.
        auth_key: Optional[str] = None
            Use a different auth key than the one from the client

        Returns
        -------
        labels: List[Label]
            List of labels of an entity.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{uri}/labels"
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url,
                headers=headers,
                params={
                    LOCALE_TAG: locale,
                },
                verify_ssl=self.verify_calls,
            ) as response:
                if response.ok:
                    labels: list = (await response.json(loads=orjson.loads)).get(LABELS_TAG)
                else:
                    raise await handle_error(f"Failed to pull labels. URI:={uri}.", response, headers=headers)
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return [Label.create_from_dict(label) for label in labels]

    async def literals(
        self, uri: str, locale: LocaleCode = EN_US, auth_key: Optional[str] = None
    ) -> List[DataProperty]:
        """
        Collect all literals of entity.

        Parameters
        ----------
        uri: str
            Entities URI of the source
        locale: LocaleCode [default:=EN_US]
            ISO-3166 Country Codes and ISO-639 Language Codes in the format <language_code>_<country>, e.g., en_US.
        auth_key: Optional[str] [default:=None]
            Use a different auth key than the one from the client
        Returns
        -------
        literals: List[DataProperty]
            List of data properties of an entity.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{uri}/literals"
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url,
                headers=headers,
                params={
                    LOCALE_TAG: locale,
                },
                verify_ssl=self.verify_calls,
            ) as response:
                if response.ok:
                    literals: list = (await response.json(loads=orjson.loads)).get(DATA_PROPERTIES_TAG)
                else:
                    raise await handle_error(f"Failed to pull literals. URI:={uri}.", response, headers=headers)
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return DataProperty.create_from_list(literals)

    async def create_relation(
        self, source: str, relation: OntologyPropertyReference, target: str, auth_key: Optional[str] = None
    ):
        """
        Creates a relation for an entity to a source entity.

        Parameters
        ----------
        source: str
            Entities URI of the source
        relation: OntologyPropertyReference
            ObjectProperty property
        target: str
            Entities URI of the target
        auth_key: Optional[str] [default:=None]
            Use a different auth key than the one from the client

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{source}/relation"
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        params: dict = {RELATION_TAG: relation.iri, TARGET: target}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.post(url, params=params, headers=headers, verify_ssl=self.verify_calls) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Creation of relation failed. URI:={source}.", response, headers=headers, parameters=params
                    )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)

    async def create_relations_bulk(
        self,
        source: str,
        relations: Dict[OntologyPropertyReference, List[str]],
        auth_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Creates all the relations for an entity to a source entity.

        Parameters
        ----------
        source: str
            Entities URI of the source

        relations: Dict[OntologyPropertyReference, List[str]]
            ObjectProperty property and targets mapping.

        auth_key: Optional[str] = None
            If the auth key is set the logged-in user (if any) will be ignored and the auth key will be used.

        timeout: int
            Request timeout in seconds (default: 60 seconds)

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{source}/relations"
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        async with AsyncServiceAPIClient.__async_session__() as session:
            for update_bulk in split_updates(relations):
                async with session.post(
                    url, json=update_bulk, headers=headers, verify_ssl=self.verify_calls, timeout=timeout
                ) as response:
                    if not response.ok:
                        raise await handle_error(
                            f"Creation of relation failed. URI:={source}.",
                            response,
                            headers=headers,
                            parameters=update_bulk,
                        )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)

    async def remove_relation(
        self,
        source: str,
        relation: OntologyPropertyReference,
        target: str,
        auth_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Removes a relation.

        Parameters
        ----------
        source: str
            Entities uri of the source
        relation: OntologyPropertyReference
            ObjectProperty property
        target: str
            Entities uri of the target
        auth_key: Optional[str] [default:=None]
            Use a different auth key than the one from the client
        timeout: int
            Request timeout in seconds (default: 60 seconds)

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ENTITY_ENDPOINT}/{source}/relation"
        params: Dict[str, str] = {RELATION_TAG: relation.iri, TARGET: target}
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.delete(
                url, params=params, headers=headers, timeout=timeout, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Removal of relation failed. URI:={source}.", response, headers=headers, parameters=params
                    )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)

    async def activations(
        self, uris: List[str], depth: int, auth_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
    ) -> Tuple[Dict[str, ThingObject], List[Tuple[str, OntologyPropertyReference, str]]]:
        """
        Spreading activation, retrieving the entities related to an entity.

        Parameters
        ----------
        uris: List[str]
            List of URIS for entity.
        depth: int
            Depth of activations
        auth_key: Optional[str] [default:=None]
            Use a different auth key than the one from the client
        timeout: int
            Request timeout in seconds (default: 60 seconds)

        Returns
        -------
        entity_map: Dict[str, ThingObject]
            Map with entity and its URI as key.
        relations: List[Tuple[str, OntologyPropertyReference, str]]
            List of relations with subject predicate, (Property), and subject

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code, and activation failed.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.ACTIVATIONS_ENDPOINT}"
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        params: dict = {URIS_TAG: uris, ACTIVATION_TAG: depth}

        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url, headers=headers, params=params, verify_ssl=self.verify_calls, timeout=timeout
            ) as response:
                if response.ok:
                    entities: Dict[str, Any] = await response.json(loads=orjson.loads)
                    things: Dict[str, ThingObject] = {
                        e[URI_TAG]: ThingObject.from_dict(e) for e in entities[ENTITIES_TAG]
                    }
                    relations: List[Tuple[str, OntologyPropertyReference, str]] = []
                    for r in entities[RELATIONS_TAG]:
                        relation: OntologyPropertyReference = OntologyPropertyReference.parse(r[PREDICATE])
                        relations.append((r[SUBJECT], relation, r[OBJECT]))
                        if r[SUBJECT] in things:
                            things[r[SUBJECT]].add_relation(ObjectProperty(relation, outgoing=[r[OBJECT]]))
                else:
                    raise await handle_error(
                        f"Activation failed. URIS:={uris}.", response, headers=headers, parameters=params
                    )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return things, relations

    async def listing(
        self,
        filter_type: OntologyClassReference,
        page_id: Optional[str] = None,
        limit: int = 30,
        locale: Optional[LocaleCode] = None,
        visibility: Optional[Visibility] = None,
        is_owner: Optional[bool] = None,
        estimate_count: bool = False,
        auth_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Tuple[List[ThingObject], int, str]:
        """
        List all entities visible to users.

        Parameters
        ----------
        filter_type: OntologyClassReference
            Filtering with entity
        page_id: Optional[str]
            Page id. Start from this page id
        limit: int
            Limit of the returned entities.
        locale: Optional[LocaleCode] [default:=None]
            ISO-3166 Country Codes and ISO-639 Language Codes in the format '<language_code>_<country>', e.g., en_US.
        visibility: Optional[Visibility] [default:=None]
            Filter the entities based on its visibilities
        is_owner: Optional[bool] [default:=None]
            Filter the entities based on its owner
        estimate_count: bool [default:=False]
            Request an estimate of the entities in a tenant.
        auth_key: Optional[str]
            Auth key from user if not set, the client auth key will be used
        timeout: int
            Timeout for the request (default: 60 seconds)

        Returns
        -------
        entities: List[ThingObject]
            List of entities
        estimated_total_number: int
            Number of all entities
        next_page_id: str
            Identifier of the next page

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code
        """
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.LISTING_ENDPOINT}"
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        # Header with auth token
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        # Parameter with filtering and limit
        parameters: Dict[str, str] = {
            TYPE_TAG: filter_type.iri,
            LIMIT_PARAMETER: str(limit),
            ESTIMATE_COUNT: str(estimate_count),
        }
        if is_owner is not None:
            parameters[IS_OWNER_PARAM] = str(is_owner)
        if locale:
            parameters[LOCALE_TAG] = locale
        if visibility:
            parameters[VISIBILITY_TAG] = str(visibility.value)
        # If filtering is configured
        if page_id is not None:
            parameters[NEXT_PAGE_ID_TAG] = page_id
        async with AsyncServiceAPIClient.__async_session__() as session:
            # Send request
            async with session.get(
                url, params=parameters, headers=headers, verify_ssl=self.verify_calls, timeout=timeout
            ) as response:
                # If response is successful
                if response.ok:
                    entities_resp: Dict[str, Any] = await response.json(loads=orjson.loads)
                    next_page_id: str = entities_resp[NEXT_PAGE_ID_TAG]
                    estimated_total_number: int = entities_resp.get(TOTAL_COUNT, 0)
                    entities: List[ThingObject] = []
                    if LISTING in entities_resp:
                        for e in entities_resp[LISTING]:
                            thing: ThingObject = ThingObject.from_dict(e)
                            thing.status_flag = EntityStatus.SYNCED
                            entities.append(thing)
                else:
                    raise await handle_error(
                        f"Failed to list the entities (since:= {page_id}, limit:={limit}). ", response
                    )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return entities, estimated_total_number, next_page_id

    async def ontology_update(self, fix: bool = False, auth_key: Optional[str] = None):
        """
        Update the ontology.

        **Remark:**
        Works for users with role 'TenantAdmin'.

        Parameters
        ----------
        fix: bool [default:=False]
            Fix the ontology if tenant is in inconsistent state.
        auth_key: Optional[str] [default:=None]
            Auth key from user if not set, the client auth key will be used

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code and commit failed.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = (
            f"{self.service_base_url}{AsyncWacomKnowledgeService.ONTOLOGY_UPDATE_ENDPOINT}" f'{"/fix" if fix else ""}'
        )
        # Header with auth token
        headers: dict = {USER_AGENT_HEADER_FLAG: self.user_agent, AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.patch(
                url, headers=headers, timeout=DEFAULT_TIMEOUT, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error("Ontology update failed. ", response, headers=headers)
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)

    async def search_all(
        self,
        search_term: str,
        language_code: LocaleCode,
        types: List[OntologyClassReference],
        limit: int = 30,
        next_page_id: str = None,
        auth_key: Optional[str] = None,
    ) -> Tuple[List[ThingObject], str]:
        """Search term in labels, literals, and description.

        Parameters
        ----------
        search_term: str
            Search term.
        language_code: LocaleCode
            ISO-3166 Country Codes and ISO-639 Language Codes in the format '<language_code>_<country>', e.g., en_US.
        types: List[OntologyClassReference]
            Limits the types for search.
        limit: int  (default:= 30)
            Size of the page for pagination.
        next_page_id: str [default:=None]
            ID of the next page within pagination.
        auth_key: Optional[str] [default:=None]
            Auth key from user if not set, the client auth key will be used

        Returns
        -------
        results: List[ThingObject]
            List of things matching the search term
        next_page_id: str
            ID of the next page.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        parameters: Dict[str, Any] = {
            SEARCH_TERM: search_term,
            LANGUAGE_PARAMETER: language_code,
            TYPES_PARAMETER: [ot.iri for ot in types],
            LIMIT: limit,
        }
        # Only add next page id if it is not None
        if next_page_id is not None:
            parameters[NEXT_PAGE_ID_TAG] = next_page_id
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.SEARCH_TYPES_ENDPOINT}"
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url, headers=headers, params=parameters, timeout=DEFAULT_TIMEOUT, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Search on labels {search_term} failed. ", response, headers=headers, parameters=parameters
                    )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return await AsyncWacomKnowledgeService.__search_results__(await response.json(loads=orjson.loads))

    async def search_labels(
        self,
        search_term: str,
        language_code: LocaleCode,
        exact_match: bool = False,
        limit: int = 30,
        next_page_id: str = None,
        auth_key: Optional[str] = None,
    ) -> Tuple[List[ThingObject], str]:
        """Search for matches in labels.

        Parameters
        ----------
        search_term: str
            Search term.
        language_code: LocaleCode
            ISO-3166 Country Codes and ISO-639 Language Codes in the format '<language_code>_<country>', e.g., en_US.
        exact_match: bool [default:=False]
            Exact match of the search term.
        limit: int  (default:= 30)
            Size of the page for pagination.
        next_page_id: str [default:=None]
            ID of the next page within pagination.
        auth_key: Optional[str] [default:=None]
            Auth key from user if not set, the client auth key will be used

        Returns
        -------
        results: List[ThingObject]
            List of things matching the search term
        next_page_id: str
            ID of the next page.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.SEARCH_LABELS_ENDPOINT}"
        headers: Dict[str, str] = {
            USER_AGENT_HEADER_FLAG: self.user_agent,
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
        }
        parameters: Dict[str, Any] = {
            SEARCH_TERM: search_term,
            LOCALE_TAG: language_code,
            EXACT_MATCH: str(exact_match),
            LIMIT: str(limit),
        }
        # Only add next page id if it is not None
        if next_page_id is not None:
            parameters[NEXT_PAGE_ID_TAG] = next_page_id

        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url, headers=headers, params=parameters, timeout=DEFAULT_TIMEOUT, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Search on labels {search_term} failed. ", response, headers=headers, parameters=parameters
                    )
                entities, next_page_id = await AsyncWacomKnowledgeService.__search_results__(
                    await response.json(loads=orjson.loads)
                )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return entities, next_page_id

    async def search_literal(
        self,
        search_term: str,
        literal: OntologyPropertyReference,
        pattern: SearchPattern = SearchPattern.REGEX,
        language_code: LocaleCode = EN_US,
        limit: int = 30,
        next_page_id: str = None,
        auth_key: Optional[str] = None,
    ) -> Tuple[List[ThingObject], str]:
        """
         Search for matches in literals.

         Parameters
         ----------
         search_term: str
             Search term.
         literal: OntologyPropertyReference
             Literal used for the search
         pattern: SearchPattern (default:= SearchPattern.REGEX)
             Search pattern. The chosen search pattern must fit the type of the entity.
         language_code: LocaleCode
             ISO-3166 Country Codes and ISO-639 Language Codes in the format '<language_code>_<country>', e.g., en_US.
         limit: int (default:= 30)
             Size of the page for pagination.
         next_page_id: str [default:=None]
             ID of the next page within pagination.
         auth_key: Optional[str] [default:=None]
             Auth key from user if not set, the client auth key will be used
         Returns
         -------
         results: List[ThingObject]
            List of things matching the search term
        next_page_id: str
            ID of the next page.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.SEARCH_LITERALS_ENDPOINT}"
        parameters: Dict[str, Any] = {
            VALUE: search_term,
            LITERAL_PARAMETER: literal.iri,
            LANGUAGE_PARAMETER: language_code,
            LIMIT: str(limit),
            SEARCH_PATTERN_PARAMETER: pattern.value,
        }
        # Only add next page id if it is not None
        if next_page_id is not None:
            parameters[NEXT_PAGE_ID_TAG] = next_page_id
        headers: Dict[str, str] = {AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(
                url, headers=headers, params=parameters, timeout=DEFAULT_TIMEOUT, verify_ssl=self.verify_calls
            ) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Search on literals {search_term} failed. ", response, headers=headers, parameters=parameters
                    )
                entities, n_p = await AsyncWacomKnowledgeService.__search_results__(
                    await response.json(loads=orjson.loads)
                )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return entities, n_p

    async def search_relation(
        self,
        relation: OntologyPropertyReference,
        language_code: LocaleCode,
        subject_uri: str = None,
        object_uri: str = None,
        limit: int = 30,
        next_page_id: str = None,
        auth_key: Optional[str] = None,
    ) -> Tuple[List[ThingObject], str]:
        """
         Search for matches in literals.

         Parameters
         ----------
         relation: OntologyPropertyReference
             Search term.
         language_code: LocaleCode
             ISO-3166 Country Codes and ISO-639 Language Codes in the format '<language_code>_<country>', e.g., en_US.
         subject_uri: str [default:=None]
             URI of the subject
         object_uri: str [default:=None]
             URI of the object
         limit: int (default:= 30)
             Size of the page for pagination.
         next_page_id: str [default:=None]
             ID of the next page within pagination.
         auth_key: Optional[str] [default:=None]
             Auth key from user if not set, the client auth key will be used

         Returns
         -------
         results: List[ThingObject]
            List of things matching the search term
         next_page_id: str
            ID of the next page.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.SEARCH_RELATION_ENDPOINT}"
        parameters: Dict[str, Any] = {RELATION_URI: relation.iri, LANGUAGE_PARAMETER: language_code, LIMIT: str(limit)}
        if subject_uri is not None and object_uri is not None:
            raise WacomServiceException("Only one parameter is allowed: either subject_uri or object_uri!")
        if subject_uri is None and object_uri is None:
            raise WacomServiceException("At least one parameters is must be defined: either subject_uri or object_uri!")
        if subject_uri is not None:
            parameters[SUBJECT_URI] = subject_uri
        if object_uri is not None:
            parameters[OBJECT_URI] = object_uri
        # Only add next page id if it is not None
        if next_page_id is not None:
            parameters[NEXT_PAGE_ID_TAG] = next_page_id
        headers: dict = {AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(url, headers=headers, params=parameters, verify_ssl=self.verify_calls) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Search on: subject:={subject_uri}, relation {relation.iri}, "
                        f"object:= {object_uri} failed. ",
                        response,
                        headers=headers,
                        parameters=parameters,
                    )
                entities, n_p = await AsyncWacomKnowledgeService.__search_results__(
                    await response.json(loads=orjson.loads)
                )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return entities, n_p

    async def search_description(
        self,
        search_term: str,
        language_code: LocaleCode,
        limit: int = 30,
        auth_key: Optional[str] = None,
        next_page_id: str = None,
    ) -> Tuple[List[ThingObject], str]:
        """Search for matches in description.

        Parameters
        ----------
        search_term: str
            Search term.
        language_code: LocaleCode
            ISO-3166 Country Codes and ISO-639 Language Codes in the format '<language_code>_<country>', e.g., en_US.
        limit: int  (default:= 30)
            Size of the page for pagination.
        auth_key: Optional[str] [default:=None]
            Auth key from user if not set, the client auth key will be used
        next_page_id: str [default:=None]
            ID of the next page within pagination.

        Returns
        -------
        results: List[ThingObject]
            List of things matching the search term
        next_page_id: str
            ID of the next page.

        Raises
        ------
        WacomServiceException
            If the graph service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        url: str = f"{self.service_base_url}{AsyncWacomKnowledgeService.SEARCH_DESCRIPTION_ENDPOINT}"
        parameters: Dict[str, Any] = {SEARCH_TERM: search_term, LOCALE_TAG: language_code, LIMIT: str(limit)}
        # Only add next page id if it is not None
        if next_page_id is not None:
            parameters[NEXT_PAGE_ID_TAG] = next_page_id
        headers: dict = {AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}"}
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.get(url, headers=headers, params=parameters, verify_ssl=self.verify_calls) as response:
                if not response.ok:
                    raise await handle_error(
                        f"Search on descriptions {search_term} failed. ",
                        response,
                        headers=headers,
                        parameters=parameters,
                    )
                entities, n_p = await AsyncWacomKnowledgeService.__search_results__(
                    await response.json(loads=orjson.loads)
                )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return entities, n_p

    @staticmethod
    async def __search_results__(response: Dict[str, Any]) -> Tuple[List[ThingObject], str]:
        results: List[ThingObject] = []
        for elem in response[RESULT_TAG]:
            results.append(ThingObject.from_dict(elem))
        return results, response[NEXT_PAGE_ID_TAG]

    async def link_personal_entities(
        self, text: str, language_code: LocaleCode = EN_US, auth_key: Optional[str] = None
    ) -> List[KnowledgeGraphEntity]:
        """
        Performs Named Entities Linking on a text. It only finds entities which are accessible by the user identified by
        the auth key.

        Parameters
        ----------
        auth_key: str
            Auth key identifying a user within the Wacom personal knowledge service.
        text: str
            Text where the entities shall be tagged in.
        language_code: LocaleCode
            ISO-3166 Country Codes and ISO-639 Language Codes in the format '<language_code>_<country>', e.g., 'en_US'.

        Returns
        -------
        entities: List[KnowledgeGraphEntity]
            List of knowledge graph entities.

        Raises
        ------
        WacomServiceException
            If the Named Entities Linking service returns an error code.
        """
        if auth_key is None:
            auth_key, _ = await self.handle_token()
        named_entities: List[KnowledgeGraphEntity] = []
        url: str = f"{self.service_base_url}{self.NAMED_ENTITY_LINKING_ENDPOINT}"
        headers: Dict[str, str] = {
            AUTHORIZATION_HEADER_FLAG: f"Bearer {auth_key}",
            USER_AGENT_HEADER_FLAG: self.user_agent,
            CONTENT_TYPE_HEADER_FLAG: APPLICATION_JSON_HEADER,
        }
        payload: Dict[str, str] = {LOCALE_TAG: language_code, TEXT_TAG: text}

        # Create a session and mount the retry adapter
        async with AsyncServiceAPIClient.__async_session__() as session:
            async with session.post(url, headers=headers, json=payload, verify_ssl=self.verify_calls) as response:
                if response.ok:
                    results: dict = await response.json(loads=orjson.loads)
                    for e in results:
                        entity_types: List[str] = []
                        # --------------------------- Entities content ---------------------------------------------------
                        source: Optional[EntitySource] = None
                        if "uri" in e:
                            source = EntitySource(e["uri"], KnowledgeSource.WACOM_KNOWLEDGE)
                        # --------------------------- Ontology types ---------------------------------------------------
                        if "type" in e:
                            entity_types.append(e["type"])
                        # ----------------------------------------------------------------------------------------------
                        start: int = e["startPosition"]
                        end: int = e["endPosition"]
                        ne: KnowledgeGraphEntity = KnowledgeGraphEntity(
                            ref_text=text[start : end + 1],
                            start_idx=start,
                            end_idx=end,
                            label=e["value"],
                            confidence=0.0,
                            source=source,
                            content_link="",
                            ontology_types=entity_types,
                            entity_type=EntityType.PERSONAL_ENTITY,
                            tokens=e.get("tokens"),
                            token_indexes=e.get("tokenIndexes"),
                        )
                        ne.relevant_type = OntologyClassReference.parse(e["type"])
                        named_entities.append(ne)
                else:
                    raise await handle_error(
                        f"Named entity linking for text:={text}@{language_code} failed. ",
                        response,
                        headers=headers,
                        parameters=payload,
                    )
        await asyncio.sleep(0.250 if self.use_graceful_shutdown else 0)
        return named_entities
