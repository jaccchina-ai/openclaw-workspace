#!/usr/bin/env python3
"""
T01进化阶段提醒脚本
定时发送阶段进展和提醒，确保按计划完成三个阶段的进化任务
"""

import os
import sys
from datetime import datetime, timedelta
import subprocess
import json
from pathlib import Path

# 添加当前目录到路径，确保可以导入T01模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def get_current_stage_info():
    """获取当前进化阶段信息"""
    today = datetime.now()
    
    # 进化阶段时间线
    stages = {
        "stage1": {
            "name": "基础强化阶段",
            "start": datetime(2026, 3, 10),
            "end": datetime(2026, 3, 14),
            "goals": [
                "验证PATH修复效果（T日评分消息发送）",
                "集成成功标准（T+2收盘/T+1开盘>1.03%）",
                "实现'连续3天无选股'预警机制",
                "运行第一次MoA策略反思"
            ],
            "priority": "P0"
        },
        "stage2": {
            "name": "因子系统升级阶段", 
            "start": datetime(2026, 3, 17),
            "end": datetime(2026, 3, 21),
            "goals": [
                "IC值监控模块（每周因子信息系数回测）",
                "因子正交化处理（PCA提取独立信息）",
                "交易数据驱动权重优化",
                "Alpha Decay应对机制"
            ],
            "priority": "P1"
        },
        "stage3": {
            "name": "全系统进化阶段",
            "start": datetime(2026, 3, 24),
            "end": datetime(2026, 3, 31),
            "goals": [
                "Alpha因子挖掘引擎",
                "深度归因分析仪表板",
                "自适应阈值系统",
                "全自动进化闭环"
            ],
            "priority": "P2"
        }
    }
    
    # 判断当前阶段
    current_stage = None
    days_until_end = None
    
    for stage_key, stage_info in stages.items():
        if stage_info["start"] <= today <= stage_info["end"]:
            current_stage = stage_key
            days_until_end = (stage_info["end"] - today).days
            break
    
    # 判断是否在阶段结束前2天
    stage_ending_soon = False
    stage_ending_info = None
    
    for stage_key, stage_info in stages.items():
        days_left = (stage_info["end"] - today).days
        if 0 <= days_left <= 2:
            stage_ending_soon = stage_key
            stage_ending_info = stage_info
            break
    
    return {
        "today": today.strftime("%Y-%m-%d"),
        "current_stage": current_stage,
        "current_stage_info": stages.get(current_stage) if current_stage else None,
        "days_until_end": days_until_end,
        "stage_ending_soon": stage_ending_soon,
        "stage_ending_info": stage_ending_info,
        "all_stages": stages
    }

def send_feishu_message(message):
    """发送飞书消息"""
    try:
        # 确保PATH包含Node.js路径
        env = os.environ.copy()
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
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
            print(f"✅ 飞书消息发送成功: {message[:50]}...")
            return True
        else:
            print(f"❌ 飞书消息发送失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 发送消息异常: {e}")
        return False

def check_t01_status():
    """检查T01系统状态"""
    status = {
        "scheduler_running": False,
        "candidate_files": [],
        "last_scoring_date": None
    }
    
    try:
        # 检查调度器状态
        result = subprocess.run(
            ['systemctl', 'is-active', 't01-scheduler'],
            capture_output=True, text=True
        )
        status["scheduler_running"] = result.stdout.strip() == 'active'
        
        # 检查候选股文件
        state_dir = os.path.join(current_dir, "state")
        if os.path.exists(state_dir):
            candidate_files = []
            for f in os.listdir(state_dir):
                if f.startswith("candidates_") and f.endswith(".json"):
                    candidate_files.append(f)
            status["candidate_files"] = sorted(candidate_files)[-3:]  # 最近3个文件
            
            if candidate_files:
                # 从文件名提取最后评分日期
                latest_file = candidate_files[-1]
                # 格式: candidates_YYYYMMDD_to_YYYYMMDD.json
                parts = latest_file.split('_')
                if len(parts) >= 3:
                    status["last_scoring_date"] = parts[1]
        
        # 检查数据库是否存在
        db_path = os.path.join(current_dir, "data", "t01_database.db")
        status["database_exists"] = os.path.exists(db_path)
        
    except Exception as e:
        print(f"❌ 检查T01状态异常: {e}")
    
    return status

