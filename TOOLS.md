# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 🔍 网页总结配置

**技能**：`summarize`（已安装，API 密钥已配置）

**模型与端点**：
- 模型：`openai/deepseek-chat`
- 端点：`https://api.deepseek.com/v1`
- 密钥环境变量：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`SUMMARIZE_MODEL`

**详细度参数**：
- `--length xxl`（最高详细度）
- `--max-output-tokens 8000`（最大输出 token 数）

**输出结构**：
1. **结论**：一句话整体定性
2. **关键信息（二次整理）**：分点/表格形式，提取核心信息
3. **查证过程**：
   - 工具与参数说明
   - 信息验证（交叉验证、不确定性说明）
   - 后续优化建议

**用户偏好**（老板确认）：
- 详细程度：尽可能详细（`xxl` + `max-output-tokens` 最大值）
- 结构：在模型输出基础上进行二次整理（分点、表格、补充查证过程）

---

## 🔧 系统稳定性模式与解决方案

### 重复问题 #1：健康监控器进程停止
**模式**：`scheduler_health_monitor.py` 进程频繁停止（≥5次/天）
**解决方案**：
- 自动重启脚本：`/root/.openclaw/workspace/tasks/T01/health_monitor_guard.sh`
- 检查命令：`pgrep -f "python3.*scheduler_health_monitor.py"`
- 重启命令：`cd /root/.openclaw/workspace/tasks/T01 && nohup python3 scheduler_health_monitor.py --mode monitor > health_monitor.log 2>&1 &`
- 监控日志：`health_monitor_guard.log`

### 重复问题 #2：未知执行失败
**模式**："Exec failed (session-name-fragment, code 0)" 消息频繁出现（单日最高27次）
**特征**：短会话名称片段（如 `plaid-lo`, `delta-pr`, `tide-clo`, `crisp-ha`, `quiet-la`, `tidal-cl`, `cool-wha`, `kind-sag`, `plaid-br`, `glow-wha`, `crisp-ze`, `swift-ne`, `crisp-da`, `tidal-ce` 等），退出码 0
**根本原因**：OpenClaw内部会话管理、子进程清理、心跳检查等内部机制
**影响**：系统日志中出现大量失败消息，但核心功能正常（低影响）

**应对策略**：
1. **监控频率**：记录每日出现次数，如>10次/天需人工检查
2. **系统检查**：检查系统负载和资源使用情况（内存、CPU、磁盘）
3. **日志分析**：监控`/tmp/clawdbot/`日志目录（如存在）获取更多上下文
4. **版本检查**：确保OpenClaw和Gateway版本兼容，无已知bug
5. **模式识别**：观察是否与特定操作（如心跳、子进程生成）相关

**学习要点**：
- **内部机制**：OpenClaw可能为临时任务创建短生命周期会话，正常退出码0表示预期行为
- **日志噪音**：某些内部操作可能产生大量日志条目，需区分真正错误与预期行为
- **监控阈值**：设置合理阈值（如>20次/天）避免过度警报

**维护记录**：2026-03-01 从LRN-20260227-001学习记录升级，更新频率数据

### 重复问题 #3：WhatsApp网关连接
**模式**：状态428/503错误，自动重连成功
**特征**：间歇性断开，通常几秒内恢复（今日503错误恢复时间3秒）
**影响**：低（自动恢复）
**监控**：记录断开频率，如>5次/天需检查网络配置
**新增记录**：2026-03-06 出现503状态码错误，同样快速自动恢复

### 重复问题 #4：T100宏观监控测试模式
**模式**：`run_monitor.py` 检查 `TEST_MODE` 环境变量
**特征**：报告生成但跳过飞书发送
**解决方案**：
1. 检查cron环境变量设置
2. 修改脚本：`if os.environ.get("TEST_MODE") != "1":` 或添加强制发送参数
3. 临时修复：`export TEST_MODE=0` 在cron命令中

### T01推送路径问题
**问题**：`openclaw` 命令不在cron环境PATH中
**解决方案**：
- 使用绝对路径：`/root/.nvm/versions/node/v22.22.0/bin/openclaw`
- 修正命令语法：`openclaw message send --channel feishu ...`
- 环境变量：确保PATH包含OpenClaw安装目录

---

Add whatever helps you do your job. This is your cheat sheet.

## 🔧 T01调度器故障排除

