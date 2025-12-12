from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.database.connection import get_db
from src.common.logger import get_logger
from maim_db.maimconfig_models.models import PluginSettings, Tenant, Agent

logger = get_logger(__name__)
router = APIRouter(prefix="/plugins", tags=["plugins"])

class PluginSettingResponse(BaseModel):
    plugin_name: str
    enabled: bool
    config: Dict[str, Any]

@router.get("/settings", response_model=List[PluginSettingResponse])
async def get_plugin_settings(
    tenant_id: str = Query(..., description="Tenant ID"),
    agent_id: Optional[str] = Query(None, description="Agent ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取指定租户/Agent的插件配置列表"""
    try:
        query = select(PluginSettings).where(PluginSettings.tenant_id == tenant_id)
        
        if agent_id:
            # 如果指定了agent_id，获取该Agent的特定配置以及没有特定Agent的通用配置
            # 这里的逻辑可能需要根据业务调整。简单起见，我们优先匹配 Agent 及其 Tenant 的配置
            # 或者，我们可以约定：PluginSettings表里，agent_id为空表示Tenant全局默认
            # 如果查询带有agent_id，我们应当返回：
            # 1. 该Agent特定的配置
            # 2. 该Tenant全局配置（如果Agent特定的没有覆盖）
            # 当前简化：只返回匹配 tenant_id 和 (agent_id OR null) 的记录
            query = query.where(
                and_(
                    PluginSettings.tenant_id == tenant_id,
                    (PluginSettings.agent_id == agent_id) | (PluginSettings.agent_id.is_(None))
                )
            )
        else:
            # 仅返回 Tenant 全局配置 (agent_id is None)
            query = query.where(PluginSettings.agent_id.is_(None))

        result = await db.execute(query)
        settings = result.scalars().all()
        
        # 转换并处理覆盖逻辑 (Agent 设置覆盖 Tenant 设置)
        # 简单的 Map 处理
        merged_settings: Dict[str, PluginSettings] = {}
        
        for s in settings:
            # 如果字典里已有（说明遇到过），我们需要决定优先级
            # 优先级：Agent特定 > Tenant全局
            # 假设我们按某种顺序或者逻辑处理。
            # 当前逻辑：如果 s.agent_id 存在，它是高优的。
            # 如果 s.agent_id 为 None，它是低优的。
            if s.plugin_name not in merged_settings:
                merged_settings[s.plugin_name] = s
            else:
                existing = merged_settings[s.plugin_name]
                if s.agent_id is not None and existing.agent_id is None:
                    merged_settings[s.plugin_name] = s
        
        return [
            PluginSettingResponse(
                plugin_name=s.plugin_name,
                enabled=s.enabled,
                config=s.config or {}
            )
            for s in merged_settings.values()
        ]

    except Exception as e:
        logger.error(f"获取插件配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings", response_model=PluginSettingResponse)
async def upsert_plugin_setting(
    setting: PluginSettingResponse,
    tenant_id: str = Query(..., description="Tenant ID"),
    agent_id: Optional[str] = Query(None, description="Agent ID"),
    db: AsyncSession = Depends(get_db)
):
    """更新或插入插件配置"""
    try:
        # 查找现有记录
        query = select(PluginSettings).where(
            PluginSettings.tenant_id == tenant_id,
            PluginSettings.plugin_name == setting.plugin_name
        )
        if agent_id:
            query = query.where(PluginSettings.agent_id == agent_id)
        else:
            query = query.where(PluginSettings.agent_id.is_(None))
            
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.enabled = setting.enabled
            existing.config = setting.config
            db_obj = existing
        else:
            db_obj = PluginSettings(
                id=f"ps_{tenant_id}_{agent_id or 'global'}_{setting.plugin_name}", # 简单ID生成
                tenant_id=tenant_id,
                agent_id=agent_id,
                plugin_name=setting.plugin_name,
                enabled=setting.enabled,
                config=setting.config
            )
            db.add(db_obj)
            
        await db.commit()
        await db.refresh(db_obj)
        
        return PluginSettingResponse(
            plugin_name=db_obj.plugin_name,
            enabled=db_obj.enabled,
            config=db_obj.config or {}
        )
        
    except Exception as e:
        logger.error(f"保存插件配置失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
