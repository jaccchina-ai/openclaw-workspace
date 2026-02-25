# Errors

Command failures, exceptions, and integration issues.

**Categories**: command_failure | api_error | integration_failure | timeout | permission_denied
**Areas**: frontend | backend | infra | tests | docs | config | data | external_api
**Statuses**: pending | in_progress | resolved | wont_fix | promoted

## Status Definitions

| Status | Meaning |
|--------|---------|
| `pending` | Not yet investigated |
| `in_progress` | Being investigated or fixed |
| `resolved` | Issue fixed |
| `wont_fix` | Decided not to address (reason in Resolution) |
| `promoted` | Learning promoted to workspace files |


## [ERR-20260224-001] macro-monitor T99 data sharing failure

**Logged**: 2026-02-24T21:41:00Z
**Priority**: medium
**Status**: resolved
**Area**: data

### Summary
Failed to save T99 shared data due to type comparison error between NoneType and int

### Error
```
保存T99共享数据失败: '>' not supported between instances of 'NoneType' and 'int'
```

### Context
- Operation: Saving shared data for T99 (strategy review) integration
- File: skills/macro-monitor/run_monitor.py
- Environment: OpenClaw workspace, cron job execution

### Suggested Fix
Check data types before comparison, ensure all numeric values are properly initialized

### Metadata
- Reproducible: yes (occurs during daily macro-monitor execution)
- Related Files: skills/macro-monitor/run_monitor.py, skills/macro-monitor/data/
- See Also: None

### Resolution
- **Resolved**: 2026-02-24T22:11:00Z
- **Notes**: Fixed type comparison issue by using (value or default) pattern instead of .get(key, default) to handle None values properly

---
## [ERR-20260225-001] macro-monitor web_search integration failure

**Logged**: 2026-02-25T23:11:00Z
**Priority**: medium
**Status**: resolved
**Area**: integration

### Summary
macro-monitor skill fails to call web_search via openclaw CLI due to missing command in PATH

### Error
```
调用 web_search 异常: [Errno 2] No such file or directory: 'openclaw'
```

### Context
- Operation: Fallback data collection in macro-monitor (crude oil, US Treasury yield, etc.)
- File: skills/macro-monitor/run_monitor.py
- Environment: OpenClaw workspace, cron job execution
- Issue: Skill uses subprocess.call(["openclaw", "web_search", ...]) but openclaw CLI not in PATH

### Resolution
- **Resolved**: 2026-02-25T09:15:00Z
- **Commit/PR**: Playwright scraper integration
- **Notes**: Replaced failing web_search calls with Playwright scraper integration for all 5 macroeconomic data sources (exchange rate, crude oil, US Treasury yield, VIX, gold price). Also fixed openclaw CLI PATH issue by using absolute path `/root/.nvm/versions/node/v22.22.0/bin/openclaw` in scripts.

### Fix Details
1. **Playwright Integration**: Created `_call_playwright_scraper()` function to scrape data from original websites
2. **Data Source Replacements**:
   - USD/CNY exchange rate: XE.com (via Playwright stealth)
   - Crude oil price: Investing.com (via Playwright stealth)
   - US Treasury yield: Investing.com (via Playwright stealth)
   - VIX index: CBOE website (via Playwright stealth)
   - Gold price: gold.cnfol.com (via Playwright stealth)
3. **PATH Fix**: Updated OPENCLAW_PATH variable in run_monitor.py
4. **Testing**: All 5 data sources successfully tested (2026-02-25 09:15 UTC)

### Metadata
- Reproducible: was yes, now resolved
- Related Files: skills/macro-monitor/run_monitor.py, skills/playwright-scraper-skill/
- See Also: None

---

## Entry Format

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description of what failed

### Error
```
Actual error message or output
```

### Context
- Command/operation attempted
- Input or parameters used
- Environment details if relevant

### Suggested Fix
If identifiable, what might resolve this

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-20250110-001 (if recurring)

---

```

## ID Generation

Format: `ERR-YYYYMMDD-XXX`
- `ERR`: Error type
- `YYYYMMDD**: Current date
- `XXX**: Sequential number or random 3 chars (e.g., `001`, `A7B`)

## Resolution

When an error is fixed, update the entry:

1. Change `**Status**: pending` → `**Status**: resolved`
2. Add resolution block:

```markdown
### Resolution
- **Resolved**: ISO-8601 timestamp
- **Commit/PR**: abc123 or #42 (if applicable)
- **Notes**: Brief description of what was done
```

## Promotion

When an error reveals a broader issue that should be documented:

1. **Promote to TOOLS.md**: Tool-specific gotchas, configuration issues
2. **Promote to AGENTS.md**: Workflow improvements, automation opportunities
3. **Update entry**: Change `**Status**: pending` → `**Status**: promoted`

---

