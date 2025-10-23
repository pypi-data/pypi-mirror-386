#!/usr/bin/env python
# coding:utf-8
"""redis缓存
author：dqy
邮箱：yu12377@163.com
time：2020-06-28
"""
import os
import sys
import json
import sqlite3
from pathlib import Path
from redis import Redis, ConnectionPool

from . import logger
from .utils import byte_to_str, get_caller_info
from .encrypt import to_decode, sum_md5
from .file import read_file_content, save_json_to_file


def get_cache_obj(db_index: int = 15):
    """获取缓存对象
    :param db_index: int, redis中数据库索引编号
    """
    if os.environ.get("REDIS_DB_CONNECT"):
        try:
            _redis = MyRedis(db_index)
        except Exception as _e:
            pass
        else:
            logger.debug(f"redis缓存初始成功！")
            return _redis

    if sys.platform == "win32":
        _target_path = Path(os.environ["USERPROFILE"])
    else:
        _target_path = Path(os.environ["HOME"])
    __cache_path__ = _target_path / ".dbox_cache.db"
    logger.warning(f"redis缓存不可用，启动本地SQLite缓存：{__cache_path__}")
    return MyCache(__cache_path__)


def get_redis_pool(db_index=0, max_connections=None):
    """获取redis连接池
    :param db_index: int, redis中数据库索引编号
    :param max_connections: int, 最大连接数
    """
    redis_connect = os.environ.get("REDIS_DB_CONNECT")
    if not redis_connect:
        raise ValueError("REDIS_DB_CONNECT environment variable not set")
    _connect = json.loads(to_decode(redis_connect))
    return ConnectionPool(
        host=_connect["host"],
        port=_connect["port"],
        password=_connect["pass"],
        db=db_index,
        max_connections=max_connections,
    )


def get_redis_handler(db_index=0):
    """获取redis连接
    :param db_index: int, redis中数据库索引编号
    """
    try:
        redis_obj = Redis(connection_pool=get_redis_pool(db_index))
        if redis_obj.ping():
            return redis_obj
        else:
            return None
    except (ConnectionError, TimeoutError):
        return None


def batch_delete_key(db_index: int, name_expression: str):
    """批量删除redis key
    :param db_index: int, redis中数据库索引编号
    :param name_expression: str, key值通配符
    """
    redis = get_redis_handler(db_index)
    if redis is None:
        logger.warning("Redis connection failed, cannot delete keys")
        return
    temp_lock_list = redis.keys(name_expression)  # type: ignore
    if temp_lock_list:
        redis.delete(*list(temp_lock_list))  # type: ignore


class MyRedis(Redis):
    def __init__(self, db_index=0):
        super().__init__(connection_pool=get_redis_pool(db_index))

    def batch_delete(self, name_expression):
        key_list = self.keys(name_expression)  # type: ignore
        if key_list:
            self.delete(*list(key_list))  # type: ignore

    def get_to_json(self, name):
        if name:
            value_raw = self.get(name)  # type: ignore
            if value_raw:
                try:
                    if isinstance(value_raw, str):
                        user = json.loads(value_raw)
                    else:
                        user = json.loads(value_raw.decode("utf-8"))  # type: ignore
                except (TypeError, json.decoder.JSONDecodeError) as e:
                    self.delete(name)
                else:
                    return MyDict(**user)
        return None

    def set_obj(self, prefix: str, value, **kwargs):
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, ensure_ascii=False)
            key = prefix + sum_md5(value)
            self.set(key, value, **kwargs)
            return key
        else:
            raise TypeError("此方法只用于保存对象！")

    def push_obj(self, queue_name: str, value):
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, ensure_ascii=False)
            return self.rpush(queue_name, value)
        else:
            return self.rpush(queue_name, value)

    def pop_obj(self, queue_name: str):
        value = self.lpop(queue_name)  # type: ignore
        try:
            if value and isinstance(value, str):
                return json.loads(value)
            return value
        except Exception as e:
            return value

    def hgetall(self, name):
        _v = super(MyRedis, self).hgetall(name)  # type: ignore
        if isinstance(_v, dict):
            return {
                _k.decode("utf-8") if isinstance(_k, bytes) else _k: _v.decode("utf-8") if isinstance(_v, bytes) else _v
                for _k, _v in _v.items()
            }
        else:
            return _v

    def lpop(self, name, count=None):
        _k = super(MyRedis, self).lpop(name, count)  # type: ignore
        if _k:
            if isinstance(_k, bytes):
                return _k.decode("utf-8")
            return _k
        else:
            return _k

    def keys(self, pattern="*", **kwargs):
        _l = super(MyRedis, self).keys(pattern, **kwargs)  # type: ignore
        if _l:
            return [_i.decode("utf-8") if isinstance(_i, bytes) else _i for _i in _l]  # type: ignore
        else:
            return _l

    def get(self, name):
        _v = super(MyRedis, self).get(name)  # type: ignore
        if _v:
            if isinstance(_v, bytes):
                _v = _v.decode("utf-8")
        return _v

    def smembers(self, name):
        _l = super(MyRedis, self).smembers(name)  # type: ignore
        if _l:
            return set(_i.decode("utf-8") if isinstance(_i, bytes) else _i for _i in _l)  # type: ignore
        else:
            return _l


