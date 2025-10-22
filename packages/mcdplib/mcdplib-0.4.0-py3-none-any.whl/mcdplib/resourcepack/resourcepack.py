from mcdplib.core.file import extensions_file_selector, read_text_file, read_json_file
from mcdplib.core.registry import Registry, RegistryResourceType, RegistryResourceBuilderLoader
from mcdplib.core.pack import PackInformation, PackFeatures, PackFilters, PackOverlays, Pack
from mcdplib.core.resource.resource_binary import BinaryResource, StaticBinaryResourceBuilderLoader
from mcdplib.core.resource.resource_object import ObjectResource, ObjectResourceBuilder, StaticObjectResourceBuilder, DynamicObjectResourceBuilder, StaticObjectResourceBuilderLoader, DynamicObjectResourceBuilderLoader
from mcdplib.core.resource.resource_string import StringResource, StaticStringResourceBuilderLoader
from mcdplib.resourcepack.shader import FSHShader, VSHShader, GLSLShader, StaticFSHShaderBuilderLoader, StaticVSHShaderBuilderLoader, StaticGLSLShaderBuilderLoader
import os


class PackLanguage:
    def __init__(self, language_code: str, name: str, region: str, bidirectional: bool):
        self.language_code: str = language_code
        self.name: str = name
        self.region: str = region
        self.bidirectional: bool = bidirectional

    def build(self) -> dict:
        return {
            "name": self.name,
            "region": self.region,
            "bidirectional": self.bidirectional
        }


class ExternalObjectResource:
    def __init__(self, name: str, static_file_extension: str, dynamic_file_extension: str):
        self.name: str = name
        self.static_file_extension: str = static_file_extension
        self.dynamic_file_extension: str = dynamic_file_extension
        self._resource_builders: list[ObjectResourceBuilder] = list()
        self._resource: ObjectResource | None = None

    def load(self, data_directory: str, context: dict) -> None:
        for namespace in os.listdir(data_directory):
            file = f"{data_directory}/{namespace}/{self.name}"
            static_file = f"{file}.{self.static_file_extension}"
            dynamic_file = f"{file}.{self.dynamic_file_extension}"
            if os.path.exists(static_file):
                self._resource_builders.append(StaticObjectResourceBuilder(
                    registry_name="",
                    identifier=f"{namespace}:",
                    resource_data=read_json_file(static_file)
                ))
            if os.path.exists(dynamic_file):
                self._resource_builders.append(DynamicObjectResourceBuilder(
                    registry_name="",
                    identifier=f"{namespace}:{self.name}",
                    code=read_text_file(dynamic_file)
                ))

    def build(self, context: dict) -> None:
        for resource_builder in self._resource_builders:
            self._resource = resource_builder.build(context)[0]
            if self._resource is not None:
                break

    def write(self, data_directory: str) -> None:
        if self._resource is not None:
            self._resource.write(f"{data_directory}/{self._resource.identifier.namespace}/{self.name}.json")


