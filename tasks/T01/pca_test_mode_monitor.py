#!/usr/bin/env python3
"""
T01 PCA测试模式观测与决策系统
自动观测PCA效果，根据测试结果决定是否开启PCA
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


class PCATestModeMonitor:
    """PCA测试模式监控器"""
    
    def __init__(self):
        self.config = self._load_config()
        self.db_path = os.path.join(current_dir, "data", "t01_database.db")
        self.state_file = os.path.join(current_dir, "state", "pca_test_state.json")
        self._ensure_state_dir()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        import yaml
        config_path = os.path.join(current_dir, "config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get("pca", {})
    
    def _ensure_state_dir(self):
        """确保状态目录存在"""
        state_dir = os.path.dirname(self.state_file)
        os.makedirs(state_dir, exist_ok=True)
    
    def _load_state(self) -> Dict:
        """加载测试状态"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "test_start_date": None,
            "test_phase": "not_started",  # not_started, testing, decided
            "samples_collected": 0,
            "decision": None,
            "decision_date": None,
            "metrics_history": []
        }
    
    def _save_state(self, state: Dict):
        """保存测试状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def _get_performance_data(self, days: int = 30) -> Dict:
        """获取绩效数据"""
        if not os.path.exists(self.db_path):
            return {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='t01_performance'")
            if not cursor.fetchone():
                conn.close()
                return {}
            
            # 获取最近N天的绩效
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT date, win_rate, sharpe_ratio, max_drawdown, avg_return, pca_enabled
                FROM t01_performance 
                WHERE date >= ? 
                ORDER BY date DESC
            """, (start_date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 分离PCA开启和关闭的数据
            pca_off_data = [r for r in rows if not r[5]]  # pca_enabled = 0/false
            pca_on_data = [r for r in rows if r[5]]  # pca_enabled = 1/true
            
            return {
                "pca_off": self._calculate_metrics(pca_off_data),
                "pca_on": self._calculate_metrics(pca_on_data),
                "total_samples": len(rows)
            }
            
        except Exception as e:
            print(f"❌ 获取绩效数据失败: {e}")
            return {}
    
    def _calculate_metrics(self, data: List) -> Dict:
        """计算指标"""
        if not data:
            return {}
        
        import statistics
        
        win_rates = [r[1] for r in data if r[1] is not None]
        sharpe_ratios = [r[2] for r in data if r[2] is not None]
        max_drawdowns = [r[3] for r in data if r[3] is not None]
        avg_returns = [r[4] for r in data if r[4] is not None]
        
        return {
            "count": len(data),
            "win_rate": statistics.mean(win_rates) if win_rates else 0,
            "sharpe_ratio": statistics.mean(sharpe_ratios) if sharpe_ratios else 0,
            "max_drawdown": statistics.mean(max_drawdowns) if max_drawdowns else 0,
            "avg_return": statistics.mean(avg_returns) if avg_returns else 0
        }
    
    def _make_decision(self, pca_off: Dict, pca_on: Dict) -> Tuple[str, str]:
        """
        根据测试结果做出决策
        返回: (decision, reason)
        decision: "enable", "disable", "continue_testing"
        """
        test_config = self.config.get("test_mode", {})
        promote = test_config.get("promote_threshold", {})
        demote = test_config.get("demote_threshold", {})
        min_samples = test_config.get("min_samples", 10)
        
        # 检查样本量
        if pca_on.get("count", 0) < min_samples:
            return "continue_testing", f"PCA样本不足({pca_on.get('count', 0)}/{min_samples})，继续测试"
        
        # 计算改进幅度
        win_rate_diff = pca_on.get("win_rate", 0) - pca_off.get("win_rate", 0)
        sharpe_diff = pca_on.get("sharpe_ratio", 0) - pca_off.get("sharpe_ratio", 0)
        
        # 判断是否满足开启条件
        if win_rate_diff >= promote.get("win_rate_improvement", 0.05) and \
           sharpe_diff >= promote.get("sharpe_improvement", 0.1):
            return "enable", f"PCA表现优异: 胜率提升{win_rate_diff:.2%}, 夏普提升{sharpe_diff:.2f}"
        
        # 判断是否满足关闭条件（表现明显变差）
        if win_rate_diff <= demote.get("win_rate_drop", -0.03) or \
           sharpe_diff <= demote.get("sharpe_drop", -0.05):
            return "disable", f"PCA表现不佳: 胜率变化{win_rate_diff:.2%}, 夏普变化{sharpe_diff:.2f}"
        
        # 继续测试
        return "continue_testing", f"PCA效果不明显: 胜率变化{win_rate_diff:.2%}, 夏普变化{sharpe_diff:.2f}"
    
    def check_and_decide(self) -> Dict:
        """检查状态并做出决策"""
        test_config = self.config.get("test_mode", {})
        
        if not test_config.get("enabled", False):
            return {"status": "test_mode_disabled", "action": "none"}
        
        state = self._load_state()
        
        # 如果已经做出决策，不再重复
        if state.get("decision"):
            return {
                "status": "already_decided",
                "decision": state["decision"],
                "decision_date": state["decision_date"],
                "action": "none"
            }
        
        # 获取绩效数据
        duration_days = test_config.get("duration_days", 14)
        performance = self._get_performance_data(days=duration_days)
        
        if not performance:
            return {"status": "no_data", "action": "none"}
        
        # 做出决策
        pca_off = performance.get("pca_off", {})
        pca_on = performance.get("pca_on", {})
        decision, reason = self._make_decision(pca_off, pca_on)
        
        # 更新状态
        state["samples_collected"] = performance.get("total_samples", 0)
        state["metrics_history"].append({
            "date": datetime.now().isoformat(),
            "pca_off": pca_off,
            "pca_on": pca_on,
            "decision": decision,
            "reason": reason
        })
        
        # 如果决策不是继续测试，保存最终决策
        if decision != "continue_testing":
            state["decision"] = decision
            state["decision_date"] = datetime.now().isoformat()
            state["test_phase"] = "decided"
            
            # 自动更新配置
            if decision == "enable":
                self._update_pca_config(enabled=True)
            
            self._send_notification(decision, reason, pca_off, pca_on)
        
        self._save_state(state)
        
        return {
            "status": "decision_made" if decision != "continue_testing" else "testing",
            "decision": decision,
            "reason": reason,
            "pca_off_metrics": pca_off,
            "pca_on_metrics": pca_on,
            "action": "enable_pca" if decision == "enable" else "none"
        }
    
    def _update_pca_config(self, enabled: bool):
        """更新PCA配置"""
        import yaml
        
        config_path = os.path.join(current_dir, "config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        config["pca"]["enabled"] = enabled
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        
        print(f"✅ PCA配置已更新: enabled={enabled}")
    
    def _send_notification(self, decision: str, reason: str, pca_off: Dict, pca_on: Dict):
        """发送飞书通知"""
        try:
            env = os.environ.copy()
            node_path = "/root/.nvm/versions/node/v22.22.0/bin"
            if node_path not in env.get('PATH', ''):
                env['PATH'] = node_path + ':' + env.get('PATH', '')
            
            today_str = datetime.now().strftime("%Y年%m月%d日")
            
            if decision == "enable":
                message = f"""🎉 **PCA测试完成 - 决策: 开启**

**决策时间**: {today_str}
**决策原因**: {reason}

**测试数据对比**:
| 指标 | PCA关闭 | PCA开启 | 变化 |
|------|---------|---------|------|
| 胜率 | {pca_off.get('win_rate', 0):.2%} | {pca_on.get('win_rate', 0):.2%} | +{pca_on.get('win_rate', 0) - pca_off.get('win_rate', 0):.2%} |
| 夏普比率 | {pca_off.get('sharpe_ratio', 0):.2f} | {pca_on.get('sharpe_ratio', 0):.2f} | +{pca_on.get('sharpe_ratio', 0) - pca_off.get('sharpe_ratio', 0):.2f} |
| 最大回撤 | {pca_off.get('max_drawdown', 0):.2%} | {pca_on.get('max_drawdown', 0):.2%} | {pca_on.get('max_drawdown', 0) - pca_off.get('max_drawdown', 0):.2%} |
| 平均收益 | {pca_off.get('avg_return', 0):.2%} | {pca_on.get('avg_return', 0):.2%} | +{pca_on.get('avg_return', 0) - pca_off.get('avg_return', 0):.2%} |

**系统行动**:
✅ PCA已自动开启
✅ 下次选股将使用PCA因子正交化

**建议**:
继续监控PCA效果，如有异常及时调整。"""
            else:
                message = f"""📊 **PCA测试完成 - 决策: 保持关闭**

**决策时间**: {today_str}
**决策原因**: {reason}

**测试数据对比**:
| 指标 | PCA关闭 | PCA开启 | 变化 |
|------|---------|---------|------|
| 胜率 | {pca_off.get('win_rate', 0):.2%} | {pca_on.get('win_rate', 0):.2%} | {pca_on.get('win_rate', 0) - pca_off.get('win_rate', 0):.2%} |
| 夏普比率 | {pca_off.get('sharpe_ratio', 0):.2f} | {pca_on.get('sharpe_ratio', 0):.2f} | {pca_on.get('sharpe_ratio', 0) - pca_off.get('sharpe_ratio', 0):.2f} |

**系统行动**:
✅ PCA保持关闭
✅ 继续使用原始评分逻辑

**建议**:
可考虑调整PCA参数后重新测试，或等待更多数据。"""
            
            import subprocess
            cmd = [
                '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
                'message', 'send',
                '--channel', 'feishu',
                '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
                '--message', message
            ]
            
            subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
            print("✅ 通知已发送")
            
        except Exception as e:
            print(f"❌ 发送通知失败: {e}")


def main():
    """主函数"""
    print("🔍 启动PCA测试模式观测...")
    
    monitor = PCATestModeMonitor()
    result = monitor.check_and_decide()
    
    print(f"\n📊 决策结果:")
    print(f"  状态: {result['status']}")
    print(f"  决策: {result.get('decision', 'N/A')}")
    print(f"  原因: {result.get('reason', 'N/A')}")
    print(f"  行动: {result['action']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
