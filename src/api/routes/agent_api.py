"""
Agent管理API路由 - 使用maim_db的AgentConfig系统
"""

import time
import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

# 导入maim_db配置管理器
import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "maim_db", "src")
    ),
)

try:
    from maim_db.core import (
        AsyncAgentActiveState,
        AgentConfigManager,
        init_database,
        close_database,
        get_database,
    )
    from maim_db.core.models import AGENT_CONFIG_MODELS
    
    # Import Async wrappers from local models
    from src.database.models import Tenant, Agent as AsyncAgent, AgentStatus

    MAIM_DB_AVAILABLE = True
except ImportError:
    MAIM_DB_AVAILABLE = False

    # 创建占位符类
    class AsyncAgent:
        pass

    class Tenant:
        pass

    class AgentStatus:
        pass

    class AgentConfigManager:
        pass


from src.utils.response import create_success_response, create_error_response
from src.common.logger import get_logger
from src.api.routes.system_api import load_system_models_from_toml, SYSTEM_DEFAULT_PROVIDERS

logger = get_logger(__name__)
router = APIRouter()

def validate_model_config_security(config: Dict[str, Any]):
    """
    Validate that user configuration does not bypass system security controls.
    Rule: Users cannot define custom models using System Providers.
    """
    if not config:
        return

    # Check config_overrides.model.models
    overrides = config.get("config_overrides", {})
    if not overrides:
        return
        
    model_config = overrides.get("model", {})
    user_models = model_config.get("models", [])
    
    if not user_models:
        return

    # Get System Providers
    system_data = load_system_models_from_toml()
    system_providers = set()
    
    if system_data and "providers" in system_data:
        for p in system_data["providers"]:
            system_providers.add(p["name"])
    else:
        # Fallback
        for p in SYSTEM_DEFAULT_PROVIDERS:
            system_providers.add(p["name"])

    # Validate
    for m in user_models:
        provider = m.get("api_provider")
        if provider in system_providers:
            raise ValueError(f"Security Violation: Cannot use system provider '{provider}' for custom model '{m.get('name')}'. Please use system models directly.")


class AgentCreateRequest(BaseModel):
    """创建Agent请求模型"""

    tenant_id: str
    name: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tags: Optional[list] = None


class AgentUpdateRequest(BaseModel):
    """更新Agent请求模型"""

    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[AgentStatus] = None
    tags: Optional[list] = None


class AgentResponse(BaseModel):
    """Agent响应模型"""

    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: AgentStatus
    created_at: str
    updated_at: str
    tags: Optional[list] = None


class AgentListRequest(BaseModel):
    """Agent列表查询参数"""

    tenant_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[AgentStatus] = None


async def generate_agent_id() -> str:
    """生成Agent ID"""
    return f"agent_{uuid.uuid4().hex[:12]}"


def agent_to_response(
    agent: AsyncAgent, config_manager: AgentConfigManager = None
) -> AgentResponse:
    """将Agent模型转换为响应模型"""
    # 获取配置
    config = None
    if config_manager:
        try:
            config = config_manager.get_all_configs(mask_secrets=True)
        except Exception as e:
            logger.error(f"获取Agent配置失败: {e}")
            config = None

    return AgentResponse(
        id=agent.id,
        tenant_id=agent.tenant_id,
        name=agent.name,
        description=agent.description,
        template_id=agent.template_id,
        config=config,
        status=agent.status,
        created_at=agent.created_at.isoformat() if agent.created_at else "",
        updated_at=agent.updated_at.isoformat() if agent.updated_at else "",
        tags=None,  # TODO: 从config中获取tags
    )


async def check_tenant_exists(tenant_id: str) -> bool:
    """检查租户是否存在"""
    if not MAIM_DB_AVAILABLE:
        return True  # 占位符实现
    try:
        tenant = await Tenant.get(tenant_id)
        return tenant is not None
    except Exception as e:
        logger.error(f"检查租户失败: {e}")
        return False


