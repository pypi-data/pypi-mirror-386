from __future__ import annotations
from mcdplib.core.string import string_contains_only


class InvalidIdentifierTypeError(TypeError):
    def __init__(self, invalid_identifier: any):
        super().__init__(f"Invalid identifier type: {type(invalid_identifier)}")


class InvalidIdentifierFormatError(ValueError):
    def __init__(self, invalid_identifier: str):
        super().__init__(f"Invalid identifier format: \"{invalid_identifier}\"")


class InvalidIdentifierNamespaceError(ValueError):
    def __init__(self, invalid_namespace: str):
        super().__init__(f"Invalid identifier namespace: \"{invalid_namespace}\"")


class InvalidIdentifierNameError(ValueError):
    def __init__(self, invalid_name: str):
        super().__init__(f"Invalid identifier name: \"{invalid_name}\"")


class Identifier:
    NAMESPACE_SEPARATOR: str = ":"
    NAME_PATH_SEPARATOR: str = "/"
    NAMESPACE_ALLOWED_SYMBOLS: str = "0123456789abcdefghijklmnopqrstuvwxyz_-."
    NAME_ALLOWED_SYMBOLS: str = NAMESPACE_ALLOWED_SYMBOLS + NAME_PATH_SEPARATOR

    @classmethod
    def identifier(cls, identifier: IdentifierLike) -> Identifier:
        if isinstance(identifier, str):
            if identifier.count(Identifier.NAMESPACE_SEPARATOR) != 1:
                raise InvalidIdentifierFormatError(identifier)
            namespace, name = identifier.split(":")
            return Identifier(
                namespace=namespace,
                name=name
            )
        if isinstance(identifier, Identifier):
            return identifier
        raise InvalidIdentifierTypeError(identifier)

    def __init__(self, namespace: str, name: str):
        if not string_contains_only(namespace, Identifier.NAMESPACE_ALLOWED_SYMBOLS):
            raise InvalidIdentifierNamespaceError(namespace)
        if not string_contains_only(name, Identifier.NAME_ALLOWED_SYMBOLS):
            raise InvalidIdentifierNameError(name)
        self.namespace: str = namespace
        self.name: str = name

    def get_parent(self) -> Identifier:
        if Identifier.NAME_PATH_SEPARATOR in self.name:
            return Identifier(
                namespace=self.namespace,
                name=self.name.rsplit(Identifier.NAME_PATH_SEPARATOR, maxsplit=1)[0]
            )
        return Identifier(
            namespace=self.namespace,
            name=""
        )

    def get_child(self, child_name: str) -> Identifier:
        if self.name == "":
            return Identifier(
                namespace=self.namespace,
                name=child_name
            )
        return Identifier(
            namespace=self.namespace,
            name=f"{self.name}{Identifier.NAME_PATH_SEPARATOR}{child_name}"
        )

    def __str__(self):
        return f"{self.namespace}{Identifier.NAMESPACE_SEPARATOR}{self.name}"


IdentifierLike = str | Identifier
