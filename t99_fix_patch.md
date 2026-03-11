# T99修复补丁：交易日历本地缓存集成

## 问题
T99扫描连续失败≥7天，核心原因为Tushare `trade_cal` API在非交易日挂起。

## 解决方案
使用本地交易日历文件替代`trade_cal` API调用，完全避免API挂起问题。

## 修改文件
`/root/.openclaw/workspace/skills/a-share-short-decision/tools/market_data.py`

## 修改内容

### 1. 添加交易日历加载函数（在文件顶部附近）
```python
import json
import os

def _load_trading_calendar():
    """加载本地交易日历文件"""
    calendar_path = "/root/.openclaw/workspace/trading_calendar.json"
    try:
        with open(calendar_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] 加载交易日历失败: {e}")
        return None

def _is_trading_day_local(date_str):
    """使用本地日历检查是否为交易日"""
    calendar = _load_trading_calendar()
    if not calendar:
        return None  # 无法确定
    
    year = date_str[:4]
    if year not in calendar:
        return None
    
    year_data = calendar[year]
    
    # 检查是否为交易日
    if date_str in year_data.get('trading_days', []):
        return True
    
    # 检查是否为假日
    if date_str in year_data.get('holidays', []):
        return False
    
    # 检查是否为周末
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        if date_obj.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
    except Exception:
        pass
    
    return None  # 未明确标记
```

### 2. 修改`get_sector_rotation()`函数（约第559行）
在周末检查之后，添加本地日历检查：

```python
def get_sector_rotation(top_n: int = 5, analysis_date: str | None = None, debug: bool = False) -> dict[str, Any]:
    debug = resolve_debug(debug)
    screener_cfg = get_screener_config()
    fallback_ok = is_fallback_enabled(default=False)
    target_ymd, target_date = _parse_analysis_date(analysis_date)

    # 1. 优先使用本地交易日历检查
    local_trading_check = _is_trading_day_local(target_ymd)
    if local_trading_check is not None:
        if not local_trading_check:
            if debug:
                print(f"[DEBUG] 本地日历标记为非交易日 ({target_ymd})，返回空数据")
            dbg: dict[str, Any] = {"module": "get_sector_rotation", "analysis_date": target_ymd, 
                                  "local_calendar_skip": True, "is_trading_day": False}
            return _fallback_sector_rotation(debug=debug, debug_info=dbg) if fallback_ok else with_debug(
                {
                    "date": target_date.strftime("%Y-%m-%d"),
                    "top_sectors": [],
                    "data_source": "local_calendar",
                    "error": "non_trading_day_local",
                },
                debug,
                dbg,
            )
        else:
            if debug:
                print(f"[DEBUG] 本地日历确认为交易日 ({target_ymd})，继续执行")
    else:
        if debug:
            print(f"[DEBUG] 本地日历未明确标记 ({target_ymd})，使用原有逻辑")

    # 2. 原有的周末检查（保留作为备用）
    if target_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
        if debug:
            print(f"[DEBUG] Weekend detected ({target_date.strftime('%Y-%m-%d')}), returning empty sector data")
        dbg: dict[str, Any] = {"module": "get_sector_rotation", "analysis_date": target_ymd, 
                              "api_calls": [], "fallback_enabled": fallback_ok, "weekend_skip": True}
        return _fallback_sector_rotation(debug=debug, debug_info=dbg) if fallback_ok else with_debug(
            {
                "date": target_date.strftime("%Y-%m-%d"),
                "top_sectors": [],
                "data_source": "weekend",
                "error": "weekend_no_data",
            },
            debug,
            dbg,
        )

    # 3. 原有的Tushare交易日检查（保留但添加超时）
    # ... 原有代码不变，但为trade_cal API添加更健壮的超时机制
```

### 3. 增强超时机制（替代signal.alarm）
```python
import threading

class TimeoutException(Exception):
    pass

def call_with_timeout(func, timeout=5, default=None):
    """使用threading.Timer实现超时"""
    result = [default]
    exception = [None]
    
    def worker():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        # 超时，尝试终止
        return default
    elif exception[0]:
        raise exception[0]
    else:
        return result[0]

# 在Tushare API调用处使用
try:
    cal = call_with_timeout(
        lambda: pro.trade_cal(exchange="SSE", start_date=query_date, end_date=query_date),
        timeout=3,
        default=None
    )
    if cal is None:
        # 超时，跳过Tushare API调用
        dbg["tushare_timeout"] = True
        raise Exception("Tushare API调用超时")
except Exception as e:
    # 处理异常
    pass
```

## 测试验证
1. **单元测试**: 验证本地日历函数正确识别交易日/非交易日
2. **集成测试**: 运行T99扫描，验证不再卡在`trade_cal` API
3. **周一14:30**: 实际生产环境验证

## 回滚方案
如果修改导致问题，可恢复原始文件：
```bash
cp /root/.openclaw/workspace/skills/a-share-short-decision/tools/market_data.py.backup \
   /root/.openclaw/workspace/skills/a-share-short-decision/tools/market_data.py
```

## 预期效果
- **立即解决**: `trade_cal` API挂起问题
- **零成本**: 本地文件，无API调用费用
- **快速实施**: 1小时内完成修改和测试
- **周一验证**: 14:30扫描正常执行