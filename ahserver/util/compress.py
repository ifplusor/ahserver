# encoding=utf-8

__all__ = ["supported_encoding"]

from collections import OrderedDict


supported_encoding = OrderedDict()


# gzip compress supported
try:
    import gzip

    supported_encoding["gzip"] = gzip.compress
except Exception:
    pass


def nop(data):
    return data


supported_encoding["identity"] = nop
