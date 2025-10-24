import json
from typing import IO, TYPE_CHECKING, Any, Optional, Self, cast
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
    GraphQLClientInvalidResponseError,
)

if TYPE_CHECKING:
    from .async_base_client import _AsyncBaseClient

class _BaseClient:
    def __init__(
        self,
        base_url: str,
        auth: Optional[AbstractTokenAuth] = None,
        *,
        headers: Optional[dict[str, str]] = None,
        graphql_url: str | None = None,
        search_url: str | None = None,
    ) -> None:
        self.base_url: str = base_url.replace("/v3/graphql", "")
        self._graphql_url: str | None = graphql_url
        self._search_url: str | None = search_url

        self.auth: AbstractTokenAuth | None = auth
        self.headers: dict[str, str] | None = headers
        self.http_client: httpx.Client = httpx.Client(headers=headers, auth=auth)

    @property
    def graphql_url(self) -> str:
        return self._graphql_url or urljoin(self.base_url, "v3/graphql")

    @property
    def search_url(self) -> str:
        return self._search_url or urljoin(self.base_url, "api/search")

    def with_auth(self, auth: Optional[AbstractTokenAuth]) -> Self:
        return self.__class__(  # pyright: ignore[reportReturnType]
            # original inputs
            base_url=self.base_url,
            graphql_url=self._graphql_url,
            search_url=self._search_url,
            headers=self.headers,

            # overridden auth
            auth=auth
        )

    @classmethod
    def extend_async(cls, client: "_AsyncBaseClient") -> Self:
        return cls(
            base_url=client.base_url,
            graphql_url=client._graphql_url,
            search_url=client._search_url,
            headers=client.ws_headers,
            auth=client.auth
        )

    @classmethod
    def extend(cls, client: "_BaseClient") -> Self:
        return cls(
            base_url=client.base_url,
            graphql_url=client._graphql_url,
            search_url=client._search_url,
            headers=client.headers,
            auth=client.auth
        )

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        self.http_client.close()

    def execute(
        self,
        query: str,
        operation_name: Optional[str] = None,
        variables: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        processed_variables, files, files_map = self._process_variables(variables)

        if files and files_map:
            return self._execute_multipart(
                query=query,
                operation_name=operation_name,
                variables=processed_variables,
                files=files,
                files_map=files_map,
                **kwargs,
            )

        return self._execute_json(
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

    def _execute_multipart(
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

        return self.http_client.post(url=self.graphql_url, data=data, files=files, **kwargs)

    def _execute_json(
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

        return self.http_client.post(
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

    def _search_path(self, subpath: str) -> str:
        return posixpath.join(self.search_url, subpath)
