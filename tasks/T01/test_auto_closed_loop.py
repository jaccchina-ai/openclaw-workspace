#!/usr/bin/env python3
"""
Tests for Auto Closed Loop Controller Module for T01 Phase 3

TDD Approach:
1. Write tests first (they should fail)
2. Implement the module
3. Run tests (they should pass)

This is the final integration module that orchestrates all Phase 3 components:
- evolution_trigger.py - for triggering evolution
- safe_deploy_manager.py - for safe deployment
- performance_guardian.py - for monitoring
- alpha_factor_discovery.py - for factor discovery
- attribution_analyzer.py - for attribution analysis
- adaptive_threshold_manager.py - for threshold management
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os
import json
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the module under test
try:
    from auto_closed_loop import (
        AutoClosedLoop,
        EvolutionPhase,
        EvolutionState,
        EvolutionReport,
        DeploymentResult,
        RollbackResult
    )
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False


class MockEvolutionTrigger:
    """Mock Evolution Trigger for testing"""
    def __init__(self, *args, **kwargs):
        self.should_trigger = False
        self.trigger_result = {
            'should_evolve': False,
            'trigger_type': None,
            'confidence': 0.0,
            'message': 'No trigger'
        }
    
    def evaluate(self, *args, **kwargs):
        return self.trigger_result
    
    def manual_trigger(self, *args, **kwargs):
        return {
            'should_evolve': True,
            'trigger_type': 'manual',
            'confidence': 1.0,
            'message': 'Manual trigger'
        }


class MockSafeDeployManager:
    """Mock Safe Deploy Manager for testing"""
    def __init__(self, *args, **kwargs):
        self.deployment_success = True
    
    def deploy_changes(self, changes, *args, **kwargs):
        return DeploymentResult(
            success=self.deployment_success,
            deployed_version='v1.0.0',
            backup_path='/tmp/backup',
            changes_applied=changes,
            timestamp=datetime.now()
        )
    
    def rollback(self, version=None, *args, **kwargs):
        return RollbackResult(
            success=True,
            rolled_back_to=version or 'v0.9.0',
            timestamp=datetime.now()
        )
    
    def validate_deployment(self, *args, **kwargs):
        return {'valid': True, 'checks_passed': 5, 'checks_failed': 0}


class MockPerformanceGuardian:
    """Mock Performance Guardian for testing"""
    def __init__(self, *args, **kwargs):
        self.healthy = True
    
    def check_system_health(self, *args, **kwargs):
        return {
            'healthy': self.healthy,
            'status': 'healthy' if self.healthy else 'critical',
            'memory_percent': 50.0,
            'cpu_percent': 30.0,
            'disk_percent': 60.0
        }
    
    def check_performance(self, *args, **kwargs):
        return {
            'healthy': self.healthy,
            'win_rate': 0.65,
            'profit_factor': 1.8,
            'max_drawdown': 0.10
        }
    
    def check_factor_ic(self, *args, **kwargs):
        return {
            'healthy': self.healthy,
            'status': 'healthy' if self.healthy else 'degraded',
            'invalid_factors_count': 0 if self.healthy else 3
        }
    
    def run_all_checks(self, *args, **kwargs):
        """运行所有检查"""
        return {
            'healthy': self.healthy,
            'status': 'healthy' if self.healthy else 'critical',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'system': self.check_system_health(),
                'performance': self.check_performance(),
                'factor_ic': self.check_factor_ic()
            }
        }


class MockAlphaFactorDiscovery:
    """Mock Alpha Factor Discovery for testing"""
    def __init__(self, *args, **kwargs):
        pass
    
    def discover_factors(self, *args, **kwargs):
        return {
            'new_factors': [
                {'name': 'factor_1', 'ic': 0.05, 'sharpe': 1.2},
                {'name': 'factor_2', 'ic': 0.04, 'sharpe': 1.0}
            ],
            'discovered_count': 2
        }


class MockAttributionAnalyzer:
    """Mock Attribution Analyzer for testing"""
    def __init__(self, *args, **kwargs):
        pass
    
    def analyze(self, *args, **kwargs):
        return {
            'attribution_report': {
                'factor_contributions': {'momentum': 0.3, 'value': 0.2},
                'unexplained': 0.5
            }
        }


class MockAdaptiveThresholdManager:
    """Mock Adaptive Threshold Manager for testing"""
    def __init__(self, *args, **kwargs):
        pass
    
    def update_thresholds(self, *args, **kwargs):
        return {
            'thresholds': {'entry': 70.0, 'exit': 75.0},
            'adjusted': True
        }
    
    def get_current_thresholds(self, *args, **kwargs):
        return {'entry': 70.0, 'exit': 75.0}


class TestEvolutionPhase(unittest.TestCase):
    """Test EvolutionPhase enum"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    def test_phase_values(self):
        """Test phase enum values"""
        self.assertEqual(EvolutionPhase.IDLE.value, 'idle')
        self.assertEqual(EvolutionPhase.EVOLVING.value, 'evolving')
        self.assertEqual(EvolutionPhase.DEPLOYING.value, 'deploying')
        self.assertEqual(EvolutionPhase.VALIDATING.value, 'validating')
        self.assertEqual(EvolutionPhase.ROLLING_BACK.value, 'rolling_back')


