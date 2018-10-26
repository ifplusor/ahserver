#include <stdlib.h>
#include <string.h>
#include "msgbuf.h"


int ahp_msgbuf_init(ahp_msgbuf_t *buf, long size) {
  if (size < 0) {
    size = 4 * 1024; // 4k
  }

  // 4 字节对齐
  if (size & 0x03) {
      size = (size | 0x03) + 1;
  }

  char *buffer = (char*) malloc(size);
  if (buffer == NULL) {
    return -1;
  }

  buf->base = buffer;
  buf->start = buf->end = 0;
  buf->size = size;

  return 0;
}


void ahp_msgbuf_free(ahp_msgbuf_t *buf) {
  free(buf->base);
  buf->base = NULL;
  buf->size = buf->start = buf->end = 0;
}


int ahp_msgbuf_append(ahp_msgbuf_t *buf, const char *data, unsigned long len) {
  size_t rlen = buf->end - buf->start;  // 缓冲区中剩余数据长度

  // 调整缓冲区

  if(rlen == 0) {
    // 空，重置 (尽量避免前一次新增的小块数据引起 memmove 调用)
    buf->start = buf->end = 0;
  }

  if (len > buf->size - buf->end) {
    if (rlen != 0) {
      // 溢出，移动数据
      memmove(buf->base, buf->base + buf->start, rlen);
      buf->start = 0;
      buf->end = rlen;
    }

    if (len > buf->size - rlen) {
      // 空间不足，扩充
      size_t new_size = buf->size * 2;
      if (new_size < rlen + len) {
        new_size = rlen + len;
      }

      // 4 字节对齐
      if (new_size & 0x03) {
          new_size = (new_size | 0x03) + 1;
      }

      char *new_buffer = (char*) realloc(buf->base, new_size);
      if (new_buffer == NULL) {
        return -1;
      }

      buf->base = new_buffer;
      buf->size = new_size;
    }
  }

  // 拷贝数据到缓冲区
  memcpy(buf->base + buf->end, data, len);
  buf->end += len;

  return 0;
}

