from typing import Annotated, Any, Optional, cast

from pydantic import Field
from aiware.client._stdlib_generated.async_client import _StdlibGeneratedAsyncAiware

from aiware.common.schemas import BaseSchema
from aiware.common.sdo import TypedSDO
from aiware.client.sdo import TypedSDOPage, TypedSdoSliceSearchResult
from aiware.client._stdlib_generated.base_model_ref import UNSET, UnsetType
from aiware.client.utils import acatch_not_found
from aiware.common.utils import not_none
from aiware.client.search_models import SdoSliceSearchResult, SearchRequestFilter, SearchSDOsRequest, VectorSearchRequest, SearchRequest, SliceSearchResult, VectorSearchResults

class AsyncAiware(_StdlibGeneratedAsyncAiware):
    async def get_typed_sdo[S: BaseSchema](
        self, schema_cls: type[S], schema_id: str, id: str
    ) -> Optional[TypedSDO[S]]:
        sdo_res = await acatch_not_found(
            self._get_sdo(id=id, schemaId=schema_id)
        )

        if sdo_res is None:
            return None

        return TypedSDO.from_json(
            schema_cls=schema_cls,
            schema_id=schema_id,
            json_data=not_none(sdo_res.structuredDataObject),
        )

    async def get_typed_sdos[S: BaseSchema](
        self,
        schema_cls: type[S],
        schema_id: str,
        limit: Optional[int] | UnsetType = UNSET,
        offset: Optional[int] | UnsetType = UNSET,
    ) -> TypedSDOPage[S]:
        sdos_res = await self._get_sd_os(
            schemaId=schema_id, limit=limit, offset=offset
        )

        sdos_page = not_none(sdos_res.structuredDataObjects)

        return TypedSDOPage.from_sdo_page(schema_cls, sdos_page)

    async def get_typed_sdos_by_ids[S: BaseSchema](
        self,
        schema_cls: type[S],
        schema_id: str,
        ids: list[str],
    ) -> dict[str, TypedSDO[S]]:
        sdos: dict[str, TypedSDO[S]] = {}

        if len(ids) == 0:
            return sdos

        # FIXME: paginate

        sdos_res = await self._get_sd_os(
            schemaId=schema_id, ids=ids, limit=len(ids)
        )

        sdos_page = not_none(sdos_res.structuredDataObjects)

        for sdo_ in not_none(sdos_page.records):
            sdo = not_none(sdo_)
            sdos[sdo.id] = TypedSDO.from_json(
                schema_cls, schema_id=schema_id, json_data=sdo
            )

        return sdos

    async def create_typed_sdo[S: BaseSchema](
        self,
        schema_cls: type[S],
        schema_id: str,
        id: str,
        sdo_data: S,
        *,
        exclude_unset: bool = False,
        exclude_none: bool = False
    ):
        create_res = await self._create_sdo(
            schemaId=schema_id, id=id, data=sdo_data.dump_sdo(exclude_unset=exclude_unset, exclude_none=exclude_none)
        )

        return TypedSDO.from_json(
            schema_cls=schema_cls,
            schema_id=schema_id,
            json_data=not_none(create_res.createStructuredData),
        )

    async def upsert_typed_sdo[S: BaseSchema](
        self, sdo: TypedSDO[S],
        *,
        exclude_unset: bool = False,
        exclude_none: bool = False
    ) -> TypedSDO[S]:
        await self._update_sdo(
            schemaId=sdo.schemaId, id=sdo.id, data=sdo.data.dump_sdo(exclude_unset=exclude_unset, exclude_none=exclude_none)
        )

        return TypedSDO(
            schema_cls=sdo.schema_cls,
            schemaId=sdo.schemaId,
            id=sdo.id,
            createdDateTime=sdo.createdDateTime,
            modifiedDateTime=sdo.modifiedDateTime,
            data=sdo.data, # preserve reference
        )

    async def search_media(self, request: SearchRequest) -> SliceSearchResult:
        data = request.model_dump(mode='json', exclude_unset=True)
        response = await self.http_client.post(self._search_path(""), json=data)
        response.raise_for_status()

        return SliceSearchResult.model_validate_json(response.text)

    async def search_sdos(self, request: SearchSDOsRequest) -> SdoSliceSearchResult:
        return (await self.search_media(request=cast(SearchRequest, cast(object, request)))).as_model(SdoSliceSearchResult)

    async def vector_search(self, request: VectorSearchRequest) -> VectorSearchResults:
        data = request.model_dump(mode='json', exclude_unset=True)
        response = await self.http_client.post(self._search_path("vector"), json=data)
        response.raise_for_status()

        return VectorSearchResults.model_validate_json(response.text)
    
    async def search_typed_sdos[S: BaseSchema](
        self,
        schema_cls: type[S],
        schema_id: str,
        query: SearchRequestFilter,
        sort: Annotated[
            Optional[list[dict[str, Any]]],
            Field(
                description="See https://github.com/veritone/core-search-server#sort-statements."
            ),
        ] = None,
        offset: Annotated[
            Optional[float],
            Field(
                description="Used for paging, indicates the zero-base index of the first result. If not provided, defaults to 0."
            ),
        ] = None,
        limit: Annotated[
            Optional[float],
            Field(
                description="Maximum of results to return. Cannot exceed 100. Defaults to 10."
            ),
        ] = None,
    ) -> TypedSdoSliceSearchResult[S]:
        untyped_search_result = await self.search_sdos(
            SearchSDOsRequest(
                index=["mine"],
                type=schema_id,
                query=query,
                sort=sort,
                offset=offset,
                limit=limit,
            )
        )

        return TypedSdoSliceSearchResult.from_sdo_search_result(
            schema_cls=schema_cls, schema_id=schema_id, search_result=untyped_search_result
        )
