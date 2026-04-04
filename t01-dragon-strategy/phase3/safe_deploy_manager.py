#!/usr/bin/env python3
"""
Safe Deploy Manager Module - T01 Phase 3

Manages safe deployment of system changes with backup and rollback capabilities.
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DeploymentResult:
    """部署结果数据类"""
    success: bool
    deployed_version: str
    backup_path: str
    changes_applied: Dict[str, Any]
    timestamp: datetime
    message: str = ""


@dataclass
class RollbackResult:
    """回滚结果数据类"""
    success: bool
    rolled_back_to: str
    timestamp: datetime
    message: str = ""


class SafeDeployManager:
    """
    安全部署管理器
    
    职责:
    1. 创建系统变更前的备份
    2. 安全地应用配置变更
    3. 验证部署后的系统状态
    4. 在失败时执行回滚
    """
    
    def __init__(self, config_path: str = 'config.yaml', backup_dir: str = None):
        """
        初始化安全部署管理器
        
        Args:
            config_path: 主配置文件路径
            backup_dir: 备份目录路径
        """
        self.config_path = Path(config_path)
        
        if backup_dir is None:
            self.backup_dir = Path('backups/deployments')
        else:
            self.backup_dir = Path(backup_dir)
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 版本历史
        self.version_history_file = self.backup_dir / 'version_history.json'
        self.versions = self._load_version_history()
        
        logger.info("SafeDeployManager初始化完成")
    
    def _load_version_history(self) -> List[Dict[str, Any]]:
        """加载版本历史"""
        if self.version_history_file.exists():
            try:
                with open(self.version_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载版本历史失败: {e}")
        return []
    
    def _save_version_history(self):
        """保存版本历史"""
        try:
            with open(self.version_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.versions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存版本历史失败: {e}")
    
    def _generate_version(self) -> str:
        """生成新版本号"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"v{timestamp}"
    
    def _create_backup(self, version: str) -> str:
        """
        创建配置备份
        
        Args:
            version: 版本号
            
        Returns:
            备份路径
        """
        backup_path = self.backup_dir / version
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 备份配置文件
        if self.config_path.exists():
            shutil.copy2(self.config_path, backup_path / 'config.yaml')
        
        # 备份状态目录
        state_dir = Path('state')
        if state_dir.exists():
            shutil.copytree(state_dir, backup_path / 'state', dirs_exist_ok=True)
        
        logger.info(f"备份已创建: {backup_path}")
        return str(backup_path)
    
    def deploy_changes(self, changes: Dict[str, Any], 
                       validate: bool = True) -> DeploymentResult:
        """
        部署变更
        
        Args:
            changes: 要应用的变更
            validate: 是否验证部署
            
        Returns:
            DeploymentResult: 部署结果
        """
        version = self._generate_version()
        timestamp = datetime.now()
        
        try:
            # 1. 创建备份
            backup_path = self._create_backup(version)
            
            # 2. 应用变更
            self._apply_changes(changes)
            
            # 3. 验证部署（如果启用）
            if validate:
                validation = self.validate_deployment()
                if not validation.get('valid', False):
                    # 验证失败，回滚
                    self.rollback(version)
                    return DeploymentResult(
                        success=False,
                        deployed_version=version,
                        backup_path=backup_path,
                        changes_applied={},
                        timestamp=timestamp,
                        message=f"部署验证失败: {validation.get('errors', [])}"
                    )
            
            # 4. 记录版本
            self.versions.append({
                'version': version,
                'timestamp': timestamp.isoformat(),
                'changes': changes,
                'backup_path': backup_path,
                'status': 'deployed'
            })
            self._save_version_history()
            
            logger.info(f"部署成功: {version}")
            return DeploymentResult(
                success=True,
                deployed_version=version,
                backup_path=backup_path,
                changes_applied=changes,
                timestamp=timestamp,
                message="部署成功"
            )
            
        except Exception as e:
            logger.error(f"部署失败: {e}")
            # 尝试回滚
            try:
                self.rollback(version)
            except Exception as rollback_error:
                logger.error(f"回滚也失败: {rollback_error}")
            
            return DeploymentResult(
                success=False,
                deployed_version=version,
                backup_path="",
                changes_applied={},
                timestamp=timestamp,
                message=f"部署失败: {str(e)}"
            )
    
    def _apply_changes(self, changes: Dict[str, Any]):
        """
        应用变更到配置文件
        
        Args:
            changes: 变更字典
        """
        import yaml
        
        # 加载当前配置
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # 应用变更
        for key, value in changes.items():
            if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                config[key].update(value)
            else:
                config[key] = value
        
        # 保存配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"变更已应用: {list(changes.keys())}")
    
    def validate_deployment(self) -> Dict[str, Any]:
        """
        验证部署
        
        Returns:
            验证结果
        """
        errors = []
        checks_passed = 0
        
        # 1. 检查配置文件是否存在且有效
        if self.config_path.exists():
            try:
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                checks_passed += 1
            except Exception as e:
                errors.append(f"配置文件无效: {e}")
        else:
            errors.append("配置文件不存在")
        
        # 2. 检查必要的配置项
        if self.config_path.exists():
            try:
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                
                required_keys = ['api', 'strategy', 'data_sources']
                for key in required_keys:
                    if key in config:
                        checks_passed += 1
                    else:
                        errors.append(f"缺少必要配置项: {key}")
            except Exception as e:
                errors.append(f"配置检查失败: {e}")
        
        # 3. 检查数据目录
        data_dir = Path('data')
        if data_dir.exists():
            checks_passed += 1
        else:
            errors.append("数据目录不存在")
        
        # 4. 检查日志目录
        logs_dir = Path('logs')
        if logs_dir.exists():
            checks_passed += 1
        else:
            errors.append("日志目录不存在")
        
        return {
            'valid': len(errors) == 0,
            'checks_passed': checks_passed,
            'checks_failed': len(errors),
            'errors': errors
        }
    
    def rollback(self, version: str = None) -> RollbackResult:
        """
        回滚到指定版本
        
        Args:
            version: 要回滚到的版本，None表示回滚到上一个版本
            
        Returns:
            RollbackResult: 回滚结果
        """
        timestamp = datetime.now()
        
        try:
            if version is None:
                # 找到上一个成功部署的版本
                deployed_versions = [v for v in self.versions if v.get('status') == 'deployed']
                if len(deployed_versions) < 2:
                    return RollbackResult(
                        success=False,
                        rolled_back_to="",
                        timestamp=timestamp,
                        message="没有可回滚的版本"
                    )
                version = deployed_versions[-2]['version']
            
            backup_path = self.backup_dir / version
            
            if not backup_path.exists():
                return RollbackResult(
                    success=False,
                    rolled_back_to=version,
                    timestamp=timestamp,
                    message=f"备份不存在: {backup_path}"
                )
            
            # 恢复配置文件
            config_backup = backup_path / 'config.yaml'
            if config_backup.exists():
                shutil.copy2(config_backup, self.config_path)
            
            # 恢复状态目录
            state_backup = backup_path / 'state'
            if state_backup.exists():
                state_dir = Path('state')
                if state_dir.exists():
                    shutil.rmtree(state_dir)
                shutil.copytree(state_backup, state_dir)
            
            # 更新版本状态
            for v in self.versions:
                if v['version'] == version:
                    v['status'] = 'rolled_back'
            self._save_version_history()
            
            logger.info(f"回滚成功: {version}")
            return RollbackResult(
                success=True,
                rolled_back_to=version,
                timestamp=timestamp,
                message=f"成功回滚到 {version}"
            )
            
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return RollbackResult(
                success=False,
                rolled_back_to=version or "",
                timestamp=timestamp,
                message=f"回滚失败: {str(e)}"
            )
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return self.versions
    
    def get_current_version(self) -> Optional[str]:
        """获取当前版本"""
        deployed = [v for v in self.versions if v.get('status') == 'deployed']
        if deployed:
            return deployed[-1]['version']
        return None


def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Safe Deploy Manager 模块测试")
    print("="*60)
    
    manager = SafeDeployManager()
    
    # 测试部署
    print("\n1. 测试部署...")
    changes = {
        'scoring': {
            'weights': {
                'factor1': 0.5,
                'factor2': 0.5
            }
        }
    }
    result = manager.deploy_changes(changes)
    print(f"   部署成功: {result.success}")
    print(f"   版本: {result.deployed_version}")
    
    # 测试验证
    print("\n2. 测试验证...")
    validation = manager.validate_deployment()
    print(f"   验证通过: {validation['valid']}")
    print(f"   通过检查: {validation['checks_passed']}")
    
    # 测试回滚
    print("\n3. 测试回滚...")
    rollback = manager.rollback()
    print(f"   回滚成功: {rollback.success}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
