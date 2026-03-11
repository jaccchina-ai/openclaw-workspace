#!/usr/bin/env python3
"""
导入剩余文件到memory-lancedb
"""

import json
import os
import time
from pathlib import Path

def read_file_content(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 读取文件失败 {file_path}: {e}")
        return None

def format_memory_text(content, metadata):
    """格式化记忆文本"""
    return f"""记忆来源: {metadata['title']}
文件类型: {metadata['file_type']}
导入时间: {metadata['import_time']}
文件路径: {metadata['source_file']}

内容:
{content}
"""

def import_remaining_files():
    """导入剩余文件"""
    # 读取导入报告
    report_file = Path("/root/.openclaw/workspace/memory_import_actual_report.json")
    if not report_file.exists():
        print("❌ 导入报告不存在")
        return
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # 已经导入的文件路径
    imported_files = [f["path"] for f in report.get("files", [])]
    print(f"报告中的文件数量: {len(imported_files)}")
    
    # 实际检查哪些文件已经导入到memory-lancedb
    # 这里我们假设前4个文件已经导入（SOUL.md, USER.md, AGENTS.md, MEMORY.md）
    already_imported = imported_files[:4]  # 前4个核心文件
    
    # 需要导入的文件
    to_import = []
    for file_info in report.get("files", [])[4:]:  # 从第5个开始
        if file_info["path"] not in already_imported:
            to_import.append(file_info)
    
    print(f"需要导入的文件数量: {len(to_import)}")
    
    # 导入每个文件
    for i, file_info in enumerate(to_import, 1):
        print(f"\n[{i}/{len(to_import)}] 导入: {file_info['path']}")
        
        # 读取内容
        content = read_file_content(file_info["path"])
        if not content:
            print(f"❌ 跳过: 无法读取内容")
            continue
        
        # 检查内容长度
        if len(content) > 4000:
            print(f"⚠️  内容过长 ({len(content)} 字符)，将截断")
            content = content[:4000] + "...[已截断]"
        
        # 构建元数据
        metadata = {
            "title": file_info["title"],
            "file_type": Path(file_info["path"]).name,
            "source_file": file_info["path"],
            "import_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        }
        
        # 格式化记忆文本
        memory_text = format_memory_text(content, metadata)
        
        # 导入记忆
        try:
            # 这里应该调用实际的memory_store API
            # 目前打印出命令供手动执行
            print(f"📦 准备导入: {file_info['title'][:50]}...")
            print(f"   类别: {file_info['category']}, 重要性: {file_info['importance']}")
            
            # 在实际实现中，这里应该调用memory_store
            # 为了演示，我们假设成功
            print(f"✅ 模拟导入成功")
            
        except Exception as e:
            print(f"❌ 导入失败: {e}")
        
        # 批量延迟
        if i % 5 == 0 and i < len(to_import):
            print(f"   暂停 2 秒...")
            time.sleep(2)
    
    print(f"\n=== 导入完成 ===")
    print(f"总计: {len(to_import)} 个文件")
    print(f"已模拟导入: {len(to_import)} 个文件")

def main():
    print("=== 导入剩余文件到memory-lancedb ===")
    print(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    print()
    
    import_remaining_files()
    
    print("\n📋 下一步:")
    print("1. 执行批量导入脚本（需要实际调用memory_store）")
    print("2. 测试memory-lancedb高级功能")
    print("3. 验证LanceDB可靠性")

if __name__ == "__main__":
    main()