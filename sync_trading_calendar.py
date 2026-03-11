#!/usr/bin/env python3
"""
交易日历同步脚本
每月从Tushare API同步交易日历，与本地缓存合并
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import time
import signal

# Tushare配置
TUSHARE_TOKEN = "870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab"

def setup_timeout(timeout_seconds=10):
    """设置函数超时机制"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"API调用超时 ({timeout_seconds}秒)")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    return signal.alarm

def fetch_tushare_calendar(year_month=None, timeout=10):
    """
    从Tushare API获取交易日历
    
    Args:
        year_month: 格式为YYYY-MM，如"2026-03"
        timeout: API调用超时时间(秒)
    
    Returns:
        dict: 交易日历数据，格式为 {date_str: is_trading}
    """
    if year_month is None:
        # 获取当前日期和下个月
        today = datetime.now()
        year_month = today.strftime("%Y-%m")
    
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 解析年份和月份
        year, month = map(int, year_month.split('-'))
        
        # 计算开始和结束日期 (整个月)
        start_date = f"{year:04d}{month:02d}01"
        if month == 12:
            end_date = f"{year+1:04d}0101"
        else:
            end_date = f"{year:04d}{month+1:02d}01"
        
        # 设置超时
        cancel_alarm = setup_timeout(timeout)
        
        try:
            # 调用Tushare API
            print(f"🔍 从Tushare获取交易日历: {year_month} (start={start_date}, end={end_date})")
            df = pro.trade_cal(
                exchange="SSE",  # 上交所
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                print("⚠️  Tushare返回空数据")
                return {}
            
            # 解析数据
            calendar_data = {}
            for _, row in df.iterrows():
                date_str = row['cal_date']
                is_open = int(row['is_open']) == 1
                
                # 转换为YYYY-MM-DD格式
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                calendar_data[formatted_date] = is_open
            
            print(f"✅ 成功获取 {len(calendar_data)} 天交易日历数据")
            return calendar_data
            
        finally:
            # 取消超时
            signal.alarm(0)
            
    except TimeoutError as e:
        print(f"❌ Tushare API调用超时: {e}")
        return {}
    except Exception as e:
        print(f"❌ Tushare API调用失败: {e}")
        return {}

def load_local_calendar():
    """加载本地交易日历文件"""
    calendar_path = Path(__file__).parent / "trading_calendar.json"
    
    if not calendar_path.exists():
        print("❌ 本地交易日历文件不存在")
        return {}
    
    try:
        with open(calendar_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 加载本地交易日历，最后更新: {data.get('2026', {}).get('last_updated', '未知')}")
        return data
    except Exception as e:
        print(f"❌ 加载本地交易日历失败: {e}")
        return {}

def save_calendar(data):
    """保存交易日历到文件"""
    calendar_path = Path(__file__).parent / "trading_calendar.json"
    
    try:
        # 创建备份
        backup_path = calendar_path.with_suffix('.json.bak')
        if calendar_path.exists():
            import shutil
            shutil.copy2(calendar_path, backup_path)
            print(f"📋 创建备份文件: {backup_path}")
        
        # 保存新数据
        with open(calendar_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 交易日历保存成功: {calendar_path}")
        return True
    except Exception as e:
        print(f"❌ 保存交易日历失败: {e}")
        return False

def merge_calendars(local_data, tushare_data, year_month):
    """
    合并本地和Tushare交易日历
    
    Args:
        local_data: 本地日历数据
        tushare_data: Tushare API数据 {date: is_trading}
        year_month: 要同步的月份 (YYYY-MM)
    
    Returns:
        tuple: (merged_data, differences)
    """
    if not local_data:
        print("⚠️  本地数据为空，使用Tushare数据")
        return tushare_data, {}
    
    year = year_month.split('-')[0]
    
    # 确保数据结构存在
    if year not in local_data:
        local_data[year] = {
            "trading_days": [],
            "holidays": [],
            "weekends": ["Saturday", "Sunday"],
            "special_schedules": [],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "source": "mixed",
            "notes": "Mixed calendar: local cache + Tushare API sync"
        }
    
    year_data = local_data[year]
    
    # 解析Tushare数据
    tushare_trading_days = [date for date, is_trading in tushare_data.items() if is_trading]
    tushare_non_trading = [date for date, is_trading in tushare_data.items() if not is_trading]
    
    # 提取当前月份的本地数据
    local_trading_days = [d for d in year_data.get("trading_days", []) 
                         if d.startswith(year_month)]
    local_holidays = [d for d in year_data.get("holidays", []) 
                     if d.startswith(year_month)]
    
    # 找出差异
    differences = {
        "trading_days_added": list(set(tushare_trading_days) - set(local_trading_days)),
        "trading_days_removed": list(set(local_trading_days) - set(tushare_trading_days)),
        "holidays_added": list(set(tushare_non_trading) - set(local_holidays)),
        "holidays_removed": list(set(local_holidays) - set(tushare_non_trading))
    }
    
    # 合并数据：Tushare数据覆盖当前月份，其他月份保持原样
    # 移除当前月份的所有数据
    year_data["trading_days"] = [d for d in year_data.get("trading_days", []) 
                               if not d.startswith(year_month)]
    year_data["holidays"] = [d for d in year_data.get("holidays", []) 
                           if not d.startswith(year_month)]
    
    # 添加Tushare数据
    year_data["trading_days"].extend(tushare_trading_days)
    year_data["holidays"].extend(tushare_non_trading)
    
    # 排序和去重
    year_data["trading_days"] = sorted(list(set(year_data["trading_days"])))
    year_data["holidays"] = sorted(list(set(year_data["holidays"])))
    
    # 更新元数据
    year_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    year_data["source"] = "mixed"
    year_data["notes"] = f"混合日历: 本地缓存 + Tushare API同步 (最后同步: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
    
    local_data[year] = year_data
    
    return local_data, differences

def generate_difference_report(differences, year_month):
    """生成差异报告"""
    if not any(differences.values()):
        return "✅ 无差异: Tushare数据与本地缓存完全一致"
    
    report_lines = [f"📊 交易日历差异报告 ({year_month})"]
    report_lines.append("=" * 40)
    
    changes_found = False
    
    if differences["trading_days_added"]:
        report_lines.append(f"📈 新增交易日 ({len(differences['trading_days_added'])}个):")
        for date in sorted(differences["trading_days_added"]):
            report_lines.append(f"  + {date}")
        changes_found = True
    
    if differences["trading_days_removed"]:
        report_lines.append(f"📉 移除交易日 ({len(differences['trading_days_removed'])}个):")
        for date in sorted(differences["trading_days_removed"]):
            report_lines.append(f"  - {date}")
        changes_found = True
    
    if differences["holidays_added"]:
        report_lines.append(f"🏖️  新增假日 ({len(differences['holidays_added'])}个):")
        for date in sorted(differences["holidays_added"]):
            report_lines.append(f"  + {date}")
        changes_found = True
    
    if differences["holidays_removed"]:
        report_lines.append(f"📅 移除假日 ({len(differences['holidays_removed'])}个):")
        for date in sorted(differences["holidays_removed"]):
            report_lines.append(f"  - {date}")
        changes_found = True
    
    if not changes_found:
        report_lines.append("✅ 无实际差异")
    
    return "\n".join(report_lines)

def send_feishu_notification(message, title="交易日历同步报告"):
    """发送飞书通知"""
    try:
        import subprocess
        import os
        
        # 构建openclaw命令
        openclaw_path = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
        
        # 确保环境变量包含Node.js路径
        env = os.environ.copy()
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
        cmd = [
            openclaw_path, "message", "send",
            "--channel", "feishu",
            "--message", f"{title}\n\n{message}"
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 飞书通知发送成功")
            return True
        else:
            print(f"❌ 飞书通知发送失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 发送飞书通知异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 启动交易日历同步任务")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 加载本地日历
    local_data = load_local_calendar()
    if not local_data:
        print("⚠️  无法加载本地日历，使用空数据")
        local_data = {}
    
    # 2. 确定要同步的月份 (下个月)
    today = datetime.now()
    next_month = today.replace(day=1) + timedelta(days=32)
    year_month = next_month.strftime("%Y-%m")
    
    print(f"📅 同步目标月份: {year_month}")
    
    # 3. 从Tushare获取数据 (10秒超时)
    tushare_data = fetch_tushare_calendar(year_month, timeout=10)
    
    if not tushare_data:
        print("❌ Tushare数据获取失败，使用本地缓存")
        
        # 如果没有Tushare数据，只更新元数据
        if "2026" in local_data:
            local_data["2026"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            local_data["2026"]["notes"] = f"本地缓存 (Tushare同步失败: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        
        save_calendar(local_data)
        
        # 发送失败通知
        message = f"❌ Tushare API同步失败\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n月份: {year_month}\n状态: 保持本地缓存"
        send_feishu_notification(message, "交易日历同步失败")
        return 1
    
    # 4. 合并数据
    merged_data, differences = merge_calendars(local_data, tushare_data, year_month)
    
    # 5. 保存合并后的数据
    if not save_calendar(merged_data):
        print("❌ 保存合并数据失败")
        return 2
    
    # 6. 生成并显示差异报告
    report = generate_difference_report(differences, year_month)
    print("\n" + report)
    
    # 7. 发送通知 (如果有差异或重要更新)
    if any(differences.values()):
        print("\n📨 检测到差异，发送飞书通知")
        send_feishu_notification(report, "交易日历更新通知")
    else:
        # 即使没有差异，也发送成功通知
        summary = f"✅ 交易日历同步完成\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n月份: {year_month}\n状态: 数据一致，无更新"
        send_feishu_notification(summary, "交易日历同步成功")
    
    print(f"\n✅ 交易日历同步任务完成")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  任务被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 同步任务异常: {e}")
        
        # 尝试发送错误通知
        try:
            error_msg = f"❌ 交易日历同步异常\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n错误: {str(e)[:200]}"
            send_feishu_notification(error_msg, "交易日历同步异常")
        except:
            pass
        
        sys.exit(3)