/**
 * file:         splitter.c
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  simple http2 frame splitter
 * reference:    rfc7540
 */

#include <errno.h>

#include <ahparser/splitter.h>
#include <ahparser/strbuf.h>

static const uint32_t OFFSET_0 = 1;
static const uint32_t OFFSET_1 = 256;
static const uint32_t OFFSET_2 = 256 * 256;
static const uint32_t OFFSET_3 = 256 * 256 * 256;

static inline uint8_t parse_uint8(char* data) {
  uint8_t* field = (uint8_t*)data;
  // Big-Endian, 8bits
  return field[0] * OFFSET_0;
}

static inline uint16_t parse_uint16(char* data) {
  uint8_t* field = (uint8_t*)data;
  // Big-Endian, 16bits
  return field[0] * OFFSET_1 + field[1] * OFFSET_0;
}

static inline uint32_t parse_uint24(char* data) {
  uint8_t* field = (uint8_t*)data;
  // Big-Endian, 24bits
  return field[0] * OFFSET_2 + field[1] * OFFSET_1 + field[2] * OFFSET_0;
}

static inline uint32_t parse_uint32(char* data) {
  uint8_t* field = (uint8_t*)data;
  // Big-Endian, 32bits
  return field[0] * OFFSET_3 + field[1] * OFFSET_2 + field[2] * OFFSET_1 + field[3] * OFFSET_0;
}

static inline uint32_t parse_uint31(char* data) {
  return 0x7FFFFFFF & parse_uint32(data);
}

int ahp_parse_data_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +---------------+
   *    |Pad Length? (8)|
   *    +---------------+-----------------------------------------------+
   *    |                            Data (*)                         ...
   *    +---------------------------------------------------------------+
   *    |                           Padding (*)                       ...
   *    +---------------------------------------------------------------+
   */

  char* cursor = payload->str;
  uint8_t pad_length = 0;
  if (flags & AHP_FRAME_FLAG_PADDED) {
    pad_length = parse_uint8(cursor);
    cursor += 1;
    if (pad_length > payload->len - 1) {
      return -1;
    }
  }
  ahp_strlen_t data = {.str = cursor, .len = payload->len - (cursor - payload->str) - pad_length};
  return 0;
}

int ahp_parse_headers_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +---------------+
   *    |Pad Length? (8)|
   *    +-+-------------+-----------------------------------------------+
   *    |E|                 Stream Dependency? (31)                     |
   *    +-+-------------+-----------------------------------------------+
   *    |  Weight? (8)  |
   *    +-+-------------+-----------------------------------------------+
   *    |                   Header Block Fragment (*)                 ...
   *    +---------------------------------------------------------------+
   *    |                           Padding (*)                       ...
   *    +---------------------------------------------------------------+
   */

  char* cursor = payload->str;
  uint8_t pad_length = 0;
  uint32_t dependency = 0;
  uint8_t weight = 0;
  if (flags & AHP_FRAME_FLAG_PADDED) {
    pad_length = parse_uint8(cursor);
    cursor += 1;
    if (pad_length > payload->len - 1) {
      return -1;
    }
  }
  if (flags & AHP_FRAME_FLAG_PRIORITY) {
    dependency = parse_uint31(cursor);
    cursor += 4;
    weight = parse_uint8(cursor);
    cursor += 1;
  }
  ahp_strlen_t header_block_fragment = {.str = cursor, .len = payload->len - (cursor - payload->str) - pad_length};
  return 0;
}

int ahp_parse_priority_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +-+-------------------------------------------------------------+
   *    |E|                  Stream Dependency (31)                     |
   *    +-+-------------+-----------------------------------------------+
   *    |   Weight (8)  |
   *    +-+-------------+
   */
}

int ahp_parse_rst_stream_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +---------------------------------------------------------------+
   *    |                        Error Code (32)                        |
   *    +---------------------------------------------------------------+
   */
}

int ahp_parse_settings_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +-------------------------------+
   *    |       Identifier (16)         |
   *    +-------------------------------+-------------------------------+
   *    |                        Value (32)                             |
   *    +---------------------------------------------------------------+
   */

  char* cursor = payload->str;
  char* end = payload->str + payload->len;
  while (cursor < end) {
    uint16_t identifier = parse_uint16(cursor);
    cursor += 2;
    uint32_t value = parse_uint32(cursor);
    cursor += 4;
    splitter->on_settings_frame(splitter, frame, identifier, value);
  }
  return 0;
}

