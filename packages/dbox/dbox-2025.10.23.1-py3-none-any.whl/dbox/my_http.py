import os
import json
import requests
from urllib.parse import urlparse, unquote
from requests.cookies import RequestsCookieJar
from requests.structures import CaseInsensitiveDict

from . import logger
from .utils import get_caller_info, MyJSONEncoder


def parser_cookies_by_headers(headers: CaseInsensitiveDict):
    cookies = RequestsCookieJar()
    cookie_str = headers.get("Cookie", "")
    if cookie_str:
        for cookie in cookie_str.strip().split(";"):
            key, value = cookie.strip().split("=")
            cookies.set(key.strip(), value.strip())
    return cookies


def check_response(
    response: requests.Response,
    operate="",
    ignore_error=True,
    echo=False,
    caller_info: dict | None = None,
    disable_echo: bool = False,
) -> bool:
    """检查response是否成功
    :param response: Requests的请求返回对象
    :param operate: str, 请求操作描述，为空时会自动根据函数调用栈定位到源函数，获取其描述信息
    :param ignore_error: bool, 为True时即使请求不成功也不抛错，直接返回Response原始对象
    :param echo: bool, 强制输出日志，优化级低于disable_echo
    :param caller_info: dict, 调用源信息，优先级低于operate
    :param disable_echo: bool, 为True时禁用显示请求报文，优先级最高
    """
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        if content_type and "json" in content_type:
            if not operate:
                _info = caller_info or get_caller_info(2)
                operate = f"调用{_info['output']})"
            if response.json().get("code") in (0, 200, "200"):
                status = True
            elif response.json().get("success") is True:
                status = True
            else:
                msg = f"{operate}失败，错误详情：{response.text}"
                if ignore_error:
                    status = False
                    logger.error(msg)
                else:
                    if disable_echo is False:
                        format_output(response, level="error", depth=3)
                    raise ValueError(msg)

            # 根据请求结果与调试标志输出
            if not status or echo or os.environ.get("ALWAYS_ECHO_RESULT"):
                if status:
                    level = "debug"
                else:
                    level = "error"
                if disable_echo is False:
                    format_output(response, level=level, depth=3)
            return status
        else:
            return True
    else:
        if ignore_error:
            if disable_echo is False:
                format_output(response, level="warning", depth=3)
            return False
        else:
            if disable_echo is False:
                format_output(response, level="error", depth=3)
            raise ValueError(response.text)


def format_output(obj, level="debug", depth=2, caller_info: dict | None = None):
    def __output_response(__obj: requests.Response):
        _logger(f"请求地址：{__obj.request.method}, {__obj.request.url}")
        _logger(f"请求头部：{json.dumps(dict(__obj.request.headers), ensure_ascii=False, indent=4, cls=MyJSONEncoder)}")
        if __obj.request.body:
            if "application/json" in __obj.request.headers.get("Content-Type", ""):
                if isinstance(__obj.request.body, bytes):
                    body = json.loads(__obj.request.body.decode("utf-8"))
                else:
                    body = json.loads(__obj.request.body)
                _logger(f"请求内容：{json.dumps(body, ensure_ascii=False, indent=4, cls=MyJSONEncoder)}")
            elif "multipart/form-data" in __obj.request.headers.get("Content-Type", ""):
                if isinstance(__obj.request.body, bytes):
                    _logger(f"请求内容：可能包含文件内容，忽略不显示")
                else:
                    _logger(f"请求内容：{str(__obj.request.body)}")
            else:
                if isinstance(__obj.request.body, bytes):
                    _logger(f"请求内容：{__obj.request.body.decode('utf-8')}")
                else:
                    _logger(f"请求内容：{__obj.request.body}")
        _logger(f"响应首行：{__obj.status_code}, {__obj.reason}, {__obj.url}, 耗时：{__obj.elapsed}")
        _logger(f"响应头部：{json.dumps(dict(__obj.headers), ensure_ascii=False, indent=4, cls=MyJSONEncoder)}")
        if __obj.text.strip():
            if "application/json" in __obj.headers.get("Content-Type", ""):
                _logger(f"响应内容：{json.dumps(__obj.json(), ensure_ascii=False, indent=4, cls=MyJSONEncoder)}")
            else:
                if "attachment" in __obj.headers.get("Content-Disposition", ""):
                    _logger(f"响应内容：包含文件内容，忽略不显示")
                else:
                    _logger(f"响应内容：{__obj.text}")

    _info = caller_info or get_caller_info(depth)
    _logger = getattr(logger, level)
    _logger(f"格式化输出调用源：{_info['output']}")
    try:
        if isinstance(obj, (dict, list, tuple)):
            _logger(json.dumps(obj, ensure_ascii=False, indent=4, cls=MyJSONEncoder))
        elif isinstance(obj, requests.Response):
            if obj.history:
                for __obj in obj.history:
                    __output_response(__obj)
            __output_response(obj)
        else:
            _logger(obj)
    except Exception as _e:
        logger.exception(_e)
        logger.warning("格式法输出对象出错，忽略")
        _logger(f"type={type(obj)}, value={str(obj)}")


