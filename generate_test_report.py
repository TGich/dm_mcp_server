#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦 MCP 服务器 - 测试总结报告生成
"""

import os
import json
from datetime import datetime
from pathlib import Path

def generate_final_report():
    """生成最终的测试总结报告"""
    
    report_dir = os.path.dirname(__file__)
    
    # 收集所有测试报告
    test_reports = []
    
    for report_file in ['test_report.json', 'comprehensive_test_report.json']:
        report_path = os.path.join(report_dir, report_file)
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                test_reports.append({
                    'name': report_file,
                    'data': json.load(f)
                })
    
    # 生成综合报告
    final_report = {
        'title': '达梦 MCP 服务器测试总结',
        'timestamp': datetime.now().isoformat(),
        'project_info': {
            'name': 'dm-mcp-server',
            'version': '2.4',
            'description': '达梦数据库 Model Context Protocol (MCP) 服务器',
            'repository': 'https://github.com/example-org/dm-mcp-server'
        },
        'test_suites': test_reports,
        'features': {
            'tools': [
                {
                    'name': 'test_connection',
                    'description': '测试数据库连接状态',
                    'parameters': [],
                    'returns': 'Dict[str, Any]'
                },
                {
                    'name': 'execute_sql',
                    'description': '执行 SQL 语句（强制限定配置下的SCHEMA操作）',
                    'parameters': [
                        {'name': 'sql', 'type': 'str', 'description': 'SQL 语句'},
                        {'name': 'fetch_results', 'type': 'bool', 'default': True, 'description': '是否获取结果'}
                    ],
                    'returns': 'Dict[str, Any]'
                },
                {
                    'name': 'list_tables',
                    'description': '只能查询配置SCHEMA下的所有表',
                    'parameters': [
                        {'name': 'schema', 'type': 'str', 'optional': True, 'description': 'Schema 名称'}
                    ],
                    'returns': 'Dict[str, Any]'
                },
                {
                    'name': 'count_tables',
                    'description': '只能统计配置SCHEMA下的表数量',
                    'parameters': [
                        {'name': 'schema', 'type': 'str', 'optional': True, 'description': 'Schema 名称'}
                    ],
                    'returns': 'Dict[str, Any]'
                },
                {
                    'name': 'get_current_schema',
                    'description': '获取当前配置的数据库的SCHEMA',
                    'parameters': [],
                    'returns': 'Dict[str, Any]'
                }
            ]
        },
        'security_features': [
            'SCHEMA 限制 - 防止跨 Schema 操作',
            'SQL 检查 - 检测并拦截危险的 SQL 操作',
            '连接超时 - TCP 连接超时检查',
            '错误处理 - 全面的异常捕获和报告',
            '环境变量配置 - 安全的配置管理'
        ],
        'environment_variables': [
            {
                'name': 'DAMENG_HOST',
                'description': '数据库主机地址',
                'required': True,
                'example': 'localhost'
            },
            {
                'name': 'DAMENG_PORT',
                'description': '数据库端口',
                'required': False,
                'default': 5236,
                'example': '5236'
            },
            {
                'name': 'DAMENG_USER',
                'description': '数据库用户名',
                'required': True,
                'example': 'SYSDBA'
            },
            {
                'name': 'DAMENG_PASSWORD',
                'description': '数据库密码',
                'required': True,
                'example': 'SYSDBA'
            },
            {
                'name': 'DAMENG_SCHEMA',
                'description': '数据库 Schema（模式）',
                'required': True,
                'example': 'SYSDBA'
            }
        ],
        'dependencies': {
            'runtime': [
                'mcp>=1.0.0',
                'dmPython>=2.0.0',
                'setuptools-scm>=6.2'
            ],
            'python_version': '>=3.10'
        },
        'test_results_summary': {
            'total_suites': len(test_reports),
            'total_tests': sum(r['data'].get('summary', {}).get('total', 0) for r in test_reports),
            'total_passed': sum(r['data'].get('summary', {}).get('passed', 0) for r in test_reports),
            'total_failed': sum(r['data'].get('summary', {}).get('failed', 0) for r in test_reports)
        },
        'recommendations': [
            '如果 dmPython 驱动导入失败，请确保已正确安装: pip install dmPython',
            '在使用前必须设置所有必要的环境变量（DAMENG_HOST, DAMENG_USER, DAMENG_PASSWORD, DAMENG_SCHEMA）',
            '建议在生产环境中使用强密码和安全的连接配置',
            '定期测试数据库连接以确保 MCP 服务器正常运行'
        ]
    }
    
    # 保存最终报告
    report_path = os.path.join(report_dir, 'TEST_REPORT_FINAL.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
    
    print("✅ 最终测试报告已生成")
    print(f"📄 报告位置: {report_path}")
    
    # 生成 Markdown 格式的报告
    markdown_report = generate_markdown_report(final_report)
    md_path = os.path.join(report_dir, 'TEST_REPORT.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print(f"📄 Markdown 报告: {md_path}")
    
    return report_path, md_path

def generate_markdown_report(report):
    """生成 Markdown 格式的报告"""
    md = f"""# {report['title']}

