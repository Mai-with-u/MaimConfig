# MaimConfig（MaiMBot 控制平面）

快速跳转：
- [API 文档](./docs/API文档.md)
- [设计指导](./docs/设计指导.md)
- [Agent 配置参考](./docs/Agent配置字段完整说明.md)
- [项目总结](./docs/项目总结.md)

独立的 FastAPI 服务，负责多租户的租户/Agent/API 密钥管理，以及 Agent 活跃心跳上报。默认作为内网服务部署，接口无需鉴权，依赖网络层隔离。

## 功能概览
- 租户管理：创建/查询/更新/删除租户。
- Agent 管理：创建/查询/更新/删除 Agent，并写入 maim_db 的 AgentConfig；创建时自动上报活跃 TTL（12h）。
- API 密钥管理：生成/查询/更新 API Key，格式 `mmc_{base64(tenant_agent_random_version)}`。
- API Key 认证：解析、验证、检查权限并记录使用统计。
- Agent 活跃状态：上报/查询租户-Agent 的活跃 TTL。
- 插件配置（实验特性）：/api/v1/plugins/settings 读写插件设置，依赖 maim_db 的 maimconfig_models（SQLAlchemy）。
- 运维接口：`/health`、`/info`、根路径服务描述。

## 运行要求
- Python 3.10+
- 依赖项目：`maim_db`（Peewee 模型 + AgentConfig 管理器）；可选 `maim_db.maimconfig_models`（插件配置用 SQLAlchemy）。
- 数据库：MySQL（由 maim_db 配置）；Redis 未在本项目直接使用。

## 快速开始
```bash
pip install -r requirements.txt
export PYTHONPATH="$(pwd)"  # 确保可导入 maim_db
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动时会：
1) 初始化 maim_db 数据库连接；2) 调用 `maim_db.core.db_manager.create_tables(ALL_MODELS)` 以创建表（包含 `agent_active_states`）。

## 主要端点（前缀 `/api/v2`，插件为 `/api/v1`）
- 租户：`POST /tenants`，`GET /tenants/{id}`，`GET /tenants`（分页），`PUT /tenants/{id}`，`DELETE /tenants/{id}`
- Agent：`POST /agents`，`GET /agents/{id}`，`GET /agents?tenant_id=...`，`PUT /agents/{id}`，`DELETE /agents/{id}`
- API Key：`POST /api-keys`，`GET /api-keys`，`GET /api-keys/{id}`，`PUT /api-keys/{id}`
- Auth：`POST /auth/parse-api-key`，`POST /auth/validate-api-key`，`POST /auth/check-permission`
- 活跃状态：`PUT /agent-activity`，`GET /agent-activity`
- 插件（实验）：`GET /api/v1/plugins/settings`，`POST /api/v1/plugins/settings`
- 运维：`GET /health`，`GET /info`，`GET /`

## 配置与依赖
- 数据库连接由 maim_db 提供（Peewee）；本项目的 `src/database/connection.py` 仅做异步包装。
- Agent 配置读取/写入通过 `maim_db.core.AgentConfigManager`；存储在 maim_db 的配置目录/表中。
- 插件接口依赖 `maim_db.maimconfig_models`（SQLAlchemy）。如未安装该子模块，插件接口将不可用。

## 目录结构（节选）
```
MaimConfig/
├── main.py                  # FastAPI 入口，注册路由与生命周期
├── src/
│   ├── api/routes/          # 路由：tenant / agent / api_key / auth / active_state / plugin
│   ├── database/            # maim_db 异步封装与枚举
│   ├── common/logger.py     # 日志
│   └── utils/response.py    # 统一响应格式
├── docs/                    # 文档（API、设计、总结、Agent 字段说明）
└── requirements.txt
```

## 开发与测试
- 直接使用 `pytest` 或脚本 `test_api.py`（如有）运行集成测试；目前仓库未内置单元测试。 
- 本服务默认“无鉴权”，部署时务必通过网络/Ingress/防火墙限制访问。

## 迁移与兼容提示
- 新增的 `agent_active_states` 表需在目标数据库执行创建；启动时会尝试自动创建，但生产环境建议先运行迁移脚本。
- 代码使用 `maim_db` 的 Peewee 模型；旧文档中提到的 SQLAlchemy/Redis 聊天接口已不在当前代码中实现。

## 参考文档
- `docs/API文档.md`：端点与示例
- `docs/Agent配置字段完整说明.md`：Agent 配置存储结构
- `docs/设计指导.md`：架构与隔离要点
- `docs/项目总结.md`：功能完成度与待办

### 使用API密钥

API密钥创建完成后，可以用于外部服务进行身份验证和权限控制。

## 项目结构

```
api-backend/
├── src/
│   ├── api/
│   │   └── routes/          # API路由模块
│   │       ├── tenant_api.py     # 租户管理API（无需认证）
│   │       ├── agent_api.py      # Agent管理API（无需认证）
│   │       ├── api_key_api.py    # API密钥管理（无需认证）
│   │       └── auth_api.py       # API密钥认证和验证（无需认证）
│   ├── database/
│   │   ├── connection.py    # 数据库连接
│   │   └── models.py        # 数据库模型
│   ├── common/
│   │   ├── config.py        # 配置管理
│   │   └── logger.py        # 日志配置
│   └── utils/
│       └── response.py      # 响应格式工具
├── main.py                  # 应用入口
├── requirements.txt         # Python依赖
├── docker-compose.yml       # Docker编排
├── Dockerfile              # Docker镜像
└── README.md               # 项目文档
```

## 配置说明

### 数据库配置

```bash
DATABASE_URL=mysql+aiomysql://username:password@localhost:3306/maimbot_api
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=maimbot_api
DATABASE_USER=username
DATABASE_PASSWORD=password
```

### 服务器配置

```bash
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### 安全配置

```bash
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 开发指南

### 添加新的API接口

1. 在`src/api/routes/`目录下创建新的路由文件
2. 定义请求/响应模型
3. 实现业务逻辑
4. 在`src/api/routes/__init__.py`中导出路由
5. 在`main.py`中注册路由

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_tenant_api.py

# 生成测试报告
pytest --cov=src tests/
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t maimbot-api .

# 运行容器
docker run -d -p 8000:8000 --name maimbot-api maimbot-api
```

### 生产环境配置

1. 设置环境变量`DEBUG=false`
2. 使用强密码和安全的SECRET_KEY
3. 配置反向代理（Nginx）
4. 启用HTTPS
5. 配置日志收集和监控

## 监控和日志

- 应用日志：支持结构化JSON格式输出
- 健康检查：`GET /health`
- 性能指标：包含执行时间和使用统计
- 错误追踪：详细的错误信息和错误码

## 许可证

[MIT License](LICENSE)

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题，请通过以下方式联系：

- 项目地址：https://github.com/your-org/maimbot-api
- 问题反馈：https://github.com/your-org/maimbot-api/issues