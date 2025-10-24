from ast import AsyncFunctionDef, FunctionDef
from typing import override
from ariadne_codegen.plugins.base import Plugin
from graphql import OperationDefinitionNode

class StdlibOperationNamesPlugin(Plugin):
    @override
    def generate_client_method(
        self,
        method_def: FunctionDef | AsyncFunctionDef,
        operation_definition: OperationDefinitionNode,
    ) -> FunctionDef | AsyncFunctionDef:
        method_def.name = "_" + method_def.name
        return method_def
