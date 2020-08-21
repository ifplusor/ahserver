/**
 * file:         parser.c
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  simple http message parser
 * reference:
 *
 *     RFC5234: https://tools.ietf.org/html/rfc5234
 *     RFC7230: https://tools.ietf.org/html/rfc7230
 *     RFC7231: https://tools.ietf.org/html/rfc7231
 *
 */

#include <errno.h>
#include <stdio.h>
#include <string.h>

#include <ahparser/parser.h>
#include <ahparser/strbuf.h>

/**
 * 解码 HEX
 */
int parse_hex(strbuf_t* buf, ahp_strlen_t* str) {
  /*
   * hex  = 1*HEX
   */

  ahp_strlen_t t;
  if (str == NULL) {
    str = &t;
  }
  strbuf_consume(buf, AHP_RULES_HEX, str);
  if (str->len <= 0) {
    return -1;  // 未能取得 HEX 字符串
  } else {
    return 0;
  }
}

/**
 * 从报文中提取一行 ( 包含 CRLF )
 */
int ahp_consume_line(strbuf_t* msg, strbuf_t* line) {
  unsigned char* cur = strbuf_pos(msg);
  unsigned char* end = strbuf_end(msg);

  while (cur < end) {
    if (*cur == AHP_RULES_CR) {
      cur++;
      if (cur == end) {
        return EAGAIN;
      }
      if (*cur == AHP_RULES_LF) {
        // received CRLF
        cur++;
        if (line != NULL) {
          strbuf_init_with_buf(line, strbuf_pos(msg), cur - strbuf_pos(msg));
        }
        strbuf_rewind(msg, cur);  // 调整 buf
        return 0;
      } else {
        // 在 http 报文头中, \r 后面必须紧接着 \n 凑成 CRLF 对
        return EBADMSG;
      }
    }
    cur++;
  }

  // wait more data
  return EAGAIN;
}

/**
 * 解码 quoted-string
 */
int ahp_parse_quoted(strbuf_t* buf, ahp_strlen_t* str) {
  /*
   * In Section 3.2.6. of [RFC7230]
   *
   *   quoted-string  = DQUOTE *( qdtext / quoted-pair ) DQUOTE
   *   qdtext         = HTAB / SP /%x21 / %x23-5B / %x5D-7E / obs-text
   *   obs-text       = %x80-FF
   *
   *   quoted-pair    = "\" ( HTAB / SP / VCHAR / obs-text )
   */

  int err = 0;
  unsigned char* start = strbuf_pos(buf);

  int ch = strbuf_pop(buf);
  if (ch != '"') {
    err = EBADMSG;
    goto error;
  }

  for (;;) {
    ch = strbuf_pop(buf);

    // terminal sign
    if (ch == '"') {
      break;
    }

    // quoted-pair
    else if (ch == '\\') {
      ch = strbuf_pop(buf);
      if (ch == EOF || !AHP_RULES_ETEXT[ch]) {
        err = EBADMSG;
        goto error;
      }
    }

    else if (ch == EOF || !AHP_RULES_QDTEXT[ch]) {
      err = EBADMSG;
      goto error;
    }
  }

  if (str != NULL) {
    // 去 \"
    str->str = (char*)start + 1;
    str->len = buf->pos - start - 2;
  }

  goto success;

error:
  if (err == EAGAIN) {
    strbuf_rewind(buf, start);  // 恢复 buf
  }
  goto finally;

success:
  err = 0;
  goto finally;

finally:
  return err;
}

/**
 * 解码请求方法 ( 从请求行中 )
 */
int parse_method(strbuf_t* buf, ahp_strlen_t* str) {
  /*
   * method         = token
   * token          = 1*tchar
   */
  return strbuf_consume_expectc(buf, AHP_RULES_TCHAR, AHP_RULES_SP, str);
}

/**
 * 将方法字符串转换为枚举量
 */
