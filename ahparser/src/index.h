/**
 * file:         index.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:
 */
#ifndef AHPARSER_INDEX_H_
#define AHPARSER_INDEX_H_

#include "ahparser/strlen.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ahp_header_index {
  ahp_strlen_t* name;
  ahp_strlen_t* value;
} ahp_header_index_t;

extern const size_t STATIC_INDEX_TABLE_SIZE;
extern ahp_header_index_t ahp_static_index_table[];

#ifdef __cplusplus
}
#endif

#endif  // AHPARSER_INDEX_H_
