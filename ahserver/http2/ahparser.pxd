# encoding=utf-8

from libc.stdint cimport uint8_t, uint16_t, uint32_t

cdef extern from "ahparser/ahparser.h":

    #
    # strlen.h

    ctypedef struct ahp_strlen_t:
        char *str
        long len

    #
    # msgbuf.h

    ctypedef struct ahp_msgbuf_t:
        pass

    int ahp_msgbuf_init(ahp_msgbuf_t *buf, long size)
    void ahp_msgbuf_free(ahp_msgbuf_t *buf)
    int ahp_msgbuf_append(ahp_msgbuf_t *buf, const char *data, unsigned long len)
    int ahp_msgbuf_copy(ahp_msgbuf_t *src, ahp_msgbuf_t *dst)
    char *ahp_msgbuf_data(ahp_msgbuf_t *buf)
    long ahp_msgbuf_length(ahp_msgbuf_t *buf)
    void ahp_msgbuf_reset(ahp_msgbuf_t *buf)

    #
    # http.h

    ctypedef enum ahp_method_t:
        AHP_METHOD_OPTIONS
        AHP_METHOD_GET
        AHP_METHOD_HEAD
        AHP_METHOD_POST
        AHP_METHOD_PUT
        AHP_METHOD_DELETE
        AHP_METHOD_TRACE
        AHP_METHOD_CONNECT

    ctypedef enum ahp_version_t:
        AHP_VERSION_10
        AHP_VERSION_11
        AHP_VERSION_20

    #
    # parser.h

    # parser callbacks
    ctypedef int (*ahp_request_line_callback)(ahp_parser_t *parser, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version)
    ctypedef int (*ahp_request_line_ext_callback)(ahp_parser_t *parser, ahp_strlen_t *method, ahp_strlen_t *uri, ahp_version_t version)
    ctypedef int (*ahp_message_header_callback)(ahp_parser_t *parser, ahp_strlen_t *name, ahp_strlen_t *value)
    ctypedef int (*ahp_message_body_callback)(ahp_parser_t *parser, ahp_strlen_t *body)

    ctypedef struct ahp_parser_t:
        void *data

        ahp_request_line_callback on_request_line
        ahp_request_line_ext_callback on_request_line_ext
        ahp_message_header_callback on_message_header
        ahp_message_body_callback on_message_body

    void ahp_parse_reset(ahp_parser_t *parser)
    int ahp_parse_request(ahp_parser_t *parser, ahp_msgbuf_t *msg)
    int ahp_parse_body_length(ahp_parser_t *parser, ahp_msgbuf_t *msg, long length)
    int ahp_parse_body_chunked(ahp_parser_t *parser, ahp_msgbuf_t *msg)
    int ahp_parse_body(ahp_parser_t *parser, ahp_msgbuf_t *msg)

    # parser hacker methods
    void _ahp_request_header_will_end(ahp_parser_t *parser)

    #
    # splitter.h

    # splitter delegate
    ctypedef void* (*ahp_alloc_frame_delegate)(ahp_splitter_t *splitter, uint8_t type, uint8_t flags, uint32_t identifier, ahp_strlen_t *payload)
    ctypedef void (*ahp_free_frame_delegate)(ahp_splitter_t *splitter, void *frame)

    # splitter callbacks
    ctypedef int (*ahp_frame_received_callback)(ahp_splitter_t *splitter, void *frame)
    ctypedef int (*ahp_data_frame_callback)(ahp_splitter_t *splitter, void *frame, ahp_strlen_t *data)
    ctypedef int (*ahp_settings_frame_callback)(ahp_splitter_t *splitter, void *frame, uint16_t identifier, uint32_t value)

    ctypedef struct ahp_splitter_t:
        void *data

        ahp_alloc_frame_delegate alloc_frame
        ahp_free_frame_delegate free_frame

        ahp_frame_received_callback on_frame_received
        ahp_data_frame_callback on_data_frame
        ahp_settings_frame_callback on_settings_frame

    int ahp_split_frame(ahp_splitter_t *splitter, ahp_msgbuf_t *msg)
