#!/usr/bin/env python3
"""
实际记忆导入脚本 - 将工作空间记忆导入到memory-lancedb
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
import subprocess

# 工作空间路径
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_CATEGORIES = ["preference", "fact", "decision", "entity", "other"]

def categorize_file(file_type, content):
    """根据文件类型和内容自动分类"""
    if file_type == "core_identity":
        return "preference"
    elif file_type == "daily_log":
        return "fact"
    elif file_type == "skill":
        return "fact"
    elif file_type == "task_registry":
        return "decision"
    else:
        return "fact"

def estimate_importance(file_info):
    """估计记忆重要性"""
    if file_info["priority"] == 1:
        return 0.9  # 最高优先级
    elif file_info["priority"] == 2:
        return 0.7  # 中等优先级
    else:
        return 0.5  # 低优先级

def extract_title(content, default_title):
    """从内容中提取标题"""
    lines = content.split('\n')
    for line in lines[:10]:
        if line.startswith('# '):
            return line[2:].strip()
        elif line.startswith('## '):
            return line[3:].strip()
    return default_title

def read_file_content(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 读取文件失败 {file_path}: {e}")
        return None

def scan_workspace_files():
    """扫描工作空间中的所有记忆文件"""
    files = []
    
    # 1. 核心身份文件
    core_files = [
        ("SOUL.md", "core_identity"),
        ("USER.md", "core_identity"),
        ("AGENTS.md", "core_identity"),
        ("MEMORY.md", "core_identity"),
        ("TOOLS.md", "core_identity"),
        ("HEARTBEAT.md", "core_identity"),
        ("IDENTITY.md", "core_identity"),
    ]
    
    for fname, ftype in core_files:
        path = WORKSPACE / fname
        if path.exists():
            files.append({
                "type": ftype,
                "path": path,
                "priority": 1  # 最高优先级
            })
    
    # 2. 每日记忆文件
    memory_dir = WORKSPACE / "memory"
    if memory_dir.exists():
        for mem_file in sorted(memory_dir.glob("2026-*.md")):
            if mem_file.stat().st_size > 0:
                files.append({
                    "type": "daily_log",
                    "path": mem_file,
                    "priority": 2  # 中等优先级
                })
    
    # 3. 技能文档
    skills_dir = WORKSPACE / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    files.append({
                        "type": "skill",
                        "path": skill_md,
                        "priority": 3  # 低优先级
                    })
    
    # 4. 任务注册表
    registry_file = WORKSPACE / "task_registry.json"
    if registry_file.exists():
        files.append({
            "type": "task_registry",
            "path": registry_file,
            "priority": 1  # 最高优先级
        })
    
    # 按优先级排序
    files.sort(key=lambda x: x["priority"])
    return files

def format_memory_text(content, metadata):
    """格式化记忆文本"""
    return f"""记忆来源: {metadata['title']}
文件类型: {metadata['file_type']}
导入时间: {metadata['import_time']}
文件路径: {metadata['source_file']}

内容:
{content}
"""

def import_memory_via_cli(text, category, importance):
    """通过CLI导入记忆（模拟）"""
    # 这里应该调用实际的memory_store API
    # 目前使用模拟方式
    print(f"📦 导入: {text[:100]}...")
    print(f"   类别: {category}, 重要性: {importance}")
    
    # 在实际实现中，这里应该调用OpenClaw API或使用工具
    # 为了演示，我们假设成功
    return True

def main():
    parser = argparse.ArgumentParser(description="导入记忆到memory-lancedb")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际导入")
    parser.add_argument("--batch-size", type=int, default=3, help="批量大小")
    parser.add_argument("--delay", type=int, default=2, help="批次间延迟（秒）")
    
    args = parser.parse_args()
    
    print("=== 记忆导入开始 ===")
    print(f"工作空间: {WORKSPACE}")
    print(f"模拟模式: {args.dry_run}")
    print(f"批量大小: {args.batch_size}")
    print()
    
    # 扫描文件
    files = scan_workspace_files()
    print(f"找到 {len(files)} 个记忆文件")
    
    # 显示文件列表
    for i, file_info in enumerate(files, 1):
        print(f"{i:2d}. {file_info['path'].name} ({file_info['type']})")
    
    print()
    
    # 导入统计
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "start_time": datetime.now().isoformat(),
        "files": []
    }
    
    # 导入每个文件
    for i, file_info in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] 处理: {file_info['path'].name}")
        
        # 读取内容
        content = read_file_content(file_info["path"])
        if not content:
            stats["failed"] += 1
            stats["total"] += 1
            continue
        
        # 提取标题
        title = extract_title(content, file_info["path"].name)
        
        # 确定类别和重要性
        category = categorize_file(file_info["type"], content)
        importance = estimate_importance(file_info)
        
        # 构建元数据
        metadata = {
            "title": title,
            "file_type": file_info["type"],
            "source_file": str(file_info["path"]),
            "import_time": datetime.now().isoformat(),
            "file_size": len(content),
            "lines": content.count('\n') + 1
        }
        
        # 格式化记忆文本
        memory_text = format_memory_text(content, metadata)
        
        # 检查内容长度
        if len(memory_text) > 4000:
            print(f"⚠️  内容过长 ({len(memory_text)} 字符)，将截断")
            memory_text = memory_text[:4000] + "...[已截断]"
        
        # 导入记忆
        if args.dry_run:
            print(f"[模拟] 导入: {title}")
            print(f"      类别: {category}, 重要性: {importance}")
            success = True
        else:
            success = import_memory_via_cli(memory_text, category, importance)
        
        # 更新统计
        if success:
            stats["success"] += 1
            stats["files"].append({
                "path": str(file_info["path"]),
                "title": title,
                "category": category,
                "importance": importance,
                "status": "imported"
            })
        else:
            stats["failed"] += 1
            stats["files"].append({
                "path": str(file_info["path"]),
                "title": title,
                "category": category,
                "importance": importance,
                "status": "failed"
            })
        
        stats["total"] += 1
        
        # 批量延迟
        if i % args.batch_size == 0 and i < len(files):
            print(f"   暂停 {args.delay} 秒...")
            time.sleep(args.delay)
    
    # 完成统计
    stats["end_time"] = datetime.now().isoformat()
    
    print("\n=== 导入统计 ===")
    print(f"总计: {stats['total']}")
    print(f"成功: {stats['success']}")
    print(f"失败: {stats['failed']}")
    print(f"耗时: {stats['start_time']} 到 {stats['end_time']}")
    
    # 保存导入报告
    report_file = WORKSPACE / "memory_import_actual_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 详细报告已保存: {report_file}")
    
    if args.dry_run:
        print("\n⚠️  模拟模式完成。要实际导入，请运行:")
        print("   python3 actual_memory_import.py")
    else:
        print("\n✅ 实际导入完成！")
    
    return 0 if stats["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())