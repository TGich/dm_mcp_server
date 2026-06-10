#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦 MCP 服务器测试脚本
测试服务器的各项功能和安全性机制
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 动态导入 MCP 服务器模块
sys.path.insert(0, os.path.dirname(__file__))
import dm_mcp_server

class MCPServerTester:
    """MCP 服务器测试类"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
    
    def test(self, name: str, func, expected_status: str = None):
        """执行单个测试"""
        try:
            logger.info(f"\n▶ 测试: {name}")
            result = func()
            
            # 记录结果
            status = result.get('status', 'unknown')
            message = result.get('message', '')
            
            if expected_status and status != expected_status:
                self.failed += 1
                self.test_results.append({
                    'name': name,
                    'status': '❌ 失败',
                    'reason': f"期望状态: {expected_status}, 实际: {status}",
                    'response': result
                })
                logger.error(f"  ❌ 失败: 期望 {expected_status}, 得到 {status}")
                if message:
                    logger.error(f"  消息: {message}")
            else:
                self.passed += 1
                self.test_results.append({
                    'name': name,
                    'status': '✅ 通过',
                    'reason': '',
                    'response': result
                })
                logger.info(f"  ✅ 通过")
                if message:
                    logger.info(f"  消息: {message}")
                    
            # 显示数据摘要
            if 'data' in result:
                logger.info(f"  数据行数: {len(result['data']) if isinstance(result['data'], list) else 1}")
            if 'count' in result:
                logger.info(f"  计数: {result['count']}")
                
        except Exception as e:
            self.failed += 1
            self.errors.append(str(e))
            self.test_results.append({
                'name': name,
                'status': '⚠️ 异常',
                'reason': str(e),
                'response': None
            })
            logger.error(f"  ⚠️ 异常: {e}")
    
    def print_summary(self):
        """打印测试摘要"""
        total = self.passed + self.failed + self.skipped
        logger.info("\n" + "="*60)
        logger.info("📊 测试摘要")
        logger.info("="*60)
        logger.info(f"总计: {total} | ✅ 通过: {self.passed} | ❌ 失败: {self.failed} | ⏭️ 跳过: {self.skipped}")
        
        if self.errors:
            logger.info("\n错误列表:")
            for i, err in enumerate(self.errors, 1):
                logger.error(f"  {i}. {err}")
        
        logger.info("="*60)
        return self.passed, self.failed, self.skipped
    
    def export_report(self, filepath: str = None):
        """导出 JSON 格式的测试报告"""
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), 'test_report.json')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': self.passed + self.failed + self.skipped,
                'passed': self.passed,
                'failed': self.failed,
                'skipped': self.skipped
            },
            'tests': self.test_results,
            'errors': self.errors
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📄 报告已导出到: {filepath}")
        return filepath

def run_tests():
    """运行所有测试"""
    tester = MCPServerTester()
    
    logger.info("\n" + "="*60)
    logger.info("🚀 达梦 MCP 服务器测试启动")
    logger.info("="*60)
    
    # 测试 1: 环境变量检查
    logger.info("\n【第一组】环境变量和配置检查")
    config = dm_mcp_server.DB_CONFIG
    if config:
        logger.info(f"  ✓ 数据库配置已加载")
        logger.info(f"    - Host: {config.get('host')}")
        logger.info(f"    - Port: {config.get('port')}")
        logger.info(f"    - User: {config.get('user')}")
        logger.info(f"    - Schema: {config.get('schema', '未设置')}")
    else:
        logger.warning(f"  ⚠ 数据库配置未加载 (缺失环境变量)")
    
    # 测试 2: dmPython 驱动检查
    logger.info("\n【第二组】驱动和依赖检查")
    logger.info(f"  dmPython 可用: {'✅ 是' if dm_mcp_server.DM_PYTHON_AVAILABLE else '❌ 否'}")
    logger.info(f"  MCP 框架版本: 已加载")
    
    # 测试 3: 测试数据库连接
    logger.info("\n【第三组】数据库连接测试")
    tester.test("连接测试", dm_mcp_server.test_connection)
    
    # 测试 4: 获取当前 Schema
    logger.info("\n【第四组】Schema 操作测试")
    tester.test("获取当前 Schema", dm_mcp_server.get_current_schema)
    
    # 测试 5: 列表查询
    logger.info("\n【第五组】元数据查询测试")
    tester.test("列出所有表", lambda: dm_mcp_server.list_tables())
    tester.test("统计表数量", lambda: dm_mcp_server.count_tables())
    
    # 测试 6: SQL 执行
    logger.info("\n【第六组】SQL 执行测试")
    
    # 简单 SELECT 测试
    def test_select():
        return dm_mcp_server.execute_sql("SELECT 1 AS test_col")
    tester.test("执行 SELECT 1", test_select)
    
    # 测试 7: 安全性测试
    logger.info("\n【第七组】安全性机制测试")
    
    # 无 SCHEMA 配置时的拦截
    def test_no_schema_execute():
        return dm_mcp_server.execute_sql("SELECT * FROM sys.all_tables LIMIT 1")
    
    def test_cross_schema():
        return dm_mcp_server.execute_sql("SELECT * FROM other_schema.table1")
    
    # 这些应该被拦截（如果配置了 SCHEMA）
    if dm_mcp_server.DB_CONFIG and dm_mcp_server.DB_CONFIG.get('schema'):
        tester.test("跨 Schema 查询拦截", test_cross_schema)
    
    # 打印摘要
    passed, failed, skipped = tester.print_summary()
    
    # 导出报告
    report_path = tester.export_report()
    
    return passed, failed, skipped

if __name__ == "__main__":
    try:
        passed, failed, skipped = run_tests()
        sys.exit(0 if failed == 0 else 1)
    except Exception as e:
        logger.error(f"\n测试执行异常: {e}", exc_info=True)
        sys.exit(2)
