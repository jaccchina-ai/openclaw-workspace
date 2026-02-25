# SESSION-STATE.md - Active Working Memory

> Write-Ahead Logging (WAL) Protocol: Capture critical details BEFORE responding.
> Updated: 2026-03-25 (初始化)

## 🎯 Current Focus

**激活 proactive-agent 技能**
- 选择选项1：快速初始化
- 已复制模板文件到工作空间
- 正在进行引导流程设置

## 📋 WAL Protocol Status

**状态:** 已激活
**上次更新:** 2026-03-25 (初始化)
**协议版本:** v3.1.0 (proactive-agent)

### WAL 触发规则

**检测并立即记录:**
- ✏️ **Corrections** — "It's X, not Y" / "Actually..." / "No, I meant..."
- 📍 **Proper nouns** — Names, places, companies, products
- 🎨 **Preferences** — Colors, styles, approaches, "I like/don't like"
- 📋 **Decisions** — "Let's do X" / "Go with Y" / "Use Z"
- 📝 **Draft changes** — Edits to something we're working on
- 🔢 **Specific values** — Numbers, dates, IDs, URLs

**工作流:**
1. 检测到上述任何内容 → **STOP**（不要开始回复）
2. **WRITE** → 更新此文件
3. **THEN** → 回复人类

## 🔍 Self-Improvement Protocol (Integrated)

**状态:** 已激活
**集成时间:** 2026-03-25
**核心原则:** 避免三个陷阱（重复记录、过度记录、维护负担）

### 分层记录系统（避免重复）
| 层级 | 记录位置 | 内容 | 升级条件 |
|------|----------|------|----------|
| **瞬时** | `SESSION-STATE.md` (WAL) | 对话中的即时修正、决策 | 立即 |
| **近期** | `memory/YYYY-MM-DD.md` | 今日重要事件、学习 | 24小时 |
| **学习** | `.learnings/LEARNINGS.md` | **仅升级**：重复或重要到需要永久记住 | 经过验证 |
| **永久** | `AGENTS.md/SOUL.md/TOOLS.md` | 通用原则、工作流、工具陷阱 | 经过审查 |

### 优先级过滤器（避免过度记录）
**记录到 .learnings/ 当：**
- ✅ **修正**：老板明确纠正（"不，那是错的"）
- ✅ **错误**：命令/API失败，影响任务完成
- ✅ **知识缺口**：我的知识过时/错误
- ✅ **重复模式**：同一问题第三次出现
- ✅ **重要决策**：影响系统架构

**不记录到 .learnings/ 当：**
- ❌ **偏好**："我喜欢蓝色"（记录到 SESSION-STATE.md）
- ❌ **一次性错误**：拼写错误、小格式问题
- ❌ **信息确认**："是的，正确"、"好的"

### 操作流程
1. **检测事件** → 应用优先级过滤器
2. **重要事件** → 记录到 SESSION-STATE.md (WAL)
3. **符合 .learnings 标准** → 追加到相应文件
4. **每日心跳** → 快速扫描新条目
5. **每周日审查** → 升级合格条目，清理旧条目

### 自动化升级标准
- **升级到 AGENTS.md**：自动化可解决的重现问题（≥3次），工作流改进（节省≥5分钟/次）
- **升级到 SOUL.md**：行为原则改变，沟通风格调整，核心决策逻辑
- **升级到 TOOLS.md**：工具使用陷阱，API集成问题，配置难点

## 🧩 Context Fragments

### 来自当前对话
- **2026-03-25:** 老板选择选项1（快速初始化proactive-agent技能）
- **ONBOARDING状态:** 已更新为 in_progress，预填写了4/12个问题
- **2026-03-25:** 老板要求"完成引导流程的剩余问题"
- **忌讳清单 (Pet peeves):** 
  1. 冗长、空洞、没有可执行结论的解释
  2. 在信息不充分时编造或假设数据（不确定请明确说明）
  3. 重复确认已明确的事项，降低效率
  4. 混淆不同任务（如选股系统与客户跟进）的上下文
  5. 未经授权主动执行高风险操作（如发送邮件、下单、修改数据）
  6. 提供与我当前业务无关的泛泛建议
- **理想状态 (Ideal life):**
  1. 时间自主，不被琐事占用精力
  2. 专注于战略决策、产品创新和长期价值创造
  3. 业务稳定增长，有可靠的自动化系统支持日常运营
  4. 能与家人保持高质量陪伴，同时持续学习和探索新技术
  5. 每天清楚知道最重要的事情是什么，并高效完成
  6. 内心从容、有掌控感，而不是被事务追着走
- **工作效率时段:**
  - 上午 9:00-12:00：适合深度思考、战略决策、复杂任务
  - 下午 14:00-17:00：适合沟通协调、执行类工作
  - 晚上仅处理紧急或创意类事项，不安排高强度任务
- **沟通偏好:**
  - 优先使用异步沟通（如汇总消息、待办清单、定时提醒），以减少打扰并提高专注度
  - 仅在以下情况使用实时沟通：
    1. 紧急事项或高优先级风险
    2. 截止时间临近
    3. 需要立即决策
    4. 老板明确要求实时响应
- **ONBOARDING决策:** 老板要求"逐一提问"确认剩余3个问题
- **工作项目补充:**
  - 当前项目：T01龙头战法、T99复盘、T100宏观监控、API文档库
  - 未来增加项目：
    1. 客户跟进与业务拓展自动化
    2. AI驱动的任务管理与工作流程优化
    3. 多应用场景任务系统（如选股系统、客户跟进等）
    4. 信息整理与知识库建设
    5. 提升决策效率与自动化程度
