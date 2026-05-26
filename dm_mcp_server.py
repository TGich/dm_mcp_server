#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦数据库 MCP 服务器
遵循 FastMCP 规范实现，通过环境变量进行配置。
"""

import os
import re
import sys
import datetime
import logging
from typing import Dict, Any, List, Optional
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

LOG_LEVEL = os.environ.get("DAMENG_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dm-mcp-server")

mcp = FastMCP("Dameng-MCP")

READONLY_KEYWORDS = {"SELECT", "WITH", "EXPLAIN", "SHOW", "DESC", "DESCRIBE"}

DANGEROUS_PATTERNS = [
    re.compile(r";\s*\w", re.IGNORECASE),
    re.compile(r"--", re.IGNORECASE),
    re.compile(r"/\*", re.IGNORECASE),
    re.compile(r"\bEXEC(UTE)?\b", re.IGNORECASE),
    re.compile(r"\bCALL\b", re.IGNORECASE),
    re.compile(r"\b xp_", re.IGNORECASE),
    re.compile(r"\b sp_", re.IGNORECASE),
    re.compile(r"\bINJECTION\b", re.IGNORECASE),
]


def _parse_bool(val: str) -> bool:
    return val.strip().upper() in ("TRUE", "1", "YES", "ON")


def _parse_allowed_schemas() -> Optional[List[str]]:
    raw = os.environ.get("DAMENG_ALLOWED_SCHEMAS", "").strip()
    if not raw:
        return None
    schemas = [s.strip().upper() for s in raw.split(",") if s.strip()]
    return schemas if schemas else None


def get_config():
    config = {
        'host': os.environ.get("DAMENG_HOST"),
        'port': os.environ.get("DAMENG_PORT"),
        'user': os.environ.get("DAMENG_USER"),
        'password': os.environ.get("DAMENG_PASSWORD"),
        'schema': os.environ.get("DAMENG_SCHEMA"),
        'read_only': _parse_bool(os.environ.get("DAMENG_READ_ONLY", "false")),
        'allowed_schemas': _parse_allowed_schemas(),
    }
    if not all([config['host'], config['user'], config['password']]):
        return None

    try:
        config['port'] = int(config['port']) if config['port'] else 5236
    except (ValueError, TypeError):
        config['port'] = 5236

    if config['allowed_schemas'] and config['schema']:
        if config['schema'].upper() not in config['allowed_schemas']:
            logger.warning(
                "DAMENG_SCHEMA '%s' 不在 DAMENG_ALLOWED_SCHEMAS 列表中，已自动追加",
                config['schema'],
            )
            config['allowed_schemas'].append(config['schema'].upper())

    return config


DB_CONFIG = get_config()


def _resolve_schema(requested_schema: Optional[str]) -> Optional[str]:
    if not DB_CONFIG:
        return None
    default_schema = DB_CONFIG.get('schema')
    allowed = DB_CONFIG.get('allowed_schemas')

    if not requested_schema:
        return default_schema

    if not allowed:
        if requested_schema.upper() == default_schema.upper():
            return default_schema
        return None

    if requested_schema.upper() in allowed:
        return requested_schema
    return None


@contextmanager
def get_db_connection(schema: Optional[str] = None):
    if not DM_PYTHON_AVAILABLE:
        raise ImportError("缺少 dmPython 库，请先安装：pip install dmPython")
    if not DB_CONFIG:
        raise ValueError("数据库配置不完整，请设置 DAMENG_HOST/USER/PASSWORD 环境变量")

    target_schema = schema or DB_CONFIG.get('schema')

    conn = dmPython.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
    )
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SET CHAR_CODE UTF-8")
            if target_schema:
                cursor.execute(f"SET SCHEMA \"{target_schema}\"")
                logger.debug("会话已切换到 Schema: %s", target_schema)
        except Exception as e:
            logger.warning("初始化会话失败: %s", e)
        finally:
            cursor.close()
        yield conn
    finally:
        conn.close()


def resp(status: str, **kwargs):
    return {
        "status": status,
        "timestamp": datetime.datetime.now().isoformat(),
        **kwargs,
    }


def _validate_sql_security(sql: str, allowed_schemas: Optional[List[str]]) -> Optional[str]:
    sql_upper = sql.upper().strip()

    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(sql):
            msg = f"安全性限制：SQL 包含潜在的注入风险模式，已被拦截"
            logger.warning("SQL 安全拦截: %s | SQL: %.200s", msg, sql)
            return msg

    if "." in sql:
        tokens = re.findall(r'"([^"]+)"\.\w+|(\w+)\.\w+', sql)
        for quoted, unquoted in tokens:
            name = (quoted or unquoted).upper()
            if allowed_schemas:
                if name not in allowed_schemas:
                    return f"安全性限制：禁止跨SCHEMA操作，'{name}' 不在允许列表中"
            else:
                default = DB_CONFIG.get('schema', '').upper()
                if name != default:
                    return f"安全性限制：禁止跨SCHEMA操作。仅允许操作模式: {default}"

    owner_match = re.search(r"OWNER\s*[=<>]+\s*['\"](.+?)['\"]", sql_upper)
    if owner_match:
        found_owner = owner_match.group(1).strip()
        if allowed_schemas:
            if found_owner not in allowed_schemas:
                return f"安全性限制：禁止查询非允许SCHEMA ({', '.join(allowed_schemas)}) 的元数据"
        else:
            default = DB_CONFIG.get('schema', '').upper()
            if found_owner != default:
                return f"安全性限制：禁止查询非本SCHEMA ({default}) 的元数据"

    return None


def _check_read_only(sql: str) -> Optional[str]:
    if not DB_CONFIG or not DB_CONFIG.get('read_only'):
        return None
    sql_upper = sql.upper().strip()
    first_word = sql_upper.split()[0] if sql_upper.split() else ""
    if first_word not in READONLY_KEYWORDS:
        return f"只读模式已开启，仅允许查询操作（SELECT/WITH/EXPLAIN/SHOW/DESCRIBE），当前语句类型: {first_word}"
    return None


@mcp.tool()
def test_connection() -> Dict[str, Any]:
    """测试数据库连接状态"""
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")
    try:
        with get_db_connection():
            schema_info = DB_CONFIG.get('schema', '未指定')
            read_only = "是" if DB_CONFIG.get('read_only') else "否"
            allowed = DB_CONFIG.get('allowed_schemas')
            allowed_info = ', '.join(allowed) if allowed else schema_info
            return resp(
                "success",
                message="数据库连接成功",
                schema=schema_info,
                allowed_schemas=allowed_info,
                read_only=read_only,
            )
    except Exception as e:
        logger.error("数据库连接测试失败: %s", e)
        return resp("error", message=str(e))


@mcp.tool()
def execute_sql(
    sql: str,
    fetch_results: bool = True,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """执行 SQL 语句（强制限定配置下的SCHEMA操作）

    参数:
        sql: 要执行的 SQL 语句
        fetch_results: 是否返回查询结果（默认 True）
        limit: 限制返回的行数，用于分页（可选）
        offset: 跳过的行数，用于分页（可选）
    """
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    schema = DB_CONFIG.get('schema')
    if not schema:
        return resp("error", message="安全性错误：必须设置 DAMENG_SCHEMA 环境变量")

    read_only_err = _check_read_only(sql)
    if read_only_err:
        return resp("error", message=read_only_err)

    security_err = _validate_sql_security(sql, DB_CONFIG.get('allowed_schemas'))
    if security_err:
        return resp("error", message=security_err)

    sql_upper = sql.upper().strip()
    is_select = sql_upper.startswith(('SELECT', 'WITH'))

    if is_select and fetch_results and (limit is not None or offset is not None):
        effective_limit = limit if limit is not None else 1000
        effective_offset = offset if offset is not None else 0
        sql = f"SELECT * FROM ({sql}) LIMIT {effective_limit} OFFSET {effective_offset}"
        logger.info("分页查询: LIMIT=%d OFFSET=%d", effective_limit, effective_offset)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            if fetch_results and is_select:
                if limit is None and offset is None:
                    res = cursor.fetchall()
                else:
                    res = cursor.fetchall()
                cols = [d[0] for d in cursor.description] if cursor.description else []
                data = [dict(zip(cols, r)) for r in res]
                result = resp("success", data=data, count=len(data))
                if limit is not None or offset is not None:
                    result["pagination"] = {
                        "limit": limit,
                        "offset": offset,
                    }
                return result
            return resp("success", affected_rows=cursor.rowcount)
    except Exception as e:
        logger.error("SQL 执行失败: %s", e)
        return resp("error", message=str(e))


@mcp.tool()
def list_tables(schema: Optional[str] = None) -> Dict[str, Any]:
    """查询指定SCHEMA下的所有表，不指定则查询默认SCHEMA"""
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    target_schema = _resolve_schema(schema)
    if target_schema is None:
        allowed = DB_CONFIG.get('allowed_schemas') or [DB_CONFIG.get('schema', '')]
        return resp("error", message=f"安全性限制：禁止查询非允许SCHEMA的数据。允许的SCHEMA: {', '.join(allowed)}")

    try:
        with get_db_connection(schema=target_schema) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME")
            res = cursor.fetchall()
            tables = [r[0] for r in res]
            return resp("success", data=tables, count=len(tables), schema=target_schema)
    except Exception as e:
        logger.error("列出表失败: %s", e)
        return resp("error", message=str(e))


@mcp.tool()
def count_tables(schema: Optional[str] = None) -> Dict[str, Any]:
    """统计指定SCHEMA下的表数量，不指定则统计默认SCHEMA"""
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    target_schema = _resolve_schema(schema)
    if target_schema is None:
        allowed = DB_CONFIG.get('allowed_schemas') or [DB_CONFIG.get('schema', '')]
        return resp("error", message=f"安全性限制：禁止统计非允许SCHEMA的数据。允许的SCHEMA: {', '.join(allowed)}")

    try:
        with get_db_connection(schema=target_schema) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM USER_TABLES")
            res = cursor.fetchone()
            return resp("success", count=res[0] if res else 0, schema=target_schema)
    except Exception as e:
        logger.error("统计表数量失败: %s", e)
        return resp("error", message=str(e))


@mcp.tool()
def get_current_schema() -> Dict[str, Any]:
    """获取当前配置的数据库的SCHEMA及允许的SCHEMA列表"""
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")
    schema = DB_CONFIG.get('schema')
    if not schema:
        return resp("error", message="安全性错误：尚未配置SCHEMA")
    allowed = DB_CONFIG.get('allowed_schemas')
    return resp(
        "success",
        schema=schema,
        allowed_schemas=allowed if allowed else [schema],
        read_only=DB_CONFIG.get('read_only', False),
    )


@mcp.tool()
def switch_schema(schema: str) -> Dict[str, Any]:
    """切换当前操作的SCHEMA（仅在配置了DAMENG_ALLOWED_SCHEMAS时可用）"""
    if not DB_CONFIG:
        return resp("error", message="缺失环境变量配置")

    allowed = DB_CONFIG.get('allowed_schemas')
    if not allowed:
        return resp("error", message="未启用多SCHEMA模式。请设置 DAMENG_ALLOWED_SCHEMAS 环境变量以启用")

    if schema.upper() not in allowed:
        return resp("error", message=f"安全性限制：'{schema}' 不在允许的SCHEMA列表中。允许: {', '.join(allowed)}")

    DB_CONFIG['schema'] = schema
    logger.info("SCHEMA 已切换为: %s", schema)
    return resp("success", schema=schema, message=f"已切换到SCHEMA: {schema}")


def main():
    if not DB_CONFIG:
        logger.error("数据库配置缺失，请确保 DAMENG_HOST / DAMENG_USER / DAMENG_PASSWORD 环境变量已设置")
        return

    logger.info(
        "达梦 MCP 服务器启动 | Schema: %s | 只读: %s | 允许Schema: %s",
        DB_CONFIG.get('schema'),
        "是" if DB_CONFIG.get('read_only') else "否",
        ', '.join(DB_CONFIG['allowed_schemas']) if DB_CONFIG.get('allowed_schemas') else DB_CONFIG.get('schema'),
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
