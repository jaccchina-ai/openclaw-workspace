#!/usr/bin/env python3
"""
T01 增强版飞书消息发送器
结合多种发送策略，彻底解决Node.js内存溢出问题

策略优先级:
1. 直接API调用 (最高优先级，无Node.js依赖)
2. React Loop发送器 (带内存限制和重试)
3. 文件Fallback (最终保障)
"""

import os
import sys
import json
import time
import logging
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import requests

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


class FeishuDirectAPI:
    """飞书直接API调用 - 绕过Node.js，使用Python requests"""

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or os.environ.get('FEISHU_APP_ID')
        self.app_secret = app_secret or os.environ.get('FEISHU_APP_SECRET')
        self.access_token: Optional[str] = None
        self.token_expire_time: Optional[float] = None
        self.base_url = "https://open.feishu.cn/open-apis"

    def _get_access_token(self) -> Optional[str]:
        """获取飞书访问令牌"""
        if self.access_token and self.token_expire_time and time.time() < self.token_expire_time:
            return self.access_token

        if not self.app_id or not self.app_secret:
            logger.warning("⚠️ 飞书应用凭证未配置")
            return None

        try:
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            headers = {"Content-Type": "application/json"}
            data = {"app_id": self.app_id, "app_secret": self.app_secret}

            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()

            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                expire = result.get("expire", 7200)
                self.token_expire_time = time.time() + expire - 300
                logger.info("✅ 飞书访问令牌获取成功")
                return self.access_token
            else:
                logger.error(f"❌ 获取飞书访问令牌失败: {result}")
                return None
        except Exception as e:
            logger.error(f"❌ 获取飞书访问令牌异常: {e}")
            return None

    def send_message(self, user_id: str, message: str, msg_type: str = "text") -> bool:
        """发送消息给指定用户"""
        try:
            token = self._get_access_token()
            if not token:
                return False

            url = f"{self.base_url}/im/v1/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            if msg_type == "text":
                content = json.dumps({"text": message})
            else:
                content = json.dumps({"text": message})

            params = {"receive_id_type": "open_id"}
            data = {
                "receive_id": user_id,
                "msg_type": msg_type,
                "content": content
            }

            logger.info(f"📤 直接API发送飞书消息: {len(message)}字符")
            response = requests.post(url, headers=headers, params=params, json=data, timeout=15)
            result = response.json()

            if result.get("code") == 0:
                logger.info("✅ 飞书消息直接API发送成功")
                return True
            else:
                logger.error(f"❌ 飞书消息发送失败: {result}")
                return False
        except requests.Timeout:
            logger.error("❌ 飞书消息发送超时")
            return False
        except Exception as e:
            logger.error(f"❌ 飞书消息发送异常: {e}")
            return False


