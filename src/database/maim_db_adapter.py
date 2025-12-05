"""
maim_db数据库适配器
将maim_db的Peewee模型适配为maimconfig需要的接口
"""

import sys
import os
from typing import AsyncGenerator, Optional, Any, List, Dict
from contextlib import asynccontextmanager
import json
from datetime import datetime

# 添加maim_db路径
maim_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'maim_db')
if maim_db_path not in sys.path:
    sys.path.insert(0, maim_db_path)

try:
    from maim_db.src.core import (
        Tenant as MaimDbTenant,
        Agent as MaimDbAgent,
        ApiKey as MaimDbApiKey,
        get_database,
        init_database,
        close_database
    )
    from maim_db.src.core.models.system_v2 import (
        TenantType,
        TenantStatus,
        AgentStatus,
        ApiKeyStatus
    )
    MAIM_DB_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入maim_db: {e}")
    MAIM_DB_AVAILABLE = False


class MaimDbAdapter:
    """maim_db适配器类"""

    def __init__(self):
        if not MAIM_DB_AVAILABLE:
            raise ImportError("maim_db 未安装或路径不正确")

        self.database = get_database()

    async def init_database(self):
        """初始化数据库连接"""
        try:
            init_database()
            print("✅ maim_db 数据库连接初始化成功")
        except Exception as e:
            print(f"❌ maim_db 数据库连接初始化失败: {e}")
            raise

    async def close_database(self):
        """关闭数据库连接"""
        try:
            close_database()
            print("✅ maim_db 数据库连接关闭成功")
        except Exception as e:
            print(f"❌ maim_db 数据库连接关闭失败: {e}")

    @asynccontextmanager
    async def get_session(self):
        """获取数据库会话上下文管理器"""
        try:
            self.database.connect()
            yield self.database
        except Exception as e:
            print(f"❌ 数据库会话错误: {e}")
            raise
        finally:
            if self.database.is_connection_usable():
                self.database.close()


# 创建全局适配器实例
try:
    db_adapter = MaimDbAdapter()
except ImportError:
    db_adapter = None
    print("⚠️ maim_db 适配器初始化失败，将使用模拟模式")


