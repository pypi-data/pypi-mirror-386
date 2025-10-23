import os
import sys
import json
import time
import ctypes
import logging
from pathlib import Path
from urllib.parse import urlparse
from .utils import execute_cmd, byte_to_str, bytes_to_str, ExecuteCMDException


logger = logging.getLogger("DBox")


def get_system_info(win_rm_session=None) -> dict:
    """获取系统信息"""
    # 本地缓存路径
    __system_path = Path(os.environ.get("TEMP") or os.environ.get("HOME") or ".") / "system_info.json"
    # 本地时优化检查缓存，远程不存在缓存一说
    if not win_rm_session:
        _system_info: dict
        if __system_path.exists():
            with open(__system_path, encoding="utf-8") as _file:
                try:
                    _system_info = json.load(_file)
                except Exception as e:
                    logger.exception(e)
                    logger.warning(f"读取缓存出错，重新计算：{str(e)}")
                else:
                    for _key, _value in _system_info.items():
                        if not _value:
                            logger.warning(f"缓存信息不完整，重新计算：{_system_info}")
                            break
                    else:
                        timestamp = _system_info.pop("timestamp")
                        if int(time.time()) - timestamp <= 1 * 24 * 60 * 60:
                            logger.debug(
                                f"系统信息缓存未过期：{json.dumps(_system_info, ensure_ascii=False, indent=4)}"
                            )
                            return _system_info
                        else:
                            logger.info(f"缓存过期，重新获取")

    # 实时获取系统信息
    systems = {
        "host_name": "",
        "os_name": "",
        "os_version": "",
        "os_arch": "",
        "ip_address": "",
        "mac_address": "",
    }
    try:
        if win_rm_session:
            res = win_rm_session.run_cmd("systemInfo")
            system_info = bytes_to_str(res.std_out)
        else:
            res = execute_cmd(["systemInfo"], encoding="", level="")
            if res is None:
                system_info = ""
            else:
                system_info = bytes_to_str(res.stdout)
        for line in system_info.split("\n"):
            line = line.strip()
            if line.startswith("主机名:") or line.startswith("主機名稱:") or line.startswith("Host Name:"):
                systems["host_name"] = line.split(":")[-1].strip()
            elif line.startswith("OS 名称:") or line.startswith("作業系統名稱:") or line.startswith("OS Name:"):
                systems["os_name"] = line.split(":")[-1].strip()
            elif line.startswith("OS 版本:") or line.startswith("作業系統版本:") or line.startswith("OS Version:"):
                systems["os_version"] = line.split(":")[-1].strip()
            elif line.startswith("系统类型:") or line.startswith("系統類型:") or line.startswith("System Type:"):
                systems["os_arch"] = line.split(":")[-1].strip()
        try:
            from . import net as net_utils
        except ImportError:
            import net as net_utils
        if win_rm_session:
            systems["ip_address"] = urlparse(win_rm_session.url).netloc.split(":")[0]
        else:
            systems["ip_address"] = net_utils.get_host_ip()
        systems["mac_address"] = get_mac_address(systems["ip_address"], win_rm_session)
        logger.info(f"当前机器系统信息：{json.dumps(systems, ensure_ascii=False, indent=4)}")
        if not win_rm_session:
            with open(__system_path, mode="w", encoding="utf-8") as _file:
                _temp = systems.copy()
                _temp["timestamp"] = str(int(time.time()))
                json.dump(_temp, _file, ensure_ascii=False, indent=4)
        return systems
    except Exception as e:
        logger.exception(e)
        return systems


def get_mac_address(ip_address: str, win_rm_session=None) -> str:
    """根据IP地址获取网卡MAC地址，兼容中文简体、中文繁体、英文
    :param ip_address: str, 目标网卡对应的IP地址
    :param win_rm_session: Windows 远程管理服务会话对象
    """
    mac_address: str = ""
    try:
        if win_rm_session:
            res = win_rm_session.run_cmd("ipconfig /all")
            network_info = bytes_to_str(res.std_out)
        else:
            res = execute_cmd(["ipconfig", "/all"], encoding="", level="")
            if res is None:
                network_info = ""
            else:
                network_info = bytes_to_str(res.stdout)
        for _line in network_info.split("\n"):
            _line = _line.strip()
            if _line:
                if _line.startswith("Physical Address") or _line.startswith("物理地址") or _line.startswith("實體位址"):
                    mac_address = _line.split(":")[-1].strip()
                elif _line.startswith("IPv4 Address") or _line.startswith("IPv4 地址") or _line.startswith("IPv4 位址"):
                    if ip_address in _line:
                        return mac_address
            else:
                # 切换网卡、重置mac
                mac_address = ""
    except Exception as e:
        logger.exception(e)

    return ""


def is_running_as_admin() -> bool:
    """检查当前是否以管理员权限运行"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


def get_current_app_list(detail=False, win_rm_session=None, timeout: int = 60) -> list:
    """获取当前用户实时app列表"""
    cmd_text = 'tasklist /nh /fo csv /fi "SESSION ne 0"'
    if detail:
        cmd_text += " /v"

    if win_rm_session:
        _res = win_rm_session.run_cmd(cmd_text, timeout=timeout)
        out_decode = bytes_to_str(_res.std_out)
    else:
        _res = execute_cmd(cmd_text, encoding="", level="", timeout=timeout)
        if _res is None:
            out_decode = ""
        else:
            out_decode = bytes_to_str(_res.stdout)

    _app_list = []
    for _line in out_decode.strip().split("\n"):
        _app_info = _line.strip().strip('"').split('","')
        if _app_info:
            try:
                _app = {
                    "name": _app_info[0],
                    "pid": _app_info[1],
                    "session_name": _app_info[2],
                    "session_id": _app_info[3],
                    "mem": _app_info[4],
                }
                if detail:
                    _app["status"] = _app_info[5]
                    _app["username"] = _app_info[6]
                    _app["cpu_time"] = _app_info[7]
                    _app["window_title"] = _app_info[8]
            except Exception as e:
                logger.exception(e)
                logger.error(_line)
            else:
                _app_list.append(_app)
    return _app_list


def kill_pid(pid: int, force: bool = False, timeout: int = 60):
    """kill指定进程"""
    cmd_text = f"taskkill /pid {pid} /t"
    if force:
        cmd_text += " /F"
    try:
        _res = execute_cmd(cmd_text, encoding="GBK", timeout=timeout)
    except ExecuteCMDException as _e:
        if "没有找到进程" in str(_e):
            pass
        else:
            logger.error(_e)


def kill_process(name: str, force: bool = False, timeout: int = 60):
    """kill指定进程"""
    cmd_text = f"taskkill /im {name} /t"
    if force:
        cmd_text += " /F"
    try:
        _res = execute_cmd(cmd_text, encoding="GBK", timeout=timeout)
    except ExecuteCMDException as _e:
        if "没有找到进程" in str(_e):
            pass
        else:
            logger.error(_e)


def get_exe_name_by_pid(pid: int) -> str:
    """通过进程PID获取EXE名称"""
    _cmd = f'tasklist /nh /V /fi "PID eq {pid}"'
    try:
        _res = os.popen(_cmd)
        _info = _res.read()
        _list = _info.split()
        if int(_list[1]) == int(pid):
            return _list[0]
    except Exception as _e:
        logger.exception(_e)
        logger.error(f"执行cmd命令出错：{_cmd}")
    return ""


def is_32_python_on_window() -> bool:
    """判断当前是否为32位的Python"""
    return "32 bit" in sys.version
