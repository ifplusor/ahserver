# encoding=utf-8
# cython: language_level=3
# cython: embedsignature=True

from .ahparser cimport ahp_msgbuf_t

cdef class Buffer:
    cdef ahp_msgbuf_t _buffer
