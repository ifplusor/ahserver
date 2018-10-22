/**
 * file:         parser.c
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  simple http message parser
 * reference:    rfc1945, rfc2616
 */

#include <stdio.h>
#include <string.h>
#include <errno.h>

#include "parser.h"
#include "strbuf.h"

/*
 * Augmented BNF:
 *
 *  name = definition
 *    The name of a rule is simply the name itself (without any enclosing "<"
 *    and ">") and is separated from its definition by the equal "=" character.
 *    White space is only significant in that indentation of continuation lines
 *    is used to indicate a rule definition that spans more than one line.
 *    Certain basic rules are in uppercase, such as SP, LWS, HT, CRLF, DIGIT,
 *    ALPHA, etc. Angle brackets are used within definitions whenever their
 *    presence will facilitate discerning the use of rule names.
 *
 *  "literal"
 *    Quotation marks surround literal text. Unless stated otherwise,
 *    the text is case-insensitive.
 *
 *  rule1 | rule2
 *    Elements separated by a bar ("|") are alternatives, e.g.,
 *    "yes | no" will accept yes or no.
 *
 *  (rule1 rule2)
 *    Elements enclosed in parentheses are treated as a single element.
 *    Thus, "(elem (foo | bar) elem)" allows the token sequences
 *    "elem foo elem" and "elem bar elem".
 *
 *  *rule
 *    The character "*" preceding an element indicates repetition.
 *    The full form is "<n>*<m>element" indicating at least <n> and at most <m>
 *    occurrences of element. Default values are 0 and infinity so that
 *    "*(element)" allows any number, including zero; "1*element" requires at
 *    least one; and "1*2element" allows one or two.
 *
 *  [rule]
 *    Square brackets enclose optional elements; "[foo bar]" is equivalent to
 *    "*1(foo bar)".
 *
 *  N rule
 *    Specific repetition: "<n>(element)" is equivalent to "<n>*<n>(element)";
 *    that is, exactly <n> occurrences of (element). Thus 2DIGIT is a 2-digit
 *    number, and 3ALPHA is a string of three alphabetic characters.
 *
 *  #rule
 *    A construct "#" is defined, similar to "*", for defining lists of
 *    elements. The full form is "<n>#<m>element" indicating at least <n> and
 *    at most <m> elements, each separated by one or more commas (",") and
 *    OPTIONAL linear white space (LWS). This makes the usual form of lists
 *    very easy; a rule such as
 *           ( *LWS element *( *LWS "," *LWS element ))
 *    can be shown as
 *           1#element
 *    Wherever this construct is used, null elements are allowed, but do not
 *    contribute to the count of elements present.
 *    That is, "(element), , (element) " is permitted, but counts as only two
 *    elements. Therefore, where at least one element is required, at least one
 *    non-null element MUST be present. Default values are 0 and infinity so
 *    that "#element" allows any number, including zero; "1#element" requires
 *    at least one; and "1#2element" allows one or two.
 *
 *  ; comment
 *    A semi-colon, set off some distance to the right of rule text, starts a
 *    comment that continues to the end of line. This is a simple way of
 *    including useful notes in parallel with the specifications.
 *
 *  implied *LWS
 *    The grammar described by this specification is word-based. Except where
 *    noted otherwise, linear white space (LWS) can be included between any two
 *    adjacent words (token or quoted-string), and between adjacent words and
 *    separators, without changing the interpretation of a field. At least one
 *    delimiter (LWS and/or separators) MUST exist between any two tokens (for
 *    the definition of "token" below), since they would otherwise be
 *    interpreted as a single token.
 *
 */

/**
 * 解码 HEX
 */
