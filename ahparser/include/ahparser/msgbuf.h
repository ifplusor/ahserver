/**
 * file:         msgbuf.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  message buffer, for store part of http message to parse
 */
#ifndef AHPARSER_MSGBUF_H_
#define AHPARSER_MSGBUF_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ahp_msgbuf {
  char* base;
  size_t size, start, end;
} ahp_msgbuf_t;

int ahp_msgbuf_init(ahp_msgbuf_t* buf, long size);
void ahp_msgbuf_free(ahp_msgbuf_t* buf);
int ahp_msgbuf_append(ahp_msgbuf_t* buf, const char* data, size_t len);

static inline int ahp_msgbuf_appendc(ahp_msgbuf_t* buf, char ch) {
  return ahp_msgbuf_append(buf, &ch, 1);
}

int ahp_msgbuf_copy(ahp_msgbuf_t* src, ahp_msgbuf_t* dst);

static inline char* ahp_msgbuf_data(ahp_msgbuf_t* buf) {
  return buf->base + buf->start;
}

static inline long ahp_msgbuf_length(ahp_msgbuf_t* buf) {
  return buf->end - buf->start;
}

static inline void ahp_msgbuf_reset(ahp_msgbuf_t* buf) {
  buf->start = buf->end = 0;
}

static inline void ahp_msgbuf_forward(ahp_msgbuf_t* buf, long size) {
  buf->start += size;
}

#ifdef __cplusplus
}
#endif

#endif  // AHPARSER_MSGBUF_H_
