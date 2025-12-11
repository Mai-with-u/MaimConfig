"""
API密钥管理API路由
"""

import time
import uuid
import base64
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

# Remove SQLAlchemy dependencies and get_db
from src.database.models import ApiKey, Agent, Tenant, ApiKeyStatus
from src.utils.response import (
    create_success_response,
    create_error_response,
    calculate_pagination
)
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ApiKeyCreateRequest(BaseModel):
    """创建API密钥请求模型"""
    tenant_id: str
    agent_id: str
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    expires_at: Optional[datetime] = None


class ApiKeyUpdateRequest(BaseModel):
    """更新API密钥请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


async def generate_api_key(tenant_id: str, agent_id: str, version: str = "v1") -> str:
    """生成API密钥"""
    random_hash = uuid.uuid4().hex[:16]
    key_data = f"{tenant_id}_{agent_id}_{random_hash}_{version}"
    encoded_key = base64.b64encode(key_data.encode()).decode()
    return f"mmc_{encoded_key}"


async def generate_api_key_id() -> str:
    """生成API密钥ID"""
    return f"key_{uuid.uuid4().hex[:12]}"


@router.post("/api-keys", summary="创建API密钥")
async def create_api_key(
    request: ApiKeyCreateRequest
):
    """为指定Agent创建新的API密钥"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 验证租户是否存在
        tenant = await Tenant.get(request.tenant_id)
        if not tenant:
            return create_error_response(
                message="租户不存在",
                error="指定的租户ID不存在",
                error_code="TENANT_001",
                request_id=request_id
            )

        # 验证Agent是否存在且属于指定租户
        agent = await Agent.get(request.agent_id)
        if not agent or agent.tenant_id != request.tenant_id:
            return create_error_response(
                message="Agent不存在或不属于指定租户",
                error="指定的Agent ID不存在或权限不匹配",
                error_code="AGENT_001",
                request_id=request_id
            )

        # 检查API密钥名称是否在租户内重复
        existing_key = await ApiKey.get_by_tenant_and_name(request.tenant_id, request.name)
        if existing_key:
            return create_error_response(
                message="API密钥名称在租户内已存在",
                error="API密钥名称重复",
                error_code="KEY_002",
                request_id=request_id
            )

        # 生成API密钥
        api_key_value = await generate_api_key(request.tenant_id, request.agent_id)

        # 创建API密钥记录
        api_key = await ApiKey.create(
            id=await generate_api_key_id(),
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            api_key=api_key_value,
            permissions=request.permissions,
            status=ApiKeyStatus.ACTIVE.value,
            expires_at=request.expires_at
        )

        execution_time = time.time() - start_time
        return create_success_response(
            message="API密钥创建成功",
            data={
                "api_key_id": api_key.id,
                "tenant_id": api_key.tenant_id,
                "agent_id": api_key.agent_id,
                "name": api_key.name,
                "description": api_key.description,
                "api_key": api_key.api_key,
                "permissions": api_key.permissions,
                "status": api_key.status,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "created_at": api_key.created_at.isoformat() if api_key.created_at else None
            },
            tenant_id=api_key.tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"创建API密钥失败: {e}")
        return create_error_response(
            message="创建API密钥失败",
            error=str(e),
            error_code="KEY_CREATE_ERROR",
            request_id=request_id
        )


@router.get("/api-keys", summary="获取API密钥列表")
async def list_api_keys(
    tenant_id: str = Query(..., description="租户ID (必需)"),
    agent_id: Optional[str] = Query(None, description="Agent ID (可选)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[ApiKeyStatus] = Query(None, description="密钥状态过滤")
):
    """获取指定租户的API密钥列表"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # Use new list method
        status_val = status.value if status else None
        api_keys, total = await ApiKey.list(
            tenant_id=tenant_id,
            agent_id=agent_id,
            status=status_val,
            page=page,
            page_size=page_size
        )

        # 构建响应数据
        items = []
        for key in api_keys:
            items.append({
                "api_key_id": key.id,
                "tenant_id": key.tenant_id,
                "agent_id": key.agent_id,
                "name": key.name,
                "description": key.description,
                "api_key": key.api_key,
                "permissions": key.permissions,
                "status": key.status,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "usage_count": key.usage_count,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "updated_at": key.updated_at.isoformat() if key.updated_at else None
            })

        pagination = calculate_pagination(page, page_size, total)
        execution_time = time.time() - start_time

        return create_success_response(
            message="获取API密钥列表成功",
            data={
                "items": items,
                "pagination": pagination.model_dump()
            },
            tenant_id=tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"获取API密钥列表失败: {e}")
        return create_error_response(
            message="获取API密钥列表失败",
            error=str(e),
            error_code="KEY_LIST_ERROR",
            request_id=request_id
        )


@router.get("/api-keys/{api_key_id}", summary="获取API密钥详情")
async def get_api_key(
    api_key_id: str
):
    """获取指定API密钥的详细信息"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        api_key = await ApiKey.get(api_key_id)

        if not api_key:
            return create_error_response(
                message="API密钥不存在",
                error="指定的API密钥ID不存在",
                error_code="KEY_001",
                request_id=request_id
            )

        execution_time = time.time() - start_time
        return create_success_response(
            message="获取API密钥详情成功",
            data={
                "api_key_id": api_key.id,
                "tenant_id": api_key.tenant_id,
                "agent_id": api_key.agent_id,
                "name": api_key.name,
                "description": api_key.description,
                "api_key": api_key.api_key,
                "permissions": api_key.permissions,
                "status": api_key.status,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                "usage_count": api_key.usage_count,
                "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
                "updated_at": api_key.updated_at.isoformat() if api_key.updated_at else None
            },
            tenant_id=api_key.tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"获取API密钥详情失败: {e}")
        return create_error_response(
            message="获取API密钥详情失败",
            error=str(e),
            error_code="KEY_GET_ERROR",
            request_id=request_id
        )


@router.put("/api-keys/{api_key_id}", summary="更新API密钥")
async def update_api_key(
    api_key_id: str,
    request: ApiKeyUpdateRequest
):
    """更新API密钥的配置"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        api_key = await ApiKey.get(api_key_id)

        if not api_key:
            return create_error_response(
                message="API密钥不存在",
                error="指定的API密钥ID不存在",
                error_code="KEY_001",
                request_id=request_id
            )

        # 如果更新API密钥名称，检查名称是否重复
        if request.name and request.name != api_key.name:
            existing_key = await ApiKey.get_by_tenant_and_name(api_key.tenant_id, request.name)
            if existing_key and existing_key.id != api_key_id:
                return create_error_response(
                    message="API密钥名称在租户内已存在",
                    error="API密钥名称重复",
                    error_code="KEY_002",
                    request_id=request_id
                )

        # 准备更新数据
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.description is not None:
            update_data['description'] = request.description
        if request.permissions is not None:
            update_data['permissions'] = request.permissions
        if request.expires_at is not None:
            update_data['expires_at'] = request.expires_at

        # 执行更新
        await api_key.update(**update_data)

        execution_time = time.time() - start_time
        return create_success_response(
            message="API密钥更新成功",
            data={
                "api_key_id": api_key.id,
                "updated_at": api_key.updated_at.isoformat() if api_key.updated_at else None
            },
            tenant_id=api_key.tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"更新API密钥失败: {e}")
        return create_error_response(
            message="更新API密钥失败",
            error=str(e),
            error_code="KEY_UPDATE_ERROR",
            request_id=request_id
        )