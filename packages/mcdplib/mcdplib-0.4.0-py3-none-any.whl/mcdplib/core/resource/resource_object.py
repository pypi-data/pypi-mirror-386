from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.file import read_text_file, read_json_file, write_json_file
from mcdplib.core.evaluation import execute
from mcdplib.core.resource.resource import Resource, ResourceBuilder, ResourceBuilderLoader


class ObjectResource(Resource):
    def __init__(self, registry_name: str, identifier: IdentifierLike, data: dict):
        super().__init__(registry_name, identifier)
        self.data: dict = data

    def write(self, file: str) -> None:
        write_json_file(file, self.data)


class ObjectResourceBuilder(ResourceBuilder):
    REGISTRY_NAME_FIELD: str = "registry"
    IDENTIFIER_FIELD: str = "id"

    def _create_resource_from_resource_data(self, resource_data: dict) -> ObjectResource:
        registry_name: str = self.registry_name
        identifier: IdentifierLike = self.identifier
        if ObjectResourceBuilder.REGISTRY_NAME_FIELD in resource_data:
            registry_name = resource_data[ObjectResourceBuilder.REGISTRY_NAME_FIELD]
            resource_data.pop(ObjectResourceBuilder.REGISTRY_NAME_FIELD)
        if ObjectResourceBuilder.IDENTIFIER_FIELD in resource_data:
            identifier = resource_data[ObjectResourceBuilder.IDENTIFIER_FIELD]
            resource_data.pop(ObjectResourceBuilder.IDENTIFIER_FIELD)
        return ObjectResource(
            registry_name=registry_name,
            identifier=identifier,
            data=resource_data
        )

    def build(self, context: dict) -> list[ObjectResource]:
        resources: list[ObjectResource] = list()
        return resources


# Static

class StaticObjectResourceBuilder(ObjectResourceBuilder):
    def __init__(self, registry_name: str, identifier: IdentifierLike, resource_data: dict):
        super().__init__(registry_name, identifier)
        self.resource_data: dict = resource_data

    def build(self, context: dict) -> list[ObjectResource]:
        resources: list[ObjectResource] = list()
        resources.append(self._create_resource_from_resource_data(self.resource_data))
        return resources


class StaticObjectResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[StaticObjectResourceBuilder]:
        resource_builders: list[StaticObjectResourceBuilder] = list()
        resource_builders.append(StaticObjectResourceBuilder(
            registry_name=registry_name,
            identifier=identifier,
            resource_data=read_json_file(file)
        ))
        return resource_builders


# Dynamic

class DynamicObjectResourceBuilder(ObjectResourceBuilder):
    RESOURCE_FIELD: str = "resource"
    RESOURCES_FIELD: str = "resources"

    def __init__(self, registry_name: str, identifier: IdentifierLike, code: str):
        super().__init__(registry_name, identifier)
        self.code: str = code

    def build(self, context: dict) -> list[ObjectResource]:
        resources: list[ObjectResource] = list()
        execute(self.code, context)
        if DynamicObjectResourceBuilder.RESOURCE_FIELD in context:
            resources.append(self._create_resource_from_resource_data(context[DynamicObjectResourceBuilder.RESOURCE_FIELD]))
        if DynamicObjectResourceBuilder.RESOURCES_FIELD in context:
            for resource_data in context[DynamicObjectResourceBuilder.RESOURCES_FIELD]:
                resources.append(self._create_resource_from_resource_data(resource_data))
        return resources


class DynamicObjectResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[DynamicObjectResourceBuilder]:
        resource_builders: list[DynamicObjectResourceBuilder] = list()
        resource_builders.append(DynamicObjectResourceBuilder(
            registry_name=registry_name,
            identifier=identifier,
            code=read_text_file(file)
        ))
        return resource_builders
