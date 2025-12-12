"""
API路由模块
"""

from .tenant_api import router as tenant_router
from .agent_api import router as agent_router
from .api_key_api import router as api_key_router
from .auth_api import router as auth_router
from .auth_api import router as auth_router
from .active_state_api import router as active_state_router
from .plugin_api import router as plugin_router

__all__ = [
    "tenant_router",
    "agent_router",
    "api_key_router",
    "auth_router",
    "active_state_router",
    "plugin_router",
]
