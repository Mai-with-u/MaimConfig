# MaiMBot Agent配置字段完整说明

## 概述

MaiMBot的Agent配置系统是一个完整的多层级、多租户隔离的配置管理体系，支持人格配置、行为配置、聊天配置等多个维度的灵活配置。本文档详细说明所有可用的配置字段。

## 1. Agent基础配置（Agent）

### 1.1 核心字段

| 字段名        | 类型     | 必需 | 默认值 | 说明                                              |
| ------------- | -------- | ---- | ------ | ------------------------------------------------- |
| `agent_id`    | string   | ✅    | -      | Agent的唯一标识符，通常格式为`tenant_id:agent_id` |
| `name`        | string   | ✅    | -      | Agent的显示名称，用于界面展示                     |
| `description` | string   | ❌    | `""`   | Agent的简要描述信息                               |
| `tags`        | string[] | ❌    | `[]`   | 标签列表，用于分类和检索                          |

### 1.2 配置覆盖字段

| 字段名             | 类型              | 必需 | 默认值 | 说明                    |
| ------------------ | ----------------- | ---- | ------ | ----------------------- |
| `persona`          | PersonalityConfig | ✅    | -      | Agent专属的人格配置对象 |
| `bot_overrides`    | object            | ❌    | `{}`   | Bot基础配置的覆盖项     |
| `config_overrides` | object            | ❌    | `{}`   | 整体配置系统的覆盖项    |

## 2. 人格配置（PersonalityConfig）

### 2.1 核心人格字段

| 字段名        | 类型   | 必需 | 默认值 | 说明                                             |
| ------------- | ------ | ---- | ------ | ------------------------------------------------ |
| `personality` | string | ✅    | -      | **人格核心描述**，定义AI的基本性格特征和行为准则 |

### 2.2 表达风格字段

| 字段名               | 类型   | 必需 | 默认值 | 说明                                                 |
| -------------------- | ------ | ---- | ------ | ---------------------------------------------------- |
| `reply_style`        | string | ❌    | `""`   | **回复风格**，如"轻松自然"、"正式礼貌"、"幽默风趣"等 |
| `interest`           | string | ❌    | `""`   | **兴趣领域**，影响对话内容的偏好和话题选择           |
| `plan_style`         | string | ❌    | `""`   | **群聊行为风格**，定义在群聊中的说话规则和行为模式   |
| `private_plan_style` | string | ❌    | `""`   | **私聊行为风格**，定义在私聊中的说话规则和行为模式   |

### 2.3 多媒体风格字段

| 字段名         | 类型   | 必需 | 默认值 | 说明                                           |
| -------------- | ------ | ---- | ------ | ---------------------------------------------- |
| `visual_style` | string | ❌    | `""`   | **视觉风格**，生成图片时的提示词风格和美学偏好 |

### 2.4 状态系统字段

| 字段名              | 类型     | 必需 | 默认值 | 说明                                                      |
| ------------------- | -------- | ---- | ------ | --------------------------------------------------------- |
| `states`            | string[] | ❌    | `[]`   | **状态列表**，多种人格状态用于随机切换，增加对话多样性    |
| `state_probability` | float    | ❌    | `0.0`  | **状态切换概率**，0.0-1.0之间，控制人格状态随机切换的频率 |

## 3. Bot基础配置覆盖（BotConfig Overrides）

### 3.1 必需字段覆盖

| 字段名       | 类型   | 必需 | 默认值 | 说明                                          |
| ------------ | ------ | ---- | ------ | --------------------------------------------- |
| `platform`   | string | ❌    | -      | **运行平台**，如"qq"、"telegram"、"discord"等 |
| `qq_account` | string | ❌    | -      | **QQ账号**，数字字符串格式                    |
| `nickname`   | string | ❌    | -      | **机器人昵称**，在聊天中显示的名称            |

### 3.2 扩展字段覆盖

| 字段名        | 类型     | 必需 | 默认值 | 说明                                       |
| ------------- | -------- | ---- | ------ | ------------------------------------------ |
| `platforms`   | string[] | ❌    | `[]`   | **其他支持平台**列表                       |
| `alias_names` | string[] | ❌    | `[]`   | **别名列表**，用于识别机器人的多种称呼方式 |

## 4. 整体配置覆盖（Config Overrides）

### 4.1 聊天配置覆盖（ChatConfig）

