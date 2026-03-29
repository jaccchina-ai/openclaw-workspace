# T01 Phase 3: 全系统进化

**版本**: 1.4.0  
**状态**: 开发中  
**最后更新**: 2026-03-30

---

## 概述

T01 Phase 3 是龙头战法选股系统的终极进化阶段，实现了完整的自动化策略进化闭环。本阶段包含四大核心模块：

1. **Alpha因子挖掘** - 通过遗传编程和神经网络发现新的预测因子
2. **深度归因分析** - 使用SHAP值和交易聚类理解策略表现
3. **自适应阈值** - 根据市场状态动态调整评分阈值
4. **全自动闭环** - 完整的自动化进化、部署和监控

---

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    T01 Phase 3 全系统进化                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Alpha Factor    │      │  Deep Attribution│            │
│  │  Mining          │      │  Analysis        │            │
│  │                  │      │                  │            │
│  │  • 遗传编程      │      │  • SHAP解释器   │            │
│  │  • 神经网络      │      │  • 交易聚类     │            │
│  │  • 横截面分析    │      │  • 归因报告     │            │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                         │                       │
│           ▼                         ▼                       │
│  ┌─────────────────────────────────────────┐               │
│  │         Adaptive Threshold Manager       │               │
│  │                                          │               │
│  │  • 波动率调节                            │               │
│  │  • 市场状态适应                          │               │
│  │  • 绩效反馈优化                          │               │
│  └────────┬────────────────────────────────┘               │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────┐               │
│  │         Auto Closed Loop Controller      │               │
│  │                                          │               │
│  │  • 智能触发进化                          │               │
│  │  • 安全部署回滚                          │               │
│  │  • 24/7性能守护                          │               │
│  └────────┬────────────────────────────────┘               │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────┐               │
│  │         T01 Core Strategy               │               │
│  │    (limit_up_strategy_new.py)           │               │
│  └─────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块说明

### 1. Alpha因子挖掘 (Alpha Factor Mining)

**目标**: 发现新的Alpha因子，扩展因子库

**核心模块**:
- `genetic_factor_evolution.py` - 遗传编程因子进化
- `neural_factor_extractor.py` - 神经网络因子提取
- `alpha_factor_discovery.py` - 因子发现主控

**功能**:
- 通过遗传算法进化数学表达式生成新因子
- 使用自编码器从原始数据中提取非线性因子
- 横截面分析识别跨市场有效的因子
- 自动IC值筛选和因子入库

**配置** (`config_phase3.yaml`):
```yaml
alpha_factor_mining:
  enabled: true
  genetic_params:
    population_size: 50
    generations: 30
    mutation_rate: 0.1
  neural_params:
    bottleneck_size: 10
    epochs: 100
```

---

### 2. 深度归因分析 (Deep Attribution Analysis)

**目标**: 理解交易成功/失败的根因

**核心模块**:
- `shap_explainer.py` - SHAP值解释器
- `trade_clustering.py` - 交易聚类分析
- `attribution_analyzer.py` - 归因分析主控

**功能**:
- 计算每个因子对交易结果的贡献度
- 聚类相似交易，识别赢/输模式
- 分解收益归因到各个因子
- 生成可解释的归因报告

**配置**:
```yaml
attribution_analysis:
  enabled: true
  shap_params:
    background_samples: 100
  clustering:
    algorithm: kmeans
    n_clusters: 5
```

---

### 3. 自适应阈值 (Adaptive Thresholds)

**目标**: 根据市场状态动态调整策略参数

**核心模块**:
- `market_regime_detector.py` - 市场状态检测
- `volatility_adjuster.py` - 波动率调节
- `adaptive_threshold_manager.py` - 阈值管理主控

**功能**:
- 实时检测牛市/熊市/震荡市
- 根据波动率调整评分阈值
- 基于历史绩效反馈优化参数
- 多目标优化平衡胜率/收益/回撤

**配置**:
```yaml
adaptive_thresholds:
  enabled: true
  volatility_params:
    high_vol_percentile: 70
    adjustment_factor: 0.2
  regime_params:
    bull_threshold: 1.05
    bear_threshold: 0.95
```

---

### 4. 全自动闭环 (Auto Closed Loop)

**目标**: 实现策略进化的完全自动化

**核心模块**:
- `evolution_trigger.py` - 进化触发器
- `safe_deploy_manager.py` - 安全部署管理
- `performance_guardian.py` - 性能守护者
- `auto_closed_loop.py` - 闭环控制主控

**功能**:
- 智能监控触发进化条件（胜率下降、IC衰减、回撤超限）
- 安全部署新参数，支持A/B测试
- 自动回滚失败的变更
- 24/7系统健康监控

