from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.file import read_binary_file, write_binary_file
from mcdplib.core.resource.resource import Resource, ResourceBuilder, ResourceBuilderLoader


class BinaryResource(Resource):
    def __init__(self, registry_name: str, identifier: IdentifierLike, data: bytes):
        super().__init__(registry_name, identifier)
        self.data: bytes = data

    def write(self, file: str) -> None:
        write_binary_file(file, self.data)


class BinaryResourceBuilder(ResourceBuilder):
    def build(self, context: dict) -> list[BinaryResource]:
        resources: list[BinaryResource] = list()
        return resources


# Static

class StaticBinaryResourceBuilder(BinaryResourceBuilder):
    def __init__(self, registry_name: str, identifier: IdentifierLike, resource_data: bytes):
        super().__init__(registry_name, identifier)
        self.resource_data: bytes = resource_data

    def build(self, context: dict) -> list[BinaryResource]:
        resources: list[BinaryResource] = list()
        resources.append(BinaryResource(
            registry_name=self.registry_name,
            identifier=self.identifier,
            data=self.resource_data
        ))
        return resources


class StaticBinaryResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[StaticBinaryResourceBuilder]:
        resource_builders: list[StaticBinaryResourceBuilder] = list()
        resource_builders.append(StaticBinaryResourceBuilder(
            registry_name=registry_name,
            identifier=identifier,
            resource_data=read_binary_file(file)
        ))
        return resource_builders
