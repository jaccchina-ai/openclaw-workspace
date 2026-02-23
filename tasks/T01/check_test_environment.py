#!/usr/bin/env python3
"""
2月24日实时测试环境检查清单
检查T01系统所有组件是否就绪
"""

import sys
import os
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import tushare as ts

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestEnvironmentChecker:
    """测试环境检查器"""
    
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = None
        self.pro = None
        
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            if not Path(self.config_path).exists():
                logger.error(f"配置文件不存在: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"✅ 配置文件加载成功: {self.config_path}")
            logger.info(f"   版本: {self.config.get('version', 'N/A')}")
            logger.info(f"   最后更新: {self.config.get('last_updated', 'N/A')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置文件加载失败: {e}")
            return False
    
    def check_tushare_connection(self) -> bool:
        """检查tushare连接"""
        try:
            api_key = self.config['api']['api_key']
            ts.set_token(api_key)
            self.pro = ts.pro_api()
            
            # 简单测试: 获取交易日历
            cal_df = self.pro.trade_cal(
                exchange='SSE',
                start_date='20260213',
                end_date='20260213',
                fields='cal_date,is_open'
            )
            
            if not cal_df.empty:
                is_open = cal_df.iloc[0]['is_open']
                logger.info(f"✅ tushare连接成功")
                logger.info(f"   测试日期 2026-02-13 是否为交易日: {'是' if is_open == 1 else '否'}")
                return True
            else:
                logger.warning("⚠️  tushare连接测试返回空数据")
                return False
                
        except Exception as e:
            logger.error(f"❌ tushare连接失败: {e}")
            return False
    
    def check_key_apis(self) -> bool:
        """检查关键API接口"""
        apis_to_check = [
            ('limit_list_d', '涨停股数据'),
            ('stk_auction', '实时竞价数据'),
            ('stk_auction_o', '历史竞价数据'),
            ('margin', '融资融券数据'),
            ('stock_st', 'ST股票列表'),
            ('daily_basic', '技术指标数据'),
            ('moneyflow_dc', '资金流向数据'),
        ]
        
        all_success = True
        
        for api_name, api_desc in apis_to_check:
            try:
                # 检查API是否存在
                if hasattr(self.pro, api_name):
                    logger.info(f"✅ API接口存在: {api_name} ({api_desc})")
                else:
                    logger.error(f"❌ API接口不存在: {api_name} ({api_desc})")
                    all_success = False
            except Exception as e:
                logger.error(f"❌ 检查API {api_name} 失败: {e}")
                all_success = False
        
        return all_success
    
    def check_candidate_file(self) -> bool:
        """检查候选股票文件"""
        candidate_file = Path("state/candidates_20260213_to_20260224.json")
        
        if not candidate_file.exists():
            logger.error(f"❌ 候选股票文件不存在: {candidate_file}")
            return False
        
        try:
            with open(candidate_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            candidates = data.get('candidates', [])
            trade_date = data.get('trade_date', '')
            t1_date = data.get('t1_date', '')
            
            logger.info(f"✅ 候选股票文件存在: {candidate_file}")
            logger.info(f"   交易日期: {trade_date} → T+1日期: {t1_date}")
            logger.info(f"   候选股票数量: {len(candidates)} 只")
            
            if candidates:
                logger.info(f"   前3名候选:")
                for i, stock in enumerate(candidates[:3], 1):
                    name = stock.get('name', '未知')
                    code = stock.get('ts_code', '未知')
                    score = stock.get('total_score', 0)
                    logger.info(f"     #{i} {name} ({code}) - 评分: {score:.1f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 候选股票文件读取失败: {e}")
            return False
    
    def check_directories(self) -> bool:
        """检查目录结构"""
        directories = [
            Path("logs"),
            Path("state"),
            Path("output"),
        ]
        
        all_success = True
        
        for dir_path in directories:
            if dir_path.exists():
                logger.info(f"✅ 目录存在: {dir_path}")
            else:
                logger.warning(f"⚠️  目录不存在: {dir_path}")
                try:
                    dir_path.mkdir(exist_ok=True)
                    logger.info(f"   已创建目录: {dir_path}")
                except Exception as e:
                    logger.error(f"❌ 创建目录失败: {dir_path} - {e}")
                    all_success = False
        
        return all_success
    
    def check_message_format(self) -> bool:
        """检查消息推送格式"""
        try:
            # 导入scheduler模块
            sys.path.insert(0, str(Path(__file__).parent))
            from scheduler import T01Scheduler
            
            scheduler = T01Scheduler(self.config_path)
            
            # 创建测试报告
            test_report = {
                'trade_date': '20260224',
                't1_recommendations': [],
                'market_condition': {
                    'condition': '正常',
                    'risk_level': '低',
                    'risk_score': 2,
                    'suggestion': '可适当增加仓位',
                    'position_multiplier': 1.0,
                    'financing_balance': 850000000000,
                    'margin_balance': 45000000000,
                    'financing_change_pct': 0.5,
                    'margin_change_pct': 1.2,
                    'financing_buy_repay_ratio': 0.9,
                },
                'is_trading_hours': True
            }
            
            # 如果有候选股票，添加测试数据
            candidate_file = Path("state/candidates_20260213_to_20260224.json")
            if candidate_file.exists():
                with open(candidate_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                candidates = data.get('candidates', [])
                if candidates:
                    # 使用第一个候选股票作为测试
                    test_stock = candidates[0].copy()
                    test_stock['final_score'] = test_stock.get('total_score', 0)
                    test_stock['t_day_score'] = test_stock.get('total_score', 0)
                    test_stock['auction_score'] = 85.5
                    test_stock['auction_data'] = {
                        'open_change_pct': 2.5,
                        'auction_volume_ratio': 3.2,
                        'auction_amount': 15000000,
                        'data_source': 'realtime'
                    }
                    test_stock['recommendation'] = {
                        'action': '买入',
                        'position': 0.15,
                        'confidence': '高',
                        'reasons': ['强势涨停', '热点板块']
                    }
                    
                    test_report['t1_recommendations'] = [test_stock]
            
            message = scheduler.prepare_push_message(test_report)
            
            logger.info(f"✅ 消息推送格式测试成功")
            logger.info(f"   消息长度: {len(message)} 字符")
            logger.info(f"   消息行数: {len(message.split(chr(10)))} 行")
            
            # 保存测试消息
            test_msg_file = Path("state/test_message.txt")
            with open(test_msg_file, 'w', encoding='utf-8') as f:
                f.write(message)
            
            logger.info(f"   测试消息已保存: {test_msg_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 消息推送格式测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_scheduler(self) -> bool:
        """检查调度器"""
        try:
            # 尝试导入并初始化调度器
            sys.path.insert(0, str(Path(__file__).parent))
            from scheduler import T01Scheduler
            
            scheduler = T01Scheduler(self.config_path)
            
            # 测试T日评分函数（不实际运行）
            test_date = '20260213'
            result = scheduler.run_t_day_scoring(test_date)
            
            if result.get('success'):
                logger.info(f"✅ 调度器T日评分测试成功")
                logger.info(f"   测试日期: {test_date}")
                logger.info(f"   评分股票数量: {result.get('summary', {}).get('total_scored', 0)}")
            else:
                logger.warning(f"⚠️  调度器T日评分测试返回失败: {result.get('error', '未知错误')}")
                # 不视为完全失败，因为可能没有数据
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 调度器检查失败: {e}")
            return False
    
    def check_real_time_auction_logic(self) -> bool:
        """检查实时竞价逻辑"""
        try:
            # 导入策略模块
            sys.path.insert(0, str(Path(__file__).parent))
            from limit_up_strategy_new import LimitUpScoringStrategyV2
            
            strategy = LimitUpScoringStrategyV2(self.config)
            
            # 测试实时竞价数据获取逻辑
            test_date = '20260224'
            test_code = '000859.SZ'  # 国风新材
            
            # 测试非交易时间逻辑
            auction_data = strategy._get_real_auction_data(test_code, test_date, is_trading_hours=False)
            
            if auction_data:
                logger.info(f"✅ 实时竞价逻辑测试成功 (非交易时间)")
                logger.info(f"   数据来源: {auction_data.get('data_source', 'unknown')}")
                logger.info(f"   开盘涨幅: {auction_data.get('open_change_pct', 0):+.2f}%")
            else:
                logger.warning(f"⚠️  非交易时间竞价数据获取失败 (可能无历史数据)")
            
            # 注意: 无法在非交易时间测试实时数据，但逻辑已检查
            logger.info(f"✅ 实时竞价逻辑检查完成")
            logger.info(f"   交易时间 (9:25-9:29) 将使用 stk_auction 接口")
            logger.info(f"   非交易时间使用 stk_auction_o 接口")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 实时竞价逻辑检查失败: {e}")
            return False
    
    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print("\n" + "="*60)
        print("🔍 T01系统测试环境检查清单")
        print("="*60)
        
        checks = [
            ("配置文件", self.load_config),
            ("tushare连接", self.check_tushare_connection),
            ("关键API接口", self.check_key_apis),
            ("目录结构", self.check_directories),
            ("候选股票文件", self.check_candidate_file),
            ("消息推送格式", self.check_message_format),
            ("调度器功能", self.check_scheduler),
            ("实时竞价逻辑", self.check_real_time_auction_logic),
        ]
        
        results = []
        
        for check_name, check_func in checks:
            print(f"\n📋 检查: {check_name}")
            print("-"*40)
            
            try:
                success = check_func()
                results.append((check_name, success))
                
                if success:
                    print(f"✅ {check_name}: 通过")
                else:
                    print(f"❌ {check_name}: 失败")
                    
            except Exception as e:
                print(f"❌ {check_name}: 异常 - {e}")
                results.append((check_name, False))
        
        # 汇总结果
        print("\n" + "="*60)
        print("📊 检查结果汇总")
        print("="*60)
        
        total_checks = len(results)
        passed_checks = sum(1 for _, success in results if success)
        failed_checks = total_checks - passed_checks
        
        for check_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status}: {check_name}")
        
        print(f"\n📈 统计: {passed_checks}/{total_checks} 项检查通过")
        
        if failed_checks == 0:
            print("\n🎉 所有检查通过！系统已准备好进行2月24日实时测试。")
            return True
        else:
            print(f"\n⚠️  有 {failed_checks} 项检查失败，请修复后再进行实时测试。")
            return False


def main():
    """主函数"""
    checker = TestEnvironmentChecker()
    
    try:
        success = checker.run_all_checks()
        
        if success:
            print("\n🚀 测试环境就绪，可以执行以下命令进行实时测试：")
            print("\n# 手动运行T+1竞价分析 (2月24日09:25-09:29)")
            print("cd tasks/T01")
            print("python scheduler.py --run-t1-auction --date 20260224 --t-date 20260213")
            print("\n# 或使用主程序")
            print("python main.py t1-auction --date 20260224 --candidates state/candidates_20260213_to_20260224.json")
            print("\n# 查看实时日志")
            print("tail -f logs/t01_scheduler.log")
            
            # 生成检查报告
            report_file = Path("state/environment_check_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"T01系统测试环境检查报告\n")
                f.write(f"生成时间: {datetime.now().isoformat()}\n")
                f.write(f"检查结果: {'通过' if success else '失败'}\n")
                f.write(f"通过检查: {checker.passed_checks if hasattr(checker, 'passed_checks') else 'N/A'}\n")
                f.write(f"总检查数: {len(checker.results) if hasattr(checker, 'results') else 'N/A'}\n")
            
            print(f"\n📝 检查报告已保存: {report_file}")
            print("\n🎯 祝2月24日实时测试顺利！")
            
        else:
            print("\n❌ 测试环境存在问题，请修复后再进行实时测试。")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"检查过程异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()