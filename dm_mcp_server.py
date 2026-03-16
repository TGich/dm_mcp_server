#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦数据库 MCP 服务器
遵循 FastMCP 规范实现，通过环境变量进行配置。
"""

import os
import sys
import datetime
import logging
from typing import Dict, Any, List
from contextlib import contextmanager
from mcp.server.fastmcp import FastMCP

# 环境与编码设置
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')

# 设置标准输出编码（针对 Windows 环境）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 达梦驱动导入
try:
    import dmPython
    DM_PYTHON_AVAILABLE = True
except ImportError:
    DM_PYTHON_AVAILABLE = False

# 极简日志配置
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 初始化 FastMCP
mcp = FastMCP("Dameng-MCP")

def get_config():
    """从环境变量获取数据库配置"""
    config = {
        'host': os.environ.get("DAMENG_HOST"),
        'port': os.environ.get("DAMENG_PORT"),
        'user': os.environ.get("DAMENG_USER"),
        'password': os.environ.get("DAMENG_PASSWORD"),
        'schema': os.environ.get("DAMENG_SCHEMA")
    }
    # 核心参数缺失则返回 None
    if not all([config['host'], config['user'], config['password']]):
        return None
    
    try:
        config['port'] = int(config['port']) if config['port'] else 5236
    except (ValueError, TypeError):
        config['port'] = 5236
    return config

# 全局配置对象
DB_CONFIG = get_config()

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    if not DM_PYTHON_AVAILABLE:
        raise ImportError("缺少 dmPython 库，请先安装：pip install dmPython")
    if not DB_CONFIG:
        raise ValueError("数据库配置不完整，请设置 DAMENG_HOST/USER/PASSWORD 环境变量")
    
    conn = dmPython.connect(
        host=DB_CONFIG['host'], 
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'], 
        password=DB_CONFIG['password']
    )
    try:
        cursor = conn.cursor()
        try:
            # 强化编码设置与 Schema 切换
            cursor.execute("SET CHAR_CODE UTF-8")
            if DB_CONFIG.get('schema'):
                cursor.execute(f"SET SCHEMA \"{DB_CONFIG['schema']}\"")
        except Exception as e:
            logger.warning(f"初始化会话失败: {e}")
        finally:
            cursor.close()
        yield conn
    finally:
        conn.close()

def resp(status: str, **kwargs):
    """统一响应格式"""
    return {
        "status": status, 
        "timestamp": datetime.datetime.now().isoformat(), 
        **kwargs
    }

@mcp.tool()
def test_connection() -> Dict[str, Any]:
    """测试数据库连接状态"""
    if not DB_CONFIG: return resp("error", message="缺失环境变量配置")
    try:
        with get_db_connection(): return resp("success", message="数据库连接成功")
    except Exception as e: return resp("error", message=str(e))

@mcp.tool()
def execute_sql(sql: str, fetch_results: bool = True) -> Dict[str, Any]:
    """执行 SQL 语句（强制限定配置下的SCHEMA操作）"""
    if not DB_CONFIG: return resp("error", message="缺失环境变量配置")
    schema = DB_CONFIG.get('schema')
    if not schema: return resp("error", message="安全性错误：必须设置 DAMENG_SCHEMA 环境变量")
    
    # 深度安全性审核
    sql_upper = sql.upper()
    
    # 1. 检测是否显式引用了其他模式名
    # 我们认为任何不等于当前模式名的标识符出现在点号前，或出现在 OWNER = 'xxx' 中都是威胁
    # 简单而严格的检查：如果 SQL 中包含了任何其他模式的 OWNER 过滤或点号引用，则拦截
    if "." in sql:
        valid_prefix = f"{schema.upper()}."
        valid_prefix_quoted = f"\"{schema.upper()}\"."
        # 允许不带前缀，但如果带了前缀，必须是当前 schema
        for word in sql_upper.split():
            if "." in word and not (word.startswith(valid_prefix) or word.startswith(valid_prefix_quoted)):
                return resp("error", message=f"安全性限制：禁止跨SCHEMA操作。仅允许操作模式: {schema}")

    # 2. 拦截对 ALL_TABLES/ALL_OBJECTS 等视图中非本SCHEMA的过滤尝试
    # 检查是否存在 OWNER = '非本SCHEMA' 的情况
    import re
    owner_match = re.search(r"OWNER\s*[=<>]+\s*['\"](.+?)['\"]", sql_upper)
    if owner_match:
        found_owner = owner_match.group(1).strip()
        if found_owner != schema.upper():
            return resp("error", message=f"安全性限制：禁止查询非本SCHEMA ({schema}) 的元数据")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SET SCHEMA \"{schema}\"")
            cursor.execute(sql)
            if fetch_results and sql_upper.strip().startswith('SELECT'):
                res = cursor.fetchall()
                cols = [d[0] for d in cursor.description] if cursor.description else []
                data = [dict(zip(cols, r)) for r in res]
                return resp("success", data=data, count=len(data))
            return resp("success", affected_rows=cursor.rowcount)
    except Exception as e: return resp("error", message=str(e))

@mcp.tool()
def list_tables(schema: str = None) -> Dict[str, Any]:
    """只能查询配置SCHEMA下的所有表，不能查询其他SCHEMA的表"""  
    if not DB_CONFIG: return resp("error", message="缺失环境变量配置")
    target_schema = DB_CONFIG.get('schema')
    if not target_schema: return resp("error", message="安全性错误：必须设置 DAMENG_SCHEMA 环境变量")
    
    # 显式校验：如果传入了模式名，必须与配置一致
    if schema and schema.upper() != target_schema.upper():
        return resp("error", message=f"安全性限制：禁止查询非配置SCHEMA ({target_schema}) 的数据")
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SET SCHEMA \"{target_schema}\"")
            cursor.execute("SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME")
            res = cursor.fetchall()
            tables = [r[0] for r in res]
            return resp("success", data=tables, count=len(tables))
    except Exception as e: return resp("error", message=str(e))

@mcp.tool()
def count_tables(schema: str = None) -> Dict[str, Any]:
    """只能统计配置SCHEMA下的表数量，不能统计其他SCHEMA的表数量"""
    if not DB_CONFIG: return resp("error", message="缺失环境变量配置")
    target_schema = DB_CONFIG.get('schema')
    if not target_schema: return resp("error", message="安全性错误：必须设置 DAMENG_SCHEMA 环境变量")
    
    # 显式校验：如果传入了模式名，必须与配置一致
    if schema and schema.upper() != target_schema.upper():
        return resp("error", message=f"安全性限制：禁止统计非配置SCHEMA ({target_schema}) 的数据")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SET SCHEMA \"{target_schema}\"")
            cursor.execute("SELECT COUNT(*) FROM USER_TABLES")
            res = cursor.fetchone()
            return resp("success", count=res[0] if res else 0)
    except Exception as e: return resp("error", message=str(e))

@mcp.tool()
def get_current_schema() -> Dict[str, Any]:
    """获取当前配置的数据库的SCHEMA"""
    if not DB_CONFIG: return resp("error", message="缺失环境变量配置")
    schema = DB_CONFIG.get('schema')
    if not schema: return resp("error", message="安全性错误：尚未配置SCHEMA")
    return resp("success", schema=schema)

def main():
    """服务器入口函数"""
    if not DB_CONFIG:
        logger.error("!!! 请确保在启动前通过环境变量进行注入。")
    
    # 启动 MCP 服务器
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()