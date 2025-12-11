"""
数据库连接管理 - 使用maim_db
"""

import sys
import os
import asyncio
import json
from typing import AsyncGenerator

# 添加maim_db路径
maim_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'maim_db', 'src'))
if maim_db_path not in sys.path:
    sys.path.insert(0, maim_db_path)
    print(f"添加maim_db路径: {maim_db_path}")

# 直接从maim_db导入基础模型
try:
    import sys
    sys.path.insert(0, maim_db_path)

    # 直接导入需要使用的模块
    # 直接导入需要使用的模块
    from maim_db.core.models.system_v2 import (
        Tenant as MaimDbTenant,
        Agent as MaimDbAgent,
        ApiKey as MaimDbApiKey,
        TenantType,
        TenantStatus,
        AgentStatus,
        ApiKeyStatus
    )
    from maim_db.core import init_database, close_database, get_database
    from .enums import (
        TenantType as LocalTenantType,
        TenantStatus as LocalTenantStatus,
        AgentStatus as LocalAgentStatus,
        ApiKeyStatus as LocalApiKeyStatus
    )

    MAIM_DB_AVAILABLE = True
    print("✅ maim_db 导入成功")

except ImportError as e:
    print(f"错误: 无法导入maim_db: {e}")
    print(f"maim_db路径: {maim_db_path}")
    MAIM_DB_AVAILABLE = False

    # 创建占位符类
    class MaimDbTenant: pass
    class MaimDbAgent: pass
    class MaimDbApiKey: pass

    class TenantType: pass
    class TenantStatus: pass
    class AgentStatus: pass
    class ApiKeyStatus: pass

    class LocalTenantType: pass
    class LocalTenantStatus: pass
    class LocalAgentStatus: pass
    class LocalApiKeyStatus: pass

    async def init_database(): pass
    async def close_database(): pass
    def get_database(): return None


# Alias for compatibility
get_db = get_database


# 创建异步包装器类
class AsyncTenant:
    @classmethod
    async def create(cls, **kwargs):
        def _create():
            data = {
                'tenant_name': kwargs.get('tenant_name'),
                'tenant_type': kwargs.get('tenant_type', 'personal'),
                'description': kwargs.get('description'),
                'contact_email': kwargs.get('contact_email'),
                'tenant_config': json.dumps(kwargs.get('tenant_config', {})),
                'status': kwargs.get('status', 'active'),
                'owner_id': kwargs.get('owner_id'),
            }

            if 'id' not in kwargs:
                import uuid
                data['id'] = f"tenant_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            tenant = MaimDbTenant(**data)
            tenant.save(force_insert=True)
            return tenant

        tenant = await asyncio.get_event_loop().run_in_executor(None, _create)
        return cls(tenant)

    def __init__(self, maim_db_tenant=None):
        if maim_db_tenant:
            self.id = maim_db_tenant.id
            self.tenant_name = maim_db_tenant.tenant_name
            self.tenant_type = maim_db_tenant.tenant_type
            self.description = maim_db_tenant.description
            self.contact_email = maim_db_tenant.contact_email
            self.tenant_config = self._parse_json(maim_db_tenant.tenant_config)
            self.status = maim_db_tenant.status
            self.owner_id = maim_db_tenant.owner_id
            self.created_at = maim_db_tenant.created_at
            self.updated_at = maim_db_tenant.updated_at
            self._tenant = maim_db_tenant

    def _parse_json(self, json_str):
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except:
            return None

    @classmethod
    async def get(cls, tenant_id):
        def _get():
            try:
                return MaimDbTenant.get_by_id(tenant_id)
            except MaimDbTenant.DoesNotExist:
                return None

        tenant = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(tenant) if tenant else None

    @classmethod
    async def get_by_name(cls, tenant_name):
        def _get():
            try:
                return MaimDbTenant.get(MaimDbTenant.tenant_name == tenant_name)
            except MaimDbTenant.DoesNotExist:
                return None

        tenant = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(tenant) if tenant else None

    @classmethod
    async def get_all(cls, limit=None, offset=0):
        def _get_all():
            query = MaimDbTenant.select()
            if limit:
                query = query.limit(limit).offset(offset)
            return list(query)

        tenants = await asyncio.get_event_loop().run_in_executor(None, _get_all)
        return [cls(tenant) for tenant in tenants]

    @classmethod
    async def count(cls):
        def _count():
            return MaimDbTenant.select().count()

        return await asyncio.get_event_loop().run_in_executor(None, _count)

    async def update(self, **kwargs):
        def _update():
            for field, value in kwargs.items():
                if hasattr(self._tenant, field):
                    if field == 'tenant_config' and value is not None:
                        value = json.dumps(value)
                    setattr(self._tenant, field, value)
            self._tenant.save()
            return self._tenant

        await asyncio.get_event_loop().run_in_executor(None, _update)

        # 更新本地属性
        for field, value in kwargs.items():
            if hasattr(self, field):
                if field == 'tenant_config':
                    value = self._parse_json(json.dumps(value)) if value else None
                setattr(self, field, value)

        return self

    async def delete(self):
        def _delete():
            self._tenant.delete_instance()

        await asyncio.get_event_loop().run_in_executor(None, _delete)


