# encoding=utf-8

__all__ = ["FieldNameEnumParser", "IntEnumParser", "IntPairEnumParser"]

from enum import Enum, EnumMeta, IntEnum

from typing import Type, Union


class EnumParser:
    def __init__(self, enum_type):
        self.enum_type = enum_type

    def __call__(self, clazz: Type[Enum]):
        return clazz


class FieldNameEnumParser(EnumParser):
    def __call__(self, clazz: Type[Enum]):
        super(FieldNameEnumParser, self).__call__(clazz)

        @classmethod
        def parse(cls: EnumMeta, filed_name: Union[str, bytes]):
            if isinstance(filed_name, bytes):
                filed_name = filed_name.decode("ascii")

            key = filed_name.upper().replace("-", "_")
            if key in cls.__members__:
                return cls[key]

            raise Exception("Unknown {}.".format(self.enum_type))

        clazz.parse = parse

        return clazz


class IntEnumParser(EnumParser):
    def __call__(self, clazz: Type[IntEnum]):
        super(IntEnumParser, self).__call__(clazz)

        @classmethod
        def parse(cls: Type[IntEnum], int_value: int):
            try:
                return cls._value2member_map_[int_value]
            except KeyError:
                raise Exception("Unknown {}.".format(self.enum_type))

        clazz.parse = parse

        return clazz


class IntPairEnumParser(EnumParser):
    def __call__(self, clazz: Type[Enum]):
        """add common functions to class"""
        super(IntPairEnumParser, self).__call__(clazz)

        clazz._int2member_map_ = {value[0]: member for value, member in clazz._value2member_map_.items()}

        @classmethod
        def parse(cls: Type[IntEnum], int_value: int):
            try:
                return cls._int2member_map_[int_value]
            except KeyError:
                raise Exception("Unknown {}.".format(self.enum_type))

        clazz.parse = parse

        return clazz