def response_to_str(response: requests.Response) -> str:
    request = response.request
    _msg = f"请求地址：{request.method} - {request.url}\n"
    _msg += f"请求头：{json.dumps(dict(request.headers), ensure_ascii=False, indent=4, cls=MyJSONEncoder)}\n"

    if request.body:
        if "application/json" in request.headers.get("Content-Type", ""):
            if isinstance(request.body, bytes):
                body = json.loads(request.body.decode("utf-8"))
            else:
                body = json.loads(request.body)
            _msg += f"请求内容：{json.dumps(body, ensure_ascii=False, indent=4, cls=MyJSONEncoder)}\n"
        elif "multipart/form-data" in request.headers.get("Content-Type", ""):
            if isinstance(request.body, bytes):
                _msg += f"请求内容：可能包含文件内容，忽略不显示\n"
            else:
                _msg += f"请求内容：{str(request.body)}\n"
        else:
            if isinstance(request.body, bytes):
                _msg += f"请求内容：{request.body.decode('utf-8')}\n"
            else:
                _msg += f"请求内容：{request.body}\n"
    _msg += f"响应首行：{response.status_code}, {response.reason}, {response.url}, 耗时：{response.elapsed}\n"
    _msg += f"响应头部：{json.dumps(dict(response.headers), ensure_ascii=False, indent=4, cls=MyJSONEncoder)}\n"
    if response.text.strip():
        if "application/json" in response.headers.get("Content-Type", ""):
            _msg += f"响应内容：{json.dumps(response.json(), ensure_ascii=False, indent=4, cls=MyJSONEncoder)}\n"
        else:
            if "attachment" in response.headers.get("Content-Disposition", ""):
                _msg += f"响应内容：包含文件内容，忽略不显示\n"
            else:
                _msg += f"响应内容：{response.text}\n"
    else:
        _msg += f"响应内容：无\n"
    return _msg


def clean_null_key_for_dict(my_dict: dict):
    """将字典中第一层的空值清除"""
    if isinstance(my_dict, dict):
        for key, value in list(my_dict.items()):
            if value is None:
                my_dict.pop(key)
    return my_dict


def parse_url_to_dict(url: str, _all=True, unquote_count: int = 0) -> dict:
    """将url解析成字典"""
    payload = dict()
    url = unquote_url(url, unquote_count)
    url_obj = urlparse(url)
    if _all:
        payload["scheme"] = url_obj.scheme
        payload["netloc"] = url_obj.netloc
        payload["path"] = url_obj.path
        payload["params"] = url_obj.params
        payload["query"] = url_obj.query
        payload["fragment"] = url_obj.fragment

    query_dict = query_str_to_dict(url_obj.query)
    fragment_dict = query_str_to_dict(url_obj.fragment)
    payload.update(query_dict)
    payload.update(fragment_dict)
    return payload


def pop_key_from_dict(my_dict: dict, key, default=None):
    if key in my_dict:
        value = my_dict.pop(key)
    else:
        value = default
    return value


def query_str_to_dict(_str: str) -> dict:
    """将URL查询字符串转换成dict"""
    payload = dict()
    if _str:
        _str = unquote(_str)

        while "?" in _str:
            _key, _str = _str.split("?", 1)
            logger.debug(f"剥离{_key}")

        for item in _str.split("&"):
            try:
                key, values = item.split("=")
            except ValueError as e:
                logger.warning(
                    "拆包时出现异常，可能是字符串中存在多个【=】导致，启用备用方案拆包：忽略第2个及以后的【=】字符"
                )
                logger.warning(f"原始字符串：{item}")
                key, values = item.split("=", 1)
            payload[key] = values
    return payload


def unquote_url(url, unquote_count: int = 0) -> str:
    """解析URL"""
    if unquote_count > 0:
        # 按指定的循环次数解码
        for _ in range(unquote_count):
            url = unquote(url)
    else:
        # 自动解码
        while True:
            _before_url = url
            url = unquote(url)
            if _before_url == url:
                break
    return url
