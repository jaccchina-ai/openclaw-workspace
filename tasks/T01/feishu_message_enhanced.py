#!/usr/bin/env python3
"""
飞书消息发送增强模块
提供可靠的消息发送功能：重试、超时调整、监控、降级方案
"""

import subprocess
import os
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# 默认配置
DEFAULT_CONFIG = {
    "openclaw_path": "/root/.nvm/versions/node/v22.22.0/bin/openclaw",
    "max_retries": 5,  # 增加重试次数
    "retry_delay": 3,  # 增加初始延迟
    "timeout": 60,  # 增加超时时间到60秒
    "use_exponential_backoff": True,
    "backoff_factor": 2,
    "max_backoff": 120,  # 增加最大退避时间
    "enable_fallback": True,
    "fallback_to_log": True,
    "log_file": "/root/.openclaw/workspace/logs/feishu_message.log",
    "monitor_enabled": True,
    "stats_file": "/root/.openclaw/workspace/logs/feishu_stats.json"
}

class FeishuMessageSender:
    """飞书消息发送器（增强版）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        """
        初始化消息发送器
        
        Args:
            config: 配置字典，覆盖默认配置
            logger: 日志记录器，如果为None则创建新记录器
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # 设置日志
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        
        # 统计数据
        self.stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_retries": 0,
            "last_success": None,
            "last_failure": None,
            "consecutive_failures": 0
        }
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self.config["log_file"]), exist_ok=True)
        if self.config["stats_file"]:
            os.makedirs(os.path.dirname(self.config["stats_file"]), exist_ok=True)
    
    def _save_stats(self):
        """保存统计数据到文件"""
        if not self.config["stats_file"]:
            return
        
        try:
            import json
            with open(self.config["stats_file"], 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"保存统计数据失败: {e}")
    
    def _log_fallback(self, message: str, reason: str):
        """记录到fallback日志文件"""
        if not self.config["fallback_to_log"]:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] FALLBACK - {reason}\n{message}\n{'-'*40}\n"
            
            with open(self.config["log_file"], 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            self.logger.info(f"消息已记录到fallback日志: {self.config['log_file']}")
            return True
        except Exception as e:
            self.logger.error(f"记录到fallback日志失败: {e}")
            return False
    
    def _check_environment(self) -> Dict[str, Any]:
        """检查环境是否就绪"""
        result = {
            "openclaw_exists": os.path.exists(self.config["openclaw_path"]),
            "node_in_path": False,
            "openclaw_executable": False,
            "errors": []
        }
        
        # 检查Node.js路径
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        current_path = os.environ.get("PATH", "")
        result["node_in_path"] = node_path in current_path
        
        # 检查openclaw是否可执行
        if result["openclaw_exists"]:
            try:
                # 测试基本命令
                test_cmd = [self.config["openclaw_path"], "--version"]
                # 确保环境变量包含Node.js路径
                env = os.environ.copy()
                node_path = "/root/.nvm/versions/node/v22.22.0/bin"
                if node_path not in env.get('PATH', ''):
                    env['PATH'] = node_path + ':' + env.get('PATH', '')
                
                test_result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,  # 增加超时时间
                    env=env
                )
                result["openclaw_executable"] = test_result.returncode == 0
                if test_result.returncode != 0:
                    result["errors"].append(f"openclaw执行失败: {test_result.stderr[:100]}")
            except Exception as e:
                result["errors"].append(f"openclaw测试异常: {e}")
                result["openclaw_executable"] = False
        else:
            result["errors"].append(f"openclaw文件不存在: {self.config['openclaw_path']}")
        
        return result
    
    def _send_single_attempt(self, message: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        单次发送尝试
        
        Args:
            message: 消息内容
            timeout: 超时时间（秒），如果为None使用配置中的timeout
            
        Returns:
            发送结果字典
        """
        if timeout is None:
            timeout = self.config["timeout"]
        
        try:
            openclaw_path = self.config["openclaw_path"]
            cmd = [
                openclaw_path, 'message', 'send',
                '--channel', 'feishu',
                '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
                '--message', message
            ]
            
            # 确保环境变量包含Node.js路径
            env = os.environ.copy()
            node_path = "/root/.nvm/versions/node/v22.22.0/bin"
            if node_path not in env.get('PATH', ''):
                env['PATH'] = node_path + ':' + env.get('PATH', '')
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "elapsed_seconds": elapsed,
                    "output": result.stdout,
                    "attempt": "success"
                }
            else:
                return {
                    "success": False,
                    "elapsed_seconds": elapsed,
                    "error": result.stderr,
                    "output": result.stdout,
                    "attempt": "failed"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "elapsed_seconds": timeout,
                "error": f"超时 ({timeout}秒)",
                "attempt": "timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "elapsed_seconds": 0,
                "error": str(e),
                "attempt": "exception"
            }
    
    def send_with_retry(self, message: str, context: str = "unknown") -> Dict[str, Any]:
        """
        发送消息并自动重试
        
        Args:
            message: 消息内容
            context: 上下文描述，用于日志记录
            
        Returns:
            发送结果字典
        """
        self.logger.info(f"📤 发送飞书消息 ({context}): {len(message)} 字符")
        self.stats["total_sent"] += 1
        
        # 检查环境
        env_check = self._check_environment()
        if not env_check["openclaw_executable"]:
            self.logger.error(f"❌ 环境检查失败: {env_check['errors']}")
            
            # 尝试fallback
            if self.config["enable_fallback"]:
                self._log_fallback(message, f"环境检查失败: {env_check['errors']}")
                self.stats["total_failed"] += 1
                self.stats["consecutive_failures"] += 1
                self._save_stats()
                return {
                    "success": False,
                    "fallback_used": True,
                    "reason": "environment_check_failed",
                    "errors": env_check["errors"]
                }
            
            return {
                "success": False,
                "fallback_used": False,
                "reason": "environment_check_failed",
                "errors": env_check["errors"]
            }
        
        # 执行重试逻辑
        max_retries = self.config["max_retries"]
        retry_delay = self.config["retry_delay"]
        use_backoff = self.config["use_exponential_backoff"]
        backoff_factor = self.config["backoff_factor"]
        max_backoff = self.config["max_backoff"]
        
        last_error = None
        attempt_results = []
        
        for attempt in range(max_retries + 1):  # 包括首次尝试
            if attempt > 0:
                self.logger.info(f"🔄 重试 {attempt}/{max_retries}...")
                self.stats["total_retries"] += 1
                
                # 计算延迟
                if use_backoff:
                    delay = min(retry_delay * (backoff_factor ** (attempt - 1)), max_backoff)
                else:
                    delay = retry_delay
                
                self.logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
            
            # 发送尝试
            result = self._send_single_attempt(message)
            attempt_results.append(result)
            
            if result["success"]:
                self.logger.info(f"✅ 飞书消息发送成功 (耗时: {result['elapsed_seconds']:.2f}秒)")
                self.stats["last_success"] = datetime.now().isoformat()
                self.stats["consecutive_failures"] = 0
                self._save_stats()
                
                return {
                    "success": True,
                    "elapsed_seconds": result["elapsed_seconds"],
                    "attempts": attempt + 1,
                    "all_attempts": attempt_results,
                    "fallback_used": False
                }
            else:
                error_type = result.get("attempt", "unknown")
                error_msg = result.get("error", "未知错误")
                last_error = error_msg
                
                self.logger.warning(f"❌ 发送尝试 {attempt+1} 失败 ({error_type}): {error_msg[:100]}")
        
        # 所有尝试都失败
        self.logger.error(f"❌ 所有 {max_retries+1} 次尝试均失败")
        self.stats["total_failed"] += 1
        self.stats["last_failure"] = datetime.now().isoformat()
        self.stats["consecutive_failures"] += 1
        self._save_stats()
        
        # 尝试fallback
        fallback_success = False
        if self.config["enable_fallback"]:
            fallback_success = self._log_fallback(message, f"所有尝试失败: {last_error}")
        
        return {
            "success": False,
            "elapsed_seconds": sum(r.get("elapsed_seconds", 0) for r in attempt_results),
            "attempts": max_retries + 1,
            "all_attempts": attempt_results,
            "last_error": last_error,
            "fallback_used": self.config["enable_fallback"],
            "fallback_success": fallback_success
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取当前统计数据"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计数据"""
        self.stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_retries": 0,
            "last_success": None,
            "last_failure": None,
            "consecutive_failures": 0
        }
        self._save_stats()