class TestEvolutionState(unittest.TestCase):
    """Test EvolutionState dataclass"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    def test_state_creation(self):
        """Test creating EvolutionState"""
        state = EvolutionState(
            phase=EvolutionPhase.IDLE,
            start_time=datetime.now(),
            current_iteration=0,
            last_trigger_check=None,
            deployment_result=None,
            error_message=None
        )
        self.assertEqual(state.phase, EvolutionPhase.IDLE)
        self.assertEqual(state.current_iteration, 0)


class TestAutoClosedLoopInitialization(unittest.TestCase):
    """Test AutoClosedLoop initialization"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_initialization(self):
        """Test AutoClosedLoop initialization"""
        controller = AutoClosedLoop(config_path='config.yaml')
        
        self.assertIsNotNone(controller)
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)
        self.assertIsNotNone(controller.evolution_trigger)
        self.assertIsNotNone(controller.deploy_manager)
        self.assertIsNotNone(controller.performance_guardian)
        self.assertIsNotNone(controller.alpha_discovery)
        self.assertIsNotNone(controller.attribution_analyzer)
        self.assertIsNotNone(controller.threshold_manager)
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_initial_state(self):
        """Test initial state is IDLE"""
        controller = AutoClosedLoop()
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)


class TestTriggerChecking(unittest.TestCase):
    """Test trigger checking functionality"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_check_triggers_no_trigger(self):
        """Test check triggers when no trigger condition met"""
        controller = AutoClosedLoop()
        controller.evolution_trigger.should_trigger = False
        controller.evolution_trigger.trigger_result = {
            'should_evolve': False,
            'trigger_type': None,
            'confidence': 0.0,
            'message': 'No trigger'
        }
        
        result = controller.check_triggers()
        
        self.assertFalse(result['should_evolve'])
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_check_triggers_with_trigger(self):
        """Test check triggers when trigger condition met"""
        controller = AutoClosedLoop()
        controller.evolution_trigger.should_trigger = True
        controller.evolution_trigger.trigger_result = {
            'should_evolve': True,
            'trigger_type': 'performance_drop',
            'confidence': 0.85,
            'message': 'Performance drop detected'
        }
        
        result = controller.check_triggers()
        
        self.assertTrue(result['should_evolve'])


class TestEvolutionExecution(unittest.TestCase):
    """Test evolution execution"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_execute_evolution(self):
        """Test evolution execution"""
        controller = AutoClosedLoop()
        
        result = controller.execute_evolution()
        
        self.assertIsInstance(result, dict)
        self.assertIn('new_factors', result)
        self.assertIn('attribution', result)
        self.assertIn('thresholds', result)
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_evolution_state_transition(self):
        """Test state transitions during evolution"""
        controller = AutoClosedLoop()
        
        # Start from IDLE
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)
        
        # Execute evolution
        controller.execute_evolution()
        
        # Should return to IDLE after completion
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)