- **关键关系补充:**
  - 客户与潜在客户
  - 合作伙伴与供应商
  - 内部团队成员
  - 不同任务场景对应的联系人
  - 主要沟通渠道：飞书、钉钉、QQ、邮件等
  - 未来增加：Telegram、WhatsApp等
- **ONBOARDING状态:** ✅ 已完成 (2026-03-25)
- **AI助手性格补充:**
  1. 专业、可靠
  2. 主动但不过度打扰
  3. 以可执行建议为主
  4. 不胡编，不夸张
- **Proactive-Agent 工作范围定义 (2026-03-25):**
  - **Scope (做什么):**
    1. 主动识别：待办、风险、异常、机会点
    2. 主动建议：下一步行动、模板、检查清单
    3. 主动提醒：按规则提醒（每日/每周/触发条件）
  - **Out of Scope (不做什么):**
    1. 不生成虚构数据；不在不确定时装作确定
    2. 不跨任务混淆（不同 Task Registry 的任务要隔离）

### Proactive-Agent 配置
- **ONBOARDING.md:** 已复制，状态为 not_started
- **HEARTBEAT.md:** 已替换为完整检查清单
- **AGENTS.md:** 已合并更新，添加了Proactive Work和Blockers部分
- **SOUL.md:** 已更新，添加proactive原则
- **USER.md:** 已扩展，添加更多上下文
- **SESSION-STATE.md:** 本文件，WAL协议核心
- **working-buffer.md:** 待创建（当上下文>60%时激活）

## 📝 Open Tasks / Decisions

### 立即执行
- [x] 检查ONBOARDING.md状态，开始引导流程
- [x] 创建memory/working-buffer.md（准备危险区日志）
- [x] 创建notes/areas/proactive-ideas.md
- [x] 配置基础Cron任务用于自主检查
  - [x] 配置T01 isolated agentTurn cron（每日20:00评分 + 09:25竞价）
  - [x] 配置T99 isolated agentTurn cron（首次运行2026-03-14 15:00）
  - [x] 配置T100 isolated agentTurn cron（每日22:00宏观监控）
  - [x] 配置每周反向提问cron（每周一09:00北京）
  - [x] 配置健康监控cron（每日08:00北京）

### 待确认
- [ ] 确认WAL协议触发机制工作正常
- [ ] 测试工作缓冲区协议（当上下文>60%时）
- [ ] 修复T01飞书推送功能（openclaw命令在systemd环境中可能无法访问）

## 🔄 Recurring Patterns

### 常见任务类型
1. **金融投资系统开发** (T01, T99, T100)
2. **文档整理与优化**
3. **API集成与测试**
4. **系统监控与维护**

### 老板偏好
- 直接、务实的沟通方式
- 重视系统化和自动化
- 功能实现优先于界面美化
- 文档记录很重要

## 🧠 Memory Anchors

### 关键系统位置
- **Task Registry:** `/root/.openclaw/workspace/task_registry.json`
- **T01 龙头战法:** `tasks/T01/`
- **T99 复盘任务:** `skills/a-share-short-decision/`
- **T100 宏观监控:** `skills/macro-monitor/`
- **API文档库:** `reference/apis/`

### 重要凭证位置
- **Tushare Pro token:** 存储在环境变量中
- **StockAPI token:** 存储在环境变量中
- **Tavily API:** 存储在环境变量中

---

## WAL 协议日志

### 2026-03-25
- **初始化:** 创建SESSION-STATE.md文件，激活WAL协议
- **决策:** 老板选择选项1（快速初始化proactive-agent技能）
- **操作:** 复制ONBOARDING.md、HEARTBEAT.md等模板文件
- **更新:** 合并AGENTS.md、更新SOUL.md、扩展USER.md
- **Cron配置 (2026-03-25):** 部署5个isolated agentTurn cron任务
  1. **T01 Daily Limit-up Scoring** (ID: aa652ab1-ab3c-459b-8a19-0545ab8ff05f) - 每日20:00北京 (UTC 12:00)
  2. **T01 Next-day Auction Analysis** (ID: 062ab359-104b-4fee-b4ee-d659fc93ae93) - 每日09:25北京 (UTC 01:25)
  3. **T99 Strategy Review** (ID: d42a187c-6066-43d9-8e27-67ef99e64332) - 首次运行2026-03-14 15:00北京 (UTC 07:00)
  4. **T100 Macro Monitor Daily** (ID: bf83cba4-8b68-4fc3-837c-1319fa538165) - 每日22:00北京 (UTC 14:00)
  5. **Weekly Reverse Prompting** (ID: c1f765a3-9c52-4cea-ab16-f7a6842228e1) - 每周一09:00北京 (UTC 01:00)
  6. **Daily System Health Check** (ID: 2fb51829-e855-4fea-9c6c-b9f5fbb23140) - 每日08:00北京 (UTC 00:00)
- **2026-03-25 后续:** 老板询问self-improving-agent技能是否已真正运行
- **2026-03-25 决策:** 老板同意开始实施self-improving-agent集成，要求避免三个陷阱：
  1. 同一事件重复记录多次
  2. 过度记录琐碎内容
  3. 让日记的维护变成负担而不帮助
- **集成方案:** 分层记录系统 + 优先级过滤器 + 自动化升级流程
- **实施完成 (2026-03-25):** 
  1. 创建 `.learnings/` 目录和模板文件
  2. 更新 `HEARTBEAT.md` 添加自我改进审查部分
  3. 部署每周审查Cron: `Weekly Self-Improvement Review` (ID: a3c46c1c-9ae8-4e9b-abde-d5bbb5ef910a) - 每周日22:00北京 (UTC 14:00)
  4. 集成验证: 避免三个陷阱的机制已就位

---

*保持此文件更新。这是你抵御上下文丢失的主要防线。*