int ahp_parse_push_promise_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +---------------+
   *    |Pad Length? (8)|
   *    +-+-------------+-----------------------------------------------+
   *    |R|                  Promised Stream ID (31)                    |
   *    +-+-----------------------------+-------------------------------+
   *    |                   Header Block Fragment (*)                 ...
   *    +---------------------------------------------------------------+
   *    |                           Padding (*)                       ...
   *    +---------------------------------------------------------------+
   */
}

int ahp_parse_ping_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +---------------------------------------------------------------+
   *    |                                                               |
   *    |                      Opaque Data (64)                         |
   *    |                                                               |
   *    +---------------------------------------------------------------+
   */
}

int ahp_parse_goway_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +-+-------------------------------------------------------------+
   *    |R|                  Last-Stream-ID (31)                        |
   *    +-+-------------------------------------------------------------+
   *    |                      Error Code (32)                          |
   *    +---------------------------------------------------------------+
   *    |                  Additional Debug Data (*)                    |
   *    +---------------------------------------------------------------+
   */
}

int ahp_parse_window_update_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +-+-------------------------------------------------------------+
   *    |R|              Window Size Increment (31)                     |
   *    +-+-------------------------------------------------------------+
   */
}

int ahp_parse_continuation_frame(ahp_splitter_t* splitter, uint8_t flags, ahp_strlen_t* payload, void* frame) {
  /*
   *    +---------------------------------------------------------------+
   *    |                   Header Block Fragment (*)                 ...
   *    +---------------------------------------------------------------+
   */
}

int ahp_check_frame(uint8_t type, uint8_t flags, uint32_t identifier, ahp_strlen_t* payload) {
  switch (type) {
    case AHP_FRAME_TYPE_SETTINGS:
      if (flags & AHP_FRAME_FLAG_ACK && payload->len != 0) {
        return -AHP_ERROR_FRAME_SIZE_ERROR;
      }
      break;
    default:
      break;
  }
  return 0;
}

typedef int (*ahp_parse_frame_func)(ahp_splitter_t*, uint8_t, ahp_strlen_t*, void*);
const ahp_parse_frame_func parser_table[] = {
    ahp_parse_data_frame,          ahp_parse_headers_frame,      ahp_parse_priority_frame, ahp_parse_rst_stream_frame,
    ahp_parse_settings_frame,      ahp_parse_push_promise_frame, ahp_parse_ping_frame,     ahp_parse_goway_frame,
    ahp_parse_window_update_frame, ahp_parse_continuation_frame};

int ahp_split_frame(ahp_splitter_t* splitter, ahp_msgbuf_t* msg) {
  /*
   *    +-----------------------------------------------+
   *    |                 Length (24)                   |
   *    +---------------+---------------+---------------+
   *    |   Type (8)    |   Flags (8)   |
   *    +-+-------------+---------------+-------------------------------+
   *    |R|                 Stream Identifier (31)                      |
   *    +=+=============================================================+
   *    |                   Frame Payload (0...)                      ...
   *    +---------------------------------------------------------------+
   */

  int err;

  do {
    long len = ahp_msgbuf_length(msg);
    // 帧以9字节的报头开始并且跟着可变长度的负载
    if (len < 9) {
      return EAGAIN;
    }

    char* packet = ahp_msgbuf_data(msg);

    uint32_t length = parse_uint24(packet);
    if (len < length + 9) {
      return EAGAIN;
    }

    uint8_t type = parse_uint8(packet + 3);
    if (type > AHP_ERROR_HTTP_1_1_REQUIRED) {
      return EBADMSG;
    }

    uint8_t flags = parse_uint8(packet + 4);
    uint32_t identifier = parse_uint31(packet + 5);
    ahp_strlen_t payload = {.str = packet + 9, .len = length};

    // check
    err = ahp_check_frame(type, flags, identifier, &payload);
    if (err != 0) {
      return err;
    }

    // callback for create frame
    void* frame = splitter->alloc_frame(splitter, type, flags, identifier, &payload);
    if (frame == NULL) {
      return EINVAL;
    }

    err = parser_table[type](splitter, flags, &payload, frame);
    if (err == 0) {
      err = splitter->on_frame_received(splitter, frame);
    }

    splitter->free_frame(splitter, frame);

    if (err != 0) {
      return err;
    }

    ahp_msgbuf_forward(msg, length + 9);
  } while (1);
}
