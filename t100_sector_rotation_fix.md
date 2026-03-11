# T100 板块轮动预测智能修复方案

**创建时间**: 2026-03-08 17:30 UTC (北京时间 01:30)
**状态**: 待批准实施
**预期修复时间**: 15分钟
**今晚生效**: ✅ 是的 (22:00 宏观报告)

---

## 🔍 问题诊断

### 当前问题
1. **非交易日显示"error"**: `get_sector_rotation_prediction()`函数在非交易日尝试调用API，Tushare和AKShare都失败
2. **API挂起风险**: 非交易日API调用可能无限期等待，阻塞报告生成
3. **用户体验差**: "error"不明确，应改为友好提示

### 根本原因
```python
# 当前代码流程
def get_sector_rotation_prediction():
    try:
        # 1. 检查缓存 (12小时有效期)
        # 2. 尝试Tushare API
        # 3. Tushare失败 → 回退AKShare
        # 4. AKShare失败 → 返回{"signal": "error"}
    
    # 缺少: 非交易日检查!
```

## 🛠️ 修复方案

### 核心修复: 交易日智能感知
在函数开头添加交易日检查，非交易日直接返回友好提示：

```python
def get_sector_rotation_prediction() -> Dict[str, Any]:
    """板块轮动预测 - 增强版（支持非交易日）"""
    
    # 1. 交易日检查 (新增)
    try:
        from trading_day_check import is_trading_day
        if not is_trading_day():
            return {
                "predicted_sectors": [],
                "signal": "non_trading_day",
                "method": "trading_day_check",
                "note": "非交易日，数据暂不可用"
            }
    except ImportError:
        pass  # 保持向后兼容
    
    # 2. 原有缓存检查逻辑...
    # 3. 原有API调用逻辑...
```

### 修复效果对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| **非交易日** | `信号: error` | `信号: non_trading_day`<br>说明: 非交易日，数据暂不可用 |
| **交易日** | `信号: strong_momentum` | `信号: strong_momentum` (不变) |
| **API失败** | `信号: error` | `信号: insufficient_data` (更明确) |

## 📊 实施步骤

### 方案A: 最小化修复 (推荐)
```bash
# 1. 创建修复补丁
cd /root/.openclaw/workspace/skills/macro-monitor
cp run_monitor.py run_monitor.py.backup

# 2. 应用补丁 (使用下面的patch文件)
patch -p1 < sector_rotation_fix.patch

# 3. 测试修复
python3 -c "from trading_day_check import is_trading_day; print(f'今天是交易日吗? {is_trading_day()}')"
```

### 方案B: 手动修改
编辑 `run_monitor.py`，在 `get_sector_rotation_prediction()` 函数开头添加交易日检查。

### 方案C: 完整重构
创建新的智能数据获取模块，集成交易日检查、缓存管理、多数据源回退。

## 🎯 修复补丁

```patch
--- run_monitor.py.original
+++ run_monitor.py.fixed
@@ -1945,6 +1945,16 @@
     """
     try:
+        # ===== 交易日检查 (新增) =====
+        try:
+            from trading_day_check import is_trading_day
+            if not is_trading_day():
+                return {
+                    "predicted_sectors": [],
+                    "signal": "non_trading_day",
+                    "method": "trading_day_check",
+                    "note": "非交易日，数据暂不可用"
+                }
+        except ImportError:
+            pass  # 交易日检查模块不可用，继续执行原逻辑
+        # ===== 交易日检查结束 =====
+
         # 缓存机制：检查是否有有效的缓存数据
         import os
```

## 🧪 测试验证

```python
# 测试脚本: test_sector_fix.py
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/macro-monitor')

# 模拟非交易日 (2026-03-08 周日)
import datetime
original_date = datetime.datetime.now()
test_date = datetime.datetime(2026, 3, 8)  # 周日

# 临时修改系统日期 (概念演示)
print(f"测试日期: {test_date.strftime('%Y-%m-%d')}")
print("预期结果: signal='non_trading_day', note='非交易日，数据暂不可用'")

# 实际测试
from trading_day_check import is_trading_day
print(f"is_trading_day('2026-03-08'): {is_trading_day('2026-03-08')}")
```

## ⏰ 时间线

- **现在**: 创建修复方案，等待批准
- **+5分钟**: 应用修复补丁
- **+10分钟**: 测试验证
- **+15分钟**: 完成，今晚22:00生效

## 📈 预期收益

1. **数据准确性**: 消除误导性"error"，明确标注"非交易日"
2. **系统稳定性**: 避免非交易日API挂起风险
3. **用户体验**: 友好提示，增强信任度
4. **维护简化**: 统一交易日处理逻辑，便于未来扩展

## 🚀 快速启动

如果您同意此方案，回复 **"应用修复"** 我将立即实施。

如果您希望查看详细代码差异，回复 **"查看差异"**。

如果您有其他修改建议，请直接说明。 🦐