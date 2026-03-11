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

def analyze_no_selection_streak(candidate_files):
    """分析连续无选股的天数"""
    if not candidate_files:
        print("ℹ️ 无候选股文件")
        return {
            "streak_days": 0,
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
            "last_selection_date": None,
            "has_selection_today": False,
            "status": "DATE_PARSE_ERROR"
        }
    
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
                "last_selection_date": latest_date.strftime("%Y-%m-%d"),
                "has_selection_today": True,
                "status": "HAS_SELECTION"
            }
        else:
            print(f"⚠️ 最近文件无候选股: {latest_file}")
            
            # 计算连续无选股天数
            today = datetime.now()
            streak_days = 1  # 最近文件这天无选股
            
            # 检查更早的文件
            for file in candidate_files[1:]:
                file_date = extract_date_from_filename(file)
                if not file_date:
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
                        
                except Exception as e:
                    print(f"❌ 读取文件失败 {file}: {e}")
                    break
            
            return {
                "streak_days": streak_days,
                "last_selection_date": latest_date.strftime("%Y-%m-%d"),
                "has_selection_today": False,
                "status": "NO_SELECTION_STREAK"
            }
            
    except Exception as e:
        print(f"❌ 分析文件失败 {latest_file}: {e}")
        return {
            "streak_days": 0,
            "last_selection_date": latest_date.strftime("%Y-%m-%d") if latest_date else None,
            "has_selection_today": False,
            "status": "FILE_READ_ERROR"
        }

def send_feishu_warning(streak_days, threshold, config):
    """发送飞书预警消息"""
    try:
        # 确保PATH包含Node.js路径
        env = os.environ.copy()
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
        # 构建预警消息
        today_str = datetime.now().strftime("%Y年%m月%d日")
        
        if streak_days >= threshold:
            message = f"""🚨 **T01策略失效预警**

**预警类型**: 连续无选股
**连续天数**: {streak_days}天 (阈值: {threshold}天)
**触发时间**: {today_str}

**当前状态**:
• T01调度器: 运行中
• 候选股文件: 最近{streak_days}天无涨停股
• 策略有效性: ⚠️ 需要人工检查

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
• MoA策略反思将分析此问题
• 周五将进行深度复盘"""
        else:
            message = f"""📊 **T01无选股状态监控**

**连续无选股天数**: {streak_days}天
**预警阈值**: {threshold}天
**剩余天数**: {threshold - streak_days}天
**监控时间**: {today_str}

**当前状态**:
• T01调度器: 运行中
• 候选股文件: 最近{streak_days}天无涨停股
• 策略状态: ⚠️ 监控中

**注意**:
如达到{threshold}天连续无选股，将触发"策略失效预警"。

**建议**:
保持监控，如有异常及时调整。"""
        
        # 使用openclaw发送消息
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
    
    # 只在有连续无选股且不是今天有选股的情况下检查
    if streak_days > 0 and not analysis["has_selection_today"]:
        # 如果达到或超过阈值，发送预警
        if streak_days >= threshold:
            print(f"🚨 触发策略失效预警: 连续{streak_days}天无选股 ≥ 阈值{threshold}天")
            send_feishu_warning(streak_days, threshold, config)
        elif streak_days == threshold - 1:
            print(f"⚠️ 预警前提醒: 连续{streak_days}天无选股，再{1}天将触发预警")
            send_feishu_warning(streak_days, threshold, config)
        else:
            print(f"ℹ️ 监控中: 连续{streak_days}天无选股，未达阈值{threshold}天")
            # 可选：发送状态更新
            # send_feishu_warning(streak_days, threshold, config)
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