"""
API密钥管理API路由
"""

import time
import uuid
import base64
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from src.database.connection import get_db
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


async def parse_api_key(api_key: str) -> Optional[dict]:
    """解析API密钥"""
    try:
        if not api_key.startswith("mmc_"):
            return None

        encoded_key = api_key[4:]  # 去掉 "mmc_" 前缀
        decoded_data = base64.b64decode(encoded_key).decode()
        parts = decoded_data.split("_")

        if len(parts) >= 4:
            return {
                "tenant_id": parts[0],
                "agent_id": parts[1],
                "random_hash": parts[2],
                "version": parts[3],
                "format_valid": True
            }
    except Exception:
        pass

    return None


async def generate_api_key_id() -> str:
    """生成API密钥ID"""
    return f"key_{uuid.uuid4().hex[:12]}"


@router.post("/api-keys", summary="创建API密钥")
async def create_api_key(
    request: ApiKeyCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """为指定Agent创建新的API密钥"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 验证租户是否存在
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == request.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            return create_error_response(
                message="租户不存在",
                error="指定的租户ID不存在",
                error_code="TENANT_001",
                request_id=request_id
            )

        # 验证Agent是否存在且属于指定租户
        agent_result = await db.execute(
            select(Agent).where(
                and_(
                    Agent.id == request.agent_id,
                    Agent.tenant_id == request.tenant_id
                )
            )
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            return create_error_response(
                message="Agent不存在或不属于指定租户",
                error="指定的Agent ID不存在或权限不匹配",
                error_code="AGENT_001",
                request_id=request_id
            )

        # 检查API密钥名称是否在租户内重复
        existing_key = await db.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.tenant_id == request.tenant_id,
                    ApiKey.name == request.name
                )
            )
        )
        if existing_key.scalar_one_or_none():
            return create_error_response(
                message="API密钥名称在租户内已存在",
                error="API密钥名称重复",
                error_code="KEY_002",
                request_id=request_id
            )

        # 生成API密钥
        api_key_value = await generate_api_key(request.tenant_id, request.agent_id)

        # 创建API密钥记录
        api_key = ApiKey(
            id=await generate_api_key_id(),
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            api_key=api_key_value,
            permissions=request.permissions,
            status=ApiKeyStatus.ACTIVE,
            expires_at=request.expires_at
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

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
        await db.rollback()
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
    status: Optional[ApiKeyStatus] = Query(None, description="密钥状态过滤"),
    db: AsyncSession = Depends(get_db)
):
    """获取指定租户的API密钥列表"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 构建查询条件
        conditions = [ApiKey.tenant_id == tenant_id]
        if agent_id:
            conditions.append(ApiKey.agent_id == agent_id)
        if status:
            conditions.append(ApiKey.status == status)

        # 查询总数
        count_query = select(func.count(ApiKey.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        if total == 0:
            pagination = calculate_pagination(page, page_size, 0)
            return create_success_response(
                message="获取API密钥列表成功",
                data={
                    "items": [],
                    "pagination": pagination.model_dump()
                },
                tenant_id=tenant_id,
                execution_time=time.time() - start_time,
                request_id=request_id
            )

        # 查询API密钥列表
        query = select(ApiKey).where(and_(*conditions))
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(ApiKey.created_at.desc())

        result = await db.execute(query)
        api_keys = result.scalars().all()

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
    api_key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取指定API密钥的详细信息"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 查询API密钥
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == api_key_id)
        )
        api_key = result.scalar_one_or_none()

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
    request: ApiKeyUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新API密钥的配置"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 查询API密钥
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == api_key_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return create_error_response(
                message="API密钥不存在",
                error="指定的API密钥ID不存在",
                error_code="KEY_001",
                request_id=request_id
            )

        # 如果更新API密钥名称，检查名称是否重复
        if request.name and request.name != api_key.name:
            existing_key = await db.execute(
                select(ApiKey).where(
                    and_(
                        ApiKey.tenant_id == api_key.tenant_id,
                        ApiKey.name == request.name,
                        ApiKey.id != api_key_id
                    )
                )
            )
            if existing_key.scalar_one_or_none():
                return create_error_response(
                    message="API密钥名称在租户内已存在",
                    error="API密钥名称重复",
                    error_code="KEY_002",
                    request_id=request_id
                )

        # 更新API密钥信息
        if request.name is not None:
            api_key.name = request.name
        if request.description is not None:
            api_key.description = request.description
        if request.permissions is not None:
            api_key.permissions = request.permissions
        if request.expires_at is not None:
            api_key.expires_at = request.expires_at

        await db.commit()

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
        await db.rollback()
        logger.error(f"更新API密钥失败: {e}")
        return create_error_response(
            message="更新API密钥失败",
            error=str(e),
            error_code="KEY_UPDATE_ERROR",
            request_id=request_id
        )


@router.post("/api-keys/{api_key_id}/disable", summary="禁用API密钥")
async def disable_api_key(
    api_key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """临时禁用API密钥"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 查询API密钥
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == api_key_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return create_error_response(
                message="API密钥不存在",
                error="指定的API密钥ID不存在",
                error_code="KEY_001",
                request_id=request_id
            )

        # 禁用API密钥
        api_key.status = ApiKeyStatus.DISABLED
        await db.commit()

        execution_time = time.time() - start_time
        return create_success_response(
            message="API密钥已禁用",
            data={
                "api_key_id": api_key.id,
                "status": api_key.status,
                "disabled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            tenant_id=api_key.tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"禁用API密钥失败: {e}")
        return create_error_response(
            message="禁用API密钥失败",
            error=str(e),
            error_code="KEY_DISABLE_ERROR",
            request_id=request_id
        )


@router.delete("/api-keys/{api_key_id}", summary="删除API密钥")
async def delete_api_key(
    api_key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """永久删除API密钥（不可恢复）"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 查询API密钥
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == api_key_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return create_error_response(
                message="API密钥不存在",
                error="指定的API密钥ID不存在",
                error_code="KEY_001",
                request_id=request_id
            )

        # 删除API密钥
        await db.delete(api_key)
        await db.commit()

        execution_time = time.time() - start_time
        return create_success_response(
            message="API密钥删除成功",
            data={
                "api_key_id": api_key_id,
                "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            tenant_id=api_key.tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"删除API密钥失败: {e}")
        return create_error_response(
            message="删除API密钥失败",
            error=str(e),
            error_code="KEY_DELETE_ERROR",
            request_id=request_id
        )