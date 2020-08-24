/**
 * file: parser.h
 * author: James Yin<ywhjames@hotmail.com>
 * description: http parser
 */
#ifndef AHPARSER_PARSER_H_
#define AHPARSER_PARSER_H_

#include <stdint.h>

#include "http.h"
#include "msgbuf.h"
#include "strlen.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum ahp_parser_state {
  AHP_PARSER_STATE_IDLE,
  AHP_PARSER_STATE_PARSE_REQUEST_LINE,
  AHP_PARSER_STATE_PARSE_RESPONSE_LINE,
  AHP_PARSER_STATE_PARSE_MESSAGE_HEADER,
  AHP_PARSER_STATE_PARSE_BODY,
  AHP_PARSER_STATE_PARSE_CHUNKED_HEAD,
  AHP_PARSER_STATE_PARSE_CHUNKED_DATA,
  AHP_PARSER_STATE_PARSE_CHUNKED_TRAILER
} ahp_parser_state_t;

struct ahp_parser;
typedef struct ahp_parser ahp_parser_t;

typedef int (*ahp_request_line_callback)(ahp_parser_t* parser,
                                         ahp_method_t method,
                                         ahp_strlen_t* uri,
                                         ahp_version_t version);
typedef int (*ahp_request_line_ext_callback)(ahp_parser_t* parser,
                                             ahp_strlen_t* method,
                                             ahp_strlen_t* uri,
                                             ahp_version_t version);
typedef int (*ahp_message_header_callback)(ahp_parser_t* parser, ahp_strlen_t* name, ahp_strlen_t* value);
typedef int (*ahp_message_body_callback)(ahp_parser_t* parser, ahp_strlen_t* body);

struct ahp_parser {
  ahp_parser_state_t state;
  long expected_length;

  void* data;

  // callbacks
  ahp_request_line_callback on_request_line;
  ahp_request_line_ext_callback on_request_line_ext;
  ahp_message_header_callback on_message_header;
  ahp_message_body_callback on_message_body;
};

static inline void ahp_parse_reset(ahp_parser_t* parser) {
  parser->state = AHP_PARSER_STATE_IDLE;
}

int ahp_parse_request(ahp_parser_t* parser, ahp_msgbuf_t* msg);
int ahp_parse_body_length(ahp_parser_t* parser, ahp_msgbuf_t* msg, long length);
int ahp_parse_body_chunked(ahp_parser_t* parser, ahp_msgbuf_t* msg);
int ahp_parse_body(ahp_parser_t* parser, ahp_msgbuf_t* msg);

#ifdef __cplusplus
}
#endif

#endif  // AHPARSER_PARSER_H_
