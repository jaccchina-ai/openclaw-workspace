# 子Agent模式设计方案

## 目标
- **主会话永不阻塞**：长时间任务（如T99扫描）在子Agent中运行
- **自动推送结果**：子Agent完成任务后自动将结果发送到主会话
- **失败隔离**：子Agent崩溃不影响主会话稳定性
- **进度监控**：可随时查看子Agent运行状态

## 适用场景
1. **T99每日复盘扫描**（5-10分钟）
2. **T100宏观监控**（如有复杂数据采集）
3. **T01选股任务**（如有耗时计算）
4. **其他长时间API调用任务**

## 技术实现

### 1. 使用 `sessions_spawn` API
```python
sessions_spawn(
    task="运行T99今日扫描，交易日: YYYYMMDD",
    agentId="main",
    mode="run",  # 一次性任务
    label="T99扫描任务",
    timeoutSeconds=300,
    runTimeoutSeconds=600  # 任务最大运行时间
)
```

### 2. 子Agent脚本模板
```python
#!/usr/bin/env python3
# subagent_t99.py - T99扫描子Agent

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/skills/a-share-short-decision')

def run_t99_scan():
    from tools.fusion_engine import short_term_signal_engine
    from datetime import datetime
    
    # 确定交易日（自动判断）
    today = datetime.now()
    # TODO: 使用Tushare trade_cal判断是否为交易日
    
    result = short_term_signal_engine(analysis_date='20260302', debug=False)
    
    # 格式化结果消息
    message = f"📊 T99扫描结果 ({result['analysis_date']})\n"
    message += f"信号: {result['signal']} | 分数: {result['score']}\n"
    message += f"候选股: {len(result['candidates'])}只\n"
    
    # 通过OpenClaw CLI发送消息
    import subprocess
    cmd = [
        '/root/.nvm/versions/node/v22.22.0/bin/node',
        '/root/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/openclaw.mjs',
        'message', 'send',
        '--channel', 'feishu',
        '--target', 'chat:oc_ff08c55a23630937869cd222dad0bf14',
        '--message', message
    ]
    subprocess.run(cmd, timeout=30)
    
    return True

if __name__ == '__main__':
    try:
        success = run_t99_scan()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"子Agent运行失败: {e}")
        sys.exit(1)
```

### 3. Cron集成方案
```bash
# 原始cron（阻塞模式）
30 14 * * 1-5 cd /root/.openclaw/workspace/skills/a-share-short-decision && ./run_scan.sh

# 子Agent模式（非阻塞）
30 14 * * 1-5 cd /root/.openclaw/workspace && /root/.nvm/versions/node/v22.22.0/bin/node -e "require('openclaw').sessions_spawn({task: '运行T99扫描', agentId: 'main', mode: 'run'})"
```

### 4. 监控与管理
```bash
# 查看子Agent状态
sessions_list --kinds run

# 查看子Agent历史
sessions_history --sessionKey <session_key>

# 终止子Agent
subagents kill --target <session_key>
```

## 实施步骤
1. ✅ **T100修复验证**（今晚22:00）
2. 🔧 **创建子Agent脚本模板**（等待T100成功后）
3. 🔧 **修改T99 cron配置**（使用子Agent模式）
4. 🔧 **测试子Agent工作流程**
5. 🔧 **扩展到其他任务**

## 优势总结
1. **用户体验**：主会话即时响应，无需等待长时间任务
2. **系统稳定性**：子Agent失败不影响主功能
3. **可扩展性**：易于添加新的后台任务
4. **监控能力**：OpenClaw原生支持会话管理

## 注意事项
1. **资源限制**：避免同时启动过多子Agent
2. **超时设置**：合理设置任务超时，避免僵尸进程
3. **错误处理**：子Agent应有完善的错误处理和日志记录
4. **结果传递**：确保结果能正确传递回主会话

---
*设计版本: 1.0 | 更新日期: 2026-03-01*