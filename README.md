# 达梦数据库 MCP 服务器

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

达梦数据库 MCP 服务器是一个基于 Model Context Protocol 的数据库访问服务。它可以让 Codex、Claude Code 以及其他支持 MCP 的 AI 开发工具，通过标准工具接口连接达梦数据库，执行连接测试、查看当前 Schema、列出表、统计表数量以及执行 SQL。

本项目通过环境变量配置数据库连接信息。你可以把同一份服务用于不同数据库、不同 Schema 或不同 MCP 客户端，而不需要修改源码。

## 功能特性

- 基于 FastMCP 实现，支持标准 MCP 客户端接入。
- 使用环境变量配置数据库连接，避免把账号密码写进代码。
- 支持通过 `DAMENG_SCHEMA` 指定当前服务使用的 Schema。
- 提供连接测试、Schema 查询、表列表、表数量统计和 SQL 执行工具。
- 返回结构化 JSON，便于 AI 客户端理解和继续分析。
- 支持 Codex、Claude Code 以及其他兼容 MCP 的工具。

## 一、准备环境

### 1. 安装 Python

本项目要求 Python 3.10 或更高版本。

可以在命令行中检查本机是否已经安装 Python：

```bash
python --version
```

如果提示找不到 `python`，可以再试：

```bash
python3 --version
```

如果没有安装，前往 Python 官网下载安装：

```text
https://www.python.org/downloads/
```

Windows 安装时建议勾选：

```text
Add python.exe to PATH
```

安装完成后重新打开终端，再次执行：

```bash
python --version
```

确认版本号为 `3.10` 或更高。

### 2. 安装 Git

如果你要从 GitHub 克隆项目，需要先安装 Git。

检查是否已安装：

```bash
git --version
```

如果未安装，可以从 Git 官网下载安装：

```text
https://git-scm.com/downloads
```

### 3. 安装 uv

推荐使用 `uv` 管理 Python 依赖。

安装命令：

```bash
pip install uv
```

安装完成后检查：

```bash
uv --version
```

如果你不想使用 `uv`，也可以使用 Python 自带的虚拟环境和 `pip`，下文会同时给出两种方式。

## 二、下载项目

使用 Git 克隆项目：

```bash
git clone https://github.com/example-org/dm-mcp-server.git
cd dm_mcp_server-2.3.9
```

如果你是下载 ZIP 包，解压后进入项目目录即可。

## 三、安装依赖

### 方式一：使用 uv

在项目根目录执行：

```bash
uv sync
```

这会根据项目配置创建虚拟环境并安装依赖。

### 方式二：使用 venv + pip

Linux/macOS：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 PowerShell 提示脚本执行策略限制，可以临时允许当前会话执行脚本：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 四、配置数据库连接

服务启动时会读取以下环境变量：

| 环境变量 | 是否必填 | 说明 |
| --- | --- | --- |
| `DAMENG_HOST` | 是 | 达梦数据库主机地址 |
| `DAMENG_PORT` | 否 | 达梦数据库端口，未配置时默认 `5236` |
| `DAMENG_USER` | 是 | 数据库用户名 |
| `DAMENG_PASSWORD` | 是 | 数据库密码 |
| `DAMENG_SCHEMA` | 建议填写 | MCP 服务默认使用的 Schema |

请不要把真实数据库密码提交到 Git 仓库。公开配置文件中建议使用占位符，真实密码只保存在本机环境变量、未提交的本地配置文件或密钥管理系统中。

### Linux/macOS 设置示例

```bash
export DAMENG_HOST="db.example.com"
export DAMENG_PORT="5236"
export DAMENG_USER="DM_USER"
export DAMENG_PASSWORD="change_me"
export DAMENG_SCHEMA="APP_SCHEMA"
```

### Windows PowerShell 设置示例

```powershell
$env:DAMENG_HOST="db.example.com"
$env:DAMENG_PORT="5236"
$env:DAMENG_USER="DM_USER"
$env:DAMENG_PASSWORD="change_me"
$env:DAMENG_SCHEMA="APP_SCHEMA"
```

