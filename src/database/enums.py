"""
数据库枚举定义 - Pydantic兼容版本
"""

from enum import Enum
from typing import Literal


class TenantType(str, Enum):
    """租户类型"""
    PERSONAL = "personal"
    ENTERPRISE = "enterprise"

    @classmethod
    def get_values(cls):
        return [e.value for e in cls]


class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

    @classmethod
    def get_values(cls):
        return [e.value for e in cls]


class AgentStatus(str, Enum):
    """Agent状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

    @classmethod
    def get_values(cls):
        return [e.value for e in cls]


class ApiKeyStatus(str, Enum):
    """API密钥状态"""
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"

    @classmethod
    def get_values(cls):
        return [e.value for e in cls]


# 类型别名，用于Pydantic
TenantTypeLiteral = Literal[TenantType.PERSONAL.value, TenantType.ENTERPRISE.value]
TenantStatusLiteral = Literal[TenantStatus.ACTIVE.value, TenantStatus.INACTIVE.value, TenantStatus.SUSPENDED.value]
AgentStatusLiteral = Literal[AgentStatus.ACTIVE.value, AgentStatus.INACTIVE.value, AgentStatus.ARCHIVED.value]
ApiKeyStatusLiteral = Literal[ApiKeyStatus.ACTIVE.value, ApiKeyStatus.DISABLED.value, ApiKeyStatus.EXPIRED.value]


__all__ = [
    'TenantType', 'TenantStatus', 'AgentStatus', 'ApiKeyStatus',
    'TenantTypeLiteral', 'TenantStatusLiteral',
    'AgentStatusLiteral', 'ApiKeyStatusLiteral'
]