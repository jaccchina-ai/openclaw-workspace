#!/usr/bin/env python3
"""
T01预警系统优化版
增强版连续无选股预警监控，包含更多监控维度
"""

import os
import sys
import json
import glob
from datetime import datetime, timedelta
import subprocess
from pathlib import Path

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def get_config():
    """获取配置文件"""
    config_path = os.path.join(current_dir, "config.yaml")
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return None
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return None

def get_candidate_files():
    """获取候选股文件列表"""
    state_dir = os.path.join(current_dir, "state")
    if not os.path.exists(state_dir):
        print(f"❌ state目录不存在: {state_dir}")
        return []
    
    pattern = os.path.join(state_dir, "candidates_*.json")
    files = glob.glob(pattern)
    files = [f for f in files if not f.endswith('.bak') and not f.endswith('.backup')]
    files.sort(key=os.path.getmtime, reverse=True)
    return files

def extract_date_from_filename(filename):
    """从文件名提取日期"""
    basename = os.path.basename(filename)
    try:
        date_str = basename.split('_')[1]
        return datetime.strptime(date_str, "%Y%m%d")
    except (IndexError, ValueError) as e:
        print(f"❌ 无法从文件名提取日期: {basename}, 错误: {e}")
        return None

def analyze_no_selection_streak(candidate_files):
    """分析连续无选股的天数"""
    if not candidate_files:
        return {"streak_days": 0, "last_selection_date": None, "has_selection_today": False, "status": "NO_FILES"}
    
    latest_file = candidate_files[0]
    latest_date = extract_date_from_filename(latest_file)
    
    if not latest_date:
        return {"streak_days": 0, "last_selection_date": None, "has_selection_today": False, "status": "DATE_PARSE_ERROR"}
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        has_candidates = bool(data.get("candidates", []))
        
        if has_candidates:
            return {"streak_days": 0, "last_selection_date": latest_date.strftime("%Y-%m-%d"), "has_selection_today": True, "status": "HAS_SELECTION"}
        else:
            streak_days = 1
            
            for file in candidate_files[1:]:
                file_date = extract_date_from_filename(file)
                if not file_date:
                    continue
                
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    if file_data.get("candidates", []):
                        break
                    else:
                        streak_days += 1
                except Exception as e:
                    print(f"❌ 读取文件失败 {file}: {e}")
                    break
            
            return {"streak_days": streak_days, "last_selection_date": latest_date.strftime("%Y-%m-%d"), "has_selection_today": False, "status": "NO_SELECTION_STREAK"}
            
    except Exception as e:
        print(f"❌ 分析文件失败 {latest_file}: {e}")
        return {"streak_days": 0, "last_selection_date": latest_date.strftime("%Y-%m-%d"), "has_selection_today": False, "status": "FILE_READ_ERROR"}

def check_trading_calendar():
    """检查交易日历"""
    calendar_file = os.path.join(current_dir, "..", "..", "trading_calendar.json")
    if not os.path.exists(calendar_file):
        return {"status": "NO_CALENDAR", "is_trading_day": True}
    
    try:
        with open(calendar_file, 'r', encoding='utf-8') as f:
            calendar = json.load(f)
        
        today = datetime.now().strftime("%Y-%m-%d")
        is_trading = today in calendar.get("trading_days", [])
        
        return {"status": "OK", "is_trading_day": is_trading, "today": today}
    except Exception as e:
        print(f"⚠️ 读取交易日历失败: {e}")
        return {"status": "ERROR", "is_trading_day": True}

def check_scheduler_status():
    """检查调度器状态"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 't01-scheduler'],
            capture_output=True, text=True, timeout=5
        )
        is_active = result.returncode == 0
        
        return {"status": "active" if is_active else "inactive", "is_healthy": is_active}
    except Exception as e:
        print(f"⚠️ 检查调度器状态失败: {e}")
        return {"status": "UNKNOWN", "is_healthy": True}

def send_feishu_warning(streak_days, threshold, config, additional_info=None):
    """发送飞书预警消息"""
    try:
        env = os.environ.copy()
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
        today_str = datetime.now().strftime("%Y年%m月%d日")
        
        # 构建附加信息
        extra_info = ""
        if additional_info:
            if additional_info.get("scheduler"):
                extra_info += f"\n**调度器状态**: {additional_info['scheduler']['status']}"
            if additional_info.get("trading_day") is not None:
                extra_info += f"\n**今日是否交易日**: {'是' if additional_info['trading_day'] else '否'}"
        
        if streak_days >= threshold:
            message = f"""🚨 **T01策略失效预警** (增强版)

