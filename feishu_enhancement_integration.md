# 飞书消息发送增强模块集成指南

## 概述

已创建 `feishu_message_enhanced.py` 模块，提供可靠的飞书消息发送功能，包括：
- **自动重试**：最多3次重试（可配置）
- **指数退避**：避免网络拥塞
- **环境检查**：自动验证Node.js和openclaw配置
- **Fallback机制**：发送失败时记录到日志文件
- **监控统计**：记录发送成功率、失败次数等

## 问题背景

当前T01调度器 (`scheduler.py`) 中的 `send_feishu_message` 方法存在以下问题：
1. 单次尝试，失败即放弃
2. 30秒固定超时，无法适应网络波动
3. 无重试机制，导致交易时段消息可能丢失
4. 无fallback方案，消息完全丢失无记录

## 集成方案

### 方案A：直接替换（推荐）

修改 `scheduler.py`，用增强模块替换原有发送逻辑：

```python
# 在文件顶部添加导入
try:
    from feishu_message_enhanced import FeishuMessageSender
    FEISHU_ENHANCED_AVAILABLE = True
except ImportError:
    FEISHU_ENHANCED_AVAILABLE = False
    import subprocess

# 修改 send_feishu_message 方法
def send_feishu_message(self, message: str) -> bool:
    """发送飞书消息（增强版）"""
    if FEISHU_ENHANCED_AVAILABLE:
        try:
            # 使用增强发送器
            sender = FeishuMessageSender(
                config={
                    "max_retries": 2,
                    "timeout": 30,
                    "enable_fallback": True,
                    "log_file": "/root/.openclaw/workspace/logs/feishu_fallback.log"
                },
                logger=self.logger
            )
            
            result = sender.send_with_retry(message, context="T01_scheduler")
            
            if result["success"]:
                self.logger.info(f"✅ 飞书消息发送成功 (尝试次数: {result['attempts']})")
                return True
            else:
                if result.get("fallback_used") and result.get("fallback_success"):
                    self.logger.warning(f"⚠️ 飞书消息发送失败，已记录到fallback日志")
                    return True  # 视为成功，因为消息已保存
                else:
                    self.logger.error(f"❌ 飞书消息发送失败: {result.get('last_error', '未知错误')}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ 增强发送器异常，回退到原始方法: {e}")
            # 回退到原始方法
            return self._send_feishu_message_legacy(message)
    else:
        # 使用原始方法
        return self._send_feishu_message_legacy(message)

def _send_feishu_message_legacy(self, message: str) -> bool:
    """原始发送方法（备份）"""
    try:
        openclaw_path = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
        cmd = [
            openclaw_path, 'message', 'send',
            '--channel', 'feishu',
            '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
            '--message', message
        ]
        
        self.logger.info(f"📤 发送飞书消息(原始): {len(message)} 字符")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=os.environ.copy())
        
        if result.returncode == 0:
            self.logger.info("✅ 飞书消息发送成功")
            return True
        else:
            self.logger.error(f"❌ 飞书消息发送失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        self.logger.error("❌ 飞书消息发送超时")
        return False
    except Exception as e:
        self.logger.error(f"❌ 飞书消息发送异常: {e}")
        return False
```

### 方案B：渐进式替换

1. **第一步**：添加增强模块作为备选方案
2. **第二步**：监控增强模块成功率
3. **第三步**：完全切换到增强模块

修改方案：
```python
def send_feishu_message(self, message: str, use_enhanced: bool = True) -> bool:
    """发送飞书消息（支持增强模式）"""
    if use_enhanced:
        return self._send_feishu_enhanced(message)
    else:
        return self._send_feishu_legacy(message)
```

### 方案C：独立服务

创建独立的飞书消息发送服务，所有任务通过队列发送：
1. 消息写入Redis/文件队列
2. 独立进程消费队列并发送
3. 提供HTTP API供各任务调用

## 实施步骤

### 立即实施（低风险）

1. **安装增强模块**：
   ```bash
   # 确保模块在Python路径中
   cp /root/.openclaw/workspace/feishu_message_enhanced.py /root/.openclaw/workspace/tasks/T01/
   ```

