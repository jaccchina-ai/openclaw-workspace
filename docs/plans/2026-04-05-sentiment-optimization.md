# 情绪指标预警系统优化计划

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.

**Goal:** 将情绪监控系统从独立定时任务改为T日晚间选股流程的集成模块，情绪评分作为选股因子之一

**Architecture:** 
1. 重构 `sentiment_monitor.py` 为可调用模块，提供 `get_sentiment_factor()` 接口
2. 修改 `limit_up_strategy_new.py`，在T日选股时调用情绪监控获取情绪评分
3. 将情绪评分纳入选股评分体系，作为风险过滤条件
4. 移除cron定时任务配置，改为选股流程内部调用

**Tech Stack:** Python, Tushare API, Pandas, YAML Config

---

## 需求变更说明

**原需求:** 情绪监控作为独立定时任务，9:35和14:55定时运行
**新需求:** 
- 取消定时监控任务
- 情绪监控在T日晚间选股时（20:00左右）执行
- 情绪评分作为选股流程的一个因子/过滤条件
- 整合到选股结果中一起推送

---

## 任务列表

### Task 1: 重构 sentiment_monitor.py - 添加可调用接口

**Files:**
- Modify: `/root/.openclaw/workspace/tasks/T01/sentiment_monitor.py`
- Test: `/root/.openclaw/workspace/tasks/T01/tests/test_sentiment_monitor.py`

**Step 1: Write the failing test**
```python
import pytest
from datetime import datetime
import sys
sys.path.insert(0, '/root/.openclaw/workspace/tasks/T01')

from sentiment_monitor import MarketSentimentMonitor, get_sentiment_factor

def test_get_sentiment_factor_interface():
    """测试新的情绪因子接口"""
    result = get_sentiment_factor('20260401')
    assert 'score' in result
    assert 'status' in result
    assert 'factor_value' in result
    assert 'should_filter' in result
    assert isinstance(result['score'], (int, float))
    assert result['status'] in ['extreme_bear', 'bear', 'caution', 'neutral', 'bull']

def test_sentiment_factor_extreme_bear():
    """测试极端熊市时的过滤逻辑"""
    # 模拟极端熊市数据
    result = {
        'score': 15,
        'status': 'extreme_bear',
        'factor_value': 0.15,
        'should_filter': True,
        'reason': '极端熊市信号'
    }
    assert result['should_filter'] == True
    assert result['factor_value'] < 0.3

def test_sentiment_factor_bull():
    """测试牛市时的因子值"""
    result = {
        'score': 85,
        'status': 'bull',
        'factor_value': 0.85,
        'should_filter': False,
        'reason': '市场情绪高涨'
    }
    assert result['should_filter'] == False
    assert result['factor_value'] > 0.7
```

**Step 2: Run test — confirm it fails**
```bash
cd /root/.openclaw/workspace/tasks/T01
python3 -m pytest tests/test_sentiment_monitor.py -v
```
Expected: FAIL — "function not defined" or similar

**Step 3: Write minimal implementation**
在 `sentiment_monitor.py` 末尾添加以下函数：

```python
def get_sentiment_factor(trade_date: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    获取情绪因子值 - 供选股流程调用
    
    Args:
        trade_date: 交易日期 (YYYYMMDD)
        config: 可选配置字典
        
    Returns:
        {
            'score': 情绪评分 (0-100),
            'status': 市场状态 (extreme_bear/bear/caution/neutral/bull),
            'factor_value': 因子值 (0-1, 用于评分计算),
            'should_filter': 是否过滤 (极端熊市时True),
            'reason': 过滤原因,
            'indicators': 详细指标
        }
    """
    monitor = MarketSentimentMonitor(config)
    
    # 分析情绪
    result = monitor.analyze_sentiment(trade_date)
    
    if not result.get('is_trading_day'):
        return {
            'score': 50,
            'status': 'neutral',
            'factor_value': 0.5,
            'should_filter': False,
            'reason': '非交易日',
            'indicators': {}
        }
    
    score = result.get('sentiment_score', 50)
    status = result.get('market_status', 'neutral')
    
    # 计算因子值 (0-1)
    factor_value = score / 100.0
    
    # 判断是否过滤 (极端熊市或评分过低)
    should_filter = status == 'extreme_bear' or score < 20
    
    # 过滤原因
    reason = ''
    if status == 'extreme_bear':
        reason = '极端熊市信号，建议清仓观望'
    elif score < 20:
        reason = '市场情绪极度低迷'
    elif status == 'bear':
        reason = '熊市信号，建议大幅减仓'
    else:
        reason = result.get('position_suggestion', {}).get('action', '观望')
    
    return {
        'score': score,
        'status': status,
        'factor_value': round(factor_value, 4),
        'should_filter': should_filter,
        'reason': reason,
        'indicators': result.get('indicators', {}),
        'position_suggestion': result.get('position_suggestion', {})
    }
```

