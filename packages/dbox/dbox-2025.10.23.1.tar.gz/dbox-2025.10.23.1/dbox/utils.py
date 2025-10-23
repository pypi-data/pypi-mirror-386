"""工具函数，与打包逻辑无直接关联"""

import math

# coding = utf-8
import os
import uuid
import json
import time
import logging
import inspect
import datetime
import subprocess
from collections.abc import Sequence
from pathlib import Path
from decimal import Decimal
from functools import wraps


logger = logging.getLogger("DBox")


class ExecuteCMDException(Exception):
    """执行外部命令异常"""

    pass


def pop_key_from_dict(my_dict: dict, key, default=None):
    if key in my_dict:
        value = my_dict.pop(key)
    else:
        value = default
    return value


def execute_cmd(
    *popenargs,
    input=None,
    capture_output=True,
    timeout=None,
    check=False,
    level="info",
    encoding="utf-8",
    **kwargs,
):
    """通过subprocess库执行命令行"""
    kwargs["input"] = input
    kwargs["capture_output"] = capture_output
    kwargs["timeout"] = timeout
    kwargs["check"] = check
    ignore_error_log = pop_key_from_dict(kwargs, "ignore_error_log", default=True)
    cmd_output_level = pop_key_from_dict(kwargs, "cmd_output_level", default=level)
    if encoding:
        kwargs["encoding"] = encoding
    if isinstance(popenargs, Sequence):
        if isinstance(popenargs[0], str):
            cmd_text = popenargs[0]
        elif isinstance(popenargs[0], Sequence):
            cmd_text = " ".join(popenargs[0])
        elif isinstance(popenargs[0], Path):
            cmd_text = popenargs[0].name
            kwargs["cwd"] = popenargs[0].parent
        else:
            raise ValueError(f"参数遇到未知情况：{popenargs}")
    else:
        raise ValueError(f"参数遇到未知情况：{popenargs}")

    if level:
        getattr(logger, level)(f"执行命令：{cmd_text}")

    # 增加异常兼容逻辑，处理npm时的可能报错
    for run_count in range(2):
        try:
            _res = subprocess.run(*popenargs, **kwargs)
        except IndexError as e:
            if run_count == 0:
                logger.exception(e)
                logger.warning(f"运行报错，当前capture_output={capture_output}，翻转capture_output参数，再次尝试运行……")
                kwargs["capture_output"] = not kwargs["capture_output"]
            else:
                error_msg = f"执行命令出错：{os.getcwd()} - {cmd_text}\n{str(e)}"
                if not ignore_error_log:
                    logger.error(error_msg)
                raise ExecuteCMDException(error_msg)
        except Exception as e:
            error_msg = f"执行命令出错：{os.getcwd()} - {cmd_text}\n{str(e)}"
            if not ignore_error_log:
                logger.error(error_msg)
            raise ExecuteCMDException(error_msg)
        else:
            if _res.returncode == 0:
                if _res.stdout and cmd_output_level:
                    # 有些命令如npm，会将警告信息打印在stderr中
                    output = f"{byte_to_str(_res.stderr)}\n{byte_to_str(_res.stdout)}"
                    getattr(logger, cmd_output_level)(output)
                return _res
            else:
                error_output = f"{byte_to_str(_res.stderr)}\n{byte_to_str(_res.stdout)}"
                error_msg = f"执行命令出错：{os.getcwd()} - {cmd_text}\n{error_output}"
                if not ignore_error_log:
                    logger.error(error_msg)
                raise ExecuteCMDException(error_msg)


def check_shell_run_result(res_code, desc=""):
    """检查结果，非0时报错"""
    if res_code == 0:
        return True
    else:
        raise ExecuteCMDException(f"{desc}命令执行失败，返回结果={res_code}")


def my_json_serializable(o):
    """补充标准库中json serializable逻辑"""
    if isinstance(o, datetime.datetime):
        return o.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(o, datetime.date):
        return o.strftime("%Y-%m-%d")
    if isinstance(o, uuid.UUID):
        return str(o)
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, Decimal):
        return float(o)
    if hasattr(o, "__html__"):
        return str(o.__html__())

    try:
        return str(o)
    except (TypeError, ValueError):
        raise TypeError(f"Object of type {o.__class__.__name__} " f"is not JSON serializable")


class MyJSONEncoder(json.encoder.JSONEncoder):
    """自定义JSON序列化类"""

    def default(self, o):
        return my_json_serializable(o)


def json_to_str(content, indent: int = 4) -> str:
    try:
        return json.dumps(content, ensure_ascii=False, indent=4, cls=MyJSONEncoder)
    except Exception as _error:
        return str(content)


def byte_to_str(src, encoding=None) -> str:
    if isinstance(src, bytes):
        error_list = []
        encoding_list = ["utf-8", "GBK", "GB2312", "GB18030", "ISO-8859-1"]
        if encoding:
            # 已经存在时删除再插入到第一位，确保指定的编码第一个运行
            if encoding in encoding_list:
                encoding_list.remove(encoding)
            encoding_list.insert(0, encoding)

        for encoding in encoding_list:
            try:
                return str(src, encoding=encoding).strip()
            except UnicodeDecodeError as e:
                error_list.append(e)
        if error_list:
            logger.warning(f"bytes转换成str时出错，尝试的编码有：{encoding_list}，原始对象：{src}")
    elif src is None:
        return ""
    return src.strip() if isinstance(src, str) else str(src)


