#!/usr/bin/env python3
"""
版本验证工具
验证当前版本与期望版本是否一致，确保100%准确
"""

import os
import sys
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VersionVerifier:
    """版本验证器"""
    
    def __init__(self, workspace_root: str = "/root/.openclaw/workspace"):
        self.workspace_root = Path(workspace_root)
    
    def verify_task_version(self, task_id: str, expected_version: str) -> Dict[str, Any]:
        """
        验证任务版本
        
        Args:
            task_id: 任务ID
            expected_version: 期望版本号
            
        Returns:
            验证结果
        """
        logger.info(f"验证任务 {task_id} 版本是否为 {expected_version}")
        
        verification = {
            'task_id': task_id,
            'expected_version': expected_version,
            'actual_version': None,
            'checks': [],
            'passed': False,
            'summary': ''
        }
        
        try:
            # 1. 检查配置文件版本
            config_check = self._check_config_version(task_id, expected_version)
            verification['checks'].append(config_check)
            
            # 2. 检查Git标签
            git_check = self._check_git_tag(task_id, expected_version)
            verification['checks'].append(git_check)
            
            # 3. 检查Task Registry
            registry_check = self._check_registry_version(task_id, expected_version)
            verification['checks'].append(registry_check)
            
            # 4. 检查关键文件完整性
            integrity_check = self._check_file_integrity(task_id)
            verification['checks'].append(integrity_check)
            
            # 5. 检查依赖环境
            env_check = self._check_environment(task_id)
            verification['checks'].append(env_check)
            
            # 总结
            passed_checks = sum(1 for check in verification['checks'] if check.get('passed', False))
            total_checks = len(verification['checks'])
            
            verification['passed_checks'] = passed_checks
            verification['total_checks'] = total_checks
            verification['success_rate'] = passed_checks / total_checks if total_checks > 0 else 0
            
            # 判断是否通过
            verification['passed'] = verification['success_rate'] >= 0.9  # 90%通过率
            
            # 设置实际版本
            for check in verification['checks']:
                if check.get('name') == 'config_version' and 'actual_version' in check:
                    verification['actual_version'] = check['actual_version']
                    break
            
            # 生成总结
            if verification['passed']:
                verification['summary'] = f"✅ 验证通过: {task_id} v{expected_version} ({passed_checks}/{total_checks} 检查通过)"
                logger.info(verification['summary'])
            else:
                verification['summary'] = f"❌ 验证失败: {task_id} v{expected_version} ({passed_checks}/{total_checks} 检查通过)"
                logger.warning(verification['summary'])
                
                # 显示失败详情
                for check in verification['checks']:
                    if not check.get('passed', False):
                        logger.warning(f"  检查失败: {check.get('name')} - {check.get('error', '未知错误')}")
            
            return verification
            
        except Exception as e:
            logger.error(f"验证过程出错: {e}")
            verification.update({
                'error': str(e),
                'passed': False,
                'summary': f"❌ 验证过程出错: {e}"
            })
            return verification
    
    def _check_config_version(self, task_id: str, expected_version: str) -> Dict[str, Any]:
        """检查配置文件版本"""
        check_result = {
            'name': 'config_version',
            'description': '检查配置文件版本',
            'passed': False
        }
        
        task_path = self.workspace_root / "tasks" / task_id
        if not task_path.exists():
            check_result['error'] = f"任务目录不存在: {task_path}"
            return check_result
        
        # 查找配置文件
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
                    logger.warning(f"读取配置文件失败 {config_file}: {e}")
        
        check_result['actual_version'] = actual_version
        check_result['config_file'] = str(config_file_found) if config_file_found else None
        
        if actual_version == expected_version:
            check_result['passed'] = True
            check_result['message'] = f"配置文件版本匹配: {actual_version}"
        elif actual_version is None:
            check_result['error'] = "未找到版本信息"
        else:
            check_result['error'] = f"版本不匹配: 期望 {expected_version}, 实际 {actual_version}"
        
        return check_result
    
    def _check_git_tag(self, task_id: str, expected_version: str) -> Dict[str, Any]:
        """检查Git标签"""
        check_result = {
            'name': 'git_tag',
            'description': '检查Git标签',
            'passed': False
        }
        
        try:
            import subprocess
            
            tag_name = f"{task_id}-v{expected_version}"
            result = subprocess.run(
                ['git', 'tag', '-l', tag_name],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and tag_name in result.stdout:
                check_result['passed'] = True
                check_result['message'] = f"Git标签存在: {tag_name}"
            else:
                check_result['error'] = f"Git标签不存在: {tag_name}"
                
        except Exception as e:
            check_result['error'] = f"检查Git标签失败: {e}"
        
        return check_result
    
    def _check_registry_version(self, task_id: str, expected_version: str) -> Dict[str, Any]:
        """检查Task Registry版本"""
        check_result = {
            'name': 'registry_version',
            'description': '检查Task Registry版本',
            'passed': False
        }
        
        registry_file = self.workspace_root / "task_registry.json"
        if not registry_file.exists():
            check_result['error'] = "Task Registry文件不存在"
            return check_result
        
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            registry_version = None
            for task in registry.get('tasks', []):
                if task.get('id') == task_id:
                    registry_version = task.get('version')
                    break
            
            check_result['registry_version'] = registry_version
            
            if registry_version == expected_version:
                check_result['passed'] = True
                check_result['message'] = f"Registry版本匹配: {registry_version}"
            elif registry_version is None:
                check_result['error'] = f"Registry中未找到任务: {task_id}"
            else:
                check_result['error'] = f"Registry版本不匹配: 期望 {expected_version}, 实际 {registry_version}"
                
        except Exception as e:
            check_result['error'] = f"读取Registry失败: {e}"
        
        return check_result
    
    def _check_file_integrity(self, task_id: str) -> Dict[str, Any]:
        """检查文件完整性"""
        check_result = {
            'name': 'file_integrity',
            'description': '检查关键文件完整性',
            'passed': False
        }
        
        task_path = self.workspace_root / "tasks" / task_id
        if not task_path.exists():
            check_result['error'] = f"任务目录不存在: {task_path}"
            return check_result
        
        # 定义关键文件（根据任务类型可能不同）
        critical_files = []
        
        if task_id == "T01":
            critical_files = [
                task_path / "config.yaml",
                task_path / "main.py",
                task_path / "limit_up_strategy_new.py",
                task_path / "scheduler.py"
            ]
        else:
            # 通用检查
            critical_files = [
                task_path / "config.yaml",
                task_path / "main.py"
            ]
        
        missing_files = []
        existing_files = []
        
        for file_path in critical_files:
            if file_path.exists():
                existing_files.append(str(file_path.relative_to(self.workspace_root)))
            else:
                missing_files.append(str(file_path.relative_to(self.workspace_root)))
        
        check_result['critical_files'] = [str(f.relative_to(self.workspace_root)) for f in critical_files]
        check_result['existing_files'] = existing_files
        check_result['missing_files'] = missing_files
        
        if not missing_files:
            check_result['passed'] = True
            check_result['message'] = f"所有关键文件都存在 ({len(existing_files)}/{len(critical_files)})"
        else:
            check_result['error'] = f"缺少关键文件: {', '.join(missing_files)}"
        
        return check_result
    
    def _check_environment(self, task_id: str) -> Dict[str, Any]:
        """检查环境变量"""
        check_result = {
            'name': 'environment',
            'description': '检查环境变量',
            'passed': False
        }
        
        # 根据任务类型检查必要的环境变量
        required_env_vars = []
        
        if task_id == "T01":
            required_env_vars = ['TUSHARE_TOKEN']
        elif task_id in ["T99", "T100"]:
            required_env_vars = []  # 这些任务可能不需要特定环境变量
        
        missing_vars = []
        existing_vars = []
        
        for var in required_env_vars:
            if var in os.environ and os.environ[var].strip():
                existing_vars.append(var)
            else:
                missing_vars.append(var)
        
        check_result['required_vars'] = required_env_vars
        check_result['existing_vars'] = existing_vars
        check_result['missing_vars'] = missing_vars
        
        if not missing_vars:
            check_result['passed'] = True
            check_result['message'] = f"所有必要环境变量都存在 ({len(existing_vars)}/{len(required_env_vars)})"
        else:
            check_result['error'] = f"缺少环境变量: {', '.join(missing_vars)}"
            check_result['warning'] = True  # 标记为警告而非错误
        
        return check_result
    
    def generate_report(self, verification_result: Dict[str, Any]) -> str:
        """生成验证报告"""
        report = []
        report.append("=" * 60)
        report.append("版本验证报告")
        report.append("=" * 60)
        report.append(f"任务: {verification_result['task_id']}")
        report.append(f"期望版本: {verification_result['expected_version']}")
        report.append(f"实际版本: {verification_result.get('actual_version', '未知')}")
        report.append(f"验证结果: {'✅ 通过' if verification_result['passed'] else '❌ 失败'}")
        report.append(f"通过率: {verification_result.get('success_rate', 0)*100:.1f}% ({verification_result.get('passed_checks', 0)}/{verification_result.get('total_checks', 0)})")
        report.append("")
        report.append("详细检查结果:")
        report.append("-" * 40)
        
        for check in verification_result.get('checks', []):
            status = "✅" if check.get('passed', False) else "❌"
            name = check.get('name', '未知检查')
            message = check.get('message', check.get('error', '无详情'))
            report.append(f"{status} {name}: {message}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='版本验证工具')
    parser.add_argument('--task', required=True, help='任务ID (如 T01)')
    parser.add_argument('--version', required=True, help='期望版本号 (如 1.2.0)')
    parser.add_argument('--workspace', default='/root/.openclaw/workspace', help='工作空间路径')
    parser.add_argument('--report', action='store_true', help='生成详细报告')
    
    args = parser.parse_args()
    
    try:
        verifier = VersionVerifier(args.workspace)
        result = verifier.verify_task_version(args.task, args.version)
        
        if args.report:
            report = verifier.generate_report(result)
            print(report)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 退出码：0表示通过，1表示失败
        sys.exit(0 if result.get('passed', False) else 1)
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()