#!/usr/bin/env python3
"""
T01 调度器诊断工具
检查调度器运行状态、候选股文件、竞价接口等关键组件
"""

import os
import sys
import json
import subprocess
import psutil
import time
import datetime
from pathlib import Path

# 添加父目录到路径，以便导入 T01 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_scheduler_process():
    """检查调度器进程是否运行"""
    print("🔍 检查调度器进程...")
    
    scheduler_pids = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'scheduler.py' in ' '.join(cmdline):
                scheduler_pids.append(proc.info['pid'])
                print(f"  ✅ 找到调度器进程 PID: {proc.info['pid']}, 命令行: {' '.join(cmdline[:2])}...")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if scheduler_pids:
        return {"status": "running", "pids": scheduler_pids}
    else:
        return {"status": "not_running", "pids": []}

def check_candidate_files():
    """检查候选股票文件"""
    print("\n📋 检查候选股票文件...")
    
    base_dir = Path(__file__).parent
    state_dir = base_dir / "state"
    
    # 查找最新的候选文件
    candidate_files = list(state_dir.glob("candidates_*.json"))
    if not candidate_files:
        return {"status": "no_files", "latest": None, "count": 0}
    
    # 按修改时间排序
    candidate_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_file = candidate_files[0]
    
    # 检查文件内容
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        candidates = data.get('candidates', [])
        t_date = data.get('t_date', '未知')
        t1_date = data.get('t1_date', '未知')
        
        print(f"  ✅ 最新候选文件: {latest_file.name}")
        print(f"     生成日期: T日={t_date}, T+1日={t1_date}")
        print(f"     候选股票数量: {len(candidates)} 只")
        
        if candidates:
            print(f"     前3只股票:")
            for i, stock in enumerate(candidates[:3]):
                print(f"       {i+1}. {stock.get('ts_code', 'N/A')} {stock.get('name', 'N/A')} - 评分: {stock.get('total_score', 0):.2f}")
        
        return {
            "status": "valid",
            "latest_file": str(latest_file),
            "t_date": t_date,
            "t1_date": t1_date,
            "candidate_count": len(candidates),
            "candidates": candidates[:5]  # 返回前5只
        }
    except Exception as e:
        print(f"  ❌ 读取候选文件失败: {e}")
        return {"status": "invalid", "error": str(e)}

def check_tushare_connection():
    """检查 Tushare API 连接"""
    print("\n📡 检查 Tushare API 连接...")
    
    try:
        import tushare as ts
        # 从配置文件读取 token
        import yaml
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        token = config['api']['api_key']
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 测试接口：交易日历
        today = datetime.datetime.now().strftime('%Y%m%d')
        df = pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
        
        if not df.empty:
            is_open = df.iloc[0]['is_open']
            print(f"  ✅ Tushare API 连接正常")
            print(f"     当前日期 {today} 交易日状态: {'开市' if is_open == 1 else '休市'}")
            return {"status": "connected", "trade_date": today, "is_open": bool(is_open)}
        else:
            print(f"  ⚠️  Tushare API 连接正常但返回空数据")
            return {"status": "connected_but_empty"}
    except Exception as e:
        print(f"  ❌ Tushare API 连接失败: {e}")
        return {"status": "failed", "error": str(e)}

def check_auction_interface():
    """检查竞价数据接口"""
    print("\n⏰ 检查竞价数据接口...")
    
    try:
        import tushare as ts
        import yaml
        
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        token = config['api']['api_key']
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 获取当前时间
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 检查是否在竞价时间 (09:15-09:25)
        is_auction_window = False
        if now.hour == 9 and now.minute >= 15 and now.minute <= 29:
            is_auction_window = True
            print(f"  ⚠️  当前时间 {current_time} 在竞价窗口内 (09:15-09:29)")
        else:
            print(f"  ✅ 当前时间 {current_time} 不在竞价窗口内")
        
        # 测试 stk_auction 接口
        try:
            # 使用昨天的日期测试历史接口
            yesterday = (now - datetime.timedelta(days=1)).strftime('%Y%m%d')
            df = pro.stk_auction(trade_date=yesterday, ts_code='000001.SZ')
            
            if df is not None and not df.empty:
                print(f"  ✅ stk_auction 历史接口正常 (日期: {yesterday})")
                return {
                    "status": "available",
                    "auction_window": is_auction_window,
                    "current_time": current_time,
                    "historical_test": "passed"
                }
            else:
                print(f"  ⚠️  stk_auction 历史接口返回空数据")
                return {
                    "status": "empty_response",
                    "auction_window": is_auction_window,
                    "current_time": current_time
                }
        except Exception as e:
            print(f"  ⚠️  stk_auction 接口异常: {e}")
            return {
                "status": "error",
                "auction_window": is_auction_window,
                "current_time": current_time,
                "error": str(e)
            }
            
    except Exception as e:
        print(f"  ❌ 检查竞价接口失败: {e}")
        return {"status": "failed", "error": str(e)}

