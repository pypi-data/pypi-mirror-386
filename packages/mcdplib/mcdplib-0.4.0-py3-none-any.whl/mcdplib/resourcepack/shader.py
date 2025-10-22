from mcdplib.core.identifier import Identifier
from mcdplib.core.file import read_text_file
from mcdplib.core.resource.resource_string import StringResource, StaticStringResourceBuilder, StaticStringResourceBuilderLoader


class FSHShader(StringResource):
    pass


class VSHShader(StringResource):
    pass


class GLSLShader(StringResource):
    pass


class StaticFSHShaderBuilder(StaticStringResourceBuilder):
    def build(self, context: dict) -> list[FSHShader]:
        resources: list[FSHShader] = list()
        resources.append(FSHShader(
            registry_name=self.registry_name,
            identifier=self.identifier,
            data=self.resource_data
        ))
        return resources


class StaticVSHShaderBuilder(StaticStringResourceBuilder):
    def build(self, context: dict) -> list[VSHShader]:
        resources: list[VSHShader] = list()
        resources.append(VSHShader(
            registry_name=self.registry_name,
            identifier=self.identifier,
            data=self.resource_data
        ))
        return resources


class StaticGLSLShaderBuilder(StaticStringResourceBuilder):
    def build(self, context: dict) -> list[GLSLShader]:
        resources: list[GLSLShader] = list()
        resources.append(GLSLShader(
            registry_name=self.registry_name,
            identifier=self.identifier,
            data=self.resource_data
        ))
        return resources


class StaticFSHShaderBuilderLoader(StaticStringResourceBuilderLoader):
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[StaticFSHShaderBuilder]:
        resource_builders: list[StaticFSHShaderBuilder] = list()
        resource_builders.append(StaticFSHShaderBuilder(
            registry_name=registry_name,
            identifier=identifier,
            resource_data=read_text_file(file)
        ))
        return resource_builders


class StaticVSHShaderBuilderLoader(StaticStringResourceBuilderLoader):
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[StaticVSHShaderBuilder]:
        resource_builders: list[StaticVSHShaderBuilder] = list()
        resource_builders.append(StaticVSHShaderBuilder(
            registry_name=registry_name,
            identifier=identifier,
            resource_data=read_text_file(file)
        ))
        return resource_builders


class StaticGLSLShaderBuilderLoader(StaticStringResourceBuilderLoader):
    def load(self, directory: str, file: str, registry_name: str, identifier: Identifier) -> list[StaticGLSLShaderBuilder]:
        resource_builders: list[StaticGLSLShaderBuilder] = list()
        resource_builders.append(StaticGLSLShaderBuilder(
            registry_name=registry_name,
            identifier=identifier,
            resource_data=read_text_file(file)
        ))
        return resource_builders