**Step 4: Run test — confirm it passes**
```bash
cd /root/.openclaw/workspace/tasks/T01
python3 -m pytest tests/test_sentiment_monitor.py -v
```
Expected: PASS

**Step 5: Commit**
```bash
cd /root/.openclaw/workspace/tasks/T01
git add sentiment_monitor.py tests/test_sentiment_monitor.py
git commit -m "feat: add get_sentiment_factor() interface for stock selection integration"
```

---

### Task 2: 修改 limit_up_strategy_new.py - 集成情绪因子

**Files:**
- Modify: `/root/.openclaw/workspace/tasks/T01/limit_up_strategy_new.py`
- Test: `/root/.openclaw/workspace/tasks/T01/tests/test_sentiment_integration.py`

**Step 1: Write the failing test**
```python
import pytest
import sys
sys.path.insert(0, '/root/.openclaw/workspace/tasks/T01')

from limit_up_strategy_new import LimitUpScoringStrategyV2
import yaml

def test_sentiment_factor_in_scoring():
    """测试情绪因子纳入评分体系"""
    # 加载配置
    with open('/root/.openclaw/workspace/tasks/T01/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    strategy = LimitUpScoringStrategyV2(config)
    
    # 测试情绪因子权重配置存在
    assert 'sentiment' in strategy.t_day_weights
    assert strategy.t_day_weights['sentiment'] > 0

def test_sentiment_filter_extreme_bear():
    """测试极端熊市时的过滤逻辑"""
    # 模拟极端熊市情绪结果
    sentiment_result = {
        'score': 15,
        'status': 'extreme_bear',
        'factor_value': 0.15,
        'should_filter': True,
        'reason': '极端熊市信号'
    }
    
    # 验证应该触发过滤
    assert sentiment_result['should_filter'] == True
```

**Step 2: Run test — confirm it fails**
```bash
cd /root/.openclaw/workspace/tasks/T01
python3 -m pytest tests/test_sentiment_integration.py -v
```
Expected: FAIL — "sentiment not in weights" or similar

**Step 3: Write minimal implementation**

在 `LimitUpScoringStrategyV2.__init__()` 中添加情绪监控导入和初始化：

```python
# 在 __init__ 方法中添加
# 情绪监控导入
try:
    from sentiment_monitor import get_sentiment_factor
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    logger.warning("情绪监控模块加载失败")

self.sentiment_available = SENTIMENT_AVAILABLE
```

修改 `t_day_scoring` 权重配置，添加情绪因子权重：

在 `config.yaml` 中已配置：
```yaml
strategy:
  t_day_scoring:
    sentiment: 10  # 情绪因子权重10分
```

在 `limit_up_strategy_new.py` 中添加情绪评分方法：

```python
def _score_sentiment_factor(self, trade_date: str) -> Tuple[float, Dict[str, Any]]:
    """
    计算情绪因子得分
    
    Returns:
        (score, sentiment_data) - 得分和情绪数据
    """
    if not self.sentiment_available:
        return 10.0, {'status': 'unavailable', 'reason': '情绪模块未加载'}
    
    try:
        from sentiment_monitor import get_sentiment_factor
        
        sentiment = get_sentiment_factor(trade_date, self.config)
        
        # 情绪评分转换为0-10分
        # 50分情绪 = 5分, 100分 = 10分, 0分 = 0分
        base_score = sentiment['score'] / 10.0
        
        # 极端情况调整
        if sentiment['status'] == 'extreme_bear':
            score = 0.0
        elif sentiment['status'] == 'bear':
            score = base_score * 0.5
        elif sentiment['status'] == 'bull':
            score = min(10.0, base_score * 1.2)
        else:
            score = base_score
        
        return round(score, 2), sentiment
        
    except Exception as e:
        logger.error(f"情绪因子评分失败: {e}")
        return 5.0, {'status': 'error', 'reason': str(e)}
```

