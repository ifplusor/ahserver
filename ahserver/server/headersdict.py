# encoding=utf-8

__all__ = ["HeadersDict"]

from collections import MutableMapping

from ..util.dict import CaseInsensitiveDict
from .constant import LATIN1_ENCODING

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any, AnyStr, Iterator


def _to_latin1(val):  # type: (Any) -> bytes
    if isinstance(val, bytes):
        return val
    elif isinstance(val, str):
        return val.encode(LATIN1_ENCODING)
    else:
        return str(val).encode(LATIN1_ENCODING)


class HeadersDict(MutableMapping):
    def __init__(self):
        super(HeadersDict, self).__init__()
        self.headers = CaseInsensitiveDict()

    def __contains__(self, field_name):  # type: (Any) -> bool
        key = _to_latin1(field_name)
        return key in self.headers

    def __setitem__(self, field_name, field_value):  # type: (Any, AnyStr) -> None
        key = _to_latin1(field_name)
        val = _to_latin1(field_value)
        if key in self.headers:
            self.headers[key] += b"," + val
        else:
            self.headers[key] = val

    def __getitem__(self, field_name):  # type: (Any) -> bytes
        key = _to_latin1(field_name)
        return self.headers[key]

    def __delitem__(self, field_name):  # type: (Any) -> None
        key = _to_latin1(field_name)
        del self.headers[key]

    def __iter__(self):  # type: () -> Iterator[bytes]
        return self.headers.__iter__()

    __len__ = None
