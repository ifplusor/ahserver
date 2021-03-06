/**
 * file:         msgbuf.c
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  message buffer
 */
#include "ahparser/msgbuf.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

int ahp_msgbuf_init(ahp_msgbuf_t* buf, long size) {
  if (buf == NULL) {
    return EFAULT;
  }

  if (size < 0) {
    size = 32;  // 32 bytes
  }

  // 4 字节对齐
  if (size & 0x03) {
    size = (size | 0x03) + 1;
  }

  char* buffer = (char*)malloc(size);
  if (buffer == NULL) {
    buf->base = NULL;
    return ENOMEM;
  }

  buf->base = buffer;
  buf->start = buf->end = 0;
  buf->size = size;

  return 0;
}

void ahp_msgbuf_free(ahp_msgbuf_t* buf) {
  if (buf == NULL) {
    return;
  }

  free(buf->base);
  buf->base = NULL;
  buf->size = buf->start = buf->end = 0;
}

int ahp_msgbuf_append(ahp_msgbuf_t* buf, const char* data, size_t len) {
  size_t remains_len = buf->end - buf->start;  // 缓冲区中剩余数据长度

  // 调整缓冲区

  if (remains_len == 0) {
    // 空，重置 (尽量避免前一次新增的小块数据引起 memmove 调用)
    buf->start = buf->end = 0;
  }

  if (len > buf->size - buf->end) {
    if (remains_len != 0) {
      // 溢出，移动数据
      memmove(buf->base, buf->base + buf->start, remains_len);
      buf->start = 0;
      buf->end = remains_len;
    }

    if (len > buf->size - remains_len) {
      // 空间不足，扩充
      size_t new_size = buf->size * 2;
      if (new_size < remains_len + len) {
        new_size = remains_len + len;
      }

      // 4 字节对齐
      if (new_size & 0x03) {
        new_size = (new_size | 0x03) + 1;
      }

      char* new_buffer = (char*)realloc(buf->base, new_size);
      if (new_buffer == NULL) {
        return ENOMEM;
      }

      buf->base = new_buffer;
      buf->size = new_size;
    }
  }

  // 拷贝数据到缓冲区
  if (len < 32) {
    char* write = buf->base + buf->end;
    for (int i = 0; i < len; i++) {
      write[i] = data[i];
    }
  } else {
    memcpy(buf->base + buf->end, data, len);
  }
  buf->end += len;

  return 0;
}

int ahp_msgbuf_copy(ahp_msgbuf_t* src, ahp_msgbuf_t* dst) {
  return ahp_msgbuf_append(dst, ahp_msgbuf_data(src), ahp_msgbuf_length(src));
}
