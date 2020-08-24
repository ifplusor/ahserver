/**
 * file:         hpack.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  hpack implementation
 */
#ifndef AHPARSER_HPACK_H_
#define AHPARSER_HPACK_H_

#include "msgbuf.h"
#include "strlen.h"

struct ahp_hpack;
typedef struct ahp_hpack ahp_hpack_t;

typedef int (*ahp_header_field_callback)(ahp_hpack_t* hpack, ahp_strlen_t* name, ahp_strlen_t* value);

struct ahp_hpack {
  ahp_msgbuf_t name_buffer;
  ahp_msgbuf_t value_buffer;

  void* data;

  // callbacks
  ahp_header_field_callback on_header_field;
};

int ahp_hpack_decode(ahp_hpack_t* hpack, ahp_msgbuf_t* block);

#endif  // AHPARSER_HPACK_H_