@router.post("/agents", summary="创建Agent")
async def create_agent(request: AgentCreateRequest):
    """创建新的Agent"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 验证租户是否存在
        if not await check_tenant_exists(request.tenant_id):
            return create_error_response(
                message="租户不存在",
                error="指定的租户ID无效",
                error_code="AGENT_001",
                request_id=request_id,
            )

        # 检查Agent名称是否已存在（在同一租户下）
        if MAIM_DB_AVAILABLE:
            existing_agents = await AsyncAgent.get_by_tenant(request.tenant_id)
            for existing_agent in existing_agents:
                if existing_agent.name == request.name:
                    return create_error_response(
                        message="Agent名称在该租户下已存在",
                        error="Agent名称重复",
                        error_code="AGENT_002",
                        request_id=request_id,
                    )

        # 验证配置安全性
        if request.config:
            try:
                validate_model_config_security(request.config)
            except ValueError as e:
                return create_error_response(
                    message="配置验证失败",
                    error=str(e),
                    error_code="AGENT_011",
                    request_id=request_id,
                )

        # 创建Agent
        agent = await AsyncAgent.create(
            id=await generate_agent_id(),
            tenant_id=request.tenant_id,
            name=request.name,
            description=request.description,
            template_id=request.template_id,
            config=request.config or {},
            status=AgentStatus.ACTIVE.value,
        )

        # 创建后标记为活跃（TTL 12 小时）
        try:
            await AsyncAgentActiveState.upsert(
                request.tenant_id, agent.id, ttl_seconds=12 * 3600
            )
        except Exception as e:
            logger.warning(f"标记Agent活跃失败: {e}")

        # 创建配置管理器并保存配置
        config_manager = AgentConfigManager(agent.id)
        # Config already validated above
        if request.config:
            try:
                config_manager.update_config_from_json(request.config)
            except Exception as e:
                logger.error(f"保存Agent配置失败: {e}")
                # 配置保存失败不影响Agent创建

        logger.info(f"创建Agent成功: {agent.id}, 名称: {agent.name}")

        # 返回包含配置的完整Agent信息
        return create_success_response(
            data=agent_to_response(agent, config_manager),
            message="Agent创建成功",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"创建Agent失败: {str(e)}")
        return create_error_response(
            message="创建Agent失败",
            error=str(e),
            error_code="AGENT_003",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )


@router.get("/agents/{agent_id}", summary="获取Agent详情")
async def get_agent(agent_id: str):
    """获取指定Agent的详细信息"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        agent = await AsyncAgent.get(agent_id)
        if not agent:
            return create_error_response(
                message="Agent不存在",
                error="未找到指定的Agent",
                error_code="AGENT_004",
                request_id=request_id,
            )

        # 获取配置管理器和完整配置
        config_manager = AgentConfigManager(agent_id)

        return create_success_response(
            data=agent_to_response(agent, config_manager),
            message="获取Agent成功",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"获取Agent失败: {str(e)}")
        return create_error_response(
            message="获取Agent失败",
            error=str(e),
            error_code="AGENT_005",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )


@router.get("/agents", summary="获取Agent列表")
async def list_agents(
    tenant_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[AgentStatus] = Query(None, description="Agent状态筛选"),
):
    """获取Agent列表"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 验证租户是否存在
        if not await check_tenant_exists(tenant_id):
            return create_error_response(
                message="租户不存在",
                error="指定的租户ID无效",
                error_code="AGENT_001",
                request_id=request_id,
            )

        offset = (page - 1) * size
        agents = await AsyncAgent.get_by_tenant(tenant_id)

        # 状态筛选
        if status:
            filtered_agents = []
            for agent in agents:
                if agent.status == status.value:
                    filtered_agents.append(agent)
            agents = filtered_agents

        # 分页处理
        total = len(agents)
        start_idx = min(offset, total)
        end_idx = min(offset + size, total)
        paginated_agents = agents[start_idx:end_idx]

        agent_list = []
        config_manager = None
        for agent in paginated_agents:
            if not config_manager or config_manager.agent_id != agent.id:
                config_manager = AgentConfigManager(agent.id)
            agent_list.append(agent_to_response(agent, config_manager))

        return create_success_response(
            data={
                "items": agent_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            },
            message="获取Agent列表成功",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"获取Agent列表失败: {str(e)}")
        return create_error_response(
            message="获取Agent列表失败",
            error=str(e),
            error_code="AGENT_006",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )


@router.put("/agents/{agent_id}", summary="更新Agent")
async def update_agent(agent_id: str, request: AgentUpdateRequest):
    """更新Agent信息"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        agent = await AsyncAgent.get(agent_id)
        if not agent:
            return create_error_response(
                message="Agent不存在",
                error="未找到指定的Agent",
                error_code="AGENT_004",
                request_id=request_id,
            )

        # 准备更新数据
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.status is not None:
            update_data["status"] = request.status.value
        
        if request.config is not None:
            # 验证配置安全性
            try:
                validate_model_config_security(request.config)
            except ValueError as e:
                return create_error_response(
                    message="配置验证失败",
                    error=str(e),
                    error_code="AGENT_011",
                    request_id=request_id,
                )
            update_data["config"] = request.config

        # 执行更新
        await agent.update(**update_data)

        # 更新配置
        if request.config is not None:
            config_manager = AgentConfigManager(agent_id)
            try:
                config_manager.update_config_from_json(request.config)
            except Exception as e:
                logger.error(f"更新Agent配置失败: {e}")
                # 配置更新失败不影响基本信息更新

        logger.info(f"更新Agent成功: {agent_id}")

        # 获取更新后的完整配置
        config_manager = AgentConfigManager(agent_id)

        return create_success_response(
            data=agent_to_response(agent, config_manager),
            message="Agent更新成功",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"更新Agent失败: {str(e)}")
        return create_error_response(
            message="更新Agent失败",
            error=str(e),
            error_code="AGENT_007",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )


