from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.file import read_text_file, write_text_file
from mcdplib.core.resource.resource import Resource, ResourceBuilder, ResourceBuilderLoader


class StringResource(Resource):
    def __init__(self, registry_name: str, identifier: IdentifierLike, data: str):
        super().__init__(registry_name, identifier)
        self.data: str = data

    def write(self, file: str) -> None:
        write_text_file(file, self.data)


class StringResourceBuilder(ResourceBuilder):
    def build(self, context: dict) -> list[StringResource]:
        resources: list[StringResource] = list()
        return resources


# Static

class StaticStringResourceBuilder(StringResourceBuilder):
    def __init__(self, registry_name: str, identifier: IdentifierLike, resource_data: str):
        super().__init__(registry_name, identifier)
        self.resource_data: str = resource_data

    def build(self, context: dict) -> list[StringResource]:
        resources: list[StringResource] = list()
        resources.append(StringResource(
            registry_name=self.registry_name,
            identifier=self.identifier,
            data=self.resource_data
        ))
        return resources


class StaticStringResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[StaticStringResourceBuilder]:
        resource_builders: list[StaticStringResourceBuilder] = list()
        resource_builders.append(StaticStringResourceBuilder(
            registry_name=registry_name,
            identifier=identifier,
            resource_data=read_text_file(file)
        ))
        return resource_builders
