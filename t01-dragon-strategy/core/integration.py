#!/usr/bin/env python3
"""
T01任务与现有a-share-short-decision技能的集成模块
"""

import sys
import os
from pathlib import Path

# 添加现有技能目录到Python路径
skill_path = Path(__file__).parent.parent.parent / 'skills' / 'a-share-short-decision'
sys.path.insert(0, str(skill_path))

try:
    from tools.fusion_engine import short_term_signal_engine
    from tools.market_data import get_market_sentiment, get_sector_rotation, scan_strong_stocks
    from tools.money_flow import analyze_capital_flow
    from tools.reporting import generate_daily_report
    from tools.risk_control import short_term_risk_control
    HAS_SKILL = True
except ImportError as e:
    print(f"无法导入现有技能模块: {e}")
    HAS_SKILL = False


class ExistingSkillIntegration:
    """现有技能集成类"""
    
    def __init__(self):
        if not HAS_SKILL:
            raise RuntimeError("a-share-short-decision技能未找到或导入失败")
    
    def get_market_overview(self, date=None):
        """获取市场概览（情绪+板块）"""
        sentiment = get_market_sentiment(analysis_date=date)
        sectors = get_sector_rotation(analysis_date=date)
        
        return {
            'sentiment': sentiment,
            'sector_rotation': sectors
        }
    
    def scan_strong_candidates(self, date=None):
        """扫描强势股（基于现有技能）"""
        stocks = scan_strong_stocks(analysis_date=date)
        return stocks
    
    def get_capital_flow(self, symbol=None, date=None):
        """获取资金流数据"""
        capital = analyze_capital_flow(symbol=symbol, analysis_date=date)
        return capital
    
    def generate_signals(self, date=None):
        """生成短期交易信号"""
        signals = short_term_signal_engine(analysis_date=date)
        return signals
    
    def filter_for_dragon_head(self, signals):
        """
        从现有信号中筛选符合龙头战法的股票
        待完善：根据老板提供的龙头战法规则
        """
        if not signals or not isinstance(signals, dict):
            return []
        
        candidates = signals.get('candidates', [])
        if not candidates:
            return []
        
        # 示例筛选：涨幅大、成交活跃
        dragon_candidates = []
        for candidate in candidates:
            # 这里可以添加龙头战法特定条件
            # 例如：连板数、板块地位等
            dragon_candidates.append(candidate)
        
        return dragon_candidates[:10]  # 返回前10个
    
    def generate_dragon_head_report(self, date=None):
        """生成龙头战法专属报告"""
        # 1. 获取市场数据
        overview = self.get_market_overview(date)
        
        # 2. 获取强势股
        strong_stocks = self.scan_strong_candidates(date)
        
        # 3. 生成信号
        signals = self.generate_signals(date)
        
        # 4. 筛选龙头股
        dragon_stocks = self.filter_for_dragon_head(signals)
        
        # 5. 整理报告
        report = {
            'date': date or '最新',
            'market_overview': overview,
            'strong_stocks_count': len(strong_stocks.get('stocks', [])),
            'signal_strength': signals.get('status', {}).get('signal_strength', 0),
            'dragon_candidates': dragon_stocks,
            'recommendation': '等待龙头战法规则完善' if not dragon_stocks else '发现潜在龙头股'
        }
        
        return report


if __name__ == "__main__":
    # 测试集成
    if HAS_SKILL:
        print("成功导入现有技能模块")
        
        # 创建集成实例
        try:
            integration = ExistingSkillIntegration()
            
            # 测试获取市场概览
            print("\n测试市场概览...")
            overview = integration.get_market_overview()
            print(f"市场情绪: {overview.get('sentiment', {}).get('score', 'N/A')}")
            
            # 测试扫描强势股
            print("\n测试强势股扫描...")
            strong = integration.scan_strong_candidates()
            stocks = strong.get('stocks', [])
            print(f"找到 {len(stocks)} 只强势股")
            
            # 测试信号生成
            print("\n测试信号生成...")
            signals = integration.generate_signals()
            print(f"信号强度: {signals.get('status', {}).get('signal_strength', 'N/A')}")
            
        except Exception as e:
            print(f"集成测试失败: {e}")
    else:
        print("无法使用现有技能，请确保a-share-short-decision技能已正确安装")