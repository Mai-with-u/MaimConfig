# MaimConfig API 文档（对齐当前代码）

**基础 URL**：`http://<host>:8000`

**版本前缀**：`/api/v2`（插件配置为 `/api/v1/plugins`）

**认证**：内部服务，无鉴权；请用网络/Ingress 限制访问。

**依赖**：`maim_db`（Peewee 模型 + AgentConfig 管理器）；插件接口依赖 `maim_db.maimconfig_models`（SQLAlchemy，未安装则不可用）。

## 响应格式
成功：
```json
{
  "success": true,
  "message": "...",
  "data": {...},
  "request_id": "<uuid>",
  "execution_time": 0.12
}
```

失败：
```json
{
  "success": false,
  "message": "错误提示",
  "error": "详细错误",
  "error_code": "XXX",
  "request_id": "<uuid>"
}
```

分页（部分接口）：`data.items` + `data.pagination`（page/page_size/total/total_pages/has_next/has_prev）。

枚举：
- TenantType: `personal` / `enterprise`
- TenantStatus: `active` / `inactive` / `suspended`
- AgentStatus: `active` / `inactive` / `archived`
- ApiKeyStatus: `active` / `disabled` / `expired`

## 1. 租户管理（/api/v2）
- **POST /tenants** 创建租户
  - body: `{ tenant_name, tenant_type, description?, contact_email?, tenant_config? }`
- **GET /tenants/{tenant_id}** 租户详情
- **GET /tenants?page&size** 租户列表（分页）
- **PUT /tenants/{tenant_id}** 更新租户
  - body 可选字段：`tenant_name/description/contact_email/tenant_config/status`
- **DELETE /tenants/{tenant_id}** 删除租户

说明：名称去重在服务侧检查；`tenant_config` 以 JSON 存储。

## 2. Agent 管理（/api/v2）
- **POST /agents** 创建 Agent
  - body: `{ tenant_id, name, description?, template_id?, config?, tags? }`
  - 行为：创建成功后调用 `AsyncAgentActiveState.upsert`，默认 TTL 12h。
- **GET /agents/{agent_id}** Agent 详情（含配置）
- **GET /agents?tenant_id=...&page&size&status** Agent 列表（必填 `tenant_id`，内存分页）
- **PUT /agents/{agent_id}** 更新 Agent
  - body 可选字段：`name/description/config/status/tags`
- **DELETE /agents/{agent_id}** 删除 Agent

说明：配置读写通过 `maim_db.core.AgentConfigManager`，存储格式由 maim_db 决定；本服务不校验配置结构。

## 3. API 密钥管理（/api/v2）
- **POST /api-keys** 生成 API Key
  - body: `{ tenant_id, agent_id, name, description?, permissions[], expires_at? }`
  - 生成格式：`mmc_{base64(tenant_id_agent_id_random_version)}`
- **GET /api-keys?tenant_id=...&agent_id?&status?&page&page_size** 列表
- **GET /api-keys/{api_key_id}** 详情
- **PUT /api-keys/{api_key_id}** 更新（名称/描述/权限/过期时间）

说明：名称在租户内唯一；可用 `status` 与 `expires_at` 管控，也支持物理删除。

## 4. API Key 认证（/api/v2）
- **POST /auth/parse-api-key**
  - body: `{ api_key }` → 解析租户/Agent/版本，校验前缀 `mmc_`
- **POST /auth/validate-api-key**
  - body: `{ api_key, required_permission?, check_rate_limit?=true }`
  - 行为：检查格式 → 查询 key → 校验状态/过期 → 可选权限检查 → 若 `check_rate_limit` 为真则自增 `usage_count`、更新 `last_used_at`
- **POST /auth/check-permission**
  - body: `{ api_key, permission }` → 返回是否拥有该权限（不自增计数）

## 5. Agent 活跃状态（/api/v2）
- **PUT /agent-activity**
  - body: `{ tenant_id, agent_id, ttl_seconds>0 }`
  - 行为：校验租户/Agent 存在且激活，调用 `AsyncAgentActiveState.upsert`
- **GET /agent-activity?tenant_id?**
  - 返回仍未过期的租户-Agent 对列表

## 6. 使用日志（/api/v1，注意版本）
- **POST /usage/log** 记录使用日志
  - body: `{ tenant_id?, agent_id?, user_id?, action, details?, timestamp? }`
  - 响应: `{ success: true, data: { ...recorded_entry } }`

## 6. 插件配置（实验，/api/v1/plugins）
- **GET /plugins/settings?tenant_id=...&agent_id?**
  - 读取插件配置；若带 agent_id，返回该 Agent 特定配置 + Tenant 默认配置的合并结果（Agent 优先）。
- **POST /plugins/settings?tenant_id=...&agent_id?**
  - body: `{ plugin_name, enabled, config }`，写入或更新对应记录。

