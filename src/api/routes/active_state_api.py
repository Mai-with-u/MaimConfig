"""
Agent活跃状态API路由 - 提供租户-Agent 心跳TTL更新与活跃列表查询
"""

import os
import sys
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

# 注入 maim_db 路径
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "maim_db")
    ),
)

try:
    from maim_db.core import (
        AsyncAgentActiveState,
        AsyncAgent,
        AsyncTenant,
        AgentStatus,
        TenantStatus,
    )

    MAIM_DB_AVAILABLE = True
except ImportError:
    MAIM_DB_AVAILABLE = False

    class AsyncAgentActiveState:  # type: ignore
        pass

    class AsyncAgent:  # type: ignore
        pass

    class AsyncTenant:  # type: ignore
        pass

    class AgentStatus:  # type: ignore
        pass

    class TenantStatus:  # type: ignore
        pass


from src.common.logger import get_logger
from src.utils.response import create_error_response, create_success_response

router = APIRouter()
logger = get_logger(__name__)


class ActiveStateUpdateRequest(BaseModel):
    """心跳/TTL 更新请求"""

    tenant_id: str = Field(..., description="租户ID")
    agent_id: str = Field(..., description="Agent ID")
    ttl_seconds: int = Field(..., gt=0, description="活跃TTL，单位秒，必须为正数")


class ActiveStateResponse(BaseModel):
    """活跃状态响应模型"""

    tenant_id: str
    agent_id: str
    last_seen_at: str
    expires_at: str
    ttl_seconds: int


async def _ensure_tenant_and_agent(tenant_id: str, agent_id: str) -> Optional[str]:
    """校验租户与Agent是否存在且匹配，返回错误消息字符串或None"""
    if not MAIM_DB_AVAILABLE:
        return "maim_db 未正确安装"

    try:
        tenant = await AsyncTenant.get(tenant_id)
        if (
            not tenant
            or getattr(tenant, "status", TenantStatus.ACTIVE) != TenantStatus.ACTIVE
        ):
            return "租户不存在或未激活"

        agent = await AsyncAgent.get(agent_id)
        if not agent:
            return "Agent不存在"
        if agent.tenant_id != tenant_id:
            return "Agent不属于指定租户"
        if getattr(agent, "status", AgentStatus.ACTIVE) == AgentStatus.INACTIVE:
            return "Agent未激活"
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("校验租户/Agent失败: %s", exc)
        return "校验租户或Agent失败"


def _to_response(record: AsyncAgentActiveState) -> ActiveStateResponse:
    return ActiveStateResponse(
        tenant_id=record.tenant_id,
        agent_id=record.agent_id,
        last_seen_at=record.last_seen_at.isoformat() if record.last_seen_at else "",
        expires_at=record.expires_at.isoformat() if record.expires_at else "",
        ttl_seconds=record.ttl_seconds or 0,
    )


@router.put("/agent-activity", summary="更新租户-Agent 的活跃TTL")
async def upsert_agent_activity(request: ActiveStateUpdateRequest):
    start_time = time.time()
    request_id = str(uuid.uuid4())

    if not MAIM_DB_AVAILABLE:
        return create_error_response(
            message="数据库模块不可用",
            error="maim_db未导入",
            error_code="ACTIVITY_001",
            request_id=request_id,
        )

    error_msg = await _ensure_tenant_and_agent(request.tenant_id, request.agent_id)
    if error_msg:
        return create_error_response(
            message=error_msg,
            error="校验失败",
            error_code="ACTIVITY_002",
            request_id=request_id,
        )

    try:
        record = await AsyncAgentActiveState.upsert(
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            ttl_seconds=request.ttl_seconds,
        )

        return create_success_response(
            message="活跃TTL已更新",
            data=_to_response(record),
            request_id=request_id,
            execution_time=time.time() - start_time,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("更新活跃TTL失败: %s", exc)
        return create_error_response(
            message="更新活跃TTL失败",
            error=str(exc),
            error_code="ACTIVITY_003",
            request_id=request_id,
        )


@router.get("/agent-activity", summary="获取所有仍然活跃的租户-Agent 对")
async def list_agent_activity(
    tenant_id: Optional[str] = Query(None, description="可选租户过滤"),
):
    start_time = time.time()
    request_id = str(uuid.uuid4())

    if not MAIM_DB_AVAILABLE:
        return create_error_response(
            message="数据库模块不可用",
            error="maim_db未导入",
            error_code="ACTIVITY_001",
            request_id=request_id,
        )

    try:
        records = await AsyncAgentActiveState.list_active()
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]

        payload: List[ActiveStateResponse] = [
            _to_response(record) for record in records
        ]

        return create_success_response(
            message="活跃租户-Agent 列表获取成功",
            data={"items": payload, "count": len(payload)},
            request_id=request_id,
            execution_time=time.time() - start_time,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("获取活跃租户-Agent 列表失败: %s", exc)
        return create_error_response(
            message="获取活跃列表失败",
            error=str(exc),
            error_code="ACTIVITY_004",
            request_id=request_id,
        )
