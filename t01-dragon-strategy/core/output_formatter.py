#!/usr/bin/env python3
"""
输出格式化模块
根据老板要求的格式输出筛选结果
"""

import pandas as pd
from typing import Dict, Any, List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputFormatter:
    """输出格式化类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_config = config.get('output', {})
        
    def format_output(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化输出结果
        返回结构化数据，便于后续保存或展示
        """
        formatted = {
            'timestamp': datetime.now().isoformat(),
            'candidates': [],
            'ranked_stocks': [],
            'alerts': signals.get('alerts', []),
            'summary': signals.get('summary', {}),
            'metadata': {
                'strategy': '龙头战法',
                'version': 'T01',
                'config': self.output_config
            }
        }
        
        # 格式化候选股票
        candidates = signals.get('candidates', [])
        if isinstance(candidates, pd.DataFrame) and not candidates.empty:
            formatted['candidates'] = candidates.to_dict('records')
        elif isinstance(candidates, list):
            formatted['candidates'] = candidates
        
        # 格式化排名股票
        ranked = signals.get('ranked_stocks', pd.DataFrame())
        if isinstance(ranked, pd.DataFrame) and not ranked.empty:
            formatted['ranked_stocks'] = ranked.to_dict('records')
        
        # 生成摘要统计
        if not formatted['summary']:
            formatted['summary'] = self._generate_summary(formatted)
        
        return formatted
    
    def _generate_summary(self, formatted_output: Dict[str, Any]) -> Dict[str, Any]:
        """生成结果摘要"""
        candidates = formatted_output.get('candidates', [])
        ranked = formatted_output.get('ranked_stocks', [])
        
        summary = {
            'total_candidates': len(candidates),
            'total_ranked': len(ranked),
            'alert_count': len(formatted_output.get('alerts', [])),
            'generated_at': formatted_output['timestamp']
        }
        
        # 如果有排名数据，添加top股票信息
        if ranked:
            top_n = min(self.output_config.get('top_n', 5), len(ranked))
            summary['top_stocks'] = ranked[:top_n]
        
        return summary
    
    def to_table(self, formatted_output: Dict[str, Any]) -> str:
        """
        转换为表格格式字符串
        适合控制台输出或简单文本展示
        """
        ranked = formatted_output.get('ranked_stocks', [])
        
        if not ranked:
            return "暂无符合条件的股票"
        
        # 创建DataFrame
        df = pd.DataFrame(ranked)
        
        # 选择要显示的列
        display_cols = []
        if not df.empty:
            # 优先显示常见字段
            available_cols = df.columns.tolist()
            preferred = ['symbol', 'name', 'change_pct', 'volume_ratio', 'composite_score']
            for col in preferred:
                if col in available_cols:
                    display_cols.append(col)
            
            # 添加其他字段（最多6列）
            other_cols = [c for c in available_cols if c not in preferred]
            display_cols.extend(other_cols[:6 - len(display_cols)])
        
        if display_cols:
            df_display = df[display_cols].head(self.output_config.get('top_n', 10))
            return df_display.to_string(index=False)
        else:
            return df.head(10).to_string(index=False)
    
    def to_csv(self, formatted_output: Dict[str, Any], filepath: str = None) -> str:
        """保存为CSV文件"""
        if not filepath:
            # 使用配置中的路径模板
            template = self.output_config.get('file_path', './output/results_{date}.csv')
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = template.format(date=date_str)
        
        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        ranked = formatted_output.get('ranked_stocks', [])
        if ranked:
            df = pd.DataFrame(ranked)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"结果已保存到: {filepath}")
            return filepath
        else:
            logger.warning("没有排名数据可保存")
            return ""
    
    def to_json(self, formatted_output: Dict[str, Any], filepath: str = None) -> str:
        """保存为JSON文件"""
        if not filepath:
            template = self.output_config.get('file_path', './output/results_{date}.json').replace('.csv', '.json')
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = template.format(date=date_str)
        
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(formatted_output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON结果已保存到: {filepath}")
        return filepath
    
    def generate_alerts(self, formatted_output: Dict[str, Any]) -> List[str]:
        """
        生成告警消息列表
        根据配置的阈值检查异常情况
        """
        alerts = formatted_output.get('alerts', [])
        
        # 如果没有告警但配置了告警阈值，可以自动检测
        if not alerts and formatted_output.get('ranked_stocks'):
            ranked = formatted_output['ranked_stocks']
            df = pd.DataFrame(ranked)
            
            # 检查价格波动告警
            price_threshold = self.output_config.get('alert_thresholds', {}).get('price_change', 5)
            if 'change_pct' in df.columns:
                big_movers = df[df['change_pct'].abs() >= price_threshold]
                for _, row in big_movers.iterrows():
                    alerts.append(
                        f"价格波动告警: {row.get('symbol', 'N/A')} 涨跌幅 {row['change_pct']:.2f}%"
                    )
            
            # 检查成交量异常
            volume_threshold = self.output_config.get('alert_thresholds', {}).get('volume_spike', 200)
            if 'volume_ratio' in df.columns:
                volume_spikes = df[df['volume_ratio'] >= volume_threshold]
                for _, row in volume_spikes.iterrows():
                    alerts.append(
                        f"成交量异常: {row.get('symbol', 'N/A')} 成交量放大 {row['volume_ratio']:.1f}倍"
                    )
        
        return alerts


if __name__ == "__main__":
    # 测试
    config = {'output': {}}
    formatter = OutputFormatter(config)
    
    test_output = {
        'candidates': [],
        'ranked_stocks': [
            {'symbol': '000001', 'name': '平安银行', 'change_pct': 3.5, 'volume_ratio': 1.8},
            {'symbol': '000002', 'name': '万科A', 'change_pct': -2.1, 'volume_ratio': 2.3}
        ],
        'alerts': []
    }
    
    formatted = formatter.format_output(test_output)
    print("表格格式:")
    print(formatter.to_table(formatted))
    print("\n告警检测:")
    print(formatter.generate_alerts(formatted))