def generate_weekly_report(stage_info, t01_status):
    """生成每周进展报告"""
    today_str = datetime.now().strftime("%Y年%m月%d日")
    
    if stage_info["current_stage"]:
        stage = stage_info["current_stage_info"]
        report = f"""📊 **T01进化周报 ({today_str})**

**当前阶段**: {stage['name']} ({stage_info['days_until_end']}天后结束)
**优先级**: {stage['priority']}

**阶段目标**:
{chr(10).join(f'• {goal}' for goal in stage['goals'])}

**T01系统状态**:
• 调度器: {'✅ 运行中' if t01_status['scheduler_running'] else '❌ 已停止'}
• 候选股文件: {len(t01_status['candidate_files'])} 个最新文件
• 最后评分: {t01_status['last_scoring_date'] or '未知'}
• 数据库: {'✅ 存在' if t01_status['database_exists'] else '❌ 缺失'}

**本周重点**:
1. 完成{stage['goals'][0]}
2. 准备下一个阶段({stage_info['days_until_end']}天后开始)

**建议行动**: 按原计划推进，有任何问题及时调整。"""
    else:
        report = f"""📊 **T01进化周报 ({today_str})**

**当前状态**: 阶段间过渡期
**下一个阶段**: {list(stage_info['all_stages'].values())[0]['name']} (即将开始)

**T01系统状态**:
• 调度器: {'✅ 运行中' if t01_status['scheduler_running'] else '❌ 已停止'}
• 候选股文件: {len(t01_status['candidate_files'])} 个最新文件
• 最后评分: {t01_status['last_scoring_date'] or '未知'}
• 数据库: {'✅ 存在' if t01_status['database_exists'] else '❌ 缺失'}

**准备事项**:
1. 回顾已完成阶段的经验教训
2. 准备下一个阶段的技术方案
3. 确保系统资源充足

**建议行动**: 利用过渡期进行系统优化和资源准备。"""
    
    return report

def generate_stage_ending_alert(stage_info, t01_status):
    """生成阶段结束提醒"""
    stage = stage_info["stage_ending_info"]
    days_left = (stage["end"] - datetime.now()).days
    
    alert = f"""🚨 **T01进化阶段即将结束提醒**

**阶段**: {stage['name']}
**剩余时间**: {days_left}天
**优先级**: {stage['priority']}

**待完成目标**:
{chr(10).join(f'• {goal}' for goal in stage['goals'])}

**T01系统状态**:
• 调度器: {'✅ 运行中' if t01_status['scheduler_running'] else '❌ 已停止'}
• 最后评分: {t01_status['last_scoring_date'] or '未知'}

**紧急程度**: {'⚠️ 高 (今天结束)' if days_left == 0 else '⚠️ 中 (明天结束)' if days_left == 1 else '⚠️ 低 (2天后结束)'}

**建议行动**: 
1. 检查未完成目标
2. 必要时调整计划
3. 准备阶段总结报告

请确保按时完成阶段目标，以免影响后续计划。"""
    
    return alert

def main():
    """主函数"""
    print("🔍 开始T01进化提醒检查...")
    
    # 获取阶段信息
    stage_info = get_current_stage_info()
    print(f"📅 今天: {stage_info['today']}")
    print(f"📋 当前阶段: {stage_info['current_stage'] or '无'}") 
    
    # 检查T01系统状态
    t01_status = check_t01_status()
    print(f"⚙️ T01调度器状态: {'✅ 运行中' if t01_status['scheduler_running'] else '❌ 已停止'}")
    
    # 判断需要发送的消息类型
    messages_to_send = []
    
    # 如果是阶段结束前提醒
    if stage_info["stage_ending_soon"]:
        alert_message = generate_stage_ending_alert(stage_info, t01_status)
        messages_to_send.append(("阶段结束提醒", alert_message))
    
    # 如果是周日，发送周报 (0=周一, 6=周日，但cron在周日22:00运行，UTC 14:00)
    # 这里简单判断：如果是周日，发送周报
    today = datetime.now()
    if today.weekday() == 6:  # 周日
        weekly_report = generate_weekly_report(stage_info, t01_status)
        messages_to_send.append(("每周进展报告", weekly_report))
    
    # 如果没有特定消息，发送简要状态更新
    if not messages_to_send:
        status_message = f"""📌 **T01进化状态简报 ({stage_info['today']})**

**当前阶段**: {stage_info['current_stage_info']['name'] if stage_info['current_stage_info'] else '阶段间过渡期'}
**T01状态**: {'✅ 正常' if t01_status['scheduler_running'] else '❌ 异常'}

**最近活动**: 候选股文件: {len(t01_status['candidate_files'])}个
**最后评分**: {t01_status['last_scoring_date'] or '未知'}

按计划推进中，如有问题会及时报告。"""
        messages_to_send.append(("状态简报", status_message))
    
    # 发送所有消息
    success_count = 0
    for msg_type, message in messages_to_send:
        print(f"\n📤 准备发送{msg_type}...")
        if send_feishu_message(message):
            success_count += 1
    
    print(f"\n📊 发送完成: {success_count}/{len(messages_to_send)} 条消息发送成功")
    
    # 记录执行日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "stage_info": {
            "today": stage_info["today"],
            "current_stage": stage_info["current_stage"],
            "days_until_end": stage_info["days_until_end"],
            "stage_ending_soon": stage_info["stage_ending_soon"]
        },
        "t01_status": t01_status,
        "messages_sent": len(messages_to_send),
        "messages_successful": success_count
    }
    
    # 保存日志
    log_dir = os.path.join(current_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "evolution_reminder.log")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
    
    print(f"📝 日志已保存到: {log_file}")
    return success_count == len(messages_to_send)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)