ahp_method_t str2method(ahp_strlen_t* method) {
  /*
   * In Section 4.1. of [RFC7231], Overview:
   *
   * This specification defines a number of standardized methods that are
   * commonly used in HTTP, as outlined by the following table.  By
   * convention, standardized methods are defined in all-uppercase
   * US-ASCII letters.
   *
   * +---------+-------------------------------------------------+-------+
   * | Method  | Description                                     | Sec.  |
   * +---------+-------------------------------------------------+-------+
   * | GET     | Transfer a current representation of the target | 4.3.1 |
   * |         | resource.                                       |       |
   * | HEAD    | Same as GET, but only transfer the status line  | 4.3.2 |
   * |         | and header section.                             |       |
   * | POST    | Perform resource-specific processing on the     | 4.3.3 |
   * |         | request payload.                                |       |
   * | PUT     | Replace all current representations of the      | 4.3.4 |
   * |         | target resource with the request payload.       |       |
   * | DELETE  | Remove all current representations of the       | 4.3.5 |
   * |         | target resource.                                |       |
   * | CONNECT | Establish a tunnel to the server identified by  | 4.3.6 |
   * |         | the target resource.                            |       |
   * | OPTIONS | Describe the communication options for the      | 4.3.7 |
   * |         | target resource.                                |       |
   * | TRACE   | Perform a message loop-back test along the path | 4.3.8 |
   * |         | to the target resource.                         |       |
   * +---------+-------------------------------------------------+-------+
   *
   */

  if (*(method->str) == 'G') {
    if (method->len == 3 && strncmp(method->str, "GET", 3) == 0) {
      return AHP_METHOD_GET;
    }
  } else if (*(method->str) == 'P') {
    if (method->len == 4) {
      if (strncmp(method->str, "POST", 4) == 0) {
        return AHP_METHOD_POST;
      }
    } else if (method->len == 3) {
      if (strncmp(method->str, "PUT", 3) == 0) {
        return AHP_METHOD_PUT;
      }
    }
  } else if (*(method->str) == 'O') {
    if (method->len == 7 && strncmp(method->str, "OPTIONS", 7) == 0) {
      return AHP_METHOD_OPTIONS;
    }
  } else if (*(method->str) == 'D') {
    if (method->len == 6 && strncmp(method->str, "DELETE", 6) == 0) {
      return AHP_METHOD_DELETE;
    }
  } else if (*(method->str) == 'C') {
    if (method->len == 7 && strncmp(method->str, "CONNECT", 7) == 0) {
      return AHP_METHOD_CONNECT;
    }
  } else if (*(method->str) == 'H') {
    if (method->len == 4 && strncmp(method->str, "HEAD", 4) == 0) {
      return AHP_METHOD_HEAD;
    }
  } else if (*(method->str) == 'T') {
    if (method->len == 5 && strncmp(method->str, "TRACE", 5) == 0) {
      return AHP_METHOD_TRACE;
    }
  }

  return AHP_METHOD_CUSTOM;
}

/**
 * 解码 URI ( 从请求行中 )
 */
int parse_uri(strbuf_t* buf, ahp_strlen_t* str) {
  /*
   * request-target = origin-form
   *                / absolute-form
   *                / authority-form
   *                / asterisk-form
   *
   * origin-form    = absolute-path [ "?" query ]
   * absolute-form  = absolute-URI
   * authority-form = authority
   * asterisk-form  = "*"
   *
   * absolute-path = 1*( "/" segment )
   * query         = <query, see [RFC3986], Section 3.4>
   * absolute-URI  = <absolute-URI, see [RFC3986], Section 4.3>
   * authority     = <authority, see [RFC3986], Section 3.2>
   *
   */

  // 获得合法字符的序列，未验证 uri 的合法性
  return strbuf_consume_expectc(buf, AHP_RULES_URL, AHP_RULES_SP, str);
}

/**
 * 解码 HTTP 版本号 ( 从请求行中 )
 */
int parse_version(strbuf_t* buf, ahp_version_t* version) {
  /*
   * HTTP-version  = HTTP-name "/" DIGIT "." DIGIT
   * HTTP-name     = %x48.54.54.50 ; "HTTP", case-sensitive
   */

  if (strbuf_expect(buf, "HTTP/", 5) != 0) {
    return -1;
  }

  if (buf->pos[1] == AHP_RULES_DOT) {
    char major = (char)buf->pos[0];
    char minor = (char)buf->pos[2];
    if (major == '1') {
      if (minor == '0') {
        *version = AHP_VERSION_10;
      } else if (minor == '1') {
        *version = AHP_VERSION_11;
      } else {
        return -1;
      }
    } else if (major == '2' && minor == '0') {
      *version = AHP_VERSION_20;
    } else {
      return -1;
    }

    buf->pos += 3;
  } else {
    return -1;
  }

  if (strbuf_expect(buf, "\r\n", 2) != 0) {
    return -1;
  }

  return 0;
}

/**
 * 解码请求行
 */
