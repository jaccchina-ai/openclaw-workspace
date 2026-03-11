#!/usr/bin/env python3
"""
通过AI接口导入记忆 - 生成可以直接执行的命令
"""

import json
import os
from pathlib import Path

# 工作空间路径
WORKSPACE = Path("/root/.openclaw/workspace")

def generate_import_commands():
    """生成导入命令"""
    # 读取模拟报告
    report_file = WORKSPACE / "memory_import_actual_report.json"
    if not report_file.exists():
        print("❌ 导入报告不存在")
        return []
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    commands = []
    
    for file_info in report.get("files", []):
        if file_info.get("status") == "imported":
            # 这里应该生成实际的导入命令
            # 由于memory_store是通过AI调用的，我们需要创建调用模板
            path = Path(file_info["path"])
            
            # 读取文件内容
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 构建记忆文本
                memory_text = f"""记忆来源: {file_info['title']}
文件类型: {path.name}
文件路径: {path}
导入时间: {report['end_time']}

内容摘要:
{content[:500]}...""" if len(content) > 500 else content
                
                command = {
                    "text": memory_text,
                    "category": file_info["category"],
                    "importance": file_info["importance"],
                    "source_file": str(path)
                }
                commands.append(command)
                
            except Exception as e:
                print(f"❌ 读取文件失败 {path}: {e}")
    
    return commands

def generate_import_script(commands):
    """生成导入脚本"""
    script_content = """# 记忆导入脚本
# 将此内容复制到AI对话中执行

"""
    
    for i, cmd in enumerate(commands, 1):
        # 转义文本中的特殊字符
        text = cmd["text"].replace('"', '\\"').replace('\n', '\\n')
        script_content += f'''# 导入 {i}: {cmd["source_file"]}
memory_store(text="{text}", importance={cmd["importance"]}, category="{cmd["category"]}")

'''
    
    return script_content

def main():
    print("=== 生成记忆导入脚本 ===")
    
    commands = generate_import_commands()
    print(f"找到 {len(commands)} 个记忆需要导入")
    
    if not commands:
        print("❌ 没有找到需要导入的记忆")
        return 1
    
    # 生成脚本
    script = generate_import_script(commands)
    
    # 保存脚本
    script_file = WORKSPACE / "memory_import_script.txt"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"📋 导入脚本已保存: {script_file}")
    print(f"\n📝 脚本包含 {len(commands)} 个记忆导入命令")
    print("\n📌 使用说明:")
    print("1. 复制脚本内容到AI对话中")
    print("2. AI将逐个执行memory_store命令")
    print("3. 每个导入后等待1-2秒，避免API限制")
    
    # 显示前3个命令示例
    print("\n🔍 示例命令:")
    for i in range(min(3, len(commands))):
        cmd = commands[i]
        print(f"{i+1}. {cmd['source_file']} -> {cmd['category']} (重要性: {cmd['importance']})")
    
    return 0

if __name__ == "__main__":
    exit(main())