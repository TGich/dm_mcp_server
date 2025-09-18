#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦数据库 MCP 服务器
提供完整的达梦数据库操作功能

Author: AI Assistant
Version: 2.0
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
except ImportError:
    print("错误: 缺少 dmPython 包，请运行: pip install dmPython")
    exit(1)

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
mcp = FastMCP("达梦数据库 MCP服务器")

# 全局变量
DB_CONFIG: Optional[Dict[str, Any]] = None
query_history: List[Dict[str, Any]] = []
operation_history: List[Dict[str, Any]] = []

# ==================== 核心工具函数 ====================

@contextmanager
def get_db_connection(host: Optional[str] = None, port: Optional[int] = None, 
                     user: Optional[str] = None, password: Optional[str] = None, 
                     database: Optional[str] = None):
    """获取数据库连接的上下文管理器"""
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


def format_table_name(table_name: str, schema: Optional[str] = None) -> str:
    """格式化表名"""
    return f'"{schema}".{table_name}' if schema else table_name


def format_column_name(column_name: str) -> str:
    """格式化列名，处理保留字问题"""
    # SQL保留字列表
    reserved_words = {
        'class', 'order', 'group', 'select', 'from', 'where', 'insert', 'update', 
        'delete', 'create', 'drop', 'alter', 'table', 'index', 'view', 'user',
        'database', 'schema', 'constraint', 'primary', 'foreign', 'key', 'unique',
        'check', 'default', 'null', 'not', 'and', 'or', 'in', 'like', 'between',
        'is', 'as', 'desc', 'asc', 'limit', 'offset', 'union', 'join', 'inner',
        'left', 'right', 'outer', 'on', 'having', 'distinct', 'count', 'sum',
        'avg', 'min', 'max', 'case', 'when', 'then', 'else', 'end', 'exists'
    }
    
    # 如果是保留字，使用双引号包围
    if column_name.lower() in reserved_words:
        return f'"{column_name}"'
    return column_name


def execute_with_error_handling(func, *args, **kwargs) -> Dict[str, Any]:
    """统一的错误处理装饰器"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"操作失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        logger.error(f"操作失败: {e}")
        return error_result


def setup_chinese_encoding(cursor) -> None:
    """设置中文编码支持"""
    try:
        # 尝试设置字符集
        cursor.execute("SET CHAR_CODE UTF-8")
    except Exception:
        pass
    
    try:
        # 尝试设置语言环境
        cursor.execute("ALTER SESSION SET NLS_LANGUAGE='SIMPLIFIED CHINESE'")
    except Exception:
        pass
    
    try:
        # 尝试设置字符集
        cursor.execute("ALTER SESSION SET NLS_CHARACTERSET='UTF8'")
    except Exception:
        pass


def execute_comment_sql(cursor, sql: str, comment: str) -> None:
    """执行注释SQL，处理中文编码问题"""
    try:
        # 设置中文编码
        setup_chinese_encoding(cursor)
        
        # 尝试多种方式执行注释SQL
        methods = [
            # 方法1: 直接字符串拼接
            lambda: cursor.execute(f"{sql} '{comment}'"),
            # 方法2: 使用参数化查询
            lambda: cursor.execute(f"{sql} ?", [comment]),
            # 方法3: 使用Unicode编码
            lambda: cursor.execute(f"{sql} '{comment.encode('utf-8').decode('utf-8')}'"),
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                method()
                logger.info(f"注释SQL执行成功，使用方法{i}")
                return
            except Exception as e:
                logger.warning(f"注释SQL执行方法{i}失败: {e}")
                continue
        
        # 如果所有方法都失败，抛出最后一个异常
        raise Exception("所有注释SQL执行方法都失败")
        
    except Exception as e:
        logger.error(f"执行注释SQL失败: {e}")
        raise

# ==================== 数据库连接管理工具 ====================

@mcp.tool()
def connect_database(host: str = "localhost", port: int = 5236, 
                    user: str = "SYSDBA", password: str = "", 
                    database: str = "") -> Dict[str, Any]:
    """
    连接到达梦数据库
    
    Args:
        host: 数据库主机地址
        port: 数据库端口
        user: 数据库用户名
        password: 数据库密码
        database: 数据库名称
    
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
        with get_db_connection(host, port, user, password, database) as conn:
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
                "database": database or "默认数据库",
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
                "database": DB_CONFIG.get('database', '默认数据库'),
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


