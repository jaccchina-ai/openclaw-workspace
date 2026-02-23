#!/usr/bin/env python3
"""
测试消息推送格式
"""

import json
import sys
from pathlib import Path

def main():
    print("测试消息推送格式优化")
    print("="*50)
    
    # 加载候选股票
    candidates_file = Path("state/candidates_20260213_to_20260224.json")
    if not candidates_file.exists():
        print(f"❌ 文件不存在: {candidates_file}")
        return False
    
    with open(candidates_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    trade_date = data.get('trade_date', '20260213')
    t1_date = data.get('t1_date', '20260224')
    
    if not candidates:
        print("❌ 没有候选股票数据")
        return False
    
    print(f"📅 T日: {trade_date}, T+1日: {t1_date}")
    print(f"📊 候选股票数量: {len(candidates)}")
    
    # 生成优化后的消息
    message_parts = []
    
    # 标题
    message_parts.append(f"📊 **T01策略候选股票 - {trade_date} (用于{t1_date}竞价测试)**")
    message_parts.append("="*50)
    
    # 市场状况
    message_parts.append(f"**市场状况**: 基于{trade_date}数据生成")
    message_parts.append(f"**风险等级**: 待评估 (等待竞价数据)")
    message_parts.append(f"**建议**: 观察2月24日竞价表现")
    
    # 融资融券信息
    message_parts.append(f"**数据备注**: T日评分完成，等待T+1竞价数据")
    message_parts.append("="*50)
    
    # 候选股票
    message_parts.append(f"**🎯 候选股票 ({len(candidates)}只)**")
    
    for i, stock in enumerate(candidates, 1):
        name = stock.get('name', 'N/A')
        code = stock.get('ts_code', 'N/A')
        total_score = stock.get('total_score', 0)
        
        message_parts.append(f"\n#{i} **{name}** ({code})")
        message_parts.append(f"  **综合评分**: {total_score:.1f}")
        
        # 关键指标
        message_parts.append(f"  **关键指标**:")
        message_parts.append(f"    涨停涨幅: {stock.get('pct_chg', 0)}%")
        
        first_time = stock.get('first_time', '')
        if first_time:
            try:
                time_str = f"{first_time[:2]}:{first_time[2:4]}:{first_time[4:6]}"
                message_parts.append(f"    首次涨停: {time_str}")
            except:
                message_parts.append(f"    首次涨停: {first_time}")
        else:
            message_parts.append(f"    首次涨停: 未知")
        
        message_parts.append(f"    封成比: {stock.get('seal_ratio', 0):.3f}")
        message_parts.append(f"    封单/流通: {stock.get('seal_to_mv', 0)*10000:.2f}bp")
        message_parts.append(f"    换手率: {stock.get('turnover_ratio', 0):.2f}%")
        message_parts.append(f"    热点板块: {'是' if stock.get('is_hot_sector', False) else '否'}")
        message_parts.append(f"    行业: {stock.get('industry', '未知')}")
        
        # 评分详情
        message_parts.append(f"  **评分详情**:")
        message_parts.append(f"    涨停时间评分: {stock.get('first_limit_time_score', 0):.1f}")
        message_parts.append(f"    封单质量评分: {stock.get('order_quality_score', 0):.1f}")
        message_parts.append(f"    流动性评分: {stock.get('liquidity_score', 0):.1f}")
        message_parts.append(f"    资金流评分: {stock.get('money_flow_score', 0):.1f}")
        message_parts.append(f"    热点板块评分: {stock.get('sector_score', 0):.1f}")
        message_parts.append(f"    龙虎榜评分: {stock.get('dragon_list_score', 0):.1f}")
        
        # 资金信息
        fd_amount = stock.get('fd_amount', 0)
        amount = stock.get('amount', 0)
        float_mv = stock.get('float_mv', 0)
        
        message_parts.append(f"  **资金信息**:")
        if fd_amount > 0:
            message_parts.append(f"    封单金额: {fd_amount/1e6:.2f}万")
        if amount > 0:
            message_parts.append(f"    成交金额: {amount/1e6:.2f}万")
        if float_mv > 0:
            message_parts.append(f"    流通市值: {float_mv/1e8:.2f}亿")
    
    # 注意事项
    message_parts.append("\n" + "="*50)
    message_parts.append("**📋 重要提示**")
    message_parts.append("1. 以上为T日评分结果，基于历史数据")
    message_parts.append("2. 实际推荐需等待T+1日竞价数据")
    message_parts.append("3. 2月24日09:25将进行竞价分析")
    message_parts.append("4. 最终推荐将结合竞价表现确定")
    
    message_parts.append("\n**⏰ 下一步计划**:")
    message_parts.append("1. 2月24日09:25: 获取实时竞价数据")
    message_parts.append("2. 2月24日09:28: 生成最终推荐")
    message_parts.append("3. 2月24日09:30前: 推送买入建议")
    
    # 生成完整消息
    full_message = "\n".join(message_parts)
    
    print(f"\n📋 优化后的消息推送格式:")
    print("="*80)
    print(full_message)
    print("="*80)
    
    # 检查消息长度
    message_length = len(full_message)
    print(f"\n📊 消息统计:")
    print(f"  总长度: {message_length} 字符")
    print(f"  行数: {len(full_message.split(chr(10)))} 行")
    
    # 飞书消息长度建议：一般不超过2000字符
    if message_length > 1900:
        print(f"  ⚠️  消息可能过长，建议精简")
    else:
        print(f"  ✅ 消息长度合适")
    
    # 保存消息示例
    output_file = Path("state/message_example.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_message)
    
    print(f"\n💾 消息示例已保存: {output_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)