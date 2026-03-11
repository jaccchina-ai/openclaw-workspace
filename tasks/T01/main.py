#!/usr/bin/env python3
"""
T01 龙头战法选股主程序 - 涨停股评分系统
"""

import argparse
import logging
import sys
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import tushare as ts

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from limit_up_strategy_new import LimitUpScoringStrategyV2 as LimitUpScoringStrategy
from output_formatter import OutputFormatter


def setup_logging(level=logging.INFO):
    """配置日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('t01_limit_up.log', encoding='utf-8')
        ]
    )


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='涨停股评分系统 T01',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s t-day --date 20240222     # T日涨停股评分
  %(prog)s t1-auction --date 20240223 --candidates candidates.json  # T+1竞价评分
  %(prog)s full-pipeline --t-date 20240222 --t1-date 20240223  # 完整流程
  %(prog)s test-api                   # 测试API连接
  %(prog)s config                     # 查看配置
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['t-day', 't1-auction', 'full-pipeline', 'test-api', 'config', 'run'],
        help='运行模式'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    
    parser.add_argument(
        '--date',
        help='交易日期 (格式: YYYYMMDD), 用于t-day模式'
    )
    
    parser.add_argument(
        '--t-date',
        help='T日日期 (格式: YYYYMMDD), 用于full-pipeline模式'
    )
    
    parser.add_argument(
        '--t1-date',
        help='T+1日日期 (格式: YYYYMMDD), 用于full-pipeline模式'
    )
    
    parser.add_argument(
        '--candidates',
        help='T日候选股票JSON文件路径, 用于t1-auction模式'
    )
    
    parser.add_argument(
        '--output',
        choices=['table', 'json', 'csv', 'all'],
        default='table',
        help='输出格式 (默认: table)'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='保存结果到文件'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    return parser.parse_args()


def get_trade_date(date_str: str = None, offset: int = 0) -> str:
    """获取交易日期"""
    if date_str:
        return date_str
    
    # 如果没有提供日期，获取最近交易日
    pro = ts.pro_api()
    today = datetime.now().strftime('%Y%m%d')
    
    # 获取最近30天交易日历
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    cal = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=today)
    trade_dates = cal[cal['is_open'] == 1]['cal_date'].tolist()
    
    if offset < 0 and abs(offset) < len(trade_dates):
        return trade_dates[-offset]  # offset为负，-offset为正索引
    
    # 默认返回最近交易日 (列表是降序的，trade_dates[0]是最新的)
    return trade_dates[0] if trade_dates else today


def run_t_day_scoring(config: dict, trade_date: str, args):
    """运行T日涨停股评分"""
    logger = logging.getLogger(__name__)
    logger.info(f"开始T日涨停股评分 (日期: {trade_date})")
    
    # 初始化策略
    strategy = LimitUpScoringStrategy(config)
    
    # 获取涨停股票
    limit_up_stocks = strategy.get_limit_up_stocks(trade_date)
    
    if limit_up_stocks.empty:
        logger.warning(f"日期 {trade_date} 没有涨停股票")
        return {"error": "没有涨停股票"}
    
    logger.info(f"获取到 {len(limit_up_stocks)} 只涨停股票")
    
    # 计算评分
    scored_stocks = strategy.calculate_t_day_score(limit_up_stocks, trade_date)
    
    if scored_stocks.empty:
        logger.warning("评分失败，没有有效结果")
        return {"error": "评分失败"}
    
    logger.info(f"成功评分 {len(scored_stocks)} 只股票")
    
    # 选择前N名候选
    top_n = config['strategy']['output'].get('top_n_candidates', 5)
    candidates = scored_stocks.head(top_n).copy()
    
    # 准备输出
    output_formatter = OutputFormatter(config)
    
    # 转换为输出格式
    output_data = {
        'trade_date': trade_date,
        'candidates': candidates.to_dict('records'),
        'summary': {
            'total_limit_up': len(limit_up_stocks),
            'total_scored': len(scored_stocks),
            'top_n_selected': len(candidates),
            'top_score': candidates.iloc[0]['total_score'] if not candidates.empty else 0,
            'generated_at': datetime.now().isoformat()
        }
    }
    
    return output_data


def run_t1_auction_scoring(config: dict, trade_date: str, candidates_data: dict, args):
    """运行T+1日竞价评分"""
    logger = logging.getLogger(__name__)
    logger.info(f"开始T+1日竞价评分 (日期: {trade_date})")
    
    # 初始化策略
    strategy = LimitUpScoringStrategy(config)
    
    # 将候选数据转换为DataFrame
    candidates_df = pd.DataFrame(candidates_data.get('candidates', []))
    
    if candidates_df.empty:
        logger.warning("没有候选股票数据")
        return {"error": "没有候选股票数据"}
    
    logger.info(f"分析 {len(candidates_df)} 只候选股票的竞价数据")
    
    # 分析竞价数据
    t1_results = strategy.analyze_t1_auction(candidates_df, trade_date)
    
    if t1_results.empty:
        logger.warning("竞价分析失败")
        return {"error": "竞价分析失败"}
    
    logger.info(f"成功分析 {len(t1_results)} 只股票的竞价数据")
    
    # 生成最终报告
    final_report = strategy.generate_final_report(candidates_df, t1_results)
    
    return final_report


def run_full_pipeline(config: dict, t_date: str, t1_date: str, args):
    """运行完整流程"""
    logger = logging.getLogger(__name__)
    logger.info(f"运行完整流程: T日={t_date}, T+1日={t1_date}")
    
    # 第一步: T日评分
    t_day_results = run_t_day_scoring(config, t_date, args)
    
    if 'error' in t_day_results:
        logger.error(f"T日评分失败: {t_day_results['error']}")
        return t_day_results
    
    # 保存T日结果
    if args.save or args.output in ['json', 'all']:
        output_file = f"t_day_results_{t_date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(t_day_results, f, ensure_ascii=False, indent=2)
        logger.info(f"T日结果已保存: {output_file}")
    
    # 第二步: T+1日竞价评分
    t1_results = run_t1_auction_scoring(config, t1_date, t_day_results, args)
    
    if 'error' in t1_results:
        logger.error(f"T+1日评分失败: {t1_results['error']}")
        return t1_results
    
    # 合并结果
    final_result = {
        't_day': t_day_results,
        't1_auction': t1_results,
        'pipeline_completed': True,
        'completed_at': datetime.now().isoformat()
    }
    
    return final_result


def test_api_connection(config: dict):
    """测试API连接"""
    logger = logging.getLogger(__name__)
    logger.info("测试tushare API连接...")
    
    token = config['api']['api_key']
    ts.set_token(token)
    pro = ts.pro_api()
    
    results = {
        'success': False,
        'tests': {},
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # 测试交易日历
        cal = pro.trade_cal(exchange='SSE', start_date='20240222', end_date='20240222')
        results['tests']['trade_cal'] = {
            'success': True,
            'records': len(cal)
        }
        
        # 测试日线数据
        daily = pro.daily(trade_date='20240222', fields='ts_code,trade_date,close')
        results['tests']['daily'] = {
            'success': True,
            'records': len(daily)
        }
        
        # 测试涨停板数据
        try:
            limit_list = pro.limit_list(trade_date='20240222', limit_type='U')
            results['tests']['limit_list'] = {
                'success': True,
                'records': len(limit_list)
            }
        except Exception as e:
            results['tests']['limit_list'] = {
                'success': False,
                'error': str(e)
            }
        
        # 测试资金流数据
        try:
            moneyflow = pro.moneyflow(trade_date='20240222')
            results['tests']['moneyflow'] = {
                'success': True,
                'records': len(moneyflow),
                'fields': moneyflow.columns.tolist()[:10] if not moneyflow.empty else []
            }
        except Exception as e:
            results['tests']['moneyflow'] = {
                'success': False,
                'error': str(e)
            }
        
        results['success'] = True
        results['message'] = "API测试完成"
        
        logger.info("✅ API测试完成")
        
    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
        logger.error(f"❌ API测试失败: {e}")
    
    return results


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    # 检查配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        print(f"请创建配置文件: {config_path}")
        print("可复制 config.example.yaml 并修改")
        sys.exit(1)
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if args.mode == 'config':
        # 显示配置
        print("当前配置:")
        print(yaml.dump(config, allow_unicode=True, default_flow_style=False))
        return
    
    if args.mode == 'test-api':
        # 测试API连接
        results = test_api_connection(config)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    
    # 根据模式执行
    if args.mode == 't-day':
        # T日涨停股评分
        trade_date = get_trade_date(args.date, offset=0)
        results = run_t_day_scoring(config, trade_date, args)
        
    elif args.mode == 't1-auction':
        # T+1日竞价评分
        if not args.candidates:
            logger.error("需要提供候选股票文件 (--candidates)")
            sys.exit(1)
        
        trade_date = get_trade_date(args.date, offset=0)
        
        # 加载候选股票数据
        with open(args.candidates, 'r', encoding='utf-8') as f:
            candidates_data = json.load(f)
        
        results = run_t1_auction_scoring(config, trade_date, candidates_data, args)
        
    elif args.mode == 'full-pipeline':
        # 完整流程
        if not args.t_date or not args.t1_date:
            logger.error("需要提供T日(--t-date)和T+1日(--t1-date)")
            sys.exit(1)
        
        results = run_full_pipeline(config, args.t_date, args.t1_date, args)
        
    elif args.mode == 'run':
        # 默认运行模式：使用最近两个交易日
        pro = ts.pro_api()
        today = datetime.now().strftime('%Y%m%d')
        
        # 获取最近两个交易日
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
        cal = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=today)
        trade_dates = cal[cal['is_open'] == 1]['cal_date'].tolist()
        
        if len(trade_dates) >= 2:
            t_date = trade_dates[-2]  # 倒数第二个交易日 (T日)
            t1_date = trade_dates[-1]  # 倒数第一个交易日 (T+1日)
            
            logger.info(f"自动选择日期: T日={t_date}, T+1日={t1_date}")
            results = run_full_pipeline(config, t_date, t1_date, args)
        else:
            logger.error("无法获取足够的交易日")
            results = {"error": "交易日不足"}
    
    else:
        logger.error(f"未知模式: {args.mode}")
        sys.exit(1)
    
    # 输出结果
    output_formatter = OutputFormatter(config)
    
    if 'error' in results:
        print(f"\n❌ 错误: {results['error']}")
        sys.exit(1)
    
    # 表格输出
    if args.output in ['table', 'all']:
        print("\n" + "="*60)
        
        if args.mode == 't-day':
            print(f"T日涨停股评分结果 (日期: {results.get('trade_date', 'N/A')})")
            print("="*60)
            
            candidates = results.get('candidates', [])
            if candidates:
                df = pd.DataFrame(candidates)
                # 显示关键字段
                display_cols = ['ts_code', 'name', 'total_score', 'pct_chg', 'turnover_rate']
                available_cols = [c for c in display_cols if c in df.columns]
                
                if available_cols:
                    print(df[available_cols].to_string(index=False))
                else:
                    print(df.head().to_string(index=False))
            
            summary = results.get('summary', {})
            if summary:
                print("\n" + "-"*60)
                print("摘要:")
                print(f"  涨停股票总数: {summary.get('total_limit_up', 0)}")
                print(f"  成功评分数量: {summary.get('total_scored', 0)}")
                print(f"  入选候选数量: {summary.get('top_n_selected', 0)}")
                print(f"  最高分数: {summary.get('top_score', 0):.1f}")
        
        elif args.mode in ['t1-auction', 'full-pipeline']:
            recommendations = results.get('t1_recommendations', [])
            if recommendations:
                print("T+1日竞价推荐结果")
                print("="*60)
                
                for i, rec in enumerate(recommendations, 1):
                    print(f"\n#{i} {rec.get('name', 'N/A')} ({rec.get('ts_code', 'N/A')})")
                    print(f"  最终分数: {rec.get('final_score', 0):.1f}")
                    
                    rec_info = rec.get('recommendation', {})
                    if rec_info:
                        print(f"  操作建议: {rec_info.get('action', 'N/A')}")
                        print(f"  仓位建议: {rec_info.get('position', 0)*100:.1f}%")
                        print(f"  置信度: {rec_info.get('confidence', 'N/A')}")
                        
                        reasons = rec_info.get('reasons', [])
                        if reasons:
                            print(f"  理由: {', '.join(reasons)}")
            
            market = results.get('market_condition', {})
            if market:
                print("\n" + "-"*60)
                print("市场状况:")
                print(f"  市场状态: {market.get('condition', 'N/A')}")
                print(f"  风险等级: {market.get('risk_level', 'N/A')}")
                print(f"  建议: {market.get('suggestion', 'N/A')}")
    
    # 保存结果
    if args.save or args.output in ['json', 'csv', 'all']:
        if args.output in ['json', 'all']:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"t01_results_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n📁 JSON结果已保存: {output_file}")
        
        if args.output in ['csv', 'all'] and 'candidates' in results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"t01_candidates_{timestamp}.csv"
            
            df = pd.DataFrame(results['candidates'])
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            print(f"📁 CSV结果已保存: {output_file}")
    
    logger.info("任务完成")


if __name__ == "__main__":
    main()