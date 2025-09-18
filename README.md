# 达梦数据库 MCP 服务器

[![PyPI version](https://badge.fury.io/py/dm-mcp-server.svg)](https://badge.fury.io/py/dm-mcp-server)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于 FastMCP 框架的达梦数据库 Model Context Protocol (MCP) 服务器，提供完整的达梦数据库操作功能。

## 特性

- 🚀 **动态连接**: 无需配置文件，运行时通过工具连接数据库
- 🔧 **完整功能**: 支持表管理、数据操作、查询执行等完整数据库操作
- 🌏 **中文支持**: 完美支持中文注释和UTF-8编码
- 📊 **资源管理**: 提供模式、表、状态等资源访问
- 📝 **操作历史**: 记录查询和操作历史，便于追踪
- ⚡ **高性能**: 基于FastMCP框架，性能优异
- 🎯 **uvx支持**: 支持uvx直接运行，无需安装

## 技术栈

- **框架**: FastMCP (Model Context Protocol)
- **数据库**: 达梦数据库 (DM Database)
- **驱动**: dmPython
- **语言**: Python 3.8+
- **依赖**: 仅需 mcp 和 dmPython

## 安装

### 方法一：使用 uvx 运行（推荐）

```bash
# 直接运行，无需安装
uvx dm-mcp-server
```

### 方法二：从 PyPI 安装

```bash
pip install dm-mcp-server
```

### 方法三：从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-username/dm-mcp-server.git
cd dm-mcp-server

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install .
```

### 方法四：直接运行

```bash
# 安装依赖
pip install mcp dmPython

# 直接运行
python dm_mcp_server.py
```

## 配置

### Cursor MCP 配置

#### 使用 uvx（推荐）

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "uvx",
      "args": ["dm-mcp-server"]
    }
  }
}
```

#### 使用 pip 安装

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "python",
      "args": ["-m", "dm_mcp_server"]
    }
  }
}
```

#### 直接运行

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "python",
      "args": ["path/to/dm_mcp_server.py"]
    }
  }
}
```

### 示例配置

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "D:\\Python\\Python313\\python.exe",
      "args": ["E:\\PycharmProjects\\dm_mcp_server\\dm_mcp_server.py"]
    }
  }
}
```

## 使用方法

### 1. 连接数据库

首先需要连接到数据库：

```python
# 连接到达梦数据库
result = connect_database(
    host="your_host",
    port=15237,
    user="SYSDBA",
    password="your_password"
)
```

### 2. 基本操作

#### 创建表

```python
# 创建学生表
columns = [
    {"name": "id", "type": "INT", "constraints": "PRIMARY KEY"},
    {"name": "name", "type": "VARCHAR(50)"},
    {"name": "age", "type": "INT"},
    {"name": "gender", "type": "VARCHAR(10)"},
    {"name": "class", "type": "VARCHAR(20)"}
]

result = create_table(
    table_name="test_student",
    columns=columns,
    schema="test"
)
```

#### 添加中文注释

```python
# 为表添加注释
add_table_comment("test_student", "学生信息表", "test")

# 为列添加注释
add_column_comment("test_student", "name", "学生姓名", "test")
add_column_comment("test_student", "age", "学生年龄", "test")
add_column_comment("test_student", "gender", "学生性别", "test")
add_column_comment("test_student", "class", "学生班级", "test")

# 或者使用批量添加注释
comments = {
    "table": "学生信息表",
    "name": "学生姓名",
    "age": "学生年龄", 
    "gender": "学生性别",
    "class": "学生班级"
}
batch_add_comments("test_student", comments, "test")

# 测试中文注释功能
test_chinese_comment("test_student", "测试中文注释", "test")
```

#### 插入数据

```python
# 插入学生数据
data = [
    {"id": 1, "name": "张三", "age": 20, "gender": "男", "class": "计算机1班"},
    {"id": 2, "name": "李四", "age": 19, "gender": "女", "class": "计算机2班"}
]

result = insert_data("test_student", data, "test")
```

#### 查询数据

```python
# 查询所有学生
result = select_data("test_student", schema="test")