@router.delete("/agents/{agent_id}", summary="删除Agent")
async def delete_agent(agent_id: str):
    """删除Agent"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        agent = await AsyncAgent.get(agent_id)
        if not agent:
            return create_error_response(
                message="Agent不存在",
                error="未找到指定的Agent",
                error_code="AGENT_004",
                request_id=request_id,
            )

        # 删除配置
        config_manager = AgentConfigManager(agent_id)
        try:
            config_manager.delete_all_configs()
        except Exception as e:
            logger.error(f"删除Agent配置失败: {e}")
            # 配置删除失败不影响Agent删除

        # 删除Agent
        await agent.delete()

        logger.info(f"删除Agent成功: {agent_id}")

        return create_success_response(
            data={"id": agent_id},
            message="Agent删除成功",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"删除Agent失败: {str(e)}")
        return create_error_response(
            message="删除Agent失败",
            error=str(e),
            error_code="AGENT_008",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )


@router.get("/agents/{agent_id}/config", summary="获取Agent配置")
async def get_agent_config(agent_id: str):
    """获取Agent的详细配置"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 验证Agent是否存在
        agent = await AsyncAgent.get(agent_id)
        if not agent:
            return create_error_response(
                message="Agent不存在",
                error="未找到指定的Agent",
                error_code="AGENT_004",
                request_id=request_id,
            )

        # 获取完整配置
        config_manager = AgentConfigManager(agent_id)
        config = config_manager.get_all_configs(mask_secrets=True)

        return create_success_response(
            data=config,
            message="获取Agent配置成功",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"获取Agent配置失败: {str(e)}")
        return create_error_response(
            message="获取Agent配置失败",
            error=str(e),
            error_code="AGENT_009",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )


@router.put("/agents/{agent_id}/config", summary="更新Agent配置")
async def update_agent_config(agent_id: str, config_data: Dict[str, Any]):
    """更新Agent配置"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 验证Agent是否存在
        agent = await AsyncAgent.get(agent_id)
        if not agent:
            return create_error_response(
                message="Agent不存在",
                error="未找到指定的Agent",
                error_code="AGENT_004",
                request_id=request_id,
            )

        # 验证配置安全性
        try:
            validate_model_config_security(config_data)
        except ValueError as e:
            return create_error_response(
                message="配置验证失败",
                error=str(e),
                error_code="AGENT_011",
                request_id=request_id,
            )

        # 更新配置
        config_manager = AgentConfigManager(agent_id)
        config_manager.update_config_from_json(config_data)

        logger.info(f"更新Agent配置成功: {agent_id}")

        # 返回更新后的完整配置
        updated_config = config_manager.get_all_configs(mask_secrets=True)

        return create_success_response(
            data=updated_config,
            message="Agent配置更新成功",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"更新Agent配置失败: {str(e)}")
        return create_error_response(
            message="更新Agent配置失败",
            error=str(e),
            error_code="AGENT_010",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )
