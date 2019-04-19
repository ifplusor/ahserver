/**
 * file:         strbuf.c
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  string buffer
 */

#include <string.h>

#include <ahparser/strbuf.h>

/**
 * 取得由字母表指定的字符序列，并以指定字符表中的字符结束
 */
int strbuf_consume_expect(strbuf_t* buf, const ahp_alphabet_t accept, const ahp_alphabet_t stop, ahp_strlen_t* str) {
  unsigned char* start = buf->start;

  strbuf_skip(buf, accept);
  int ch = strbuf_peek(buf);
  if (ch != EOF && stop[ch]) {
    if (str != NULL) {
      str->str = (char*)start;
      str->len = buf->start - start;
    }
    strbuf_forward(buf);
    return 0;
  }

  buf->start = start;
  return -1;
}

/**
 * 取得由字母表指定的字符序列，并以指定字符结束
 *
 * NOTE: stop 应为 unsigned char
 */
int strbuf_consume_expectc(strbuf_t* buf, const ahp_alphabet_t accept, const int stop, ahp_strlen_t* str) {
  unsigned char* start = buf->start;

  strbuf_skip(buf, accept);
  int ch = strbuf_peek(buf);
  if (ch == stop) {  // stop 接受 EOF
    if (str != NULL) {
      str->str = (char*)start;
      str->len = buf->start - start;
    }
    if (ch != EOF) {
      strbuf_forward(buf);
    }
    return 0;
  }

  buf->start = start;
  return -1;
}

int strbuf_expect(strbuf_t* buf, const char* accept, long len) {
  long blen = buf->end - buf->start;
  if (blen >= len && strncmp((char*)buf->start, accept, len) == 0) {
    buf->start += len;
    return 0;
  }
  return -1;
}

// clang-format off
int hex2int[256] = {
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  0,  0,  0,  0,  0,  0,  // 0~9
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0, 10, 11, 12, 13, 14, 15,  0,  0,  0,  0,  0,  0,  0,  0,  0,  // A~F
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0, 10, 11, 12, 13, 14, 15,  0,  0,  0,  0,  0,  0,  0,  0,  0,  // a~f
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
};
// clang-format on

long htoi(ahp_strlen_t* hex) {
  long num = 0;
  unsigned char* cur = (unsigned char*)hex->str;
  unsigned char* end = (unsigned char*)hex->str + hex->len;
  while (cur != end) {
    num = num * 16 + hex2int[*cur];
  }
  return num;
}
