# OpenClaw 版本控制与灾难恢复机制

## 🎯 目标
确保任何任务/策略版本可以**100%准确回退**到之前的稳定版本

## 📊 当前状态分析

### 已存在的版本控制元素
1. **Git仓库**：已初始化，但跟踪不完整
2. **Task Registry**：`task_registry.json` 记录任务版本
3. **配置版本化**：`tasks/T01/config.yaml` 有version字段
4. **同步脚本**：`sync_registry.py` 同步代码与Registry版本

### 缺失的灾难恢复机制
1. 完整的Git提交策略
2. 版本标签系统
3. 配置快照
4. 自动化恢复脚本
5. 恢复验证机制

## 🚀 灾难恢复系统设计

### 1. Git提交策略（严格执行）

#### 每次版本更新必须：
```bash
# 1. 提交所有更改
git add .
git commit -m "T01 v1.2.0: 新增竞价成交量/T日成交量比值指标"

# 2. 打上版本标签
git tag -a "T01-v1.2.0" -m "T01 version 1.2.0 - 新增舆情分析模块"

# 3. 推送到远程（如果有）
git push origin master --tags
```

#### 版本标签规范：
```
格式: <任务名>-v<主版本>.<次版本>.<修订版本>
示例: T01-v1.2.0, T100-v1.0.2, T99-v1.2.0

特殊情况:
- T01-v1.2.0-rollback-from-v1.3.0  # 回退版本
- T01-v1.2.0-hotfix-20260224      # 热修复版本
```

### 2. 配置快照系统

#### 快照内容：
```yaml
# snapshot-T01-v1.2.0.yaml
metadata:
  task_id: "T01"
  version: "1.2.0"
  created_at: "2026-02-24T05:10:00Z"
  git_commit: "a1b2c3d4e5f6"
  git_tag: "T01-v1.2.0"
  
files:
  - path: "tasks/T01/config.yaml"
    checksum: "sha256:abc123..."
  - path: "tasks/T01/limit_up_strategy_new.py"
    checksum: "sha256:def456..."
  - path: "task_registry.json"
    checksum: "sha256:ghi789..."
  
dependencies:
  python_packages:
    - "tushare==1.2.85"
    - "pandas==2.1.4"
  environment_variables:
    - "TAVILY_API_KEY"
    - "TUSHARE_TOKEN"
```

#### 自动生成快照脚本：
```python
# 每次版本更新时自动运行
python3 create_snapshot.py --task T01 --version 1.2.0
```

### 3. 灾难恢复流程

#### 场景：需要从 v1.3.0 回退到 v1.2.0

```bash
# 1. 验证目标版本存在
git tag -l | grep "T01-v1.2.0"

# 2. 检查快照完整性
python3 verify_snapshot.py --task T01 --version 1.2.0

# 3. 执行回退
python3 rollback_version.py --task T01 --from 1.3.0 --to 1.2.0

# 4. 验证回退成功
python3 verify_rollback.py --task T01 --expected 1.2.0
```

### 4. 回退脚本设计

```python
# rollback_version.py 核心逻辑
def rollback_task(task_id: str, from_version: str, to_version: str):
    # 1. 停止当前运行的任务
    stop_task(task_id)
    
    # 2. 从Git恢复代码
    git_checkout_tag(f"{task_id}-v{to_version}")
    
    # 3. 恢复配置文件
    restore_config_snapshot(task_id, to_version)
    
    # 4. 更新Task Registry
    update_registry_version(task_id, to_version)
    
    # 5. 恢复依赖环境
    restore_dependencies(task_id, to_version)
    
    # 6. 验证恢复完整性
    verify_integrity(task_id, to_version)
    
    # 7. 重新启动任务
    start_task(task_id)
    
    return {
        "success": True,
        "task_id": task_id,
        "from_version": from_version,
        "to_version": to_version,
        "rollback_time": datetime.now().isoformat()
    }
```

### 5. 验证机制

