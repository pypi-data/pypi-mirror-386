"""Protein MCP - 基于FastMCP的蛋白质数据访问工具"""

__version__ = "0.1.5"
__author__ = "gqy20"
__email__ = "qingyu_ge@foxmail.com"

from .server import create_server, main
from .tools import register_all_tools

__all__ = ["create_server", "main", "register_all_tools"]