**预警类型**: 连续无选股
**连续天数**: {streak_days}天 (阈值: {threshold}天)
**触发时间**: {today_str}
**预警级别**: 🔴 高

**当前状态**:
• T01调度器: {'运行中' if additional_info and additional_info.get('scheduler', {}).get('is_healthy') else '需检查'}
• 候选股文件: 最近{streak_days}天无涨停股
• 策略有效性: ⚠️ 需要人工检查{extra_info}

**可能原因**:
1. 市场无涨停股票
2. 选股策略过于严格
3. 数据源异常
4. 系统配置问题

**建议行动**:
1. 检查市场实际情况
2. 审核选股策略参数
3. 验证数据源连接
4. 考虑调整策略阈值

**自动化响应**:
• 已记录到系统日志
• 建议立即进行人工检查
• 周五将进行MoA深度复盘"""
        else:
            message = f"""📊 **T01无选股状态监控** (增强版)

**连续无选股天数**: {streak_days}天
**预警阈值**: {threshold}天
**剩余天数**: {threshold - streak_days}天
**监控时间**: {today_str}

**当前状态**:
• T01调度器: {'运行中' if additional_info and additional_info.get('scheduler', {}).get('is_healthy') else '需检查'}
• 候选股文件: 最近{streak_days}天无涨停股
• 策略状态: ⚠️ 监控中{extra_info}

**注意**:
如达到{threshold}天连续无选股，将触发"策略失效预警"。

**建议**:
保持监控，如有异常及时调整。"""
        
        cmd = [
            '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
            'message', 'send',
            '--channel', 'feishu',
            '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
            '--message', message
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ 飞书预警消息发送成功")
            return True
        else:
            print(f"❌ 飞书预警消息发送失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 发送预警消息异常: {e}")
        return False

def main():
    """主函数"""
    print("🔍 启动T01增强版预警监控...")
    
    config = get_config()
    if not config:
        print("❌ 无法获取配置，退出")
        sys.exit(1)
    
    threshold = config.get("performance_tracking", {}).get("no_selection_warning_threshold", 3)
    print(f"📊 预警阈值: {threshold}天")
    
    # 获取附加信息
    additional_info = {}
    
    # 检查调度器状态
    print("🔍 检查调度器状态...")
    scheduler_status = check_scheduler_status()
    additional_info["scheduler"] = scheduler_status
    print(f"✅ 调度器状态: {scheduler_status['status']}")
    
    # 检查交易日历
    print("🔍 检查交易日历...")
    calendar_status = check_trading_calendar()
    additional_info["trading_day"] = calendar_status.get("is_trading_day", True)
    print(f"✅ 今日是否交易日: {calendar_status.get('is_trading_day', True)}")
    
    # 获取候选股文件
    candidate_files = get_candidate_files()
    print(f"📁 找到 {len(candidate_files)} 个候选股文件")
    
    # 分析连续无选股天数
    analysis = analyze_no_selection_streak(candidate_files)
    
    print(f"📈 连续无选股天数: {analysis['streak_days']}天")
    print(f"📅 最后选股日期: {analysis['last_selection_date']}")
    print(f"🎯 今日是否有选股: {analysis['has_selection_today']}")
    
    # 检查是否需要发送预警
    streak_days = analysis["streak_days"]
    
    if streak_days > 0 and not analysis["has_selection_today"]:
        if streak_days >= threshold:
            print(f"🚨 触发策略失效预警: 连续{streak_days}天无选股 ≥ 阈值{threshold}天")
            send_feishu_warning(streak_days, threshold, config, additional_info)
        elif streak_days == threshold - 1:
            print(f"⚠️ 预警前提醒: 连续{streak_days}天无选股，再{1}天将触发预警")
            send_feishu_warning(streak_days, threshold, config, additional_info)
        else:
            print(f"ℹ️ 监控中: 连续{streak_days}天无选股，未达阈值{threshold}天")
    elif analysis["has_selection_today"]:
        print("✅ 今日有选股，无需预警")
    else:
        print("ℹ️ 无连续无选股记录")
    
    # 记录日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis,
        "threshold": threshold,
        "warning_triggered": streak_days >= threshold,
        "scheduler_status": scheduler_status,
        "calendar_status": calendar_status,
        "config_version": config.get("version", "unknown")
    }
    
    log_dir = os.path.join(current_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "enhanced_warning.log")
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
    
    print(f"📝 日志已保存到: {log_file}")
    
    if streak_days >= threshold:
        print("⚠️ 返回警告状态码")
        sys.exit(2)
    else:
        print("✅ 监控完成，状态正常")
        sys.exit(0)

if __name__ == "__main__":
    main()
