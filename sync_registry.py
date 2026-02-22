#!/usr/bin/env python3
"""
Task Registry 同步脚本
自动同步代码版本与Registry版本
"""

import json
import yaml
import os
import sys
from datetime import datetime
from pathlib import Path
import argparse
from typing import Dict, Any, Optional, Tuple


class RegistrySyncer:
    """Registry同步器"""
    
    def __init__(self, registry_path: str = "task_registry.json"):
        self.registry_path = Path(registry_path)
        self.workspace_root = Path.cwd()
        
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry文件不存在: {self.registry_path}")
        
        # 加载Registry
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)
    
    def get_version_from_source(self, task_config: Dict[str, Any]) -> Optional[str]:
        """
        从代码源中提取版本号
        支持多种配置文件格式
        """
        task_id = task_config['id']
        location = task_config['location']
        config_file = task_config.get('configuration_file')
        
        # 构建完整路径
        source_dir = self.workspace_root / location
        
        if not source_dir.exists():
            print(f"警告: Task {task_id} 的目录不存在: {source_dir}")
            return None
        
        # 尝试从配置文件读取版本
        if config_file and config_file != "无独立配置文件":
            config_path = source_dir / config_file
            
            if config_path.exists():
                return self._extract_version_from_file(config_path)
        
        # 如果没有配置文件或文件不存在，尝试常见位置
        return self._find_version_in_directory(source_dir, task_id)
    
    def _extract_version_from_file(self, file_path: Path) -> Optional[str]:
        """从配置文件中提取版本号"""
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('version')
            
            elif suffix in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    # 查找版本信息
                    if isinstance(data, dict):
                        # 尝试直接获取version字段
                        if 'version' in data:
                            return str(data['version'])
                        # 尝试从注释中提取
                        content = file_path.read_text(encoding='utf-8')
                        for line in content.split('\n'):
                            if '版本:' in line or 'version:' in line.lower():
                                parts = line.split(':')
                                if len(parts) > 1:
                                    return parts[1].strip().lstrip(':').strip()
            
            elif suffix == '.py':
                # Python文件中的版本（如__version__）
                content = file_path.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if '__version__' in line or 'version =' in line:
                        parts = line.split('=')
                        if len(parts) > 1:
                            version = parts[1].strip().strip('"\' ')
                            return version
            
        except Exception as e:
            print(f"解析文件 {file_path} 时出错: {e}")
        
        return None
    
    def _find_version_in_directory(self, directory: Path, task_id: str) -> Optional[str]:
        """在目录中查找版本信息"""
        # 尝试常见配置文件
        common_files = [
            '_meta.json',
            'config.json',
            'config.yaml',
            'config.yml',
            'package.json',
            'pyproject.toml',
            'setup.py',
            'setup.cfg'
        ]
        
        for filename in common_files:
            file_path = directory / filename
            if file_path.exists():
                version = self._extract_version_from_file(file_path)
                if version:
                    return version
        
        # 对于特定Task的特殊处理
        if task_id == 'T01':
            # T01的特殊处理：从config.yaml注释中提取
            config_path = directory / 'config.yaml'
            if config_path.exists():
                content = config_path.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if '版本:' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            return parts[1].strip()
        
        return None
    
    def check_sync_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """检查同步状态"""
        results = {
            'synced': [],
            'out_of_sync': [],
            'missing': [],
            'total_tasks': 0
        }
        
        tasks = self.registry.get('tasks', [])
        if task_id:
            tasks = [t for t in tasks if t['id'] == task_id]
            if not tasks:
                print(f"错误: Task {task_id} 未在Registry中找到")
                return results
        
        results['total_tasks'] = len(tasks)
        
        for task in tasks:
            task_id = task['id']
            registry_version = task.get('version', '未知')
            
            source_version = self.get_version_from_source(task)
            
            if source_version is None:
                results['missing'].append({
                    'id': task_id,
                    'registry_version': registry_version,
                    'source_version': '未找到',
                    'location': task['location']
                })
            elif source_version == registry_version:
                results['synced'].append({
                    'id': task_id,
                    'version': registry_version,
                    'location': task['location']
                })
            else:
                results['out_of_sync'].append({
                    'id': task_id,
                    'registry_version': registry_version,
                    'source_version': source_version,
                    'location': task['location']
                })
        
        return results
    
    def sync_registry(self, task_id: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """同步Registry与代码版本"""
        results = self.check_sync_status(task_id)
        
        if dry_run:
            print("== 模拟运行 (dry-run) ==")
            print("以下Task将被更新:")
            for task in results['out_of_sync']:
                print(f"  {task['id']}: {task['registry_version']} -> {task['source_version']}")
            return results
        
        # 实际更新
        updated_count = 0
        tasks = self.registry.get('tasks', [])
        
        for i, task in enumerate(tasks):
            if task_id and task['id'] != task_id:
                continue
            
            source_version = self.get_version_from_source(task)
            if source_version and source_version != task.get('version'):
                # 更新版本
                old_version = task.get('version', '未知')
                task['version'] = source_version
                task['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                
                print(f"更新 Task {task['id']}: {old_version} -> {source_version}")
                updated_count += 1
        
        if updated_count > 0:
            # 更新整个Registry的last_updated
            self.registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            
            # 保存Registry
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 已更新 {updated_count} 个Task")
            print(f"Registry已保存: {self.registry_path}")
        else:
            print("✅ 所有Task均已同步，无需更新")
        
        return results
    
    def print_status_report(self, results: Dict[str, Any]):
        """打印状态报告"""
        print("\n" + "="*60)
        print("Task Registry 同步状态报告")
        print("="*60)
        
        print(f"\n📊 总计: {results['total_tasks']} 个Task")
        
        if results['synced']:
            print(f"\n✅ 已同步 ({len(results['synced'])}):")
            for task in results['synced']:
                print(f"  {task['id']}: {task['version']} ({task['location']})")
        
        if results['out_of_sync']:
            print(f"\n🔄 需同步 ({len(results['out_of_sync'])}):")
            for task in results['out_of_sync']:
                print(f"  {task['id']}: Registry={task['registry_version']}, "
                      f"代码={task['source_version']} ({task['location']})")
        
        if results['missing']:
            print(f"\n⚠️  版本缺失 ({len(results['missing'])}):")
            for task in results['missing']:
                print(f"  {task['id']}: Registry={task['registry_version']}, "
                      f"代码=未找到 ({task['location']})")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='同步Task Registry与代码版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s check                 # 检查同步状态
  %(prog)s sync                  # 执行同步
  %(prog)s sync --task T01       # 只同步T01
  %(prog)s sync --dry-run        # 模拟运行
  %(prog)s check --verbose       # 详细输出
        """
    )
    
    parser.add_argument(
        'action',
        choices=['check', 'sync'],
        help='操作: check=检查状态, sync=执行同步'
    )
    
    parser.add_argument(
        '--task',
        help='指定Task ID (如 T01), 默认处理所有Task'
    )
    
    parser.add_argument(
        '--registry',
        default='task_registry.json',
        help='Registry文件路径 (默认: task_registry.json)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际修改文件'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化同步器
        syncer = RegistrySyncer(args.registry)
        
        if args.action == 'check':
            # 检查状态
            results = syncer.check_sync_status(args.task)
            syncer.print_status_report(results)
            
            # 详细输出
            if args.verbose:
                print("\n📋 Registry信息:")
                print(f"  创建时间: {syncer.registry.get('created_date', '未知')}")
                print(f"  最后更新: {syncer.registry.get('last_updated', '未知')}")
                print(f"  任务数量: {len(syncer.registry.get('tasks', []))}")
        
        elif args.action == 'sync':
            # 执行同步
            results = syncer.sync_registry(args.task, args.dry_run)
            
            if args.verbose and not args.dry_run:
                syncer.print_status_report(results)
    
    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()