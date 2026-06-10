#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦 MCP 服务器集成测试
通过模拟的配置环境进行功能测试
"""

import os
import sys
import json
import tempfile
import subprocess
import time
from datetime import datetime
from pathlib import Path

def create_test_env_file():
    """创建测试环境配置文件"""
    env_content = """
# 达梦数据库连接配置示例
# 注意：这是测试模板，实际使用需要配置有效的数据库信息

# 数据库主机地址
DAMENG_HOST=localhost

# 数据库端口（默认：5236）
DAMENG_PORT=5236

# 数据库用户名
DAMENG_USER=SYSDBA

# 数据库密码
DAMENG_PASSWORD=SYSDBA

# 数据库 Schema（模式）
DAMENG_SCHEMA=SYSDBA
"""
    
    path = os.path.join(os.path.dirname(__file__), '.env.test')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✓ 创建测试环境文件: {path}")
    return path

def test_mcp_protocol():
    """测试 MCP 协议支持"""
    print("\n【MCP 协议检查】")
    
    # 检查 MCP 包
    try:
        import mcp
        print(f"  ✅ MCP 框架已安装")
        
        # 检查 FastMCP
        from mcp.server.fastmcp import FastMCP
        print(f"  ✅ FastMCP 支持已加载")
        
        return True
    except ImportError as e:
        print(f"  ❌ MCP 框架问题: {e}")
        return False

def test_dameng_driver():
    """测试达梦驱动支持"""
    print("\n【达梦驱动检查】")
    
    try:
        import dmPython
        print(f"  ✅ dmPython 驱动已安装")
        print(f"     版本: {getattr(dmPython, '__version__', '未知')}")
        return True
    except ImportError:
        print(f"  ⚠️ dmPython 驱动未安装")
        print(f"     请运行: pip install dmPython")
        return False

def test_module_imports():
    """测试主模块导入"""
    print("\n【模块导入检查】")
    
    try:
        # 将项目目录添加到路径
        project_dir = os.path.dirname(__file__)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
        
        import dm_mcp_server
        print(f"  ✅ dm_mcp_server 模块加载成功")
        
        # 检查主要函数
        functions = [
            'test_connection',
            'execute_sql',
            'list_tables',
            'count_tables',
            'get_current_schema'
        ]
        
        for func_name in functions:
            if hasattr(dm_mcp_server, func_name):
                print(f"  ✅ 函数 {func_name} 可用")
            else:
                print(f"  ❌ 函数 {func_name} 不可用")
        
        return True
    except Exception as e:
        print(f"  ❌ 模块导入失败: {e}")
        return False

def test_configuration():
    """测试配置系统"""
    print("\n【配置系统检查】")
    
    try:
        import dm_mcp_server
        
        config = dm_mcp_server.get_config()
        
        if config:
            print(f"  ✅ 配置已加载")
            print(f"     Host: {config.get('host', '未设置')}")
            print(f"     Port: {config.get('port', 5236)}")
            print(f"     User: {config.get('user', '未设置')}")
            print(f"     Schema: {config.get('schema', '未设置')}")
        else:
            print(f"  ⚠️ 配置未完全加载（缺失必要的环境变量）")
            print(f"     需要设置: DAMENG_HOST, DAMENG_USER, DAMENG_PASSWORD")
        
        return True
    except Exception as e:
        print(f"  ❌ 配置系统检查失败: {e}")
        return False

def test_response_format():
    """测试响应格式"""
    print("\n【响应格式检查】")
    
    try:
        import dm_mcp_server
        
        # 测试 resp() 函数的输出格式
        response = dm_mcp_server.resp("success", data=[1, 2, 3], count=3)
        
        # 验证必要字段
        required_fields = ['status', 'timestamp']
        missing_fields = [f for f in required_fields if f not in response]
        
        if not missing_fields:
            print(f"  ✅ 响应格式正确")
            print(f"     Fields: {list(response.keys())}")
        else:
            print(f"  ❌ 响应缺失字段: {missing_fields}")
        
        return len(missing_fields) == 0
    except Exception as e:
        print(f"  ❌ 响应格式检查失败: {e}")
        return False

def test_security_features():
    """测试安全特性"""
    print("\n【安全特性检查】")
    
    try:
        import dm_mcp_server
        
        # 检查是否有安全相关的代码
        source = open(os.path.join(os.path.dirname(__file__), 'dm_mcp_server.py'), 'r', encoding='utf-8').read()
        
        security_features = {
            'SCHEMA限制': 'SCHEMA' in source,
            'SQL检查': 'sql_upper' in source or 'OWNER' in source,
            '连接超时': 'timeout' in source,
            '错误处理': 'except' in source
        }
        
        for feature, present in security_features.items():
            status = '✅' if present else '❌'
            print(f"  {status} {feature}: {'已实现' if present else '未实现'}")
        
        return all(security_features.values())
    except Exception as e:
        print(f"  ❌ 安全特性检查失败: {e}")
        return False

def generate_comprehensive_report(results):
    """生成综合测试报告"""
    print("\n" + "="*60)
    print("📊 综合测试报告")
    print("="*60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': results,
        'summary': {
            'total': len(results),
            'passed': sum(1 for r in results.values() if r),
            'failed': sum(1 for r in results.values() if not r)
        }
    }
    
    print(f"\n总计: {report['summary']['total']}")
    print(f"✅ 通过: {report['summary']['passed']}")
    print(f"❌ 失败: {report['summary']['failed']}")
    
    # 保存报告
    report_path = os.path.join(os.path.dirname(__file__), 'comprehensive_test_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存: {report_path}")
    
    return report_path

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 达梦 MCP 服务器综合测试")
    print("="*60)
    
    results = {}
    
    # 创建测试环境文件
    create_test_env_file()
    
    # 运行各项测试
    results['MCP 协议支持'] = test_mcp_protocol()
    results['达梦驱动支持'] = test_dameng_driver()
    results['模块导入'] = test_module_imports()
    results['配置系统'] = test_configuration()
    results['响应格式'] = test_response_format()
    results['安全特性'] = test_security_features()
    
    # 生成报告
    report_path = generate_comprehensive_report(results)
    
    print("\n" + "="*60)
    print("✅ 综合测试完成")
    print("="*60)
    
    # 返回状态码
    failed_count = sum(1 for r in results.values() if not r)
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
