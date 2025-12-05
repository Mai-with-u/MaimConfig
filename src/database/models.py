"""
数据库模型定义 - 使用maim_db的异步模型
"""

from .connection import (
    AsyncTenant as Tenant,
    AsyncAgent as Agent,
    AsyncApiKey as ApiKey,
    init_database
)
from .enums import (
    TenantType,
    TenantStatus,
    AgentStatus,
    ApiKeyStatus
)


# 为了保持兼容性，创建一些别名和辅助函数
async def create_tables() -> None:
    """创建所有数据库表 - 使用maim_db"""
    try:
        from .connection import init_database
        await init_database()
        print("✅ 数据库表初始化成功（使用maim_db）")
    except Exception as e:
        print(f"❌ 数据库表初始化失败: {e}")
        raise


# 导出所有模型和枚举
__all__ = [
    'Tenant', 'Agent', 'ApiKey',
    'TenantType', 'TenantStatus', 'AgentStatus', 'ApiKeyStatus',
    'create_tables'
]