| 字段名                         | 类型     | 必需 | 默认值   | 说明                                             |
| ------------------------------ | -------- | ---- | -------- | ------------------------------------------------ |
| `max_context_size`             | int      | ❌    | 18       | **上下文长度**，保留的历史消息数量               |
| `interest_rate_mode`           | string   | ❌    | `"fast"` | **兴趣计算模式**，"fast"快速或"accurate"精确     |
| `planner_size`                 | float    | ❌    | 1.5      | **规划器大小**，控制AI执行能力，1.0-3.0          |
| `mentioned_bot_reply`          | bool     | ❌    | true     | **提及回复**，被@时是否必须回复                  |
| `auto_chat_value`              | float    | ❌    | 1.0      | **主动聊天频率**，数值越低，主动聊天概率越低     |
| `enable_auto_chat_value_rules` | bool     | ❌    | true     | **动态聊天频率**，是否启用基于时间的自动频率调整 |
| `at_bot_inevitable_reply`      | float    | ❌    | 1.0      | **@回复必然性**，1.0为100%回复，0.0为不额外增幅  |
| `planner_smooth`               | float    | ❌    | 3.0      | **规划器平滑**，减小规划器负荷，推荐2-5          |
| `talk_value`                   | float    | ❌    | 1.0      | **思考频率**，AI主动思考和回复的频率             |
| `enable_talk_value_rules`      | bool     | ❌    | true     | **动态思考频率**，是否启用基于时间的思考频率调整 |
| `talk_value_rules`             | object[] | ❌    | `[]`     | **思考频率规则**，基于时间的动态规则列表         |
| `auto_chat_value_rules`        | object[] | ❌    | `[]`     | **聊天频率规则**，基于时间的动态规则列表         |
| `include_planner_reasoning`    | bool     | ❌    | false    | **包含规划推理**，是否将planner推理加入replyer   |

### 4.2 关系配置覆盖（RelationshipConfig）

| 字段名                | 类型 | 必需 | 默认值 | 说明                                       |
| --------------------- | ---- | ---- | ------ | ------------------------------------------ |
| `enable_relationship` | bool | ❌    | true   | **启用关系系统**，是否开启用户关系管理功能 |

### 4.3 表达配置覆盖（ExpressionConfig）

| 字段名              | 类型     | 必需 | 默认值      | 说明                                                 |
| ------------------- | -------- | ---- | ----------- | ---------------------------------------------------- |
| `mode`              | string   | ❌    | `"classic"` | **表达模式**，"classic"经典或"exp_model"表达模型模式 |
| `learning_list`     | array    | ❌    | `[]`        | **表达学习配置**列表，定义学习模式                   |
| `expression_groups` | object[] | ❌    | `[]`        | **表达学习互通组**，定义表达学习的分组规则           |

### 4.4 记忆配置覆盖（MemoryConfig）

| 字段名                   | 类型 | 必需 | 默认值 | 说明                                    |
| ------------------------ | ---- | ---- | ------ | --------------------------------------- |
| `max_memory_number`      | int  | ❌    | 100    | **记忆最大数量**，保留的长期记忆条数    |
| `memory_build_frequency` | int  | ❌    | 1      | **记忆构建频率**，每N条消息构建一次记忆 |

### 4.5 情绪配置覆盖（MoodConfig）

| 字段名                  | 类型   | 必需 | 默认值                                         | 说明                                       |
| ----------------------- | ------ | ---- | ---------------------------------------------- | ------------------------------------------ |
| `enable_mood`           | bool   | ❌    | true                                           | **启用情绪系统**，是否开启情绪状态管理     |
| `mood_update_threshold` | float  | ❌    | 1.0                                            | **情绪更新阈值**，数值越高，情绪变化越缓慢 |
| `emotion_style`         | string | ❌    | `"情绪较为稳定，但遭遇特定事件的时候起伏较大"` | **情感特征**，描述情绪变化的模式和特征     |

### 4.6 表情包配置覆盖（EmojiConfig）

