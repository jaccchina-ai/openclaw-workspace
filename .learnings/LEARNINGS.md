# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config
**Statuses**: pending | in_progress | resolved | wont_fix | promoted | promoted_to_skill

## Status Definitions

| Status | Meaning |
|--------|---------|
| `pending` | Not yet addressed |
| `in_progress` | Actively being worked on |
| `resolved` | Issue fixed or knowledge integrated |
| `wont_fix` | Decided not to address (reason in Resolution) |
| `promoted` | Elevated to CLAUDE.md, AGENTS.md, or copilot-instructions.md |
| `promoted_to_skill` | Extracted as a reusable skill |

## Skill Extraction Fields

When a learning is promoted to a skill, add these fields:

```markdown
**Status**: promoted_to_skill
**Skill-Path**: skills/skill-name
```

Example:
```markdown
## [LRN-20250115-001] best_practice

**Logged**: 2025-01-15T10:00:00Z
**Priority**: high
**Status**: promoted_to_skill
**Skill-Path**: skills/docker-m1-fixes
**Area**: infra

### Summary
Docker build fails on Apple Silicon due to platform mismatch
...
```

## [LRN-20260225-001] best_practice

**Logged**: 2026-02-25T09:30:00Z
**Priority**: high
**Status**: promoted (to TOOLS.md Tushare API 注意事项)
**Resolution**: 已修复 - 修改了`limit_up_strategy_new.py`中的`_get_real_auction_data`方法，移除`trade_date`参数，使用`pro.stk_auction(ts_code=ts_code)`调用
**Area**: config

### Summary
Tushare stk_auction实时接口在竞价窗口(09:25-09:29)期间，调用时不能使用trade_date参数，否则返回空数据。

### Context
- 发现时间: 2026-02-25 09:28 (竞价窗口内测试)
- 问题: `pro.stk_auction(trade_date='20260225', ts_code='...')` 返回空数据
- 正确调用: `pro.stk_auction()` 或 `pro.stk_auction(ts_code='...')`
- 影响: T01竞价分析在交易时间无法获取实时数据

### Recommended Action
修改 `limit_up_strategy_new.py` 中的 `_get_real_auction_data` 方法，移除 `trade_date` 参数

### Metadata
- Related Files: tasks/T01/limit_up_strategy_new.py
- Tested: Yes (09:28手动验证)
- Impact: Critical for T01 real-time auction analysis

---

## [LRN-20260227-001] pattern

**Logged**: 2026-02-27T05:58:00Z
**Priority**: high
**Status**: promoted (to TOOLS.md 重复问题 #2 & AGENTS.md 系统内部执行失败模式)
**Area**: infra

### Summary
频繁出现"Exec failed (session-name-fragment, code 0)"系统消息，今日已出现27次。模式：短会话名称片段（如"plaid-lo", "delta-pr", "tide-clo", "crisp-ha", "quiet-la", "tidal-cl", "cool-wha", "kind-sag", "plaid-br", "glow-wha", "crisp-ze", "swift-ne", "crisp-da", "tidal-ce"等），退出码0。

### Context
- 首次发现: 2026-02-27（今日）
- 模式特征: 短会话名称片段（通常2个单词部分），退出码0
- 出现频率: 今日已出现27次
- 影响: 系统日志中出现大量失败消息，但核心功能正常
- 可能原因: OpenClaw内部会话管理、子进程清理、心跳检查等

### Recommended Action
1. 调查OpenClaw内部日志以确定根本原因
2. 检查系统负载和资源使用情况
3. 监控/tmp/clawdbot/目录（如存在）获取更多信息
4. 如频率>10次/天，需人工深入检查

### Metadata
- Related Files: TOOLS.md（已添加解决方案模式）
- Tested: No（根源未明）
- Impact: Low（不影响核心功能，但需要监控）

---


## [LRN-20260307-001] best_practice

**Logged**: 2026-03-07T15:18:00Z
**Priority**: critical
**Status**: promoted (to AGENTS.md MoA增强分析调用规则 & MEMORY.md 重要规则第5条)
**Area**: config

### Summary
老板明确要求：在Task功能实现受阻、API限制、逻辑难题时，或在Task功能定期复盘寻求功能增强方向时，必须调用MoA增强版的详细分析功能寻找解决方案。

### Context
- **触发条件**: 
  1. Task功能实现受阻（代码逻辑无法正常运行）
  2. API限制或集成问题（外部API调用失败、配额限制）
  3. 复杂逻辑难题（算法设计、系统架构、性能优化）
  4. Task定期复盘（寻求功能增强方向、优化策略）
- **分析要求**:
  1. 问题根因分析（识别根本原因）
  2. 提供3~5个可行解决方案（每个方案含优缺点）
  3. 推荐实施步骤
- **传达对象**: proactive-agent和self-improving-agent skills必须遵循此原则

### Recommended Action
1. 更新AGENTS.md和MEMORY.md包含详细调用规则
2. 确保proactive-agent在主动检查中发现问题时自动触发MoA分析
3. 确保self-improving-agent在记录复杂问题时调用MoA深度分析
4. 建立MoA调用验证机制，评估分析效果

### Metadata
- Related Files: AGENTS.md, MEMORY.md, TOOLS.md
- Tested: No (新指导原则)
- Impact: High (影响所有Task的问题解决流程)
- Source: user_feedback
- Tags: moa, problem_solving, best_practice
- Pattern-Key: enhance.moa_analysis
- Recurrence-Count: 1
- First-Seen: 2026-03-07
- Last-Seen: 2026-03-07

---
