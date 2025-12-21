"""
数据库模型定义 - 使用maim_db的异步模型
"""

from .connection import (
    AsyncTenant as Tenant,
    AsyncAgent as Agent,
    AsyncApiKey as ApiKey,
    AsyncApiKey as ApiKey,
    AsyncAgentActiveState as AgentActiveState,
    init_database,
)
from .enums import TenantType, TenantStatus, AgentStatus, ApiKeyStatus


# 为了保持兼容性，创建一些别名和辅助函数
async def create_tables() -> None:
    """创建所有数据库表 - 使用maim_db"""
    try:
        from .connection import init_database

        init_database()

        # 使用 maim_db 的模型集合确保新表创建
        try:
            from maim_db.core import db_manager, ALL_MODELS

            db_manager.create_tables(ALL_MODELS)
            print("✅ 数据库表初始化成功（使用maim_db，包含活跃状态表）")
        except Exception as inner_exc:
            print(f"⚠️ 表创建阶段出现问题: {inner_exc}")
            # 不中断主流程，便于已有数据库继续启动
        else:
            return
    except Exception as e:
        print(f"❌ 数据库表初始化失败: {e}")
        raise


# 导出所有模型和枚举
__all__ = [
    "Tenant",
    "Agent",
    "ApiKey",
    "TenantType",
    "TenantStatus",
    "AgentStatus",
    "ApiKeyStatus",
    "AgentStatus",
    "ApiKeyStatus",
    "create_tables",
    "AgentActiveState",
]
