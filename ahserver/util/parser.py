# encoding=utf-8

__all__ = ["FieldNameEnumParser", "IntPairEnumParser"]

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from enum import Enum, EnumMeta
    from typing import Type, Union


class EnumParser:
    def __init__(self, enum_type):  # type: (str) -> None
        self.enum_type = enum_type

    def __call__(self, clazz):  # type: (Type[Enum]) -> Type[Enum]
        return clazz


class FieldNameEnumParser(EnumParser):
    def __call__(self, clazz):  # type: (Type[Enum]) -> Type[Enum]
        super(FieldNameEnumParser, self).__call__(clazz)

        @classmethod
        def parse(cls, filed_name):  # type: (EnumMeta, Union[str, bytes]) -> Enum
            if isinstance(filed_name, bytes):
                filed_name = filed_name.decode("ascii")

            key = filed_name.upper().replace("-", "_")
            if key in cls.__members__:
                return cls[key]

            raise Exception("Unknown {}.".format(self.enum_type))

        clazz.parse = parse

        return clazz


class IntPairEnumParser(EnumParser):
    def __call__(self, clazz):  # type: (Type[Enum]) -> Type[Enum]
        """add common functions to class"""
        super(IntPairEnumParser, self).__call__(clazz)

        clazz._int2member_map_ = {value[0]: member for value, member in clazz._value2member_map_.items()}

        @classmethod
        def parse(cls, int_value):  # type: (Type[Enum], int) -> Enum
            try:
                return cls._int2member_map_[int_value]
            except KeyError:
                raise Exception("Unknown {}.".format(self.enum_type))

        clazz.parse = parse

        return clazz
