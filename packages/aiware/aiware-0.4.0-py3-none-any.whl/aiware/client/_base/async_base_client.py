import enum
import json
from typing import IO, TYPE_CHECKING, Any, AsyncIterator, Optional, TypeVar, cast, Self
from uuid import uuid4
from urllib.parse import urljoin
import posixpath

import httpx
from pydantic import BaseModel
from pydantic_core import to_jsonable_python

from aiware.common.auth import AbstractTokenAuth

from .base_model import UNSET, Upload
from .exceptions import (
    GraphQLClientGraphQLMultiError,
    GraphQLClientHttpError,
    GraphQLClientInvalidMessageFormat,
    GraphQLClientInvalidResponseError,
)

if TYPE_CHECKING:
    from .base_client import _BaseClient

try:
    from websockets.client import ( # pyright: ignore[reportMissingImports]
        WebSocketClientProtocol,
        connect as ws_connect,
    )
    from websockets.typing import ( # pyright: ignore[reportMissingImports]
        Data,
        Origin,
        Subprotocol,
    )
except ImportError:
    from contextlib import asynccontextmanager

    @asynccontextmanager 
    async def ws_connect(*args, **kwargs):  # pylint: disable=unused-argument
        raise NotImplementedError("Subscriptions require 'websockets' package.")
        yield  # pylint: disable=unreachable

    WebSocketClientProtocol = Any
    Data = Any
    Origin = Any

    def Subprotocol(*args, **kwargs):  # pylint: disable=invalid-name
        raise NotImplementedError("Subscriptions require 'websockets' package.")


GRAPHQL_TRANSPORT_WS = "graphql-transport-ws"


class GraphQLTransportWSMessageType(str, enum.Enum):
    CONNECTION_INIT = "connection_init"
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    NEXT = "next"
    ERROR = "error"
    COMPLETE = "complete"


