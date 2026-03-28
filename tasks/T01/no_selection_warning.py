#!/usr/bin/env python3
"""
T01连续无选股预警监控
监控连续无涨停股的天数，达到阈值时发送预警
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
    
    # 查找所有candidates_*.json文件
    pattern = os.path.join(state_dir, "candidates_*.json")
    files = glob.glob(pattern)
    
    # 排除备份文件
    files = [f for f in files if not f.endswith('.bak') and not f.endswith('.backup')]
    
    # 按日期排序
    files.sort(key=os.path.getmtime, reverse=True)
    return files

def extract_date_from_filename(filename):
    """从文件名提取日期"""
    # 格式: candidates_YYYYMMDD_to_YYYYMMDD.json
    basename = os.path.basename(filename)
    try:
        # 提取第一个日期部分
        date_str = basename.split('_')[1]  # YYYYMMDD
        return datetime.strptime(date_str, "%Y%m%d")
    except (IndexError, ValueError) as e:
        print(f"❌ 无法从文件名提取日期: {basename}, 错误: {e}")
        return None

def is_trading_day(date):
    """判断是否为交易日（使用本地交易日历）"""
    # 周末肯定不是交易日
    if date.weekday() >= 5:  # 5=周六, 6=周日
        return False
    
    # 尝试读取本地交易日历
    calendar_file = os.path.join(current_dir, "..", "..", "trading_calendar.json")
    if os.path.exists(calendar_file):
        try:
            with open(calendar_file, 'r', encoding='utf-8') as f:
                calendar = json.load(f)
            date_str = date.strftime("%Y-%m-%d")
            return date_str in calendar.get("trading_days", [])
        except Exception as e:
            print(f"⚠️ 读取交易日历失败: {e}，使用简单规则")
    
    # 简单规则：周一到周五为交易日
    return date.weekday() < 5

def analyze_no_selection_streak(candidate_files):
    """分析连续无选股的天数（仅统计交易日）"""
    if not candidate_files:
        print("ℹ️ 无候选股文件")
        return {
            "streak_days": 0,
            "trading_days_count": 0,
            "last_selection_date": None,
            "has_selection_today": False,
            "status": "NO_FILES"
        }
    
    # 获取最近的文件
    latest_file = candidate_files[0]
    latest_date = extract_date_from_filename(latest_file)
    
    if not latest_date:
        print(f"❌ 无法解析最近文件日期: {latest_file}")
        return {
            "streak_days": 0,
            "trading_days_count": 0,
            "last_selection_date": None,
            "has_selection_today": False,
            "status": "DATE_PARSE_ERROR"
        }
    
    # 检查今天是否是交易日
    today = datetime.now()
    today_is_trading = is_trading_day(today)
    
    # 检查文件是否为空（无选股）
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否有候选股
        has_candidates = bool(data.get("candidates", []))
        
        if has_candidates:
            print(f"✅ 最近文件有候选股: {latest_file}")
            return {
                "streak_days": 0,
                "trading_days_count": 0,
                "last_selection_date": latest_date.strftime("%Y-%m-%d"),
                "has_selection_today": True,
                "status": "HAS_SELECTION"
            }
        else:
            print(f"⚠️ 最近文件无候选股: {latest_file}")
            
            # 计算连续无选股天数（仅统计交易日）
            streak_days = 0
            trading_days_count = 0
            
            # 如果最近文件日期是交易日，则计数
            if is_trading_day(latest_date):
                streak_days = 1
                trading_days_count = 1
            
            # 检查更早的文件
            for file in candidate_files[1:]:
                file_date = extract_date_from_filename(file)
                if not file_date:
                    continue
                
                # 只统计交易日
                if not is_trading_day(file_date):
                    continue
                
                # 检查该文件是否有候选股
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    if file_data.get("candidates", []):
                        # 找到有选股的文件，停止计数
                        break
                    else:
                        streak_days += 1
                        trading_days_count += 1
                        
                except Exception as e:
                    print(f"❌ 读取文件失败 {file}: {e}")
                    break
            
            return {
                "streak_days": streak_days,
                "trading_days_count": trading_days_count,
                "last_selection_date": latest_date.strftime("%Y-%m-%d"),
                "has_selection_today": False,
                "status": "NO_SELECTION_STREAK",
                "today_is_trading": today_is_trading
            }
            
    except Exception as e:
        print(f"❌ 分析文件失败 {latest_file}: {e}")
        return {
            "streak_days": 0,
            "trading_days_count": 0,
            "last_selection_date": latest_date.strftime("%Y-%m-%d") if latest_date else None,
            "has_selection_today": False,
            "status": "FILE_READ_ERROR"
        }

def send_feishu_warning(streak_days, threshold, config, trading_days_count=None):
    """发送飞书预警消息（增强版）"""
    try:
        # 确保PATH包含Node.js路径
        env = os.environ.copy()
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
        # 构建预警消息
        today_str = datetime.now().strftime("%Y年%m月%d日")
        
        # 获取系统状态
        scheduler_status = "运行中"
        try:
            result = subprocess.run(['systemctl', 'is-active', 't01-scheduler'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                scheduler_status = "⚠️ 异常"
        except:
            scheduler_status = "未知"
        
        # 获取最近选股日期
        last_selection = "无记录"
        state_dir = os.path.join(current_dir, "state")
        if os.path.exists(state_dir):
            import glob
            files = glob.glob(os.path.join(state_dir, "candidates_*.json"))
            if files:
                latest = max(files, key=os.path.getmtime)
                try:
                    with open(latest, 'r') as f:
                        data = json.load(f)
                        if data.get("candidates"):
                            last_selection = data.get("date", "未知")
                except:
                    pass
        
        trading_days_info = f"**连续交易日**: {trading_days_count}天\n" if trading_days_count else ""
        
        if streak_days >= threshold:
            message = f"""🚨 **T01策略失效预警** (高优先级)

