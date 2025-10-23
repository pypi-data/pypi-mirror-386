import sys
import logging
import logging.handlers
from pathlib import Path


__version__ = "2025.10.23.1"
__commit_id__ = "01a97b2"
log_format = logging.Formatter(
    "[%(asctime)s] %(threadName)s/%(name)s/%(filename)s/%(lineno)s/%(funcName)s/%(levelname)s: %(message)s"
)

# 日志句柄
logger = logging.getLogger("DBox")
# 此处必须为DEBUG，否则在UiBot中多次加载时会覆盖configure_logger中level配置
logger.setLevel(logging.DEBUG)

# 防止多次加载时产生重复的StreamHandler handler
if not logger.handlers:
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)


def clean_repeat_handler():
    """清理重复的日志handler"""
    from dbox.utils import get_caller_info

    _info = get_caller_info(2)
    logger.debug(f"调用来源：{_info['output']}")

    logger.debug(f"开始清理重复的日志句柄：{logger.handlers}")

    _first_console = False
    # 收集已有的 FileHandler 处理器输出文件路径列表
    log_file_set = set()
    for _handler in logger.handlers:
        if isinstance(_handler, logging.FileHandler):
            if _handler.baseFilename in log_file_set:
                _handler.flush()
                _handler.close()
                logger.removeHandler(_handler)
                logger.debug(f"关闭重复的：{_handler}")
            else:
                log_file_set.add(_handler.baseFilename)
        elif isinstance(_handler, logging.StreamHandler):
            # 对于StreamHandler实例，仅保留一个，防止越积越多
            if _first_console is False:
                _first_console = True
                logger.debug(f"保留：{_handler}")
            else:
                _handler.flush()
                _handler.close()
                logger.removeHandler(_handler)
                logger.debug(f"关闭：{_handler}")
        else:
            logger.debug(f"忽略：{_handler}")


def close_all_handler():
    """关闭所有日志handler"""
    from dbox.utils import get_caller_info

    _info = get_caller_info(2)
    logger.debug(f"调用来源：{_info['output']}")

    for handler in logger.handlers:
        handler.flush()
        handler.close()
        logger.removeHandler(handler)


def clean_handler(close_console_handler: bool = False):
    """清理日志handler，关闭所有FileHandler实例，StreamHandler实例只保留一个"""
    from dbox.utils import get_caller_info

    _info = get_caller_info(2)
    logger.debug(f"调用来源：{_info['output']}")

    _first_console = False
    logger.debug(f"开始清理日志句柄：{logger.handlers}")
    for _handler in logger.handlers:
        if isinstance(_handler, logging.FileHandler):
            logger.debug(f"关闭：{_handler}")
            _handler.flush()
            _handler.close()
            logger.removeHandler(_handler)
        elif isinstance(_handler, logging.StreamHandler):
            # 如果有指定新的console_handler，则关闭老的
            if close_console_handler:
                logger.debug(f"关闭：{_handler}")
                _handler.flush()
                _handler.close()
                logger.removeHandler(_handler)
            else:
                # 对于StreamHandler实例，仅保留一个，防止越积越多
                if _first_console is False:
                    _first_console = True
                    logger.debug(f"保留：{_handler}")
                else:
                    logger.debug(f"关闭：{_handler}")
                    _handler.flush()
                    _handler.close()
                    logger.removeHandler(_handler)
        else:
            logger.debug(f"忽略：{_handler}")