# 兼容性模型 - 将maim_db模型适配为maimconfig需要的格式
class Tenant:
    """租户模型 - maim_db适配器"""

    def __init__(self, maim_db_tenant: MaimDbTenant = None):
        if maim_db_tenant:
            self.id = maim_db_tenant.id
            self.tenant_name = maim_db_tenant.tenant_name
            self.tenant_type = TenantType(maim_db_tenant.tenant_type)
            self.description = maim_db_tenant.description
            self.contact_email = maim_db_tenant.contact_email
            self.tenant_config = self._parse_json(maim_db_tenant.tenant_config)
            self.status = TenantStatus(maim_db_tenant.status)
            self.owner_id = maim_db_tenant.owner_id
            self.created_at = maim_db_tenant.created_at
            self.updated_at = maim_db_tenant.updated_at
            self._maim_db_instance = maim_db_tenant
        else:
            # 创建新实例时的默认值
            self.id = None
            self.tenant_name = None
            self.tenant_type = TenantType.PERSONAL
            self.description = None
            self.contact_email = None
            self.tenant_config = None
            self.status = TenantStatus.ACTIVE
            self.owner_id = None
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self._maim_db_instance = None

    def _parse_json(self, json_str: str) -> Optional[Dict]:
        """解析JSON字符串"""
        if not json_str:
            return None
        try:
            return json.loads(json_str) if isinstance(json_str, str) else json_str
        except:
            return None

    def _serialize_json(self, obj: Any) -> Optional[str]:
        """序列化为JSON字符串"""
        if not obj:
            return None
        try:
            return json.dumps(obj) if isinstance(obj, (dict, list)) else str(obj)
        except:
            return str(obj)

    @classmethod
    async def create(cls, **kwargs) -> 'Tenant':
        """创建租户"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        async with db_adapter.get_session() as db:
            # 准备数据
            data = {
                'tenant_name': kwargs.get('tenant_name'),
                'tenant_type': kwargs.get('tenant_type', TenantType.PERSONAL.value),
                'description': kwargs.get('description'),
                'contact_email': kwargs.get('contact_email'),
                'tenant_config': json.dumps(kwargs.get('tenant_config', {})),
                'status': kwargs.get('status', TenantStatus.ACTIVE.value),
                'owner_id': kwargs.get('owner_id'),
            }

            # 如果没有提供ID，生成一个
            if 'id' not in kwargs:
                import uuid
                data['id'] = f"tenant_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            maim_db_tenant = MaimDbTenant.create(**data)
            return cls(maim_db_tenant)

    @classmethod
    async def get(cls, tenant_id: str) -> Optional['Tenant']:
        """获取租户"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        try:
            async with db_adapter.get_session() as db:
                maim_db_tenant = MaimDbTenant.get_by_id(tenant_id)
                return cls(maim_db_tenant)
        except MaimDbTenant.DoesNotExist:
            return None

    @classmethod
    async def get_by_name(cls, tenant_name: str) -> Optional['Tenant']:
        """根据名称获取租户"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        try:
            async with db_adapter.get_session() as db:
                maim_db_tenant = MaimDbTenant.get(MaimDbTenant.tenant_name == tenant_name)
                return cls(maim_db_tenant)
        except MaimDbTenant.DoesNotExist:
            return None

    @classmethod
    async def get_all(cls, limit: int = None, offset: int = 0) -> List['Tenant']:
        """获取所有租户"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        async with db_adapter.get_session() as db:
            query = MaimDbTenant.select()
            if limit:
                query = query.limit(limit).offset(offset)

            tenants = []
            for maim_db_tenant in query:
                tenants.append(cls(maim_db_tenant))
            return tenants

    @classmethod
    async def count(cls) -> int:
        """获取租户总数"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        async with db_adapter.get_session() as db:
            return MaimDbTenant.select().count()

    async def update(self, **kwargs) -> 'Tenant':
        """更新租户"""
        if not self._maim_db_instance:
            raise RuntimeError("租户实例未关联到数据库记录")

        async with db_adapter.get_session() as db:
            # 更新字段
            for field, value in kwargs.items():
                if hasattr(self._maim_db_instance, field):
                    if field in ['tenant_config'] and value is not None:
                        value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                    setattr(self._maim_db_instance, field, value)

            # 保存更新
            self._maim_db_instance.save()

            # 更新本地属性
            for field, value in kwargs.items():
                if hasattr(self, field):
                    setattr(self, field, value)

            return self

    async def delete(self):
        """删除租户"""
        if not self._maim_db_instance:
            raise RuntimeError("租户实例未关联到数据库记录")

        async with db_adapter.get_session() as db:
            self._maim_db_instance.delete_instance()

    def __repr__(self):
        return f"<Tenant(id='{self.id}', name='{self.tenant_name}')>"


class Agent:
    """Agent模型 - maim_db适配器"""

    def __init__(self, maim_db_agent: MaimDbAgent = None):
        if maim_db_agent:
            self.id = maim_db_agent.id
            self.tenant_id = maim_db_agent.tenant_id
            self.name = maim_db_agent.name
            self.description = maim_db_agent.description
            self.template_id = maim_db_agent.template_id
            self.config = self._parse_json(maim_db_agent.config)
            self.status = AgentStatus(maim_db_agent.status)
            self.created_at = maim_db_agent.created_at
            self.updated_at = maim_db_agent.updated_at
            self._maim_db_instance = maim_db_agent
        else:
            self.id = None
            self.tenant_id = None
            self.name = None
            self.description = None
            self.template_id = None
            self.config = None
            self.status = AgentStatus.ACTIVE
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self._maim_db_instance = None

    def _parse_json(self, json_str: str) -> Optional[Dict]:
        if not json_str:
            return None
        try:
            return json.loads(json_str) if isinstance(json_str, str) else json_str
        except:
            return None

    @classmethod
    async def create(cls, **kwargs) -> 'Agent':
        """创建Agent"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        async with db_adapter.get_session() as db:
            data = {
                'tenant_id': kwargs.get('tenant_id'),
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'template_id': kwargs.get('template_id'),
                'config': json.dumps(kwargs.get('config', {})),
                'status': kwargs.get('status', AgentStatus.ACTIVE.value),
            }

            if 'id' not in kwargs:
                import uuid
                data['id'] = f"agent_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            maim_db_agent = MaimDbAgent.create(**data)
            return cls(maim_db_agent)

    @classmethod
    async def get(cls, agent_id: str) -> Optional['Agent']:
        """获取Agent"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        try:
            async with db_adapter.get_session() as db:
                maim_db_agent = MaimDbAgent.get_by_id(agent_id)
                return cls(maim_db_agent)
        except MaimDbAgent.DoesNotExist:
            return None

    @classmethod
    async def get_by_tenant(cls, tenant_id: str) -> List['Agent']:
        """获取租户下的所有Agent"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        async with db_adapter.get_session() as db:
            agents = []
            for maim_db_agent in MaimDbAgent.select().where(MaimDbAgent.tenant_id == tenant_id):
                agents.append(cls(maim_db_agent))
            return agents

    def __repr__(self):
        return f"<Agent(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


