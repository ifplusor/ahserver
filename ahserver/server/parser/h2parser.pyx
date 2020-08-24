# encoding=utf-8
# cython: language_level=3
# cython: embedsignature=True

from libc.errno cimport *
from cpython.ref cimport Py_INCREF, Py_DECREF

from ..frame import (
    HttpFrame,
    HttpDataFrame,
    HttpHeadersFrame,
    HttpSettingsFrame,
    HttpWindowUpdateFrame,
)
from ..protocol import HttpVersion
from .ahparser cimport *
from .buffer cimport Buffer

try:
    from typing import TYPE_CHECKING
except Exception:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Callable


cdef class H2Parser:
    cdef:
        Buffer _buffer
        ahp_splitter_t _splitter

        ahp_msgbuf_t _header_buffer
        ahp_hpack_t _hpack

        object _create_frame  # frame工厂
        object _on_frame  # 完整 http frame 解析完成回调

        object _request

    def __cinit__(self):
        cdef int errno = ahp_msgbuf_init(&self._header_buffer, 1024)
        if errno != 0:
            raise Exception("Failed to init Buffer. errno:{}".format(errno))

        # 注册 splitter 回调
        self._splitter.data = <void*> self
        self._splitter.alloc_frame = __alloc_frame_delegate
        self._splitter.free_frame = __free_frame_delegate
        self._splitter.on_frame_received = __frame_received_callback
        self._splitter.on_data_frame = __data_frame_callback
        self._splitter.on_headers_frame = __headers_frame_callback
        self._splitter.on_settings_frame = __settings_frame_callback
        self._splitter.on_window_update_frame = __window_update_frame_callback

        # 注册 hpack 回调
        self._hpack.data = <void*> self
        self._hpack.on_header_field = __header_field_callback

    def __dealloc__(self):
        ahp_msgbuf_free(&self._header_buffer)

    def __init__(self, buffer, create_frame, on_frame):  # type:(Buffer, Callable[[HttpFrame], int]) -> None
        self._buffer = buffer  # 注入msgbuf
        self._create_frame = create_frame  # 注入frame工厂
        self._on_frame = on_frame  # 注入frame处理回调

    def parse(self):
        """接收新数据"""

        cdef int errno = ahp_split_frame(&self._splitter, &self._buffer._buffer)
        if errno != EAGAIN:
            return -1

        return 0

    cdef void* _alloc_frame(self, uint8_t frame_type, uint8_t flags, uint32_t identifier, ahp_strlen_t *payload):
        frame = self._create_frame(frame_type, flags, identifier)
        if frame is None:
            return NULL
        # 将frame传递到c库中, 加引用
        Py_INCREF(frame)
        return <void*>frame

    cdef void _free_frame(self, void *frame_ptr):
        frame = <object> frame_ptr
        # c库释放frame, 减引用
        Py_DECREF(frame)

    cdef int _on_frame_received(self, void *frame_ptr):
        frame: HttpFrame = <object> frame_ptr
        return self._on_frame(frame)

    cdef int _on_data_frame(self, void *frame_ptr, ahp_strlen_t *data):
        frame: HttpDataFrame = <object> frame_ptr
        # NOTE: 数据拷贝(payload)
        frame.data = data.str[:data.len]
        return 0

    cdef int _on_headers_frame(self, void *frame_ptr, ahp_strlen_t *header_block_fragment):
        cdef int errno = ahp_msgbuf_append(&self._header_buffer, header_block_fragment.str, header_block_fragment.len)
        if errno != 0:
            return errno

        frame: HttpHeadersFrame = <object> frame_ptr
        self._request = frame.request
        errno = ahp_hpack_decode(&self._hpack, &self._header_buffer)

        if errno == 0 or (errno == EAGAIN and (frame.flag & AHP_FRAME_FLAG_END_HEADERS) == 0):
            return 0

        return EBADMSG

    cdef int _on_settings_frame(self, void *frame_ptr, uint16_t identifier, uint32_t value):
        frame: HttpSettingsFrame = <object> frame_ptr
        frame.settings[identifier] = value
        return 0

    cdef int _on_window_update_frame(sel, void *frame_ptr, uint32_t increment):
        frame: HttpWindowUpdateFrame = <object> frame_ptr
        frame.increment = increment
        return 0

    cdef int _on_header_field(self, ahp_strlen_t* name, ahp_strlen_t* value):
        field_name = name.str[:name.len]
        if name.str[0] == 0x3A:
            if field_name == b":method":
                self._request.method = value.str[:value.len]
            elif field_name == b":path":
                self._request.uri = value.str[:value.len]
            elif field_name == b":authority":
                self._request[b"host"] = value.str[:value.len]
        else:
            self._request[field_name] = value.str[:value.len]
        return 0


cdef void* __alloc_frame_delegate(ahp_splitter_t *splitter, uint8_t type, uint8_t flags, uint32_t identifier, ahp_strlen_t *payload):
    cdef H2Parser obj = <H2Parser> splitter.data
    return obj._alloc_frame(type, flags, identifier, payload)

cdef void __free_frame_delegate(ahp_splitter_t *splitter, void *frame):
    cdef H2Parser obj = <H2Parser> splitter.data
    obj._free_frame(frame)

cdef int __frame_received_callback(ahp_splitter_t *splitter, void *frame):
    cdef H2Parser obj = <H2Parser> splitter.data
    return obj._on_frame_received(frame)

cdef int __data_frame_callback(ahp_splitter_t *splitter, void *frame, ahp_strlen_t *data):
    cdef H2Parser obj = <H2Parser> splitter.data
    return obj._on_data_frame(frame, data)

cdef int __headers_frame_callback(ahp_splitter_t *splitter, void *frame, ahp_strlen_t *header_block_fragment):
    cdef H2Parser obj = <H2Parser> splitter.data
    return obj._on_headers_frame(frame, header_block_fragment)

cdef int __settings_frame_callback(ahp_splitter_t *splitter, void *frame, uint16_t identifier, uint32_t value):
    cdef H2Parser obj = <H2Parser> splitter.data
    return obj._on_settings_frame(frame, identifier, value)

cdef int __window_update_frame_callback(ahp_splitter_t *splitter, void *frame, uint32_t increment):
    cdef H2Parser obj = <H2Parser> splitter.data
    return obj._on_window_update_frame(frame, increment)

cdef int __header_field_callback(ahp_hpack_t* hpack, ahp_strlen_t* name, ahp_strlen_t* value):
    cdef H2Parser obj = <H2Parser> hpack.data
    return obj._on_header_field(name, value)