class EnhancedFeishuSender:
    """
    增强版飞书消息发送器

    发送策略（按优先级）:
    1. 直接API调用 (无Node.js依赖)
    2. CLI调用 (带内存限制)
    3. 文件Fallback
    """

    def __init__(self,
                 fallback_dir: str = "/root/.openclaw/workspace/logs/feishu_messages",
                 node_memory_mb: int = 1024,
                 process_timeout: int = 30,
                 max_retries: int = 3):
        self.fallback_dir = Path(fallback_dir)
        self.fallback_dir.mkdir(parents=True, exist_ok=True)

        self.node_memory_mb = node_memory_mb
        self.process_timeout = process_timeout
        self.max_retries = max_retries
        self.openclaw_path = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"

        # 初始化直接API客户端
        self.direct_api = FeishuDirectAPI()

        # 消息队列
        self.message_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None

        # 统计
        self.stats = {
            'total': 0,
            'direct_api_success': 0,
            'cli_success': 0,
            'failed': 0,
            'fallback': 0,
        }

        logger.info(f"EnhancedFeishuSender 初始化完成")
        logger.info(f"  - Node内存限制: {node_memory_mb}MB")
        logger.info(f"  - 进程超时: {process_timeout}秒")

    def send(self, content: str, target: str = "ou_b8a256a9cb526db6c196cb438d6893a6",
             channel: str = "feishu", block: bool = True) -> MessageTask:
        """发送消息"""
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
            self._process_task(task)
        else:
            self.message_queue.put(task)
            if not self.is_running:
                self.start_worker()

        return task

    def _process_task(self, task: MessageTask):
        """处理消息任务"""
        task.status = MessageStatus.PROCESSING
        logger.info(f"处理消息任务 {task.id}")

        # 策略1: 直接API调用
        logger.info("尝试策略1: 直接API调用...")
        try:
            if self.direct_api.send_message(task.target, task.content):
                task.status = MessageStatus.SUCCESS
                self.stats['direct_api_success'] += 1
                logger.info(f"✅ 消息 {task.id} 直接API发送成功")
                return
        except Exception as e:
            logger.warning(f"⚠️ 直接API调用失败: {e}")

        # 策略2: CLI调用（带内存限制）
        logger.info("尝试策略2: CLI调用...")
        for attempt in range(self.max_retries):
            task.attempts = attempt + 1
            try:
                if self._send_via_cli(task):
                    task.status = MessageStatus.SUCCESS
                    self.stats['cli_success'] += 1
                    logger.info(f"✅ 消息 {task.id} CLI发送成功")
                    return
            except Exception as e:
                task.last_error = str(e)
                logger.warning(f"⚠️ CLI调用第{attempt + 1}次失败: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避

        # 策略3: 降级到文件
        logger.warning(f"所有发送策略失败，降级到文件保存")
        task.status = MessageStatus.FALLBACK
        self._save_to_fallback(task)
        self.stats['fallback'] += 1

    def _send_via_cli(self, task: MessageTask) -> bool:
        """通过CLI发送消息"""
        # 创建临时脚本
        script_content = self._generate_sender_script(task)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name

        try:
            env = os.environ.copy()
            env['NODE_OPTIONS'] = f'--max-old-space-size={self.node_memory_mb}'
            env['PYTHONUNBUFFERED'] = '1'

            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            try:
                stdout, stderr = process.communicate(timeout=self.process_timeout)
                if process.returncode == 0:
                    result = json.loads(stdout.strip())
                    return result.get('success', False)
                else:
                    logger.error(f"CLI子进程失败: {stderr}")
                    return False
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                logger.error(f"CLI子进程超时")
                return False
        finally:
            try:
                os.unlink(script_path)
            except:
                pass

    def _generate_sender_script(self, task: MessageTask) -> str:
        """生成发送脚本"""
        escaped_content = task.content.replace('"', '\\"').replace("'", "\\'")

        return f'''#!/usr/bin/env python3
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

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout={self.process_timeout})

    result['success'] = proc.returncode == 0
    result['stdout'] = proc.stdout
    result['stderr'] = proc.stderr
    result['returncode'] = proc.returncode

except Exception as e:
    result['error'] = str(e)

print(json.dumps(result))
sys.exit(0 if result['success'] else 1)
'''

    def _save_to_fallback(self, task: MessageTask):
        """保存到fallback文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{task.id}.json"
        filepath = self.fallback_dir / filename

        data = {
            'task': task.to_dict(),
            'saved_at': datetime.now().isoformat(),
            'full_content': task.content,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 消息已保存到fallback: {filepath}")

    def start_worker(self):
        """启动后台工作线程"""
        if self.is_running:
            return
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("工作线程已启动")

    def stop_worker(self):
        """停止后台工作线程"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("工作线程已停止")

    def _worker_loop(self):
        """工作线程主循环"""
        while self.is_running:
            try:
                task = self.message_queue.get(timeout=1)
                self._process_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程异常: {e}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()


# 便捷函数
_sender_instance: Optional[EnhancedFeishuSender] = None

def get_sender() -> EnhancedFeishuSender:
    """获取全局发送器实例"""
    global _sender_instance
    if _sender_instance is None:
        _sender_instance = EnhancedFeishuSender()
    return _sender_instance

def send_message(content: str, target: str = "ou_b8a256a9cb526db6c196cb438d6893a6",
                 channel: str = "feishu", block: bool = True) -> bool:
    """便捷函数：发送飞书消息"""
    sender = get_sender()
    task = sender.send(content, target, channel, block)
    return task.status == MessageStatus.SUCCESS


# 测试
if __name__ == "__main__":
    test_message = """📊 **T01增强版发送器测试**
时间: {}
状态: 测试运行中
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    print("=" * 60)
    print("Enhanced Feishu Sender 测试")
    print("=" * 60)

    sender = EnhancedFeishuSender()
    task = sender.send(test_message, block=True)

    print(f"\n结果: {task.status.value}")
    print(f"尝试次数: {task.attempts}")
    print(f"统计: {sender.get_stats()}")
    print("\n✅ 测试完成")