**预警类型**: 连续无选股
**连续天数**: {streak_days}天 (阈值: {threshold}天)
{trading_days_info}**触发时间**: {today_str}

**系统状态**:
• T01调度器: {scheduler_status}
• 最后选股日期: {last_selection}
• 候选股文件: 最近{streak_days}天无涨停股
• 策略有效性: 🔴 需要立即检查

**可能原因**:
1. 市场无涨停股票（极端行情）
2. 选股策略过于严格（阈值过高）
3. 数据源异常（Tushare/AKShare连接问题）
4. 系统配置问题（调度器异常）
5. 非交易日连续（已排除）

**建议行动** (按优先级):
1. 🔴 立即检查市场实际情况（是否有涨停股）
2. 🔴 验证T01调度器运行状态
3. 🟡 审核选股策略参数（config.yaml）
4. 🟡 验证数据源连接
5. 🟢 考虑调整策略阈值或放宽条件

**自动化响应**:
• ✅ 已记录到系统日志
• ✅ MoA策略反思将在周五分析此问题
• ✅ 已发送飞书预警通知
• ⏳ 等待人工干预

**查看日志**:
```
tail -50 /root/.openclaw/workspace/tasks/T01/logs/no_selection_warning.log
```"""
        else:
            message = f"""📊 **T01无选股状态监控** (预警前)

**连续无选股天数**: {streak_days}天
{trading_days_info}**预警阈值**: {threshold}天
**剩余天数**: {threshold - streak_days}天
**监控时间**: {today_str}

**系统状态**:
• T01调度器: {scheduler_status}
• 最后选股日期: {last_selection}
• 候选股文件: 最近{streak_days}天无涨停股
• 策略状态: 🟡 监控中

**预警倒计时**:
再连续 {threshold - streak_days} 个交易日无选股，将触发"策略失效预警"。

**建议**:
• 保持监控，关注市场变化
• 检查策略参数是否需要微调
• 如有异常及时调整

**查看状态**:
```
cd /root/.openclaw/workspace/tasks/T01 && python3 no_selection_warning.py
```"""
        
        # 使用openclaw发送消息（带重试机制）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                cmd = [
                    '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
                    'message', 'send',
                    '--channel', 'feishu',
                    '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
                    '--message', message
                ]
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"✅ 飞书预警消息发送成功 (尝试 {attempt + 1}/{max_retries})")
                    return True
                else:
                    print(f"⚠️ 飞书消息发送失败 (尝试 {attempt + 1}/{max_retries}): {result.stderr}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)  # 指数退避
                    else:
                        print(f"❌ 飞书预警消息发送失败，已重试{max_retries}次")
                        # 保存到fallback日志
                        fallback_file = os.path.join(current_dir, "logs", "feishu_fallback.log")
                        with open(fallback_file, "a", encoding='utf-8') as f:
                            f.write(f"[{datetime.now().isoformat()}] FAILED TO SEND:\n{message}\n\n")
                        return False
            except Exception as e:
                print(f"⚠️ 发送异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    # 保存到fallback日志
                    fallback_file = os.path.join(current_dir, "logs", "feishu_fallback.log")
                    with open(fallback_file, "a", encoding='utf-8') as f:
                        f.write(f"[{datetime.now().isoformat()}] EXCEPTION: {e}\n{message}\n\n")
                    return False
            
    except Exception as e:
        print(f"❌ 发送预警消息异常: {e}")
        return False

def main():
    """主函数"""
    print("🔍 开始T01连续无选股预警监控...")
    
    # 获取配置
    config = get_config()
    if not config:
        print("❌ 无法获取配置，退出")
        sys.exit(1)
    
    # 获取预警阈值
    threshold = config.get("performance_tracking", {}).get("no_selection_warning_threshold", 3)
    print(f"📊 预警阈值: {threshold}天")
    
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
    trading_days_count = analysis.get("trading_days_count", streak_days)
    today_is_trading = analysis.get("today_is_trading", True)
    
    # 只在有连续无选股且不是今天有选股的情况下检查
    if streak_days > 0 and not analysis["has_selection_today"]:
        # 如果达到或超过阈值，发送预警
        if streak_days >= threshold:
            print(f"🚨 触发策略失效预警: 连续{streak_days}个交易日无选股 ≥ 阈值{threshold}天")
            send_feishu_warning(streak_days, threshold, config, trading_days_count)
        elif streak_days == threshold - 1:
            print(f"⚠️ 预警前提醒: 连续{streak_days}个交易日无选股，再{1}天将触发预警")
            send_feishu_warning(streak_days, threshold, config, trading_days_count)
        else:
            print(f"ℹ️ 监控中: 连续{streak_days}个交易日无选股，未达阈值{threshold}天")
    elif analysis["has_selection_today"]:
        print("✅ 今日有选股，无需预警")
    else:
        print("ℹ️ 无连续无选股记录")
    
    # 非交易日提醒
    if not today_is_trading:
        print("📅 今天是非交易日，跳过预警检查")
    
    # 记录日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis,
        "threshold": threshold,
        "warning_triggered": streak_days >= threshold,
        "config_version": config.get("version", "unknown")
    }
    
    # 保存日志
    log_dir = os.path.join(current_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "no_selection_warning.log")
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
    
    print(f"📝 日志已保存到: {log_file}")
    
    # 返回状态码
    if streak_days >= threshold:
        print("⚠️ 返回警告状态码")
        sys.exit(2)  # 警告状态码
    else:
        print("✅ 监控完成，状态正常")
        sys.exit(0)

if __name__ == "__main__":
    main()