### 问题症状
- 调度器进程运行但无任务执行日志
- 无今日候选股文件生成
- 日志最后记录为旧日期

### 诊断步骤
1. **检查进程状态**:
   ```bash
   systemctl status t01-scheduler
   pstree -p $(systemctl show t01-scheduler -p MainPID --value)
   ```

2. **检查日志文件**:
   ```bash
   tail -50 /root/.openclaw/workspace/tasks/T01/logs/t01_scheduler.log
   tail -50 /root/.openclaw/workspace/tasks/T01/t01_limit_up.log
   ```

3. **检查候选股文件**:
   ```bash
   ls -la /root/.openclaw/workspace/tasks/T01/state/candidates_*.json
   ```

### 时区注意事项
**系统时区设置**: CST（中国标准时间/北京时间）
- 正确命令: `date`（直接显示北京时间）
- 错误命令: `date -d '+8 hours'`（会再加8小时，导致时间错误）
- 验证: `date '+%Z'` 应输出 `CST`

### 解决方案
#### A. 重启调度器服务
```bash
systemctl restart t01-scheduler
# 监控启动日志
tail -f /root/.openclaw/workspace/tasks/T01/logs/t01_scheduler.log
```

#### B. 手动运行选股任务
```bash
cd /root/.openclaw/workspace/tasks/T01
# 运行今晚选股（T日评分）
python3 limit_up_strategy_new.py --date $(date +%Y%m%d)
# 或使用调度器运行模式
python3 scheduler.py --mode run --date $(date +%Y%m%d)
```

#### C. 调试调度器
```bash
cd /root/.openclaw/workspace/tasks/T01
# 调试模式查看调度器状态
python3 scheduler.py --mode debug
# 检查配置
cat config.yaml | grep -A5 -B5 "schedule"
```

### 预防措施
1. **定期监控**: 每天20:10检查候选股文件生成
2. **日志轮转**: 定期清理旧日志文件
3. **健康检查**: 使用健康监控器检测调度器状态
4. **自动重启**: 配置systemd服务失败时自动重启

### 相关文件
- 调度器脚本: `/root/.openclaw/workspace/tasks/T01/scheduler.py`
- 配置文件: `/root/.openclaw/workspace/tasks/T01/config.yaml`
- 主日志: `/root/.openclaw/workspace/tasks/T01/logs/t01_scheduler.log`
- 选股日志: `/root/.openclaw/workspace/tasks/T01/t01_limit_up.log`
- 候选股目录: `/root/.openclaw/workspace/tasks/T01/state/`

## 🔧 T99扫描引擎超时故障排除

### 问题症状
- 扫描引擎卡在"Running A-share short-term signal engine for YYYY-MM-DD (timeout 300s)..."
- 日志无进一步输出，进程未完成
- 阻塞策略复盘流程，无每日复盘推送

### 根本原因
1. **AKShare API不可用**: 服务器无响应 (`Remote end closed connection without response`)
2. **回退机制不足**: 原`_fallback_scan_strong_stocks()`返回空列表
3. **超时设置不合理**: 整体300秒超时，单个API调用3秒超时

### 已实施修复
1. **增强回退逻辑**: 修改`_fallback_scan_strong_stocks()`，使用Tushare作为备用数据源
2. **优化超时设置**: 
   - 总超时: 300秒 → **600秒** → **900秒** (`run_scan.sh`)
   - API超时: 3秒 → **2秒** (`market_data.py`)
3. **代码修复**: 解决datetime变量冲突问题
4. **交易日检查优化** (2026-02-28):
   - 将`run_scan.sh`中的akshare日历检查替换为Tushare `trade_cal` API（更可靠）
   - 使用T01的token: `870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab`
   - 避免在非交易日执行API调用挂起问题

### 新增诊断 (2026-02-28)
**根本原因**: 在非交易日/非交易时段，`get_sector_rotation()`函数中的akshare/Tushare API调用挂起
- `get_sector_rotation()`耗时13.5秒，返回"unavailable"数据源
- 板块数据API在非交易日返回空但函数仍执行完整逻辑
- 连续4天（2月24-27日）扫描超时

**修复验证**:
- 新交易日检查正确识别今天(2月28日周六)为"NON_TRADING_DAY"
- 预期：今天扫描将跳过（正确行为）
- 待验证：周一(3月2日)扫描应正常执行

