#!/usr/bin/env python3
"""
T01飞书消息直接发送模块
绕过openclaw CLI，直接使用飞书API发送消息
解决subprocess调用导致的超时和GC问题
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FeishuDirectSender:
    """飞书直接发送器 - 使用飞书Open API直接发送消息"""
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        """
        初始化飞书发送器
        
        Args:
            app_id: 飞书应用ID，如果不提供则从环境变量获取
            app_secret: 飞书应用密钥，如果不提供则从环境变量获取
        """
        self.app_id = app_id or os.environ.get('FEISHU_APP_ID')
        self.app_secret = app_secret or os.environ.get('FEISHU_APP_SECRET')
        self.access_token: Optional[str] = None
        self.token_expire_time: Optional[datetime] = None
        
        # 飞书API基础URL
        self.base_url = "https://open.feishu.cn/open-apis"
        
        if not self.app_id or not self.app_secret:
            logger.warning("⚠️ 飞书应用凭证未配置，将使用webhook方式发送")
    
    def _get_access_token(self) -> Optional[str]:
        """获取飞书访问令牌"""
        # 检查令牌是否过期
        if self.access_token and self.token_expire_time and datetime.now() < self.token_expire_time:
            return self.access_token
        
        try:
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                # 令牌有效期约2小时，提前5分钟过期
                expire = result.get("expire", 7200)
                self.token_expire_time = datetime.now().timestamp() + expire - 300
                logger.info("✅ 飞书访问令牌获取成功")
                return self.access_token
            else:
                logger.error(f"❌ 获取飞书访问令牌失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取飞书访问令牌异常: {e}")
            return None
    
    def send_message_to_user(self, user_id: str, message: str, msg_type: str = "text") -> bool:
        """
        发送消息给指定用户
        
        Args:
            user_id: 用户open_id
            message: 消息内容
            msg_type: 消息类型，默认text
            
        Returns:
            bool: 是否发送成功
        """
        try:
            token = self._get_access_token()
            if not token:
                logger.error("❌ 无法获取飞书访问令牌")
                return False
            
            url = f"{self.base_url}/im/v1/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 构建消息内容
            if msg_type == "text":
                content = json.dumps({"text": message})
            elif msg_type == "interactive":
                content = message  # 已经是JSON字符串
            else:
                content = json.dumps({"text": message})
            
            params = {
                "receive_id_type": "open_id"
            }
            
            data = {
                "receive_id": user_id,
                "msg_type": msg_type,
                "content": content
            }
            
            logger.info(f"📤 直接发送飞书消息给用户: {user_id}, 长度: {len(message)}")
            
            response = requests.post(
                url, 
                headers=headers, 
                params=params,
                json=data, 
                timeout=15
            )
            
            result = response.json()
            
            if result.get("code") == 0:
                logger.info("✅ 飞书消息直接发送成功")
                return True
            else:
                logger.error(f"❌ 飞书消息发送失败: {result}")
                return False
                
        except requests.Timeout:
            logger.error("❌ 飞书消息发送超时(15秒)")
            return False
        except Exception as e:
            logger.error(f"❌ 飞书消息发送异常: {e}")
            return False
    
    def send_message_webhook(self, webhook_url: str, message: str) -> bool:
        """
        使用webhook发送消息（备用方案）
        
        Args:
            webhook_url: 飞书webhook URL
            message: 消息内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }
            
            logger.info(f"📤 通过webhook发送飞书消息，长度: {len(message)}")
            
            response = requests.post(
                webhook_url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 or result.get("StatusCode") == 0:
                    logger.info("✅ Webhook消息发送成功")
                    return True
                else:
                    logger.error(f"❌ Webhook消息发送失败: {result}")
                    return False
            else:
                logger.error(f"❌ Webhook请求失败: {response.status_code}")
                return False
                
        except requests.Timeout:
            logger.error("❌ Webhook消息发送超时(10秒)")
            return False
        except Exception as e:
            logger.error(f"❌ Webhook消息发送异常: {e}")
            return False


# 便捷函数
def send_feishu_message_direct(user_id: str, message: str, app_id: Optional[str] = None, app_secret: Optional[str] = None) -> bool:
    """
    便捷函数：直接发送飞书消息
    
    Args:
        user_id: 用户open_id
        message: 消息内容
        app_id: 飞书应用ID（可选）
        app_secret: 飞书应用密钥（可选）
        
    Returns:
        bool: 是否发送成功
    """
    sender = FeishuDirectSender(app_id, app_secret)
    return sender.send_message_to_user(user_id, message)


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    # 测试消息
    test_msg = "🧪 测试消息：T01飞书直接发送模块工作正常"
    
    # 从环境变量获取配置
    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    user_id = os.environ.get('FEISHU_USER_ID', 'ou_b8a256a9cb526db6c196cb438d6893a6')
    
    if app_id and app_secret:
        success = send_feishu_message_direct(user_id, test_msg, app_id, app_secret)
        print(f"发送结果: {'成功' if success else '失败'}")
    else:
        print("⚠️ 未配置飞书应用凭证，跳过测试")
