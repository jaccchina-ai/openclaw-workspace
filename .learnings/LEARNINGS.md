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
**Status**: resolved
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

