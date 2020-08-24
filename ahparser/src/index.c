/**
 * file:         index.c
 * author:       James Yin<ywhjames@hotmail.com>
 * description:
 * reference:
 *
 *     RFC5234: https://tools.ietf.org/html/rfc7541
 *
 */
#include "index.h"

ahp_strlen_t HPACK_FIELD_AUTHORITY = {.str = ":authority", .len = 10};
ahp_strlen_t HPACK_FIELD_METHOD = {.str = ":method", .len = 7};
ahp_strlen_t HPACK_FIELD_PATH = {.str = ":path", .len = 5};
ahp_strlen_t HPACK_FIELD_SCHEME = {.str = ":scheme", .len = 7};
ahp_strlen_t HPACK_FIELD_STATUS = {.str = ":status", .len = 7};
ahp_strlen_t HPACK_FIELD_ACCEPT_CHARSET = {.str = "accept-charset", .len = 14};
ahp_strlen_t HPACK_FIELD_ACCEPT_ENCODING = {.str = "accept-encoding", .len = 15};
ahp_strlen_t HPACK_FIELD_ACCEPT_LANGUAGE = {.str = "accept-language", .len = 15};
ahp_strlen_t HPACK_FIELD_ACCEPT_RANGE = {.str = "accept-range", .len = 12};
ahp_strlen_t HPACK_FIELD_ACCEPT = {.str = "accept", .len = 6};
ahp_strlen_t HPACK_FIELD_ACCESS_CONTROL_ALLOW_ORIGIN = {.str = "access-control-allow-origin", .len = 27};
ahp_strlen_t HPACK_FIELD_AGE = {.str = "age", .len = 3};
ahp_strlen_t HPACK_FIELD_ALLOW = {.str = "allow", .len = 5};
ahp_strlen_t HPACK_FIELD_AUTHORIZATION = {.str = "authorization", .len = 13};
ahp_strlen_t HPACK_FIELD_CACHE_CONTROL = {.str = "cache-control", .len = 13};
ahp_strlen_t HPACK_FIELD_CONTENT_DISPOSITION = {.str = "content-disposition", .len = 19};
ahp_strlen_t HPACK_FIELD_CONTENT_ENCODING = {.str = "content-encoding", .len = 16};
ahp_strlen_t HPACK_FIELD_CONTENT_LANGUAGE = {.str = "content-language", .len = 16};
ahp_strlen_t HPACK_FIELD_CONTENT_LENGTH = {.str = "content-length", .len = 14};
ahp_strlen_t HPACK_FIELD_CONTENT_LOCATION = {.str = "content-location", .len = 16};
ahp_strlen_t HPACK_FIELD_CONTENT_RANGE = {.str = "content-range", .len = 13};
ahp_strlen_t HPACK_FIELD_CONTENT_TYPE = {.str = "content-type", .len = 12};
ahp_strlen_t HPACK_FIELD_COOKIE = {.str = "cookie", .len = 6};
ahp_strlen_t HPACK_FIELD_DATE = {.str = "date", .len = 4};
ahp_strlen_t HPACK_FIELD_ETAG = {.str = "etag", .len = 4};
ahp_strlen_t HPACK_FIELD_EXPECT = {.str = "expect", .len = 6};
ahp_strlen_t HPACK_FIELD_EXPIRES = {.str = "expires", .len = 7};
ahp_strlen_t HPACK_FIELD_FROM = {.str = "from", .len = 4};
ahp_strlen_t HPACK_FIELD_HOST = {.str = "host", .len = 4};
ahp_strlen_t HPACK_FIELD_IF_MATCH = {.str = "if-match", .len = 8};
ahp_strlen_t HPACK_FIELD_IF_MODIFIED_SINCE = {.str = "if-modified-since", .len = 17};
ahp_strlen_t HPACK_FIELD_IF_NONE_MATCH = {.str = "if-none-match", .len = 13};
ahp_strlen_t HPACK_FIELD_IF_RANGE = {.str = "if-range", .len = 8};
ahp_strlen_t HPACK_FIELD_IF_UNMODIFIED_SINCE = {.str = "if-unmodified-since", .len = 19};
ahp_strlen_t HPACK_FIELD_LAST_MODIFIED = {.str = "last-modified", .len = 13};
ahp_strlen_t HPACK_FIELD_LINK = {.str = "link", .len = 4};
ahp_strlen_t HPACK_FIELD_LOCATION = {.str = "location", .len = 8};
ahp_strlen_t HPACK_FIELD_MAX_FORWARDS = {.str = "max-forwards", .len = 12};
ahp_strlen_t HPACK_FIELD_PROXY_AUTHENTICATE = {.str = "proxy-authenticate", .len = 18};
ahp_strlen_t HPACK_FIELD_PROXY_AUTHORIZATION = {.str = "proxy-authorization", .len = 19};
ahp_strlen_t HPACK_FIELD_RANGE = {.str = "range", .len = 5};
ahp_strlen_t HPACK_FIELD_REFERER = {.str = "referer", .len = 7};
ahp_strlen_t HPACK_FIELD_REFRESH = {.str = "refresh", .len = 7};
ahp_strlen_t HPACK_FIELD_RETRY_AFTER = {.str = "retry-after", .len = 11};
ahp_strlen_t HPACK_FIELD_SERVER = {.str = "server", .len = 6};
ahp_strlen_t HPACK_FIELD_SET_COOKIE = {.str = "set-cookie", .len = 10};
ahp_strlen_t HPACK_FIELD_STRICT_TRANSPORT_SECURITY = {.str = "strict-transport-security", .len = 25};
ahp_strlen_t HPACK_FIELD_TRANSFER_ENCODING = {.str = "transfer-encoding", .len = 17};
ahp_strlen_t HPACK_FIELD_USER_AGENT = {.str = "user-agent", .len = 10};
ahp_strlen_t HPACK_FIELD_VARY = {.str = "vary", .len = 4};
ahp_strlen_t HPACK_FIELD_VIA = {.str = "via", .len = 3};
ahp_strlen_t HPACK_FIELD_WWW_AUTHENTICATE = {.str = "www-authenticate", .len = 16};

