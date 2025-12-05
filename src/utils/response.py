"""
统一响应格式工具
"""

from typing import Any, Optional, Dict, List
from pydantic import BaseModel
import time
import uuid


class ApiResponse(BaseModel):
    """统一API响应格式"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: str
    request_id: str
    tenant_id: Optional[str] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class PaginationInfo(BaseModel):
    """分页信息"""
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel):
    """分页响应格式"""
    success: bool
    message: str
    data: Dict[str, Any]
    timestamp: str
    request_id: str
    tenant_id: Optional[str] = None
    execution_time: Optional[float] = None


def create_success_response(
    message: str,
    data: Any = None,
    tenant_id: Optional[str] = None,
    execution_time: Optional[float] = None,
    request_id: Optional[str] = None
) -> ApiResponse:
    """创建成功响应"""
    return ApiResponse(
        success=True,
        message=message,
        data=data,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        request_id=request_id or str(uuid.uuid4()),
        tenant_id=tenant_id,
        execution_time=execution_time
    )


def create_error_response(
    message: str,
    error: str = None,
    error_code: str = None,
    tenant_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> ApiResponse:
    """创建错误响应"""
    return ApiResponse(
        success=False,
        message=message,
        error=error,
        error_code=error_code,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        request_id=request_id or str(uuid.uuid4()),
        tenant_id=tenant_id
    )


def create_paginated_response(
    message: str,
    items: List[Any],
    pagination: PaginationInfo,
    tenant_id: Optional[str] = None,
    execution_time: Optional[float] = None,
    request_id: Optional[str] = None
) -> PaginatedResponse:
    """创建分页响应"""
    return PaginatedResponse(
        success=True,
        message=message,
        data={
            "items": items,
            "pagination": pagination.model_dump()
        },
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        request_id=request_id or str(uuid.uuid4()),
        tenant_id=tenant_id,
        execution_time=execution_time
    )


def calculate_pagination(
    page: int,
    page_size: int,
    total: int
) -> PaginationInfo:
    """计算分页信息"""
    total_pages = (total + page_size - 1) // page_size
    return PaginationInfo(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )