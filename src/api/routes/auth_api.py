"""
API密钥认证路由
"""

import time
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from src.database.connection import get_db
from src.database.models import ApiKey, ApiKeyStatus
from src.utils.response import create_success_response, create_error_response
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ApiKeyParseRequest(BaseModel):
    """API密钥解析请求模型"""
    api_key: str


class ApiKeyValidateRequest(BaseModel):
    """API密钥验证请求模型"""
    api_key: str
    required_permission: Optional[str] = None
    check_rate_limit: Optional[bool] = True


class ApiKeyPermissionRequest(BaseModel):
    """API密钥权限检查请求模型"""
    api_key: str
    permission: str


async def parse_api_key(api_key: str) -> Optional[dict]:
    """解析API密钥"""
    try:
        import base64

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


@router.post("/auth/parse-api-key", summary="解析API密钥")
async def parse_api_key_endpoint(
    request: ApiKeyParseRequest,
    db: AsyncSession = Depends(get_db)
):
    """解析API密钥获取租户和Agent信息"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        parsed_info = await parse_api_key(request.api_key)

        if not parsed_info:
            return create_error_response(
                message="API密钥格式无效",
                error="API密钥格式不正确",
                error_code="AUTH_001",
                request_id=request_id
            )

        execution_time = time.time() - start_time
        return create_success_response(
            message="API密钥解析成功",
            data=parsed_info,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"解析API密钥失败: {e}")
        return create_error_response(
            message="解析API密钥失败",
            error=str(e),
            error_code="AUTH_PARSE_ERROR",
            request_id=request_id
        )


@router.post("/auth/validate-api-key", summary="验证API密钥")
async def validate_api_key(
    request: ApiKeyValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """验证API密钥的有效性和权限"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 解析API密钥
        parsed_info = await parse_api_key(request.api_key)

        if not parsed_info:
            return create_error_response(
                message="API密钥格式无效",
                error="API密钥格式不正确",
                error_code="AUTH_001",
                request_id=request_id
            )

        # 查询API密钥
        result = await db.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.api_key == request.api_key,
                    ApiKey.tenant_id == parsed_info["tenant_id"],
                    ApiKey.agent_id == parsed_info["agent_id"]
                )
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return create_error_response(
                message="API密钥不存在",
                error="指定的API密钥不存在",
                error_code="AUTH_005",
                request_id=request_id
            )

        # 检查API密钥状态
        if api_key.status == ApiKeyStatus.DISABLED:
            return create_error_response(
                message="API密钥已禁用",
                error="API密钥已被禁用",
                error_code="AUTH_004",
                request_id=request_id
            )

        if api_key.status == ApiKeyStatus.EXPIRED:
            return create_error_response(
                message="API密钥已过期",
                error="API密钥已过期",
                error_code="AUTH_002",
                request_id=request_id
            )

        # 检查过期时间
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            # 更新状态为已过期
            api_key.status = ApiKeyStatus.EXPIRED
            await db.commit()

            return create_error_response(
                message="API密钥已过期",
                error="API密钥已过期",
                error_code="AUTH_002",
                request_id=request_id
            )

        # 检查权限
        has_permission = True
        if request.required_permission:
            has_permission = request.required_permission in api_key.permissions

        # 更新使用统计
        if request.check_rate_limit:
            api_key.last_used_at = datetime.utcnow()
            api_key.usage_count += 1
            await db.commit()

        execution_time = time.time() - start_time
        return create_success_response(
            message="API密钥验证成功",
            data={
                "valid": True,
                "tenant_id": api_key.tenant_id,
                "agent_id": api_key.agent_id,
                "api_key_id": api_key.id,
                "permissions": api_key.permissions,
                "has_permission": has_permission,
                "status": api_key.status
            },
            tenant_id=api_key.tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"验证API密钥失败: {e}")
        return create_error_response(
            message="验证API密钥失败",
            error=str(e),
            error_code="AUTH_VALIDATE_ERROR",
            request_id=request_id
        )


@router.post("/auth/check-permission", summary="检查权限")
async def check_permission(
    request: ApiKeyPermissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """检查API密钥是否具有指定权限"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # 解析API密钥
        parsed_info = await parse_api_key(request.api_key)

        if not parsed_info:
            return create_error_response(
                message="API密钥格式无效",
                error="API密钥格式不正确",
                error_code="AUTH_001",
                request_id=request_id
            )

        # 查询API密钥
        result = await db.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.api_key == request.api_key,
                    ApiKey.tenant_id == parsed_info["tenant_id"],
                    ApiKey.agent_id == parsed_info["agent_id"]
                )
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return create_error_response(
                message="API密钥不存在",
                error="指定的API密钥不存在",
                error_code="AUTH_005",
                request_id=request_id
            )

        # 检查API密钥状态
        if api_key.status != ApiKeyStatus.ACTIVE:
            status_text = {
                ApiKeyStatus.DISABLED: "已禁用",
                ApiKeyStatus.EXPIRED: "已过期"
            }.get(api_key.status, "状态异常")

            return create_error_response(
                message="API密钥不可用",
                error=f"API密钥{status_text}",
                error_code="AUTH_004",
                request_id=request_id
            )

        # 检查过期时间
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return create_error_response(
                message="API密钥已过期",
                error="API密钥已过期",
                error_code="AUTH_002",
                request_id=request_id
            )

        # 检查权限
        has_permission = request.permission in api_key.permissions

        execution_time = time.time() - start_time
        return create_success_response(
            message="权限检查完成",
            data={
                "has_permission": has_permission,
                "permission": request.permission,
                "all_permissions": api_key.permissions,
                "tenant_id": api_key.tenant_id,
                "agent_id": api_key.agent_id,
                "api_key_status": api_key.status
            },
            tenant_id=api_key.tenant_id,
            execution_time=execution_time,
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"检查权限失败: {e}")
        return create_error_response(
            message="检查权限失败",
            error=str(e),
            error_code="AUTH_PERMISSION_ERROR",
            request_id=request_id
        )