/**
 * file: parser.h
 * author: James Yin<weihe.yin@istarshine.com>
 * description:
 *
 *   ahparser 是为 async io 设计的 http 报文解析器。ahparser 只专注于报文解析，
 *   使用 delegate 模式解耦 http 协议处理职责，使用状态机机制支持异步模式下网络 io 与解析运算的交错运行。
 *
 */

/*
 * API 约定:
 *   所有以 ahp_ 作为前缀的函数，都以 errno 作为返回值;
 *   所有不以 ahp_ 作为前缀的解码函数，失败后不应产生副作用;
 *
 * API 返回值说明:
 *   0       - 操作成功
 *   EAGAIN  - 需要更多数据
 *   EBADMSG - 报文格式错误
 */

#ifndef AHPARSER_PARSER_H
#define AHPARSER_PARSER_H

#include "strlen.h"
#include "msgbuf.h"
#include "http.h"


typedef enum ahp_parse_state {
  AHP_STATE_PARSE_IDLE,
  AHP_STATE_PARSE_REQUEST_LINE,
  AHP_STATE_PARSE_RESPONSE_LINE,
  AHP_STATE_PARSE_MESSAGE_HEADER,
  AHP_STATE_PARSE_MESSAGE_HEADER_LWS,
  AHP_STATE_PARSE_LENGTH_BODY,
  AHP_STATE_PARSE_CHUNKED_SIZE,
  AHP_STATE_PARSE_CHUNKED_EXT,
  AHP_STATE_PARSE_CHUNKED_DATA,
  AHP_STATE_PARSE_CHUNKED_TRAILER
} ahp_parse_state_t;


struct ahp_parser;
typedef struct ahp_parser ahp_parser_t;


typedef int (*ahp_request_line_cb)(ahp_parser_t *parser, ahp_method_t method, ahp_strlen_t *uri, ahp_version_t version);
typedef int (*ahp_request_line_cm_cb)(ahp_parser_t *parser, ahp_strlen_t *method, ahp_strlen_t *uri, ahp_version_t version);
typedef int (*ahp_message_header_cb)(ahp_parser_t *parser, ahp_strlen_t *name, ahp_strlen_t *value);
typedef int (*ahp_message_body_cb)(ahp_parser_t *parser, ahp_strlen_t *body);


struct ahp_parser {
  ahp_parse_state_t state;
  long content_length;
  long chunk_size;

  void *data;

  // callbacks
  ahp_request_line_cb    on_request_line;
  ahp_request_line_cm_cb on_request_line_cm;
  ahp_message_header_cb  on_message_header;
  ahp_message_body_cb    on_message_body;
};


inline void ahp_parse_reset(ahp_parser_t *parser) {
  parser->state = AHP_STATE_PARSE_IDLE;
}

int ahp_parse_request(ahp_parser_t *parser, ahp_msgbuf_t *msg);
int ahp_parse_body_length(ahp_parser_t *parser, ahp_msgbuf_t *msg, long length);
int ahp_parse_body_chunked(ahp_parser_t *parser, ahp_msgbuf_t *msg);
int ahp_parse_body(ahp_parser_t *parser, ahp_msgbuf_t *msg);

#endif
