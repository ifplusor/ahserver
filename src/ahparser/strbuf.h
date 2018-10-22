#ifndef AHPARSER_STRBUF_H
#define AHPARSER_STRBUF_H

#include <stdio.h>
#include "strlen.h"
#include "alphabet.h"


typedef struct strbuf {
  unsigned char *base;
  unsigned char *start;
  unsigned char *end;
  long size;
} strbuf_t;


inline void strbuf_init_with_buf(strbuf_t *buf, char *base, long len) {
  buf->base = buf->start = (unsigned char*) base;
  buf->size = len;
  buf->end = buf->base + buf->size;
}

inline void strbuf_init_with_strlen(strbuf_t *buf, ahp_strlen_t *str) {
  strbuf_init_with_buf(buf, str->str, str->len);
}

inline int strbuf_is_empty(strbuf_t *buf) {
  return buf->start == buf->end;
}

inline long strbuf_consume_length(strbuf_t *buf) {
  return buf->start - buf->base;
}

inline long strbuf_remain_length(strbuf_t *buf) {
  return buf->end - buf->start;
}

inline int strbuf_peek(strbuf_t *buf) {
  if (buf->start == buf->end) {
    return EOF;
  }
  return *(buf->start);
}

inline int strbuf_pop(strbuf_t *buf) {
  if (buf->start == buf->end) {
    return EOF;
  }
  return *(buf->start++);
}

inline void strbuf_forward(strbuf_t *buf) {
//  if (buf->start != buf->end)
    buf->start++;
}

inline void strbuf_fast_forward(strbuf_t *buf, long len) {
  buf->start += len;
}

inline void strbuf_backward(strbuf_t *buf) {
//  if (buf->start != buf->base)
    buf->start--;
}

inline void strbuf_skip(strbuf_t *buf, const ahp_alphabet_t skip) {
  while (buf->start != buf->end) {
    int ch = *(buf->start);
    if (!skip[ch]) {
      break;
    }
    buf->start++;
  }
}

inline void strbuf_skipc(strbuf_t *buf, const int skip) {
  if (buf->start != buf->end) {
    if (buf->start[0] == skip) {
      buf->start++;
    }
  }
}

inline int strbuf_consume(strbuf_t *buf, const ahp_alphabet_t accept, ahp_strlen_t *str) {
  unsigned char *start = buf->start;
  strbuf_skip(buf, accept);
  if (str != NULL) {
    str->str = (char*) start;
    str->len = buf->start - start;
  }
  return 0;
}

int strbuf_consume_expect(strbuf_t *buf, const ahp_alphabet_t accept, const ahp_alphabet_t stop, ahp_strlen_t *str);
int strbuf_consume_expectc(strbuf_t *buf, const ahp_alphabet_t accept, const int stop, ahp_strlen_t *str);

inline int strbuf_consume_len(strbuf_t *buf, long len, ahp_strlen_t *str) {
  if (buf->end - buf->start >= len) {
    if (str != NULL) {
      str->str = (char*) buf->start;
      str->len = len;
    }
    buf->start += len;
    return 0;
  }
  return -1;
}

int strbuf_expect(strbuf_t *buf, const char *accept, long len);

inline int strbuf_expectc(strbuf_t *buf, int accept) {
  if (buf->start != buf->end) {
    if (buf->start[0] == accept) {
      buf->start++;
      return 0;
    }
  } else if (accept == EOF) {
    return 0;
  }
  return -1;
}

long htoi(ahp_strlen_t *hex);

#endif