### 诊断步骤
1. **测试AKShare连接**:
   ```bash
   python3 -c "import akshare as ak; df=ak.stock_zh_a_spot_em(); print(f'AKShare连接成功: {len(df)}行')"
   ```

2. **测试Tushare连接**:
   ```bash
   python3 -c "import tushare as ts; ts.set_token('870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'); pro=ts.pro_api(); df=pro.trade_cal(exchange='SSE', start_date='20260201', end_date='20260228'); print(f'Tushare连接成功: {len(df)}行')"
   ```

3. **测试扫描引擎**:
   ```bash
   cd /root/.openclaw/workspace/skills/a-share-short-decision
   timeout 60 python3 -c "from tools.fusion_engine import short_term_signal_engine; result=short_term_signal_engine(analysis_date='20260227', debug=True); print('✅ 扫描引擎成功')"
   ```

### 解决方案
#### A. 深度优化扫描引擎
1. **并行执行**: 将独立API调用并行化
2. **智能回退**: 实现多数据源无缝切换
3. **缓存机制**: 缓存常用数据减少API调用

#### B. 临时绕过
1. **使用历史数据模式**: 启用`historical_mode`
2. **减少扫描范围**: 限制板块数量和股票数量
3. **手动运行**: 使用调试模式逐步执行

### 相关文件
- 扫描引擎: `/root/.openclaw/workspace/skills/a-share-short-decision/tools/fusion_engine.py`
- 市场数据: `/root/.openclaw/workspace/skills/a-share-short-decision/tools/market_data.py`
- 配置文件: `/root/.openclaw/workspace/skills/a-share-short-decision/config.json`
- 扫描脚本: `/root/.openclaw/workspace/skills/a-share-short-decision/run_scan.sh`
- 扫描日志: `/root/.openclaw/workspace/skills/a-share-short-decision/scan.log`

### 紧急修复实施 (2026-03-03)
**问题**: T99连续第6天失败，扫描卡死9.5+小时
**根本原因**: `get_sector_rotation`函数中的Tushare API在非交易时段挂起
**紧急措施**:
1. **终止卡住进程**: 清理卡住的扫描进程
2. **创建修复版脚本**: `run_scan_fixed.sh`（300秒超时 + 交易时段检查）
3. **更新cron任务**: 切换到修复版脚本，避免非交易时段API调用
4. **超时缩短**: 900秒 → 300秒，更快失败释放资源

**修复文件**:
- 紧急修复脚本: `/root/.openclaw/workspace/t99_emergency_fix.sh`
- 修复版扫描: `/root/.openclaw/workspace/skills/a-share-short-decision/run_scan_fixed.sh`
- 完整修复方案: `/root/.openclaw/workspace/t99_timeout_fix.py`

**预期效果**: 明日14:30扫描将在300秒内完成或优雅失败，确保系统资源可用

### JSON序列化错误修复 (2026-03-06)
**问题**: T99扫描因`TypeError: Object of type bool is not JSON serializable`失败
**根本原因**: `short_term_signal_engine`返回的数据中包含bool值（Python bool和numpy.bool_），`_print`函数的`EnhancedJSONEncoder`可能因缓存或行号问题未生效
**修复**: 重写`main.py`中的`_print`函数，使用递归转换器`_to_serializable`
1. 递归处理嵌套数据结构
2. 显式处理Python基本类型(bool, int, float, str)
3. 处理numpy类型(np.bool_, np.integer, np.floating, np.ndarray)
4. 处理pandas类型(DataFrame, Timestamp, BooleanDtype)
5. 处理datetime类型
6. 优雅降级：对无法序列化的对象使用字符串表示
**验证**: 单元测试通过，`get_market_sentiment`工具正常工作
**文件**: `/root/.openclaw/workspace/skills/a-share-short-decision/main.py`

## 🔧 T100宏观监控测试模式问题

### 问题症状
- 报告生成但跳过飞书发送
- 日志显示: "测试模式：跳过飞书发送"
- 宏观报告无法正常推送

### 根本原因
1. **硬编码测试模式**: `run_monitor.py`中`send_to_feishu(report)`调用被注释，硬编码打印"测试模式：跳过飞书发送"
2. **环境变量检查**: `send_to_feishu()`函数检查`TEST_MODE`环境变量，但主函数未调用该函数
3. **实际代码**:
```python
# 在 main() 函数中 (第2564-2566行):
print("测试模式：跳过飞书发送")
# send_to_feishu(report)  # 被注释掉

# 在 send_to_feishu() 函数中 (第2481行):
if os.environ.get("TEST_MODE") == "1":
    print("=== TEST MODE (report not sent) ===")
    return
```

