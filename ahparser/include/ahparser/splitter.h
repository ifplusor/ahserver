/**
 * file: splitter.h
 * author: James Yin<ywhjames@hotmail.com>
 * description: http 2.0 frame splitter
 */

#ifndef AHPARSER_SPLITTER_H_
#define AHPARSER_SPLITTER_H_

#include <stdint.h>

#include "msgbuf.h"
#include "strlen.h"

typedef enum ahp_frame_type {
  AHP_FRAME_TYPE_DATA = 0x00,
  AHP_FRAME_TYPE_HEADERS = 0x01,
  AHP_FRAME_TYPE_PRIORITY = 0x02,
  AHP_FRAME_TYPE_RST_STREAM = 0x03,
  AHP_FRAME_TYPE_SETTINGS = 0x04,
  AHP_FRAME_TYPE_PUSH_PROMISE = 0x05,
  AHP_FRAME_TYPE_PING = 0x06,
  AHP_FRAME_TYPE_GOWAY = 0x07,
  AHP_FRAME_TYPE_WINDOW_UPDATE = 0x08,
  AHP_FRAME_TYPE_CONTINUAION = 0x09
} ahp_frame_type_t;

typedef enum ahp_frame_flag {
  AHP_FRAME_FLAG_ACK = 0x01,
  AHP_FRAME_FLAG_END_STREAM = 0x01,
  AHP_FRAME_FLAG_END_HEADERS = 0x04,
  AHP_FRAME_FLAG_PADDED = 0x08,
  AHP_FRAME_FLAG_PRIORITY = 0x20
} ahp_frame_flag_t;

typedef enum ahp_error {
  AHP_ERROR_NO_ERROR = 0x00,
  AHP_ERROR_PROTOCOL_ERROR = 0x01,
  AHP_ERROR_INTERNAL_ERROR = 0x02,
  AHP_ERROR_FLOW_CONTROL_ERROR = 0x03,
  AHP_ERROR_SETTINGS_TIMEOUT = 0x04,
  AHP_ERROR_STREAM_CLOSED = 0x05,
  AHP_ERROR_FRAME_SIZE_ERROR = 0x06,
  AHP_ERROR_REFUSED_STREAM = 0x07,
  AHP_ERROR_CANCEL = 0x08,
  AHP_ERROR_COMPRESSION_ERROR = 0x09,
  AHP_ERROR_CONNECT_ERROR = 0x0a,
  AHP_ERROR_ENHANCE_YOUR_CALM = 0x0b,
  AHP_ERROR_INADEQUATE_SECURITY = 0x0c,
  AHP_ERROR_HTTP_1_1_REQUIRED = 0x0d
} ahp_error_t;

struct ahp_splitter;
typedef struct ahp_splitter ahp_splitter_t;

typedef void* (*ahp_alloc_frame_delegate)(ahp_splitter_t* splitter,
                                          uint8_t type,
                                          uint8_t flag,
                                          uint32_t identifier,
                                          ahp_strlen_t* payload);
typedef void (*ahp_free_frame_delegate)(ahp_splitter_t* splitter, void* frame);

typedef int (*aph_frame_received_callback)(ahp_splitter_t* splitter, void* frame);
typedef int (*ahp_data_frame_callback)(ahp_splitter_t* splitter, void* frame, ahp_strlen_t* data);
typedef int (*ahp_headers_frame_callback)(ahp_splitter_t* splitter, void* frame, ahp_strlen_t* header_block_fragment);
typedef int (*aph_settings_frame_callback)(ahp_splitter_t* splitter, void* frame, uint16_t identifier, uint32_t value);

struct ahp_splitter {
  void* data;

  ahp_alloc_frame_delegate alloc_frame;
  ahp_free_frame_delegate free_frame;

  aph_frame_received_callback on_frame_received;
  ahp_data_frame_callback on_data_frame;
  ahp_headers_frame_callback on_headers_frame;
  aph_settings_frame_callback on_settings_frame;
};

int ahp_split_frame(ahp_splitter_t* splitter, ahp_msgbuf_t* msg);

#endif  // AHPARSER_SPLITTER_H_