ahp_strlen_t HPACK_VALUE_GET = {.str = "GET", .len = 3};
ahp_strlen_t HPACK_VALUE_POST = {.str = "POST", .len = 4};
ahp_strlen_t HPACK_VALUE_SLASH = {.str = "/", .len = 1};
ahp_strlen_t HPACK_VALUE_INDEX_HTML = {.str = "/index.html", .len = 11};
ahp_strlen_t HPACK_VALUE_HTTP = {.str = "http", .len = 4};
ahp_strlen_t HPACK_VALUE_HTTPS = {.str = "https", .len = 5};
ahp_strlen_t HPACK_VALUE_200 = {.str = "200", .len = 3};
ahp_strlen_t HPACK_VALUE_204 = {.str = "204", .len = 3};
ahp_strlen_t HPACK_VALUE_206 = {.str = "206", .len = 3};
ahp_strlen_t HPACK_VALUE_304 = {.str = "304", .len = 3};
ahp_strlen_t HPACK_VALUE_400 = {.str = "400", .len = 3};
ahp_strlen_t HPACK_VALUE_404 = {.str = "405", .len = 3};
ahp_strlen_t HPACK_VALUE_500 = {.str = "500", .len = 3};
ahp_strlen_t HPACK_VALUE_GZIP_DEFALTE = {.str = "gzip, defalte", .len = 13};

const size_t STATIC_INDEX_TABLE_SIZE = 61;

