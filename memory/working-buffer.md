# Working Buffer (Danger Zone Log)

**Status:** READY (not active)
**Context Threshold:** 60% (when to activate)
**Started:** 2026-03-25 (prepared)
**Last Entry:** —

---

## Purpose

This buffer captures EVERY exchange when context usage exceeds 60% (danger zone). It survives compaction when chat history is truncated.

## Protocol Rules

1. **At 60% context** (check via `session_status`):
   - CLEAR this buffer (keep header)
   - Change status to ACTIVE
   - Start logging EVERY exchange

2. **After compaction** (session starts with truncated history):
   - Read this buffer FIRST
   - Extract important context to SESSION-STATE.md
   - Present: "Recovered from working buffer. Last task was X. Continue?"

3. **Buffer format:**
   ```
   ## [timestamp] Human
   [their message]
   
   ## [timestamp] Agent (summary)
   [1-2 sentence summary of your response + key details]
   ```

## Activation Log

### 2026-03-25
- **Buffer created** as part of proactive-agent initialization
- **Status:** READY (awaiting 60% context threshold)
- **Associated with:** WAL Protocol in SESSION-STATE.md

---

## 📝 Buffer Entries (Active when status = ACTIVE)

*No entries yet — buffer is in ready state.*

---

## Recovery Notes

When recovering from buffer:
1. **Identify key context** from the last few exchanges
2. **Update SESSION-STATE.md** with recovered details
3. **Clear or archive** old buffer entries after recovery
4. **Reset buffer** for next danger zone period

---

*This file survives context loss. Use it to recover when you wake up confused.*