| 字段名               | 类型   | 必需 | 默认值           | 说明                                          |
| -------------------- | ------ | ---- | ---------------- | --------------------------------------------- |
| `emoji_chance`       | float  | ❌    | 0.6              | **表情包概率**，发送表情包的基础概率，0.0-1.0 |
| `max_reg_num`        | int    | ❌    | 200              | **最大注册数量**，表情包缓存的最大数量        |
| `do_replace`         | bool   | ❌    | true             | **是否替换**，达到最大数量时是否替换旧表情包  |
| `check_interval`     | int    | ❌    | 120              | **检查间隔**，表情包检查间隔时间（分钟）      |
| `steal_emoji`        | bool   | ❌    | true             | **偷取表情包**，是否从聊天中学习新表情包      |
| `content_filtration` | bool   | ❌    | false            | **内容过滤**，是否开启表情包内容过滤          |
| `filtration_prompt`  | string | ❌    | `"符合公序良俗"` | **过滤要求**，表情包内容过滤的标准描述        |

### 4.7 工具配置覆盖（ToolConfig）

| 字段名                    | 类型 | 必需 | 默认值 | 说明                                       |
| ------------------------- | ---- | ---- | ------ | ------------------------------------------ |
| `enable_tool`             | bool | ❌    | false  | **启用工具**，是否在聊天中启用外部工具调用 |
| `tool_cache_ttl`          | int  | ❌    | -      | **工具缓存TTL**（秒）                      |
| `max_tool_execution_time` | int  | ❌    | -      | **最大工具执行时间**（秒）                 |
| `enable_tool_parallel`    | bool | ❌    | -      | **是否启用工具并行执行**                   |

### 4.8 语音配置覆盖（VoiceConfig）

| 字段名       | 类型 | 必需 | 默认值 | 说明                                 |
| ------------ | ---- | ---- | ------ | ------------------------------------ |
| `enable_asr` | bool | ❌    | false  | **语音识别**，是否启用语音转文字功能 |

### 4.9 插件配置覆盖（PluginConfig）

| 字段名                        | 类型     | 必需 | 默认值 | 说明                                           |
| ----------------------------- | -------- | ---- | ------ | ---------------------------------------------- |
| `enable_plugins`              | bool     | ❌    | true   | **启用插件**，是否启用插件系统                 |
| `tenant_mode_disable_plugins` | bool     | ❌    | true   | **租户模式禁用**，多租户模式下是否禁用所有插件 |
| `allowed_plugins`             | string[] | ❌    | `[]`   | **允许插件**，白名单插件列表                   |
| `blocked_plugins`             | string[] | ❌    | `[]`   | **禁止插件**，黑名单插件列表                   |

### 4.10 关键词反应配置覆盖（KeywordReactionConfig）

| 字段名          | 类型     | 必需 | 默认值 | 说明                                       |
| --------------- | -------- | ---- | ------ | ------------------------------------------ |
| `keyword_rules` | object[] | ❌    | `[]`   | **关键词规则**，基于关键词匹配的反应规则   |
| `regex_rules`   | object[] | ❌    | `[]`   | **正则规则**，基于正则表达式匹配的反应规则 |

### 4.11 LPMM知识库配置覆盖（LPMMKnowledgeConfig）

| 字段名                      | 类型   | 必需 | 默认值 | 说明                   |
| --------------------------- | ------ | ---- | ------ | ---------------------- |
| `enable`                    | bool   | ❌    | false  | **启用LPMM**           |
| `lpmm_mode`                 | string | ❌    | -      | **模式**               |
| `rag_synonym_search_top_k`  | int    | ❌    | -      | **RAG同义词搜索Top K** |
| `rag_synonym_threshold`     | float  | ❌    | -      | **RAG同义词阈值**      |
| `info_extraction_workers`   | int    | ❌    | -      | **信息抽取Worker数**   |
| `qa_relation_search_top_k`  | int    | ❌    | -      | **QA关系搜索Top K**    |
| `qa_relation_threshold`     | float  | ❌    | -      | **QA关系阈值**         |
| `qa_paragraph_search_top_k` | int    | ❌    | -      | **QA段落搜索Top K**    |
| `qa_paragraph_node_weight`  | float  | ❌    | -      | **QA段落节点权重**     |
| `qa_ent_filter_top_k`       | int    | ❌    | -      | **QA实体过滤Top K**    |
| `qa_ppr_damping`            | float  | ❌    | -      | **QA PPR阻尼系数**     |
| `qa_res_top_k`              | int    | ❌    | -      | **QA结果Top K**        |
| `embedding_dimension`       | int    | ❌    | -      | **Embedding维度**      |

