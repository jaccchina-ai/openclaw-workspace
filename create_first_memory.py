#!/usr/bin/env python3
"""
创建第一个 MemU 记忆项测试
"""

import asyncio
import os

async def main():
    print("=== 创建第一个 MemU 记忆项 ===")
    
    from memu.app import MemoryService
    
    # 初始化服务
    service = MemoryService()
    print("✅ MemoryService 初始化成功")
    
    # 尝试创建记忆项 - 使用 'knowledge' 类型
    print("创建 'knowledge' 类型记忆项...")
    try:
        result = await service.create_memory_item(
            memory_type="knowledge",
            memory_content="OpenClaw AI助手系统由小虾米维护，包含T01龙头战法、T99复盘扫描、T100宏观监控三个核心任务。",
            memory_categories=["system_overview", "openclaw"],
            user={"id": "openclaw_agent", "name": "小虾米"}
        )
        print(f"✅ 记忆项创建成功!")
        print(f"   结果ID: {result.get('id', 'N/A')}")
        print(f"   类型: {result.get('type', 'N/A')}")
        print(f"   内容预览: {result.get('content', result.get('memory_content', 'N/A'))[:80]}...")
        return True
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    # 检查数据库文件
    db_path = "/root/.openclaw/workspace/memu_data/memu.db"
    print(f"\n检查数据库文件: {db_path}")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ 数据库文件存在，大小: {size} 字节")
    else:
        print(f"⚠️  数据库文件不存在（可能使用了不同路径）")
    
    exit(0 if success else 1)