def configure_logger(
    level: int | None = None,
    handlers: list | None = None,
    log_file: Path | str | None = None,
    append: bool = True,
    caller_info: dict | None = None,
    unify_level: bool = False,
    fmt: logging.Formatter | None = None,
):
    """配置日志处理器
    :param level: int, 指定日志级别
    :param handlers: 日志处理器列表
    :param log_file: 日志文件存储路径
    :param append: 是否为追加模式。当为覆盖模式时会清空已有的handler再添加新的
    :param caller_info: 调用源信息
    :param unify_level: 统一日志级别，为True时各Handler与logger都采用统一的level
    :param fmt: 重置日志输出格式
    """
    from dbox.utils import get_caller_info

    _info = caller_info or get_caller_info(2)
    logger.debug(f"调用来源：{_info['output']}")

    # 设置主句柄日志级别
    if level is None:
        pass
    elif level in (
        logging.NOTSET,
        logging.DEBUG,
        logging.INFO,
        logging.WARN,
        logging.WARNING,
        logging.ERROR,
        logging.FATAL,
    ):
        logger.setLevel(level)
    else:
        raise ValueError(f"level参数非法：{level}")

    # 检查是否指定了新的console_handler处理器
    new_console_handler = False
    if handlers is None:
        handlers = list()
    for handler in handlers:
        if type(handler) == logging.StreamHandler:
            new_console_handler = True
            break

    # 重置日志处理器输出格式
    if fmt and isinstance(fmt, logging.Formatter):
        for handler in logger.handlers:
            handler.setFormatter(fmt)

    # 各Handler与Logger采用统一的level级别
    if isinstance(level, int) and unify_level:
        for handler in logger.handlers:
            handler.setLevel(level)

    # 非追加模式时，先清空所有已有的handler
    # 必须放置在设置已有Handler日志级别之后，因为已有的Handler可能被别处引用
    # 如果放置在最前面会导致在别处引用的handler日志级别无法受level参数控制
    if not append:
        clean_handler(new_console_handler)

    # 收集已有的 FileHandler 处理器输出文件路径列表
    log_file_list = []
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            log_file_list.append(str(handler.baseFilename))

    # 往日志句柄中添加处理器
    if handlers:
        for handler in handlers:
            # 判断是否重复
            if handler in logger.handlers:
                logger.debug(f"日志处理器已经存在，忽略：{handler}")
                continue

            # StreamHandler 类型的处理器只保留一个
            if type(handler) == logging.StreamHandler:
                if new_console_handler:
                    logger.addHandler(handler)
                    # 各Handler与Logger采用统一的level级别
                    if isinstance(level, int) and unify_level:
                        handler.setLevel(level)
                else:
                    logger.debug(f"StreamHandler 类型处理器已经存在（控制台只保留一个），忽略：{handler}")
                    continue

            # FileHandler 类型处理器不重复，输出到同一目的地的只保留一个
            if isinstance(handler, logging.FileHandler):
                if str(handler.baseFilename) in log_file_list:
                    logger.debug(f"已经有一个相同目的地的处理器，忽略：{handler}")
                    continue
                else:
                    # 各Handler与Logger采用统一的level级别
                    if isinstance(level, int) and unify_level:
                        handler.setLevel(level)
                    logger.addHandler(handler)
                    log_file_list.append(str(handler.baseFilename))
            elif isinstance(handler, logging.Handler):
                # logger.warning(f"忽略日志Handler：{handler}")
                # 各Handler与Logger采用统一的level级别
                if isinstance(level, int) and unify_level:
                    handler.setLevel(level)
                logger.addHandler(handler)
            else:
                raise TypeError(f"类型错误，预期为{logging.Handler}类型，实际为{type(handler)}类型")

    if log_file:
        if str(log_file) in log_file_list:
            logger.debug(f"已经有一个相同目的地的处理器，忽略：{log_file}")
        else:
            log_file = Path(log_file)
            if not log_file.parent.exists():
                log_file.parent.mkdir(parents=True)

            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_file, when="D", backupCount=15, encoding="utf-8"
            )
            file_handler.setFormatter(log_format)
            if level is not None:
                file_handler.setLevel(level)
            logger.addHandler(file_handler)
            log_file_list.append(str(log_file))

    logger.debug(f"日志配置完成，当前日志处理器：{logger.handlers}")


logger.info(f"当前dbox库版本号：{__version__}，唯一版本标识：{__commit_id__}")

if sys.version_info < (3, 12):
    logger.warning(
        "\033[91m[警告] 当前 Python 版本为 {}.{}，本项目仅保证 3.12 及以上版本兼容，低版本可能存在不兼容问题。\033[0m".format(
            sys.version_info.major, sys.version_info.minor
        )
    )
