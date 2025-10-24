import ast
import asyncio
from dataclasses import dataclass
import dataclasses
import os
from pathlib import Path
from urllib.parse import urljoin
import ariadne_codegen.config
from ariadne_codegen.client_generators.scalars import ScalarData
from ariadne_codegen.settings import ClientSettings
import ariadne_codegen.client_generators.constants

from aiware._internal.utils import get_package_root

@dataclass
class AiwareClientGeneratorSettings(ClientSettings):
    base_url: str = "https://api.us-1.veritone.com"
    async_client_name: str = "_StdlibGeneratedAsyncAiware"
    async_client_file_name: str = "async_client"
    async_base_client_file_path: str = os.path.abspath(
                os.path.join(
                    get_package_root(), "client/_base/async_base_client_ref.py"
                )
            )
    async_base_client_name: str = "_AsyncBaseClient"

    sync_client_name: str = "_StdlibGeneratedAiware"
    sync_client_file_name: str = "client"
    sync_base_client_file_path: str = os.path.abspath(
                os.path.join(
                    get_package_root(), "client/_base/base_client_ref.py"
                )
            )
    sync_base_client_name: str = "_BaseClient"

    include_all_inputs: bool = False
    include_all_enums: bool = False

    convert_to_snake_case: bool = False

    def __post_init__(self) -> None:
        if not self.remote_schema_url:
            self.remote_schema_url: str = urljoin(self.base_url, "/v3/graphql")

        super().__post_init__()

    def async_client_settings(self):
        return dataclasses.replace(
            self,
            async_client=True,
            client_name=self.async_client_name,
            client_file_name=self.async_client_file_name,
            base_client_file_path=self.async_base_client_file_path,
            base_client_name=self.async_base_client_name
        )

    def sync_client_settings(self):
        return dataclasses.replace(
            self,
            async_client=False,
            client_name=self.sync_client_name,
            client_file_name=self.sync_client_file_name,
            base_client_file_path=self.sync_base_client_file_path,
            base_client_name=self.sync_base_client_name
        )


def get_settings() -> AiwareClientGeneratorSettings:
    return AiwareClientGeneratorSettings(
        base_url="https://api.us-1.veritone.com",
        queries_path="src/aiware/client/operations",
        target_package_name="_stdlib_generated",
        target_package_path="src/aiware/client",
        convert_to_snake_case=False,
        include_all_inputs=False,
        include_all_enums=False,
        scalars={
            "JSONData": ScalarData(
                type_="aiware.common.schemas.JSONData",
                parse="aiware.common.schemas.parse_jsondata",
                serialize="aiware.common.schemas.serialize_jsondata",
            ),
            "DateTime": ScalarData(type_="datetime.datetime"),
        },
        plugins=["aiware._internal.generators.ariadne_plugin_stdlib_operation_names.StdlibOperationNamesPlugin", "aiware._internal.generators.ariadne_plugin_init.InitPlugin"],
    )


async def aiware_codegen_client(settings: AiwareClientGeneratorSettings):
    for async_client in [True, False]:
        config = settings.async_client_settings() if async_client else settings.sync_client_settings()

        # monkey patch ariadne_codegen.config.get_client_settings
        ariadne_codegen.config.get_client_settings = lambda _: config  # pyright: ignore[reportUnknownLambdaType]
        ariadne_codegen.client_generators.constants.BASE_MODEL_FILE_PATH = Path(os.path.abspath(
                os.path.join(
                    get_package_root(), "client/_base/base_model_ref.py"
                )
            ))
        ariadne_codegen.client_generators.constants.BASE_MODEL_CLASS_NAME = "BaseModel"
        ariadne_codegen.client_generators.constants.BASE_MODEL_IMPORT = ast.ImportFrom(
            module=ariadne_codegen.client_generators.constants.BASE_MODEL_FILE_PATH.stem, names=[ast.alias(ariadne_codegen.client_generators.constants.BASE_MODEL_CLASS_NAME)], level=1
        )
        ariadne_codegen.client_generators.constants.UPLOAD_IMPORT = ast.ImportFrom(
            module=ariadne_codegen.client_generators.constants.BASE_MODEL_FILE_PATH.stem, names=[ast.alias(ariadne_codegen.client_generators.constants.UPLOAD_CLASS_NAME)], level=1
        )
        ariadne_codegen.client_generators.constants.UNSET_NAME = "UNSET"
        ariadne_codegen.client_generators.constants.UNSET_TYPE_NAME = "UnsetType"
        ariadne_codegen.client_generators.constants.UNSET_IMPORT = ast.ImportFrom(
            module=ariadne_codegen.client_generators.constants.BASE_MODEL_FILE_PATH.stem,
            names=[ast.alias(ariadne_codegen.client_generators.constants.UNSET_NAME), ast.alias(ariadne_codegen.client_generators.constants.UNSET_TYPE_NAME)],
            level=1,
        )

        from ariadne_codegen.main import client as ariadne_codegen_client  # pyright: ignore[reportUnknownVariableType]

        ariadne_codegen_client(config)


def main():
    asyncio.run(aiware_codegen_client(get_settings()))


if __name__ == "__main__":
    main()