int ahp_parse_request_line(ahp_parser_t* parser, strbuf_t* msg) {
  /*
   * request-line   = method SP request-target SP HTTP-version CRLF
   */

  // Method
  ahp_strlen_t method;
  if (parse_method(msg, &method) != 0) {
    return EBADMSG;
  }

  // Request-URI
  ahp_strlen_t uri;
  if (parse_uri(msg, &uri) != 0) {
    return EBADMSG;
  }

  // HTTP-Version
  ahp_version_t version;
  if (parse_version(msg, &version) != 0) {
    return EBADMSG;
  }

  // callback
  ahp_method_t e_method = str2method(&method);
  if ((e_method == AHP_METHOD_CUSTOM ? parser->on_request_line_ext(parser, &method, &uri, version)
                                     : parser->on_request_line(parser, e_method, &uri, version)) != 0) {
    return EBADMSG;
  }

  return 0;
}

int ahp_parse_message_header(ahp_parser_t* parser, strbuf_t* msg) {
  /*
   * In Section 3.2 of [RFC7230], the definition of Message Headers as shown below:
   *
   *   header-field   = field-name ":" OWS field-value OWS
   *
   *   field-name     = token
   *   field-value    = *( field-content / obs-fold )
   *   field-content  = field-vchar [ 1*( SP / HTAB ) field-vchar ]
   *   field-vchar    = VCHAR / obs-text
   *
   *   obs-fold       = CRLF 1*( SP / HTAB )
   *                  ; obsolete line folding
   */

  ahp_strlen_t name;
  if (strbuf_consume_expectc(msg, AHP_RULES_TCHAR, ':', &name) != 0) {
    return EBADMSG;
  }

  ahp_strlen_t value;

  // trim preceded space
  strbuf_skip(msg, AHP_RULES_HTSP);
  unsigned char* start = strbuf_pos(msg);

  int has_fold = 0;
  for (;;) {
    if (strbuf_consume_expectc(msg, AHP_RULES_ETEXT, '\r', &value) != 0 || strbuf_expectc(msg, '\n') != 0) {
      return EBADMSG;
    }

    // obs-fold
    if (strbuf_expects(msg, AHP_RULES_HTSP)) {
      break;
    }
    has_fold = 1;
    strbuf_skip(msg, AHP_RULES_HTSP);
  }

  // trim followed space
  unsigned char* end = strbuf_pos(msg) - 2;
  while (end > start) {
    if (!AHP_RULES_FLOD[*(end - 1)]) {
      break;
    }
  }

  value.str = (char*)start;
  value.len = end - start;

  // replace obs-fold by SP
  if (has_fold != 0) {
    for (; start < end; start++) {
      if (*start == '\r') {
        break;
      }
    }
    for (unsigned char* it = start; it < end;) {
      if (*it == '\r') {
        *start++ = ' ';
        // clang-format off
        while (AHP_RULES_FLOD[*++it]);
        // clang-format on
      } else {
        *start++ = *it++;
      }
    }
    value.len = (char*)start - value.str;
  }

  if (parser->on_message_header(parser, &name, &value) != 0) {
    return EBADMSG;
  }

  return 0;
}

/**
 * 解码请求报文头 ( Request-Line + Headers )
 */
