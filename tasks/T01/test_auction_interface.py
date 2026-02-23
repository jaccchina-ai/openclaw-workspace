#!/usr/bin/env python3
"""
测试竞价数据接口
1. stk_auction_o - 历史竞价数据
2. stk_auction - 实时竞价数据
"""

import sys
import yaml
import pandas as pd
import logging
import tushare as ts

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_stk_auction_o():
    """测试历史竞价数据接口 stk_auction_o"""
    print("🔍 测试历史竞价数据接口 (stk_auction_o)...")
    
    try:
        # 加载配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 测试最近几个交易日的竞价数据
        test_dates = ['20240222', '20240221', '20240220', '20240219']
        
        for date in test_dates:
            try:
                df = pro.stk_auction_o(trade_date=date, fields='ts_code,close,vol,amount,vwap')
                
                if not df.empty:
                    print(f"✅ 日期 {date}: 获取到 {len(df)} 条竞价记录")
                    print(f"   示例: {df.iloc[0]['ts_code']}, 开盘价: {df.iloc[0]['close']}, 成交量: {df.iloc[0]['vol']}")
                    
                    # 检查关键字段
                    required_fields = ['close', 'vol', 'amount', 'vwap']
                    missing = [f for f in required_fields if f not in df.columns]
                    if missing:
                        print(f"⚠️  缺失字段: {missing}")
                    else:
                        print(f"✅ 所有关键字段存在")
                    
                    return True, df
                else:
                    print(f"⚠️  日期 {date}: 0条记录 (可能是非交易日或数据未更新)")
                    
            except Exception as e:
                print(f"❌ 日期 {date} 错误: {e}")
        
        print("❌ 所有测试日期都未获取到数据")
        return False, None
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False, None

def test_stk_auction():
    """测试实时竞价数据接口 stk_auction"""
    print("\n🔍 测试实时竞价数据接口 (stk_auction)...")
    
    try:
        # 加载配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        ts.set_token(config['api']['api_key'])
        pro = ts.pro_api()
        
        # 注意: stk_auction 是实时接口，历史数据可能返回0
        test_date = '20240222'
        
        try:
            df = pro.stk_auction(trade_date=test_date, fields='ts_code,price,pre_close,vol,amount,turnover_rate,volume_ratio')
            
            if not df.empty:
                print(f"✅ 日期 {test_date}: 获取到 {len(df)} 条实时竞价记录")
                print(f"   示例: {df.iloc[0]['ts_code']}, 价格: {df.iloc[0].get('price', 'N/A')}")
                
                # 检查关键字段
                fields_to_check = ['price', 'pre_close', 'vol', 'amount']
                available_fields = [f for f in fields_to_check if f in df.columns]
                print(f"✅ 可用字段: {available_fields}")
                
                return True
            else:
                print(f"⚠️  日期 {test_date}: 0条记录 (实时接口可能只支持当日数据)")
                print("   说明: stk_auction 接口是实时数据，仅在交易日9:25-9:29开放")
                return False
                
        except Exception as e:
            print(f"❌ 接口错误: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def compare_interfaces():
    """比较两个竞价数据接口"""
    print("\n📊 比较两个竞价数据接口...")
    
    print("""
stk_auction_o (历史数据):
  - 用途: 每日盘后更新的开盘集合竞价数据
  - 时间: 历史数据，每日盘后更新
  - 字段: close(开盘价), vol(成交量), amount(成交额), vwap(均价)
  - 权限: 需要股票分钟权限
  
stk_auction (实时数据):
  - 用途: 实时竞价数据
  - 时间: 仅交易日9:25-9:29实时数据
  - 字段: price(成交价), pre_close(前收盘), vol(成交量), amount(成交额)
  - 特点: 包含turnover_rate(换手率), volume_ratio(量比)
  
T01策略使用方案:
  - 回测/测试: 使用 stk_auction_o (历史数据)
  - 实时运行: 使用 stk_auction (实时数据)
  - 字段映射: close(历史) ↔ price(实时)
""")

def test_integration_scenario():
    """测试集成场景"""
    print("\n🎯 测试T+1竞价评分集成场景...")
    
    # 模拟数据场景
    print("""
T+1日竞价评分流程:
1. 输入: T日选出的候选股票列表
2. 数据获取:
   - 历史回测: 使用 stk_auction_o 获取竞价数据
   - 实时运行: 使用 stk_auction 获取实时竞价数据
3. 关键计算:
   - 开盘涨幅 = (竞价开盘价 - 前收盘价) / 前收盘价 * 100
   - 竞价量比 = 竞价成交量 / 5日平均成交量
   - 竞价换手率 = 竞价成交额 / 流通市值
4. 评分输出:
   - 开盘涨幅评分 (权重40%)
   - 竞价量比评分 (权重20%)
   - 竞价换手率评分 (权重20%)
   - 竞价金额评分 (权重20%)
""")

def main():
    """主测试函数"""
    print("="*60)
    print("T01策略 - 竞价数据接口测试")
    print("="*60)
    
    print("\n📅 测试计划:")
    print("1. 测试历史竞价接口 (stk_auction_o)")
    print("2. 测试实时竞价接口 (stk_auction)")
    print("3. 接口对比分析")
    print("4. 集成场景测试")
    
    results = []
    
    # 测试历史接口
    success1, df1 = test_stk_auction_o()
    results.append(("历史竞价接口", success1))
    
    # 测试实时接口
    success2 = test_stk_auction()
    results.append(("实时竞价接口", success2))
    
    # 比较接口
    compare_interfaces()
    
    # 测试集成场景
    test_integration_scenario()
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("测试汇总")
    print('='*60)
    
    passed_count = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "⚠️  部分通过/需注意"
        print(f"{status}: {test_name}")
        if result:
            passed_count += 1
    
    print(f"\n📊 结果: {passed_count}/{len(results)} 项测试通过")
    
    if df1 is not None and not df1.empty:
        print(f"\n📋 历史竞价数据示例 (前3条):")
        print(df1.head(3).to_string())
    
    print("\n🎯 明日集成计划:")
    print("1. 修改 _get_real_auction_data() 方法，支持两个接口")
    print("2. 添加竞价数据获取策略: 实时优先，历史备选")
    print("3. 测试完整的T+1竞价评分流程")
    
    return passed_count == len(results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)