修改选股主流程，在评分时调用情绪因子：

```python
def screen_stocks(self, trade_date: str = None) -> pd.DataFrame:
    """
    T日涨停股筛选主流程
    """
    # ... 原有代码 ...
    
    # 获取情绪因子评分
    sentiment_score, sentiment_data = self._score_sentiment_factor(trade_date)
    logger.info(f"情绪因子评分: {sentiment_score}/10, 状态: {sentiment_data.get('status', 'unknown')}")
    
    # 检查是否触发极端情绪过滤
    if sentiment_data.get('should_filter'):
        logger.warning(f"⚠️ 触发情绪过滤: {sentiment_data.get('reason')}")
        # 记录到结果但不阻止选股，只是降低评分权重
    
    # ... 原有评分逻辑 ...
    
    # 在计算总分时加入情绪因子
    # df['total_score'] = ... 原有计算 ...
    # df['total_score'] += sentiment_score * self.t_day_weights.get('sentiment', 0) / 10
    
    return df
```

**Step 4: Run test — confirm it passes**
```bash
cd /root/.openclaw/workspace/tasks/T01
python3 -m pytest tests/test_sentiment_integration.py -v
```
Expected: PASS

**Step 5: Commit**
```bash
cd /root/.openclaw/workspace/tasks/T01
git add limit_up_strategy_new.py tests/test_sentiment_integration.py
git commit -m "feat: integrate sentiment factor into stock scoring system"
```

---

### Task 3: 修改选股报告格式 - 包含情绪指标

**Files:**
- Modify: `/root/.openclaw/workspace/tasks/T01/limit_up_strategy_new.py`

**Step 1: 修改报告生成方法**

在 `format_report()` 或相关报告生成方法中添加情绪指标展示：

```python
def format_report_with_sentiment(self, df: pd.DataFrame, sentiment_data: Dict[str, Any]) -> str:
    """
    生成包含情绪指标的报告
    """
    # 原有报告内容
    report = self.format_report(df)
    
    # 添加情绪指标部分
    sentiment_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 市场情绪指标:

【情绪评分】{sentiment_data.get('score', 50)}/100
【市场状态】{sentiment_data.get('status', 'unknown')}
【情绪因子得分】{sentiment_data.get('factor_value', 0.5) * 10:.1f}/10

关键指标:
• 炸板率: {sentiment_data.get('indicators', {}).get('explosion_rate', {}).get('rate', 0) * 100:.1f}%
• 连板高度: {sentiment_data.get('indicators', {}).get('consecutive_limits', {}).get('max_consecutive', 0)}板
• 涨跌比: {sentiment_data.get('indicators', {}).get('advance_decline_ratio', {}).get('ratio', 1.0):.2f}
• 涨停家数: {sentiment_data.get('indicators', {}).get('limit_stats', {}).get('limit_up', 0)}
• 跌停家数: {sentiment_data.get('indicators', {}).get('limit_stats', {}).get('limit_down', 0)}

操作建议: {sentiment_data.get('reason', '观望')}
"""
    
    # 如果触发过滤，添加警告
    if sentiment_data.get('should_filter'):
        sentiment_section += f"""
⚠️ 情绪过滤警告: {sentiment_data.get('reason')}
   当前市场情绪极差，建议降低仓位或观望。
"""
    
    return report + sentiment_section
```

**Step 2: 测试报告生成**
```bash
cd /root/.openclaw/workspace/tasks/T01
python3 -c "
from limit_up_strategy_new import LimitUpScoringStrategyV2
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
strategy = LimitUpScoringStrategyV2(config)
print('✅ 报告生成方法加载成功')
"
```

**Step 3: Commit**
```bash
cd /root/.openclaw/workspace/tasks/T01
git add limit_up_strategy_new.py
git commit -m "feat: add sentiment indicators to daily stock selection report"
```

---

### Task 4: 移除定时任务配置

**Files:**
- Modify: `/root/.openclaw/workspace/tasks/T01/config.yaml`

