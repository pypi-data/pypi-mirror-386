from pydantic import Field
from aiware.client._stdlib_generated.search_types import SearchResultsPage
from aiware.client.search_models import SdoSliceSearchResult
from aiware.common.sdo import TypedSDO
from aiware.client._stdlib_generated.fragments import SDOPage

from aiware.common.schemas import BaseSchema
from aiware.common.utils import not_none


class TypedSDOPage[T: BaseSchema](SDOPage):
    records: list[TypedSDO[T]]  # pyright: ignore[reportIncompatibleVariableOverride]
    count: int  # pyright: ignore[reportIncompatibleVariableOverride]

    @staticmethod
    def from_sdo_page[S: BaseSchema](
        schema_cls: type[S], sdo_page: SDOPage
    ) -> "TypedSDOPage[S]":
        return TypedSDOPage[S](
            records=[
                TypedSDO.from_json(
                    schema_cls,
                    schema_id=not_none(record).schemaId,
                    json_data=not_none(record),
                )
                for record in not_none(sdo_page.records)
            ],
            count=sdo_page.count or 0,
            offset=sdo_page.offset,
            limit=sdo_page.limit
        )

class TypedSdoSliceSearchResult[T: BaseSchema](SearchResultsPage):
    results: list[TypedSDO[T]] = Field(default_factory=lambda: [])

    @staticmethod
    def from_sdo_search_result[S: BaseSchema](
        schema_cls: type[S], schema_id: str, search_result: SdoSliceSearchResult
    ) -> "TypedSdoSliceSearchResult[S]":
        search_result_dict = search_result.model_dump(
            mode="python"
        )
        search_result_dict.pop("results", [])

        return TypedSdoSliceSearchResult.model_validate(
            {
                **search_result_dict,
                "results": [
                    TypedSDO.from_json(
                        schema_cls=schema_cls, schema_id=schema_id, json_data=result
                    )
                    for result in search_result.results or []
                ],
            }
        )
