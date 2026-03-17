# 达梦数据库 MCP 服务器

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

一个基于 FastMCP 框架的达梦数据库 Model Context Protocol (MCP) 服务器。该服务器采用环境变量驱动，深度结合达梦数据库特性，并内置严格的安全审计机制。

## 🌟 特性

- 🚀 **环境变量驱动**: 全面通过环境变量配置，无需手动调用连接工具，即插即用。
- 🛡️ **深度安全审计**: 
  - 强制锁定配置的 `DAMENG_SCHEMA`。
  - 自动拦截跨模式 (Cross-Schema) 访问尝试。
  - 禁止在元数据查询中尝试过滤非本模式的信息。
- 🛠️ **多维工具集**: 提供从基础 SQL 执行到模式元数据管理的 5 大核心工具。
- 🌏 **编码优化**: 针对 Windows 终端及达梦 `UTF-8` 编码进行了专项适配。
- ⚡ **现代管理**: 使用 `uv` 进行依赖锁定与高性能运行时管理。

## 快速开始

### 1. 安装依赖

推荐使用 `uv` 进行环境同步：

```bash
uv sync
```

### 2. 配置环境变量

服务器在启动时会读取以下环境变量。请确保在调用前已正确设置：

| 变量名 | 说明 | 必填 | 默认值 |
| :-- | :-- | :-- | :-- |
| `DAMENG_HOST` | 数据库主机地址 | **是** | - |
| `DAMENG_PORT` | 数据库端口 | 否 | 5236 |
| `DAMENG_USER` | 数据库用户名 | **是** | - |
| `DAMENG_PASSWORD` | 数据库密码 | **是** | - |
| `DAMENG_SCHEMA` | 操作模式 (Schema) | **是** | 核心工具必须提供 |

### 3. 运行服务器

```bash
# Windows (PowerShell 示例)
$env:DAMENG_HOST="192.168.x.x"; $env:DAMENG_USER="SYSDBA"; $env:DAMENG_PASSWORD="your_password"; $env:DAMENG_SCHEMA="your_schema"; uv run dm-mcp-server
```

## 🛠️ 提供工具

服务器暴露了以下 5 个工具供 LLM 调用：

1. **`test_connection`**
   - **功能**: 验证当前环境变量配置是否能成功连接到达梦数据库。
2. **`execute_sql`**
   - **参数**: `sql` (字符串), `fetch_results` (布尔值，默认 true)。
   - **功能**: 执行任意 SQL 语句。涉及 `SELECT` 时返回字典列表。内置正则安全审查。
3. **`list_tables`**
   - **功能**: 列出当前配置模式 (`DAMENG_SCHEMA`) 下的所有表名。
4. **`count_tables`**
   - **功能**: 快速统计当前模式下的总表数。
5. **`get_current_schema`**
   - **功能**: 返回当前服务器锁定的模式名称。

## 🔒 安全性说明

为了防止非授权的数据访问，本服务器实施了以下安全策略：

- **模式隔离**: 所有 SQL 操作在执行前，都会通过 `SET SCHEMA` 显式切换到环境变量指定的模式。
- **防止注入**: 拦截包含点号 (`.`) 前缀且非当前模式的 SQL 标识符（例如禁止在 A 模式下查询 `B.TABLE`）。
- **元数据保护**: 在查询 `ALL_TABLES` 等系统视图时，如果检测到试图查询非本模式的 `OWNER`，将直接拦截。

## 在 Cursor / Claude Desktop / Antigravity / Trae 中配置

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
        "DAMENG_HOST": "192.168.x.x",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "SYSDBA",
        "DAMENG_PASSWORD": "your_password",
        "DAMENG_SCHEMA": "your_schema"
      }
    }
  }
}
```

## 许可证

MIT License