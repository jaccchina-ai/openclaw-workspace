#!/usr/bin/env python3
"""
导入工作空间记忆到OpenClaw memory-lancedb插件
注意：需要先确保memory-lancedb插件正常工作
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

class MemoryImporter:
    """记忆导入器"""
    
    def __init__(self, dry_run=False, batch_size=5):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.import_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None
        }
        
    def scan_workspace_files(self):
        """扫描工作空间中的所有记忆文件"""
        files = []
        
        # 1. 核心身份文件
        core_files = [
            ("SOUL.md", "identity", 0.9),
            ("USER.md", "preference", 0.9),
            ("AGENTS.md", "preference", 0.8),
            ("MEMORY.md", "fact", 0.8),
            ("TOOLS.md", "fact", 0.7),
            ("HEARTBEAT.md", "preference", 0.7),
            ("IDENTITY.md", "identity", 0.9),
        ]
        
        for fname, category, importance in core_files:
            path = WORKSPACE / fname
            if path.exists():
                files.append({
                    "type": "core_identity",
                    "path": path,
                    "category": category,
                    "importance": importance,
                    "priority": 1
                })
        
        # 2. 每日记忆文件
        memory_dir = WORKSPACE / "memory"
        if memory_dir.exists():
            for mem_file in sorted(memory_dir.glob("2026-*.md")):
                if mem_file.stat().st_size > 0:
                    files.append({
                        "type": "daily_log",
                        "path": mem_file,
                        "category": "fact",
                        "importance": 0.6,
                        "priority": 2
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
                            "category": "fact",
                            "importance": 0.7,
                            "priority": 3
                        })
        
        # 4. 任务注册表
        registry_file = WORKSPACE / "task_registry.json"
        if registry_file.exists():
            files.append({
                "type": "task_registry",
                "path": registry_file,
                "category": "fact",
                "importance": 0.8,
                "priority": 1
            })
        
        # 按优先级排序
        files.sort(key=lambda x: x["priority"])
        return files
    
    def read_file_content(self, file_info):
        """读取文件内容并提取元数据"""
        path = file_info["path"]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            lines = content.split('\n')
            title = path.name
            for line in lines[:10]:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
                elif line.startswith('## '):
                    title = line[3:].strip()
                    break
            
            # 提取摘要
            summary = content.replace('\n', ' ').strip()[:200]
            if len(content) > 200:
                summary += "..."
            
            return {
                "content": content,
                "metadata": {
                    "title": title,
                    "source_file": str(path),
                    "file_size": len(content),
                    "lines": content.count('\n') + 1,
                    "file_type": file_info["type"],
                    "original_category": file_info["category"],
                    "importance": file_info["importance"],
                    "import_time": datetime.now().isoformat(),
                    "summary": summary
                }
            }
            
        except Exception as e:
            print(f"❌ 读取文件失败 {path}: {e}")
            return None
    
    def format_memory_text(self, memory_data):
        """格式化记忆文本"""
        metadata = memory_data["metadata"]
        content = memory_data["content"]
        
        # 构建记忆文本
        text = f"""记忆来源: {metadata['title']}
文件类型: {metadata['file_type']}
导入时间: {metadata['import_time']}
摘要: {metadata['summary']}

内容:
{content}
"""
        return text.strip()
    
    def import_via_openclaw_api(self, memory_data):
        """通过OpenClaw API导入记忆（模拟）"""
        if self.dry_run:
            print(f"[模拟] 导入: {memory_data['metadata']['title']}")
            print(f"      类别: {memory_data['metadata']['original_category']}")
            print(f"      重要性: {memory_data['metadata']['importance']}")
            return True
        
        # TODO: 实现实际的OpenClaw API调用
        # 目前使用memory_store工具（通过AI调用）
        print(f"⚠️  实际导入需要memory-lancedb插件正常工作")
        print(f"   记忆: {memory_data['metadata']['title']}")
        
        return False
    
    def run_import(self):
        """运行导入流程"""
        print("=== 记忆导入开始 ===")
        print(f"工作空间: {WORKSPACE}")
        print(f"模拟模式: {self.dry_run}")
        print(f"批量大小: {self.batch_size}")
        print()
        
        self.import_stats["start_time"] = datetime.now().isoformat()
        
        # 扫描文件
        files = self.scan_workspace_files()
        print(f"找到 {len(files)} 个记忆文件")
        
        # 显示文件列表
        for i, file_info in enumerate(files, 1):
            print(f"{i:2d}. {file_info['path'].name} ({file_info['type']})")
        
        print()
        
        # 导入每个文件
        for i, file_info in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}] 处理: {file_info['path'].name}")
            
            # 读取内容
            memory_data = self.read_file_content(file_info)
            if not memory_data:
                self.import_stats["failed"] += 1
                continue
            
            # 检查内容长度
            if len(memory_data["content"]) > 4000:
                print(f"⚠️  内容过长 ({len(memory_data['content'])} 字符)，将截断")
                memory_data["content"] = memory_data["content"][:4000] + "...[已截断]"
            
            # 导入
            success = self.import_via_openclaw_api(memory_data)
            
            if success:
                self.import_stats["success"] += 1
            else:
                self.import_stats["failed"] += 1
            
            self.import_stats["total"] += 1
            
            # 批量延迟
            if i % self.batch_size == 0 and i < len(files):
                print(f"   暂停 2 秒...")
                time.sleep(2)
        
        # 完成统计
        self.import_stats["end_time"] = datetime.now().isoformat()
        
        print("\n=== 导入统计 ===")
        print(f"总计: {self.import_stats['total']}")
        print(f"成功: {self.import_stats['success']}")
        print(f"失败: {self.import_stats['failed']}")
        print(f"跳过: {self.import_stats['skipped']}")
        print(f"耗时: {self.import_stats['start_time']} 到 {self.import_stats['end_time']}")
        
        # 保存导入报告
        report_file = WORKSPACE / "memory_import_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.import_stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 详细报告已保存: {report_file}")
        
        return self.import_stats

def main():
    parser = argparse.ArgumentParser(description="导入记忆到memory-lancedb")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际导入")
    parser.add_argument("--batch-size", type=int, default=5, help="批量大小")
    
    args = parser.parse_args()
    
    importer = MemoryImporter(dry_run=args.dry_run, batch_size=args.batch_size)
    stats = importer.run_import()
    
    if args.dry_run:
        print("\n⚠️  模拟模式完成。要实际导入，请运行:")
        print("   python3 import_memories_to_lancedb.py")
    else:
        print("\n✅ 导入完成！")
    
    return 0 if stats["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())