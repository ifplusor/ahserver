# encoding=utf-8
# cython: language_level=3
# cython: embedsignature=True

from .ahparser cimport (
    ahp_msgbuf_t,
    ahp_msgbuf_init,
    ahp_msgbuf_free,
    ahp_msgbuf_append,
    ahp_msgbuf_copy,
    ahp_msgbuf_data,
    ahp_msgbuf_length,
    ahp_msgbuf_reset,
)


cdef class Buffer:
    """Message Buffer"""

    def __dealloc__(self):
        ahp_msgbuf_free(&self._buffer)

    def __cinit__(self):
        # 初始化 msgbuf
        cdef int errno = ahp_msgbuf_init(&self._buffer, 2048)
        if errno != 0:
            raise Exception("Failed to init Buffer. errno:{}".format(errno))

    def append(self, data, length=-1, offset=0):  # type: (bytes, int) -> None
        cdef char* buf = <char*> data
        cdef int size = len(data)
        if length == -1:
            length = size - offset
        if offset >= size or offset + length > size:
            raise IndexError("out of range")
        cdef int errno = ahp_msgbuf_append(&self._buffer, buf + <int> offset, length)
        if errno != 0:
            raise Exception("Failed to append data to Buffer. errno:{}".format(errno))

    def take(self):  # type: () -> bytes
        data = ahp_msgbuf_data(&self._buffer)[:ahp_msgbuf_length(&self._buffer)]
        ahp_msgbuf_reset(&self._buffer)
        return data

    def reset(self):
        ahp_msgbuf_reset(&self._buffer)
