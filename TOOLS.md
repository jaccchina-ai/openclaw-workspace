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

Add whatever helps you do your job. This is your cheat sheet.
