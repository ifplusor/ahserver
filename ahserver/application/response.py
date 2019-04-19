# encoding=utf-8

from ..http2 import HttpRequest, HttpResponse
from ..http2.protocol import HttpHeader, HttpStatus

try:
    from typing import Any, Dict, Optional, Union
except Exception:
    pass


supported_encoding = dict()

# gzip compress supported
try:
    import gzip

    supported_encoding["gzip"] = gzip.compress
except Exception:
    pass

# constant
SIZE_20KB = 20 * 1024
CHARSET_TYPE_LABEL = ";charset="
CHARSET_DEFAULT = "utf-8"
CHARSET_DEFAULT_TYPE_SUFFIX = CHARSET_TYPE_LABEL + CHARSET_DEFAULT

# ignored request headers in response
skipped_headers = {
    HttpHeader.CONTENT_ENCODING,
    HttpHeader.CONTENT_LENGTH,
}


class DefaultHttpResponse(HttpResponse):
    def __init__(self, request, status=HttpStatus.OK, headers=None, body=None):
        # type: (HttpRequest, Optional[Union[str, HttpStatus]], Optional[Dict[HttpHeader, str]], Any) -> None
        super(DefaultHttpResponse, self).__init__(request, status, headers)

        self._body = body
        self._rendered = None

    def _check_encoding(self):
        """选择编码算法"""

        # use Content-Encoding first
        use_encoding = self.headers.get(HttpHeader.CONTENT_ENCODING)
        if use_encoding is not None:
            return use_encoding

        # choose from Accept-Encoding
        accept_encoding = self._request.get(HttpHeader.ACCEPT_ENCODING)
        if accept_encoding is not None:
            # Accept-Encoding = "Accept-Encoding" ":" 1#( codings [ ";" "q" "=" qvalue ] )
            # codings = ( content-coding | "*" )

            encoding_list = filter(lambda x: x.strip(), accept_encoding.decode().split(","))

            def format_encoding(e: str):
                s = e.split(";q=")
                if len(s) > 1:
                    return s[0], float(s[1])
                else:
                    return s[0], 1.0

            encoding_list = map(format_encoding, encoding_list)

            # TODO: 根据 body 大小选择压缩算法

            if len(self._body) < SIZE_20KB:
                for encoding in encoding_list:
                    if "deflate" == encoding[0]:
                        return "deflate"

            encoding_list = sorted(encoding_list, key=lambda x: x[1], reverse=True)  # 稳定排序
            for encoding in encoding_list:
                # FIXME: when qvalue is 0
                if encoding[0] in supported_encoding:
                    use_encoding = encoding[0]
                    break

        return use_encoding

    def respond(self, stream):
        """render response packet"""

        if self._rendered is not None:
            # use render cache
            return self._rendered

        # prepare header
        headers_dict = self.headers.copy()
        for header in skipped_headers:
            if header in headers_dict:
                del headers_dict[header]

        # render body
        if self._body is not None:
            # convert body to bytes
            if isinstance(self._body, bytes):
                body = self._body
            else:
                body = str(self._body).encode(CHARSET_DEFAULT)
                if HttpHeader.CONTENT_TYPE in headers_dict:
                    headers_dict[HttpHeader.CONTENT_TYPE] = (
                        headers_dict[HttpHeader.CONTENT_TYPE] + CHARSET_DEFAULT_TYPE_SUFFIX
                    )

            # encode body
            encoding = self._check_encoding()
            if encoding is not None:
                body = supported_encoding[encoding](body)
                headers_dict[HttpHeader.CONTENT_ENCODING] = encoding

            headers_dict[HttpHeader.CONTENT_LENGTH] = len(body)
        else:
            body = None
            headers_dict[HttpHeader.CONTENT_LENGTH] = 0

        self.headers = headers_dict
        self.body = body

        # render packet
        self._rendered = super(DefaultHttpResponse, self).respond(stream)

        return self._rendered
