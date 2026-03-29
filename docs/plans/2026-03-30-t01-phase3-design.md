# T01 Phase 3: Full System Evolution Design

**Date**: 2026-03-30  
**Phase**: Phase 3 - Full System Evolution  
**Status**: Design Document

---

## Overview

This design document outlines the implementation of T01's Phase 3 evolution: **Full System Evolution**. This phase focuses on four critical areas:

1. **Alpha Factor Mining** - Discover new predictive factors through advanced ML techniques
2. **Deep Attribution Analysis** - Understand why trades succeed or fail
3. **Adaptive Thresholds** - Dynamic adjustment of scoring thresholds based on market conditions
4. **Full Auto-Closed Loop** - Complete automation of the strategy evolution cycle

---

## Current System State

### Already Implemented (Phase 1 & 2)
- ✅ Factor library with 50+ factors (factor_mining.py)
- ✅ IC monitoring with daily calculation (ic_monitor.py)
- ✅ Auto-evolution framework (auto_evolution.py)
- ✅ Performance tracking with 1.03% success threshold (performance_tracker.py)
- ✅ No-selection warning system (no_selection_warning.py)
- ✅ Machine learning integration (machine_learning.py)
- ✅ PCA orthogonalization framework (factor_orthogonalization.py)

### Configuration (config.yaml)
```yaml
- success_threshold: 1.03
- review_interval: 7 (weekly)
- no_selection_warning_threshold: 3
- correlation_threshold: 0.8
- machine_learning.enabled: true
- pca.enabled: false (test_mode)
```

---

## Phase 3 Requirements

### 1. Alpha Factor Mining (Alpha因子挖掘)

**Goal**: Discover new alpha factors beyond the existing 50+ factors using advanced techniques.

**Approaches**:
- **Genetic Programming**: Evolve mathematical expressions for new factors
- **Neural Network Feature Extraction**: Use autoencoders to discover non-linear factor combinations
- **Cross-Sectional Analysis**: Identify factors that work across different market regimes
- **Alternative Data Integration**: Incorporate news sentiment, sector rotation patterns

**Deliverables**:
- `alpha_factor_discovery.py` - Main module for alpha mining
- `genetic_factor_evolution.py` - Genetic programming for factor evolution
- `neural_factor_extractor.py` - Neural network-based factor discovery
- Integration with existing factor_mining.py

### 2. Deep Attribution Analysis (深度归因分析)

**Goal**: Understand the root causes of winning and losing trades to improve strategy.

**Approaches**:
- **SHAP Values**: Explain which factors contributed most to each prediction
- **Trade Clustering**: Group similar trades to identify patterns
- **Win/Loss Decomposition**: Break down returns by factor contributions
- **Market Regime Attribution**: Analyze performance across different market conditions

**Deliverables**:
- `attribution_analyzer.py` - Main attribution analysis module
- `shap_explainer.py` - SHAP value calculation for T01
- `trade_clustering.py` - Cluster trades by characteristics
- `regime_analyzer.py` - Market regime detection and analysis

### 3. Adaptive Thresholds (自适应阈值)

**Goal**: Dynamically adjust scoring thresholds based on market conditions.

**Approaches**:
- **Market Volatility Adjustment**: Lower thresholds in high volatility, raise in low volatility
- **Regime-Based Thresholds**: Different thresholds for bull/bear/sideways markets
- **Historical Performance Feedback**: Adjust based on recent win/loss patterns
- **Multi-Objective Optimization**: Balance win rate, profit factor, and drawdown

**Deliverables**:
- `adaptive_threshold_manager.py` - Dynamic threshold adjustment
- `market_regime_detector.py` - Real-time market regime classification
- `volatility_adjuster.py` - Volatility-based threshold scaling
- Integration with limit_up_strategy_new.py

### 4. Full Auto-Closed Loop (全自动闭环)

**Goal**: Complete automation of the entire strategy evolution cycle without human intervention.