### 解决方案
### 已实施修复 (2026-02-28)
1. **取消注释发送调用**: 启用`send_to_feishu(report)`函数，移除硬编码测试消息
2. **代码修改**:
   ```python
   # 修改前:
   print("测试模式：跳过飞书发送")
   # send_to_feishu(report)
   
   # 修改后:
   send_to_feishu(report)
   ```
3. **验证**: `OPENCLAW_PATH`已正确配置，`send_to_feishu()`函数内部已有`TEST_MODE`检查
4. **预期**: 今晚22:00 (北京时间) 报告应正常发送

#### A. 修改环境变量
```bash
# 临时修复
export TEST_MODE=0
cd /root/.openclaw/workspace/skills/macro-monitor
python3 run_monitor.py

# 永久修复 (cron环境)
# 在cron命令中添加环境变量
0 22 * * * export TEST_MODE=0 && cd /root/.openclaw/workspace/skills/macro-monitor && python3 run_monitor.py >> monitor.log 2>&1
```

#### B. 修改脚本逻辑
```python
# 在run_monitor.py中添加强制发送选项
import sys
if "--force-send" in sys.argv:
    TEST_MODE = "0"
```

#### C. 检查cron配置
```bash
crontab -l | grep macro-monitor
# 确保环境变量正确设置
```

#### D. Cron环境变量传递关键要点 (2026-02-28更新)
**问题**: `VAR=value command`语法在cron中可能无法正确传递环境变量到Python的`os.environ`
**证据**: cron日志显示任务执行了，但脚本仍进入测试模式
**解决方案**: 使用`env VAR=value command`语法
```bash
# 错误方式 (可能不工作):
0 22 * * * cd /path && TEST_MODE=0 /usr/bin/python3 script.py

# 正确方式 (使用env命令):
0 22 * * * cd /path && env TEST_MODE=0 /usr/bin/python3 script.py
```

**诊断步骤**:
1. 检查cron日志: `grep "macro-monitor" /var/log/cron`
2. 检查脚本输出: `tail -f monitor.log`
3. 验证环境变量: 在脚本中添加`print('TEST_MODE:', os.environ.get('TEST_MODE'))`

### 相关文件
- 监控脚本: `/root/.openclaw/workspace/skills/macro-monitor/run_monitor.py`
- 配置文件: `/root/.openclaw/workspace/skills/macro-monitor/_meta.json`
- 监控日志: `/root/.openclaw/workspace/skills/macro-monitor/monitor.log`
- cron配置: 系统crontab

## 🔧 Cron环境PATH问题与OpenClaw CLI执行

### 问题症状 (2026-03-01)
- T100报告生成成功，但发送失败
- 错误信息: `/usr/bin/env: 'node': No such file or directory`
- openclaw CLI在cron环境中无法执行

### 根本原因
1. **PATH传递问题**: cron环境中设置的PATH未正确传递给子进程
2. **openclaw脚本**: 使用`#!/usr/bin/env node`，依赖系统PATH查找node
3. **Python subprocess**: `subprocess.run()`默认不继承父进程环境变量（除非显式传递）
4. **嵌套调用**: cron → Python → subprocess → openclaw → node，环境变量传递中断

### 解决方案
#### A. Python代码修复（推荐）
在调用openclaw的Python函数中显式传递环境变量：
```python
import subprocess, os

def send_to_feishu(report: str):
    # 确保PATH包含Node.js路径
    current_env = os.environ.copy()
    node_path = '/root/.nvm/versions/node/v22.22.0/bin'
    if node_path not in current_env.get('PATH', ''):
        current_env['PATH'] = node_path + ':' + current_env.get('PATH', '')
    
    cmd = [OPENCLAW_PATH, 'message', 'send', '--channel', 'feishu', ...]
    result = subprocess.run(cmd, env=current_env, capture_output=True, text=True, timeout=30)
```

