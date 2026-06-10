#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦数据库 MCP 服务器

一个基于 FastMCP 框架的达梦数据库 Model Context Protocol (MCP) 服务器，
提供完整的达梦数据库操作功能。

Author: wxt
Version: 2.4
"""

__version__ = "2.4"
__author__ = "wxt"
__email__ = "contact@example.com"
__description__ = "达梦数据库 Model Context Protocol (MCP) 服务器"

# 导入主要模块
try:
    from .dm_mcp_server import main
    __all__ = ['main']
except ImportError:
    # 如果无法导入，可能是因为依赖未安装
    __all__ = []
