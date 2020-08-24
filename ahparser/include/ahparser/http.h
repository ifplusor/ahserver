/**
 * file:         http.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  http protocol enumeration value
 */
#ifndef AHPARSER_HTTP_H_
#define AHPARSER_HTTP_H_

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  AHP_METHOD_OPTIONS = 0,
  AHP_METHOD_GET,
  AHP_METHOD_HEAD,
  AHP_METHOD_POST,
  AHP_METHOD_PUT,
  AHP_METHOD_DELETE,
  AHP_METHOD_TRACE,
  AHP_METHOD_CONNECT,
  AHP_METHOD_CUSTOM
} ahp_method_t;

typedef enum { AHP_VERSION_10 = 0, AHP_VERSION_11, AHP_VERSION_20 } ahp_version_t;

#ifdef __cplusplus
}
#endif

#endif  // AHPARSER_HTTP_H_
