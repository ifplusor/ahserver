# encoding=utf-8


__all__ = ["HttpMethod", "HttpVersion", "HttpStatus", "PopularHttpHeaders"]

from enum import Enum


class HttpMethod(Enum):
    OPTIONS = "OPTIONS"
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    TRACE = "TRACE"
    CONNECT = "CONNECT"

    def __str__(self):
        return self.value

    @staticmethod
    def parse(method: str):
        try:
            return HttpMethod[method.upper()]
        except:
            raise Exception("Unknown http method")


class HttpVersion(Enum):
    V10 = "1.0"
    V11 = "1.1"
    V20 = "2.0"

    def __str__(self):
        return self.value

    @staticmethod
    def parse(version: str):
        if version == "1.1":
            return HttpVersion.V11
        elif version == "1.0":
            return HttpVersion.V10
        elif version == "2.0":
            return HttpVersion.V20
        else:
            raise Exception("Unknown http version.")


class HttpStatus(Enum):
    # 1xx: 信息性 - 收到请求，继续处理
    Continue = (100, "Continue")
    Switching_Protocol = (101, "Switching Protocol")

    # 2xx: 成功性 - 成功收到、理解并接受行动
    OK = (200, "OK")
    Created = (201, "Created")
    Accepted = (202, "Accepted")
    Non_Authoritative_Information = (203, "Non-Authoritative Information")
    No_Content = (204, "No Content")
    Reset_Content = (205, "Reset Content")
    Partial_Content = (206, "Partial Content")

    # 3xx: 重定向 - 必须采取进一步行动来完成请求
    Move_Permanently = (301, "Moved Permanently")
    Found = (302, "Found")
    Temporary_Redirect = (307, "Temporary Redirect")

    # 4xx: 客户端错误 - 请求包含错误语法或不能完成
    Bad_Request = (400, "Bad Request")
    Unauthorized = (401, "Unauthorized")
    Forbidden = (403, "Forbidden")
    Not_Found = (404, "Not Found")

    # 5xx: 服务器错误 - 服务器没有成功完成显然有效的请求
    Internal_Server_Error = (500, "Internal Server Error")
    Not_Implemented = (501, "Not Implemented")
    Bad_Gateway = (502, "Bad Gateway")
    Service_Unavailable = (503, "Service Unavailable")
    Gateway_Timeout = (504, "Gateway Time-out")
    HTTP_Version_Not_Unsupported = (505, "HTTP Version not supported")

    def __str__(self):
        return "{} {}".format(self.value[0], self.value[1])


class PopularHttpHeaders:
    connection_close = {"Connection": "close"}

    type_plain = {"Content-Type": "text/plain"}
    type_html = {"Content-Type": "text/html"}
    type_json = {"Content-Type": "application/json"}

    @staticmethod
    def union(*args):
        headers = {}
        for arg in args:
            headers.update(arg)
        return headers
