# 达梦数据库 MCP 服务器

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

一个基于 FastMCP 框架的达梦数据库 Model Context Protocol (MCP) 服务器，采用环境变量驱动。

## 特性

- 🚀 **环境变量配置**: 通过环境变量预设连接信息，安全且高效
- 🎯 **极致简化**: 只包含 `execute_sql` 和 `test_connection` 核心工具
- 🌏 **编码友好**: 针对 Windows 及达梦环境优化的 UTF-8 处理
- ⚡ **现代管理**: 使用 `uv` 进行高效的项目管理与依赖锁定

## 快速开始

### 1. 安装依赖

推荐使用 `uv` 进行管理：

```bash
# 同步环境
uv sync
```

### 2. 配置环境变量

在启动服务器前，需设置以下环境变量：

| 变量名 | 说明 | 必填 | 默认值 |
| :-- | :-- | :-- | :-- |
| `DAMENG_HOST` | 数据库主机地址 | 是 | - |
| `DAMENG_PORT` | 数据库端口 | 否 | 5236 |
| `DAMENG_USER` | 用户名 | 是 | - |
| `DAMENG_PASSWORD` | 密码 | 是 | - |
| `DAMENG_SCHEMA` | 默认模式 (Schema) | 否 | - |

### 3. 启动服务器

```bash
# Windows (PowerShell)
$env:DAMENG_HOST="localhost"; $env:DAMENG_USER="SYSDBA"; $env:DAMENG_PASSWORD="SYSDBA_PASSWORD"; uv run dm-mcp-server
```

## 在 Cursor / Claude Desktop 中配置

### 使用 `uvx` (推荐方式)

将以下配置添加到您的 MCP 配置文件中（如 Cursor 的 `mcpServers` 设置）：

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "uvx",
      "args": [
        "dm-mcp-server"
      ],
      "env": {
        "DAMENG_HOST": "192.168.30.86",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "SYSDBA",
        "DAMENG_PASSWORD": "your_password",
        "DAMENG_SCHEMA": "your_schema"
      }
    }
  }
}
```

### 本地开发配置 (使用 `uv`)

## 提供工具

### `test_connection`
测试当前配置是否能成功连接到达梦数据库。

### `execute_sql`
执行任意 SQL 语句。支持：
- `SELECT` 查询（返回结果列表）
- `INSERT/UPDATE/DELETE` 操作（返回受影响行数）
- `DDL` 语句（如 `CREATE TABLE`, `COMMENT ON` 等）

## 许可证

MIT License