### 4.12 梦境配置覆盖（DreamConfig）

| 字段名             | 类型 | 必需 | 默认值 | 说明               |
| ------------------ | ---- | ---- | ------ | ------------------ |
| `interval_minutes` | int  | ❌    | -      | **做梦间隔**(分钟) |
| `max_iterations`   | int  | ❌    | -      | **最大迭代次数**   |

### 4.13 术语/黑话配置覆盖（JargonConfig）

| 字段名       | 类型 | 必需 | 默认值 | 说明                       |
| ------------ | ---- | ---- | ------ | -------------------------- |
| `all_global` | bool | ❌    | -      | **全局生效**，是否全局生效 |

### 4.14 回复后处理配置覆盖（ResponsePostProcessConfig）

| 字段名                         | 类型 | 必需 | 默认值 | 说明               |
| ------------------------------ | ---- | ---- | ------ | ------------------ |
| `enable_response_post_process` | bool | ❌    | -      | **启用回复后处理** |

### 4.15 中文纠错配置覆盖（ChineseTypoConfig）

| 字段名              | 类型  | 必需 | 默认值 | 说明               |
| ------------------- | ----- | ---- | ------ | ------------------ |
| `enable`            | bool  | ❌    | -      | **启用纠错**       |
| `error_rate`        | float | ❌    | -      | **错误率**         |
| `min_freq`          | int   | ❌    | -      | **最小频率**       |
| `tone_error_rate`   | float | ❌    | -      | **声调错误率**     |
| `word_replace_rate` | float | ❌    | -      | **词语替换错误率** |

### 4.16 回复分割器配置覆盖（ResponseSplitterConfig）

| 字段名                       | 类型 | 必需 | 默认值 | 说明                     |
| ---------------------------- | ---- | ---- | ------ | ------------------------ |
| `enable`                     | bool | ❌    | -      | **启用分割器**           |
| `max_length`                 | int  | ❌    | -      | **最大长度**             |
| `max_sentence_num`           | int  | ❌    | -      | **最大句数**             |
| `enable_kaomoji_protection`  | bool | ❌    | -      | **启用颜文字保护**       |
| `enable_overflow_return_all` | bool | ❌    | -      | **启用溢出直接返回全部** |

### 4.17 调试配置覆盖（DebugConfig）

| 字段名                   | 类型 | 必需 | 默认值 | 说明                    |
| ------------------------ | ---- | ---- | ------ | ----------------------- |
| `show_prompt`            | bool | ❌    | -      | **显示Prompt**          |
| `show_replyer_prompt`    | bool | ❌    | -      | **显示Replyer Prompt**  |
| `show_replyer_reasoning` | bool | ❌    | -      | **显示Replyer推理过程** |
| `show_jargon_prompt`     | bool | ❌    | -      | **显示Jargon Prompt**   |
| `show_memory_prompt`     | bool | ❌    | -      | **显示Memory Prompt**   |
| `show_planner_prompt`    | bool | ❌    | -      | **显示Planner Prompt**  |
| `show_lpmm_paragraph`    | bool | ❌    | -      | **显示LPMM段落**        |

### 4.18 实验功能配置覆盖（ExperimentalConfig）

| 字段名               | 类型     | 必需 | 默认值 | 说明               |
| -------------------- | -------- | ---- | ------ | ------------------ |
| `enable_friend_chat` | bool     | ❌    | -      | **启用好友聊天**   |
| `chat_prompts`       | string[] | ❌    | -      | **聊天Prompt列表** |

### 4.19 MaimMessage配置覆盖（MaimMessageConfig）

| 字段名       | 类型     | 必需 | 默认值 | 说明               |
| ------------ | -------- | ---- | ------ | ------------------ |
| `use_custom` | bool     | ❌    | -      | **使用自定义配置** |
| `host`       | string   | ❌    | -      | **Host**           |
| `port`       | int      | ❌    | -      | **Port**           |
| `mode`       | string   | ❌    | -      | **Mode**           |
| `use_wss`    | bool     | ❌    | -      | **使用WSS**        |
| `cert_file`  | string   | ❌    | -      | **证书文件**       |
| `key_file`   | string   | ❌    | -      | **Key文件**        |
| `auth_token` | string[] | ❌    | -      | **Auth Token**     |

### 4.20 遥测配置覆盖（TelemetryConfig）

