#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达梦数据库 MCP 服务器 - PyPI 包配置
"""

from setuptools import setup

# 读取 README 文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

setup(
    name="dm-mcp-server",
    version="2.4",
    author="wxt",
    author_email="contact@example.com",
    description="达梦数据库 Model Context Protocol (MCP) 服务器",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example-org/dm-mcp-server",
    py_modules=["dm_mcp_server"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "dm-mcp-server=dm_mcp_server:main",
        ],
    },
    keywords="dameng database mcp model-context-protocol dmPython",
    project_urls={
        "Bug Reports": "https://github.com/example-org/dm-mcp-server/issues",
        "Source": "https://github.com/example-org/dm-mcp-server",
        "Documentation": "https://github.com/example-org/dm-mcp-server#readme",
    },
    include_package_data=False,
    zip_safe=False,
)
