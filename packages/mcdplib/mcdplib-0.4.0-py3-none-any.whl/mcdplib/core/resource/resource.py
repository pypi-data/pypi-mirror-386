from mcdplib.core.identifier import Identifier, IdentifierLike


class Resource:
    def __init__(self, registry_name: str, identifier: IdentifierLike):
        self.registry_name: str = registry_name
        self.identifier: Identifier = Identifier.identifier(identifier)

    def write(self, file: str) -> None:
        pass


class ResourceBuilder:
    def __init__(self, registry_name: str, identifier: IdentifierLike):
        self.registry_name: str = registry_name
        self.identifier: Identifier = Identifier.identifier(identifier)

    def build(self, context: dict) -> list[Resource]:
        resources: list[Resource] = list()
        return resources


class ResourceBuilderLoader:
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[ResourceBuilder]:
        resource_builders: list[ResourceBuilder] = list()
        return resource_builders
