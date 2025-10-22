# -*- coding: utf-8 -*-
"""
Tushare Docs MCP Server

提供 Tushare 接口文档查询功能的 MCP 服务器。
"""

__version__ = "0.1.0"
__author__ = "Momojie"
__email__ = "momojiesuper@gmail.com"

from .main import main
from .tools import mcp

__all__ = ["main", "mcp"]