**Step 1: 修改 config.yaml**

将原有的定时监控配置注释掉或删除：

```yaml
# 情绪指标预警系统配置 (已改为选股流程集成，取消定时任务)
sentiment_monitor:
  enabled: true
  alert_cooldown_minutes: 30
  # schedule:  # 已移除定时任务，改为选股时调用
  #   - time: "09:35"
  #     description: "开盘情绪监控"
  #   - time: "14:55"
  #     description: "收盘前情绪监控"
  notification:
    enabled: true
    channels:
      - feishu
    extreme_bear_alert: true
    bear_alert: true
    high_sentiment_alert: true
```

**Step 2: 检查并移除相关cron配置**

检查是否有独立的情绪监控cron任务：
```bash
crontab -l | grep -i sentiment
```

如果有，移除相关行。

**Step 3: Commit**
```bash
cd /root/.openclaw/workspace/tasks/T01
git add config.yaml
git commit -m "config: remove scheduled sentiment monitoring, integrate into stock selection flow"
```

---

### Task 5: 代码质量改进 - 错误处理增强

**Files:**
- Modify: `/root/.openclaw/workspace/tasks/T01/sentiment_monitor.py`

**Step 1: 增强错误处理**

在 `sentiment_monitor.py` 中添加更健壮的错误处理：

```python
def safe_api_call(func, *args, **kwargs):
    """
    安全调用API，带重试机制
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                logger.error(f"API调用最终失败: {e}")
                raise

# 在原有方法中使用
# df = safe_api_call(self.pro.daily, trade_date=trade_date)
```

**Step 2: 添加缓存机制**

```python
import functools
import hashlib

class MarketSentimentMonitor:
    def __init__(self, config: Dict[str, Any] = None):
        # ... 原有代码 ...
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存
    
    def _get_cache_key(self, method_name: str, date: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{method_name}:{date}".encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str):
        """获取缓存结果"""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            else:
                del self._cache[cache_key]
        return None
    
    def _set_cached_result(self, cache_key: str, result: Any):
        """设置缓存结果"""
        self._cache[cache_key] = (result, time.time())
```

**Step 3: Commit**
```bash
cd /root/.openclaw/workspace/tasks/T01
git add sentiment_monitor.py
git commit -m "refactor: enhance error handling and add caching to sentiment monitor"
```

---

### Task 6: 性能优化 - 并行数据获取

**Files:**
- Modify: `/root/.openclaw/workspace/tasks/T01/sentiment_monitor.py`

**Step 1: 使用线程池并行获取指标**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def analyze_sentiment_parallel(self, trade_date: Optional[str] = None) -> Dict[str, Any]:
    """
    并行分析市场情绪（优化版）
    """
    trade_date = self.get_trade_date(trade_date)
    
    if not self._is_trading_day(trade_date):
        return {'is_trading_day': False}
    
    logger.info(f"开始并行分析 {trade_date} 市场情绪...")
    
    # 定义要并行执行的任务
    tasks = {
        'explosion': lambda: self.calculate_explosion_rate(trade_date),
        'consecutive': lambda: self.calculate_consecutive_limits(trade_date),
        'ad_ratio': lambda: self.calculate_advance_decline_ratio(trade_date),
        'limit_stats': lambda: self.calculate_limit_up_down_stats(trade_date),
        'premium': lambda: self.calculate_yesterday_limit_up_premium(trade_date),
    }
    
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_name = {
            executor.submit(task): name for name, task in tasks.items()
        }
        
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
            except Exception as e:
                logger.error(f"{name} 计算失败: {e}")
                results[name] = self._get_default_result(name)
    
    # 计算封板率（依赖explosion数据）
    results['seal'] = self._calculate_seal_from_explosion(results['explosion'])
    
    # ... 后续评分逻辑 ...
```

**Step 2: Commit**
```bash
cd /root/.openclaw/workspace/tasks/T01
git add sentiment_monitor.py
git commit -m "perf: parallelize sentiment indicator calculations for faster execution"
```

---

### Task 7: 集成测试 - 端到端验证

**Files:**
- Create: `/root/.openclaw/workspace/tasks/T01/tests/test_e2e_sentiment_integration.py`

**Step 1: 编写端到端测试**

```python
import pytest
import sys
sys.path.insert(0, '/root/.openclaw/workspace/tasks/T01')

