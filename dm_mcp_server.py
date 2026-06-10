#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import logging
import socket
import threading
import re
from typing import Dict, Any
from contextlib import contextmanager
from mcp.server.fastmcp import FastMCP

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import dmPython
    DM_PYTHON_AVAILABLE = True
except ImportError:
    DM_PYTHON_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

mcp = FastMCP("Dameng-MCP")
DB_OP_LOCK = threading.RLock()


def load_local_env() -> None:
    """Load key=value pairs from .env files without overriding existing env vars."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        os.path.join(base_dir, ".env"),
        os.path.join(base_dir, ".env.test"),
    ]

    for env_path in env_paths:
        if not os.path.exists(env_path):
            continue

        try:
            with open(env_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
        except OSError:
            continue

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_local_env()


def get_config() -> Dict[str, Any] | None:
    config = {
        'host': os.environ.get("DAMENG_HOST"),
        'port': os.environ.get("DAMENG_PORT"),
        'user': os.environ.get("DAMENG_USER"),
        'password': os.environ.get("DAMENG_PASSWORD"),
        'schema': os.environ.get("DAMENG_SCHEMA"),
    }
    if not all([config['host'], config['user'], config['password']]):
        return None

    try:
        config['port'] = int(config['port']) if config['port'] else 5236
    except (ValueError, TypeError):
        config['port'] = 5236
    return config


DB_CONFIG = get_config()


def err_msg(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"


def resp(status: str, **kwargs):
    return {
        "status": status,
        "timestamp": datetime.datetime.now().isoformat(),
        **kwargs,
    }


@contextmanager
def get_db_connection():
    if not DM_PYTHON_AVAILABLE:
        raise ImportError("缺少 dmPython 库，请先安装：pip install dmPython")
    if not DB_CONFIG:
        raise ValueError("数据库配置不完整，请设置 DAMENG_HOST/USER/PASSWORD 环境变量")

    with DB_OP_LOCK:
        host = DB_CONFIG['host']
        port = DB_CONFIG['port']
        user = DB_CONFIG['user']
        schema = DB_CONFIG.get('schema')

        try:
            with socket.create_connection((host, port), timeout=3):
                pass
        except OSError as e:
            raise ConnectionError(f"TCP reachability check failed: {host}:{port} ({e})") from e

        try:
            conn = dmPython.connect(
                host=host,
                port=port,
                user=user,
                password=DB_CONFIG['password'],
            )
        except Exception as e:
            raise ConnectionError(
                f"dmPython.connect failed for user={user}, host={host}, port={port}, schema={schema}: {e!r}"
            ) from e

        try:
            cursor = conn.cursor()
            try:
                if schema:
                    cursor.execute(f'SET SCHEMA "{schema}"')
            except Exception as e:
                logger.warning(f"初始化会话失败: {e}")
            finally:
                cursor.close()
            yield conn
        finally:
            conn.close()


@mcp.tool()
def test_connection() -> Dict[str, Any]:
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")
    try:
        with get_db_connection():
            return resp("success", message="数据库连接成功")
    except Exception as e:
        logger.exception("test_connection failed")
        return resp("error", message=err_msg(e))


@mcp.tool()
def execute_sql(sql: str, fetch_results: bool = True) -> Dict[str, Any]:
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    schema = DB_CONFIG.get('schema')
    if not schema:
        return resp("error", message="安全性错误：必须设置 DAMENG_SCHEMA 环境变量")

    sql_upper = sql.upper()

    if "." in sql:
        valid_prefix = f"{schema.upper()}."
        valid_prefix_quoted = f'"{schema.upper()}".'
        for word in sql_upper.split():
            if "." in word and not (word.startswith(valid_prefix) or word.startswith(valid_prefix_quoted)):
                return resp("error", message=f"安全性限制：禁止跨SCHEMA操作。仅允许操作模式: {schema}")

    owner_match = re.search(r"OWNER\s*[=<>]+\s*['\"](.+?)['\"]", sql_upper)
    if owner_match:
        found_owner = owner_match.group(1).strip()
        if found_owner != schema.upper():
            return resp("error", message=f"安全性限制：禁止查询非本SCHEMA ({schema}) 的元数据")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SET SCHEMA "{schema}"')
            cursor.execute(sql)
            if fetch_results and sql_upper.strip().startswith('SELECT'):
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description] if cursor.description else []
                data = [dict(zip(cols, r)) for r in rows]
                return resp("success", data=data, count=len(data))
            return resp("success", affected_rows=cursor.rowcount)
    except Exception as e:
        logger.exception("execute_sql failed")
        return resp("error", message=err_msg(e))


@mcp.tool()
def list_tables(schema: str = None) -> Dict[str, Any]:
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    target_schema = DB_CONFIG.get('schema')
    if not target_schema:
        return resp("error", message="安全性错误：必须设置 DAMENG_SCHEMA 环境变量")

    if schema and schema.upper() != target_schema.upper():
        return resp("error", message=f"安全性限制：禁止查询非配置SCHEMA ({target_schema}) 的数据")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT TABLE_NAME FROM DBA_TABLES WHERE OWNER = '{target_schema}' ORDER BY TABLE_NAME")
            rows = cursor.fetchall()
            tables = [r[0] for r in rows]
            return resp("success", data=tables, count=len(tables))
    except Exception as e:
        logger.exception("list_tables failed")
        return resp("error", message=err_msg(e))


@mcp.tool()
def count_tables(schema: str = None) -> Dict[str, Any]:
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    target_schema = DB_CONFIG.get('schema')
    if not target_schema:
        return resp("error", message="安全性错误：必须设置 DAMENG_SCHEMA 环境变量")

    if schema and schema.upper() != target_schema.upper():
        return resp("error", message=f"安全性限制：禁止统计非配置SCHEMA ({target_schema}) 的数据")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM DBA_TABLES WHERE OWNER = '{target_schema}'")
            row = cursor.fetchone()
            return resp("success", count=row[0] if row else 0)
    except Exception as e:
        logger.exception("count_tables failed")
        return resp("error", message=err_msg(e))


@mcp.tool()
def get_current_schema() -> Dict[str, Any]:
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    schema = DB_CONFIG.get('schema')
    if not schema:
        return resp("error", message="安全性错误：尚未配置SCHEMA")
    return resp("success", schema=schema)


def main():
    if not DB_CONFIG:
        logger.error("!!! 缺少数据库配置，请设置环境变量或在项目目录提供 .env 文件。")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