int ahp_parse_request(ahp_parser_t* parser, ahp_msgbuf_t* msg) {
  /*
   * Request = Request-Line
   *           *(( General-Header
   *            | Request-Header
   *            | Entity-Header ) CRLF)
   *           CRLF
   *           [ Entity-Body ]
   */

  int err = 0;

  strbuf_t message;
  strbuf_init_with_msgbuf(&message, msg);

  for (;;) {
    switch (parser->state) {
      case AHP_PARSER_STATE_IDLE:
        // 初始化
        parser->state = AHP_PARSER_STATE_PARSE_REQUEST_LINE;

      case AHP_PARSER_STATE_PARSE_REQUEST_LINE: {
        strbuf_t line;
        // 从缓冲区中读取一行
        err = ahp_consume_line(&message, &line);
        if (err) {
          goto error;
        }

        // 解析请求行
        err = ahp_parse_request_line(parser, &line);
        if (err) {
          goto error;
        }

        parser->state = AHP_PARSER_STATE_PARSE_MESSAGE_HEADER;
      }

      case AHP_PARSER_STATE_PARSE_MESSAGE_HEADER: {
        unsigned char* start = strbuf_pos(&message);
        strbuf_t line;
        for (;;) {
          // 从缓冲区中读取一行
          err = ahp_consume_line(&message, &line);
          if (err) {
            if (err == EAGAIN) {
              strbuf_rewind(&message, start);
            }
            goto error;
          }

          if (line.size <= 2) {
            // 空行 ( 连续两个 crlf ), request header 结束
            goto success;
          }

          // 因为 LWS 的关系，crlf 不能做为 header 的分界符，因此要多看一个 OCTET
          int ch = strbuf_peek(&message);
          if (ch == EOF) {
            err = EAGAIN;
            strbuf_rewind(&message, start);
            goto error;
          } else if (ch != AHP_RULES_SP && ch != AHP_RULES_HT) {
            strbuf_init_with_buf(&line, start, strbuf_pos(&message) - start);

            // 解析消息头
            err = ahp_parse_message_header(parser, &line);
            if (err) {
              goto error;
            }

            // new header
            start = strbuf_pos(&message);
          }
        }
      }

      case AHP_PARSER_STATE_PARSE_MESSAGE_HEADER_CRLF: {
        unsigned char* start = strbuf_pos(&message);
        strbuf_t line;

        // 从缓冲区中读取一行
        err = ahp_consume_line(&message, &line);
        if (err) {
          if (err == EAGAIN) {
            strbuf_rewind(&message, start);
          }
          goto error;
        }

        if (line.size <= 2) {
          // 空行 ( 连续两个 crlf ), request header 结束
          goto success;
        }

        err = EBADMSG;
        goto error;
      }

      default:
        // unexpected state, parser 不可用
        return EBUSY;
    }
  }

error:
  goto finally;

success:
  parser->state = AHP_PARSER_STATE_IDLE;
  err = 0;
  goto finally;

finally:
  ahp_msgbuf_forward(msg, strbuf_consume_length(&message));  // 释放已被正确解码的缓冲
  return err;
}

int ahp_parse_length_body(ahp_parser_t* parser, strbuf_t* msg) {
  // 按长度定位 body
  if (parser->content_length > 0) {
    long size = strbuf_remain_length(msg);
    if (size > parser->content_length) {
      size = parser->content_length;
    }
    ahp_strlen_t body;
    strbuf_consume_len(msg, size, &body);
    if (parser->on_message_body(parser, &body) != 0) {
      return EBADMSG;
    }
    parser->content_length -= size;
    if (parser->content_length > 0) {
      return EAGAIN;
    }
  }
  return 0;
}

int ahp_parse_chunked_size(ahp_parser_t* parser, strbuf_t* msg) {
  /*
   * chunk-size     = 1*HEXDIG
   */

  // 解析 chunk 长度
  ahp_strlen_t chunk_size;
  if (parse_hex(msg, &chunk_size) != 0) {
    return EBADMSG;
  }

  // after is extension or crlf
  int ch = strbuf_peek(msg);
  if (ch != '\r' && ch != ';') {
    return EBADMSG;
  } else {
    parser->chunk_size = htoi(&chunk_size);
    return 0;
  }
}

int ahp_parse_chunked_ext(ahp_parser_t* parser, strbuf_t* msg) {
  /*
   * chunk-ext      = *( ";" chunk-ext-name [ "=" chunk-ext-val ] )
   *
   * chunk-ext-name = token
   * chunk-ext-val  = token | quoted-string
   */

  // 解析 chunk extension
  while (strbuf_expectc(msg, ';') == 0) {
    ahp_strlen_t name, val;

    if (strbuf_consume_expectc(msg, AHP_RULES_TCHAR, '=', &name) != 0) {
      return EBADMSG;
    }

    if ((strbuf_peek(msg) == '"' ? ahp_parse_quoted(msg, &val) : strbuf_consume(msg, AHP_RULES_TCHAR, &val)) != 0) {
      return EBADMSG;
    }

    // TODO: has extension
  }

  if (strbuf_remain_length(msg) > 2) {
    return EBADMSG;
  }

  return 0;
}

int ahp_parse_chunked_data(ahp_parser_t* parser, strbuf_t* msg) {
  if (parser->chunk_size > 0) {
    long size = strbuf_remain_length(msg);
    if (size > parser->chunk_size) {
      size = parser->chunk_size;
    }
    ahp_strlen_t data;
    strbuf_consume_len(msg, size, &data);
    if (parser->on_message_body(parser, &data) != 0) {
      return EBADMSG;
    }
    parser->chunk_size -= size;
    if (parser->chunk_size > 0) {
      return EAGAIN;
    }
  }
  if (strbuf_remain_length(msg) < 2) {
    return EAGAIN;
  }
  if (strbuf_expect(msg, "\r\n", 2) != 0) {
    return EBADMSG;
  }
  return 0;
}

