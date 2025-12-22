"""
MaiMBot API Server 主入口文件
独立后端服务，提供多租户AI聊天机器人配置和管理功能
"""

import time
import os
from dotenv import load_dotenv
load_dotenv()
print(f"DEBUG MAIMCONFIG DB URL: {os.getenv('DATABASE_URL')}", flush=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    tenant_router,
    agent_router,
    api_key_router,
    auth_router,
    active_state_router,
    plugin_router,
    usage_router,
)
from src.database.connection import init_database, close_database
from src.database.models import create_tables
from src.common.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("MaiMBot API Server 正在启动...")

    try:
        # 初始化数据库连接
        init_database()
        logger.info("数据库连接初始化完成")

        # 创建数据库表
        await create_tables()
        logger.info("数据库表创建完成")

        logger.info("MaiMBot API Server 启动完成")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise

    yield

    # 关闭时执行
    logger.info("MaiMBot API Server 正在关闭...")
    try:
        # 关闭数据库连接
        close_database()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    """
    app = FastAPI(
        title="MaiMBot API",
        description="多租户AI聊天机器人配置和管理API服务",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境中应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册API路由
    app.include_router(tenant_router, prefix="/api/v2", tags=["租户管理"])
    app.include_router(agent_router, prefix="/api/v2", tags=["Agent管理"])
    app.include_router(api_key_router, prefix="/api/v2", tags=["API密钥管理"])
    app.include_router(auth_router, prefix="/api/v2", tags=["API密钥认证"])
    app.include_router(active_state_router, prefix="/api/v2", tags=["Agent活跃状态"])
    app.include_router(plugin_router, prefix="/api/v1", tags=["插件配置管理"])
    app.include_router(usage_router, prefix="/api/v1", tags=["使用日志"])

    # 根路径
    @app.get("/")
    async def root():
        """API根路径"""
        return {
            "message": "MaiMBot API Server",
            "version": "1.0.0",
            "description": "多租户AI聊天机器人配置和管理API服务",
            "endpoints": {
                "tenants": "/api/v2/tenants",
                "agents": "/api/v2/agents",
                "api_keys": "/api/v2/api-keys",
                "auth": "/api/v2/auth",
                "docs": "/docs",
                "redoc": "/redoc",
            },
            "features": [
                "多租户隔离",
                "Agent配置管理",
                "API密钥管理",
                "API密钥认证",
                "内部服务架构",
            ],
        }

    # 健康检查
    @app.get("/health")
    async def health_check():
        """健康检查接口"""
        try:
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "services": {"database": "healthy", "api": "healthy"},
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="服务不健康"
            ) from None

    # API信息
    @app.get("/info")
    async def api_info():
        """API信息接口"""
        return {
            "name": "MaiMBot API",
            "description": "多租户AI聊天机器人配置和管理API服务",
            "version": "1.0.0",
            "architecture": {
                "isolation_levels": ["tenant", "agent", "platform"],
                "auth_mode": "internal_service",
                "database": "mysql",
            },
            "supported_features": [
                "租户管理",
                "Agent配置管理",
                "API密钥管理",
                "API密钥认证",
                "多租户隔离",
            ],
        }

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # 从环境变量获取端口，默认8000
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    # 开发环境配置
    uvicorn.run("main:app", host=host, port=port, reload=True, log_level="info", reload_excludes=[".git", ".venv", ".idea"])
