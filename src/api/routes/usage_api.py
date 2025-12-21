"""
Usage Log API
"""

import time
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from src.utils.response import create_success_response, create_error_response
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class UsageLogRequest(BaseModel):
    """Usage log request model"""
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


@router.post("/usage/log", summary="Record usage log")
async def log_usage(request: UsageLogRequest):
    """Record a usage log entry"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # Currently just log to console/file via logger
        # In a real implementation, this would save to a database
        log_entry = {
            "tenant_id": request.tenant_id,
            "agent_id": request.agent_id,
            "user_id": request.user_id,
            "action": request.action,
            "details": request.details,
            "timestamp": request.timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        logger.info(f"USAGE_LOG: {log_entry}")

        return create_success_response(
            message="Usage log recorded",
            data=log_entry,
            request_id=request_id,
            execution_time=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"Failed to record usage log: {e}")
        return create_error_response(
            message="Failed to record usage log",
            error=str(e),
            error_code="USAGE_LOG_ERROR",
            request_id=request_id,
            execution_time=time.time() - start_time
        )
