# encoding=utf-8


__all__ = ["Response", "HttpResponse"]

from .protocol import HttpStatus
from .request import HttpRequest
from ..structures.dict import CaseInsensitiveDict


class Response:
    def __init__(self, connection=None):
        self._connection = connection


supported_encoding = dict()

try:
    import gzip

    supported_encoding["gzip"] = gzip.compress
except:
    pass


class HttpResponse(Response):

    def __init__(self, request: HttpRequest, status=HttpStatus.OK, headers: dict = None, body=None):
        super().__init__(request.connection)
        self._request = request

        self.status = status
        self.headers = CaseInsensitiveDict(headers)
        self.body = body

    def _check_encoding(self):
        # use Content-Encoding first
        use_encoding = self.headers.get("Content-Encoding")
        if use_encoding is not None:
            return use_encoding

        # choose from Accept-Encoding
        accept_encoding = self._request.get_header("Accept-Encoding")
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
            encoding_list = sorted(encoding_list, key=lambda x: x[1], reverse=True)  # 稳定排序
            for encoding in encoding_list:
                # FIXME: when qvalue is 0
                if encoding[0] in supported_encoding:
                    use_encoding = encoding[0]
                    break

        return use_encoding

    def render(self):
        # Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
        status_line = "HTTP/{} {} {}\r\n".format(self._request.version, self.status.value[0], self.status.value[1])

        skipped_headers = {
            "content-encoding"
        }

        headers = ""
        for header in self.headers:
            if header.lower() in skipped_headers:
                continue
            headers += "{}: {}\r\n".format(header, self.headers[header])

        if self.body is not None:
            # convert body to bytes
            if isinstance(self.body, bytes):
                body = self.body
            else:
                body = str(self.body).encode("utf-8")

            # encode
            encoding = self._check_encoding()
            if encoding is not None:
                body = supported_encoding[encoding](body)
                headers += "{}: {}\r\n".format("Content-Encoding", encoding)

            headers += "{}: {}\r\n".format("Content-Length", len(body))
        else:
            body = b""

        return "{}{}\r\n".format(status_line, headers).encode("utf-8") + body

    def will_close(self):
        return self.headers.get("Connection", "") == "close"
