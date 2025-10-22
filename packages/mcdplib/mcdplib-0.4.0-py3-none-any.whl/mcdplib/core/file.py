import os
import json
from typing import Callable

FileSelector = Callable[[str], bool]


def extensions_file_selector(extensions: list[str]) -> FileSelector:
    def file_selector(file: str) -> bool:
        return os.path.splitext(file)[1].removeprefix(".") in extensions

    return file_selector


JsonLike = None | bool | int | float | str | tuple | list | dict


def read_binary_file(file: str) -> bytes:
    f = open(file, "rb")
    data: bytes = f.read()
    f.close()
    return data


def read_text_file(file: str, encoding: str = "utf-8") -> str:
    f = open(file, "rt", encoding=encoding)
    data: str = f.read()
    f.close()
    return data


def read_json_file(file: str, encoding: str = "utf-8") -> JsonLike:
    f = open(file, "rt", encoding=encoding)
    data: JsonLike = json.load(f)
    f.close()
    return data


def write_binary_file(file: str, content: bytes) -> None:
    directory: str = os.path.dirname(file)
    os.makedirs(directory, exist_ok=True)
    f = open(file, "wb")
    f.write(content)
    f.close()


def write_text_file(file: str, content: str, encoding: str = "utf-8") -> None:
    directory: str = os.path.dirname(file)
    os.makedirs(directory, exist_ok=True)
    f = open(file, "wt", encoding=encoding)
    f.write(content)
    f.close()


def write_json_file(file: str, content: JsonLike, indent: int | None = None, encoding: str = "utf-8") -> None:
    directory: str = os.path.dirname(file)
    os.makedirs(directory, exist_ok=True)
    f = open(file, "wt", encoding=encoding)
    json.dump(content, f, indent=indent, ensure_ascii=False)
    f.close()
