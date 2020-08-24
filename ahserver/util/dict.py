# encoding=utf-8
#
# copy from requests.structures.CaseInsensitiveDict
#

__all__ = ["CaseInsensitiveDict"]

from collections import OrderedDict, Mapping, MutableMapping, ItemsView, Iterator

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any, AnyStr, Dict, Tuple


class LowerItemsIterator(Iterator):
    def __init__(self, iterator):  # type: (Iterator) -> None
        self._iterator = iterator

    def __iter__(self):
        return self

    def __next__(self):
        key, val = next(self._iterator)
        return (key, val[1])


class LowerItemsView(ItemsView):
    def __init__(self, view):  # type: (ItemsView) -> None
        self._view = view

    def __iter__(self):  # type: () -> Iterator
        return LowerItemsIterator(self._view.__iter__())


class OriginKeyIterator(Iterator):
    def __init__(self, iterator):  # type: (Iterator) -> None
        self._iterator = iterator

    def __iter__(self):
        return self

    def __next__(self):
        key, val = next(self._iterator)
        return key


class CaseInsensitiveDict(MutableMapping):  # type: MutableMapping[AnyStr, Any]
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = OrderedDict()  # type: Dict[AnyStr, Tuple[AnyStr, Any]]
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __contains__(self, key):  # type: (AnyStr) -> bool
        return key.lower() in self._store

    def __setitem__(self, key, value):  # type: (AnyStr, Any) -> None
        # Use the lower-cased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):  # type: (AnyStr) -> Any
        return self._store[key.lower()][1]

    def __delitem__(self, key):  # type: (AnyStr) -> None
        del self._store[key.lower()]

    def __iter__(self):  # type: () -> Iterator[AnyStr]
        return OriginKeyIterator(self._store.values().__iter__())

    def __len__(self):  # type: () -> int
        return len(self._store)

    def lower_items(self):  # type: () -> ItemsView[AnyStr, Any]
        """Like iteritems(), but with all lowercase keys."""
        return LowerItemsView(self._store.items())

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))