def check_recent_logs():
    """检查最近运行日志"""
    print("\n📊 检查最近运行日志...")
    
    log_file = Path(__file__).parent / "t01_limit_up.log"
    
    if not log_file.exists():
        print(f"  ⚠️  日志文件不存在: {log_file}")
        return {"status": "no_log_file"}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print(f"  ⚠️  日志文件为空")
            return {"status": "empty"}
        
        # 获取最后10行
        last_lines = lines[-10:]
        
        # 检查错误和警告
        errors = []
        warnings = []
        last_success = None
        
        for line in last_lines:
            if 'ERROR' in line:
                errors.append(line.strip())
            elif 'WARNING' in line:
                warnings.append(line.strip())
            elif '成功' in line or '完成' in line:
                last_success = line.strip()
        
        print(f"  ✅ 日志文件存在，共 {len(lines)} 行")
        print(f"     最后10行中的错误: {len(errors)} 个")
        print(f"     最后10行中的警告: {len(warnings)} 个")
        
        if errors:
            print(f"     最近错误示例:")
            for err in errors[-2:]:
                print(f"       - {err}")
        
        return {
            "status": "valid",
            "total_lines": len(lines),
            "recent_errors": len(errors),
            "recent_warnings": len(warnings),
            "last_success": last_success
        }
    except Exception as e:
        print(f"  ❌ 读取日志失败: {e}")
        return {"status": "read_error", "error": str(e)}

def check_scheduler_config():
    """检查调度器配置"""
    print("\n⚙️  检查调度器配置...")
    
    config_file = Path(__file__).parent / "config.yaml"
    
    if not config_file.exists():
        print(f"  ❌ 配置文件不存在: {config_file}")
        return {"status": "missing"}
    
    try:
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查关键配置
        api_key = config.get('api', {}).get('api_key', '未设置')
        data_source = config.get('data_sources', {}).get('tushare', {}).get('data_source', '未设置')
        top_n = config.get('strategy', {}).get('output', {}).get('top_n_candidates', 5)
        
        print(f"  ✅ 配置文件存在")
        print(f"     API Token: {'已设置' if api_key and api_key != '未设置' else '未设置'}")
        print(f"     数据源: {data_source}")
        print(f"     候选股数量: {top_n}")
        
        # 检查调度时间 (从 scheduler.py 推断)
        scheduler_file = Path(__file__).parent / "scheduler.py"
        if scheduler_file.exists():
            with open(scheduler_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '20:00' in content:
                print(f"     T日评分时间: 20:00")
            if '09:25' in content:
                print(f"     T+1竞价分析时间: 09:25")
        
        return {
            "status": "valid",
            "api_key_set": bool(api_key and api_key != '未设置'),
            "data_source": data_source,
            "top_n_candidates": top_n
        }
    except Exception as e:
        print(f"  ❌ 读取配置失败: {e}")
        return {"status": "invalid", "error": str(e)}

def generate_report():
    """生成诊断报告"""
    print("=" * 60)
    print("T01 调度器诊断报告")
    print(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "checks": {}
    }
    
    # 执行各项检查
    report["checks"]["scheduler_process"] = check_scheduler_process()
    report["checks"]["candidate_files"] = check_candidate_files()
    report["checks"]["tushare_connection"] = check_tushare_connection()
    report["checks"]["auction_interface"] = check_auction_interface()
    report["checks"]["recent_logs"] = check_recent_logs()
    report["checks"]["scheduler_config"] = check_scheduler_config()
    
    # 总体评估
    print("\n" + "=" * 60)
    print("📈 总体评估")
    print("=" * 60)
    
    issues = []
    
    # 检查调度器进程
    if report["checks"]["scheduler_process"]["status"] != "running":
        issues.append("❌ 调度器进程未运行")
    
    # 检查候选文件
    candidate_status = report["checks"]["candidate_files"]["status"]
    if candidate_status == "no_files":
        issues.append("❌ 无候选股票文件")
    elif candidate_status == "invalid":
        issues.append("❌ 候选股票文件无效")
    
    # 检查Tushare连接
    if report["checks"]["tushare_connection"]["status"] != "connected":
        issues.append("⚠️  Tushare API 连接异常")
    
    # 检查竞价接口
    auction_status = report["checks"]["auction_interface"]["status"]
    if auction_status not in ["available", "empty_response"]:
        issues.append("⚠️  竞价数据接口异常")
    
    # 检查日志错误
    if report["checks"]["recent_logs"].get("recent_errors", 0) > 0:
        issues.append(f"⚠️  最近有 {report['checks']['recent_logs']['recent_errors']} 个错误")
    
    if not issues:
        print("✅ 所有检查通过，系统状态正常")
        report["overall_status"] = "healthy"
    else:
        print("⚠️  发现以下问题:")
        for issue in issues:
            print(f"  {issue}")
        report["overall_status"] = "issues_found"
        report["issues"] = issues
    
    # 建议操作
    print("\n💡 建议操作:")
    
    # 如果不在竞价窗口但调度器未运行
    if (report["checks"]["scheduler_process"]["status"] != "running" and 
        not report["checks"]["auction_interface"].get("auction_window", False)):
        print("  • 启动调度器: cd /root/.openclaw/workspace/tasks/T01 && python3 scheduler.py --mode run &")
    
    # 如果没有候选文件
    if candidate_status in ["no_files", "invalid"]:
        print("  • 生成候选股票: cd /root/.openclaw/workspace/tasks/T01 && python3 main.py --mode t-day")
    
    # 如果当前在竞价窗口
    if report["checks"]["auction_interface"].get("auction_window", False):
        print("  • 当前在竞价窗口 (09:15-09:29)，调度器应自动运行竞价分析")
        print("  • 手动运行竞价分析: cd /root/.openclaw/workspace/tasks/T01 && python3 main.py --mode t1-auction --date 20260226 --candidates state/candidates_20260225_to_20260226.json")
    
    print("\n📁 报告保存到: /tmp/t01_diagnostic_report.json")
    
    # 保存报告
    with open('/tmp/t01_diagnostic_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    return report

if __name__ == "__main__":
    try:
        report = generate_report()
        sys.exit(0 if report.get("overall_status") == "healthy" else 1)
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 诊断工具异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)