**Approaches**:
- **Auto-Trigger Evolution**: Automatically trigger evolution when performance degrades
- **Auto-Deploy Changes**: Safely deploy optimized parameters to production
- **Rollback Mechanism**: Automatically rollback if new parameters perform worse
- **Continuous Monitoring**: 24/7 monitoring of all system components

**Deliverables**:
- `auto_closed_loop.py` - Main closed-loop controller
- `safe_deploy_manager.py` - Safe deployment with rollback capability
- `performance_guardian.py` - Continuous performance monitoring
- `evolution_trigger.py` - Intelligent evolution triggering logic

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    T01 Full Evolution System                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Alpha Factor    │      │  Deep Attribution│            │
│  │  Mining          │      │  Analysis        │            │
│  │                  │      │                  │            │
│  │  - Genetic Prog  │      │  - SHAP Values   │            │
│  │  - Neural Extract│      │  - Trade Cluster │            │
│  │  - Cross-Section │      │  - Win/Loss Decomp│           │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                         │                       │
│           ▼                         ▼                       │
│  ┌─────────────────────────────────────────┐               │
│  │         Adaptive Threshold Manager       │               │
│  │                                          │               │
│  │  - Volatility Adjustment                 │               │
│  │  - Regime-Based Thresholds               │               │
│  │  - Historical Feedback                   │               │
│  └────────┬────────────────────────────────┘               │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────┐               │
│  │         Auto Closed Loop Controller      │               │
│  │                                          │               │
│  │  - Auto-Trigger Evolution                │               │
│  │  - Safe Deploy with Rollback             │               │
│  │  - Continuous Monitoring                 │               │
│  └────────┬────────────────────────────────┘               │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────────────────────────────┐               │
│  │         Existing T01 Strategy           │               │
│  │         (limit_up_strategy_new.py)      │               │
│  └─────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 3A: Alpha Factor Mining (Days 1-2)
1. Implement genetic programming factor evolution
2. Implement neural feature extraction
3. Integrate with existing factor library
4. Write tests for all new modules

### Phase 3B: Deep Attribution Analysis (Days 3-4)
1. Implement SHAP value explainer
2. Implement trade clustering
3. Implement win/loss decomposition
4. Create attribution reports

### Phase 3C: Adaptive Thresholds (Days 5-6)
1. Implement market regime detector
2. Implement volatility adjuster
3. Create adaptive threshold manager
4. Integrate with strategy scoring

### Phase 3D: Full Auto-Closed Loop (Days 7-8)
1. Implement evolution trigger logic
2. Create safe deploy manager
3. Implement rollback mechanism
4. Create performance guardian

### Phase 3E: Integration & Testing (Days 9-10)
1. Integrate all modules
2. End-to-end testing
3. Performance validation
4. Documentation

---

## Success Criteria

1. **Alpha Factor Mining**: Discover at least 5 new factors with IC > 0.05
2. **Deep Attribution**: Explain 90%+ of trade outcomes with SHAP values
3. **Adaptive Thresholds**: Improve win rate by 5%+ in backtests
4. **Auto-Closed Loop**: Complete evolution cycle without human intervention

---

## Files to Create/Modify

### New Files
- `alpha_factor_discovery.py`
- `genetic_factor_evolution.py`
- `neural_factor_extractor.py`
- `attribution_analyzer.py`
- `shap_explainer.py`
- `trade_clustering.py`
- `regime_analyzer.py`
- `adaptive_threshold_manager.py`
- `market_regime_detector.py`
- `volatility_adjuster.py`
- `auto_closed_loop.py`
- `safe_deploy_manager.py`
- `performance_guardian.py`
- `evolution_trigger.py`

### Modified Files
- `config.yaml` - Add Phase 3 configuration
- `limit_up_strategy_new.py` - Integrate adaptive thresholds
- `auto_evolution.py` - Integrate closed-loop logic

---

## Testing Strategy

1. **Unit Tests**: Each module has comprehensive unit tests
2. **Integration Tests**: Test module interactions
3. **Backtest Validation**: Validate on historical data
4. **Paper Trading**: Test with simulated trades

---

*Design approved for implementation*
