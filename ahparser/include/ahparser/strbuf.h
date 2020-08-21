/**
 * file:         strbuf.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  string buffer
 */

#ifndef AHPARSER_STRBUF_H_
#define AHPARSER_STRBUF_H_

#include <stdio.h>

#include "alphabet.h"
#include "msgbuf.h"
#include "strlen.h"

typedef struct strbuf {
  unsigned char* base;
  unsigned char* pos;
  unsigned char* end;
  long size;
} strbuf_t;

static inline void strbuf_init_with_buf(strbuf_t* buf, unsigned char* base, long len) {
  buf->base = buf->pos = base;
  buf->size = len;
  buf->end = buf->base + buf->size;
}

static inline void strbuf_init_with_msgbuf(strbuf_t* buf, ahp_msgbuf_t* msg) {
  strbuf_init_with_buf(buf, (unsigned char*)ahp_msgbuf_data(msg), ahp_msgbuf_length(msg));
}

static inline void strbuf_init_with_strlen(strbuf_t* buf, ahp_strlen_t* str) {
  strbuf_init_with_buf(buf, (unsigned char*)str->str, str->len);
}

static inline int strbuf_is_empty(strbuf_t* buf) {
  return buf->pos == buf->end;
}

static inline unsigned char* strbuf_pos(strbuf_t* buf) {
  return buf->pos;
}

static inline unsigned char* strbuf_end(strbuf_t* buf) {
  return buf->end;
}

static inline void strbuf_rewind(strbuf_t* buf, unsigned char* pos) {
  if (pos >= buf->base && pos <= buf->end) {
    buf->pos = pos;
  }
}

static inline long strbuf_consume_length(strbuf_t* buf) {
  return buf->pos - buf->base;
}

static inline long strbuf_remain_length(strbuf_t* buf) {
  return buf->end - buf->pos;
}

static inline int strbuf_peek(strbuf_t* buf) {
  if (buf->pos == buf->end) {
    return EOF;
  }
  return *(buf->pos);
}

static inline int strbuf_pop(strbuf_t* buf) {
  if (buf->pos == buf->end) {
    return EOF;
  }
  return *(buf->pos++);
}

static inline void strbuf_forward(strbuf_t* buf) {
  buf->pos++;
}

static inline void strbuf_fast_forward(strbuf_t* buf, long len) {
  buf->pos += len;
}

static inline void strbuf_backward(strbuf_t* buf) {
  buf->pos--;
}

static inline void strbuf_skip(strbuf_t* buf, const ahp_alphabet_t skip) {
  while (buf->pos < buf->end) {
    int ch = *(buf->pos);
    if (!skip[ch]) {
      break;
    }
    buf->pos++;
  }
}

static inline void strbuf_skipc(strbuf_t* buf, const int skip) {
  if (buf->pos != buf->end) {
    if (buf->pos[0] == skip) {
      buf->pos++;
    }
  }
}

static inline int strbuf_consume(strbuf_t* buf, const ahp_alphabet_t accept, ahp_strlen_t* str) {
  unsigned char* start = buf->pos;
  strbuf_skip(buf, accept);
  if (str != NULL) {
    str->str = (char*)start;
    str->len = buf->pos - start;
  }
  return 0;
}

int strbuf_consume_expect(strbuf_t* buf, const ahp_alphabet_t accept, const ahp_alphabet_t stop, ahp_strlen_t* str);
int strbuf_consume_expectc(strbuf_t* buf, const ahp_alphabet_t accept, const int stop, ahp_strlen_t* str);

static inline int strbuf_consume_len(strbuf_t* buf, long len, ahp_strlen_t* str) {
  if (buf->end - buf->pos >= len) {
    if (str != NULL) {
      str->str = (char*)buf->pos;
      str->len = len;
    }
    buf->pos += len;
    return 0;
  }
  return -1;
}

int strbuf_expect(strbuf_t* buf, const char* accept, long len);

static inline int strbuf_expectc(strbuf_t* buf, int accept) {
  if (buf->pos != buf->end) {
    if (buf->pos[0] == accept) {
      buf->pos++;
      return 0;
    }
  }
  return -1;
}

static inline int strbuf_expects(strbuf_t* buf, const ahp_alphabet_t accept) {
  if (buf->pos != buf->end) {
    if (accept[buf->pos[0]]) {
      buf->pos++;
      return 0;
    }
  }
  return -1;
}

long htoi(ahp_strlen_t* hex);

#endif  // AHPARSER_STRBUF_H_
