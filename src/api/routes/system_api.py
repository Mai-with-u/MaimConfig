"""
系统级API路由
提供系统默认配置、模型列表等全局信息
"""

import time
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter
from src.utils.response import create_success_response, create_error_response
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# 定义系统默认模型列表
# 这些是服务端预设的、可以直接使用的模型配置
SYSTEM_DEFAULT_PROVIDERS = [
    {
        "name": "OpenAI",
        "client_type": "openai",
        "base_url": "https://api.openai.com/v1",
        "is_server_provider": True,
        # api_key is handled by server env or global config, usually not exposed here or needed for client if it's a proxy
        # But for this hybrid design, if the user selects a system provider, they might expect the server to use its own key.
        # Here we just list them as available options.
    },
    {
        "name": "Anthropic",
        "client_type": "anthropic",
        "base_url": "https://api.anthropic.com",
        "is_server_provider": True,
    }
]

SYSTEM_DEFAULT_MODELS = [
    {
        "name": "GPT-4o",
        "model_identifier": "gpt-4o",
        "api_provider": "OpenAI",
        "description": "OpenAI's most advanced model",
        "price_in": 5.0,
        "price_out": 15.0
    },
    {
        "name": "GPT-4o Mini",
        "model_identifier": "gpt-4o-mini",
        "api_provider": "OpenAI",
        "description": "Affordable and fast model",
        "price_in": 0.15,
        "price_out": 0.6
    },
    {
        "name": "Claude 3.5 Sonnet",
        "model_identifier": "claude-3-5-sonnet-20240620",
        "api_provider": "Anthropic",
        "description": "Anthropic's latest intelligent model",
        "price_in": 3.0,
        "price_out": 15.0
    }
]

import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # For older python versions if needed

# ... existing CONSTANTS ...

def load_system_models_from_toml() -> Dict[str, List[Any]]:
    """
    Load system models from MaiMBot's model_config.toml
    """
    try:
        # 1. Determine Path
        toml_path = os.getenv("MAIMBOT_MODEL_CONFIG_PATH", "/home/tcmofashi/proj/MaiMBot/config/model_config.toml")
        
        if not os.path.exists(toml_path):
            logger.warning(f"Model config file not found at {toml_path}, using defaults.")
            return None

        # 2. Parse TOML
        with open(toml_path, "rb") as f:
            config = tomllib.load(f)

        # 3. Map Providers
        providers = []
        if "api_providers" in config:
            for p in config["api_providers"]:
                # Only expose necessary fields safely
                providers.append({
                    "name": p.get("name", "Unknown Provider"),
                    "client_type": p.get("client_type", "openai"),
                    "base_url": p.get("base_url", ""),
                    "is_server_provider": True  # Mark as system provided
                })

        # 4. Map Models
        models = []
        if "models" in config:
            for m in config["models"]:
                models.append({
                    "name": m.get("name", "Unknown Model"),
                    "model_identifier": m.get("model_identifier", ""),
                    "api_provider": m.get("api_provider", ""),
                    "description": m.get("name", ""), # Use name as description if missing
                    "price_in": m.get("price_in", 0.0),
                    "price_out": m.get("price_out", 0.0)
                })

        # 5. Map Default Task Config
        defaults = {}
        if "model_task_config" in config:
            # model_task_config in TOML is like:
            # [model_task_config.planner]
            # model_list = [...]
            # So config["model_task_config"] is a dict: {'planner': {'model_list': ...}}
            defaults = config["model_task_config"]

        return {
            "providers": providers,
            "models": models,
            "defaults": defaults
        }

    except Exception as e:
        logger.error(f"Failed to parse model_config.toml: {e}")
        return None


@router.get("/system/models", summary="获取系统默认模型列表")
async def get_system_models():
    """
    获取系统提供的默认模型和供应商列表
    优先读取 model_config.toml，失败则回退到硬编码默认值
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        # Try dynamic load
        dynamic_data = load_system_models_from_toml()
        
        if dynamic_data:
            data = dynamic_data
            source = "dynamic_toml"
        else:
            # Fallback
            data = {
                "providers": SYSTEM_DEFAULT_PROVIDERS,
                "models": SYSTEM_DEFAULT_MODELS,
                "defaults": {} # No defaults in fallback
            }
            source = "static_fallback"

        response = create_success_response(
            data=data,
            message=f"获取系统模型列表成功 (Source: {source})",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )
        return response

    except Exception as e:
        logger.error(f"获取系统模型列表失败: {str(e)}")
        return create_error_response(
            message="获取系统模型列表失败",
            error=str(e),
            error_code="SYSTEM_001",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )


def load_bot_config_defaults() -> Dict[str, Any]:
    """
    Load bot config defaults from MaiMBot's bot_config_template.toml
    """
    try:
        # Determine Path, prioritising environment variable
        toml_path = os.getenv("MAIMBOT_BOT_CONFIG_TEMPLATE_PATH", "/home/tcmofashi/proj/MaiMBot/template/bot_config_template.toml")
        
        if not os.path.exists(toml_path):
            logger.warning(f"Bot config template file not found at {toml_path}.")
            return None

        # Parse TOML
        with open(toml_path, "rb") as f:
            config = tomllib.load(f)

        # Return the whole config structure, or specific sections if needed.
        # Returning relevant sections for the frontend.
        return {
            "bot": config.get("bot", {}),
            "personality": config.get("personality", {}),
            "chat": config.get("chat", {}),
            "memory": config.get("memory", {}),
            "dream": config.get("dream", {}),
            "jargon": config.get("jargon", {}),
            "tool": config.get("tool", {}),
            "mood": config.get("mood", {}),
            "emoji": config.get("emoji", {}),
            "voice": config.get("voice", {}),
            "message_receive": config.get("message_receive", {}),
            "lpmm_knowledge": config.get("lpmm_knowledge", {}),
            "chinese_typo": config.get("chinese_typo", {}), # Note case sensitivity in TOML vs dict
             # Add other sections as required by the frontend editor
        }

    except Exception as e:
        logger.error(f"Failed to parse bot_config_template.toml: {e}")
        return None


@router.get("/system/bot-defaults", summary="获取Bot默认配置")
async def get_bot_defaults():
    """
    获取bot_config.toml的默认配置 (from template)
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    try:
        data = load_bot_config_defaults()
        
        if data:
            response = create_success_response(
                data=data,
                message="获取Bot默认配置成功",
                request_id=request_id,
                execution_time=time.time() - start_time,
            )
            return response
        else:
             return create_error_response(
                message="获取Bot默认配置失败 (Template not found or parse error)",
                error="Config not loaded",
                error_code="SYSTEM_002",
                request_id=request_id,
                execution_time=time.time() - start_time,
            )

    except Exception as e:
        logger.error(f"获取Bot默认配置失败: {str(e)}")
        return create_error_response(
            message="获取Bot默认配置失败",
            error=str(e),
            error_code="SYSTEM_003",
            request_id=request_id,
            execution_time=time.time() - start_time,
        )