# 简化的Agent和ApiKey类
class AsyncAgent:
    @classmethod
    async def create(cls, **kwargs):
        def _create():
            data = {
                'tenant_id': kwargs.get('tenant_id'),
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'template_id': kwargs.get('template_id'),
                'config': json.dumps(kwargs.get('config', {})),
                'status': kwargs.get('status', 'active'),
            }

            if 'id' not in kwargs:
                import uuid
                data['id'] = f"agent_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            agent = MaimDbAgent(**data)
            agent.save(force_insert=True)
            return agent

        agent = await asyncio.get_event_loop().run_in_executor(None, _create)
        return cls(agent)

    def __init__(self, maim_db_agent=None):
        if maim_db_agent:
            self.id = maim_db_agent.id
            self.tenant_id = maim_db_agent.tenant_id
            self.name = maim_db_agent.name
            self.description = maim_db_agent.description
            self.template_id = maim_db_agent.template_id
            self.config = self._parse_json(maim_db_agent.config)
            self.status = maim_db_agent.status
            self.created_at = maim_db_agent.created_at
            self.updated_at = maim_db_agent.updated_at
            self._agent = maim_db_agent

    def _parse_json(self, json_str):
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except:
            return None

    @classmethod
    async def get(cls, agent_id):
        def _get():
            try:
                return MaimDbAgent.get_by_id(agent_id)
            except MaimDbAgent.DoesNotExist:
                return None

        agent = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(agent) if agent else None

    @classmethod
    async def get_by_tenant(cls, tenant_id):
        def _get_by_tenant():
            agents = MaimDbAgent.select().where(MaimDbAgent.tenant_id == tenant_id)
            return list(agents)

        agents = await asyncio.get_event_loop().run_in_executor(None, _get_by_tenant)
        return [cls(agent) for agent in agents]