# 快速使用函数
def send_feishu_message(message: str, max_retries: int = 3, timeout: int = 30) -> bool:
    """
    快速发送飞书消息（简化接口）
    
    Args:
        message: 消息内容
        max_retries: 最大重试次数
        timeout: 单次尝试超时时间
        
    Returns:
        是否发送成功
    """
    sender = FeishuMessageSender({
        "max_retries": max_retries,
        "timeout": timeout
    })
    
    result = sender.send_with_retry(message, "quick_send")
    return result["success"]

# 测试函数
def test_module():
    """测试模块功能"""
    import sys
    
    print("🧪 测试飞书消息增强模块")
    
    # 创建发送器
    sender = FeishuMessageSender({
        "max_retries": 1,
        "timeout": 10,
        "enable_fallback": True
    })
    
    # 测试消息
    test_message = f"🔧 飞书增强模块测试\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n类型: 功能测试\n状态: 请忽略此测试消息"
    
    print(f"发送测试消息 ({len(test_message)} 字符)...")
    result = sender.send_with_retry(test_message, "module_test")
    
    print(f"结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"尝试次数: {result.get('attempts', 1)}")
    print(f"Fallback使用: {result.get('fallback_used', False)}")
    
    if not result["success"] and "last_error" in result:
        print(f"最后错误: {result['last_error'][:200]}")
    
    # 显示统计数据
    stats = sender.get_stats()
    print(f"\n📊 统计数据:")
    print(f"  总发送: {stats['total_sent']}")
    print(f"  总失败: {stats['total_failed']}")
    print(f"  总重试: {stats['total_retries']}")
    print(f"  连续失败: {stats['consecutive_failures']}")
    
    return result["success"]

if __name__ == "__main__":
    # 如果直接运行，执行测试
    success = test_module()
    sys.exit(0 if success else 1)