class _AsyncBaseClient:
    def __init__(
        self,
        base_url: str,
        auth: Optional[AbstractTokenAuth] = None,
        *,
        headers: Optional[dict[str, str]] = None,
        graphql_url: str | None = None,
        search_url: str | None = None,
        graphql_ws_url: str | None = None,
        ws_headers: Optional[dict[str, Any]] = None,
        ws_origin: Optional[str] = None,
        ws_connection_init_payload: Optional[dict[str, Any]] = None,
    ) -> None:
        self.base_url: str = base_url.replace("/v3/graphql", "")
        self._graphql_url: str | None = graphql_url
        self._search_url: str | None = search_url

        self.auth: AbstractTokenAuth | None = auth
        self.headers: dict[str, str] | None = headers
        self.http_client: httpx.AsyncClient = httpx.AsyncClient(headers=headers, auth=auth)

        self._graphql_ws_url: str | None = graphql_ws_url
        self.ws_headers: dict[str, str] = ws_headers or {}
        self.ws_origin: Origin | None = Origin(ws_origin) if ws_origin else None # pyright: ignore[reportCallIssue, reportInvalidTypeForm]
        self.ws_connection_init_payload: dict[str, Any] | None = ws_connection_init_payload

    @property
    def graphql_url(self) -> str:
        return self._graphql_url or urljoin(self.base_url, "v3/graphql")

    @property
    def search_url(self) -> str:
        return self._search_url or urljoin(self.base_url, "api/search")

    @property
    def graphql_ws_url(self) -> str:
        return self._graphql_ws_url or self.graphql_url.replace("http", "ws")

    def with_auth(self, auth: Optional[AbstractTokenAuth]) -> Self:
        return self.__class__(  # pyright: ignore[reportReturnType]
            # original inputs
            base_url=self.base_url,
            graphql_url=self._graphql_url,
            search_url=self._search_url,
            graphql_ws_url=self._graphql_ws_url,
            ws_headers=self.ws_headers,
            ws_origin=self.ws_origin,
            ws_connection_init_payload=self.ws_connection_init_payload,

            # overridden auth
            auth=auth
        )

    @classmethod
    def extend_async(cls, client: "_AsyncBaseClient") -> Self:
        return cls(
            base_url=client.base_url,
            graphql_url=client._graphql_url,
            search_url=client._search_url,
            graphql_ws_url=client._graphql_ws_url,
            ws_headers=client.ws_headers,
            ws_origin=client.ws_origin,
            ws_connection_init_payload=client.ws_connection_init_payload,
            auth=client.auth
        )

    @classmethod
    def extend(cls, client: "_BaseClient") -> Self:
        return cls(
            base_url=client.base_url,
            graphql_url=client._graphql_url,
            search_url=client._search_url,
            ws_headers=client.headers,
            auth=client.auth
        )

    async def __aenter__(self: Self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        await self.http_client.aclose()

    async def execute(
        self,
        query: str,
        operation_name: Optional[str] = None,
        variables: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        processed_variables, files, files_map = self._process_variables(variables)

        if files and files_map:
            return await self._execute_multipart(
                query=query,
                operation_name=operation_name,
                variables=processed_variables,
                files=files,
                files_map=files_map,
                **kwargs,
            )

        return await self._execute_json(
            query=query,
            operation_name=operation_name,
            variables=processed_variables,
            **kwargs,
        )

    def get_data(self, response: httpx.Response) -> dict[str, Any]:
        if not response.is_success:
            raise GraphQLClientHttpError(
                status_code=response.status_code, response=response
            )

        try:
            response_json = response.json()
        except ValueError as exc:
            raise GraphQLClientInvalidResponseError(response=response) from exc

        if (not isinstance(response_json, dict)) or (
            "data" not in response_json and "errors" not in response_json
        ):
            raise GraphQLClientInvalidResponseError(response=response)

        data = response_json.get("data")
        errors = response_json.get("errors")

        if errors:
            raise GraphQLClientGraphQLMultiError.from_errors_dicts(
                errors_dicts=errors, data=data
            )

        return cast(dict[str, Any], data)

    async def execute_ws(
        self,
        query: str,
        operation_name: Optional[str] = None,
        variables: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        headers = self.ws_headers.copy()
        headers.update(kwargs.get("extra_headers", {}))

        merged_kwargs: dict[str, Any] = {"origin": self.ws_origin}
        merged_kwargs.update(kwargs)
        merged_kwargs["extra_headers"] = headers

        operation_id = str(uuid4())
        async with ws_connect(
            self.graphql_ws_url,
            subprotocols=[Subprotocol(GRAPHQL_TRANSPORT_WS)],
            **merged_kwargs,
        ) as websocket:
            await self._send_connection_init(websocket)
            # wait for connection_ack from server
            await self._handle_ws_message(
                await websocket.recv(),  # pyright: ignore[reportUnknownArgumentType, reportGeneralTypeIssues]
                websocket,
                expected_type=GraphQLTransportWSMessageType.CONNECTION_ACK,
            )
            await self._send_subscribe(
                websocket,
                operation_id=operation_id,
                query=query,
                operation_name=operation_name,
                variables=variables,
            )

            async for message in websocket: # pyright: ignore[reportGeneralTypeIssues]
                data = await self._handle_ws_message(message, websocket)
                if data:
                    yield data

    def _process_variables(
        self, variables: Optional[dict[str, Any]]
    ) -> tuple[
        dict[str, Any], dict[str, tuple[str, IO[bytes], str]], dict[str, list[str]]
    ]:
        if not variables:
            return {}, {}, {}

        serializable_variables = self._convert_dict_to_json_serializable(variables)
        return self._get_files_from_variables(serializable_variables)

    def _convert_dict_to_json_serializable(
        self, dict_: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            key: self._convert_value(value)
            for key, value in dict_.items()
            if value is not UNSET
        }

    def _convert_value(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(by_alias=True, exclude_unset=True)
        if isinstance(value, list):
            return [self._convert_value(item) for item in value]
        return value

    def _get_files_from_variables(
        self, variables: dict[str, Any]
    ) -> tuple[
        dict[str, Any], dict[str, tuple[str, IO[bytes], str]], dict[str, list[str]]
    ]:
        files_map: dict[str, list[str]] = {}
        files_list: list[Upload] = []

        def separate_files(path: str, obj: Any) -> Any:
            if isinstance(obj, list):
                nulled_list = []
                for index, value in enumerate(obj):
                    value = separate_files(f"{path}.{index}", value)
                    nulled_list.append(value)
                return nulled_list

            if isinstance(obj, dict):
                nulled_dict = {}
                for key, value in obj.items():
                    value = separate_files(f"{path}.{key}", value)
                    nulled_dict[key] = value
                return nulled_dict

            if isinstance(obj, Upload):
                if obj in files_list:
                    file_index = files_list.index(obj)
                    files_map[str(file_index)].append(path)
                else:
                    file_index = len(files_list)
                    files_list.append(obj)
                    files_map[str(file_index)] = [path]
                return None

            return obj

        nulled_variables = separate_files("variables", variables)
        files: dict[str, tuple[str, IO[bytes], str]] = {
            str(i): (file_.filename, cast(IO[bytes], file_.content), file_.content_type)  # pyright: ignore[reportInvalidCast]
            for i, file_ in enumerate(files_list)
        }
        return nulled_variables, files, files_map

    async def _execute_multipart(
        self,
        query: str,
        operation_name: Optional[str],
        variables: dict[str, Any],
        files: dict[str, tuple[str, IO[bytes], str]],
        files_map: dict[str, list[str]],
        **kwargs: Any,
    ) -> httpx.Response:
        data = {
            "operations": json.dumps(
                {
                    "query": query,
                    "operationName": operation_name,
                    "variables": variables,
                },
                default=to_jsonable_python,
            ),
            "map": json.dumps(files_map, default=to_jsonable_python),
        }

        return await self.http_client.post(
            url=self.graphql_url, data=data, files=files, **kwargs
        )

    async def _execute_json(
        self,
        query: str,
        operation_name: Optional[str],
        variables: dict[str, Any],
        **kwargs: Any,
    ) -> httpx.Response:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        headers.update(kwargs.get("headers", {}))

        merged_kwargs: dict[str, Any] = kwargs.copy()
        merged_kwargs["headers"] = headers

        return await self.http_client.post(
            url=self.graphql_url,
            content=json.dumps(
                {
                    "query": query,
                    "operationName": operation_name,
                    "variables": variables,
                },
                default=to_jsonable_python,
            ),
            **merged_kwargs,
        )

    async def _send_connection_init(self, websocket: WebSocketClientProtocol) -> None:  # pyright: ignore[reportInvalidTypeForm]
        payload: dict[str, Any] = {
            "type": GraphQLTransportWSMessageType.CONNECTION_INIT.value
        }
        if self.ws_connection_init_payload:
            payload["payload"] = self.ws_connection_init_payload
        await websocket.send(json.dumps(payload))

    async def _send_subscribe(
        self,
        websocket: WebSocketClientProtocol,  # pyright: ignore[reportInvalidTypeForm]
        operation_id: str,
        query: str,
        operation_name: Optional[str] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> None:
        payload: dict[str, Any] = {
            "id": operation_id,
            "type": GraphQLTransportWSMessageType.SUBSCRIBE.value,
            "payload": {"query": query, "operationName": operation_name},
        }
        if variables:
            payload["payload"]["variables"] = self._convert_dict_to_json_serializable(
                variables
            )
        await websocket.send(json.dumps(payload))

    async def _handle_ws_message(
        self,
        message: Data,  # pyright: ignore[reportInvalidTypeForm]
        websocket: WebSocketClientProtocol,  # pyright: ignore[reportInvalidTypeForm]
        expected_type: Optional[GraphQLTransportWSMessageType] = None,
    ) -> Optional[dict[str, Any]]:
        try:
            message_dict = json.loads(message)
        except json.JSONDecodeError as exc:
            raise GraphQLClientInvalidMessageFormat(message=message) from exc

        type_ = message_dict.get("type")
        payload = message_dict.get("payload", {})

        if not type_ or type_ not in {t.value for t in GraphQLTransportWSMessageType}:
            raise GraphQLClientInvalidMessageFormat(message=message)

        if expected_type and expected_type != type_:
            raise GraphQLClientInvalidMessageFormat(
                f"Invalid message received. Expected: {expected_type.value}"
            )

        if type_ == GraphQLTransportWSMessageType.NEXT:
            if "data" not in payload:
                raise GraphQLClientInvalidMessageFormat(message=message)
            return cast(dict[str, Any], payload["data"])

        if type_ == GraphQLTransportWSMessageType.COMPLETE:
            await websocket.close()
        elif type_ == GraphQLTransportWSMessageType.PING:
            await websocket.send(
                json.dumps({"type": GraphQLTransportWSMessageType.PONG.value})
            )
        elif type_ == GraphQLTransportWSMessageType.ERROR:
            raise GraphQLClientGraphQLMultiError.from_errors_dicts(
                errors_dicts=payload, data=message_dict
            )

        return None

    def _search_path(self, subpath: str) -> str:
        return posixpath.join(self.search_url, subpath)