class ApiKey:
    """API密钥模型 - maim_db适配器"""

    def __init__(self, maim_db_api_key: MaimDbApiKey = None):
        if maim_db_api_key:
            self.id = maim_db_api_key.id
            self.tenant_id = maim_db_api_key.tenant_id
            self.agent_id = maim_db_api_key.agent_id
            self.name = maim_db_api_key.name
            self.description = maim_db_api_key.description
            self.api_key = maim_db_api_key.api_key
            self.permissions = self._parse_json(maim_db_api_key.permissions)
            self.status = ApiKeyStatus(maim_db_api_key.status)
            self.expires_at = maim_db_api_key.expires_at
            self.last_used_at = maim_db_api_key.last_used_at
            self.usage_count = maim_db_api_key.usage_count
            self.created_at = maim_db_api_key.created_at
            self.updated_at = maim_db_api_key.updated_at
            self._maim_db_instance = maim_db_api_key
        else:
            self.id = None
            self.tenant_id = None
            self.agent_id = None
            self.name = None
            self.description = None
            self.api_key = None
            self.permissions = []
            self.status = ApiKeyStatus.ACTIVE
            self.expires_at = None
            self.last_used_at = None
            self.usage_count = 0
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self._maim_db_instance = None

    def _parse_json(self, json_str: str) -> List[str]:
        if not json_str:
            return []
        try:
            result = json.loads(json_str) if isinstance(json_str, str) else json_str
            return result if isinstance(result, list) else [str(result)]
        except:
            return []

    @classmethod
    async def create(cls, **kwargs) -> 'ApiKey':
        """创建API密钥"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        async with db_adapter.get_session() as db:
            data = {
                'tenant_id': kwargs.get('tenant_id'),
                'agent_id': kwargs.get('agent_id'),
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'api_key': kwargs.get('api_key'),
                'permissions': json.dumps(kwargs.get('permissions', [])),
                'status': kwargs.get('status', ApiKeyStatus.ACTIVE.value),
                'expires_at': kwargs.get('expires_at'),
            }

            if 'id' not in kwargs:
                import uuid
                data['id'] = f"key_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            maim_db_api_key = MaimDbApiKey.create(**data)
            return cls(maim_db_api_key)

    @classmethod
    async def get(cls, api_key_id: str) -> Optional['ApiKey']:
        """获取API密钥"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        try:
            async with db_adapter.get_session() as db:
                maim_db_api_key = MaimDbApiKey.get_by_id(api_key_id)
                return cls(maim_db_api_key)
        except MaimDbApiKey.DoesNotExist:
            return None

    @classmethod
    async def get_by_key(cls, api_key_value: str) -> Optional['ApiKey']:
        """根据API密钥值获取"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        try:
            async with db_adapter.get_session() as db:
                maim_db_api_key = MaimDbApiKey.get(MaimDbApiKey.api_key == api_key_value)
                return cls(maim_db_api_key)
        except MaimDbApiKey.DoesNotExist:
            return None

    @classmethod
    async def get_by_tenant(cls, tenant_id: str) -> List['ApiKey']:
        """获取租户下的所有API密钥"""
        if not db_adapter:
            raise RuntimeError("数据库适配器未初始化")

        async with db_adapter.get_session() as db:
            api_keys = []
            for maim_db_api_key in MaimDbApiKey.select().where(MaimDbApiKey.tenant_id == tenant_id):
                api_keys.append(cls(maim_db_api_key))
            return api_keys

    def __repr__(self):
        return f"<ApiKey(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


# 导出兼容的枚举
__all__ = [
    'Tenant', 'Agent', 'ApiKey',
    'TenantType', 'TenantStatus', 'AgentStatus', 'ApiKeyStatus',
    'db_adapter'
]