int parse_hex(strbuf_t *buf, ahp_strlen_t *str) {
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
int ahp_consume_line(strbuf_t *msg, strbuf_t *line) {
  unsigned char *cur = msg->start;
  unsigned char *end = msg->end;

  while (cur != end) {
    if (*cur == AHP_RULES_CR) {
      cur++;
      if (cur == end) {
        return EAGAIN;
      }
      if (*cur == AHP_RULES_LF) {
        // received CRLF
        cur++;
        if (line != NULL) {
          strbuf_init_with_buf(line, (char*) msg->start, cur - msg->start);
        }
        msg->start = cur;  // 调整 buf
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
int ahp_parse_quoted(strbuf_t *buf, ahp_strlen_t *str) {
  /*
   * quoted-string  = ( <"> *(qdtext | quoted-pair ) <"> )
   * qdtext         = <any TEXT except <">>
   * quoted-pair    = "\" CHAR
   */

  int err;
  unsigned char *start = buf->start;

  int ch = strbuf_pop(buf);
  if (ch == EOF) {
    err = EAGAIN;
    goto error;
  } else if (ch != '"') {
    err = EBADMSG;
    goto error;
  }

  while (1) {
    int ch = strbuf_pop(buf);

    // terminal sign
    if (ch == '"') {
      break;
    }

    // quoted-pair
    else if (ch == '\\') {
      ch = strbuf_pop(buf);
      if (ch == EOF) {
        err = EAGAIN;
        goto error;
      } else if (!AHP_RULES_CHAR[ch]) {
        err = EBADMSG;
        goto error;
      }
    }

    else if (ch == EOF) {
      err = EAGAIN;
      goto error;
    }
    
    // TODO: 未处理 LWS
    else if (!AHP_RULES_TEXT[ch]) {
      err = EBADMSG;
      goto error;
    }
  }

  if (str != NULL) {
    // 去 \"
    str->str = (char*) start + 1;
    str->len = buf->start - start - 2;
  }

  goto success;

error:
  if (err == EAGAIN) {
    buf->start = start;  // 恢复 buf
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
int parse_method(strbuf_t *buf, ahp_strlen_t *str) {
  /*
   * Method         = "OPTIONS"                ; Section 9.2
   *                | "GET"                    ; Section 9.3
   *                | "HEAD"                   ; Section 9.4
   *                | "POST"                   ; Section 9.5
   *                | "PUT"                    ; Section 9.6
   *                | "DELETE"                 ; Section 9.7
   *                | "TRACE"                  ; Section 9.8
   *                | "CONNECT"                ; Section 9.9
   *                | extension-method
   * extension-method = token
   */
  return strbuf_consume_expectc(buf, AHP_RULES_TOKEN, AHP_RULES_SP, str);
}

/**
 * 将方法字符串转换为枚举量
 */
ahp_method_t str2method(ahp_strlen_t *method) {
  // GET, POST, PUT, OPTIONS, DELETE, CONNECT, HEAD, TRACE

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
int parse_uri(strbuf_t *buf, ahp_strlen_t *str) {
  /*
   * Request-URI    = "*" | absoluteURI | abs_path | authority
   */

  // 获得合法字符的序列，未验证 uri 的合法性
  return strbuf_consume_expectc(buf, AHP_RULES_URL, AHP_RULES_SP, str);
}

/**
 * 解码 HTTP 版本号 ( 从请求行中 )
 */
int parse_version(strbuf_t *buf, ahp_version_t *version) {
  /*
   * HTTP-Version = "HTTP" "/" 1*DIGIT "." 1*DIGIT
   */

  int err;
  unsigned char *start = buf->start;

  err = strbuf_expect(buf, "HTTP/", 5);
  if (err) {
    return -1;
  }

  if (buf->start[1] == AHP_RULES_DOT) {
    char major = (char) buf->start[0];
    char minor = (char) buf->start[2];
    if (major == '1') {
      if (minor == '0') {
        *version = AHP_VERSION_10;
      } else if (minor == '1') {
        *version = AHP_VERSION_11;
      } else {
        goto error;
      }
    } else if (major == '2' && minor == '0') {
      *version = AHP_VERSION_20;
    } else {
      goto error;
    }

    buf->start += 3;
  } else {
    goto error;
  }

  err = strbuf_expect(buf, "\r\n", 2);
  if (err) {
    goto error;
  }

  goto success;

error:
  buf->start = start;  // 恢复 buf
  return -1;

success:
  return 0;
}

/**
 * 解码请求行
 */
int ahp_parse_request_line(ahp_parser_t *parser, strbuf_t *msg) {
  /*
   * Request-Line = Method SP Request-URI SP HTTP-Version CRLF
   */

  int err;

  // Method
  ahp_strlen_t method;
  err = parse_method(msg, &method);
  if (err) {
    err = EBADMSG;
    goto error;
  }

  // Request-URI
  ahp_strlen_t uri;
  err = parse_uri(msg, &uri);
  if (err) {
    err = EBADMSG;
    goto error;
  }

  // HTTP-Version
  ahp_version_t version;
  err = parse_version(msg, &version);
  if (err) {
    err = EBADMSG;
    goto error;
  }

  // callback
  ahp_method_t e_method = str2method(&method);
  if (e_method == AHP_METHOD_CUSTOM) {
    err = parser->on_request_line_cm(parser, &method, &uri, version);
  } else {
    err = parser->on_request_line(parser, e_method, &uri, version);
  }
  if (err) {
    err = EBADMSG;
    goto error;
  }

  goto success;

error:
  goto finally;

success:
  err = 0;
  goto finally;

finally:
  return err;
}

int ahp_parse_message_header(ahp_parser_t *parser, strbuf_t *msg) {
  /*
   * message-header = field-name ":" [ field-value ]
   * field-name     = token
   * field-value    = *( field-content | LWS )
   * field-content  = <the OCTETs making up the field-value
   *                  and consisting of either *TEXT or combinations
   *                  of token, separators, and quoted-string>
   */

  int err;

  ahp_strlen_t name;
  err = strbuf_consume_expectc(msg, AHP_RULES_TOKEN, ':', &name);
  if (err) {
    goto error;
  }

  ahp_strlen_t value;
  strbuf_skip(msg, AHP_RULES_HTSP);  // 跳过前导空白
  err = strbuf_consume_expectc(msg, AHP_RULES_TEXT, '\r', &value);
  if (err || strbuf_expectc(msg, '\n')) {
    goto error;
  }

  err = parser->on_message_header(parser, &name, &value);
  if (err) {
    goto error;
  }

//  if (strbuf_expectc(msg, EOF)) {
//    goto error;
//  }

  return 0;

error:
  return EBADMSG;
}


/**
 * 解码请求报文头 ( Request-Line + Headers )
 */
int ahp_parse_request(ahp_parser_t *parser, ahp_msgbuf_t *msg) {
  /*
   * Request = Request-Line
   *           *(( General-Header
   *            | Request-Header
   *            | Entity-Header ) CRLF)
   *           CRLF
   *           [ Entity-Body ]
   */

  int err, ch;

  strbuf_t message, line;
  strbuf_init_with_buf(&message, ahp_msgbuf_data(msg), ahp_msgbuf_length(msg));

  do {
    switch (parser->state) {
      case AHP_STATE_PARSE_IDLE:
        // 初始化
        parser->state = AHP_STATE_PARSE_REQUEST_LINE;

      case AHP_STATE_PARSE_REQUEST_LINE:
        // 从缓冲区中读取一行
        err = ahp_consume_line(&message, &line);
        if (err) goto error;

        // 解析请求行
        err = ahp_parse_request_line(parser, &line);
        if (err) goto error;

        parser->state = AHP_STATE_PARSE_MESSAGE_HEADER;

      case AHP_STATE_PARSE_MESSAGE_HEADER:
        // 从缓冲区中读取一行
        err = ahp_consume_line(&message, &line);
        if (err) goto error;

        if (line.size <= 2) {
          // 空行 ( 连续两个 crlf ), request header 结束
          goto success;
        }

        // 因为 LWS 的关系，crlf 不能做为 header 的分界符，因此要多看一个 OCTET
        ch = strbuf_peek(&message);
        if (ch == EOF) {
          err = EAGAIN;
          goto error;
        }
        if (ch != AHP_RULES_SP && ch != AHP_RULES_HT) {
          // 解析消息头
          err = ahp_parse_message_header(parser, &line);
          if (err) {
            goto error;
          }
          break;
        }

        // LWS: CRLF ' ' or CRLF '\t'
        parser->state = AHP_STATE_PARSE_MESSAGE_HEADER_LWS;

      case AHP_STATE_PARSE_MESSAGE_HEADER_LWS:
        // TODO: parse LWS
        err = EBADMSG;
        goto error;

      default:
        // unexpected state, parser 不可用
        return EBUSY;
    }
  } while (1);

error:
  goto finally;

success:
  parser->state = AHP_STATE_PARSE_IDLE;
  err = 0;
  goto finally;

finally:
  ahp_msgbuf_forward(msg, strbuf_consume_length(&message));  // 释放已被正确解码的缓冲
  return err;
}

int ahp_parse_chunked_size(ahp_parser_t *parser, strbuf_t *msg) {
  /*
   * chunk-size     = 1*HEX
   */

  int err;

  if (strbuf_is_empty(msg)) {
    return EAGAIN;
  }

  // 解析 chunk 长度
  ahp_strlen_t chunk_size_s;
  err = parse_hex(msg, &chunk_size_s);
  if (err) {
    return EBADMSG;
  }

  // after is extension or crlf
  int ch = strbuf_peek(msg);
  if (ch == EOF) {
    return EAGAIN;
  } else if (ch != '\r' && ch != ';') {
    return EBADMSG;
  } else {
    parser->chunk_size = htoi(&chunk_size_s);
    return 0;
  }
}

int ahp_parse_chunked_ext(ahp_parser_t *parser, strbuf_t *msg) {
  /*
   * chunk-extension= *( ";" chunk-ext-name [ "=" chunk-ext-val ] )
   * chunk-ext-name = token
   * chunk-ext-val  = token | quoted-string
   */

  int err;
  unsigned char *start = msg->start;

  // 解析 chunk extension
  while (strbuf_expectc(msg, ';') == 0) {
    ahp_strlen_t ext_name, ext_val;

    err = strbuf_consume_expectc(msg, AHP_RULES_TOKEN, '=', &ext_name);
    if (err) {
      return EBADMSG;
    }

    int ch = strbuf_peek(msg);
    if (ch == '"') {
      err = ahp_parse_quoted(msg, &ext_val);
    } else {
      err = strbuf_consume(msg, AHP_RULES_TOKEN, &ext_val);
    }
    if (err) {
      return EBADMSG;
    }

    // TODO: have extension
  }

  err = strbuf_expect(msg, "\r\n", 2);
  if (err) {
    return EBADMSG;
  }

  return 0;
}

int ahp_parse_chunked_data(ahp_parser_t *parser, strbuf_t *msg) {

  int err;

  ahp_strlen_t chunked_data = {
    .str = (char*) msg->start,
    .len = parser->chunk_size
  };
  // TODO:

  strbuf_fast_forward(msg, parser->chunk_size);

  err = strbuf_expect(msg, "\r\n", 2);
  if (err) {
    return EBADMSG;
  }

  // TODO: 未处理 trailer

  err = strbuf_expect(msg, "\r\n", 2);
  if (err) {
    return EBADMSG;
  }

  if (parser->chunk_size > 0) {
    // 还有后续 chunked 包
    return EAGAIN;
  } else {
    // 最后一个 chunked 包
    return 0;
  }

  return 0;
}

/**
 * 解码报文体
 */
int ahp_parse_body(ahp_parser_t *parser, ahp_msgbuf_t *msg) {
  int err;

  strbuf_t message, line;
  strbuf_init_with_buf(&message, ahp_msgbuf_data(msg), ahp_msgbuf_length(msg));

  ahp_strlen_t body;
  do {
    switch (parser->state) {
      /*
       * Content-Length
       */

      case AHP_STATE_PARSE_LENGTH_BODY:
        // 按长度定位 body
        err = strbuf_consume_len(&message, parser->content_length, &body);
        if (err) {
          err = EAGAIN;
          goto error;
        }
        err = parser->on_message_body(parser, &body);
        if (err) {
          err = EBADMSG;
          goto error;
        }
        goto success;
        break;

      /*
       * Chunked-Body   = *chunk
       *                  last-chunk
       *                  trailer
       *                  CRLF
       *
       * chunk          = chunk-size [ chunk-extension ] CRLF
       *                  chunk-data CRLF
       * last-chunk     = 1*("0") [ chunk-extension ] CRLF
       *
       * chunk-data     = chunk-size(OCTET)
       * trailer        = *(entity-header CRLF)
       *
       */

      case AHP_STATE_PARSE_CHUNKED_SIZE:
        err = ahp_parse_chunked_size(parser, &message);
        if (err) goto error;
        parser->state = AHP_STATE_PARSE_CHUNKED_EXT;

      case AHP_STATE_PARSE_CHUNKED_EXT:
        err = ahp_parse_chunked_ext(parser, &message);
        if (err) goto error;
        parser->state = AHP_STATE_PARSE_CHUNKED_DATA;

      case AHP_STATE_PARSE_CHUNKED_DATA:

      case AHP_STATE_PARSE_CHUNKED_TRAILER:

      default:
        // unexpected state, parser 不可用
        return EBUSY;
    }
  } while (1);

error:
  goto finally;

success:
  parser->state = AHP_STATE_PARSE_IDLE;
  err = 0;
  goto finally;

finally:
  ahp_msgbuf_forward(msg, strbuf_consume_length(&message));
  return err;
}

int ahp_parse_body_length(ahp_parser_t *parser, ahp_msgbuf_t *msg, long length) {
  if (parser->state != AHP_STATE_PARSE_IDLE) {
    // unexpected state, parser 不可用
    return EBUSY;
  }

  // 初始化
  parser->content_length = length;
  parser->state = AHP_STATE_PARSE_LENGTH_BODY;

  return ahp_parse_body(parser, msg);
}


int ahp_parse_body_chunked(ahp_parser_t *parser, ahp_msgbuf_t *msg) {
  if (parser->state != AHP_STATE_PARSE_IDLE) {
    // unexpected state, parser 不可用
    return EBUSY;
  }

  // 初始化
  parser->state = AHP_STATE_PARSE_CHUNKED_SIZE;

  return ahp_parse_body(parser, msg);
}
