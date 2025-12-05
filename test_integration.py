#!/usr/bin/env python3
"""
测试maimconfig与maim_db的集成
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

async def test_maim_db_integration():
    """测试maim_db集成"""
    print("🚀 测试maimconfig与maim_db集成...")

    try:
        # 测试导入
        print("📦 测试模块导入...")
        from src.database.models import Tenant, Agent, ApiKey, TenantType, TenantStatus
        from src.database.connection import init_database, close_database
        print("✅ 模块导入成功")

        # 测试数据库连接
        print("🔗 测试数据库连接...")
        await init_database()
        print("✅ 数据库连接成功")

        # 测试创建租户
        print("🏢 测试创建租户...")
        tenant = await Tenant.create(
            tenant_name="测试租户",
            tenant_type=TenantType.PERSONAL.value,
            description="这是一个测试租户",
            tenant_config={"timezone": "Asia/Shanghai"}
        )
        print(f"✅ 创建租户成功: {tenant.id} - {tenant.tenant_name}")

        # 测试获取租户
        print("🔍 测试获取租户...")
        retrieved_tenant = await Tenant.get(tenant.id)
        if retrieved_tenant:
            print(f"✅ 获取租户成功: {retrieved_tenant.tenant_name}")
        else:
            print("❌ 获取租户失败")

        # 测试创建Agent
        print("🤖 测试创建Agent...")
        agent = await Agent.create(
            tenant_id=tenant.id,
            name="测试助手",
            description="这是一个测试AI助手",
            config={"model": "gpt-3.5-turbo", "temperature": 0.7}
        )
        print(f"✅ 创建Agent成功: {agent.id} - {agent.name}")

        # 测试获取Agent
        print("🔍 测试获取Agent...")
        retrieved_agent = await Agent.get(agent.id)
        if retrieved_agent:
            print(f"✅ 获取Agent成功: {retrieved_agent.name}")
        else:
            print("❌ 获取Agent失败")

        # 测试创建API密钥
        print("🔑 测试创建API密钥...")
        import base64
        import uuid

        key_data = f"{tenant.id}_{agent.id}_{uuid.uuid4().hex[:16]}_v1"
        api_key_value = f"mmc_{base64.b64encode(key_data.encode()).decode()}"

        api_key = await ApiKey.create(
            tenant_id=tenant.id,
            agent_id=agent.id,
            name="测试密钥",
            description="这是一个测试API密钥",
            api_key=api_key_value,
            permissions=["chat", "config"]
        )
        print(f"✅ 创建API密钥成功: {api_key.id} - {api_key.name}")

        # 清理测试数据
        print("🧹 清理测试数据...")
        await api_key.delete()
        await agent.delete()
        await tenant.delete()
        print("✅ 测试数据清理完成")

        # 关闭数据库连接
        print("🔌 关闭数据库连接...")
        await close_database()
        print("✅ 数据库连接已关闭")

        print("\n🎉 所有测试通过！maimconfig与maim_db集成成功！")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_routes():
    """测试API路由"""
    print("🌐 测试API路由...")

    try:
        # 测试导入路由
        print("📦 测试路由导入...")
        from src.api.routes.tenant_api import router as tenant_router
        print("✅ 租户路由导入成功")

        print("✅ API路由测试通过")
        return True

    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 MaiMConfig + MaimDB 集成测试")
    print("=" * 60)

    success_count = 0
    total_tests = 2

    # 测试数据库集成
    if await test_maim_db_integration():
        success_count += 1

    print()

    # 测试API路由
    if await test_api_routes():
        success_count += 1

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")

    if success_count == total_tests:
        print("🎉 所有测试通过！集成成功！")
        print("\n💡 现在可以启动FastAPI服务:")
        print("   python main.py")
    else:
        print("⚠️ 部分测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())