**配置**:
```yaml
auto_closed_loop:
  enabled: true
  trigger_conditions:
    win_rate_drop:
      threshold: 0.40
    ic_decay:
      threshold: 0.03
  safe_deploy:
    ab_testing:
      enabled: true
      initial_percentage: 20
```

---

## 使用指南

### 启动Phase 3系统

```python
from phase3_controller import T01Phase3Controller

# 初始化控制器
controller = T01Phase3Controller('config.yaml')

# 检查状态
status = controller.get_status()
print(status)

# 执行健康检查
health = controller.health_check()
print(health)
```

### Alpha因子挖掘

```python
# 发现新因子
result = controller.discover_alpha_factors()
print(f"发现 {len(result['new_factors'])} 个新因子")
```

### 归因分析

```python
# 分析近期交易
report = controller.analyze_attribution()
print(report['factor_importance'])
```

### 自适应阈值

```python
# 更新阈值
adjustments = controller.update_adaptive_thresholds()
print(f"阈值调整: {adjustments}")
```

### 全自动进化

```python
# 执行完整进化流程
result = controller.run_auto_evolution()
print(result['report'])
```

---

## 文件结构

```
tasks/T01/
├── phase3_controller.py          # Phase 3主控制器
├── config_phase3.yaml            # Phase 3配置文件
│
├── Alpha因子挖掘模块
├── genetic_factor_evolution.py   # 遗传编程因子进化
├── neural_factor_extractor.py    # 神经网络因子提取
├── alpha_factor_discovery.py     # 因子发现主控
├── test_genetic_factor_evolution.py
├── test_neural_factor_extractor.py
├── test_alpha_factor_discovery.py
│
├── 归因分析模块
├── shap_explainer.py             # SHAP值解释器
├── trade_clustering.py           # 交易聚类
├── attribution_analyzer.py       # 归因分析主控
├── test_shap_explainer.py
├── test_trade_clustering.py
├── test_attribution_analyzer.py
│
├── 自适应阈值模块
├── market_regime_detector.py     # 市场状态检测
├── volatility_adjuster.py        # 波动率调节
├── adaptive_threshold_manager.py # 阈值管理主控
├── test_market_regime_detector.py
├── test_volatility_adjuster.py
├── test_adaptive_threshold_manager.py
│
└── 全自动闭环模块
    ├── evolution_trigger.py      # 进化触发器
    ├── safe_deploy_manager.py    # 安全部署管理
    ├── performance_guardian.py   # 性能守护者
    ├── auto_closed_loop.py       # 闭环控制主控
    ├── test_evolution_trigger.py
    ├── test_safe_deploy_manager.py
    ├── test_performance_guardian.py
    └── test_auto_closed_loop.py
```

---

## 测试

### 运行所有测试

```bash
cd /root/.openclaw/workspace/tasks/T01
python -m pytest test_*phase3*.py -v
```

### 运行单个模块测试

```bash
python -m pytest test_genetic_factor_evolution.py -v
python -m pytest test_shap_explainer.py -v
python -m pytest test_adaptive_threshold_manager.py -v
```

---

## 成功指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 新因子发现 | ≥5个 | IC > 0.05的新因子 |
| 归因解释率 | ≥90% | SHAP值解释的交易结果比例 |
| 胜率提升 | ≥5% | 自适应阈值带来的胜率提升 |
| 自动化程度 | 100% | 无需人工干预的完整进化周期 |

---

## 演进路线

### Phase 3A (第1-2天): Alpha因子挖掘
- [x] 遗传因子进化模块
- [x] 神经因子提取模块
- [x] 因子发现集成

### Phase 3B (第3-4天): 深度归因分析
- [x] SHAP解释器模块
- [x] 交易聚类模块
- [x] 归因分析集成

### Phase 3C (第5-6天): 自适应阈值
- [x] 市场状态检测器
- [x] 波动率调节器
- [x] 自适应阈值管理器

### Phase 3D (第7-8天): 全自动闭环
- [x] 进化触发器
- [x] 安全部署管理器
- [x] 性能守护者
- [x] 闭环控制器

### Phase 3E (第9-10天): 集成测试
- [ ] 配置更新
- [ ] 策略集成
- [ ] 端到端测试
- [ ] 文档完善

---

## 相关文档

- [设计文档](docs/plans/2026-03-30-t01-phase3-design.md)
- [实施计划](docs/plans/2026-03-30-t01-phase3-plan.md)
- [Phase 2完成报告](PHASE2_COMPLETION_REPORT.md)
- [进化计划](evolution_plan.json)

---

## 维护者

- **小虾米** - AI助手
- **董欣** - 项目负责人

---

*最后更新: 2026-03-30*
