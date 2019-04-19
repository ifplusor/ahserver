# encoding=utf-8

__all__ = [
    "HttpMethod",
    "HttpVersion",
    "HttpStatus",
    "HttpHeader",
    "PopularHeaders",
]

from enum import Enum

from ..util.parser import FieldNameEnumParser, IntPairEnumParser


@FieldNameEnumParser("http_method")
class HttpMethod(Enum):
    OPTIONS = "OPTIONS"
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    TRACE = "TRACE"
    CONNECT = "CONNECT"
    PRI = "PRI"

    def __str__(self) -> str:
        return self.value


class HttpVersion(Enum):
    V10 = "1.0"
    V11 = "1.1"
    V2 = "2"

    def __str__(self):
        return self.value

    @staticmethod
    def parse(version: str):
        if version == "1.1":
            return HttpVersion.V11
        elif version == "2":
            return HttpVersion.V2
        elif version == "1.0":
            return HttpVersion.V10
        else:
            raise Exception("Unknown http version.")


@IntPairEnumParser("http_status")
class HttpStatus(Enum):
    # 1xx: 信息性 - 收到请求，继续处理
    CONTINUE = (100, "Continue")
    SWITCHING_PROTOCOL = (101, "Switching Protocol")
    EARLY_HINT = (103, "Early Hints")

    # 2xx: 成功性 - 成功收到、理解并接受行动
    OK = (200, "OK")
    CREATED = (201, "Created")
    ACCEPTED = (202, "Accepted")
    NON_AUTHORITATIVE_INFORMATION = (203, "Non-Authoritative Information")
    NO_CONTENT = (204, "No Content")
    RESET_CONTENT = (205, "Reset Content")
    PARTIAL_CONTENT = (206, "Partial Content")

    # 3xx: 重定向 - 必须采取进一步行动来完成请求
    MOVE_PERMANENTLY = (301, "Moved Permanently")
    FOUND = (302, "Found")
    SEE_OTHER = (303, "See Other")
    NOT_MODIFIED = (304, "Not Modified")
    USE_PROXY = (305, "Use Proxy")
    TEMPORARY_REDIRECT = (307, "Temporary Redirect")
    PERMANENT_REDIRECT = (308, "Permanent Redirect")

    # 4xx: 客户端错误 - 请求包含错误语法或不能完成
    BAD_REQUEST = (400, "Bad Request")
    UNAUTHORIZED = (401, "Unauthorized")
    PAYMENT_REQUIRED = (402, "Payment Required")
    FORBIDDEN = (403, "Forbidden")
    NOT_FOUND = (404, "Not Found")
    METHOD_NOT_ALLOWED = (405, "Method Not Allowed")
    NOT_ACCEPTABLE = (406, "Not Acceptable")
    PROXY_AUTHENTICATION_REQUIRED = (407, "Proxy Authentication Required")
    REQUEST_TIMEOUT = (408, "Request Timeout")
    CONFLICT = (409, "Conflict")
    GONE = (410, "Gone")
    LENGTH_REQUIRED = (411, "Length Required")
    PRECONDITION_FAILED = (412, "Precondition Failed")
    PAYLOAD_TOO_LARGE = (413, "Payload Too Large")
    URI_TOO_LONG = (414, "URI Too Long")
    UNSUPPORTED_MEDIA_TYPE = (415, "Unsupported Media Type")
    RANGE_NOT_SATISFIABLE = (416, "Range Not Satisfiable")
    EXPECTATION_FAILED = (417, "Expectation Failed")
    I_M_A_TEAPOT = (418, "I'm a teapot")
    UNPROCESSABLE_ENTITY = (422, "Unprocessable Entity")
    TOO_EARLY = (425, "Too Early")
    UPGRADE_REQUIRED = (426, "Upgrade Required")
    PRECONDITION_REQUIRED = (428, "Precondition Required")
    TOO_MANY_REQUESTS = (429, "Too Many Requests")
    REQUEST_HEADER_FIELDS_TOO_LARGE = (431, "Request Header Fields Too Large")
    UNAVAILABLE_FOR_LEGAL_REASONS = (451, "Unavailable For Legal Reasons")

    # 5xx: 服务器错误 - 服务器没有成功完成显然有效的请求
    INTERNAL_SERVER_ERROR = (500, "Internal Server Error")
    NOT_IMPLEMENTED = (501, "Not Implemented")
    BAD_GATEWAY = (502, "Bad Gateway")
    SERVICE_UNAVAILABLE = (503, "Service Unavailable")
    GATEWAY_TIMEOUT = (504, "Gateway Time-out")
    HTTP_VERSION_NOT_UNSUPPORTED = (505, "HTTP Version not supported")
    VARIANT_ALSO_NEGOTIATES = (506, "Variant Also Negotiates")
    INSUFFICIENT_STORAGE = (507, "Insufficient Storage")
    LOOP_DETECTED = (508, "Loop Detected")
    NETWORK_AUTHENTICATION_REQUIRED = (511, "Network Authentication Required")

    def __str__(self):
        return "{} {}".format(self.value[0], self.value[1])


