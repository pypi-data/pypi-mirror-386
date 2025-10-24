import asyncio
import json
from pathlib import Path
from datamodel_code_generator import DataModelType, DatetimeClassType, InputFileType, PythonVersion, generate
import requests

from aiware._internal.utils import get_relative_path

async def cli():
    output = Path(get_relative_path(f"client/_client_generated/search_types.py"))
        
    schema_res = requests.get("https://api.us-1.veritone.com/v1/search/search/core-search-server/api-docs.json")
    schema_res.raise_for_status()  # Raises an HTTPError for bad responses
        
    schema_json = json.loads(schema_res.text.replace("\"format\":\"date\"", "\"format\":\"date-time\""))

    generate(
        json.dumps(schema_json),
        input_file_type=InputFileType.OpenAPI,
        output=output,
        # set up the output model types
        output_model_type=DataModelType.PydanticV2BaseModel,
        target_python_version=PythonVersion.PY_312,
        field_constraints=True,
        use_annotated=True,
        use_standard_collections=True,
        use_union_operator=True,
        # specific overrides
        parent_scoped_naming=True,
        base_class="aiware.common.schemas.BaseSchema",
        output_datetime_class=DatetimeClassType.Datetime,
        disable_timestamp=True,
    )

if __name__ == "__main__":
    asyncio.run(cli())