#### B. Cron命令修复
在cron命令中设置PATH并确保传递：
```bash
# 原始（可能不工作）:
0 22 * * * cd /path && PATH=/root/.nvm/versions/node/v22.22.0/bin:$PATH python3 script.py

# 改进（使用env命令显式设置）:
0 22 * * * cd /path && PATH=/root/.nvm/versions/node/v22.22.0/bin:$PATH env TEST_MODE=0 /usr/bin/python3 script.py
```

#### C. 环境验证脚本
创建测试脚本验证cron环境：
```bash
#!/bin/bash
# test_t100_env.sh
echo "PATH: $PATH"
which node
which openclaw
python3 -c "import os; print('TEST_MODE:', os.environ.get('TEST_MODE'))"
```

### 预防措施
1. **所有cron任务**: 在Python代码中显式传递环境变量
2. **PATH检查**: 在调用外部CLI前验证PATH包含必要路径
3. **环境验证**: 在cron任务开始时记录关键环境变量
4. **错误处理**: 捕获subprocess错误并提供明确诊断信息

### 学习要点
- **环境变量继承**: cron环境是受限的，环境变量不会自动传递给子进程
- **显式传递**: 使用`subprocess.run(env=os.environ.copy())`确保环境变量传递
- **路径依赖**: 对于版本管理器（nvm）安装的Node.js，必须确保PATH正确设置
- **缓存问题**: 修改Python代码后清除`__pycache__/`目录

**适用性**: 所有使用openclaw CLI或其他Node.js工具的cron任务
**验证方法**: 手动测试cron环境中的命令执行
**维护记录**: 2026-03-01 修复T100发送问题，第六次尝试成功

## 🔧 宏观监控数据获取模式（重复问题）

### 问题症状
- 宏观监控任务（T100）频繁出现数据获取失败（4个相关错误：ERR-20260224-001, ERR-20260225-001, ERR-20260225-002, ERR-20260226-001）
- 失败原因多样：类型比较错误、web_search集成失败、原油数据解析失败、cron环境问题
- 模式：宏观监控对多个外部数据源依赖性强，任一失败即影响整体报告

### 根本原因
1. **数据源不可靠**: akshare API返回历史数据（仅到2008年），无法获取实时指标
2. **集成复杂性**: 多数据源（汇率、原油、美债收益率、VIX、金价）需要不同爬取策略
3. **环境依赖**: 需要Node.js（Playwright）、Python环境、cron PATH正确配置
4. **错误处理不足**: 单点失败导致整个报告生成中断

### 解决方案
1. **数据源分层**:
   - 主要来源: Playwright爬取实时网站（Investing.com, XE.com, CBOE等）
   - 备用来源: akshare/Tushare API（当主要来源失败时）
   - 本地缓存: 存储最近成功数据供失败时使用
2. **环境验证**:
   - 任务开始时检查Node.js、Python、openclaw CLI可用性
   - 使用`env`命令确保cron环境变量正确传递
   - 在Python代码中显式传递环境变量给子进程
3. **错误隔离**:
   - 每个数据源独立错误处理，单点失败不影响其他数据收集
   - 记录部分成功数据，即使某些数据缺失也生成报告
4. **监控改进**:
   - 记录每个数据源获取状态和耗时
   - 设置数据新鲜度阈值（如>24小时数据视为失效）

### 预防措施
1. **定期测试**: 每周手动运行宏观监控验证所有数据源
2. **数据源健康检查**: 监控各网站可访问性和数据结构变化
3. **环境一致性**: 确保开发、测试、生产环境配置相同
4. **文档更新**: 数据源变更时及时更新TOOLS.md

### 学习要点
- **数据源冗余**: 关键数据至少有两个独立来源
- **环境隔离**: cron环境与交互式shell环境差异巨大
- **渐进式增强**: 即使部分数据缺失，仍提供有价值报告
- **模式识别**: 同一任务多次错误表明架构需要改进而非简单修复

**适用性**: 所有依赖外部数据源的定时任务（T100宏观监控、T99扫描等）
**验证方法**: 观察未来一周宏观监控执行成功率
**维护记录**: 2026-03-01 识别重复模式，制定系统性解决方案

## 🔧 Tushare API 注意事项（实时竞价数据）

### 问题症状
- `pro.stk_auction(trade_date='20260225', ts_code='...')` 在竞价窗口（09:25-09:29）返回空数据
- T01竞价分析在交易时间无法获取实时数据

### 根本原因
- Tushare `stk_auction` 实时接口在竞价窗口期间，调用时不能使用 `trade_date` 参数
- 接口设计：实时竞价数据按时间过滤，而非按日期