## 五、本地启动服务

### 使用 uv 启动

```bash
uv run dm-mcp-server
```

### 直接使用 Python 启动

如果你使用的是 `venv + pip`：

```bash
python dm_mcp_server.py
```

Windows 也可以直接指定虚拟环境里的 Python：

```powershell
.\.venv\Scripts\python.exe .\dm_mcp_server.py
```

服务通常由 MCP 客户端自动启动。手动启动主要用于排查依赖、环境变量和数据库连接问题。

## 六、配置 MCP 客户端

多数 MCP 客户端使用 JSON 配置，核心结构通常是 `mcpServers`。

下面是通用配置模板。请把 `/path/to/dm_mcp_server-2.3.9` 替换为你本机项目目录，把数据库连接信息替换为你自己的配置。

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/dm_mcp_server-2.3.9",
        "dm-mcp-server"
      ],
      "env": {
        "DAMENG_HOST": "db.example.com",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "DM_USER",
        "DAMENG_PASSWORD": "change_me",
        "DAMENG_SCHEMA": "APP_SCHEMA"
      }
    }
  }
}
```

Windows 路径示例：

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\path\\to\\dm_mcp_server-2.3.9",
        "dm-mcp-server"
      ],
      "env": {
        "DAMENG_HOST": "db.example.com",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "DM_USER",
        "DAMENG_PASSWORD": "change_me",
        "DAMENG_SCHEMA": "APP_SCHEMA"
      }
    }
  }
}
```

## 七、Codex 配置

Codex 可以在 `config.toml` 中配置 MCP Server。

### 使用 uv 启动

```toml
[mcp_servers.dm_mcp_server]
command = "uv"
args = ["run", "--directory", "/path/to/dm_mcp_server-2.3.9", "dm-mcp-server"]
enabled = true

[mcp_servers.dm_mcp_server.env]
DAMENG_HOST = "db.example.com"
DAMENG_PORT = "5236"
DAMENG_USER = "DM_USER"
DAMENG_PASSWORD = "change_me"
DAMENG_SCHEMA = "APP_SCHEMA"
```

### 使用虚拟环境 Python 启动

Linux/macOS：

```toml
[mcp_servers.dm_mcp_server]
command = "/path/to/dm_mcp_server-2.3.9/.venv/bin/python"
args = ["/path/to/dm_mcp_server-2.3.9/dm_mcp_server.py"]
enabled = true

[mcp_servers.dm_mcp_server.env]
DAMENG_HOST = "db.example.com"
DAMENG_PORT = "5236"
DAMENG_USER = "DM_USER"
DAMENG_PASSWORD = "change_me"
DAMENG_SCHEMA = "APP_SCHEMA"
```

Windows：

```toml
[mcp_servers.dm_mcp_server]
command = "C:\\path\\to\\dm_mcp_server-2.3.9\\.venv\\Scripts\\python.exe"
args = ["C:\\path\\to\\dm_mcp_server-2.3.9\\dm_mcp_server.py"]
enabled = true

[mcp_servers.dm_mcp_server.env]
DAMENG_HOST = "db.example.com"
DAMENG_PORT = "5236"
DAMENG_USER = "DM_USER"
DAMENG_PASSWORD = "change_me"
DAMENG_SCHEMA = "APP_SCHEMA"
```

修改配置后，重启 Codex 让 MCP Server 重新加载。

## 八、Claude Code 配置

