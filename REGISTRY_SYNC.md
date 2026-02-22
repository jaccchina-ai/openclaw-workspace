# Task Registry 同步系统

## 概述

`sync_registry.py` 脚本用于自动同步代码版本与Task Registry版本，确保Registry始终反映最新的任务状态。

## 文件结构

```
/root/.openclaw/workspace/
├── task_registry.json          # Task Registry (权威定义源)
├── sync_registry.py           # 主同步脚本
├── REGISTRY_SYNC.md          # 本文档
├── tasks/T01/config.yaml     # T01配置文件 (含version字段)
├── skills/a-share-short-decision/config.json      # T99配置文件
└── skills/macro-monitor/_meta.json                # T100配置文件
```

## 版本存储位置

| Task | 版本源文件 | 版本字段 |
|------|------------|----------|
| T01 | `tasks/T01/config.yaml` | `version: "1.0.0"` |
| T99 | `skills/a-share-short-decision/config.json` | `"version": "1.2.0"` |
| T100 | `skills/macro-monitor/_meta.json` | `"version": "1.0.2"` |

## 使用说明

### 1. 检查同步状态

```bash
# 检查所有Task
python3 sync_registry.py check

# 检查特定Task
python3 sync_registry.py check --task T01

# 详细输出
python3 sync_registry.py check --verbose
```

### 2. 执行同步

```bash
# 同步所有Task
python3 sync_registry.py sync

# 只同步T01
python3 sync_registry.py sync --task T01

# 模拟运行 (不实际修改文件)
python3 sync_registry.py sync --dry-run
```

### 3. 自动化选项

#### 方案A: Git钩子 (推荐)
```bash
# 创建pre-commit钩子
cp sync_registry.py .git/hooks/pre-commit-sync
chmod +x .git/hooks/pre-commit-sync

# 在.git/hooks/pre-commit中添加:
# python3 /path/to/sync_registry.py sync
```

#### 方案B: Cron定时任务
```bash
# 每天9点检查并同步
0 9 * * * cd /root/.openclaw/workspace && python3 sync_registry.py sync >> registry_sync.log 2>&1
```

#### 方案C: 手动触发
```bash
# 在任务更新脚本中调用
cd /root/.openclaw/workspace && python3 sync_registry.py sync --task T01
```

## 工作原理

1. **读取Registry**：加载 `task_registry.json`
2. **定位版本源**：根据每个Task的 `location` 和 `configuration_file` 字段
3. **提取版本**：支持JSON、YAML、Python文件中的版本字段
4. **比较版本**：Registry版本 vs 代码版本
5. **更新Registry**：如果不一致，更新版本和 `last_updated` 字段

## 配置文件要求

### T01 (YAML格式)
```yaml
# 版本信息
version: "1.0.0"
last_updated: "2026-02-22"
```

### T99/T100 (JSON格式)
```json
{
  "version": "1.2.0",
  "skill_name": "..."
}
```

## 错误处理

- **版本源缺失**：警告但不中断
- **文件格式错误**：跳过该Task
- **Registry文件不存在**：终止执行

## 维护原则

1. **代码为主**：代码版本变化时，同步更新Registry
2. **冲突解决**：如聊天内容与Registry冲突，以Registry为准
3. **版本语义**：遵循语义化版本 (major.minor.patch)

## 扩展支持

脚本支持以下版本源格式：
- JSON文件中的 `version` 字段
- YAML文件中的 `version` 字段  
- Python文件中的 `__version__` 变量
- 注释中的版本信息 (如 `# 版本: 1.0.0`)

如需支持新格式，修改 `_extract_version_from_file()` 方法。