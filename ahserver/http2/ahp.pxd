# encoding=utf-8


cdef extern from "ahparser/parser.h":

    #
    # strlen.h

    ctypedef struct ahp_strlen_t:
        char *str
        long len

    #
    # msgbuf.h

    ctypedef struct ahp_msgbuf_t:
        pass

    int ahp_msgbuf_init(ahp_msgbuf_t *buf, long size);
    void ahp_msgbuf_free(ahp_msgbuf_t *buf);
    int ahp_msgbuf_append(ahp_msgbuf_t *buf, const char *data, unsigned long len);
    void ahp_msgbuf_reset(ahp_msgbuf_t *buf);

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

    # callbacks
    ctypedef int (*ahp_request_line_cb)(ahp_parser_t *parser, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version);
    ctypedef int (*ahp_request_line_cm_cb)(ahp_parser_t *parser, ahp_strlen_t *method, ahp_strlen_t *uri, ahp_version_t version);
    ctypedef int (*ahp_message_header_cb)(ahp_parser_t *parser, ahp_strlen_t *name, ahp_strlen_t *value);
    ctypedef int (*ahp_message_body_cb)(ahp_parser_t *parser, ahp_strlen_t *body);

    ctypedef struct ahp_parser_t:
        void *data;
        ahp_request_line_cb    on_request_line;
        ahp_request_line_cm_cb on_request_line_cm;
        ahp_message_header_cb  on_message_header;
        ahp_message_body_cb    on_message_body;

    void ahp_parse_reset(ahp_parser_t *parser);
    int ahp_parse_request(ahp_parser_t *parser, ahp_msgbuf_t *msg);
    int ahp_parse_body_length(ahp_parser_t *parser, ahp_msgbuf_t *msg, long length);
    int ahp_parse_body_chunked(ahp_parser_t *parser, ahp_msgbuf_t *msg);
    int ahp_parse_body(ahp_parser_t *parser, ahp_msgbuf_t *msg);