| 字段名   | 类型 | 必需 | 默认值 | 说明         |
| -------- | ---- | ---- | ------ | ------------ |
| `enable` | bool | ❌    | -      | **启用遥测** |

### 4.21 模型配置覆盖 (ModelConfig)

模型配置覆盖允许Agent自定义使用的模型、API提供商以及为特定任务指定模型。

| 字段名              | 类型            | 必需 | 默认值 | 说明                                                         |
| ------------------- | --------------- | ---- | ------ | ------------------------------------------------------------ |
| `models`            | object[]        | ❌    | `[]`   | **模型列表**，定义或覆盖可用的模型，同名覆盖                 |
| `api_providers`     | object[]        | ❌    | `[]`   | **API提供商列表**，定义或覆盖API提供商，同名覆盖             |
| `model_task_config` | ModelTaskConfig | ❌    | `{}`   | **任务模型配置**，指定各功能模块使用的模型及参数（递归覆盖） |

#### 4.21.1 模型详情 (ModelInfo)

`models` 列表中的对象结构：

| 字段名              | 类型   | 必需 | 默认值 | 说明                           |
| ------------------- | ------ | ---- | ------ | ------------------------------ |
| `name`              | string | ✅    | -      | **模型名称**，系统内部引用的ID |
| `model_identifier`  | string | ✅    | -      | **模型标识符**，API调用的ID    |
| `api_provider`      | string | ✅    | -      | **API提供商名称**              |
| `price_in`          | float  | ❌    | 0.0    | **输入价格**（$/1M tok）       |
| `price_out`         | float  | ❌    | 0.0    | **输出价格**（$/1M tok）       |
| `temperature`       | float  | ❌    | -      | **温度**，覆盖默认温度         |
| `force_stream_mode` | bool   | ❌    | false  | **强制流式**                   |
| `extra_params`      | object | ❌    | `{}`   | **额外参数**                   |

#### 4.21.2 API提供商详情 (APIProvider)

`api_providers` 列表中的对象结构：

| 字段名           | 类型   | 必需 | 默认值   | 说明             |
| ---------------- | ------ | ---- | -------- | ---------------- |
| `name`           | string | ✅    | -        | **提供商名称**   |
| `base_url`       | string | ✅    | -        | **Base URL**     |
| `api_key`        | string | ❌    | -        | **API Key**      |
| `client_type`    | string | ❌    | "openai" | **客户端类型**   |
| `max_retry`      | int    | ❌    | 2        | **最大重试次数** |
| `timeout`        | int    | ❌    | 10       | **超时时间**(秒) |
| `retry_interval` | int    | ❌    | 10       | **重试间隔**(秒) |

#### 4.21.3 任务配置详情 (ModelTaskConfig)

`model_task_config` 对象包含以下键（每个键对应 `TaskConfig`）：
`utils`, `utils_small`, `replyer`, `vlm`, `voice`, `tool_use`, `planner`, `embedding`, `lpmm_entity_extract`, `lpmm_rdf_build`, `lpmm_qa`

每个任务配置 (`TaskConfig`) 包含：

| 字段名           | 类型     | 必需 | 默认值 | 说明             |
| ---------------- | -------- | ---- | ------ | ---------------- |
| `model_list`     | string[] | ❌    | `[]`   | **备选模型列表** |
| `max_tokens`     | int      | ❌    | 1024   | **最大Token数**  |
| `temperature`    | float    | ❌    | 0.3    | **温度**         |
| `slow_threshold` | float    | ❌    | 15.0   | **慢响应阈值**   |

## 5. 完整配置示例 (更新)

```json
{
  "agent_id": "tenant_123:customer_service",
  "name": "全能助手",
  "config": {
    "persona": { ... },
    "config_overrides": {
      "chat": { "max_context_size": 100 },
      "debug": {
        "show_prompt": true,
        "show_replyer_reasoning": true
      },
      "lpmm_knowledge": {
        "enable": true,
        "lpmm_mode": "accurate"
      },
      "chinese_typo": {
        "enable": true,
        "error_rate": 0.05
      },
      "model": {
        "model_task_config": {
            "replyer": {
                "model_list": ["gpt-4-custom"],
                "temperature": 0.8
            }
        }
      }
    }
  }
}
```

---

**文档版本**: 1.2.0
**最后更新**: 2025-12-15