生成时间: {report['timestamp']}

## 项目信息

- **名称**: {report['project_info']['name']}
- **版本**: {report['project_info']['version']}
- **描述**: {report['project_info']['description']}

## 测试结果总结

| 指标 | 数值 |
|------|------|
| 测试套件 | {report['test_results_summary']['total_suites']} |
| 总测试数 | {report['test_results_summary']['total_tests']} |
| 通过 | {report['test_results_summary']['total_passed']} |
| 失败 | {report['test_results_summary']['total_failed']} |

## 功能列表

本 MCP 服务器提供以下工具函数：

"""
    
    for tool in report['features']['tools']:
        md += f"""### {tool['name']}

**描述**: {tool['description']}

**参数**:
"""
        if tool['parameters']:
            for param in tool['parameters']:
                param_name = param.get('name', 'N/A')
                param_desc = param.get('description', 'N/A')
                md += f"- `{param_name}`: {param_desc}\n"
        else:
            md += "- 无参数\n"
        
        md += f"""
**返回值**: {tool['returns']}

"""
    
    md += """## 安全特性

"""
    for feature in report['security_features']:
        md += f"- ✅ {feature}\n"
    
    md += """

## 环境变量配置

"""
    for env_var in report['environment_variables']:
        required = "必需" if env_var['required'] else "可选"
        md += f"""### {env_var['name']} ({required})

{env_var['description']}

"""
        if 'default' in env_var:
            md += f"**默认值**: {env_var['default']}\n"
        if 'example' in env_var:
            md += f"**示例**: `{env_var['example']}`\n"
        md += "\n"
    
    md += """## 依赖项

"""
    md += f"""### 运行时依赖

```
"""
    for dep in report['dependencies']['runtime']:
        md += f"{dep}\n"
    md += f"""```

### Python 版本

{report['dependencies']['python_version']}

## 建议和最佳实践

"""
    for i, rec in enumerate(report['recommendations'], 1):
        md += f"{i}. {rec}\n"
    
    md += """

## 如何运行测试

```bash
# 运行功能测试
python test_mcp_server.py

# 运行综合测试
python test_comprehensive.py

# 生成测试报告
python generate_test_report.py
```

## 快速开始

### 1. 安装项目

```bash
pip install -e .
```

### 2. 配置环境变量

```bash
export DAMENG_HOST=localhost
export DAMENG_PORT=5236
export DAMENG_USER=SYSDBA
export DAMENG_PASSWORD=SYSDBA
export DAMENG_SCHEMA=SYSDBA
```

### 3. 启动 MCP 服务器

```bash
dm-mcp-server
```

### 4. 连接到客户端

使用支持 MCP 协议的客户端连接到服务器进行数据库操作。

"""
    
    return md

if __name__ == "__main__":
    json_path, md_path = generate_final_report()
    print("\n✅ 测试报告生成完成！")
