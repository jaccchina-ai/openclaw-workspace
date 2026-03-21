#!/usr/bin/env python3
"""
Feishu Message Sender - React Loop Pattern Implementation
使用React Loop模式彻底解决Node.js内存溢出问题

核心设计:
1. 消息队列 - 所有消息先入队
2. 独立进程 - 每个消息在独立子进程中发送
3. 资源隔离 - 严格控制内存和超时
4. 指数退避 - 失败后延迟重试
5. 优雅降级 - 最终保存到文件
"""

import os
import sys
import json
import time
import logging
import subprocess
import tempfile
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """消息状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    FALLBACK = "fallback"


@dataclass
class MessageTask:
    """消息任务"""
    id: str
    content: str
    target: str
    channel: str
    status: MessageStatus
    created_at: float
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    result: Optional[Any] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'target': self.target,
            'channel': self.channel,
            'status': self.status.value,
            'created_at': self.created_at,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'last_error': self.last_error,
        }


class ReactLoopFeishuSender:
    """
    React Loop 模式飞书消息发送器
    
    核心特性:
    1. 消息队列缓冲
    2. 独立进程执行 (资源隔离)
    3. 指数退避重试
    4. 内存限制 (Node.js --max-old-space-size)
    5. 超时控制
    6. 优雅降级到文件
    """
    
    def __init__(self,
                 fallback_dir: str = "/root/.openclaw/workspace/logs/feishu_messages",
                 node_memory_mb: int = 512,
                 process_timeout: int = 30,
                 max_retries: int = 3,
                 retry_delays: list = None):
        """
        初始化发送器
        
        Args:
            fallback_dir: 失败消息保存目录
            node_memory_mb: Node.js内存限制(MB)
            process_timeout: 子进程超时(秒)
            max_retries: 最大重试次数
            retry_delays: 重试延迟列表(秒)
        """
        self.fallback_dir = Path(fallback_dir)
        self.fallback_dir.mkdir(parents=True, exist_ok=True)
        
        self.node_memory_mb = node_memory_mb
        self.process_timeout = process_timeout
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [1, 3, 5]  # 指数退避
        
        self.openclaw_path = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
        
        # 消息队列
        self.message_queue = queue.Queue()
        
        # 处理线程
        self.worker_thread = None
        self.is_running = False
        
        # 统计
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'fallback': 0,
        }
        
        logger.info(f"ReactLoopFeishuSender 初始化完成")
        logger.info(f"  - Fallback目录: {self.fallback_dir}")
        logger.info(f"  - Node内存限制: {node_memory_mb}MB")
        logger.info(f"  - 进程超时: {process_timeout}秒")
        logger.info(f"  - 最大重试: {max_retries}次")
    
    def start_worker(self):
        """启动后台工作线程"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("ReactLoop 工作线程已启动")
    
    def stop_worker(self):
        """停止后台工作线程"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("ReactLoop 工作线程已停止")
    
    def _worker_loop(self):
        """工作线程主循环"""
        while self.is_running:
            try:
                # 非阻塞获取消息
                task = self.message_queue.get(timeout=1)
                self._process_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程异常: {e}")
    
    def _process_task(self, task: MessageTask):
        """处理单个消息任务"""
        task.status = MessageStatus.PROCESSING
        logger.info(f"处理消息任务 {task.id}: 第{task.attempts + 1}次尝试")
        
        # React Loop: 尝试发送
        for attempt in range(self.max_retries):
            task.attempts = attempt + 1
            
            try:
                success = self._send_in_isolated_process(task)
                if success:
                    task.status = MessageStatus.SUCCESS
                    self.stats['success'] += 1
                    logger.info(f"✅ 消息 {task.id} 发送成功")
                    return
                
            except Exception as e:
                task.last_error = str(e)
                logger.warning(f"⚠️ 消息 {task.id} 第{attempt + 1}次尝试失败: {e}")
            
            # 指数退避延迟
            if attempt < self.max_retries - 1:
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                logger.info(f"⏱️ 等待 {delay} 秒后重试...")
                time.sleep(delay)
        
        # 所有尝试失败，降级到文件
        task.status = MessageStatus.FALLBACK
        self._save_to_fallback(task)
        self.stats['fallback'] += 1
    
    def _send_in_isolated_process(self, task: MessageTask) -> bool:
        """
        在隔离进程中发送消息
        
        这是React Loop的核心：每个消息都在全新的子进程中发送，
        确保内存泄漏不会影响主进程。
        """
        # 创建临时脚本文件
        script_content = self._generate_sender_script(task)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['NODE_OPTIONS'] = f'--max-old-space-size={self.node_memory_mb}'
            env['PYTHONUNBUFFERED'] = '1'
            
            # 启动隔离进程
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                # 限制子进程资源
                preexec_fn=self._limit_resources if os.name != 'nt' else None
            )
            
            # 等待完成或超时
            try:
                stdout, stderr = process.communicate(timeout=self.process_timeout)
                
                if process.returncode == 0:
                    result = json.loads(stdout.strip())
                    return result.get('success', False)
                else:
                    logger.error(f"子进程失败: {stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                # 超时强制终止
                process.kill()
                process.wait()
                logger.error(f"⏱️ 子进程超时({self.process_timeout}秒)，已强制终止")
                return False
                
        finally:
            # 清理临时文件
            try:
                os.unlink(script_path)
            except:
                pass
    
    def _limit_resources(self):
        """限制子进程资源 (Unix only)"""
        try:
            import resource
            # 限制内存使用 (512MB)
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
            # 限制CPU时间 (60秒)
            resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
        except:
            pass
    
    def _generate_sender_script(self, task: MessageTask) -> str:
        """生成隔离进程的发送脚本"""
        # 转义消息内容中的特殊字符
        escaped_content = task.content.replace('"', '\\"').replace("'", "\\'")
        
        script = f'''#!/usr/bin/env python3
import subprocess
import json
import sys

result = {{'success': False, 'error': None}}

try:
    cmd = [
        '{self.openclaw_path}',
        'message', 'send',
        '--channel', '{task.channel}',
        '--target', 'user:{task.target}',
        '--message', """{escaped_content}"""
    ]
    
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout={self.process_timeout}
    )
    
    result['success'] = proc.returncode == 0
    result['stdout'] = proc.stdout
    result['stderr'] = proc.stderr
    result['returncode'] = proc.returncode
    
except Exception as e:
    result['error'] = str(e)

print(json.dumps(result))
sys.exit(0 if result['success'] else 1)
'''
        return script
    
    def _save_to_fallback(self, task: MessageTask):
        """保存失败消息到fallback文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{task.id}.json"
        filepath = self.fallback_dir / filename
        
        data = {
            'task': task.to_dict(),
            'saved_at': datetime.now().isoformat(),
            'full_content': task.content,  # 保存完整内容
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 消息已保存到fallback: {filepath}")
    
    def send(self, content: str, target: str = "ou_b8a256a9cb526db6c196cb438d6893a6", 
             channel: str = "feishu", block: bool = False) -> MessageTask:
        """
        发送消息
        
        Args:
            content: 消息内容
            target: 目标用户ID
            channel: 通道
            block: 是否阻塞等待结果
            
        Returns:
            MessageTask 对象
        """
        task = MessageTask(
            id=f"msg_{int(time.time() * 1000)}_{hash(content) % 10000}",
            content=content,
            target=target,
            channel=channel,
            status=MessageStatus.PENDING,
            created_at=time.time(),
            max_attempts=self.max_retries
        )
        
        self.stats['total'] += 1
        
        if block:
            # 同步处理
            self._process_task(task)
        else:
            # 异步入队
            self.message_queue.put(task)
            # 确保工作线程运行
            if not self.is_running:
                self.start_worker()
        
        return task
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.message_queue.qsize()


# 全局发送器实例
_sender_instance: Optional[ReactLoopFeishuSender] = None

def get_sender() -> ReactLoopFeishuSender:
    """获取全局发送器实例"""
    global _sender_instance
    if _sender_instance is None:
        _sender_instance = ReactLoopFeishuSender()
        _sender_instance.start_worker()
    return _sender_instance


def send_feishu_message(content: str, target: str = "ou_b8a256a9cb526db6c196cb438d6893a6",
                        channel: str = "feishu", block: bool = False) -> bool:
    """
    便捷函数：发送飞书消息
    
    Args:
        content: 消息内容
        target: 目标用户ID
        channel: 通道
        block: 是否阻塞
        
    Returns:
        bool: 是否成功入队（非实际发送结果）
    """
    sender = get_sender()
    task = sender.send(content, target, channel, block)
    return task.status != MessageStatus.FAILED


# 测试
if __name__ == "__main__":
    # 测试发送
    test_message = """📊 **T01策略测试消息**
React Loop 模式测试
时间: {}
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    print("=" * 60)
    print("React Loop Feishu Sender 测试")
    print("=" * 60)
    
    sender = ReactLoopFeishuSender()
    
    # 同步发送测试
    print("\n1. 同步发送测试...")
    task = sender.send(test_message, block=True)
    print(f"   结果: {task.status.value}")
    print(f"   尝试次数: {task.attempts}")
    
    # 异步发送测试
    print("\n2. 异步发送测试...")
    task = sender.send(test_message, block=False)
    print(f"   任务ID: {task.id}")
    print(f"   队列大小: {sender.get_queue_size()}")
    
    # 等待处理
    time.sleep(5)
    
    print(f"\n3. 统计信息:")
    print(f"   {sender.get_stats()}")
    
    sender.stop_worker()
    print("\n✅ 测试完成")
