"""
FastAPI Stoplight Elements

一个将 FastAPI 与 Stoplight Elements 结合的库，用于快速生成美观、交互式的 API 文档。
"""

__version__ = "0.1.0"
__author__ = "月间"
__email__ = ""
__description__ = "FastAPI + Stoplight Elements 快速开发API文档"

from .fastapi_stoplight import (
    get_stoplight_elements_html,
    TryItCredentialsPolicy,
    DocumentationLayout,
    NavigationRouter,
)

__all__ = [
    "get_stoplight_elements_html",
    "TryItCredentialsPolicy", 
    "DocumentationLayout",
    "NavigationRouter",
]