@FieldNameEnumParser("http_header")
class HttpHeader(Enum):
    # General Header Fields
    CACHE_CONTROL = "Cache-Control"
    CONNECTION = "Connection"
    DATE = "Date"
    PRAGMA = "Pragma"
    TRAILER = "Trailer"
    TRANSFER_ENCODING = "Transfer-Encoding"
    UPGRADE = "Upgrade"
    VIA = "Via"
    WARNING = "Warning"

    # Request Header Fields
    ACCEPT = "Accept"
    ACCEPT_CHARSET = "Accept-Charset"
    ACCEPT_ENCODING = "Accept-Encoding"
    ACCEPT_LANGUAGE = "Accept-Language"
    AUTHORIZATION = "Authorization"
    EXCEPT = "Except"
    FROM = "From"
    HOST = "Host"
    IF_MATCH = "If-Match"
    IF_MODIFIED_SINCE = "If-Modified-Since"
    IF_NONE_MATCH = "If-None-Match"
    IF_Range = "If-Range"
    IF_UNMODIFIED_SINCE = "If-Unmodified-Since"
    MAX_FORWARDS = "Max-Forwards"
    PROXY_AUTHORIZATION = "Proxy-Authorization"
    RANGE = "Range"
    REFERER = "Referer"
    TE = "TE"
    USER_AGENT = "User-Agent"
    HTTP2_SETTINGS = "HTTP2-Settings"

    # Response Header Fields
    ACCEPT_RANGES = "Accept-Ranges"
    AGE = "Age"
    ETAG = "Etag"
    LOCATION = "Location"
    PROXY_AUTHENTICATE = "Proxy-Authenticate"
    RETRY_AFTER = "Retry-After"
    SERVER = "Server"
    VARY = "Vary"
    WWW_AUTHENTICATE = "WWW-Authenticate"

    # Entity Header Fields
    ALLOW = "Allow"
    CONTENT_ENCODING = "Content-Encoding"
    CONTENT_LANGUAGE = "Content-Language"
    CONTENT_LENGTH = "Content-Length"
    CONTENT_MD5 = "Content-MD5"
    CONTENT_RANGE = "Content-Range"
    CONTENT_TYPE = "Content-Type"
    EXPIRES = "Expires"
    LAST_MODIFIED = "Last-Modified"

    def __str__(self) -> str:
        return self.value


class PopularHeaders:
    CONNECTION_CLOSE = {HttpHeader.CONNECTION: "close"}

    CONTENT_EMPTY = {HttpHeader.CONTENT_LENGTH: "0"}

    TYPE_PLAIN = {HttpHeader.CONTENT_TYPE: "text/plain"}
    TYPE_HTML = {HttpHeader.CONTENT_TYPE: "text/html"}
    TYPE_JSON = {HttpHeader.CONTENT_TYPE: "application/json"}

    UPGRADE_H2C = {HttpHeader.CONNECTION: "Upgrade", HttpHeader.UPGRADE: "h2c"}

    @staticmethod
    def union(*args):
        headers = {}
        for arg in args:
            headers.update(arg)
        return headers