def bytes_to_str(src, encoding=None):
    return byte_to_str(src, encoding=encoding)


def to_boolean(flag, default=False):
    """将字符串或数字转换成布尔型"""
    if isinstance(flag, bool):
        return flag
    elif flag is None or len(str(flag)) == 0:
        return default
    elif str(flag).lower() in ("false", "no", "0"):
        return False
    else:
        return True


def get_digit_from_input(params=None):
    """从键盘获取一个数字，并做规范性检查
    :param params: list | tuple, 如果给出则输入的数字必须在params内。
    """
    while True:
        try:
            num_str = input("请输入一个有效数字：")
            if num_str.isdigit():
                num_int = int(num_str)
                if isinstance(params, (tuple, list)) and params:
                    if num_int in params:
                        break
                    else:
                        print("输入的不是一个有效选项！")
                else:
                    break
            else:
                print("输入的不是一个数字！")
        except (ValueError, TypeError):
            print("输入的不是一个数字！")
    return num_int


def stat_func_elapsed(func):
    """装饰器：统计被装饰方法的运行耗时"""

    @wraps(func)
    def _stat_func_elapsed(*args, **kwargs):
        func_name = func.__name__
        func_desc = func.__doc__.strip().split()[0] or ""
        logger.info(f"开始运行：{func_name}（{func_desc}）")
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = round(time.perf_counter() - start_time, 3)
            logger.info(f"结束运行：{func_name}（{func_desc}），耗时：{elapsed}秒")

    return _stat_func_elapsed


def polishing_int(number: int, length: int, fill_char: str = "0") -> str:
    """数字补齐"""
    number_str = str(number)
    if len(number_str) < length:
        return fill_char * (length - len(number_str)) + number_str
    return number_str


def extract_func_elapsed(elapsed_collector, parent=None, node=None):
    """装饰器：统计被装饰方法的运行耗时"""

    def _stat_func_elapsed1(func):
        @wraps(func)
        def _stat_func_elapsed2(*args, **kwargs):
            func_name = func.__name__
            func_desc = func.__doc__.strip().split()[0] or ""

            index_no = elapsed_collector.size()
            index_no = polishing_int(index_no, length=3, fill_char="0")

            # 记录打包节点信息
            # 判断节点是否已经存在
            if node and node in elapsed_collector.nodes.keys():
                node_identifier = node + "-" + str(elapsed_collector.size() + 1)
            elif func_name in elapsed_collector.nodes.keys():
                node_identifier = func_name + "-" + str(elapsed_collector.size() + 1)
            else:
                node_identifier = node or func_name

            elapsed_collector.create_node(
                tag=f"{index_no} - {func_name}（{func_desc}）：运行中",
                identifier=node_identifier,
                parent=parent,
            )

            logger.info(f"开始运行：{func_name}（{func_desc}）")
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = round(time.perf_counter() - start_time, 1)
                logger.info(f"结束运行：{func_name}（{func_desc}），耗时：{elapsed}秒")
                elapsed_collector.nodes[node_identifier].tag = (
                    f"{index_no} - 耗时【{elapsed}】：{func_name}（{func_desc}）"
                )

        return _stat_func_elapsed2

    return _stat_func_elapsed1


def get_caller_info(depth: int) -> dict[str, str]:
    """获取调用方名称与描述
    :param depth: int, 函数调用栈递归深度，当前方法为0，依次往上递增
    """
    # 获取调用方描述
    from_obj = inspect.stack()[depth]

    _filename = Path(from_obj.filename).name
    _lineno = from_obj.lineno
    _func_name = from_obj.function

    _func_desc = from_obj.frame.f_code.co_consts[0]
    if _func_desc:
        _func_desc = _func_desc.split("\n")[0].strip()
    else:
        _func_desc = ""
    return {
        "file_abs_path": from_obj.filename,
        "filename": _filename,
        "lineno": str(_lineno),
        "func_name": _func_name,
        "func_desc": _func_desc,
        "output": f"[{_filename}/{_lineno}/{_func_name}/{_func_desc}]",
    }


def get_caller_desc(depth: int) -> str:
    """获取调用者描述或名称
    :param depth: int, 函数调用栈递归深度，当前方法为0，依次往上递增
    """
    try:
        doc_str = inspect.stack()[depth].frame.f_code.co_consts[0]
        if doc_str:
            doc_str = doc_str.split("\n")[0].strip()
        else:
            doc_str = inspect.stack()[depth].frame.f_code.co_name
        return doc_str
    except Exception as err:
        logger.exception(err)
        return ""


def get_excel_col_name_by_index(col_index: int) -> str:
    """根据列索引获取Excel中的列名"""
    if col_index <= 0:
        raise ValueError("Excel列索引号为从1开始的正整数")

    if 0 < col_index <= 26:
        return chr(col_index + 64)
    else:
        quotient = math.floor(col_index / 26)
        remainder = col_index % 26
        if remainder == 0:
            return get_excel_col_name_by_index(quotient - 1) + "Z"
        else:
            return get_excel_col_name_by_index(quotient) + chr(remainder + 64)
