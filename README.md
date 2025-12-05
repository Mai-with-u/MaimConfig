# MaiMBot API Server

独立的后端API服务，提供多租户AI聊天机器人配置和管理功能。

## 功能特性

- 🏢 **多租户管理** - 支持个人和企业级租户，完全数据隔离
- 🤖 **Agent配置** - 灵活的AI Agent配置和模板管理
- 🔐 **API密钥管理** - 安全的API密钥生成、管理和权限控制
- 🔑 **API密钥认证** - 完整的API密钥解析、验证和权限检查
- 📊 **监控统计** - 完整的使用统计和性能监控
- 🚀 **内部服务架构** - 无需认证，通过网络层面控制访问

## 技术栈

- **Web框架**: FastAPI
- **数据库**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0 (异步)
- **缓存**: Redis
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd api-backend

# 复制环境配置
cp .env.example .env
```

### 2. 使用Docker Compose启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### 3. 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## API接口

### 租户管理
- `POST /api/v2/tenants` - 创建租户
- `GET /api/v2/tenants/{tenant_id}` - 获取租户详情
- `PUT /api/v2/tenants/{tenant_id}` - 更新租户
- `DELETE /api/v2/tenants/{tenant_id}` - 删除租户

### Agent管理
- `POST /api/v2/agents` - 创建Agent
- `GET /api/v2/agents` - 获取Agent列表
- `GET /api/v2/agents/{agent_id}` - 获取Agent详情
- `PUT /api/v2/agents/{agent_id}` - 更新Agent
- `DELETE /api/v2/agents/{agent_id}` - 删除Agent

### API密钥管理
- `POST /api/v2/api-keys` - 创建API密钥
- `GET /api/v2/api-keys` - 获取API密钥列表
- `GET /api/v2/api-keys/{api_key_id}` - 获取API密钥详情
- `PUT /api/v2/api-keys/{api_key_id}` - 更新API密钥
- `POST /api/v2/api-keys/{api_key_id}/disable` - 禁用API密钥
- `DELETE /api/v2/api-keys/{api_key_id}` - 删除API密钥

### API密钥认证
- `POST /api/v2/auth/parse-api-key` - 解析API密钥
- `POST /api/v2/auth/validate-api-key` - 验证API密钥
- `POST /api/v2/auth/check-permission` - 检查权限


## 使用示例

### 创建租户

```bash
curl -X POST "http://localhost:8000/api/v2/tenants" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "我的公司",
    "tenant_type": "enterprise",
    "description": "AI聊天服务提供商",
    "contact_email": "admin@company.com"
  }'
```

### 创建Agent

```bash
curl -X POST "http://localhost:8000/api/v2/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_xyz789",
    "name": "客服助手",
    "description": "专业的客户服务AI助手",
    "config": {
      "persona": "友好、专业的客服助手",
      "tags": ["客服", "技术支持"]
    }
  }'
```

### 创建API密钥

```bash
curl -X POST "http://localhost:8000/api/v2/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_xyz789",
    "agent_id": "agent_pqr345",
    "name": "生产环境密钥",
    "permissions": ["chat"]
  }'
```

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