ahp_header_index_t ahp_static_index_table[STATIC_INDEX_TABLE_SIZE + 1] = {
    /*  0 */ {.name = NULL, .value = NULL},
    /*  1 */ {.name = &HPACK_FIELD_AUTHORITY, .value = NULL},
    /*  2 */ {.name = &HPACK_FIELD_METHOD, .value = &HPACK_VALUE_GET},
    /*  3 */ {.name = &HPACK_FIELD_METHOD, .value = &HPACK_VALUE_POST},
    /*  4 */ {.name = &HPACK_FIELD_PATH, .value = &HPACK_VALUE_SLASH},
    /*  5 */ {.name = &HPACK_FIELD_PATH, .value = &HPACK_VALUE_INDEX_HTML},
    /*  6 */ {.name = &HPACK_FIELD_SCHEME, .value = &HPACK_VALUE_HTTP},
    /*  7 */ {.name = &HPACK_FIELD_SCHEME, .value = &HPACK_VALUE_HTTPS},
    /*  8 */ {.name = &HPACK_FIELD_STATUS, .value = &HPACK_VALUE_200},
    /*  9 */ {.name = &HPACK_FIELD_STATUS, .value = &HPACK_VALUE_204},
    /* 10 */ {.name = &HPACK_FIELD_STATUS, .value = &HPACK_VALUE_206},
    /* 11 */ {.name = &HPACK_FIELD_STATUS, .value = &HPACK_VALUE_400},
    /* 12 */ {.name = &HPACK_FIELD_STATUS, .value = &HPACK_VALUE_404},
    /* 13 */ {.name = &HPACK_FIELD_STATUS, .value = &HPACK_VALUE_304},
    /* 14 */ {.name = &HPACK_FIELD_STATUS, .value = &HPACK_VALUE_500},
    /* 15 */ {.name = &HPACK_FIELD_ACCEPT_CHARSET, .value = NULL},
    /* 16 */ {.name = &HPACK_FIELD_ACCEPT_ENCODING, .value = &HPACK_VALUE_GZIP_DEFALTE},
    /* 17 */ {.name = &HPACK_FIELD_ACCEPT_LANGUAGE, .value = NULL},
    /* 18 */ {.name = &HPACK_FIELD_ACCEPT_RANGE, .value = NULL},
    /* 19 */ {.name = &HPACK_FIELD_ACCEPT, .value = NULL},
    /* 20 */ {.name = &HPACK_FIELD_ACCESS_CONTROL_ALLOW_ORIGIN, .value = NULL},
    /* 21 */ {.name = &HPACK_FIELD_AGE, .value = NULL},
    /* 22 */ {.name = &HPACK_FIELD_ALLOW, .value = NULL},
    /* 23 */ {.name = &HPACK_FIELD_AUTHORIZATION, .value = NULL},
    /* 24 */ {.name = &HPACK_FIELD_CACHE_CONTROL, .value = NULL},
    /* 25 */ {.name = &HPACK_FIELD_CONTENT_DISPOSITION, .value = NULL},
    /* 26 */ {.name = &HPACK_FIELD_CONTENT_ENCODING, .value = NULL},
    /* 27 */ {.name = &HPACK_FIELD_CONTENT_LANGUAGE, .value = NULL},
    /* 28 */ {.name = &HPACK_FIELD_CONTENT_LENGTH, .value = NULL},
    /* 29 */ {.name = &HPACK_FIELD_CONTENT_LOCATION, .value = NULL},
    /* 30 */ {.name = &HPACK_FIELD_CONTENT_RANGE, .value = NULL},
    /* 31 */ {.name = &HPACK_FIELD_CONTENT_TYPE, .value = NULL},
    /* 32 */ {.name = &HPACK_FIELD_COOKIE, .value = NULL},
    /* 33 */ {.name = &HPACK_FIELD_DATE, .value = NULL},
    /* 34 */ {.name = &HPACK_FIELD_ETAG, .value = NULL},
    /* 35 */ {.name = &HPACK_FIELD_EXPECT, .value = NULL},
    /* 36 */ {.name = &HPACK_FIELD_EXPIRES, .value = NULL},
    /* 37 */ {.name = &HPACK_FIELD_FROM, .value = NULL},
    /* 38 */ {.name = &HPACK_FIELD_HOST, .value = NULL},
    /* 39 */ {.name = &HPACK_FIELD_IF_MATCH, .value = NULL},
    /* 40 */ {.name = &HPACK_FIELD_IF_MODIFIED_SINCE, .value = NULL},
    /* 41 */ {.name = &HPACK_FIELD_IF_NONE_MATCH, .value = NULL},
    /* 42 */ {.name = &HPACK_FIELD_IF_RANGE, .value = NULL},
    /* 43 */ {.name = &HPACK_FIELD_IF_UNMODIFIED_SINCE, .value = NULL},
    /* 44 */ {.name = &HPACK_FIELD_LAST_MODIFIED, .value = NULL},
    /* 45 */ {.name = &HPACK_FIELD_LINK, .value = NULL},
    /* 46 */ {.name = &HPACK_FIELD_LOCATION, .value = NULL},
    /* 47 */ {.name = &HPACK_FIELD_MAX_FORWARDS, .value = NULL},
    /* 48 */ {.name = &HPACK_FIELD_PROXY_AUTHENTICATE, .value = NULL},
    /* 49 */ {.name = &HPACK_FIELD_PROXY_AUTHORIZATION, .value = NULL},
    /* 50 */ {.name = &HPACK_FIELD_RANGE, .value = NULL},
    /* 51 */ {.name = &HPACK_FIELD_REFERER, .value = NULL},
    /* 52 */ {.name = &HPACK_FIELD_REFRESH, .value = NULL},
    /* 53 */ {.name = &HPACK_FIELD_RETRY_AFTER, .value = NULL},
    /* 54 */ {.name = &HPACK_FIELD_SERVER, .value = NULL},
    /* 55 */ {.name = &HPACK_FIELD_SET_COOKIE, .value = NULL},
    /* 56 */ {.name = &HPACK_FIELD_STRICT_TRANSPORT_SECURITY, .value = NULL},
    /* 57 */ {.name = &HPACK_FIELD_TRANSFER_ENCODING, .value = NULL},
    /* 58 */ {.name = &HPACK_FIELD_USER_AGENT, .value = NULL},
    /* 59 */ {.name = &HPACK_FIELD_VARY, .value = NULL},
    /* 60 */ {.name = &HPACK_FIELD_VIA, .value = NULL},
    /* 61 */ {.name = &HPACK_FIELD_WWW_AUTHENTICATE, .value = NULL},
};
