#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦数据库 MCP 服务器
提供完整的达梦数据库操作功能

Author: AI Assistant
Version: 2.1.0
"""

# ==================== 依赖检查和导入 ====================

# 第三方库导入
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("错误: 缺少 mcp 包，请运行: pip install mcp")
    exit(1)

try:
    import dmPython
    DM_PYTHON_AVAILABLE = True
except ImportError:
    DM_PYTHON_AVAILABLE = False
    print("警告: 缺少 dmPython 包，部分功能可能不可用。请运行: pip install dmPython")

# 标准库导入
from typing import List, Dict, Any, Optional
import json
import datetime
import logging
from contextlib import contextmanager

# ==================== 配置和初始化 ====================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 只使用控制台输出，避免文件日志
    ]
)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
try:
    mcp = FastMCP("达梦数据库 MCP服务器")
    logger.info("MCP服务器实例创建成功")
except Exception as e:
    logger.error(f"MCP服务器实例创建失败: {e}")
    raise

# 全局变量
DB_CONFIG: Optional[Dict[str, Any]] = None
query_history: List[Dict[str, Any]] = []
operation_history: List[Dict[str, Any]] = []

# ==================== 核心工具函数 ====================

@contextmanager
def get_db_connection(host: Optional[str] = None, port: Optional[int] = None, 
                     user: Optional[str] = None, password: Optional[str] = None):
    """获取数据库连接的上下文管理器"""
    if not DM_PYTHON_AVAILABLE:
        raise ImportError("dmPython 不可用，请安装 dmPython 包")
    
    connection = None
    try:
        if DB_CONFIG:
            connection = dmPython.connect(**DB_CONFIG)
        else:
            config = {
                'host': host or 'localhost',
                'port': port or 5236,
                'user': user or 'SYSDBA',
                'password': password or ''
            }
            # 注意：dmPython可能不支持charset等参数，只使用基本参数
            connection = dmPython.connect(**config)
        yield connection
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        raise
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass


def log_operation(operation_type: str, details: Dict[str, Any], success: bool = True) -> None:
    """记录操作历史"""
    operation_record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "operation_type": operation_type,
        "details": details,
        "success": success
    }
    operation_history.append(operation_record)
    logger.info(f"操作记录: {operation_type} - {'成功' if success else '失败'}")


def check_connection() -> Optional[Dict[str, Any]]:
    """检查数据库连接状态"""
    if not DB_CONFIG:
        return {
            "status": "error",
            "message": "未连接到数据库，请先使用 connect_database 工具连接",
            "timestamp": datetime.datetime.now().isoformat()
        }
    return None



# ==================== 数据库连接管理工具 ====================

@mcp.tool()
def connect_database(host: str = "localhost", port: int = 5236, 
                    user: str = "SYSDBA", password: str = "") -> Dict[str, Any]:
    """
    连接到达梦数据库
    
    Args:
        host: 数据库主机地址
        port: 数据库端口
        user: 数据库用户名
        password: 数据库密码
    
    Returns:
        连接结果
    """
    global DB_CONFIG
    try:
        # 设置全局配置
        DB_CONFIG = {
            'host': host,
            'port': port,
            'user': user,
            'password': password
        }
        # 注意：dmPython可能不支持charset等参数，只使用基本参数
        
        # 测试连接
        with get_db_connection(host, port, user, password) as conn:
            cursor = conn.cursor()
            # 设置会话字符集
            try:
                cursor.execute("SET CHAR_CODE UTF-8")
            except Exception:
                pass  # 忽略字符集设置错误
            
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
            
            result = {
                "status": "success",
                "message": "数据库连接成功",
                "host": host,
                "port": port,
                "user": user,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("connect_database", result)
            return result
            
    except Exception as e:
        DB_CONFIG = None
        error_result = {
            "status": "error",
            "message": f"数据库连接失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("connect_database", error_result, success=False)
        return error_result


@mcp.tool()
def disconnect_database() -> Dict[str, Any]:
    """
    断开数据库连接
    
    Returns:
        断开结果
    """
    global DB_CONFIG
    try:
        DB_CONFIG = None
        result = {
            "status": "success",
            "message": "数据库连接已断开",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("disconnect_database", result)
        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"断开连接失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("disconnect_database", error_result, success=False)
        return error_result


@mcp.tool()
def test_connection() -> Dict[str, Any]:
    """
    测试数据库连接
    
    Returns:
        连接测试结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
            
            result = {
                "status": "success",
                "message": "数据库连接正常",
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "user": DB_CONFIG['user'],
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("test_connection", result)
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"数据库连接失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("test_connection", error_result, success=False)
        return error_result



# ==================== 核心工具（简化版） ====================

# ==================== 高级查询工具 ====================

@mcp.tool()
def execute_sql(sql: str, fetch_results: bool = True) -> Dict[str, Any]:
    """
    执行自定义SQL语句
    
    Args:
        sql: SQL语句
        fetch_results: 是否获取结果集
    
    Returns:
        执行结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(sql)
            
            if fetch_results and sql.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # 格式化结果
                formatted_results = []
                for row in results:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(column_names):
                            row_dict[column_names[i]] = value
                    formatted_results.append(row_dict)
                
                result = {
                    "status": "success",
                    "data": formatted_results,
                    "count": len(results),
                    "sql": sql,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            else:
                affected_rows = cursor.rowcount
                result = {
                    "status": "success",
                    "message": "SQL执行成功",
                    "affected_rows": affected_rows,
                    "sql": sql,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            cursor.close()
            
            # 记录查询历史
            query_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "sql": sql,
                "result_count": result.get("count", 0)
            }
            query_history.append(query_record)
            
            log_operation("execute_sql", {"sql": sql[:100] + "..." if len(sql) > 100 else sql})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"SQL执行失败: {str(e)}",
            "sql": sql,
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("execute_sql", {"sql": sql[:100] + "..." if len(sql) > 100 else sql}, success=False)
        return error_result


# ==================== 系统管理工具 ====================


@mcp.tool()
def check_dependencies() -> Dict[str, Any]:
    """
    检查依赖包状态
    
    Returns:
        依赖包状态信息
    """
    dependencies = {
        "mcp": True,  # 如果能运行到这里，说明mcp已经可用
        "dmPython": DM_PYTHON_AVAILABLE
    }
    
    return {
        "dependencies": dependencies,
        "all_available": all(dependencies.values()),
        "message": "所有依赖可用" if all(dependencies.values()) else "部分依赖缺失",
        "timestamp": datetime.datetime.now().isoformat()
    }
                    



# ==================== 主程序入口 ====================

if __name__ == "__main__":
    print("启动达梦数据库 MCP服务器...")
    print("可用工具:")
    print("- connect_database: 连接到达梦数据库")
    print("- disconnect_database: 断开数据库连接")
    print("- test_connection: 测试数据库连接")
    print("- execute_sql: 执行自定义SQL（核心工具）")
    print("- check_dependencies: 检查依赖包状态")
    print("\n注意: 使用前请先调用 connect_database 工具连接数据库")
    print("所有数据库操作都可通过 execute_sql 工具完成")
    print("服务器运行中...")
    
    mcp.run(transport="stdio")

def main():
    """主函数，用于命令行启动"""
    try:
        print("达梦数据库 MCP 服务器 v2.1.0")
        print("正在启动服务器...")
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()