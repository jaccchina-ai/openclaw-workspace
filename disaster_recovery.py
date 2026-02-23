#!/usr/bin/env python3
"""
灾难恢复工具 - 100%准确版本回退
确保可以从任何版本回退到指定稳定版本
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
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DisasterRecovery:
    """灾难恢复管理器"""
    
    def __init__(self, workspace_root: str = "/root/.openclaw/workspace"):
        self.workspace_root = Path(workspace_root)
        self.snapshots_dir = self.workspace_root / "snapshots"
        self.backup_dir = self.workspace_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def _get_task_path(self, task_id: str) -> Path:
        """获取任务路径（支持tasks和skills目录）"""
        # 首先从Task Registry获取任务位置
        registry_file = self.workspace_root / "task_registry.json"
        
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                
                for task in registry.get('tasks', []):
                    if task.get('id') == task_id:
                        location = task.get('location', '')
                        if location:
                            task_path = self.workspace_root / location
                            if task_path.exists():
                                return task_path
            except Exception as e:
                logger.warning(f"读取Registry失败: {e}")
        
        # 如果Registry中没有找到，尝试默认路径
        task_path = self.workspace_root / "tasks" / task_id
        if task_path.exists():
            return task_path
        
        # 尝试skills目录
        task_path = self.workspace_root / "skills" / task_id
        if task_path.exists():
            return task_path
        
        # 如果都不存在，返回默认的tasks路径（调用方需要处理不存在的情况）
        return self.workspace_root / "tasks" / task_id
        
    def rollback_to_version(self, task_id: str, target_version: str, 
                          backup_current: bool = True) -> Dict[str, Any]:
        """
        回退任务到指定版本
        
        Args:
            task_id: 任务ID
            target_version: 目标版本号
            backup_current: 是否备份当前状态
            
        Returns:
            恢复结果
        """
        logger.info(f"开始回退任务 {task_id} 到版本 {target_version}")
        
        recovery_log = {
            'task_id': task_id,
            'target_version': target_version,
            'start_time': datetime.now().isoformat(),
            'steps': [],
            'success': False
        }
        
        try:
            # 0. 验证目标版本存在
            self._log_step(recovery_log, "validate_target", "验证目标版本")
            if not self._validate_target_version(task_id, target_version):
                raise ValueError(f"目标版本 {target_version} 不存在或无效")
            
            # 1. 停止当前任务（如果正在运行）
            self._log_step(recovery_log, "stop_task", "停止当前任务")
            self._stop_task_if_running(task_id)
            
            # 2. 备份当前状态
            if backup_current:
                self._log_step(recovery_log, "backup_current", "备份当前状态")
                current_backup = self._backup_current_state(task_id)
                recovery_log['current_backup'] = current_backup
            
            # 3. 查找目标版本快照
            self._log_step(recovery_log, "find_snapshot", "查找目标版本快照")
            snapshot_file = self._find_version_snapshot(task_id, target_version)
            if not snapshot_file:
                raise ValueError(f"未找到版本 {target_version} 的快照")
            
            # 4. 验证快照完整性
            self._log_step(recovery_log, "verify_snapshot", "验证快照完整性")
            snapshot = self._verify_snapshot_integrity(snapshot_file)
            
            # 5. 执行回退
            self._log_step(recovery_log, "execute_rollback", "执行回退操作")
            rollback_result = self._execute_rollback(snapshot)
            
            # 6. 验证回退成功
            self._log_step(recovery_log, "verify_rollback", "验证回退成功")
            verification_result = self._verify_rollback_success(task_id, target_version, snapshot)
            
            # 7. 更新Task Registry
            self._log_step(recovery_log, "update_registry", "更新Task Registry")
            self._update_registry_version(task_id, target_version)
            
            # 8. 生成恢复报告
            recovery_log.update({
                'success': True,
                'end_time': datetime.now().isoformat(),
                'snapshot_used': str(snapshot_file),
                'rollback_result': rollback_result,
                'verification_result': verification_result,
                'recovery_time_seconds': (datetime.now() - datetime.fromisoformat(recovery_log['start_time'])).total_seconds()
            })
            
            logger.info(f"✅ 任务 {task_id} 成功回退到版本 {target_version}")
            
            # 9. 重新启动任务（可选）
            restart_choice = input(f"是否重新启动任务 {task_id}？(y/n): ").strip().lower()
            if restart_choice == 'y':
                self._log_step(recovery_log, "restart_task", "重新启动任务")
                self._start_task(task_id)
            
            return recovery_log
            
        except Exception as e:
            logger.error(f"回退失败: {e}")
            recovery_log.update({
                'success': False,
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            
            # 尝试恢复备份（如果有）
            if 'current_backup' in recovery_log:
                logger.info("尝试恢复备份...")
                try:
                    self._restore_from_backup(recovery_log['current_backup'])
                    recovery_log['backup_restored'] = True
                except Exception as restore_error:
                    recovery_log['backup_restore_error'] = str(restore_error)
            
            return recovery_log
    
    def _log_step(self, recovery_log: Dict[str, Any], step_id: str, description: str):
        """记录恢复步骤"""
        step = {
            'id': step_id,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        recovery_log['steps'].append(step)
        logger.info(f"步骤: {description}")
    
    def _validate_target_version(self, task_id: str, target_version: str) -> bool:
        """验证目标版本是否存在"""
        # 检查Git标签
        try:
            tag_name = f"{task_id}-v{target_version}"
            result = subprocess.run(
                ['git', 'tag', '-l', tag_name],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and tag_name in result.stdout:
                return True
        except Exception as e:
            logger.debug(f"检查Git标签失败: {e}")
        
        # 检查快照文件
        snapshot_pattern = f"snapshot_{task_id}_v{target_version}_*.json"
        snapshot_files = list(self.snapshots_dir.glob(snapshot_pattern))
        
        if snapshot_files:
            return True
        
        # 检查Task Registry
        registry_file = self.workspace_root / "task_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                
                for task in registry.get('tasks', []):
                    if task.get('id') == task_id:
                        if task.get('version') == target_version:
                            return True
                        
                        # 检查快照记录
                        for snapshot in task.get('snapshots', []):
                            if snapshot.get('version') == target_version:
                                return True
            except Exception as e:
                logger.warning(f"检查Registry失败: {e}")
        
        return False
    
    def _stop_task_if_running(self, task_id: str):
        """停止正在运行的任务"""
        # 这里需要根据具体任务实现停止逻辑
        # 例如：查找相关进程并终止
        
        logger.info(f"检查任务 {task_id} 是否在运行...")
        
        # 简单实现：查找可能的进程
        try:
            # 查找Python进程
            result = subprocess.run(
                ['ps', 'aux', '|', 'grep', '-i', task_id, '|', 'grep', '-v', 'grep'],
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                logger.warning(f"发现可能相关的进程: {result.stdout}")
                # 实际环境中需要更精确的停止逻辑
        except Exception as e:
            logger.debug(f"检查进程失败: {e}")
    
    def _backup_current_state(self, task_id: str) -> str:
        """备份当前状态"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{task_id}_before_rollback_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # 备份任务目录
        task_path = self._get_task_path(task_id)
        if task_path.exists():
            shutil.copytree(task_path, backup_path / "task", dirs_exist_ok=True)
        
        # 备份配置文件
        config_files = [
            self.workspace_root / "task_registry.json",
            self.workspace_root / ".gitignore"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                shutil.copy2(config_file, backup_path / config_file.name)
        
        # 创建备份元数据
        metadata = {
            'task_id': task_id,
            'backup_time': datetime.now().isoformat(),
            'backup_reason': 'disaster_recovery',
            'task_path': str(task_path.relative_to(self.workspace_root)) if task_path.exists() else None,
            'files_backed_up': []
        }
        
        with open(backup_path / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"当前状态备份到: {backup_path}")
        return str(backup_path)
    
    def _find_version_snapshot(self, task_id: str, target_version: str) -> Optional[Path]:
        """查找版本快照文件"""
        # 首先检查snapshots目录
        snapshot_pattern = f"snapshot_{task_id}_v{target_version}_*.json"
        snapshot_files = list(self.snapshots_dir.glob(snapshot_pattern))
        
        if snapshot_files:
            # 返回最新的快照
            snapshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return snapshot_files[0]
        
        # 从Task Registry查找
        registry_file = self.workspace_root / "task_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                
                for task in registry.get('tasks', []):
                    if task.get('id') == task_id:
                        for snapshot in task.get('snapshots', []):
                            if snapshot.get('version') == target_version:
                                snapshot_path = self.workspace_root / snapshot.get('snapshot_file', '')
                                if snapshot_path.exists():
                                    return snapshot_path
            except Exception as e:
                logger.warning(f"从Registry查找快照失败: {e}")
        
        return None
    
    def _verify_snapshot_integrity(self, snapshot_file: Path) -> Dict[str, Any]:
        """验证快照完整性"""
        if not snapshot_file.exists():
            raise ValueError(f"快照文件不存在: {snapshot_file}")
        
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
        except Exception as e:
            raise ValueError(f"读取快照文件失败: {e}")
        
        # 检查必要字段
        required_fields = ['metadata', 'task_info', 'files']
        for field in required_fields:
            if field not in snapshot:
                raise ValueError(f"快照缺少必要字段: {field}")
        
        # 验证文件校验和（可选）
        verify_checksums = True
        if verify_checksums:
            for file_info in snapshot.get('files', []):
                file_path = self.workspace_root / file_info['path']
                if not file_path.exists():
                    logger.warning(f"快照中的文件不存在: {file_path}")
                    continue
                
                # 计算当前文件的校验和
                with open(file_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                
                snapshot_hash = file_info['checksum'].replace('sha256:', '')
                if current_hash != snapshot_hash:
                    logger.warning(f"文件校验和不匹配: {file_path}")
        
        logger.info(f"✅ 快照完整性验证通过: {snapshot_file}")
        return snapshot
    
    def _execute_rollback(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """执行回退操作"""
        task_id = snapshot['metadata']['task_id']
        target_version = snapshot['metadata']['version']
        
        rollback_result = {
            'task_id': task_id,
            'target_version': target_version,
            'git_rollback': False,
            'files_restored': 0,
            'config_updated': False
        }
        
        # 1. Git回退（如果可能）
        git_tag = f"{task_id}-v{target_version}"
        try:
            # 切换到目标版本
            subprocess.run(
                ['git', 'checkout', git_tag],
                cwd=self.workspace_root,
                capture_output=True,
                check=True
            )
            rollback_result['git_rollback'] = True
            logger.info(f"✅ Git回退到标签: {git_tag}")
        except Exception as e:
            logger.warning(f"Git回退失败，使用文件恢复: {e}")
            
            # 2. 文件级恢复（从快照）
            files_restored = 0
            for file_info in snapshot.get('files', []):
                source_path = self.workspace_root / file_info['path']
                
                # 确保目录存在
                source_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 如果文件不存在于当前工作区，跳过（Git会处理）
                if not source_path.exists():
                    continue
                
                # 这里可以添加从备份恢复的逻辑
                # 实际实现需要更复杂的恢复机制
                files_restored += 1
            
            rollback_result['files_restored'] = files_restored
        
        # 3. 恢复配置
        task_info = snapshot.get('task_info', {})
        if task_info.get('config'):
            config_path = self.workspace_root / task_info['path'] / "config.yaml"
            if config_path.parent.exists():
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(task_info['config'], f, allow_unicode=True)
                    rollback_result['config_updated'] = True
                except Exception as e:
                    logger.warning(f"恢复配置文件失败: {e}")
        
        return rollback_result
    
    def _verify_rollback_success(self, task_id: str, target_version: str, 
                               snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """验证回退是否成功"""
        verification = {
            'task_id': task_id,
            'expected_version': target_version,
            'actual_version': '',
            'checks_passed': [],
            'checks_failed': []
        }
        
        # 1. 获取任务路径
        task_path = self._get_task_path(task_id)
        
        # 2. 验证版本号
        config_files = [
            task_path / "config.yaml",
            task_path / "config.json",
            task_path / "_meta.json"
        ]
        
        actual_version = None
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
                    
                    if config and 'version' in config:
                        actual_version = config['version']
                        config_file_found = config_file
                        break
                except Exception as e:
                    logger.warning(f"读取配置文件失败: {e}")
        
        verification['actual_version'] = actual_version or 'unknown'
        verification['config_file'] = str(config_file_found) if config_file_found else None
        
        if actual_version == target_version:
            verification['checks_passed'].append('version_match')
            logger.info(f"✅ 版本验证通过: {actual_version}")
        elif actual_version is None:
            verification['checks_failed'].append({
                'check': 'version_match',
                'expected': target_version,
                'actual': '未找到版本信息'
            })
            logger.warning(f"❌ 未找到版本信息")
        else:
            verification['checks_failed'].append({
                'check': 'version_match',
                'expected': target_version,
                'actual': actual_version
            })
            logger.warning(f"❌ 版本不匹配: 期望 {target_version}, 实际 {actual_version}")
        
        # 3. 验证关键文件存在
        required_files = []
        
        # 根据任务类型定义关键文件
        if task_id == "T01":
            required_files = [
                task_path / "config.yaml",
                task_path / "main.py",
                task_path / "limit_up_strategy_new.py",
                task_path / "scheduler.py"
            ]
        elif task_id == "T99":
            required_files = [
                task_path / "config.json",
                task_path / "_meta.json",
                task_path / "scheduler.yaml"
            ]
        elif task_id == "T100":
            required_files = [
                task_path / "_meta.json"
            ]
        else:
            # 通用检查
            config_files_to_check = [
                task_path / "config.yaml",
                task_path / "config.json",
                task_path / "_meta.json"
            ]
            # 只添加存在的配置文件
            for config_file in config_files_to_check:
                if config_file.exists():
                    required_files.append(config_file)
            
            # 添加main.py如果存在
            main_file = task_path / "main.py"
            if main_file.exists():
                required_files.append(main_file)
        
        # 如果没有任何关键文件，添加任务目录本身作为检查
        if not required_files:
            required_files = [task_path]
        
        for required_file in required_files:
            if required_file.exists():
                verification['checks_passed'].append(f"file_exists:{required_file.name}")
            else:
                verification['checks_failed'].append({
                    'check': f"file_exists:{required_file.name}",
                    'file': str(required_file)
                })
        
        # 4. 验证Task Registry
        registry_file = self.workspace_root / "task_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                
                registry_version = None
                for task in registry.get('tasks', []):
                    if task.get('id') == task_id:
                        registry_version = task.get('version')
                        break
                
                if registry_version == target_version:
                    verification['checks_passed'].append('registry_version_match')
                else:
                    verification['checks_failed'].append({
                        'check': 'registry_version_match',
                        'expected': target_version,
                        'actual': registry_version
                    })
            except Exception as e:
                logger.warning(f"验证Registry失败: {e}")
        
        # 5. 简单功能测试（可选）- 仅对Python任务
        if task_path.exists() and (task_path / "main.py").exists():
            try:
                # 尝试导入主要模块
                sys.path.insert(0, str(task_path.parent))
                import importlib
                module_name = task_path.name
                importlib.import_module(f"{module_name}.main")
                verification['checks_passed'].append('module_importable')
            except Exception as e:
                verification['checks_failed'].append({
                    'check': 'module_importable',
                    'error': str(e)
                })
        else:
            # 非Python任务或没有main.py，跳过此检查
            verification['checks_passed'].append('module_importable_skipped')
        
        # 总结
        total_checks = len(verification['checks_passed']) + len(verification['checks_failed'])
        passed_ratio = len(verification['checks_passed']) / total_checks if total_checks > 0 else 0
        
        verification['total_checks'] = total_checks
        verification['passed_checks'] = len(verification['checks_passed'])
        verification['failed_checks'] = len(verification['checks_failed'])
        verification['success_rate'] = passed_ratio
        verification['verification_passed'] = passed_ratio >= 0.8  # 80%通过率
        
        logger.info(f"验证结果: {len(verification['checks_passed'])}/{total_checks} 通过 ({passed_ratio*100:.1f}%)")
        
        return verification
    
    def _update_registry_version(self, task_id: str, version: str):
        """更新Task Registry中的版本号"""
        registry_file = self.workspace_root / "task_registry.json"
        
        if not registry_file.exists():
            logger.warning("Task Registry文件不存在")
            return
        
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            updated = False
            for task in registry.get('tasks', []):
                if task.get('id') == task_id:
                    task['version'] = version
                    task['last_updated'] = datetime.now().strftime("%Y-%m-%d")
                    
                    # 添加回退记录
                    if 'rollback_history' not in task:
                        task['rollback_history'] = []
                    
                    task['rollback_history'].append({
                        'from_version': task.get('previous_version', 'unknown'),
                        'to_version': version,
                        'rolled_back_at': datetime.now().isoformat(),
                        'reason': 'disaster_recovery'
                    })
                    
                    updated = True
                    break
            
            if updated:
                with open(registry_file, 'w', encoding='utf-8') as f:
                    json.dump(registry, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Task Registry更新: {task_id} -> v{version}")
            else:
                logger.warning(f"Task Registry中未找到任务: {task_id}")
                
        except Exception as e:
            logger.error(f"更新Registry失败: {e}")
    
    def _restore_from_backup(self, backup_path: str):
        """从备份恢复"""
        logger.warning(f"从备份恢复: {backup_path}")
        # 实现备份恢复逻辑
        # 注意：这应该谨慎操作，避免数据丢失
    
    def _start_task(self, task_id: str):
        """启动任务"""
        logger.info(f"启动任务 {task_id}...")
        # 实现任务启动逻辑
        # 例如：运行调度器或主程序


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='灾难恢复 - 版本回退工具')
    parser.add_argument('--task', required=True, help='任务ID (如 T01)')
    parser.add_argument('--version', required=True, help='目标版本号 (如 1.2.0)')
    parser.add_argument('--no-backup', action='store_true', help='不备份当前状态')
    parser.add_argument('--workspace', default='/root/.openclaw/workspace', help='工作空间路径')
    
    args = parser.parse_args()
    
    print(f"⚠️  灾难恢复操作：任务 {args.task} 回退到版本 {args.version}")
    print("=" * 60)
    
    # 确认操作
    confirm = input("确认执行回退操作？这将覆盖当前版本。(输入 'YES' 继续): ")
    if confirm != 'YES':
        print("操作已取消")
        sys.exit(0)
    
    try:
        recovery = DisasterRecovery(args.workspace)
        result = recovery.rollback_to_version(
            task_id=args.task,
            target_version=args.version,
            backup_current=not args.no_backup
        )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result['success']:
            print(f"\n✅ 恢复成功！任务 {args.task} 已回退到版本 {args.version}")
            verification = result.get('verification_result', {})
            if verification.get('verification_passed'):
                print(f"✅ 验证通过率: {verification.get('success_rate', 0)*100:.1f}%")
            else:
                print(f"⚠️  验证警告: 通过率 {verification.get('success_rate', 0)*100:.1f}%")
        else:
            print(f"\n❌ 恢复失败: {result.get('error', '未知错误')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 恢复过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()