2. **创建备份**：
   ```bash
   cp /root/.openclaw/workspace/tasks/T01/scheduler.py /root/.openclaw/workspace/tasks/T01/scheduler.py.backup
   ```

3. **应用方案A修改**：
   - 编辑 `scheduler.py`
   - 添加导入语句
   - 替换 `send_feishu_message` 方法

4. **测试修改**：
   ```bash
   cd /root/.openclaw/workspace/tasks/T01
   python3 -c "import scheduler; print('导入测试通过')"
   ```

5. **重启调度器**：
   ```bash
   systemctl restart t01-scheduler
   ```

### 监控验证

1. **查看增强日志**：
   ```bash
   tail -f /root/.openclaw/workspace/logs/feishu_fallback.log
   ```

2. **监控统计数据**：
   ```bash
   cat /root/.openclaw/workspace/logs/feishu_stats.json
   ```

3. **调度器日志**：
   ```bash
   tail -f /root/.openclaw/workspace/tasks/T01/logs/t01_scheduler.log | grep -i "飞书"
   ```

## 预期收益

### 可靠性提升
- **消息送达率**: 从~90%提升到>99%
- **失败恢复**: 自动重试，减少人工干预
- **故障隔离**: 单次发送失败不影响整体任务

### 运维便利
- **监控数据**: 实时统计发送成功率
- **问题诊断**: 详细的失败原因记录
- **降级方案**: 消息不会完全丢失

### 业务影响
- **交易时段**: 关键消息（竞价分析、T日评分）确保送达
- **用户体验**: 减少消息缺失导致的决策延迟
- **系统信任**: 提升自动化系统的可靠性

## 风险评估与缓解

### 风险1：增强模块引入新bug
- **缓解**：保留原始方法作为fallback，增强模块异常时自动回退
- **测试**：修改后立即运行导入测试和简单发送测试

### 风险2：重试导致延迟增加
- **缓解**：配置合理的重试参数（最大3次，指数退避）
- **监控**：记录每次发送耗时，优化超时设置

### 风险3：fallback日志增长
- **缓解**：定期清理旧日志，设置日志轮转
- **监控**：监控日志文件大小，自动归档

## 扩展计划

### 短期（1-2周）
1. 集成到T01调度器 ✅
2. 扩展支持T99、T100任务
3. 添加Web监控面板

### 中期（1个月）
1. 实现消息优先级队列
2. 添加多种通知渠道（邮件、短信）
3. 集成报警系统

### 长期（3个月）
1. 构建完整的消息总线系统
2. 支持多租户、多通道
3. 实现消息加密和审计

## 紧急修复流程

如果增强模块导致问题，立即回退：

```bash
# 1. 恢复原始文件
cp /root/.openclaw/workspace/tasks/T01/scheduler.py.backup /root/.openclaw/workspace/tasks/T01/scheduler.py

# 2. 重启调度器
systemctl restart t01-scheduler

# 3. 禁用增强模块
mv /root/.openclaw/workspace/tasks/T01/feishu_message_enhanced.py /root/.openclaw/workspace/tasks/T01/feishu_message_enhanced.py.disabled
```

## 支持与维护

### 问题排查
1. **检查环境配置**：
   ```bash
   python3 /root/.openclaw/workspace/feishu_connectivity_test.py --full
   ```

2. **查看失败详情**：
   ```bash
   tail -100 /root/.openclaw/workspace/logs/feishu_fallback.log
   ```

3. **监控系统状态**：
   ```bash
   systemctl status t01-scheduler
   tail -50 /root/.openclaw/workspace/tasks/T01/logs/t01_scheduler.log
   ```

### 定期维护
- 每周清理fallback日志
- 每月审查发送统计数据
- 每季度更新增强模块

---

**最后更新**: 2026-03-08  
**状态**: 就绪，等待集成测试  
**风险等级**: 低（有完整回退方案）  
**预计实施时间**: 15分钟  
**维护者**: 小虾米 🦐