@mcp.tool()
def get_database_info() -> Dict[str, Any]:
    """
    获取数据库信息
    
    Returns:
        数据库详细信息
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 获取所有用户模式
            cursor.execute("SELECT USERNAME FROM DBA_USERS WHERE ACCOUNT_STATUS = 'OPEN' ORDER BY USERNAME")
            schemas = [row[0] for row in cursor.fetchall()]
            
            # 获取当前用户可访问的所有模式
            cursor.execute("SELECT DISTINCT OWNER FROM ALL_OBJECTS WHERE OWNER IS NOT NULL ORDER BY OWNER")
            all_schemas = [row[0] for row in cursor.fetchall()]
            
            # 获取所有表
            cursor.execute("SELECT DISTINCT OWNER, TABLE_NAME FROM ALL_TABLES ORDER BY OWNER, TABLE_NAME")
            tables = cursor.fetchall()
            
            cursor.close()
            
            result = {
                "user_schemas": schemas,
                "all_schemas": all_schemas,
                "tables": [{"schema": table[0], "table_name": table[1]} for table in tables],
                "table_count": len(tables),
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("get_database_info", result)
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取数据库信息失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("get_database_info", error_result, success=False)
        return error_result

# ==================== 表管理工具 ====================

@mcp.tool()
def create_table(table_name: str, columns: List[Dict[str, str]], 
                schema: Optional[str] = None,
                primary_key: Optional[str] = None) -> Dict[str, Any]:
    """
    创建数据表
    
    Args:
        table_name: 表名
        columns: 列定义列表，格式: [{"name": "id", "type": "INT", "constraints": "PRIMARY KEY"}]
        schema: 模式名
        primary_key: 主键列名
    
    Returns:
        创建结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 构建列定义
            column_definitions = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                if 'constraints' in col and col['constraints']:
                    col_def += f" {col['constraints']}"
                column_definitions.append(col_def)
            
            # 添加主键
            if primary_key:
                column_definitions.append(f"PRIMARY KEY ({primary_key})")
            
            # 构建CREATE TABLE语句
            full_table_name = format_table_name(table_name, schema)
            create_sql = f"CREATE TABLE {full_table_name} ({', '.join(column_definitions)})"
            
            cursor.execute(create_sql)
            cursor.close()
            
            result = {
                "status": "success",
                "message": f"表 {table_name} 创建成功",
                "sql": create_sql,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("create_table", {"table_name": table_name, "schema": schema, "columns": columns})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"创建表失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("create_table", {"table_name": table_name, "schema": schema}, success=False)
        return error_result


@mcp.tool()
def describe_table(table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
    """
    获取表结构信息
    
    Args:
        table_name: 表名
        schema: 模式名
    
    Returns:
        表结构信息
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if schema:
                sql = f"""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, DATA_DEFAULT
                FROM ALL_TAB_COLUMNS 
                WHERE TABLE_NAME = '{table_name.upper()}' AND OWNER = '{schema.upper()}'
                ORDER BY COLUMN_ID
                """
            else:
                sql = f"""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, DATA_DEFAULT
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = '{table_name.upper()}'
                ORDER BY COLUMN_ID
                """
            
            cursor.execute(sql)
            columns = cursor.fetchall()
            cursor.close()
            
            # 格式化列信息
            column_info = []
            for col in columns:
                column_info.append({
                    "column_name": col[0],
                    "data_type": col[1],
                    "data_length": col[2],
                    "nullable": col[3],
                    "default_value": col[4]
                })
            
            result = {
                "table_name": table_name,
                "schema": schema,
                "columns": column_info,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("describe_table", {"table_name": table_name, "schema": schema})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"获取表结构失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("describe_table", {"table_name": table_name, "schema": schema}, success=False)
        return error_result


@mcp.tool()
def drop_table(table_name: str, schema: Optional[str] = None, 
               if_exists: bool = True) -> Dict[str, Any]:
    """
    删除数据表
    
    Args:
        table_name: 表名
        schema: 模式名
        if_exists: 如果表不存在是否报错
    
    Returns:
        删除结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            full_table_name = format_table_name(table_name, schema)
            if_exists_clause = "IF EXISTS" if if_exists else ""
            drop_sql = f"DROP TABLE {if_exists_clause} {full_table_name}"
            
            cursor.execute(drop_sql)
            cursor.close()
            
            result = {
                "status": "success",
                "message": f"表 {table_name} 删除成功",
                "sql": drop_sql,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("drop_table", {"table_name": table_name, "schema": schema})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"删除表失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("drop_table", {"table_name": table_name, "schema": schema}, success=False)
        return error_result

# ==================== 数据操作工具 ====================

@mcp.tool()
def insert_data(table_name: str, data: List[Dict[str, Any]], 
               schema: Optional[str] = None) -> Dict[str, Any]:
    """
    插入数据
    
    Args:
        table_name: 表名
        data: 要插入的数据列表
        schema: 模式名
    
    Returns:
        插入结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    if not data:
        return {"status": "error", "message": "数据不能为空"}
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            full_table_name = format_table_name(table_name, schema)
            
            # 获取列名
            columns = list(data[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            # 构建INSERT语句
            insert_sql = f"INSERT INTO {full_table_name} ({column_names}) VALUES ({placeholders})"
            
            # 准备数据
            values_list = []
            for row in data:
                values = [row[col] for col in columns]
                values_list.append(tuple(values))
            
            # 执行批量插入
            cursor.executemany(insert_sql, values_list)
            affected_rows = cursor.rowcount
            cursor.close()
            
            result = {
                "status": "success",
                "message": f"成功插入 {affected_rows} 条记录",
                "affected_rows": affected_rows,
                "sql": insert_sql,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("insert_data", {"table_name": table_name, "schema": schema, "rows": len(data)})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"插入数据失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("insert_data", {"table_name": table_name, "schema": schema}, success=False)
        return error_result


@mcp.tool()
def select_data(table_name: str, columns: str = "*", 
               where_clause: Optional[str] = None,
               order_by: Optional[str] = None,
               limit: Optional[int] = None,
               schema: Optional[str] = None) -> Dict[str, Any]:
    """
    查询数据
    
    Args:
        table_name: 表名
        columns: 要查询的列，默认为*
        where_clause: WHERE条件
        order_by: 排序条件
        limit: 限制记录数
        schema: 模式名
    
    Returns:
        查询结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            full_table_name = format_table_name(table_name, schema)
            
            # 构建SELECT语句
            select_sql = f"SELECT {columns} FROM {full_table_name}"
            
            if where_clause:
                select_sql += f" WHERE {where_clause}"
            
            if order_by:
                select_sql += f" ORDER BY {order_by}"
            
            if limit:
                select_sql += f" LIMIT {limit}"
            
            cursor.execute(select_sql)
            results = cursor.fetchall()
            
            # 获取列名
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            cursor.close()
            
            # 记录查询历史
            query_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "sql": select_sql,
                "table": table_name,
                "schema": schema,
                "result_count": len(results)
            }
            query_history.append(query_record)
            
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
                "sql": select_sql,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("select_data", {"table_name": table_name, "schema": schema, "count": len(results)})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"查询数据失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("select_data", {"table_name": table_name, "schema": schema}, success=False)
        return error_result


@mcp.tool()
def update_data(table_name: str, set_clause: str, 
               where_clause: Optional[str] = None,
               schema: Optional[str] = None) -> Dict[str, Any]:
    """
    更新数据
    
    Args:
        table_name: 表名
        set_clause: SET子句，格式: "column1=value1, column2=value2"
        where_clause: WHERE条件
        schema: 模式名
    
    Returns:
        更新结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            full_table_name = format_table_name(table_name, schema)
            
            # 构建UPDATE语句
            update_sql = f"UPDATE {full_table_name} SET {set_clause}"
            
            if where_clause:
                update_sql += f" WHERE {where_clause}"
            
            cursor.execute(update_sql)
            affected_rows = cursor.rowcount
            cursor.close()
            
            result = {
                "status": "success",
                "message": f"成功更新 {affected_rows} 条记录",
                "affected_rows": affected_rows,
                "sql": update_sql,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("update_data", {"table_name": table_name, "schema": schema, "affected_rows": affected_rows})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"更新数据失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("update_data", {"table_name": table_name, "schema": schema}, success=False)
        return error_result


@mcp.tool()
def delete_data(table_name: str, where_clause: str, 
               schema: Optional[str] = None) -> Dict[str, Any]:
    """
    删除数据
    
    Args:
        table_name: 表名
        where_clause: WHERE条件
        schema: 模式名
    
    Returns:
        删除结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            full_table_name = format_table_name(table_name, schema)
            
            # 构建DELETE语句
            delete_sql = f"DELETE FROM {full_table_name} WHERE {where_clause}"
            
            cursor.execute(delete_sql)
            affected_rows = cursor.rowcount
            cursor.close()
            
            result = {
                "status": "success",
                "message": f"成功删除 {affected_rows} 条记录",
                "affected_rows": affected_rows,
                "sql": delete_sql,
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("delete_data", {"table_name": table_name, "schema": schema, "affected_rows": affected_rows})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"删除数据失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("delete_data", {"table_name": table_name, "schema": schema}, success=False)
        return error_result

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

# ==================== 注释管理工具 ====================

@mcp.tool()
def add_table_comment(table_name: str, comment: str, 
                     schema: Optional[str] = None) -> Dict[str, Any]:
    """
    为表添加中文注释
    
    Args:
        table_name: 表名
        comment: 表注释
        schema: 模式名
    
    Returns:
        添加结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            full_table_name = format_table_name(table_name, schema)
            
            # 使用优化的注释执行方法
            sql = f"COMMENT ON TABLE {full_table_name} IS"
            execute_comment_sql(cursor, sql, comment)
            cursor.close()
            
            result = {
                "status": "success",
                "message": f"成功为表 {table_name} 添加注释: {comment}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("add_table_comment", {"table_name": table_name, "schema": schema, "comment": comment})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"添加表注释失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("add_table_comment", {"table_name": table_name, "schema": schema}, success=False)
        return error_result


@mcp.tool()
def add_column_comment(table_name: str, column_name: str, comment: str,
                      schema: Optional[str] = None) -> Dict[str, Any]:
    """
    为表的列添加中文注释
    
    Args:
        table_name: 表名
        column_name: 列名
        comment: 列注释
        schema: 模式名
    
    Returns:
        添加结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            full_table_name = format_table_name(table_name, schema)
            
            # 使用优化的注释执行方法
            formatted_column = format_column_name(column_name)
            sql = f"COMMENT ON COLUMN {full_table_name}.{formatted_column} IS"
            execute_comment_sql(cursor, sql, comment)
            cursor.close()
            
            result = {
                "status": "success",
                "message": f"成功为表 {table_name} 的列 {column_name} 添加注释: {comment}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            log_operation("add_column_comment", {"table_name": table_name, "column_name": column_name, "schema": schema, "comment": comment})
            return result
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"添加列注释失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        log_operation("add_column_comment", {"table_name": table_name, "column_name": column_name, "schema": schema}, success=False)
        return error_result

# ==================== 中文注释测试工具 ====================

@mcp.tool()
def test_chinese_comment(table_name: str, comment: str, 
                        schema: Optional[str] = None) -> Dict[str, Any]:
    """
    测试中文注释功能
    
    Args:
        table_name: 表名
        comment: 测试注释内容
        schema: 模式名
    
    Returns:
        测试结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 测试中文编码设置
            setup_chinese_encoding(cursor)
            
            # 测试简单的SELECT语句
            cursor.execute("SELECT '中文测试' FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            
            if result and '中文测试' in str(result):
                return {
                    "status": "success",
                    "message": "中文编码测试成功",
                    "test_result": str(result),
                    "timestamp": datetime.datetime.now().isoformat()
                }
            else:
                return {
                    "status": "warning",
                    "message": "中文编码可能有问题",
                    "test_result": str(result),
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"中文编码测试失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        return error_result


@mcp.tool()
def batch_add_comments(table_name: str, comments: Dict[str, str], 
                      schema: Optional[str] = None) -> Dict[str, Any]:
    """
    批量添加表和列的中文注释
    
    Args:
        table_name: 表名
        comments: 注释字典，格式: {"table": "表注释", "column1": "列1注释", "column2": "列2注释"}
        schema: 模式名
    
    Returns:
        批量添加结果
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    results = []
    success_count = 0
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 添加表注释
            if "table" in comments:
                try:
                    full_table_name = format_table_name(table_name, schema)
                    sql = f"COMMENT ON TABLE {full_table_name} IS"
                    execute_comment_sql(cursor, sql, comments["table"])
                    results.append({
                        "type": "table",
                        "name": table_name,
                        "comment": comments["table"],
                        "status": "success"
                    })
                    success_count += 1
                except Exception as e:
                    results.append({
                        "type": "table",
                        "name": table_name,
                        "comment": comments["table"],
                        "status": "error",
                        "error": str(e)
                    })
            
            # 添加列注释
            for column_name, comment in comments.items():
                if column_name != "table":
                    try:
                        full_table_name = format_table_name(table_name, schema)
                        formatted_column = format_column_name(column_name)
                        sql = f"COMMENT ON COLUMN {full_table_name}.{formatted_column} IS"
                        execute_comment_sql(cursor, sql, comment)
                        results.append({
                            "type": "column",
                            "name": column_name,
                            "comment": comment,
                            "status": "success"
                        })
                        success_count += 1
                    except Exception as e:
                        results.append({
                            "type": "column",
                            "name": column_name,
                            "comment": comment,
                            "status": "error",
                            "error": str(e)
                        })
            
            cursor.close()
            
            return {
                "status": "success" if success_count > 0 else "error",
                "message": f"批量添加注释完成，成功: {success_count}/{len(comments)}",
                "results": results,
                "success_count": success_count,
                "total_count": len(comments),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"批量添加注释失败: {str(e)}",
            "results": results,
            "timestamp": datetime.datetime.now().isoformat()
        }
        return error_result

# ==================== 系统管理工具 ====================

@mcp.tool()
def get_query_history(limit: int = 10) -> Dict[str, Any]:
    """
    获取查询历史
    
    Args:
        limit: 返回记录数量限制
    
    Returns:
        查询历史记录
    """
    recent_history = query_history[-limit:] if query_history else []
    
    return {
        "history": recent_history,
        "total_count": len(query_history),
        "limit": limit,
        "timestamp": datetime.datetime.now().isoformat()
    }


@mcp.tool()
def get_operation_history(limit: int = 10) -> Dict[str, Any]:
    """
    获取操作历史
    
    Args:
        limit: 返回记录数量限制
    
    Returns:
        操作历史记录
    """
    recent_history = operation_history[-limit:] if operation_history else []
    
    return {
        "history": recent_history,
        "total_count": len(operation_history),
        "limit": limit,
        "timestamp": datetime.datetime.now().isoformat()
    }


@mcp.tool()
def get_server_status() -> Dict[str, Any]:
    """
    获取服务器状态
    
    Returns:
        服务器状态信息
    """
    connection_check = check_connection()
    if connection_check:
        return connection_check
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 获取达梦数据库版本
            try:
                cursor.execute("SELECT SF_GET_SYSTEM_INFO('VERSION') FROM DUAL")
                version = cursor.fetchone()[0]
            except Exception:
                version = "未知版本"
            
            cursor.close()
            
            return {
                "dm_version": version,
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "database": DB_CONFIG.get('database', '默认数据库'),
                "query_history_count": len(query_history),
                "operation_history_count": len(operation_history),
                "timestamp": datetime.datetime.now().isoformat()
            }
                    
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取服务器状态失败: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

# ==================== 资源管理 ====================

@mcp.resource("dm://schema/{schema_name}")
def get_schema_resource(schema_name: str) -> str:
    """
    获取模式资源信息
    
    Args:
        schema_name: 模式名称
    
    Returns:
        模式信息的JSON字符串
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 获取模式中的表
            cursor.execute(f"SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER = '{schema_name.upper()}' ORDER BY TABLE_NAME")
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            
            info = {
                "schema_name": schema_name,
                "tables": tables,
                "table_count": len(tables),
                "timestamp": datetime.datetime.now().isoformat()
            }
            return json.dumps(info, ensure_ascii=False, indent=2)
            
    except Exception as e:
        error_info = {
            "error": f"获取模式信息失败: {str(e)}",
            "schema_name": schema_name,
            "timestamp": datetime.datetime.now().isoformat()
        }
        return json.dumps(error_info, ensure_ascii=False, indent=2)


@mcp.resource("dm://table/{table_name}")
def get_table_resource(table_name: str) -> str:
    """
    获取表资源信息
    
    Args:
        table_name: 表名
    
    Returns:
        表信息的JSON字符串
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 获取表结构
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, DATA_DEFAULT
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = '{table_name.upper()}'
                ORDER BY COLUMN_ID
            """)
            columns = cursor.fetchall()
            
            cursor.close()
            
            info = {
                "table_name": table_name,
                "columns": [
                    {
                        "column_name": col[0],
                        "data_type": col[1],
                        "data_length": col[2],
                        "nullable": col[3],
                        "default_value": col[4]
                    } for col in columns
                ],
                "timestamp": datetime.datetime.now().isoformat()
            }
            return json.dumps(info, ensure_ascii=False, indent=2)
            
    except Exception as e:
        error_info = {
            "error": f"获取表信息失败: {str(e)}",
            "table_name": table_name,
            "timestamp": datetime.datetime.now().isoformat()
        }
        return json.dumps(error_info, ensure_ascii=False, indent=2)


@mcp.resource("dm://status")
def get_dm_status_resource() -> str:
    """
    获取达梦数据库状态资源
    
    Returns:
        达梦数据库状态信息的JSON字符串
    """
    status = get_server_status()
    return json.dumps(status, ensure_ascii=False, indent=2)

# ==================== 主程序入口 ====================

if __name__ == "__main__":
    print("启动达梦数据库 MCP服务器...")
    print("可用工具:")
    print("- connect_database: 连接到达梦数据库")
    print("- disconnect_database: 断开数据库连接")
    print("- test_connection: 测试数据库连接")
    print("- get_database_info: 获取数据库信息")
    print("- create_table: 创建数据表")
    print("- describe_table: 获取表结构")
    print("- drop_table: 删除数据表")
    print("- insert_data: 插入数据")
    print("- select_data: 查询数据")
    print("- update_data: 更新数据")
    print("- delete_data: 删除数据")
    print("- execute_sql: 执行自定义SQL")
    print("- add_table_comment: 为表添加中文注释")
    print("- add_column_comment: 为列添加中文注释")
    print("- test_chinese_comment: 测试中文注释功能")
    print("- batch_add_comments: 批量添加中文注释")
    print("- get_query_history: 获取查询历史")
    print("- get_operation_history: 获取操作历史")
    print("- get_server_status: 获取服务器状态")
    print("\n可用资源:")
    print("- dm://schema/{schema_name}: 模式信息")
    print("- dm://table/{table_name}: 表信息")
    print("- dm://status: 达梦数据库状态信息")
    print("\n注意: 使用前请先调用 connect_database 工具连接数据库")
    print("服务器运行中...")
    
    mcp.run(transport="stdio")

def main():
    """主函数，用于命令行启动"""
    print("达梦数据库 MCP 服务器 v2.0.0")
    print("正在启动服务器...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()