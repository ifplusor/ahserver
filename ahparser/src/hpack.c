/**
 * file:         hpack.c
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  hpack implementation
 * reference:
 *
 *     RFC5234: https://tools.ietf.org/html/rfc7541
 *
 */
#include "ahparser/hpack.h"

#include <errno.h>
#include <stdint.h>

#include "huffman.h"
#include "index.h"
#include "strbuf.h"

int MAX_OCTET_INTEGER[5] = {0xFF, 0x7F, 0x3F, 0x1F, 0x0F};

int decode_integer(strbuf_t* block, size_t prefix_size) {
  int octet = strbuf_pop(block);
  if (octet == EOF) {
    return -1;
  }
  int integer = octet & MAX_OCTET_INTEGER[prefix_size];
  if (integer < MAX_OCTET_INTEGER[prefix_size]) {
    return integer;
  }
  int base = 1;
  for (;;) {
    octet = strbuf_pop(block);
    if (octet == EOF) {
      return -1;
    }
    integer += (octet & 0x7F) * base;
    if (octet & 0x80 != 0x80) {
      break;
    }
    base *= 128;
  }
  return integer;
}

int ahp_decode_huffman(strbuf_t* block, int length, ahp_msgbuf_t* buffer, ahp_strlen_t* string) {
  ahp_msgbuf_reset(buffer);

  huffman_code_t* decode_table = ahp_huffman_decode_table[0];
  uint8_t check = 0, cache = 0;
  int check_bits = 0, cache_bits = 0;
  for (;;) {
    // 将cache补进check
    if (cache_bits > 0) {
      check |= cache >> check_bits;
      if (check_bits + cache_bits > 8) {
        cache <<= (8 - check_bits);
        cache_bits -= 8 - check_bits;
        check_bits = 8;
      } else {
        check_bits += cache_bits;
        cache_bits = 0;
      }
    }

    // 从strbuf补进check
    if (check_bits < 8) {
      if (length <= 0) {
        if (decode_table[check].len > check_bits) {
          if (decode_table == ahp_huffman_decode_table[0]) {
            break;
          } else {
            return EBADMSG;
          }
        }
      } else {
        // read more data
        int octet = strbuf_pop(block);
        if (octet == EOF) {
          return EAGAIN;
        }
        length--;

        check |= octet >> check_bits;
        cache = octet << (8 - check_bits);
        cache_bits = check_bits;
        check_bits = 8;
      }
    }

    int ch = decode_table[check].code;
    if (ch >= 256) {
      return EBADMSG;
    } else if (ch >= 0) {
      ahp_msgbuf_appendc(buffer, (char)ch);
      check_bits -= decode_table[check].len;
      check <<= decode_table[check].len;
      decode_table = ahp_huffman_decode_table[0];
    } else {
      decode_table = ahp_huffman_decode_table[-ch];
    }
  }

  string->str = ahp_msgbuf_data(buffer);
  string->len = ahp_msgbuf_length(buffer);

  return 0;
}

int ahp_decode_string(strbuf_t* block, ahp_msgbuf_t* buffer, ahp_strlen_t* string) {
  int octet = strbuf_peek(block);
  int length = decode_integer(block, 1);
  if (length < 0) {
    return EAGAIN;
  }
  if ((octet & 0x80) == 0x80) {
    // huffman encoded
    return ahp_decode_huffman(block, length, buffer, string);
  } else {
    if (strbuf_consume_len(block, length, string) != 0) {
      return EAGAIN;
    }
  }
  return 0;
}

int ahp_decode_indexed_header(ahp_hpack_t* hpack, strbuf_t* header_block, ahp_strlen_t* name, ahp_strlen_t* value) {
  int index = decode_integer(header_block, 1);
  if (index < 0) {
    return EAGAIN;
  }
  if (index <= 0) {
    return EBADMSG;
  }
  if (index <= STATIC_INDEX_TABLE_SIZE) {
    // static table
    ahp_header_index_t* index_item = &ahp_static_index_table[index];
    if (index_item->value == NULL) {
      return EBADMSG;
    }
    *name = *index_item->name;
    *value = *index_item->value;
  } else {
    // dynamic table
    return EBADMSG;
  }
  return 0;
}

int ahp_decode_literal_header(ahp_hpack_t* hpack,
                              strbuf_t* header_block,
                              size_t prefix_size,
                              ahp_strlen_t* name,
                              ahp_strlen_t* value) {
  int err = 0;
  int index = decode_integer(header_block, prefix_size);
  if (index > 0) {
    if (index <= STATIC_INDEX_TABLE_SIZE) {
      // static table
      ahp_header_index_t* index_item = &ahp_static_index_table[index];
      *name = *index_item->name;
    } else {
      // dynamic table
      err = EBADMSG;
    }
  } else {
    err = ahp_decode_string(header_block, &hpack->name_buffer, name);
  }
  if (err == 0) {
    err = ahp_decode_string(header_block, &hpack->value_buffer, value);
  }
  return err;
}

int ahp_hpack_decode(ahp_hpack_t* hpack, ahp_msgbuf_t* block) {
  int err = 0;

  strbuf_t header_block;
  strbuf_init_with_msgbuf(&header_block, block);

  unsigned char* pos = strbuf_pos(&header_block);
  for (;;) {
    int octet = strbuf_peek(&header_block);
    if (octet == EOF) {
      // err = EAGAIN;
      break;
    }

    ahp_strlen_t name, value;
    if (octet & 0x80) {
      // indexed header field
      err = ahp_decode_indexed_header(hpack, &header_block, &name, &value);
    } else if (octet & 0x40) {
      // literal header field with incremental indexing
      err = ahp_decode_literal_header(hpack, &header_block, 2, &name, &value);
      if (err == 0) {
        // add new index
      }
    } else if (octet & 0x20) {
      // dynamic table size update
      return EBADMSG;
    } else if (octet & 0x10) {
      // literal header field never-indexed
      err = ahp_decode_literal_header(hpack, &header_block, 4, &name, &value);
    } else {
      // literal header field without indexing
      err = ahp_decode_literal_header(hpack, &header_block, 4, &name, &value);
    }

    if (err == 0) {
      err = hpack->on_header_field(hpack, &name, &value);
    }

    if (err != 0) {
      break;
    }

    unsigned char* next_pos = strbuf_pos(&header_block);
    ahp_msgbuf_forward(block, next_pos - pos);
    pos = next_pos;
  }

  return err;
}
