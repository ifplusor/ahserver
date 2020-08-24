/**
 * file:         strlen.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  string with length
 */
#ifndef AHPARSER_STRLEN_H_
#define AHPARSER_STRLEN_H_

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ahp_strlen {
  size_t len;
  char* str;
} ahp_strlen_t;

#ifdef __cplusplus
}
#endif

#endif  // AHPARSER_STRLEN_H_