class Resourcepack(Pack):
    ASSETS_DIRECTORY: str = "assets"

    def __init__(self, information: PackInformation, features: PackFeatures | None = None, filters: PackFilters | None = None, overlays: PackOverlays | None = None, languages: list[PackLanguage] | None = None, icon: bytes | None = None):
        super().__init__(information, Resourcepack.ASSETS_DIRECTORY, features, filters, overlays, icon)
        self.languages: list[PackLanguage] | None = languages

        self.external_object_resources: list[ExternalObjectResource] = [
            ExternalObjectResource(
                name="gpu_warnlist",
                static_file_extension="json",
                dynamic_file_extension="py"
            ),
            ExternalObjectResource(
                name="regional_compliancies",
                static_file_extension="json",
                dynamic_file_extension="py"
            ),
            ExternalObjectResource(
                name="sounds",
                static_file_extension="json",
                dynamic_file_extension="py"
            )
        ]

        self.core_shaders: Registry = Registry(
            name="shaders/core",
            resource_types=[
                RegistryResourceType(
                    resource_types=[FSHShader],
                    file_extension="fsh"
                ),
                RegistryResourceType(
                    resource_types=[VSHShader],
                    file_extension="vsh"
                )
            ],
            resource_builder_loaders=[
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["fsh"]),
                    resource_builder_loader=StaticFSHShaderBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["vsh"]),
                    resource_builder_loader=StaticVSHShaderBuilderLoader()
                )
            ]
        )
        self.add_registry(self.core_shaders)

        self.include_shaders: Registry = Registry(
            name="shaders/include",
            resource_types=[
                RegistryResourceType(
                    resource_types=[FSHShader],
                    file_extension="fsh"
                ),
                RegistryResourceType(
                    resource_types=[VSHShader],
                    file_extension="vsh"
                ),
                RegistryResourceType(
                    resource_types=[GLSLShader],
                    file_extension="glsl"
                )
            ],
            resource_builder_loaders=[
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["fsh"]),
                    resource_builder_loader=StaticFSHShaderBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["vsh"]),
                    resource_builder_loader=StaticVSHShaderBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["glsl"]),
                    resource_builder_loader=StaticGLSLShaderBuilderLoader()
                )
            ]
        )
        self.add_registry(self.include_shaders)

        self.post_shaders: Registry = Registry(
            name="shaders/post",
            resource_types=[
                RegistryResourceType(
                    resource_types=[FSHShader],
                    file_extension="fsh"
                ),
                RegistryResourceType(
                    resource_types=[VSHShader],
                    file_extension="vsh"
                )
            ],
            resource_builder_loaders=[
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["fsh"]),
                    resource_builder_loader=StaticFSHShaderBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["vsh"]),
                    resource_builder_loader=StaticVSHShaderBuilderLoader()
                )
            ]
        )
        self.add_registry(self.post_shaders)

        self.sounds: Registry = Registry(
            name="sounds",
            resource_types=[RegistryResourceType(
                resource_types=[BinaryResource],
                file_extension="ogg"
            )],
            resource_builder_loaders=[RegistryResourceBuilderLoader(
                file_selector=extensions_file_selector(["ogg"]),
                resource_builder_loader=StaticBinaryResourceBuilderLoader()
            )]
        )
        self.add_registry(self.sounds)

        self.texts: Registry = Registry(
            name="texts",
            resource_types=[
                RegistryResourceType(
                    resource_types=[StringResource],
                    file_extension="txt"
                ),
                RegistryResourceType(
                    resource_types=[ObjectResource],
                    file_extension="json"
                )
            ],
            resource_builder_loaders=[
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["txt"]),
                    resource_builder_loader=StaticStringResourceBuilderLoader()
                ),
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
        self.add_registry(self.texts)

        self.textures: Registry = Registry(
            name="textures",
            resource_types=[
                RegistryResourceType(
                    resource_types=[BinaryResource],
                    file_extension="png"
                ),
                RegistryResourceType(
                    resource_types=[ObjectResource],
                    file_extension="mcmeta"
                )
            ],
            resource_builder_loaders=[
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["png"]),
                    resource_builder_loader=StaticBinaryResourceBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["mcmeta", "json"]),
                    resource_builder_loader=StaticObjectResourceBuilderLoader()
                ),
                RegistryResourceBuilderLoader(
                    file_selector=extensions_file_selector(["py"]),
                    resource_builder_loader=DynamicObjectResourceBuilderLoader()
                )
            ]
        )
        self.add_registry(self.textures)

        self.atlases: Registry = self._create_object_resource_registry("atlases")
        self.blockstates: Registry = self._create_object_resource_registry("blockstates")
        self.equipment: Registry = self._create_object_resource_registry("equipment")
        self.font: Registry = self._create_object_resource_registry("font")
        self.items: Registry = self._create_object_resource_registry("items")
        self.langs: Registry = self._create_object_resource_registry("lang")
        self.models: Registry = self._create_object_resource_registry("models")
        self.particles: Registry = self._create_object_resource_registry("particles")
        self.post_effects: Registry = self._create_object_resource_registry("post_effect")
        self.waypoint_styles: Registry = self._create_object_resource_registry("waypoint_style")

    def build_pack_mcmeta(self) -> dict:
        pack: dict = super().build_pack_mcmeta()
        if self.languages is not None:
            for language in self.languages:
                pack[language.language_code] = language.build()
        return pack

    def load(self, data_directory: str, context: dict) -> None:
        super().load(data_directory, context)
        for external_object_resource in self.external_object_resources:
            external_object_resource.load(data_directory, context)

    def build(self, context: dict) -> None:
        super().build(context)
        for external_object_resource in self.external_object_resources:
            external_object_resource.build(context)

    def write(self, pack_directory: str) -> None:
        super().write(pack_directory)
        data_directory: str = f"{pack_directory}/{self.data_directory}"
        for external_object_resource in self.external_object_resources:
            external_object_resource.write(data_directory)
