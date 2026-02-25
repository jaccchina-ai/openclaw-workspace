# ONBOARDING.md — Getting to Know You

> This file tracks onboarding progress. Don't delete it — the agent uses it to resume.

## Status

- **State:** complete
- **Progress:** 12/12 core questions
- **Mode:** interactive
- **Last Updated:** 2026-03-25 (completed)

---

## How This Works

When your agent sees this file with `state: not_started` or `in_progress`, it knows to help you complete setup. You can:

1. **Interactive mode** — Answer questions in one session (~10 min)
2. **Drip mode** — Agent asks 1-2 questions naturally over several days
3. **Skip for now** — Agent works immediately, learns from conversation

Say "let's do onboarding" to start, or "ask me later" to drip.

---

## Core Questions

Answer these to help your agent understand you. Leave blank to skip.

### 1. Identity
**What should I call you?**
> 老板 (从现有上下文已知)

**What's your timezone?**
> GMT+8 (中国时区) (从现有上下文已知)

### 2. Communication
**How do you prefer I communicate? (direct/detailed/brief/casual)**
> 直接、务实、避免无意义的客套话 (从USER.md推断)

**Any pet peeves I should avoid?**
> 1. 冗长、空洞、没有可执行结论的解释
> 2. 在信息不充分时编造或假设数据（不确定请明确说明）
> 3. 重复确认已明确的事项，降低效率
> 4. 混淆不同任务（如选股系统与客户跟进）的上下文
> 5. 未经授权主动执行高风险操作（如发送邮件、下单、修改数据）
> 6. 提供与我当前业务无关的泛泛建议

### 3. Goals
**What's your primary goal right now? (1-3 sentences)**
> 开发并优化金融投资策略系统，提升A股短线交易决策能力。构建完整的、自动化的金融投资决策支持系统。

**What does "winning" look like for you in 1 year?**
> 构建一个完整的、自动化的金融投资决策支持系统，包括每日自动生成股票推荐、宏观数据实时监控、策略持续优化，所有任务通过Registry统一管理，系统稳定运行无需人工干预。

**What does ideal life look/feel like when you've succeeded?**
> 1. 时间自主，不被琐事占用精力
> 2. 专注于战略决策、产品创新和长期价值创造
> 3. 业务稳定增长，有可靠的自动化系统支持日常运营
> 4. 能与家人保持高质量陪伴，同时持续学习和探索新技术
> 5. 每天清楚知道最重要的事情是什么，并高效完成
> 6. 内心从容、有掌控感，而不是被事务追着走

### 4. Work Style
**When are you most productive? (morning/afternoon/evening)**
> - 上午 9:00-12:00：适合深度思考、战略决策、复杂任务
> - 下午 14:00-17:00：适合沟通协调、执行类工作
> - 晚上仅处理紧急或创意类事项，不安排高强度任务

**Do you prefer async communication or real-time?**
> 优先使用异步沟通（如汇总消息、待办清单、定时提醒），以减少打扰并提高专注度。
> 仅在以下情况使用实时沟通：
> 1. 紧急事项或高优先级风险
> 2. 截止时间临近
> 3. 需要立即决策
> 4. 我明确要求实时响应

### 5. Context
**What are you currently working on? (projects, job, etc.)**
> **当前项目:**
> - T01龙头战法选股系统
> - T99复盘任务（策略复盘与优化）
> - T100宏观监控独立报告（每日宏观数据监控）
> - 金融投资API文档库整理（Tushare Pro、StockAPI等）
> 
> **未来规划增加:**
> 1. 客户跟进与业务拓展自动化
> 2. AI驱动的任务管理与工作流程优化
> 3. 多应用场景任务系统（如选股系统、客户跟进等）
> 4. 信息整理与知识库建设
> 5. 提升决策效率与自动化程度

**Who are the key people in your work/life I should know about?**
> **关键关系:**
> - 客户与潜在客户
> - 合作伙伴与供应商
> - 内部团队成员
> - 不同任务场景对应的联系人
> 
> **主要沟通渠道:**
> - 当前：飞书、钉钉、QQ、邮件等
> - 未来增加：Telegram、WhatsApp等

### 6. Agent Preferences
**What kind of personality should your agent have?**
> **核心风格:** 接地气、有点皮、但办事靠谱的小虾米风格
> 
> **补充特质:**
> 1. 专业、可靠
> 2. 主动但不过度打扰
> 3. 以可执行建议为主
> 4. 不胡编，不夸张

---

## Completion Log

As questions are answered, the agent logs them here:

| # | Question | Answered | Source |
|---|----------|----------|--------|
| 1 | Name | ✅ | USER.md (已有上下文) |
| 2 | Timezone | ✅ | USER.md (已有上下文) |
| 3 | Communication style | ✅ | USER.md (推断) |
| 4 | Pet peeves | ✅ | 当前对话 |
| 5 | Primary goal | ✅ | USER.md (扩展) |
| 6 | 1-year vision | ✅ | USER.md (扩展) |
| 7 | Ideal life | ✅ | 当前对话 |
| 8 | Productivity time | ✅ | 当前对话 |
| 9 | Async vs real-time | ✅ | 当前对话 |
| 10 | Current projects | ✅ | 当前对话 (补充) |
| 11 | Key people | ✅ | 当前对话 (补充) |
| 12 | Agent personality | ✅ | 当前对话 (补充) |

---

## After Onboarding

Once complete (or enough answers gathered), the agent will:
1. Update USER.md with your context
2. Update SOUL.md with personality preferences
3. Set status to `complete`
4. Start proactive mode

You can always update answers by editing this file or telling your agent.
