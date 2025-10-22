"""
API路由模块

定义API路由。
"""

from .auth import router as auth_router
from .users import router as users_router

__all__ = ["auth_router", "users_router"]