# 条件查询
result = select_data(
    "test_student", 
    where_clause="age > 19",
    schema="test"
)
```

## 可用工具

### 数据库连接管理
- `connect_database`: 连接到达梦数据库
- `disconnect_database`: 断开数据库连接
- `test_connection`: 测试数据库连接
- `get_database_info`: 获取数据库信息

### 表管理
- `create_table`: 创建数据表
- `describe_table`: 获取表结构信息
- `drop_table`: 删除数据表

### 数据操作
- `insert_data`: 插入数据
- `select_data`: 查询数据
- `update_data`: 更新数据
- `delete_data`: 删除数据

### 高级功能
- `execute_sql`: 执行自定义SQL语句
- `add_table_comment`: 为表添加中文注释
- `add_column_comment`: 为列添加中文注释
- `test_chinese_comment`: 测试中文注释功能
- `batch_add_comments`: 批量添加中文注释

### 系统管理
- `get_query_history`: 获取查询历史
- `get_operation_history`: 获取操作历史
- `get_server_status`: 获取服务器状态

## 可用资源

- `dm://schema/{schema_name}`: 模式信息
- `dm://table/{table_name}`: 表信息
- `dm://status`: 达梦数据库状态信息

## 项目结构

```
dm_mcp_server/
├── dm_mcp_server.py      # 主服务器文件
├── requirements.txt      # 依赖包
├── README.md            # 项目文档
└── .cursorrules         # Cursor规则文件
```

## 代码特点

### 1. 清晰的代码结构
- 按功能模块组织代码
- 统一的错误处理
- 完善的类型注解

### 2. 高效的连接管理
- 动态数据库连接
- 上下文管理器自动管理连接
- 连接状态检查

### 3. 完善的日志记录
- 操作历史追踪
- 查询历史记录
- 统一的日志格式

### 4. 中文支持
- UTF-8编码支持
- 中文注释功能
- 参数化查询避免编码问题

## 错误处理

所有工具都提供统一的错误处理：

```json
{
  "status": "error",
  "message": "错误描述",
  "timestamp": "2024-01-01T00:00:00"
}
```

成功响应：

```json
{
  "status": "success",
  "message": "操作成功",
  "data": {...},
  "timestamp": "2024-01-01T00:00:00"
}
```

## 注意事项

1. **连接要求**: 使用前必须先调用 `connect_database` 工具连接数据库
2. **权限要求**: 确保数据库用户有足够的权限执行相应操作
3. **编码支持**: 支持UTF-8编码，中文注释功能完善
4. **多模式支持**: 支持指定schema参数进行多模式操作

## 常见问题

### Q: 如何解决中文编码问题？
A: ✅ **已完全修复**！服务器现在支持：
- 自动设置UTF-8字符集和编码
- 多种中文注释执行方法（自动重试机制）
- 专门的中文注释测试工具
- 批量添加中文注释功能
- 完善的错误处理和日志记录

### Q: 如何查看操作历史？
A: 使用 `get_query_history` 和 `get_operation_history` 工具查看历史记录。

### Q: 支持哪些数据库操作？
A: 支持完整的CRUD操作、表管理、自定义SQL执行等。

## 开发指南

### 添加新工具

1. 使用 `@mcp.tool()` 装饰器
2. 添加类型注解和文档字符串
3. 实现连接检查和错误处理
4. 记录操作历史

### 代码规范

- 使用类型注解 (Type Hints)
- 遵循PEP 8代码风格
- 完善的错误处理和日志记录
- 清晰的函数命名和文档

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v2.1 (2024-01-01)
- ✅ **修复中文注释问题**: 完全解决达梦数据库中文注释编码错误
- ✅ **增强编码支持**: 添加多种中文编码处理方法
- ✅ **新增测试工具**: 提供中文注释功能测试
- ✅ **批量注释功能**: 支持一次性添加多个注释
- ✅ **自动重试机制**: 多种方法自动尝试执行注释SQL

### v2.0 (2024-01-01)
- 重构代码结构，提高可维护性
- 优化错误处理和日志记录
- 移除冗余代码和文件
- 完善文档和注释

### v1.0 (2023-12-01)
- 初始版本发布
- 支持基本数据库操作
- 中文注释支持
- FastMCP框架集成