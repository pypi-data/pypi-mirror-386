from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.file import FileSelector
from mcdplib.core.resource.resource import Resource, ResourceBuilderLoader


class InvalidResourceTypeError(TypeError):
    def __init__(self, invalid_resource: any):
        super().__init__(f"Invalid resource type: {type(invalid_resource)}")


class ResourceDoesNotExistError(KeyError):
    def __init__(self, string_identifier: str):
        super().__init__(f"Resource with identifier \"{string_identifier}\" does not exist")


class ResourceAlreadyExistsError(KeyError):
    def __init__(self, string_identifier: str):
        super().__init__(f"Resource with identifier \"{string_identifier}\" already exists")


class RegistryResourceType:
    def __init__(self, resource_types: list[type], file_extension: str):
        self.resource_types: list[type] = resource_types
        self.file_extension: str = file_extension


class RegistryResourceBuilderLoader:
    def __init__(self, file_selector: FileSelector, resource_builder_loader: ResourceBuilderLoader):
        self.file_selector: FileSelector = file_selector
        self.resource_builder_loader: ResourceBuilderLoader = resource_builder_loader


class Registry:
    def __init__(self, name: str, resource_types: list[RegistryResourceType], resource_builder_loaders: list[RegistryResourceBuilderLoader]):
        self.name: str = name
        self.resource_types: list[RegistryResourceType] = resource_types
        self.resource_builder_loaders: list[RegistryResourceBuilderLoader] = resource_builder_loaders

        self._resources: dict[str, Resource] = dict()

    def _find_registry_resource_type_for_resource(self, resource: Resource) -> RegistryResourceType | None:
        for registry_resource_type in self.resource_types:
            for resource_type in registry_resource_type.resource_types:
                if isinstance(resource, resource_type):
                    return registry_resource_type
        return None

    def get(self, identifier: IdentifierLike) -> Resource:
        string_identifier: str = Identifier.identifier(identifier).__str__()
        if string_identifier not in self._resources:
            raise ResourceDoesNotExistError(string_identifier)
        return self._resources[string_identifier]

    def get_or_none(self, identifier: IdentifierLike) -> Resource | None:
        string_identifier: str = Identifier.identifier(identifier).__str__()
        if string_identifier not in self._resources:
            return None
        return self._resources[string_identifier]

    def get_or_default(self, identifier: IdentifierLike, default: Resource) -> Resource:
        string_identifier: str = Identifier.identifier(identifier).__str__()
        if string_identifier not in self._resources:
            return default
        return self._resources[string_identifier]

    def add(self, resource: Resource) -> None:
        registry_resource_type: RegistryResourceType | None = self._find_registry_resource_type_for_resource(resource)
        if registry_resource_type is None:
            raise InvalidResourceTypeError(resource)
        string_identifier: str = resource.identifier.__str__()
        if string_identifier in self._resources:
            raise ResourceAlreadyExistsError(string_identifier)
        self._resources[string_identifier] = resource

    def write(self, data_directory: str) -> None:
        for resource in self._resources.values():
            registry_resource_type: RegistryResourceType = self._find_registry_resource_type_for_resource(resource)
            resource_file: str = f"{data_directory}/{resource.identifier.namespace}/{self.name}/{resource.identifier.name}.{registry_resource_type.file_extension}"
            resource.write(resource_file)

    def __iter__(self):
        return self._resources.values().__iter__()