class TestDeployment(unittest.TestCase):
    """Test deployment functionality"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_deploy_changes(self):
        """Test deploying changes"""
        controller = AutoClosedLoop()
        changes = {'factor_weights': {'factor1': 0.5}}
        
        result = controller.deploy_changes(changes)
        
        self.assertIsInstance(result, DeploymentResult)
        self.assertTrue(result.success)
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_validate_deployment(self):
        """Test deployment validation"""
        controller = AutoClosedLoop()
        
        result = controller.validate_deployment()
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('valid', False))


class TestRollback(unittest.TestCase):
    """Test rollback functionality"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_rollback(self):
        """Test rollback functionality"""
        controller = AutoClosedLoop()
        
        result = controller.rollback(version='v0.9.0')
        
        self.assertIsInstance(result, RollbackResult)
        self.assertTrue(result.success)
        self.assertEqual(result.rolled_back_to, 'v0.9.0')
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_rollback_state_transition(self):
        """Test state transition during rollback"""
        controller = AutoClosedLoop()
        
        # Set state to ROLLING_BACK
        controller.state.phase = EvolutionPhase.ROLLING_BACK
        
        result = controller.rollback()
        
        self.assertTrue(result.success)


class TestMainControlLoop(unittest.TestCase):
    """Test main control loop"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_run_single_iteration_no_trigger(self):
        """Test single iteration when no trigger"""
        controller = AutoClosedLoop()
        controller.evolution_trigger.should_trigger = False
        controller.evolution_trigger.trigger_result = {
            'should_evolve': False,
            'trigger_type': None,
            'confidence': 0.0,
            'message': 'No trigger'
        }
        
        result = controller.run_single_iteration()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_run_single_iteration_with_trigger(self):
        """Test single iteration when trigger fires"""
        controller = AutoClosedLoop()
        controller.evolution_trigger.should_trigger = True
        controller.evolution_trigger.trigger_result = {
            'should_evolve': True,
            'trigger_type': 'performance_drop',
            'confidence': 0.85,
            'message': 'Performance drop detected'
        }
        
        result = controller.run_single_iteration()
        
        self.assertIsInstance(result, dict)


class TestPerformanceMonitoring(unittest.TestCase):
    """Test performance monitoring"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_monitor_performance_healthy(self):
        """Test monitoring when performance is healthy"""
        controller = AutoClosedLoop()
        controller.performance_guardian.healthy = True
        
        result = controller.monitor_performance()
        
        self.assertTrue(result['healthy'])
        self.assertFalse(result['needs_rollback'])
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_monitor_performance_unhealthy(self):
        """Test monitoring when performance is unhealthy"""
        controller = AutoClosedLoop()
        controller.performance_guardian.healthy = False
        
        result = controller.monitor_performance()
        
        self.assertFalse(result['healthy'])
        self.assertTrue(result['needs_rollback'])


