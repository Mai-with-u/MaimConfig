"""
应用配置管理
"""

import os
import sys
from pydantic_settings import BaseSettings
from pydantic import Field

# 添加maim_db路径到系统路径
maim_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'maim_db')
if maim_db_path not in sys.path:
    sys.path.insert(0, maim_db_path)


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置 - 使用maim_db配置
    database_url: str = Field(
        default="sqlite:///data/MaiBot.db",
        env="DATABASE_URL"
    )
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=3306, env="DATABASE_PORT")
    database_name: str = Field(default="maimbot_api", env="DATABASE_NAME")
    database_user: str = Field(default="username", env="DATABASE_USER")
    database_password: str = Field(default="password", env="DATABASE_PASSWORD")

    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")

    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # API配置
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    api_v2_prefix: str = Field(default="/api/v2", env="API_V2_PREFIX")

    # 安全配置
    secret_key: str = Field(
        default="your-secret-key-here",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # 应用配置
    app_name: str = Field(default="MaiMBot API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
# 创建全局配置实例
settings = Settings()