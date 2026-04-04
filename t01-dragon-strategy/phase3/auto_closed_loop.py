#!/usr/bin/env python3
"""
Auto Closed Loop Controller Module - T01 Phase 3

The final integration module that orchestrates all Phase 3 components:
- evolution_trigger.py - for triggering evolution
- safe_deploy_manager.py - for safe deployment
- performance_guardian.py - for monitoring
- alpha_factor_discovery.py - for factor discovery
- attribution_analyzer.py - for attribution analysis
- adaptive_threshold_manager.py - for threshold management

This module implements the main control loop with a state machine for evolution phases.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
import traceback

# 配置日志
logger = logging.getLogger(__name__)

# 导入Phase 3组件
try:
    from evolution_trigger import EvolutionTrigger, TriggerType
    from safe_deploy_manager import SafeDeployManager, DeploymentResult, RollbackResult
    from performance_guardian import PerformanceGuardian, AlertLevel
    from alpha_factor_discovery import AlphaFactorDiscovery
    from attribution_analyzer import AttributionAnalyzer
    from adaptive_threshold_manager import AdaptiveThresholdManager
    PHASE3_MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phase 3模块导入失败: {e}")
    PHASE3_MODULES_AVAILABLE = False

# 导入AutoEvolution（Phase 2）
try:
    from auto_evolution import AutoEvolution
    AUTO_EVOLUTION_AVAILABLE = True
except ImportError:
    logger.warning("AutoEvolution模块不可用")
    AUTO_EVOLUTION_AVAILABLE = False


class EvolutionPhase(Enum):
    """
    进化阶段状态机枚举
    
    IDLE: 等待触发
    EVOLVING: 运行进化
    DEPLOYING: 部署变更
    VALIDATING: 验证部署
    ROLLING_BACK: 回滚失败的变更
    """
    IDLE = "idle"
    EVOLVING = "evolving"
    DEPLOYING = "deploying"
    VALIDATING = "validating"
    ROLLING_BACK = "rolling_back"


@dataclass
class EvolutionState:
    """进化状态数据类"""
    phase: EvolutionPhase
    start_time: datetime
    current_iteration: int = 0
    last_trigger_check: Optional[datetime] = None
    deployment_result: Optional[DeploymentResult] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'phase': self.phase.value,
            'start_time': self.start_time.isoformat(),
            'current_iteration': self.current_iteration,
            'last_trigger_check': self.last_trigger_check.isoformat() if self.last_trigger_check else None,
            'deployment_result': {
                'success': self.deployment_result.success,
                'version': self.deployment_result.deployed_version
            } if self.deployment_result else None,
            'error_message': self.error_message
        }


@dataclass
class EvolutionReport:
    """进化报告数据类"""
    timestamp: datetime
    state: EvolutionState
    trigger_result: Dict[str, Any]
    evolution_result: Dict[str, Any]
    deployment_result: Optional[DeploymentResult]
    validation_result: Dict[str, Any]
    performance_check: Dict[str, Any]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'state': self.state.to_dict(),
            'trigger_result': self.trigger_result,
            'evolution_result': self.evolution_result,
            'deployment_result': {
                'success': self.deployment_result.success,
                'version': self.deployment_result.deployed_version,
                'backup_path': self.deployment_result.backup_path
            } if self.deployment_result else None,
            'validation_result': self.validation_result,
            'performance_check': self.performance_check,
            'recommendations': self.recommendations
        }


class AutoClosedLoop:
    """
    自动闭环控制器
    
    职责:
    1. 协调所有Phase 3组件
    2. 管理进化状态机
    3. 执行主控制循环
    4. 处理部署和回滚
    5. 生成综合报告
    """
    
    def __init__(self, config_path: str = 'config.yaml', tushare_token: str = None):
        """
        初始化自动闭环控制器
        
        Args:
            config_path: 配置文件路径
            tushare_token: Tushare API token
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Tushare token
        self.tushare_token = tushare_token or self.config.get('tushare_token', os.getenv('TUSHARE_TOKEN'))
        
        # 初始化Phase 3组件
        self._init_components()
        
        # 初始化状态
        self.state = EvolutionState(
            phase=EvolutionPhase.IDLE,
            start_time=datetime.now(),
            current_iteration=0
        )
        
        # 报告目录
        self.reports_dir = Path('reports/auto_closed_loop')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 运行标志
        self._running = False
        
        logger.info("AutoClosedLoop初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
            return {}
    
    def _init_components(self):
        """初始化所有组件"""
        if not PHASE3_MODULES_AVAILABLE:
            logger.error("Phase 3模块不可用，无法初始化组件")
            return
        
        try:
            # 1. 进化触发器
            self.evolution_trigger = EvolutionTrigger(
                config_path=str(self.config_path)
            )
            logger.info("EvolutionTrigger初始化完成")
            
            # 2. 安全部署管理器
            self.deploy_manager = SafeDeployManager(
                config_path=str(self.config_path)
            )
            logger.info("SafeDeployManager初始化完成")
            
            # 3. 性能守护器
            self.performance_guardian = PerformanceGuardian(
                config_path=str(self.config_path)
            )
            logger.info("PerformanceGuardian初始化完成")
            
            # 4. Alpha因子发现
            self.alpha_discovery = AlphaFactorDiscovery(
                config_path=str(self.config_path),
                tushare_token=self.tushare_token
            )
            logger.info("AlphaFactorDiscovery初始化完成")
            
            # 5. 归因分析器
            self.attribution_analyzer = AttributionAnalyzer(
                config_path=str(self.config_path)
            )
            logger.info("AttributionAnalyzer初始化完成")
            
            # 6. 自适应阈值管理器
            self.threshold_manager = AdaptiveThresholdManager(
                config_path=str(self.config_path)
            )
            logger.info("AdaptiveThresholdManager初始化完成")
            
            # 7. AutoEvolution（Phase 2）
            if AUTO_EVOLUTION_AVAILABLE:
                self.auto_evolution = AutoEvolution(
                    config_path=str(self.config_path),
                    tushare_token=self.tushare_token
                )
                logger.info("AutoEvolution初始化完成")
            else:
                self.auto_evolution = None
                
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def check_triggers(self) -> Dict[str, Any]:
        """
        检查触发条件
        
        Returns:
            触发检查结果
        """
        logger.info("检查进化触发条件...")
        
        self.state.last_trigger_check = datetime.now()
        
        try:
            result = self.evolution_trigger.evaluate()
            logger.info(f"触发检查结果: should_evolve={result.get('should_evolve', False)}")
            return result
        except Exception as e:
            logger.error(f"触发检查失败: {e}")
            return {
                'should_evolve': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def execute_evolution(self) -> Dict[str, Any]:
        """
        执行进化流程
        
        Returns:
            进化结果
        """
        logger.info("="*60)
        logger.info("开始执行进化流程...")
        logger.info("="*60)
        
        # 状态转换: IDLE -> EVOLVING
        self._transition_to(EvolutionPhase.EVOLVING)
        
        results = {}
        
        try:
            # 1. Alpha因子发现
            logger.info("步骤1: Alpha因子发现...")
            factor_result = self.alpha_discovery.discover_factors()
            results['new_factors'] = factor_result
            logger.info(f"发现 {factor_result.get('discovered_count', 0)} 个新因子")
            
            # 2. 归因分析
            logger.info("步骤2: 归因分析...")
            attribution_result = self.attribution_analyzer.analyze()
            results['attribution'] = attribution_result
            logger.info(f"归因分析完成: success={attribution_result.get('success', False)}")
            
            # 3. 自适应阈值更新
            logger.info("步骤3: 自适应阈值更新...")
            threshold_result = self.threshold_manager.update_thresholds()
            results['thresholds'] = threshold_result
            logger.info(f"阈值更新完成: adjusted={threshold_result.get('adjusted', False)}")
            
            # 4. Phase 2 AutoEvolution（如果可用）
            if self.auto_evolution:
                logger.info("步骤4: Phase 2 AutoEvolution...")
                try:
                    evolution_report = self.auto_evolution.run_evolution_cycle()
                    results['auto_evolution'] = evolution_report.to_dict()
                    logger.info("AutoEvolution完成")
                except Exception as e:
                    logger.warning(f"AutoEvolution执行失败: {e}")
                    results['auto_evolution'] = {'error': str(e)}
            
            # 5. 构建变更
            changes = self._build_changes(results)
            results['changes'] = changes
            
            logger.info("进化流程执行完成")
            
            return results
            
        except Exception as e:
            logger.error(f"进化流程执行失败: {e}")
            logger.error(traceback.format_exc())
            self.state.error_message = str(e)
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        finally:
            # 状态转换回IDLE（如果没有部署）
            if self.state.phase == EvolutionPhase.EVOLVING:
                self._transition_to(EvolutionPhase.IDLE)
    
    def _build_changes(self, evolution_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据进化结果构建变更
        
        Args:
            evolution_results: 进化结果
            
        Returns:
            变更字典
        """
        changes = {}
        
        # 提取因子权重调整
        if 'attribution' in evolution_results:
            attribution = evolution_results['attribution']
            if attribution.get('success') and 'attribution_report' in attribution:
                report = attribution['attribution_report']
                factor_contributions = report.get('factor_contributions', {})
                
                # 构建权重调整
                weight_adjustments = {}
                for factor_name, contribution in factor_contributions.items():
                    if isinstance(contribution, dict):
                        weight_adjustments[factor_name] = contribution.get('contribution_pct', 0) / 100
                
                if weight_adjustments:
                    changes['scoring'] = {'weights': weight_adjustments}
        
        # 提取阈值调整
        if 'thresholds' in evolution_results:
            threshold_result = evolution_results['thresholds']
            if threshold_result.get('adjusted') and 'new_thresholds' in threshold_result:
                changes['adaptive_thresholds'] = threshold_result['new_thresholds']
        
        return changes
    
    def deploy_changes(self, changes: Dict[str, Any]) -> DeploymentResult:
        """
        部署变更
        
        Args:
            changes: 要部署的变更
            
        Returns:
            部署结果
        """
        logger.info("开始部署变更...")
        
        # 状态转换: EVOLVING -> DEPLOYING
        self._transition_to(EvolutionPhase.DEPLOYING)
        
        try:
            result = self.deploy_manager.deploy_changes(changes, validate=True)
            self.state.deployment_result = result
            
            if result.success:
                logger.info(f"部署成功: 版本 {result.deployed_version}")
            else:
                logger.error(f"部署失败: {result.message}")
            
            return result
            
        except Exception as e:
            logger.error(f"部署异常: {e}")
            error_result = DeploymentResult(
                success=False,
                deployed_version="",
                backup_path="",
                changes_applied={},
                timestamp=datetime.now(),
                message=f"部署异常: {str(e)}"
            )
            self.state.deployment_result = error_result
            return error_result
    
    def validate_deployment(self) -> Dict[str, Any]:
        """
        验证部署
        
        Returns:
            验证结果
        """
        logger.info("验证部署...")
        
        # 状态转换: DEPLOYING -> VALIDATING
        self._transition_to(EvolutionPhase.VALIDATING)
        
        try:
            validation = self.deploy_manager.validate_deployment()
            logger.info(f"验证结果: valid={validation.get('valid', False)}")
            return validation
        except Exception as e:
            logger.error(f"验证失败: {e}")
            return {'valid': False, 'error': str(e)}
    
    def monitor_performance(self) -> Dict[str, Any]:
        """
        监控性能
        
        Returns:
            性能监控结果
        """
        logger.info("监控性能...")
        
        try:
            # 运行所有检查
            checks = self.performance_guardian.run_all_checks()
            
            # 判断是否需要回滚
            needs_rollback = not checks.get('healthy', False)
            
            result = {
                'healthy': checks.get('healthy', False),
                'status': checks.get('status', 'unknown'),
                'needs_rollback': needs_rollback,
                'checks': checks.get('checks', {})
            }
            
            logger.info(f"性能监控: healthy={result['healthy']}, needs_rollback={needs_rollback}")
            
            return result
            
        except Exception as e:
            logger.error(f"性能监控失败: {e}")
            return {
                'healthy': False,
                'status': 'error',
                'needs_rollback': True,
                'error': str(e)
            }
    
    def rollback(self, version: str = None) -> RollbackResult:
        """
        回滚变更
        
        Args:
            version: 要回滚到的版本
            
        Returns:
            回滚结果
        """
        logger.info(f"开始回滚... (目标版本: {version or '上一个版本'})")
        
        # 状态转换: VALIDATING/VALIDATING -> ROLLING_BACK
        self._transition_to(EvolutionPhase.ROLLING_BACK)
        
        try:
            result = self.deploy_manager.rollback(version)
            
            if result.success:
                logger.info(f"回滚成功: {result.rolled_back_to}")
            else:
                logger.error(f"回滚失败: {result.message}")
            
            return result
            
        except Exception as e:
            logger.error(f"回滚异常: {e}")
            return RollbackResult(
                success=False,
                rolled_back_to=version or "",
                timestamp=datetime.now(),
                message=f"回滚异常: {str(e)}"
            )
        finally:
            # 状态转换回IDLE
            self._transition_to(EvolutionPhase.IDLE)
    
    def run_single_iteration(self) -> Dict[str, Any]:
        """
        运行单次迭代
        
        Returns:
            迭代结果
        """
        logger.info("="*60)
        logger.info(f"运行单次迭代 #{self.state.current_iteration + 1}")
        logger.info("="*60)
        
        self.state.current_iteration += 1
        
        iteration_result = {
            'iteration': self.state.current_iteration,
            'timestamp': datetime.now().isoformat(),
            'triggered': False,
            'evolution_executed': False,
            'deployed': False,
            'rolled_back': False
        }
        
        try:
            # 1. 检查触发条件
            trigger_result = self.check_triggers()
            iteration_result['trigger_result'] = trigger_result
            
            if not trigger_result.get('should_evolve', False):
                logger.info("未达到进化触发条件，跳过本次迭代")
                return iteration_result
            
            iteration_result['triggered'] = True
            
            # 2. 执行进化
            evolution_result = self.execute_evolution()
            iteration_result['evolution_result'] = evolution_result
            iteration_result['evolution_executed'] = True
            
            # 检查进化是否成功
            if 'error' in evolution_result and not any(k in evolution_result for k in ['new_factors', 'attribution']):
                logger.error("进化执行失败，跳过后续步骤")
                return iteration_result
            
            # 3. 部署变更
            changes = evolution_result.get('changes', {})
            if changes:
                deployment = self.deploy_changes(changes)
                iteration_result['deployment'] = {
                    'success': deployment.success,
                    'version': deployment.deployed_version,
                    'message': deployment.message
                }
                iteration_result['deployed'] = deployment.success
                
                if not deployment.success:
                    logger.error("部署失败，执行回滚")
                    rollback_result = self.rollback()
                    iteration_result['rollback'] = {
                        'success': rollback_result.success,
                        'version': rollback_result.rolled_back_to
                    }
                    iteration_result['rolled_back'] = rollback_result.success
                    return iteration_result
                
                # 4. 验证部署
                validation = self.validate_deployment()
                iteration_result['validation'] = validation
                
                if not validation.get('valid', False):
                    logger.error("部署验证失败，执行回滚")
                    rollback_result = self.rollback()
                    iteration_result['rollback'] = {
                        'success': rollback_result.success,
                        'version': rollback_result.rolled_back_to
                    }
                    iteration_result['rolled_back'] = rollback_result.success
                    return iteration_result
                
                # 5. 监控性能
                performance = self.monitor_performance()
                iteration_result['performance'] = performance
                
                if performance.get('needs_rollback', False):
                    logger.error("性能监控异常，执行回滚")
                    rollback_result = self.rollback()
                    iteration_result['rollback'] = {
                        'success': rollback_result.success,
                        'version': rollback_result.rolled_back_to
                    }
                    iteration_result['rolled_back'] = rollback_result.success
            
            # 状态恢复为IDLE
            self._transition_to(EvolutionPhase.IDLE)
            
            logger.info("单次迭代完成")
            return iteration_result
            
        except Exception as e:
            logger.error(f"迭代执行失败: {e}")
            logger.error(traceback.format_exc())
            iteration_result['error'] = str(e)
            iteration_result['traceback'] = traceback.format_exc()
            
            # 尝试回滚
            try:
                rollback_result = self.rollback()
                iteration_result['rollback'] = {
                    'success': rollback_result.success,
                    'version': rollback_result.rolled_back_to
                }
            except Exception as rollback_error:
                logger.error(f"回滚也失败: {rollback_error}")
            
            return iteration_result
    
    def _transition_to(self, new_phase: EvolutionPhase):
        """
        状态转换
        
        Args:
            new_phase: 新状态
        """
        old_phase = self.state.phase
        self.state.phase = new_phase
        logger.info(f"状态转换: {old_phase.value} -> {new_phase.value}")
    
    def generate_report(self) -> EvolutionReport:
        """
        生成进化报告
        
        Returns:
            进化报告
        """
        logger.info("生成进化报告...")
        
        # 获取最新状态
        trigger_result = self.check_triggers()
        
        # 性能检查
        performance_check = self.monitor_performance()
        
        # 生成建议
        recommendations = self._generate_recommendations(performance_check)
        
        report = EvolutionReport(
            timestamp=datetime.now(),
            state=self.state,
            trigger_result=trigger_result,
            evolution_result={},
            deployment_result=self.state.deployment_result,
            validation_result={},
            performance_check=performance_check,
            recommendations=recommendations
        )
        
        return report
    
    def _generate_recommendations(self, performance_check: Dict[str, Any]) -> List[str]:
        """
        生成建议
        
        Args:
            performance_check: 性能检查结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        if not performance_check.get('healthy', False):
            status = performance_check.get('status', 'unknown')
            
            if status == 'critical':
                recommendations.append("系统状态严重，建议立即检查并考虑回滚")
            elif status == 'degraded':
                recommendations.append("系统性能下降，建议优化参数或调整策略")
            elif status == 'warning':
                recommendations.append("系统存在警告，建议密切关注")
        else:
            recommendations.append("系统运行正常，建议继续保持")
        
        # 基于检查结果生成具体建议
        checks = performance_check.get('checks', {})
        
        system_check = checks.get('system', {})
        if not system_check.get('healthy', True):
            issues = system_check.get('issues', [])
            for issue in issues:
                recommendations.append(f"系统资源: {issue}")
        
        performance = checks.get('performance', {})
        if not performance.get('healthy', True):
            issues = performance.get('issues', [])
            for issue in issues:
                recommendations.append(f"策略绩效: {issue}")
        
        factor_ic = checks.get('factor_ic', {})
        if not factor_ic.get('healthy', True):
            invalid_count = factor_ic.get('invalid_factors_count', 0)
            if invalid_count > 0:
                recommendations.append(f"有{invalid_count}个因子失效，建议重新评估因子库")
        
        return recommendations
    
    def save_report(self, report: EvolutionReport, filepath: str = None) -> bool:
        """
        保存报告到文件
        
        Args:
            report: 进化报告
            filepath: 文件路径，None则使用默认路径
            
        Returns:
            是否保存成功
        """
        try:
            if filepath is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filepath = self.reports_dir / f'evolution_report_{timestamp}.json'
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"报告已保存: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            return False
    
    def run_continuous(self, interval_minutes: int = 60, max_iterations: int = None):
        """
        持续运行
        
        Args:
            interval_minutes: 检查间隔（分钟）
            max_iterations: 最大迭代次数，None表示无限
        """
        logger.info(f"开始持续运行模式 (间隔: {interval_minutes}分钟)")
        
        self._running = True
        iteration = 0
        
        try:
            while self._running:
                iteration += 1
                
                if max_iterations and iteration > max_iterations:
                    logger.info(f"达到最大迭代次数 {max_iterations}，停止运行")
                    break
                
                logger.info(f"\n{'='*60}")
                logger.info(f"开始第 {iteration} 次迭代")
                logger.info(f"{'='*60}")
                
                # 运行单次迭代
                result = self.run_single_iteration()
                
                # 生成并保存报告
                report = self.generate_report()
                self.save_report(report)
                
                # 发送告警（如果需要）
                if not result.get('deployed', False) and result.get('triggered', False):
                    self.performance_guardian.log_alert(
                        AlertLevel.WARNING,
                        "进化迭代未完成",
                        f"第{iteration}次迭代触发但未成功部署"
                    )
                
                # 等待下一次迭代
                if self._running:
                    logger.info(f"等待 {interval_minutes} 分钟后进行下一次检查...")
                    time.sleep(interval_minutes * 60)
                    
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止运行")
        finally:
            self._running = False
            logger.info("持续运行模式已停止")
    
    def stop(self):
        """停止持续运行"""
        logger.info("停止信号已发送")
        self._running = False


def main():
    """主函数 - 用于测试"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01自动闭环控制器')
    parser.add_argument('--run', action='store_true', help='运行单次迭代')
    parser.add_argument('--continuous', action='store_true', help='持续运行')
    parser.add_argument('--interval', type=int, default=60, help='检查间隔（分钟）')
    parser.add_argument('--config', type=str, default='config.yaml', help='配置文件路径')
    parser.add_argument('--token', type=str, help='Tushare token')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("T01 Phase 3 自动闭环控制器")
    print("="*60)
    
    # 初始化控制器
    controller = AutoClosedLoop(
        config_path=args.config,
        tushare_token=args.token
    )
    
    if args.continuous:
        # 持续运行
        print("\n启动持续运行模式...")
        controller.run_continuous(interval_minutes=args.interval)
    elif args.run:
        # 单次运行
        print("\n运行单次迭代...")
        result = controller.run_single_iteration()
        print("\n迭代结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 生成报告
        report = controller.generate_report()
        controller.save_report(report)
        print(f"\n报告已保存")
    else:
        # 测试模式
        print("\n测试模式 - 检查系统状态...")
        
        # 检查触发
        print("\n1. 检查触发条件...")
        trigger = controller.check_triggers()
        print(f"   是否触发: {trigger.get('should_evolve', False)}")
        
        # 检查性能
        print("\n2. 检查系统性能...")
        performance = controller.monitor_performance()
        print(f"   健康状态: {performance.get('healthy', False)}")
        print(f"   整体状态: {performance.get('status', 'unknown')}")
        
        # 生成报告
        print("\n3. 生成报告...")
        report = controller.generate_report()
        print(f"   当前状态: {report.state.phase.value}")
        print(f"   建议数: {len(report.recommendations)}")
        
        print("\n" + "="*60)
        print("测试完成")
        print("="*60)


if __name__ == '__main__':
    main()