class MyCache:
    """自定义缓存类，redis不可用时替代使用，基于SQLite3实现，支持多进程安全"""

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self._init_db()

    def _init_db(self):
        """初始化SQLite数据库和表结构"""
        try:
            with sqlite3.connect(str(self.cache_path), timeout=30.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL")  # 启用WAL模式，提高并发性能
                conn.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
                conn.execute("PRAGMA busy_timeout=30000")  # 30秒超时

                # 创建缓存表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        expire_time REAL,
                        created_time REAL DEFAULT (julianday('now'))
                    )
                """)

                # 创建过期时间索引
                conn.execute("CREATE INDEX IF NOT EXISTS idx_expire_time ON cache(expire_time)")

                conn.commit()

        except sqlite3.Error as e:
            logger.error(f"初始化SQLite缓存数据库失败: {e}")
            raise

    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(str(self.cache_path), timeout=30.0)

    def _cleanup_expired(self):
        """清理过期的缓存项"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE expire_time IS NOT NULL AND expire_time < julianday('now')"
                )
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.debug(f"清理了 {cursor.rowcount} 个过期缓存项")
        except sqlite3.Error as e:
            logger.warning(f"清理过期缓存时出错: {e}")

    def exists(self, key: str):
        """检查键是否存在（且未过期）"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 1 FROM cache
                    WHERE key = ? AND (expire_time IS NULL OR expire_time > julianday('now'))
                """, (key,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.warning(f"检查键存在性时出错: {e}")
            return False

    def get(self, key: str):
        """获取缓存值"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT value FROM cache
                    WHERE key = ? AND (expire_time IS NULL OR expire_time > julianday('now'))
                """, (key,))
                row = cursor.fetchone()
                if row:
                    try:
                        return json.loads(row[0])
                    except json.JSONDecodeError:
                        return row[0]  # 如果不是JSON格式，直接返回字符串
                return None
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.warning(f"获取缓存值时出错: {e}")
            return None

    def set(self, key: str, value):
        """设置缓存值"""
        try:
            with self._get_connection() as conn:
                # 将value序列化为JSON字符串
                if isinstance(value, (dict, list, tuple)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = json.dumps(value, ensure_ascii=False) if isinstance(value, (str, bool)) else str(value)

                conn.execute("""
                    INSERT OR REPLACE INTO cache (key, value, expire_time)
                    VALUES (?, ?, NULL)
                """, (key, value_str))
                conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"设置缓存值时出错: {e}")

    def delete(self, key: str):
        """删除缓存项"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.warning(f"删除缓存项时出错: {e}")
            return False

    def setex(self, name, expire_seconds, value):
        """设置带过期时间的缓存值"""
        try:
            with self._get_connection() as conn:
                # 使用SQLite的julianday函数计算过期时间
                cursor = conn.execute("SELECT julianday('now')")
                current_julianday = cursor.fetchone()[0]
                expire_days = expire_seconds / 86400.0  # 秒转换为天
                expire_time = current_julianday + expire_days  # 当前朱利安日 + 过期天数

                # 将value序列化为JSON字符串
                if isinstance(value, (dict, list, tuple)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = json.dumps(value, ensure_ascii=False) if isinstance(value, (str, bool)) else str(value)

                conn.execute("""
                    INSERT OR REPLACE INTO cache (key, value, expire_time)
                    VALUES (?, ?, ?)
                """, (name, value_str, expire_time))
                conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"设置带过期时间的缓存值时出错: {e}")

    def hmset(self, name, mapping):
        """设置哈希映射"""
        self.set(name, mapping)

    def hgetall(self, key: str):
        """获取哈希所有值"""
        value = self.get(key)
        if isinstance(value, dict):
            return value
        elif value is not None:
            logger.warning(f"hgetall: {key} 不是字典类型: {type(value)}")
        return {}

    def hset(self, name, key=None, value=None, mapping=None):
        """设置哈希字段"""
        if key is None and not mapping:
            raise ValueError("'key'或'mapping'不能同时为空")

        # 获取现有的哈希数据
        existing_data = self.get(name) or {}

        items = dict()
        if key is not None:
            items[key] = value
        if mapping:
            items.update(mapping)

        # 合并到现有数据
        existing_data.update(items)
        self.set(name, existing_data)

    def batch_delete(self, name_expression):
        """批量删除匹配模式的键"""
        key_list = self.keys(name_expression)
        if key_list:
            for key in key_list:
                self.delete(key)

    def get_to_json(self, name):
        """获取JSON值并返回MyDict对象"""
        if name:
            value_raw = self.get(name)
            if value_raw:
                try:
                    if isinstance(value_raw, dict):
                        return MyDict(**value_raw)
                    elif isinstance(value_raw, str):
                        user = json.loads(value_raw)
                        return MyDict(**user)
                except (TypeError, json.JSONDecodeError) as e:
                    self.delete(name)
        return None

    def set_obj(self, prefix: str, value, **kwargs):
        """设置对象并返回生成的键名"""
        if isinstance(value, (dict, list, tuple)):
            value_str = json.dumps(value, ensure_ascii=False)
            key = prefix + sum_md5(value_str)
            self.set(key, value_str)
            return key
        else:
            raise TypeError("此方法只用于保存对象！")

    def push_obj(self, queue_name: str, value):
        """推送对象到队列（简单实现）"""
        if isinstance(value, (dict, list, tuple)):
            value_str = json.dumps(value, ensure_ascii=False)
            # 使用简单的列表追加方式模拟队列
            current_queue = self.get(queue_name) or []
            current_queue.append(value_str)
            self.set(queue_name, current_queue)
            return len(current_queue)
        else:
            # 原始值
            current_queue = self.get(queue_name) or []
            current_queue.append(str(value))
            self.set(queue_name, current_queue)
            return len(current_queue)

    def pop_obj(self, queue_name: str):
        """从队列弹出对象（简单实现）"""
        current_queue = self.get(queue_name) or []
        if current_queue:
            value_str = current_queue.pop(0)
            self.set(queue_name, current_queue)
            try:
                return json.loads(value_str)
            except (json.JSONDecodeError, TypeError):
                return value_str
        return None

    def rpush(self, name, *values):
        """右推入队列（兼容Redis接口）"""
        queue = self.get(name) or []
        for value in values:
            if isinstance(value, (dict, list, tuple)):
                queue.append(json.dumps(value, ensure_ascii=False))
            else:
                queue.append(str(value))
        self.set(name, queue)
        return len(queue)

    def lpop(self, name, count=None):
        """左弹出队列（兼容Redis接口）"""
        queue = self.get(name) or []
        if not queue:
            return None

        if count is None:
            # 单个值
            value = queue.pop(0)
            self.set(name, queue)
            try:
                return json.loads(value) if isinstance(value, str) else value
            except (json.JSONDecodeError, TypeError):
                return value
        else:
            # 多个值
            count = min(count, len(queue))
            values = queue[:count]
            remaining = queue[count:]
            self.set(name, remaining)

            # 尝试解析JSON
            result = []
            for value in values:
                try:
                    result.append(json.loads(value) if isinstance(value, str) else value)
                except (json.JSONDecodeError, TypeError):
                    result.append(value)
            return result

    def smembers(self, name):
        """获取集合成员（简单实现）"""
        members = self.get(name)
        if members:
            if isinstance(members, set):
                return members
            elif isinstance(members, list):
                return set(members)
            elif isinstance(members, (str, int, float)):
                return {str(members)}
        return set()

    def keys(self, pattern="*"):
        """获取匹配模式的所有键（支持简单的通配符匹配）"""
        try:
            with self._get_connection() as conn:
                if pattern == "*":
                    cursor = conn.execute("""
                        SELECT key FROM cache
                        WHERE expire_time IS NULL OR expire_time > julianday('now')
                    """)
                else:
                    # 简单的通配符匹配
                    like_pattern = pattern.replace('*', '%')
                    cursor = conn.execute("""
                        SELECT key FROM cache
                        WHERE key LIKE ? AND (expire_time IS NULL OR expire_time > julianday('now'))
                    """, (like_pattern,))

                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.warning(f"获取键列表时出错: {e}")
            return []

    def clear(self):
        """清空所有缓存"""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"清空缓存时出错: {e}")

    def info(self):
        """获取缓存信息"""
        try:
            with self._get_connection() as conn:
                # 总键数
                total_cursor = conn.execute("SELECT COUNT(*) FROM cache")
                total_count = total_cursor.fetchone()[0]

                # 过期键数
                expired_cursor = conn.execute("""
                    SELECT COUNT(*) FROM cache
                    WHERE expire_time IS NOT NULL AND expire_time < julianday('now')
                """)
                expired_count = expired_cursor.fetchone()[0]

                # 有效键数
                active_count = total_count - expired_count

                return {
                    'total_keys': total_count,
                    'expired_keys': expired_count,
                    'active_keys': active_count,
                    'cache_file': str(self.cache_path)
                }
        except sqlite3.Error as e:
            logger.warning(f"获取缓存信息时出错: {e}")
            return {}

    def __getattr__(self, item):
        logger.warning(f"SQLite缓存类没有实现{item}方法，忽略")

        def __temp_func(*args, **kwargs):
            pass

        return __temp_func


class MyDict(dict):
    """自定义的字典类"""

    def __init__(self, *args, **kwargs):
        super(MyDict, self).__init__(*args, **kwargs)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __setattr__(self, key, value):
        self[key] = value


def hget(name, key, default=None, _type=None, db_index=1):
    if _type not in (None, int, float, str, bool, bytes):
        raise TypeError("_type只能是None,int,float,str,bool,bytes之一")

    redis_obj = MyRedis(db_index)
    value = redis_obj.hget(name, key)

    if value is None:
        return default

    if value and _type == bytes:
        return value

    value = byte_to_str(value)
    if _type:
        if _type == bool:
            if str(value).lower() in ("1", "true", "yes"):
                return True
            else:
                return False
        else:
            return _type(value)
    return value