int ahp_parse_chunked_trailer(ahp_parser_t* parser, strbuf_t* msg) {
  /*
   * trailer-part   = *( header-field CRLF )
   */

  int err;
  unsigned char* start = strbuf_pos(msg);
  strbuf_t line;
  for (;;) {
    // 从缓冲区中读取一行
    err = ahp_consume_line(msg, &line);
    if (err) {
      if (err == EAGAIN) {
        strbuf_rewind(msg, start);
      }
      return err;
    }

    if (line.size <= 2) {
      // The end of chunked encoding is CRLF after trailer-part.
      return 0;
    }

    // TODO: 解析消息头
    // err = ahp_parse_message_header(parser, &line);
    // if (err) {
    //   return err;
    // }

    // new header
    start = strbuf_pos(msg);
  }
}

/**
 * 解码报文体
 */
int ahp_parse_body(ahp_parser_t* parser, ahp_msgbuf_t* msg) {
  int err;

  strbuf_t message;
  strbuf_init_with_msgbuf(&message, msg);

  for (;;) {
    switch (parser->state) {
        /*
         * Content-Length
         */

      case AHP_PARSER_STATE_PARSE_BODY: {
        err = ahp_parse_length_body(parser, &message);
        if (err) {
          goto error;
        }
        goto success;
      }

        /*
         * chunked-body   = *chunk
         *                  last-chunk
         *                  trailer-part
         *                  CRLF
         *
         * chunk          = chunk-size [ chunk-ext ] CRLF
         *                  chunk-data CRLF
         * chunk-size     = 1*HEXDIG
         * last-chunk     = 1*("0") [ chunk-ext ] CRLF
         *
         * chunk-data     = 1*OCTET ; a sequence of chunk-size octets
         *
         */

      case AHP_PARSER_STATE_PARSE_CHUNKED_HEAD: {
        // 从缓冲区中读取一行
        strbuf_t line;
        err = ahp_consume_line(&message, &line);
        if (err) {
          goto error;
        }

        err = ahp_parse_chunked_size(parser, &line);
        if (err) {
          goto error;
        }

        err = ahp_parse_chunked_ext(parser, &line);
        if (err) {
          goto error;
        }

        if (parser->chunk_size <= 0) {
          // last-chunk
          parser->state = AHP_PARSER_STATE_PARSE_CHUNKED_TRAILER;
          break;
        }

        parser->state = AHP_PARSER_STATE_PARSE_CHUNKED_DATA;
      }

      case AHP_PARSER_STATE_PARSE_CHUNKED_DATA: {
        err = ahp_parse_chunked_data(parser, &message);
        if (err) {
          goto error;
        }
        parser->state = AHP_PARSER_STATE_PARSE_CHUNKED_HEAD;
        break;
      }

      case AHP_PARSER_STATE_PARSE_CHUNKED_TRAILER: {
        err = ahp_parse_chunked_trailer(parser, &message);
        if (err) {
          goto error;
        }
        goto success;
      }

      default:
        // unexpected state, parser 不可用
        return EBUSY;
    }
  }

error:
  goto finally;

success:
  parser->state = AHP_PARSER_STATE_IDLE;
  err = 0;
  goto finally;

finally:
  ahp_msgbuf_forward(msg, strbuf_consume_length(&message));
  return err;
}

int ahp_parse_body_length(ahp_parser_t* parser, ahp_msgbuf_t* msg, long length) {
  if (parser->state != AHP_PARSER_STATE_IDLE) {
    // unexpected state, parser 不可用
    return EBUSY;
  }

  // 初始化
  parser->content_length = length;
  parser->state = AHP_PARSER_STATE_PARSE_BODY;

  return ahp_parse_body(parser, msg);
}

int ahp_parse_body_chunked(ahp_parser_t* parser, ahp_msgbuf_t* msg) {
  if (parser->state != AHP_PARSER_STATE_IDLE) {
    // unexpected state, parser 不可用
    return EBUSY;
  }

  // 初始化
  parser->state = AHP_PARSER_STATE_PARSE_CHUNKED_HEAD;

  return ahp_parse_body(parser, msg);
}