Claude Code 通常可以在项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "dm_mcp_server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/dm_mcp_server-2.3.9", "dm-mcp-server"],
      "env": {
        "DAMENG_HOST": "db.example.com",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "DM_USER",
        "DAMENG_PASSWORD": "change_me",
        "DAMENG_SCHEMA": "APP_SCHEMA"
      }
    }
  }
}
```

如果你的 Claude Code 项目启用了 `.claude/settings.local.json` 权限控制，可以允许本服务的工具：

```json
{
  "permissions": {
    "allow": [
      "mcp__dm_mcp_server__test_connection",
      "mcp__dm_mcp_server__get_current_schema",
      "mcp__dm_mcp_server__list_tables",
      "mcp__dm_mcp_server__count_tables",
      "mcp__dm_mcp_server__execute_sql"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "dm_mcp_server"
  ]
}
```

修改 `.mcp.json` 后，重启 Claude Code 或重新打开项目。

## 九、配置多个 Schema

如果你需要同时访问多个 Schema，建议为每个 Schema 配置一个 MCP Server。它们可以使用同一个项目目录，只需要修改 server 名称和 `DAMENG_SCHEMA`。

```json
{
  "mcpServers": {
    "dm_app": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/dm_mcp_server-2.3.9", "dm-mcp-server"],
      "env": {
        "DAMENG_HOST": "db.example.com",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "DM_USER",
        "DAMENG_PASSWORD": "change_me",
        "DAMENG_SCHEMA": "APP_SCHEMA"
      }
    },
    "dm_report": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/dm_mcp_server-2.3.9", "dm-mcp-server"],
      "env": {
        "DAMENG_HOST": "db.example.com",
        "DAMENG_PORT": "5236",
        "DAMENG_USER": "DM_USER",
        "DAMENG_PASSWORD": "change_me",
        "DAMENG_SCHEMA": "REPORT_SCHEMA"
      }
    }
  }
}
```

客户端中会出现两个独立 MCP Server，便于区分不同权限范围。

## 十、可用工具

| 工具名 | 说明 |
| --- | --- |
| `test_connection` | 测试当前数据库连接配置是否可用 |
| `get_current_schema` | 返回当前 MCP Server 配置的 Schema |
| `list_tables` | 列出当前 Schema 下的表 |
| `count_tables` | 统计当前 Schema 下的表数量 |
| `execute_sql` | 执行 SQL，并可返回查询结果 |

在支持 MCP 的客户端中，你可以这样提问：

```text
使用 dm_mcp_server 测试数据库连接。
使用 dm_mcp_server 查看当前 Schema。
使用 dm_mcp_server 列出当前 Schema 下的表。
使用 dm_mcp_server 执行 SELECT COUNT(*) FROM MY_TABLE。
```

## 十一、验证流程

首次配置完成后，建议按顺序验证：

1. 调用 `test_connection`，确认数据库能连接。
2. 调用 `get_current_schema`，确认 Schema 配置正确。
3. 调用 `count_tables`，确认当前用户能读取 Schema 元数据。
4. 调用 `list_tables`，确认能列出表。
5. 最后再尝试 `execute_sql`。

## 十二、常见问题

### Python 版本不符合要求

如果执行时提示 Python 版本过低，请安装 Python 3.10 或更高版本，并确认 MCP 客户端配置中的 Python 路径指向新版本。

### 找不到 dmPython

确认依赖安装成功：

```bash
pip show dmPython
```

如果没有结果，重新安装依赖：

```bash
pip install -r requirements.txt
```

### MCP 客户端启动失败

重点检查：

- `command` 是否存在。
- `args` 中的项目路径是否正确。
- Windows 路径中的反斜杠是否正确转义，例如 `C:\\path\\to\\project`。
- 数据库环境变量是否都配置完整。

### 数据库连接失败

重点检查：

- `DAMENG_HOST` 和 `DAMENG_PORT` 是否能从本机访问。
- 数据库用户名和密码是否正确。
- `DAMENG_SCHEMA` 是否存在。
- 当前用户是否有访问目标 Schema 的权限。

## 安全建议

- 不要提交真实数据库密码。
- 对只读分析场景，建议使用只读数据库账号。
- 在生产环境或共享环境中使用 `execute_sql` 前，应先确认 SQL 内容。
- 多个业务范围或多个 Schema 建议拆成多个 MCP Server，便于控制权限。

## 许可证

MIT License
