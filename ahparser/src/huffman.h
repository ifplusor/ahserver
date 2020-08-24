/**
 * file:         huffman.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:
 */
#ifndef AHPARSER_HUFFMAN_H_
#define AHPARSER_HUFFMAN_H_

#ifdef __cplusplus
extern "C" {
#endif

typedef struct huffman_code {
  int code;
  int len;
} huffman_code_t;

extern huffman_code_t* ahp_huffman_decode_table[15];

#ifdef __cplusplus
}
#endif

#endif  // AHPARSER_HUFFMAN_H_
