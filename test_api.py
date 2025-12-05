#!/usr/bin/env python3
"""
MaiMBot API 功能测试脚本
"""

import requests
import time
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v2"


def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v2', '')}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")
        return False


def create_tenant():
    """创建测试租户"""
    print("🏢 创建测试租户...")
    try:
        data = {
            "tenant_name": "测试公司",
            "tenant_type": "enterprise",
            "description": "API测试租户",
            "contact_email": "test@example.com",
            "tenant_config": {
                "timezone": "Asia/Shanghai",
                "language": "zh-CN"
            }
        }
        response = requests.post(f"{BASE_URL}/tenants", json=data)
        if response.status_code == 200:
            result = response.json()
            tenant_id = result["data"]["tenant_id"]
            print(f"✅ 租户创建成功: {tenant_id}")
            return tenant_id
        else:
            print(f"❌ 租户创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 租户创建错误: {e}")
        return None


def create_agent(tenant_id):
    """创建测试Agent"""
    print("🤖 创建测试Agent...")
    try:
        data = {
            "tenant_id": tenant_id,
            "name": "测试助手",
            "description": "API测试Agent",
            "config": {
                "persona": "友好的测试助手",
                "bot_overrides": {
                    "nickname": "小助",
                    "platform": "test"
                },
                "tags": ["测试", "助手"]
            }
        }
        response = requests.post(f"{BASE_URL}/agents", json=data)
        if response.status_code == 200:
            result = response.json()
            agent_id = result["data"]["agent_id"]
            print(f"✅ Agent创建成功: {agent_id}")
            return agent_id
        else:
            print(f"❌ Agent创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Agent创建错误: {e}")
        return None


def create_api_key(tenant_id, agent_id):
    """创建测试API密钥"""
    print("🔑 创建测试API密钥...")
    try:
        data = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "name": "测试密钥",
            "description": "API测试密钥",
            "permissions": ["chat"]
        }
        response = requests.post(f"{BASE_URL}/api-keys", json=data)
        if response.status_code == 200:
            result = response.json()
            api_key = result["data"]["api_key"]
            print(f"✅ API密钥创建成功")
            return api_key
        else:
            print(f"❌ API密钥创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ API密钥创建错误: {e}")
        return None


def test_chat(api_key):
    """测试聊天功能"""
    print("💬 测试聊天功能...")
    try:
        data = {
            "api_key": api_key,
            "message": "你好，这是一个测试消息",
            "conversation_id": "test_conv_001",
            "user_id": "test_user_001"
        }
        response = requests.post(f"{BASE_URL}/chat", json=data)
        if response.status_code == 200:
            result = response.json()
            response_text = result["data"]["response"]
            print(f"✅ 聊天测试成功")
            print(f"   回复: {response_text}")
            return True
        else:
            print(f"❌ 聊天测试失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 聊天测试错误: {e}")
        return False


def test_api_key_auth(api_key):
    """测试API密钥认证"""
    print("🔐 测试API密钥认证...")
    try:
        # 测试解析API密钥
        data = {"api_key": api_key}
        response = requests.post(f"{BASE_URL}/auth/parse-api-key", json=data)
        if response.status_code == 200:
            print("✅ API密钥解析成功")
        else:
            print(f"❌ API密钥解析失败: {response.status_code}")
            return False

        # 测试验证API密钥
        data = {
            "api_key": api_key,
            "required_permission": "chat",
            "check_rate_limit": True
        }
        response = requests.post(f"{BASE_URL}/auth/validate-api-key", json=data)
        if response.status_code == 200:
            print("✅ API密钥验证成功")
            return True
        else:
            print(f"❌ API密钥验证失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API密钥认证错误: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始 MaiMBot API 功能测试\n")

    # 测试健康检查
    if not test_health_check():
        print("❌ 服务未启动，请先启动API服务")
        return

    print()

    # 创建租户
    tenant_id = create_tenant()
    if not tenant_id:
        print("❌ 租户创建失败，测试终止")
        return

    time.sleep(1)

    # 创建Agent
    agent_id = create_agent(tenant_id)
    if not agent_id:
        print("❌ Agent创建失败，测试终止")
        return

    time.sleep(1)

    # 创建API密钥
    api_key = create_api_key(tenant_id, agent_id)
    if not api_key:
        print("❌ API密钥创建失败，测试终止")
        return

    time.sleep(1)

    # 测试API密钥认证
    if not test_api_key_auth(api_key):
        print("❌ API密钥认证测试失败")

    time.sleep(1)

    # 测试聊天功能
    if not test_chat(api_key):
        print("❌ 聊天功能测试失败")

    print("\n🎉 API功能测试完成!")
    print(f"📋 测试信息:")
    print(f"   租户ID: {tenant_id}")
    print(f"   AgentID: {agent_id}")
    print(f"   API密钥: {api_key}")
    print("\n📖 API文档: http://localhost:8000/docs")


if __name__ == "__main__":
    main()