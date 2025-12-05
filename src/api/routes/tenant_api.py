"""
租户管理API路由 - 使用maim_db
"""

import time
import uuid
from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.database.models import Tenant, TenantType, TenantStatus
from src.utils.response import (
    create_success_response,
    create_error_response
)
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TenantCreateRequest(BaseModel):
    """创建租户请求模型"""
    tenant_name: str
    tenant_type: TenantType
    description: Optional[str] = None
    contact_email: Optional[str] = None
    tenant_config: Optional[dict] = None


class TenantUpdateRequest(BaseModel):
    """更新租户请求模型"""
    tenant_name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    tenant_config: Optional[dict] = None
    status: Optional[TenantStatus] = None


class TenantResponse(BaseModel):
    """租户响应模型"""
    id: str
    tenant_name: str
    tenant_type: TenantType
    description: Optional[str] = None
    contact_email: Optional[str] = None
    tenant_config: Optional[dict] = None
    status: TenantStatus
    owner_id: Optional[str] = None
    created_at: str
    updated_at: str


async def generate_tenant_id() -> str:
    """生成租户ID"""
    return f"tenant_{uuid.uuid4().hex[:12]}"


def tenant_to_response(tenant: Tenant) -> TenantResponse:
    """将租户模型转换为响应模型"""
    return TenantResponse(
        id=tenant.id,
        tenant_name=tenant.tenant_name,
        tenant_type=tenant.tenant_type,
        description=tenant.description,
        contact_email=tenant.contact_email,
        tenant_config=tenant.tenant_config,
        status=tenant.status,
        owner_id=tenant.owner_id,
        created_at=tenant.created_at.isoformat() if tenant.created_at else "",
        updated_at=tenant.updated_at.isoformat() if tenant.updated_at else ""
    )


@router.post("/tenants", summary="创建租户")
async def create_tenant(request: TenantCreateRequest):
    """创建新的租户"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 检查租户名称是否已存在
        existing_tenant = await Tenant.get_by_name(request.tenant_name)
        if existing_tenant:
            return create_error_response(
                message="租户名称已存在",
                error="租户名称重复",
                error_code="TENANT_002",
                request_id=request_id
            )

        # 创建租户
        tenant = await Tenant.create(
            id=await generate_tenant_id(),
            tenant_name=request.tenant_name,
            tenant_type=request.tenant_type.value,
            description=request.description,
            contact_email=request.contact_email,
            tenant_config=request.tenant_config,
            status=TenantStatus.ACTIVE.value
        )

        logger.info(f"创建租户成功: {tenant.id}, 名称: {tenant.tenant_name}")

        return create_success_response(
            data=tenant_to_response(tenant),
            message="租户创建成功",
            request_id=request_id,
            execution_time=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"创建租户失败: {str(e)}")
        return create_error_response(
            message="创建租户失败",
            error=str(e),
            error_code="TENANT_001",
            request_id=request_id,
            execution_time=time.time() - start_time
        )


@router.get("/tenants/{tenant_id}", summary="获取租户详情")
async def get_tenant(tenant_id: str):
    """获取指定租户的详细信息"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        tenant = await Tenant.get(tenant_id)
        if not tenant:
            return create_error_response(
                message="租户不存在",
                error="未找到指定的租户",
                error_code="TENANT_003",
                request_id=request_id
            )

        return create_success_response(
            data=tenant_to_response(tenant),
            message="获取租户成功",
            request_id=request_id,
            execution_time=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"获取租户失败: {str(e)}")
        return create_error_response(
            message="获取租户失败",
            error=str(e),
            error_code="TENANT_004",
            request_id=request_id,
            execution_time=time.time() - start_time
        )


@router.get("/tenants", summary="获取租户列表")
async def list_tenants(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取租户列表"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        offset = (page - 1) * size
        tenants = await Tenant.get_all(limit=size, offset=offset)
        total = await Tenant.count()

        tenant_list = [tenant_to_response(tenant) for tenant in tenants]

        return create_success_response(
            data={
                "items": tenant_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            message="获取租户列表成功",
            request_id=request_id,
            execution_time=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"获取租户列表失败: {str(e)}")
        return create_error_response(
            message="获取租户列表失败",
            error=str(e),
            error_code="TENANT_005",
            request_id=request_id,
            execution_time=time.time() - start_time
        )


@router.put("/tenants/{tenant_id}", summary="更新租户")
async def update_tenant(
    tenant_id: str,
    request: TenantUpdateRequest
):
    """更新租户信息"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        tenant = await Tenant.get(tenant_id)
        if not tenant:
            return create_error_response(
                message="租户不存在",
                error="未找到指定的租户",
                error_code="TENANT_003",
                request_id=request_id
            )

        # 准备更新数据
        update_data = {}
        if request.tenant_name is not None:
            update_data['tenant_name'] = request.tenant_name
        if request.description is not None:
            update_data['description'] = request.description
        if request.contact_email is not None:
            update_data['contact_email'] = request.contact_email
        if request.tenant_config is not None:
            update_data['tenant_config'] = request.tenant_config
        if request.status is not None:
            update_data['status'] = request.status.value

        # 执行更新
        await tenant.update(**update_data)

        logger.info(f"更新租户成功: {tenant_id}")

        return create_success_response(
            data=tenant_to_response(tenant),
            message="租户更新成功",
            request_id=request_id,
            execution_time=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"更新租户失败: {str(e)}")
        return create_error_response(
            message="更新租户失败",
            error=str(e),
            error_code="TENANT_006",
            request_id=request_id,
            execution_time=time.time() - start_time
        )


@router.delete("/tenants/{tenant_id}", summary="删除租户")
async def delete_tenant(tenant_id: str):
    """删除租户"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        tenant = await Tenant.get(tenant_id)
        if not tenant:
            return create_error_response(
                message="租户不存在",
                error="未找到指定的租户",
                error_code="TENANT_003",
                request_id=request_id
            )

        await tenant.delete()

        logger.info(f"删除租户成功: {tenant_id}")

        return create_success_response(
            data={"id": tenant_id},
            message="租户删除成功",
            request_id=request_id,
            execution_time=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"删除租户失败: {str(e)}")
        return create_error_response(
            message="删除租户失败",
            error=str(e),
            error_code="TENANT_007",
            request_id=request_id,
            execution_time=time.time() - start_time
        )