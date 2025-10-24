from typing import Any, Optional, override

import httpx


class GraphQLClientError(Exception):
    """Base exception."""


class GraphQLClientHttpError(GraphQLClientError):
    def __init__(self, status_code: int, response: httpx.Response) -> None:  # pyright: ignore[reportMissingSuperCall]
        self.status_code = status_code
        self.response = response

    @override
    def __str__(self) -> str:
        return f"HTTP status code: {self.status_code}"


class GraphQLClientInvalidResponseError(GraphQLClientError):
    def __init__(self, response: httpx.Response) -> None:  # pyright: ignore[reportMissingSuperCall]
        self.response = response

    @override
    def __str__(self) -> str:
        return "Invalid response format."


class GraphQLClientGraphQLError(GraphQLClientError):
    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        message: str,
        locations: Optional[list[dict[str, int]]] = None,
        path: Optional[list[str]] = None,
        extensions: Optional[dict[str, object]] = None,
        orginal: Optional[dict[str, object]] = None,
    ):
        self.message = message
        self.locations = locations
        self.path = path
        self.extensions = extensions
        self.orginal = orginal

    @override
    def __str__(self) -> str:
        return self.message

    @classmethod
    def from_dict(cls, error: dict[str, Any]) -> "GraphQLClientGraphQLError":
        return cls(
            message=error["message"],
            locations=error.get("locations"),
            path=error.get("path"),
            extensions=error.get("extensions"),
            orginal=error,
        )


class GraphQLClientGraphQLMultiError(GraphQLClientError):
    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        errors: list[GraphQLClientGraphQLError],
        data: Optional[dict[str, Any]] = None,
    ):
        self.errors = errors
        self.data = data

    @override
    def __str__(self) -> str:
        return "; ".join(str(e) for e in self.errors)

    @classmethod
    def from_errors_dicts(
        cls, errors_dicts: list[dict[str, Any]], data: Optional[dict[str, Any]] = None
    ) -> "GraphQLClientGraphQLMultiError":
        return cls(
            errors=[GraphQLClientGraphQLError.from_dict(e) for e in errors_dicts],
            data=data,
        )


class GraphQLClientInvalidMessageFormat(GraphQLClientError):
    def __init__(self, message: str | bytes) -> None:  # pyright: ignore[reportMissingSuperCall]
        self.message = message

    @override
    def __str__(self) -> str:
        return "Invalid message format."
