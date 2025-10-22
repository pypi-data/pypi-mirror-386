from mcdplib.core.identifier import Identifier
from mcdplib.core.file import extensions_file_selector, write_binary_file, write_json_file
from mcdplib.core.text import TextLike
from mcdplib.core.resource.resource import Resource, ResourceBuilder
from mcdplib.core.resource.resource_object import ObjectResource, StaticObjectResourceBuilderLoader, DynamicObjectResourceBuilderLoader
from mcdplib.core.registry import RegistryResourceType, RegistryResourceBuilderLoader, Registry
import shutil
import os


class RegistryDoesNotExistError(KeyError):
    def __init__(self, registry_name: str):
        super().__init__(f"Resource with name \"{registry_name}\" does not exist")


class RegistryAlreadyExistsError(KeyError):
    def __init__(self, registry_name: str):
        super().__init__(f"Resource with identifier \"{registry_name}\" already exists")


PackFormatLike = int | tuple[int] | tuple[int, int]


class PackInformation:
    def __init__(self, description: TextLike, min_format: PackFormatLike, max_format: PackFormatLike):
        self.description: TextLike = description
        self.min_format: PackFormatLike = min_format
        self.max_format: PackFormatLike = max_format

    def build(self) -> dict:
        return {
            "description": self.description,
            "min_format": self.min_format,
            "max_format": self.max_format
        }


class PackFeatures:
    def __init__(self, enabled_features: list[str]):
        self.enabled_features: list[str] = enabled_features

    def build(self) -> dict:
        return {
            "enabled": self.enabled_features
        }


class PackFilter:
    def __init__(self, namespace: str, path: str):
        self.namespace: str = namespace
        self.path: str = path

    def build(self) -> dict:
        return {
            "namespace": self.namespace,
            "path": self.path
        }


class PackFilters:
    def __init__(self, block_filters: list[PackFilter]):
        self.block_filters: list[PackFilter] = block_filters

    def build(self) -> dict:
        return {
            "block": [block_filter.build() for block_filter in self.block_filters]
        }


class PackOverlay:
    def __init__(self, directory: str, min_format: PackFormatLike, max_format: PackFormatLike):
        self.directory: str = directory
        self.min_format: PackFormatLike = min_format
        self.max_format: PackFormatLike = max_format

    def build(self) -> dict:
        return {
            "directory": self.directory,
            "min_format": self.min_format,
            "max_format": self.max_format
        }


class PackOverlays:
    def __init__(self, entry_overlays: list[PackOverlay]):
        self.entry_overlays: list[PackOverlay] = entry_overlays

    def build(self) -> dict:
        return {
            "entries": [entry_overlay.build() for entry_overlay in self.entry_overlays]
        }


class Pack:
    PACK_MCMETA_FILE: str = "pack.mcmeta"
    PACK_ICON_FILE: str = "pack.png"
    PACK_FIELD: str = "pack"
    RESOURCE_BUILDER_FIELD: str = "resource_builder"

    def __init__(self, information: PackInformation, data_directory: str, features: PackFeatures | None = None, filters: PackFilters | None = None, overlays: PackOverlays | None = None, icon: bytes | None = None):
        self.information: PackInformation = information
        self.data_directory: str = data_directory
        self.features: PackFeatures | None = features
        self.filters: PackFilters | None = filters
        self.overlays: PackOverlays | None = overlays
        self.icon: bytes | None = icon

        self._registries: dict[str, Registry] = dict()
        self._resource_builders: list[ResourceBuilder] = list()

    def get_registry(self, registry_name: str) -> Registry:
        if registry_name not in self._registries:
            raise RegistryDoesNotExistError(registry_name)
        return self._registries[registry_name]

    def get_registry_or_none(self, registry_name: str) -> Registry | None:
        if registry_name not in self._registries:
            return None
        return self._registries[registry_name]

    def get_registry_or_default(self, registry_name: str, default: Registry) -> Registry:
        if registry_name not in self._registries:
            return default
        return self._registries[registry_name]

    def add_registry(self, registry: Registry) -> None:
        if registry.name is self._registries:
            raise RegistryAlreadyExistsError(registry.name)
        self._registries[registry.name] = registry

    def add_resource_builder(self, resource_builder: ResourceBuilder) -> None:
        self._resource_builders.append(resource_builder)

    def build_pack_mcmeta(self) -> dict:
        pack: dict = {
            "pack": self.information.build()
        }
        if self.features is not None:
            pack["features"] = self.features.build()
        if self.filters is not None:
            pack["filter"] = self.filters.build()
        if self.overlays is not None:
            pack["overlays"] = self.overlays.build()
        return pack

    def load(self, data_directory: str, context: dict) -> None:
        def load_resource_builders_in_directory(directory: str, parent_name: str | None = None) -> list[ResourceBuilder]:
            resource_builders: list[ResourceBuilder] = list()
            for local_entry in os.listdir(directory):
                entry: str = f"{directory}/{local_entry}"
                if os.path.isdir(entry):
                    child_name: str = local_entry
                    if parent_name is not None:
                        child_name = f"{parent_name}/{local_entry}"
                    resource_builders.extend(load_resource_builders_in_directory(entry, child_name))
                elif os.path.isfile(entry):
                    local_name: str = os.path.splitext(local_entry)[0]
                    name: str = local_name
                    if parent_name is not None:
                        name = f"{parent_name}/{local_name}"
                    for registry_resource_builder_loader in registry.resource_builder_loaders:
                        if registry_resource_builder_loader.file_selector(entry):
                            resource_builders.extend(registry_resource_builder_loader.resource_builder_loader.load(directory, entry, registry.name, Identifier(namespace=namespace, name=name)))
            return resource_builders

        for registry in self._registries.values():
            for namespace in os.listdir(data_directory):
                namespace_directory: str = f"{data_directory}/{namespace}"
                registry_directory: str = f"{namespace_directory}/{registry.name}"
                if not os.path.exists(registry_directory):
                    continue
                self._resource_builders.extend(load_resource_builders_in_directory(registry_directory))

    def build(self, context: dict) -> None:
        context[Pack.PACK_FIELD] = self
        for resource_builder in self._resource_builders:
            context[Pack.RESOURCE_BUILDER_FIELD] = resource_builder
            resources: list[Resource] = resource_builder.build(context)
            for resource in resources:
                if resource.registry_name not in self._registries:
                    raise RegistryDoesNotExistError(resource.registry_name)
                self._registries[resource.registry_name].add(resource)

    def write(self, pack_directory: str) -> None:
        write_json_file(f"{pack_directory}/{Pack.PACK_MCMETA_FILE}", self.build_pack_mcmeta())
        if self.icon is not None:
            write_binary_file(f"{pack_directory}/{Pack.PACK_ICON_FILE}", self.icon)
        data_directory: str = f"{pack_directory}/{self.data_directory}"
        if os.path.exists(data_directory):
            shutil.rmtree(data_directory)
        for registry in self._registries.values():
            registry.write(data_directory)

    def _create_object_resource_registry(self, registry_name: str) -> Registry:
        registry: Registry = Registry(
            name=registry_name,
            resource_types=[RegistryResourceType(
                resource_types=[ObjectResource],
                file_extension="json"
            )],
            resource_builder_loaders=[
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["json"]),
                    resource_builder_loader=StaticObjectResourceBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["py"]),
                    resource_builder_loader=DynamicObjectResourceBuilderLoader()
                )
            ]
        )
        self.add_registry(registry)
        return registry

    def __iter__(self):
        return self._registries.values().__iter__()
