#!/usr/bin/env python3
"""
版本快照创建工具
为任务创建完整的版本快照，包括代码、配置和元数据
"""

import os
import sys
import json
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
import subprocess
import argparse
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VersionSnapshotCreator:
    """版本快照创建器"""
    
    def __init__(self, workspace_root: str = "/root/.openclaw/workspace"):
        self.workspace_root = Path(workspace_root)
        self.snapshots_dir = self.workspace_root / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        
    def create_snapshot(self, task_id: str, version: Optional[str] = None, message: str = "") -> Dict[str, Any]:
        """
        创建任务版本快照
        
        Args:
            task_id: 任务ID (如 "T01")
            version: 版本号 (如 "1.2.0")，如果为None则从配置读取
            message: 版本描述信息
            
        Returns:
            快照元数据
        """
        logger.info(f"开始创建任务 {task_id} 版本快照")
        
        # 1. 获取任务信息
        task_info = self._get_task_info(task_id)
        if not task_info:
            raise ValueError(f"任务 {task_id} 不存在或信息不全")
        
        # 2. 确定版本号
        if version is None:
            version = task_info.get('version', '1.0.0')
        
        # 3. 获取Git信息
        git_info = self._get_git_info()
        
        # 4. 创建快照内容
        snapshot = {
            'metadata': {
                'task_id': task_id,
                'version': version,
                'created_at': datetime.now().isoformat(),
                'git_commit': git_info.get('commit_hash', ''),
                'git_branch': git_info.get('branch', ''),
                'message': message or f"{task_id} version {version}",
                'creator': 'VersionSnapshotCreator'
            },
            'task_info': task_info,
            'files': self._scan_task_files(task_id),
            'registry_state': self._get_registry_state(),
            'environment': self._capture_environment()
        }
        
        # 5. 保存快照文件
        snapshot_file = self._save_snapshot(snapshot, task_id, version)
        
        # 6. Git操作：提交并打标签
        if git_info.get('is_git_repo', False):
            self._git_commit_and_tag(task_id, version, message)
        
        # 7. 更新Task Registry中的快照信息
        self._update_registry_snapshot(task_id, version, snapshot_file)
        
        logger.info(f"✅ 任务 {task_id} 版本 {version} 快照创建完成: {snapshot_file}")
        
        return {
            'success': True,
            'task_id': task_id,
            'version': version,
            'snapshot_file': str(snapshot_file),
            'git_tag': f"{task_id}-v{version}",
            'message': message
        }
    
    def _get_task_info(self, task_id: str) -> Dict[str, Any]:
        """获取任务信息"""
        # 首先从Task Registry获取任务位置
        registry_file = self.workspace_root / "task_registry.json"
        task_path = None
        version_from_registry = None
        
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                
                for task in registry.get('tasks', []):
                    if task.get('id') == task_id:
                        location = task.get('location', '')
                        if location:
                            task_path = self.workspace_root / location
                            version_from_registry = task.get('version')
                            break
            except Exception as e:
                logger.warning(f"读取Registry失败: {e}")
        
        # 如果Registry中没有找到，尝试默认路径
        if task_path is None or not task_path.exists():
            # 尝试tasks目录
            task_path = self.workspace_root / "tasks" / task_id
        
        # 如果tasks目录不存在，尝试skills目录
        if not task_path.exists():
            task_path = self.workspace_root / "skills" / task_id
        
        if not task_path.exists():
            raise ValueError(f"任务目录不存在: {task_path}")
        
        # 查找配置文件
        config_files = [
            task_path / "config.yaml",
            task_path / "config.json",
            task_path / "_meta.json"
        ]
        
        config = {}
        config_file_found = None
        for config_file in config_files:
            if config_file.exists():
                try:
                    if config_file.suffix == '.yaml':
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                    elif config_file.suffix == '.json':
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    
                    if config:
                        config_file_found = config_file
                        break
                except Exception as e:
                    logger.warning(f"读取配置文件失败 {config_file}: {e}")
        
        # 获取版本号：优先使用Registry中的版本，其次配置文件中的版本
        version = version_from_registry or config.get('version', '1.0.0')
        
        # 扫描任务文件
        task_files = []
        for file_path in task_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.workspace_root)
                task_files.append(str(rel_path))
        
        return {
            'path': str(task_path.relative_to(self.workspace_root)),
            'version': version,
            'config': config,
            'config_file': str(config_file_found) if config_file_found else None,
            'files': task_files,
            'file_count': len(task_files),
            'source': 'registry' if version_from_registry else 'config_file'
        }
    
    def _get_git_info(self) -> Dict[str, Any]:
        """获取Git仓库信息"""
        git_info = {
            'is_git_repo': False,
            'commit_hash': '',
            'branch': '',
            'status': ''
        }
        
        try:
            # 检查是否在Git仓库中
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                git_info['is_git_repo'] = True
                
                # 获取当前commit
                commit_result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True
                )
                if commit_result.returncode == 0:
                    git_info['commit_hash'] = commit_result.stdout.strip()
                
                # 获取当前分支
                branch_result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True
                )
                if branch_result.returncode == 0:
                    git_info['branch'] = branch_result.stdout.strip()
                
                # 获取状态
                status_result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True
                )
                if status_result.returncode == 0:
                    git_info['status'] = status_result.stdout.strip()
                    
        except Exception as e:
            logger.debug(f"获取Git信息失败: {e}")
        
        return git_info
    
    def _scan_task_files(self, task_id: str) -> List[Dict[str, Any]]:
        """扫描任务文件并计算校验和"""
        task_path = self.workspace_root / "tasks" / task_id
        files_info = []
        
        for file_path in task_path.rglob('*'):
            if file_path.is_file():
                try:
                    # 计算文件哈希
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # 获取文件信息
                    stat = file_path.stat()
                    
                    files_info.append({
                        'path': str(file_path.relative_to(self.workspace_root)),
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'checksum': f"sha256:{file_hash}",
                        'checksum_type': 'sha256'
                    })
                    
                except Exception as e:
                    logger.warning(f"处理文件失败 {file_path}: {e}")
        
        return files_info
    
    def _get_registry_state(self) -> Dict[str, Any]:
        """获取Task Registry状态"""
        registry_file = self.workspace_root / "task_registry.json"
        
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取Registry失败: {e}")
        
        return {}
    
    def _capture_environment(self) -> Dict[str, Any]:
        """捕获环境信息"""
        env_vars = {}
        important_vars = [
            'TAVILY_API_KEY',
            'TUSHARE_TOKEN',
            'OPENAI_API_KEY',
            'DEEPSEEK_API_KEY',
            'PATH',
            'PYTHONPATH'
        ]
        
        for var in important_vars:
            if var in os.environ:
                # 隐藏敏感信息的值
                if 'KEY' in var or 'TOKEN' in var or 'SECRET' in var:
                    value = os.environ[var]
                    if value:
                        env_vars[var] = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                else:
                    env_vars[var] = os.environ[var]
        
        # Python信息
        env_vars['python_version'] = sys.version
        
        return env_vars
    
    def _save_snapshot(self, snapshot: Dict[str, Any], task_id: str, version: str) -> Path:
        """保存快照到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{task_id}_v{version}_{timestamp}.json"
        snapshot_file = self.snapshots_dir / filename
        
        # 确保snapshots目录存在
        self.snapshots_dir.mkdir(exist_ok=True)
        
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        return snapshot_file
    
    def _git_commit_and_tag(self, task_id: str, version: str, message: str) -> bool:
        """执行Git提交和打标签"""
        try:
            # 添加所有文件
            subprocess.run(
                ['git', 'add', '.'],
                cwd=self.workspace_root,
                capture_output=True,
                check=True
            )
            
            # 提交
            commit_message = f"{task_id} v{version}: {message}" if message else f"{task_id} version {version}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.workspace_root,
                capture_output=True,
                check=False  # 允许没有变化的情况
            )
            
            # 打标签
            tag_name = f"{task_id}-v{version}"
            subprocess.run(
                ['git', 'tag', '-a', tag_name, '-m', f"{task_id} version {version}"],
                cwd=self.workspace_root,
                capture_output=True,
                check=True
            )
            
            logger.info(f"✅ Git标签创建: {tag_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Git操作失败: {e}")
            return False
    
    def _update_registry_snapshot(self, task_id: str, version: str, snapshot_file: Path) -> bool:
        """更新Task Registry中的快照信息"""
        registry_file = self.workspace_root / "task_registry.json"
        
        if not registry_file.exists():
            logger.warning("Task Registry文件不存在")
            return False
        
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            # 查找任务
            for task in registry.get('tasks', []):
                if task.get('id') == task_id:
                    # 添加快照信息
                    if 'snapshots' not in task:
                        task['snapshots'] = []
                    
                    task['snapshots'].append({
                        'version': version,
                        'snapshot_file': str(snapshot_file.relative_to(self.workspace_root)),
                        'created_at': datetime.now().isoformat()
                    })
                    
                    # 更新最后更新时间
                    task['last_updated'] = datetime.now().strftime("%Y-%m-%d")
                    
                    break
            
            # 保存更新
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Task Registry更新: {task_id} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"更新Registry失败: {e}")
            return False


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='创建任务版本快照')
    parser.add_argument('--task', required=True, help='任务ID (如 T01)')
    parser.add_argument('--version', help='版本号 (如 1.2.0)，默认从配置读取')
    parser.add_argument('--message', '-m', default='', help='版本描述信息')
    parser.add_argument('--workspace', default='/root/.openclaw/workspace', help='工作空间路径')
    
    args = parser.parse_args()
    
    try:
        creator = VersionSnapshotCreator(args.workspace)
        result = creator.create_snapshot(args.task, args.version, args.message)
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"创建快照失败: {e}")
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()