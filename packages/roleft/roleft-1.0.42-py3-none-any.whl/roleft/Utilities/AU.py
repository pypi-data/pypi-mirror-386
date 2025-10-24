import hashlib
from enum import Enum, unique, auto
from typing_extensions import TypedDict
from typing import NewType


@unique
class InputCate(Enum):
    Text = ("仅仅就是针对输入的字符串",)
    File = ("输入的必须是一个合法的文件路径",)

    def __init__(self, intro: str):
        self.intro = intro


@unique
class AlgorithmCate(Enum):
    Md5 = auto()
    Sha1 = auto()
    Sha256 = auto()


@unique
class CountryCate(Enum):
    """【闻祖东 2025-10-03 235829】只是作为一个例子而存在于此处，后续好借鉴"""

    CN = ("China", "People Republic Of China")
    US = ("USA", "United States of America")

    def __init__(self, short_name: str, full_name: str):
        self.short_name = short_name
        self.full_name = full_name

    def intro(self) -> None:
        print(f"this is {self.name}, and the full name is {self.full_name}")


cn = CountryCate.CN
cn.intro()

_algoDic = {
    AlgorithmCate.Md5: hashlib.md5,
    AlgorithmCate.Sha1: hashlib.sha1,
    AlgorithmCate.Sha256: hashlib.sha256,
}


def _load_text(cate: InputCate, text_or_path: str) -> bytes:
    match cate:
        case InputCate.File:
            with open(text_or_path, "rb") as file:
                return file.read()
        case InputCate.Text:
            return text_or_path.encode()
        case _:
            raise f"未定义的输入类型 - {cate}"


class AU:
    @staticmethod
    def calc(algoCate: AlgorithmCate, inputCate: InputCate, input: str) -> str:
        func = _algoDic[algoCate]
        return func(_load_text(inputCate, input)).hexdigest()

    @staticmethod
    def sha1_text(input: str) -> str:
        return AU.calc(AlgorithmCate.Sha1, InputCate.Text, input)

    @staticmethod
    def sha1_file(path: str) -> str:
        return AU.calc(AlgorithmCate.Sha1, InputCate.File, path)

    @staticmethod
    def sha256_text(input: str) -> str:
        return AU.calc(AlgorithmCate.Sha256, InputCate.Text, input)

    @staticmethod
    def sha256_file(path: str) -> str:
        return AU.calc(AlgorithmCate.Sha256, InputCate.File, path)

    @staticmethod
    def md5_text(input: str) -> str:
        return AU.calc(AlgorithmCate.Md5, InputCate.Text, input)

    @staticmethod
    def md5_file(path: str) -> str:
        return AU.calc(AlgorithmCate.Md5, InputCate.File, path)