说明：依赖 `maim_db.maimconfig_models.PluginSettings`（SQLAlchemy）。若 maim_db 未提供该模型或 `get_db` 无法返回 AsyncSession，则接口不可用。

## 7. 运维接口
- **GET /** 服务自描述（版本、主要资源路径）
- **GET /health** 健康检查
  - 响应: `{"status": "healthy", "services": {"database": "healthy", "api": "healthy"}, ...}`
- **GET /info** 服务信息
  - 响应: `{"name": "MaiMBot API", "version": "1.0.0", "supported_features": [...], ...}`

## 示例：创建租户与 Agent，再生成 API Key
```bash
# 创建租户
curl -X POST http://localhost:8000/api/v2/tenants \
  -H "Content-Type: application/json" \
  -d '{"tenant_name":"demo","tenant_type":"enterprise"}'

# 创建 Agent
curl -X POST http://localhost:8000/api/v2/agents \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"<tenant_id>","name":"assistant","config":{}}'

# 生成 API Key
curl -X POST http://localhost:8000/api/v2/api-keys \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"<tenant_id>","agent_id":"<agent_id>","name":"prod","permissions":["chat"]}'

# 验证 API Key
curl -X POST http://localhost:8000/api/v2/auth/validate-api-key \
  -H "Content-Type: application/json" \
  -d '{"api_key":"<mmc_key>","required_permission":"chat"}'

# 上报活跃 TTL
curl -X PUT http://localhost:8000/api/v2/agent-activity \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"<tenant_id>","agent_id":"<agent_id>","ttl_seconds":43200}'
```
# MaiMBot API 接口文档

## 概述

MaiMBot API v2 提供完整的多租户AI聊天机器人配置和管理功能，包括租户管理、Agent配置、API密钥管理和聊天功能。本服务设计为内部服务，所有接口都无需认证，可通过网络层面控制访问权限。

**基础URL**: `http://localhost:8000/api/v2`

**API版本**: v2

## 认证方式

### 内部服务模式
- **无需认证**: 所有API接口都无需身份验证
- **网络控制**: 通过防火墙、VPN等网络层面控制访问权限
- **专用网络**: 仅限可信网络访问

### API密钥格式
聊天接口使用的API密钥格式：
- **格式**: `mmc_{tenant_id}_{agent_id}_{random_hash}_{version}`
- **用途**: 用于外部服务调用聊天功能时的身份验证

## 统一响应格式

### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        // 具体数据内容
    },
    "timestamp": "2025-12-02T10:30:00Z",
    "request_id": "req_abc123def456",
    "tenant_id": "tenant_789",
    "execution_time": 0.123
}
```

### 错误响应
```json
{
    "success": false,
    "message": "操作失败",
    "error": "详细错误信息",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-12-02T10:30:00Z",
    "request_id": "req_abc123def456"
}
```

### 分页响应
```json
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 100,
            "total_pages": 5,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

---

## 1. 租户管理

### 1.1 创建租户（无需认证）
**POST** `/tenants`

创建新的租户，无需任何认证

**请求体**:
```json
{
    "tenant_name": "string",
    "tenant_type": "personal|enterprise",
    "description": "string",
    "contact_email": "user@example.com",
    "tenant_config": {
        "timezone": "Asia/Shanghai",
        "language": "zh-CN"
    }
}
```

**参数验证**:
- `tenant_name`: 1-100个字符
- `tenant_type`: personal 或 enterprise
- `contact_email`: 可选，有效邮箱格式

**响应**:
```json
{
    "success": true,
    "message": "租户创建成功",
    "data": {
        "tenant_id": "tenant_xyz789",
        "tenant_name": "我的公司",
        "tenant_type": "enterprise",
        "description": "AI聊天服务提供商",
        "tenant_config": {
            "timezone": "Asia/Shanghai",
            "language": "zh-CN"
        },
        "status": "active",
        "created_at": "2025-01-01T00:00:00Z"
    }
}
```

### 1.2 获取租户详情（无需认证）
**GET** `/tenants/{tenant_id}`

获取指定租户的详细信息

**路径参数**:
- `tenant_id`: 租户ID

**响应**:
```json
{
    "success": true,
    "message": "获取租户详情成功",
    "data": {
        "tenant_id": "tenant_xyz789",
        "tenant_name": "我的公司",
        "tenant_type": "enterprise",
        "status": "active",
        "description": "AI聊天服务提供商",
        "tenant_config": {
            "timezone": "Asia/Shanghai",
            "language": "zh-CN"
        },
        "owner_id": "temp_user_abc123",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-12-01T10:00:00Z"
    }
}
```

---

## 2. Agent管理

### 2.1 创建Agent（无需认证）
**POST** `/agents`

创建新的AI Agent

**请求体**:
```json
{
    "tenant_id": "tenant_xyz789",
    "name": "客服助手",
    "description": "专业的客户服务AI助手",
    "template_id": "customer_service_template",
    "config": {
        "persona": "友好、专业的客服助手，具有耐心和细致的解答能力",
        "bot_overrides": {
            "nickname": "小助手",
            "platform": "qq",
            "qq_account": "123456789"
        },
        "config_overrides": {
            "personality": {
                "reply_style": "专业、礼貌",
                "interest": "客户服务、技术支持"
            },
            "chat": {
                "max_context_size": 20,
                "response_timeout": 30
            }
        },
        "tags": ["客服", "技术支持", "AI助手"]
    }
}
```

**配置字段说明**：
Agent配置采用结构化存储，支持多层级配置覆盖系统。配置分为三个主要部分：

#### 2.1.1 persona（人格配置）
Agent的核心人格定义：
- `personality`: 人格核心描述（字符串）
- `reply_style`: 回复风格（字符串）
- `interest`: 兴趣领域（字符串）
- `plan_style`: 群聊行为风格（字符串）
- `private_plan_style`: 私聊行为风格（字符串）
- `visual_style`: 视觉风格（字符串）
- `states`: 状态列表（数组），每个状态包含：
  - `name`: 状态名称
  - `keywords`: 触发关键词数组
- `state_probability`: 状态切换概率（浮点数）

#### 2.1.2 bot_overrides（Bot基础配置覆盖）
平台和基础功能配置：
- `platform`: 运行平台（字符串）
- `qq_account`: QQ账号（字符串）
- `nickname`: 机器人昵称（字符串）
- `platforms`: 其他支持平台（字符串数组）
- `alias_names`: 别名列表（字符串数组）

#### 2.1.3 config_overrides（详细配置覆盖）
按功能模块组织的详细配置：

**chat（聊天配置）**：
- `max_context_size`: 上下文长度（整数，默认18）
- `interest_rate_mode`: 兴趣计算模式（字符串，"fast"/"medium"/"slow"）
- `planner_size`: 规划器大小（浮点数，默认1.5）
- `mentioned_bot_reply`: 提及回复（布尔值，默认true）
- `auto_chat_value`: 主动聊天频率（浮点数，默认1.0）
- `enable_auto_chat_value_rules`: 动态聊天频率（布尔值，默认true）
- `at_bot_inevitable_reply`: @回复必然性（浮点数，默认1.0）
- `planner_smooth`: 规划器平滑（浮点数，默认3.0）
- `talk_value`: 思考频率（浮点数，默认1.0）
- `enable_talk_value_rules`: 动态思考频率（布尔值，默认true）
- `talk_value_rules`: 思考频率规则（对象数组）
- `auto_chat_value_rules`: 聊天频率规则（对象数组）

**memory（记忆配置）**：
- `max_memory_number`: 记忆最大数量（整数，默认100）
- `memory_build_frequency`: 记忆构建频率（整数，默认1）

**mood（情绪配置）**：
- `enable_mood`: 启用情绪系统（布尔值，默认true）
- `mood_update_threshold`: 情绪更新阈值（浮点数，默认1.0）
- `emotion_style`: 情感特征（字符串）

**plugin（插件配置）**：
- `enable_plugins`: 启用插件（布尔值，默认true）
- `tenant_mode_disable_plugins`: 租户模式禁用（布尔值，默认true）
- `allowed_plugins`: 允许插件列表（字符串数组）
- `blocked_plugins`: 禁止插件列表（字符串数组）

**emoji（表情包配置）**：
- `emoji_chance`: 表情包概率（浮点数，默认0.6）
- `max_reg_num`: 最大注册数量（整数，默认200）
- `do_replace`: 是否替换（布尔值，默认true）
- `check_interval`: 检查间隔（整数，默认120）
- `steal_emoji`: 偷取表情包（布尔值，默认true）
- `content_filtration`: 内容过滤（布尔值，默认false）
- `filtration_prompt`: 过滤要求（字符串）

**tool（工具配置）**：
- `enable_tool`: 启用工具（布尔值，默认false）

**voice（语音配置）**：
- `enable_asr`: 语音识别（布尔值，默认false）

**expression（表达配置）**：
- `mode`: 表达模式（字符串，默认"classic"）
- `learning_list`: 表达学习配置（对象数组）
- `expression_groups`: 表达学习互通组（对象数组）

**keyword_reaction（关键词反应配置）**：
- `keyword_rules`: 关键词规则（对象数组）
- `regex_rules`: 正则规则（对象数组）

**relationship（关系配置）**：
- `enable_relationship`: 启用关系系统（布尔值，默认true）

- `tags`: 标签列表（字符串数组）

**响应**:
```json
{
    "success": true,
    "message": "Agent创建成功",
    "data": {
        "agent_id": "agent_pqr345",
        "tenant_id": "tenant_xyz789",
        "name": "客服助手",
        "description": "专业的客户服务AI助手",
        "template_id": null,
        "config": {
            "persona": "友好、专业的客服助手，具有耐心和细致的解答能力",
            "bot_overrides": {
                "nickname": "小助手",
                "platform": "qq",
                "qq_account": "123456789"
            },
            "config_overrides": {
                "personality": {
                    "reply_style": "专业、礼貌",
                    "interest": "客户服务、技术支持"
                },
                "chat": {
                    "max_context_size": 20,
                    "response_timeout": 30
                }
            },
            "tags": ["客服", "技术支持", "AI助手"]
        },
        "status": "active",
        "created_at": "2025-01-01T00:00:00Z"
    }
}
```

### 2.2 获取Agent列表（无需认证）
**GET** `/agents`

获取指定租户的Agent列表

**查询参数**:
- `tenant_id`: 租户ID (必需)
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `status`: 状态过滤 (可选)

**说明**: Agent必须属于特定租户，因此tenant_id是必需参数

**响应**:
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "agent_id": "agent_pqr345",
                "tenant_id": "tenant_xyz789",
                "name": "客服助手",
                "description": "专业的客户服务AI助手",
                "template_id": null,
                "config": {
                    "persona": "友好、专业的客服助手，具有耐心和细致的解答能力",
                    "bot_overrides": {
                        "nickname": "小助手",
                        "platform": "qq"
                    },
                    "config_overrides": {
                        "personality": {
                            "reply_style": "专业、礼貌"
                        }
                    },
                    "tags": ["客服", "技术支持"]
                },
                "status": "active",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-12-01T10:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 1,
            "total_pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }
}
```

### 2.3 获取Agent详情（无需认证）
**GET** `/agents/{agent_id}`

获取指定Agent的详细信息

**路径参数**:
- `agent_id`: Agent ID

**响应**:
```json
{
    "success": true,
    "message": "获取Agent详情成功",
    "data": {
        "agent_id": "agent_pqr345",
        "tenant_id": "tenant_xyz789",
        "name": "客服助手",
        "description": "专业的客户服务AI助手",
        "template_id": null,
        "config": {
            "persona": "友好、专业的客服助手，具有耐心和细致的解答能力",
            "bot_overrides": {
                "nickname": "小助手",
                "platform": "qq",
                "qq_account": "123456789"
            },
            "config_overrides": {
                "personality": {
                    "reply_style": "专业、礼貌",
                    "interest": "客户服务、技术支持"
                },
                "chat": {
                    "max_context_size": 20,
                    "response_timeout": 30
                }
            },
            "tags": ["客服", "技术支持", "AI助手"]
        },
        "status": "active",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-12-01T10:00:00Z"
    }
}
```

### 2.4 更新Agent（无需认证）
**PUT** `/agents/{agent_id}`

更新Agent信息和配置

**路径参数**:
- `agent_id`: Agent ID

**请求体**:
```json
{
    "name": "更新后的客服助手",
    "description": "更新后的描述",
    "config": {
        "persona": "更新后的人格描述，更加专业和高效",
        "bot_overrides": {
            "nickname": "超级助手",
            "platform": "discord"
        },
        "config_overrides": {
            "personality": {
                "reply_style": "简洁、高效",
                "interest": "技术支持、产品咨询"
            },
            "chat": {
                "max_context_size": 15
            }
        },
        "tags": ["客服", "技术支持", "专家"]
    }
}
```

**响应**:
```json
{
    "success": true,
    "message": "Agent更新成功",
    "data": {
        "agent_id": "agent_pqr345",
        "updated_at": "2025-12-02T10:30:00Z"
    }
}
```

### 2.5 获取Agent配置（无需认证）
**GET** `/agents/{agent_id}/config`

获取指定Agent的详细配置

**路径参数**:
- `agent_id`: Agent ID

**响应**:
```json
{
    "success": true,
    "message": "获取Agent配置成功",
    "data": {
        "persona": {
            "personality": "友好、专业的客服助手，具有耐心和细致的解答能力",
            "reply_style": "温和、专业、略带幽默",
            "interest": "科技、编程、帮助用户解决问题",
            "plan_style": "积极参与讨论，提供建设性意见",
            "private_plan_style": "耐心倾听，提供个性化建议",
            "visual_style": "现代简约风格",
            "states": [
                {"name": "正常", "keywords": ["你好", "帮助", "问题"]},
                {"name": "思考", "keywords": ["想想", "考虑", "分析"]}
            ],
            "state_probability": 0.3
        },
        "bot_overrides": {
            "platform": "qq",
            "qq_account": "123456789",
            "nickname": "小助手",
            "platforms": ["discord", "slack"],
            "alias_names": ["小测", "助手"]
        },
        "config_overrides": {
            "chat": {
                "max_context_size": 20,
                "interest_rate_mode": "medium",
                "planner_size": 2.0,
                "mentioned_bot_reply": true,
                "auto_chat_value": 0.8,
                "enable_auto_chat_value_rules": true,
                "at_bot_inevitable_reply": 1.2,
                "planner_smooth": 2.5,
                "talk_value": 0.9,
                "enable_talk_value_rules": true,
                "talk_value_rules": [
                    {"condition": "group_chat", "value": 0.7},
                    {"condition": "private_chat", "value": 1.2}
                ],
                "auto_chat_value_rules": [
                    {"condition": "active_group", "value": 1.5},
                    {"condition": "quiet_group", "value": 0.5}
                ]
            },
            "memory": {
                "max_memory_number": 150,
                "memory_build_frequency": 2
            },
            "mood": {
                "enable_mood": true,
                "mood_update_threshold": 1.2,
                "emotion_style": "温和友善"
            },
            "plugin": {
                "enable_plugins": true,
                "tenant_mode_disable_plugins": false,
                "allowed_plugins": ["calculator", "weather", "reminder"],
                "blocked_plugins": ["admin_only"]
            }
        }
    }
}
```

### 2.6 更新Agent配置（无需认证）
**PUT** `/agents/{agent_id}/config`

更新Agent的配置

**路径参数**:
- `agent_id`: Agent ID

**请求体**: 完整的配置对象，与创建Agent时的config字段格式相同

**响应**:
```json
{
    "success": true,
    "message": "Agent配置更新成功",
    "data": {
        "persona": {
            "personality": "更新后的人格描述"
        },
        "config_overrides": {
            "chat": {
                "max_context_size": 25
            }
        }
    }
}
```

### 2.7 删除Agent（无需认证）
**DELETE** `/agents/{agent_id}`

删除指定Agent及其所有配置

**路径参数**:
- `agent_id`: Agent ID

**响应**:
```json
{
    "success": true,
    "message": "Agent删除成功",
    "data": {
        "agent_id": "agent_pqr345",
        "deleted_at": "2025-12-02T10:30:00Z"
    }
}
```

---

## 3. API密钥管理

### 3.1 创建API密钥（无需认证）
**POST** `/api-keys`

为指定Agent创建新的API密钥

**请求体**:
```json
{
    "tenant_id": "tenant_xyz789",
    "agent_id": "agent_pqr345",
    "name": "string",
    "description": "string",
    "permissions": ["chat", "config_read"],
    "expires_at": "2026-01-01T00:00:00Z"
}
```

**响应**:
```json
{
    "success": true,
    "message": "API密钥创建成功",
    "data": {
        "api_key_id": "key_123",
        "tenant_id": "tenant_xyz789",
        "agent_id": "agent_pqr345",
        "name": "生产环境密钥",
        "description": "用于生产环境的API调用",
        "api_key": "mmc_dGVuYW50X3h5ejc4OV9hZ2VudF9wcXIzNDVfOGY4YTliMmMzZF92MQ==",
        "permissions": ["chat", "config_read"],
        "status": "active",
        "expires_at": "2026-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z"
    }
}
```

### 3.2 获取API密钥列表（无需认证）
**GET** `/api-keys`

获取指定租户的API密钥列表

**查询参数**:
- `tenant_id`: 租户ID (必需)
- `agent_id`: Agent ID (可选)
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `status`: 密钥状态过滤 (可选)

**说明**: API密钥必须属于特定租户，因此tenant_id是必需参数

**响应**:
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "api_key_id": "key_123",
                "tenant_id": "tenant_xyz789",
                "agent_id": "agent_pqr345",
                "name": "生产环境密钥",
                "description": "用于生产环境的API调用",
                "api_key": "mmc_dGVuYW50X3h5ejc4OV9hZ2VudF9wcXIzNDVfOGY4YTliMmMzZF92MQ==",
                "permissions": ["chat", "config_read"],
                "status": "active",
                "expires_at": "2026-01-01T00:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-12-01T10:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 1,
            "total_pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }
}
```

### 3.3 获取API密钥详情（无需认证）
**GET** `/api-keys/{api_key_id}`

获取指定API密钥的详细信息

**路径参数**:
- `api_key_id`: API密钥ID

**响应**:
```json
{
    "success": true,
    "message": "获取API密钥详情成功",
    "data": {
        "api_key_id": "key_123",
        "tenant_id": "tenant_xyz789",
        "agent_id": "agent_pqr345",
        "name": "生产环境密钥",
        "description": "用于生产环境的API调用",
        "api_key": "mmc_dGVuYW50X3h5ejc4OV9hZ2VudF9wcXIzNDVfOGY4YTliMmMzZF92MQ==",
        "permissions": ["chat", "config_read"],
        "status": "active",
        "expires_at": "2026-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-12-01T10:00:00Z"
    }
}
```

### 3.4 更新API密钥（无需认证）
**PUT** `/api-keys/{api_key_id}`

更新API密钥的配置

**路径参数**:
- `api_key_id`: API密钥ID

**请求体**:
```json
{
    "name": "string",
    "description": "string",
    "permissions": ["chat", "config_read", "config_write"],
    "expires_at": "2026-06-01T00:00:00Z"
}
```

**响应**:
```json
{
    "success": true,
    "message": "API密钥更新成功",
    "data": {
        "api_key_id": "key_123",
        "updated_at": "2025-12-02T10:30:00Z"
    }
}
```

### 3.5 禁用API密钥（无需认证）
**POST** `/api-keys/{api_key_id}/disable`

临时禁用API密钥

**路径参数**:
- `api_key_id`: API密钥ID

**响应**:
```json
{
    "success": true,
    "message": "API密钥已禁用",
    "data": {
        "api_key_id": "key_123",
        "status": "disabled",
        "disabled_at": "2025-12-02T10:30:00Z"
    }
}
```

### 3.6 删除API密钥（无需认证）
**DELETE** `/api-keys/{api_key_id}`

永久删除API密钥（不可恢复）

**路径参数**:
- `api_key_id`: API密钥ID

**响应**:
```json
{
    "success": true,
    "message": "API密钥删除成功",
    "data": {
        "api_key_id": "key_123",
        "deleted_at": "2025-12-02T10:30:00Z"
    }
}
```

---

## 4. API密钥认证

### 4.1 解析API密钥（无需认证）
**POST** `/auth/parse-api-key`

解析API密钥获取租户和Agent信息

**请求体**:
```json
{
    "api_key": "mmc_dGVuYW50X3h5ejc4OV9hZ2VudF9wcXIzNDVfOGY4YTliMmMzZF92MQ=="
}
```

**响应**:
```json
{
    "success": true,
    "message": "API密钥解析成功",
    "data": {
        "tenant_id": "tenant_xyz789",
        "agent_id": "agent_pqr345",
        "version": "v1",
        "format_valid": true
    }
}
```

### 4.2 验证API密钥（无需认证）
**POST** `/auth/validate-api-key`

验证API密钥的有效性和权限

**请求体**:
```json
{
    "api_key": "mmc_dGVuYW50X3h5ejc4OV9hZ2VudF9wcXIzNDVfOGY4YTliMmMzZF92MQ==",
    "required_permission": "chat",
    "check_rate_limit": true
}
```

**响应**:
```json
{
    "success": true,
    "message": "API密钥验证成功",
    "data": {
        "valid": true,
        "tenant_id": "tenant_xyz789",
        "agent_id": "agent_pqr345",
        "api_key_id": "key_123",
        "permissions": ["chat", "config_read"],
        "has_permission": true,
        "status": "active"
    }
}
```

### 4.3 检查权限（无需认证）
**POST** `/auth/check-permission`

检查API密钥是否具有指定权限

**请求体**:
```json
{
    "api_key": "mmc_dGVuYW50X3h5ejc4OV9hZ2VudF9wcXIzNDVfOGY4YTliMmMzZF92MQ==",
    "permission": "chat"
}
```

**响应**:
```json
{
    "success": true,
    "message": "权限检查完成",
    "data": {
        "has_permission": true,
        "permission": "chat",
        "all_permissions": ["chat", "config_read"],
        "tenant_id": "tenant_xyz789",
        "agent_id": "agent_pqr345",
        "api_key_status": "active"
    }
}
```

---

## 6. 错误码说明

### 6.1 认证相关错误
- `AUTH_001`: API密钥格式无效
- `AUTH_002`: API密钥已过期
- `AUTH_003`: API密钥权限不足
- `AUTH_004`: API密钥已禁用
- `AUTH_005`: API密钥不存在

### 6.2 租户管理错误
- `TENANT_001`: 租户不存在
- `TENANT_002`: 租户名称已存在
- `TENANT_003`: 租户状态无效
- `TENANT_004`: 租户类型不支持
- `TENANT_005`: 租户配额超限

### 6.3 Agent管理错误
- `AGENT_001`: Agent不存在
- `AGENT_002`: Agent名称已存在
- `AGENT_003`: Agent模板不存在
- `AGENT_004`: Agent配置无效
- `AGENT_005`: Agent状态不允许操作

### 6.4 API密钥管理错误
- `KEY_001`: API密钥不存在
- `KEY_002`: API密钥名称已存在
- `KEY_003`: API密钥已禁用
- `KEY_004`: API密钥配额超限
- `KEY_005`: API密钥权限配置无效

### 6.5 系统错误
- `SYS_001`: 内部服务器错误
- `SYS_002`: 数据库连接错误
- `SYS_003`: 外部服务不可用
- `SYS_004`: 请求超时
- `SYS_005`: 服务维护中

---

## 7. 使用示例

### 7.1 完整的API调用流程

```python
import requests

# 1. 创建租户（无需认证）
tenant_response = requests.post("http://localhost:8000/api/v2/tenants", json={
    "tenant_name": "我的公司",
    "tenant_type": "enterprise",
    "contact_email": "admin@company.com"
})

tenant_id = tenant_response.json()["data"]["tenant_id"]
print(f"租户创建成功，ID: {tenant_id}")

# 2. 创建Agent（带完整配置）
agent_config = {
    "tenant_id": tenant_id,
    "name": "客服助手",
    "description": "专业的客户服务AI助手",
    "config": {
        "persona": {
            "personality": "友好、专业的客服助手，具有耐心和细致的解答能力",
            "reply_style": "温和、专业、略带幽默",
            "interest": "客户服务、技术支持、产品咨询",
            "plan_style": "积极参与讨论，提供建设性意见",
            "private_plan_style": "耐心倾听，提供个性化建议",
            "states": [
                {"name": "正常", "keywords": ["你好", "帮助", "问题"]},
                {"name": "专注", "keywords": ["处理", "解决", "分析"]}
            ],
            "state_probability": 0.2
        },
        "bot_overrides": {
            "platform": "qq",
            "qq_account": "123456789",
            "nickname": "客服小助手",
            "platforms": ["discord", "slack"],
            "alias_names": ["小助手", "客服"]
        },
        "config_overrides": {
            "chat": {
                "max_context_size": 20,
                "interest_rate_mode": "medium",
                "planner_size": 2.0,
                "mentioned_bot_reply": True,
                "auto_chat_value": 0.8,
                "enable_auto_chat_value_rules": True,
                "talk_value": 0.9,
                "enable_talk_value_rules": True
            },
            "memory": {
                "max_memory_number": 150,
                "memory_build_frequency": 2
            },
            "mood": {
                "enable_mood": True,
                "mood_update_threshold": 1.2,
                "emotion_style": "温和友善"
            },
            "plugin": {
                "enable_plugins": True,
                "tenant_mode_disable_plugins": False,
                "allowed_plugins": ["knowledge_base", "order_query", "ticket_system"],
                "blocked_plugins": ["admin_only"]
            },
            "emoji": {
                "emoji_chance": 0.4,
                "do_replace": True,
                "content_filtration": True
            }
        }
    }
}

agent_response = requests.post("http://localhost:8000/api/v2/agents", json=agent_config)
agent_id = agent_response.json()["data"]["agent_id"]
print(f"Agent创建成功，ID: {agent_id}")

# 3. 获取Agent详细配置
config_response = requests.get(f"http://localhost:8000/api/v2/agents/{agent_id}/config")
agent_config = config_response.json()["data"]
print("Agent配置获取成功")
print(f"人格描述: {agent_config['persona']['personality']}")
print(f"聊天配置 - 最大上下文: {agent_config['config_overrides']['chat']['max_context_size']}")

# 4. 更新Agent部分配置
config_update = {
    "persona": {
        "personality": "更新后：更专业、更高效的客服助手",
        "reply_style": "简洁、高效、专业"
    },
    "config_overrides": {
        "chat": {
            "max_context_size": 25,
            "talk_value": 1.1
        }
    }
}

update_response = requests.put(f"http://localhost:8000/api/v2/agents/{agent_id}/config", json=config_update)
print("Agent配置更新成功")

# 5. 创建API密钥（无需认证）
api_key_response = requests.post("http://localhost:8000/api/v2/api-keys", json={
    "tenant_id": tenant_id,
    "agent_id": agent_id,
    "name": "生产环境密钥",
    "description": "用于生产环境的客服系统API调用",
    "permissions": ["chat", "config_read"]
})

api_key = api_key_response.json()["data"]["api_key"]
print(f"API密钥创建成功: {api_key}")

print("完整的Agent配置和管理流程完成")
print("该密钥可用于授权外部聊天服务访问Agent配置")
```

### 7.2 Agent配置管理示例

```python
import requests

# 假设已有 agent_id = "agent_abc123"

# 1. 获取当前Agent配置
config_response = requests.get("http://localhost:8000/api/v2/agents/agent_abc123/config")
current_config = config_response.json()["data"]

print("=== 当前Agent配置 ===")
print(f"人格描述: {current_config['persona']['personality']}")
print(f"回复风格: {current_config['persona']['reply_style']}")
print(f"聊天上下文大小: {current_config['config_overrides']['chat']['max_context_size']}")

# 2. 部分配置更新 - 只更新聊天配置
chat_config_update = {
    "config_overrides": {
        "chat": {
            "max_context_size": 30,  # 增加上下文大小
            "interest_rate_mode": "fast",  # 调整兴趣计算模式
            "talk_value": 1.2  # 提高思考频率
        }
    }
}

update_response = requests.put("http://localhost:8000/api/v2/agents/agent_abc123/config",
                             json=chat_config_update)
print("聊天配置更新成功")

# 3. 人格配置更新
persona_update = {
    "persona": {
        "personality": "经验丰富的技术专家，专业、耐心且乐于助人",
        "reply_style": "技术性、条理清晰、通俗易懂",
        "states": [
            {"name": "正常", "keywords": ["你好", "帮助", "问题"]},
            {"name": "技术支持", "keywords": ["技术", "问题", "解决", "代码"]},
            {"name": "教学", "keywords": ["学习", "教程", "解释"]}
        ],
        "state_probability": 0.25
    }
}

persona_response = requests.put("http://localhost:8000/api/v2/agents/agent_abc123/config",
                              json=persona_update)
print("人格配置更新成功")

# 4. 添加新的插件配置
plugin_config_update = {
    "config_overrides": {
        "plugin": {
            "enable_plugins": True,
            "allowed_plugins": ["code_runner", "documentation_search", "file_manager"],
            "blocked_plugins": ["system_admin"]
        }
    }
}

plugin_response = requests.put("http://localhost:8000/api/v2/agents/agent_abc123/config",
                              json=plugin_config_update)
print("插件配置更新成功")

# 5. 验证最终配置
final_config_response = requests.get("http://localhost:8000/api/v2/agents/agent_abc123/config")
final_config = final_config_response.json()["data"]

print("\n=== 更新后的配置 ===")
print(f"新的人格描述: {final_config['persona']['personality']}")
print(f"新的上下文大小: {final_config['config_overrides']['chat']['max_context_size']}")
print(f"允许的插件: {final_config['config_overrides']['plugin']['allowed_plugins']}")
```

### 7.3 API密钥验证流程

```python
import requests

# 验证API密钥
validation_response = requests.post("http://localhost:8000/api/v2/auth/validate-api-key",
    json={
        "api_key": "mmc_dGVuYW50X3h5ejc4OV9hZ2VudF9wcXIzNDVfOGY4YTliMmMzZF92MQ==",
        "required_permission": "chat"
    })

if validation_response.json()["success"]:
    # 密钥有效，具有chat权限
    print("API密钥验证成功，具有chat权限")
    print("该密钥可用于外部聊天服务进行身份验证")
```

---

## 8. 架构说明

### 8.1 内部服务架构
- **无需认证**: 所有接口都无需身份验证
- **网络安全**: 通过网络层面的访问控制确保服务安全
- **专用网络**: 仅限可信网络访问，通常通过VPN或防火墙规则

### 8.2 租户管理
- **直接创建**: 无需认证即可创建租户
- **资源隔离**: 完全的多租户数据隔离
- **生命周期管理**: 完整的租户生命周期支持

### 8.3 Agent配置系统架构
Agent配置采用结构化存储，支持多层级配置覆盖：

**配置层级**：
1. **persona**: Agent核心人格定义
2. **bot_overrides**: 平台和基础功能配置
3. **config_overrides**: 按功能模块组织的详细配置

**配置覆盖机制**：
- 结构化存储：12个专门的数据库表替代单一JSON字段
- 模块化管理：每个功能模块独立配置（聊天、记忆、情绪、插件等）
- 向后兼容：API响应仍保持JSON格式
- 灵活更新：支持部分配置更新和完整配置覆盖

**技术特点**：
- **类型安全**: 使用Peewee ORM提供强类型验证
- **查询优化**: 结构化字段支持高效查询和索引
- **扩展性**: 模块化设计便于添加新的配置类型
- **数据完整性**: 外键约束确保配置与Agent的关联关系

### 8.4 API设计原则
- **RESTful**: 遵循REST API设计原则
- **统一响应**: 标准化的成功和错误响应格式
- **版本控制**: 清晰的API版本管理
- **文档完整**: 详细的API文档和示例
- **配置管理**: 专门的配置管理接口，支持细粒度配置操作

### 8.5 安全考虑
- **网络隔离**: 通过防火墙、VPN控制访问权限
- **数据加密**: 敏感数据加密存储
- **日志记录**: 完整的操作日志记录
- **监控告警**: 服务状态监控和异常告警
- **配置安全**: 配置数据访问权限控制，防止未授权配置修改

---

**文档版本**: 2.1.0

**最后更新**: 2025-12-04

**重要变更**:
- v2.0.0: 移除所有需要认证的接口，改为内部服务架构
- v2.1.0: 重构Agent配置系统，采用结构化存储
  - 新增 `/agents/{agent_id}/config` 配置管理接口
  - Agent配置支持多层级覆盖和模块化管理
  - 12个专门配置表替代单一JSON字段
  - 完整的配置CRUD操作和部分更新功能

**联系方式**: 如有API使用问题，请通过 https://github.com/your-org/maimbot/issues 反馈。