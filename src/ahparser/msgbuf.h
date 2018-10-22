#ifndef AHPARSER_MSGBUF_H
#define AHPARSER_MSGBUF_H

#include <stddef.h>


typedef struct ahp_msgbuf {
  char *base;
  size_t size, start, end;
} ahp_msgbuf_t;


int ahp_msgbuf_init(ahp_msgbuf_t *buf, long size);
void ahp_msgbuf_free(ahp_msgbuf_t *buf);
int ahp_msgbuf_append(ahp_msgbuf_t *buf, const char *data, unsigned long len);


inline char *ahp_msgbuf_data(ahp_msgbuf_t *buf) {
  return buf->base + buf->start;
}

inline long ahp_msgbuf_length(ahp_msgbuf_t *buf) {
  return buf->end - buf->start;
}

inline void ahp_msgbuf_reset(ahp_msgbuf_t *buf) {
  buf->start = buf->end = 0;
}

inline void ahp_msgbuf_forward(ahp_msgbuf_t *buf, long size) {
  buf->start += size;
}

#endif