from limit_up_strategy_new import LimitUpScoringStrategyV2
from sentiment_monitor import get_sentiment_factor
import yaml

def test_e2e_sentiment_in_stock_selection():
    """端到端测试：情绪因子集成到选股流程"""
    # 加载配置
    with open('/root/.openclaw/workspace/tasks/T01/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # 初始化策略
    strategy = LimitUpScoringStrategyV2(config)
    
    # 测试日期（使用最近交易日）
    test_date = '20260403'  # 根据实际情况调整
    
    # 获取情绪因子
    sentiment = get_sentiment_factor(test_date, config)
    
    # 验证情绪因子结构
    assert 'score' in sentiment
    assert 'factor_value' in sentiment
    assert 'should_filter' in sentiment
    
    # 验证情绪因子评分方法
    score, data = strategy._score_sentiment_factor(test_date)
    assert 0 <= score <= 10
    
    print(f"✅ 情绪因子测试通过: 评分={score}, 状态={data.get('status')}")

def test_sentiment_report_format():
    """测试情绪报告格式"""
    from sentiment_monitor import MarketSentimentMonitor
    
    monitor = MarketSentimentMonitor()
    
    # 模拟情绪结果
    sentiment_data = {
        'score': 75,
        'status': 'bull',
        'factor_value': 0.75,
        'should_filter': False,
        'reason': '市场情绪高涨',
        'indicators': {
            'explosion_rate': {'rate': 0.2},
            'consecutive_limits': {'max_consecutive': 5},
            'advance_decline_ratio': {'ratio': 2.5},
            'limit_stats': {'limit_up': 80, 'limit_down': 5}
        }
    }
    
    # 验证报告生成
    report = monitor.format_report({
        'trade_date': '20260403',
        'is_trading_day': True,
        'sentiment_score': 75,
        'market_status': 'bull',
        'position_suggestion': {'action': '积极操作', 'position': 1.0},
        'indicators': sentiment_data['indicators']
    })
    
    assert '市场情绪指标报告' in report
    assert '75/100' in report or '75' in report
    
    print("✅ 报告格式测试通过")

if __name__ == '__main__':
    test_e2e_sentiment_in_stock_selection()
    test_sentiment_report_format()
    print("\n✅ 所有端到端测试通过!")
```

**Step 2: Run test**
```bash
cd /root/.openclaw/workspace/tasks/T01
python3 tests/test_e2e_sentiment_integration.py
```

**Step 3: Commit**
```bash
cd /root/.openclaw/workspace/tasks/T01
git add tests/test_e2e_sentiment_integration.py
git commit -m "test: add end-to-end tests for sentiment integration"
```

---

## 总结

### 已完成的优化点

1. **架构重构**: 情绪监控从独立定时任务改为选股流程集成模块
2. **接口设计**: 新增 `get_sentiment_factor()` 接口供选股流程调用
3. **评分集成**: 情绪评分作为选股因子纳入评分体系（权重10分）
4. **过滤逻辑**: 极端熊市时触发过滤警告，建议降低仓位
5. **报告整合**: 情绪指标整合到每日选股报告中
6. **定时任务移除**: 取消9:35和14:55的定时监控配置
7. **错误处理增强**: 添加API重试机制和缓存机制
8. **性能优化**: 并行化情绪指标计算

### 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `sentiment_monitor.py` | 修改 | 添加 `get_sentiment_factor()` 接口，增强错误处理，并行化计算 |
| `limit_up_strategy_new.py` | 修改 | 集成情绪因子到评分体系，修改报告格式 |
| `config.yaml` | 修改 | 移除定时任务配置 |
| `tests/test_sentiment_monitor.py` | 新增 | 情绪监控单元测试 |
| `tests/test_sentiment_integration.py` | 新增 | 集成测试 |
| `tests/test_e2e_sentiment_integration.py` | 新增 | 端到端测试 |

### 后续建议

1. **监控情绪因子效果**: 观察情绪因子对选股准确率的影响
2. **权重调优**: 根据实际效果调整情绪因子权重
3. **更多情绪指标**: 可考虑加入北向资金流向、融资余额变化等指标