class AsyncApiKey:
    @classmethod
    async def create(cls, **kwargs):
        def _create():
            data = {
                'tenant_id': kwargs.get('tenant_id'),
                'agent_id': kwargs.get('agent_id'),
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'api_key': kwargs.get('api_key'),
                'permissions': json.dumps(kwargs.get('permissions', [])),
                'status': kwargs.get('status', 'active'),
                'expires_at': kwargs.get('expires_at'),
            }

            if 'id' not in kwargs:
                import uuid
                data['id'] = f"key_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            api_key = MaimDbApiKey(**data)
            api_key.save(force_insert=True)
            return api_key

        api_key = await asyncio.get_event_loop().run_in_executor(None, _create)
        return cls(api_key)

    def __init__(self, maim_db_api_key=None):
        if maim_db_api_key:
            self.id = maim_db_api_key.id
            self.tenant_id = maim_db_api_key.tenant_id
            self.agent_id = maim_db_api_key.agent_id
            self.name = maim_db_api_key.name
            self.description = maim_db_api_key.description
            self.api_key = maim_db_api_key.api_key
            self.permissions = self._parse_json(maim_db_api_key.permissions)
            self.status = maim_db_api_key.status
            self.expires_at = maim_db_api_key.expires_at
            self.last_used_at = maim_db_api_key.last_used_at
            self.usage_count = maim_db_api_key.usage_count
            self.created_at = maim_db_api_key.created_at
            self.updated_at = maim_db_api_key.updated_at
            self._api_key = maim_db_api_key

    def _parse_json(self, json_str):
        if not json_str:
            return []
        try:
            result = json.loads(json_str)
            return result if isinstance(result, list) else [str(result)]
        except:
            return []

    @classmethod
    async def get(cls, api_key_id):
        def _get():
            try:
                return MaimDbApiKey.get_by_id(api_key_id)
            except MaimDbApiKey.DoesNotExist:
                return None

        api_key = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(api_key) if api_key else None

    @classmethod
    async def get_by_tenant_and_name(cls, tenant_id: str, name: str):
        def _get():
            try:
                return MaimDbApiKey.get(
                    (MaimDbApiKey.tenant_id == tenant_id) & (MaimDbApiKey.name == name)
                )
            except MaimDbApiKey.DoesNotExist:
                return None
        
        api_key = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(api_key) if api_key else None

    @classmethod
    async def list(cls, tenant_id: str, agent_id: str = None, status: str = None, page: int = 1, page_size: int = 20):
        def _list():
            query = MaimDbApiKey.select().where(MaimDbApiKey.tenant_id == tenant_id)
            if agent_id:
                query = query.where(MaimDbApiKey.agent_id == agent_id)
            if status:
                query = query.where(MaimDbApiKey.status == status)
            
            # Count total
            total = query.count()
            
            # Pagination
            query = query.order_by(MaimDbApiKey.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            return list(query), total

        result = await asyncio.get_event_loop().run_in_executor(None, _list)
        keys, total = result
        return [cls(k) for k in keys], total

    async def update(self, **kwargs):
        def _update():
            for field, value in kwargs.items():
                if hasattr(self._api_key, field):
                    if field == 'permissions' and value is not None:
                        value = json.dumps(value)
                    setattr(self._api_key, field, value)
            self._api_key.save()
            return self._api_key

        await asyncio.get_event_loop().run_in_executor(None, _update)

        # Update local attributes
        for field, value in kwargs.items():
            if hasattr(self, field):
                if field == 'permissions':
                    value = self._parse_json(json.dumps(value)) if value else []
                setattr(self, field, value)

        return self

    @classmethod
    async def get_by_key_value(cls, api_key: str, tenant_id: str = None, agent_id: str = None):
        def _get():
            try:
                query = (MaimDbApiKey.api_key == api_key)
                if tenant_id:
                    query &= (MaimDbApiKey.tenant_id == tenant_id)
                if agent_id:
                    query &= (MaimDbApiKey.agent_id == agent_id)
                
                return MaimDbApiKey.get(query)
            except MaimDbApiKey.DoesNotExist:
                return None
        
        api_key_obj = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(api_key_obj) if api_key_obj else None

    async def delete(self):
        def _delete():
            self._api_key.delete_instance()

        await asyncio.get_event_loop().run_in_executor(None, _delete)


# 导出本地枚举（用于Pydantic）
TenantType = LocalTenantType
TenantStatus = LocalTenantStatus
AgentStatus = LocalAgentStatus
ApiKeyStatus = LocalApiKeyStatus


# 导出maim_db的异步模型和函数
__all__ = [
    'AsyncTenant', 'AsyncAgent', 'AsyncApiKey',
    'TenantType', 'TenantStatus', 'AgentStatus', 'ApiKeyStatus',
    'init_database', 'close_database', 'get_database', 'get_db'
]