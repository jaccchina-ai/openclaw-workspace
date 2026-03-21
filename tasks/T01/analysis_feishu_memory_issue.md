# T01 飞书消息发送 Node.js 内存溢出问题 - 根因分析报告

## 问题概述

**症状**: `openclaw message send` 命令执行时 Node.js 内存溢出 (JavaScript heap out of memory)  
**影响**: T01 晚间选股和早间竞价分析的消息推送失败  
**发生频率**: 从2026-02-25到2026-03-05持续发生，日志中记录超过20次错误

---

## 根因分析

### 1. Node.js 内存限制

**问题**: Node.js 默认堆内存限制为 **512MB**（在64位系统上），当openclaw CLI加载大量插件和依赖时容易超出。

**证据**:
```
FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory
Mark-Compact 248.4 (258.8) -> 247.3 (259.1) MB
```

**分析**:
- openclaw-gateway 进程占用 736MB 内存
- 每次调用 `openclaw message send` 会启动新的Node.js进程
- 消息内容较大时（如完整的选股报告），序列化和传输需要额外内存
- 系统总内存仅1.9GB，可用约662MB，处于紧张状态

### 2. openclaw CLI 内存使用模式

**问题**: openclaw CLI 加载完整的插件生态系统，包括：
- memory-lancedb 插件
- 多个channel插件（feishu、telegram等）
- 工具链初始化

**证据**:
```
[plugins] memory-lancedb: plugin registered (db: /root/.openclaw/memory/lancedb, lazy init)
```

**分析**:
- 每次CLI调用都会初始化完整的运行时环境
- 即使只是发送一条简单消息，也需要加载所有插件
- 这是架构层面的问题，不是简单的配置调整可以解决的

### 3. 消息内容大小影响

**问题**: T01选股报告通常包含大量数据：
- 多只股票详细信息
- 评分数据
- 技术指标
- 格式化文本

**当前代码中的限制**:
```python
max_msg_len = 2000
if len(message) > max_msg_len:
    message = message[:max_msg_len] + "\n...(消息已截断)"
```

**分析**:
- 虽然代码已经截断到2000字符，但Node.js进程本身的内存开销更大
- 问题不在于消息内容大小，而在于CLI启动时的固定开销

### 4. 系统整体内存压力

**系统状态**:
```
Mem: 1.9Gi total, 1.3Gi used, 263Mi free
Swap: 8.0Gi total, 1.0Gi used
```

**分析**:
- 系统内存紧张，可用内存仅263MB
- Swap已使用1GB，说明内存压力持续存在
- 当系统内存不足时，Node.js更容易触发OOM

### 5. 调用方式问题

**当前调用方式**:
```python
subprocess.run([openclaw_path, 'message', 'send', ...], env=env)
```

**问题**:
- 每次调用都创建新进程
- 进程创建开销大
- 没有进程池复用
- NODE_OPTIONS环境变量设置512MB限制，但可能仍不足

---

## 根本原因总结

1. **直接原因**: Node.js堆内存限制（512MB）不足以支撑openclaw CLI的完整初始化
2. **系统原因**: 服务器内存紧张（1.9GB总内存），可用内存不足
3. **架构原因**: openclaw CLI设计为全功能工具，每次调用都加载完整运行时
4. **调用原因**: 频繁创建新进程，没有复用机制

---

## 解决方案矩阵

| 方案 | 类型 | 实施难度 | 效果 | 优先级 |
|------|------|----------|------|--------|
| 增加Node.js内存限制 | 短期 | 低 | 中 | P0 |
| 使用直接API调用绕过CLI | 中期 | 中 | 高 | P0 |
| 消息队列+批量发送 | 中期 | 中 | 高 | P1 |
| 系统内存升级 | 长期 | 高 | 高 | P2 |
| 架构重构（微服务） | 长期 | 高 | 极高 | P3 |

---

## 已实施的React Loop方案评估

**当前状态**: 已实施 `react_loop_feishu_sender.py`

**优点**:
- 消息队列缓冲
- 独立进程执行（资源隔离）
- 指数退避重试
- 优雅降级到文件

**仍需改进**:
- 仍然依赖openclaw CLI，没有从根本上解决内存问题
- 需要增加直接API调用作为备用方案
- 需要调整Node.js内存限制

---

## 建议实施路径

### 阶段1: 立即修复（今天）
1. 将NODE_OPTIONS增加到1024MB
2. 启用feishu_direct_sender作为备用方案
3. 添加内存监控和告警

### 阶段2: 短期优化（本周）
1. 实现消息队列+批量发送
2. 优化消息内容大小
3. 添加发送失败自动重试机制

### 阶段3: 长期改进（本月）
1. 评估系统内存升级
2. 考虑架构重构
3. 建立完整的监控体系

---

## 相关文件

- `/root/.openclaw/workspace/tasks/T01/scheduler.py` - 调度器主文件
- `/root/.openclaw/workspace/tasks/T01/react_loop_feishu_sender.py` - React Loop发送器
- `/root/.openclaw/workspace/tasks/T01/feishu_direct_sender.py` - 直接API发送器
- `/root/.openclaw/workspace/logs/feishu_fallback.log` - 错误日志

---

*报告生成时间: 2026-03-19*  
*分析人: ReAct Loop Agent*