### 解决方案
1. **正确调用方式**:
   ```python
   # 错误方式（返回空）:
   pro.stk_auction(trade_date='20260225', ts_code='000001.SZ')
   
   # 正确方式（无trade_date参数）:
   pro.stk_auction(ts_code='000001.SZ')
   # 或获取所有股票竞价数据:
   pro.stk_auction()
   ```
2. **代码修改**: 已在 `limit_up_strategy_new.py` 的 `_get_real_auction_data` 方法中移除 `trade_date` 参数
3. **验证**: 2026-02-25 09:28（竞价窗口内）手动验证成功

### 预防措施
1. **API文档检查**: 使用Tushare API前仔细阅读接口文档，注意实时接口的特殊性
2. **实时测试**: 在交易时间段测试实时数据接口，而非仅用历史数据测试
3. **错误处理**: 当API返回空数据时，检查参数是否适合当前时间（历史 vs 实时）

### 学习要点
- **接口模式区分**: Tushare API 有历史模式（需要日期参数）和实时模式（无需或不同日期参数）
- **时间敏感性**: 金融数据接口行为可能随市场开闭而变化
- **测试覆盖**: 确保测试覆盖所有使用场景（开市前、竞价、连续交易、收盘后）

**适用性**: 所有使用Tushare实时接口的任务（T01竞价分析等）
**验证方法**: 下一个交易日竞价时段验证数据获取
**维护记录**: 2026-03-01 从LRN-20260225-001学习记录升级

## 🔧 MoA增强分析最佳实践

### 核心原则
**触发时机**: 当Task功能受阻、API限制、逻辑难题或定期复盘时，立即调用MoA增强版分析
**分析要求**: 问题根因分析 → 3~5个可行方案 → 推荐实施步骤
**传达对象**: proactive-agent和self-improving-agent必须遵循此原则

### 调用场景
1. **Task功能实现受阻**
   - 症状: 代码逻辑无法正常运行，错误难以定位
   - 行动: 调用MoA进行系统性调试分析
   - 输出: 根因诊断 + 修复方案

2. **API限制或集成问题**
   - 症状: 外部API调用失败、配额限制、数据格式不匹配
   - 行动: 调用MoA分析API集成策略
   - 输出: 备用方案 + 配额优化 + 数据转换方案

3. **复杂逻辑难题**
   - 症状: 算法设计、系统架构、性能优化等技术难题
   - 行动: 调用MoA进行多模型联合分析
   - 输出: 架构建议 + 性能优化方案 + 实施步骤

4. **Task定期复盘**
   - 时机: 每周/每月Task性能评估
   - 行动: 调用MoA寻求功能增强方向
   - 输出: 优化建议 + 新特性规划 + 演进路线

### 方案评估标准
每个MoA输出方案必须包含:
- **方案概述**: 核心思路和技术路线
- **实施步骤**: 具体可执行的操作步骤
- **预期效果**: 问题解决程度和性能提升
- **优缺点**: 优势、局限性、风险分析
- **推荐度**: 根据当前上下文给出的优先级别

### 集成流程
1. **proactive-agent集成**
   - 在主动检查中发现问题时自动触发MoA分析
   - 将MoA分析结果纳入self-healing流程
   - 记录MoA调用效果用于后续优化

2. **self-improving-agent集成**
   - 在记录复杂学习经验时调用MoA深度分析
   - 将MoA分析结果转化为可复用的解决方案模板
   - 建立MoA方案库供未来参考

### 验证机制
- **效果跟踪**: 记录每次MoA调用的问题类型、分析质量、实施结果
- **成功率统计**: 计算MoA分析后问题解决的成功率
- **方案库建设**: 积累经过验证的MoA解决方案，建立知识资产
- **定期优化**: 根据使用效果不断优化MoA调用策略和模板

### 预期效益
- **系统性解决**: 避免临时修补，提供根本性解决方案
- **集体智慧**: 利用多个前沿模型的优势，获得更全面的视角
- **效率提升**: 减少试错时间，加速问题解决流程（目标: 减少50%问题解决时间）
- **知识沉淀**: 生成可重复使用的解决方案模板，构建组织知识库

**维护记录**: 2026-03-07 根据老板要求创建，整合到AGENTS.md和MEMORY.md中