#### 四级验证确保100%准确：
```python
# 1. 文件完整性验证
verify_checksums(expected_snapshot)

# 2. 配置一致性验证  
verify_config_matches_version(expected_version)

# 3. 功能测试验证
run_smoke_test(task_id)

# 4. 生产环境验证
verify_production_readiness(task_id)
```

## 🛠️ 实施步骤

### 阶段1：基础版本控制（立即开始）
1. ✅ 创建`.gitignore`文件
2. ✅ 提交当前所有代码
3. ✅ 为现有版本打标签
4. ✅ 创建版本快照

### 阶段2：自动化工具（今日完成）
1. 🔄 创建快照生成脚本
2. 🔄 创建回退脚本
3. 🔄 创建验证脚本
4. 🔄 集成到Git钩子

### 阶段3：灾难恢复演练（本周内）
1. 📋 模拟版本回退场景
2. 📋 测试恢复流程
3. 📋 优化恢复时间
4. 📋 文档化恢复步骤

## 📋 .gitignore 模板

```gitignore
# 日志文件
*.log
logs/

# 数据文件
*.db
*.sqlite
*.csv
*.jsonl
data/

# 缓存文件
__pycache__/
*.pyc
.pytest_cache/

# 环境文件
.env
.env.local
.env.*.local

# IDE文件
.vscode/
.idea/
*.swp
*.swo

# 临时文件
*.tmp
temp/
tmp/

# 特定文件排除
# 但保留重要配置
!task_registry.json
!tasks/*/config.yaml
```

## 🔧 关键脚本实现

### 1. 创建版本快照
```bash
# 使用方式
python3 create_snapshot.py --task T01 --message "新增舆情分析模块"

# 自动完成：
# 1. 提交代码到Git
# 2. 打版本标签
# 3. 生成配置快照
# 4. 更新Task Registry
```

### 2. 灾难恢复
```bash
# 使用方式
python3 disaster_recovery.py --task T01 --target-version 1.2.0

# 自动完成：
# 1. 备份当前状态
# 2. 回退到目标版本
# 3. 验证恢复完整性
# 4. 生成恢复报告
```

## 🎯 老板的使用流程

### 正常版本更新：
```
1. 开发新功能
2. 运行: python3 create_snapshot.py --task T01
3. 系统自动: 提交+打标签+快照+Registry更新
4. 部署新版本
```

### 需要回退时：
```
1. 发现v1.3.0有问题
2. 运行: python3 disaster_recovery.py --task T01 --target-version 1.2.0
3. 系统自动: 备份→回退→验证→重启
4. 确认回退成功
5. 分析问题，准备修复版本
```

## 💡 高级特性（可选）

### 1. 版本时间机器
```bash
# 查看任意历史版本
python3 version_time_machine.py --task T01 --version 1.2.0 --action preview

# 对比版本差异
python3 version_diff.py --task T01 --v1 1.2.0 --v2 1.3.0
```

### 2. 自动回退触发器
```python
# 监控系统异常，自动触发回退
if error_rate > 0.1:
    auto_rollback_to_last_stable(task_id)
```

### 3. 版本健康检查
```bash
# 定期检查版本健康度
python3 version_health_check.py --task T01
```

## 📞 紧急联系流程

### 当需要人工干预时：
```
1. 系统检测到无法自动恢复
2. 发送警报到飞书/邮件
3. 提供恢复选项：
   - 自动回退到上一个稳定版本
   - 人工决策回退到指定版本
   - 保持现状，等待修复
4. 记录所有恢复操作
```

## ✅ 成功标准

1. **回退成功率**: 100%（经过验证）
2. **恢复时间**: < 5分钟（小型任务）
3. **数据完整性**: 100%保证
4. **操作可追溯**: 所有回退操作有完整日志
5. **人工干预率**: < 10%（大部分情况自动化）

---

*最后更新: 2026-02-24*  
*版本: v1.0.0*