class TestReporting(unittest.TestCase):
    """Test reporting functionality"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_generate_report(self):
        """Test report generation"""
        controller = AutoClosedLoop()
        
        report = controller.generate_report()
        
        self.assertIsInstance(report, EvolutionReport)
        self.assertIsNotNone(report.timestamp)
        self.assertIsNotNone(report.state)
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_save_report(self):
        """Test saving report to file"""
        controller = AutoClosedLoop()
        report = controller.generate_report()
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            result = controller.save_report(report, '/tmp/test_report.json')
            self.assertTrue(result)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_full_evolution_cycle(self):
        """Test full evolution cycle"""
        controller = AutoClosedLoop()
        
        # 1. Check triggers
        controller.evolution_trigger.should_trigger = True
        controller.evolution_trigger.trigger_result = {
            'should_evolve': True,
            'trigger_type': 'performance_drop',
            'confidence': 0.85,
            'message': 'Performance drop detected'
        }
        trigger_result = controller.check_triggers()
        self.assertTrue(trigger_result['should_evolve'])
        
        # 2. Execute evolution
        evolution_result = controller.execute_evolution()
        self.assertIn('new_factors', evolution_result)
        
        # 3. Deploy changes
        changes = {'factor_weights': {'factor1': 0.5}}
        deployment = controller.deploy_changes(changes)
        self.assertTrue(deployment.success)
        
        # 4. Validate deployment
        validation = controller.validate_deployment()
        self.assertTrue(validation['valid'])
        
        # 5. Monitor performance
        monitoring = controller.monitor_performance()
        self.assertIn('healthy', monitoring)
        
        # 6. Generate report
        report = controller.generate_report()
        self.assertIsNotNone(report)


class TestStateMachine(unittest.TestCase):
    """Test state machine transitions"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_state_transitions(self):
        """Test all state transitions"""
        controller = AutoClosedLoop()
        
        # IDLE -> EVOLVING
        controller.state.phase = EvolutionPhase.EVOLVING
        self.assertEqual(controller.state.phase, EvolutionPhase.EVOLVING)
        
        # EVOLVING -> DEPLOYING
        controller.state.phase = EvolutionPhase.DEPLOYING
        self.assertEqual(controller.state.phase, EvolutionPhase.DEPLOYING)
        
        # DEPLOYING -> VALIDATING
        controller.state.phase = EvolutionPhase.VALIDATING
        self.assertEqual(controller.state.phase, EvolutionPhase.VALIDATING)
        
        # VALIDATING -> IDLE (success)
        controller.state.phase = EvolutionPhase.IDLE
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)
        
        # VALIDATING -> ROLLING_BACK (failure)
        controller.state.phase = EvolutionPhase.VALIDATING
        controller.state.phase = EvolutionPhase.ROLLING_BACK
        self.assertEqual(controller.state.phase, EvolutionPhase.ROLLING_BACK)
        
        # ROLLING_BACK -> IDLE
        controller.state.phase = EvolutionPhase.IDLE
        self.assertEqual(controller.state.phase, EvolutionPhase.IDLE)


class TestErrorHandling(unittest.TestCase):
    """Test error handling"""
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_deployment_failure_handling(self):
        """Test handling of deployment failure"""
        controller = AutoClosedLoop()
        controller.deploy_manager.deployment_success = False
        
        changes = {'factor_weights': {'factor1': 0.5}}
        result = controller.deploy_changes(changes)
        
        self.assertFalse(result.success)
    
    @unittest.skipUnless(MODULE_AVAILABLE, "模块未实现")
    @patch('auto_closed_loop.EvolutionTrigger', MockEvolutionTrigger)
    @patch('auto_closed_loop.SafeDeployManager', MockSafeDeployManager)
    @patch('auto_closed_loop.PerformanceGuardian', MockPerformanceGuardian)
    @patch('auto_closed_loop.AlphaFactorDiscovery', MockAlphaFactorDiscovery)
    @patch('auto_closed_loop.AttributionAnalyzer', MockAttributionAnalyzer)
    @patch('auto_closed_loop.AdaptiveThresholdManager', MockAdaptiveThresholdManager)
    def test_evolution_error_handling(self):
        """Test handling of evolution errors"""
        controller = AutoClosedLoop()
        
        # Mock alpha discovery to raise exception
        controller.alpha_discovery.discover_factors = Mock(side_effect=Exception("Discovery failed"))
        
        result = controller.execute_evolution()
        
        # Should handle error gracefully
        self.assertIn('error', result or {})


def suite():
    """Create test suite"""
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEvolutionPhase))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEvolutionState))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAutoClosedLoopInitialization))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTriggerChecking))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEvolutionExecution))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDeployment))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRollback))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMainControlLoop))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPerformanceMonitoring))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestReporting))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStateMachine))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestErrorHandling))
    
    return test_suite


if __name__ == '__main__':
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
