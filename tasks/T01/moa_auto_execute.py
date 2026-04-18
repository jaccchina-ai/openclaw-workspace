#!/usr/bin/env python3
"""
T01 MoA自动策略反思 - 简化自动执行版
每周五自动执行MoA分析，无需确认
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def get_weekly_data():
    """获取本周数据摘要"""
    state_dir = os.path.join(current_dir, "state")
    
    data = {
        "week_start": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "week_end": datetime.now().strftime("%Y-%m-%d"),
        "selection_count": 0,
        "days_with_selection": 0
    }
    
    if os.path.exists(state_dir):
        import glob
        pattern = os.path.join(state_dir, "candidates_*.json")
        files = glob.glob(pattern)
        
        for f in sorted(files)[-7:]:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    file_data = json.load(file)
                    candidates = file_data.get("candidates", [])
                    if candidates:
                        data["days_with_selection"] += 1
                        data["selection_count"] += len(candidates)
            except:
                pass
    
    return data

def execute_moa_analysis(data):
    """自动执行MoA分析"""
    try:
        print("🚀 执行MoA分析...")
        
        # 构建MoA分析提示
        prompt = f"""T01涨停股策略本周表现深度分析

【本周数据摘要】
- 数据周期: {data['week_start']} 至 {data['week_end']}
- 选股天数: {data['days_with_selection']}天
- 候选股总数: {data['selection_count']}只
- 平均每日候选: {data['selection_count'] / max(data['days_with_selection'], 1):.1f}只

【分析要求】
1. 评估当前策略在高频选股环境下的表现
2. 分析连续{data['days_with_selection']}天都有选股可能带来的风险
3. 评估候选数量(日均{data['selection_count'] / max(data['days_with_selection'], 1):.1f}只)是否过多，是否需要提高筛选标准
4. 检查是否存在过度交易风险
5. 建议是否需要调整评分阈值或权重
6. 提出下周策略优化建议

请提供具体的、可执行的建议。"""
        
        # 执行MoA分析
        moa_script = "/root/.openclaw/workspace/skills/moa/scripts/moa.js"
        if os.path.exists(moa_script):
            result = subprocess.run(
                ['node', moa_script, prompt],
                capture_output=True,
                text=True,
                timeout=300,
                cwd="/root/.openclaw/workspace/skills/moa"
            )
            
            if result.returncode == 0:
                print("✅ MoA分析执行成功")
                return True, result.stdout
            else:
                print(f"❌ MoA分析执行失败: {result.stderr}")
                return False, result.stderr
        else:
            print(f"❌ MoA脚本不存在: {moa_script}")
            return False, "MoA脚本不存在"
            
    except Exception as e:
        print(f"❌ 执行MoA分析失败: {e}")
        return False, str(e)

def save_moa_result(data, success, output):
    """保存MoA分析结果"""
    request_dir = os.path.join(current_dir, "moa_requests")
    os.makedirs(request_dir, exist_ok=True)
    
    result_file = os.path.join(request_dir, f"moa_result_{datetime.now().strftime('%Y%m%d')}.json")
    
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "weekly_strategy_review",
        "status": "completed" if success else "failed",
        "auto_executed": True,
        "week_data": data,
        "output_summary": output[:2000] if output else "",
        "prompt_template": "t01_weekly_review"
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    return result_file

def send_feishu_notification(data, success, output, result_file):
    """发送飞书通知"""
    try:
        env = os.environ.copy()
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
        today_str = datetime.now().strftime("%Y年%m月%d日")
        status_icon = "✅" if success else "❌"
        status_text = "已完成" if success else "执行失败"
        
        # 提取关键建议
        key_points = []
        if success and output:
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-', '*')) and len(line) > 10:
                    key_points.append(line[:100])
                if len(key_points) >= 5:
                    break
        
        key_points_text = '\n'.join(key_points) if key_points else '详见完整报告'
        
        message = f"""🧠 **T01策略MoA反思{status_text}** (自动执行)

**分析时间**: {today_str}
**数据周期**: {data['week_start']} 至 {data['week_end']}
**执行模式**: ⚡ 自动执行（已配置）

**本周数据摘要**:
• 选股天数: {data['days_with_selection']}天
• 候选股总数: {data['selection_count']}只
• 平均每日候选: {data['selection_count'] / max(data['days_with_selection'], 1):.1f}只

**MoA分析状态**: {status_icon} {status_text}

**关键建议**:
{key_points_text}

**📁 完整报告**: `{result_file}`

---
*注：根据老板要求，MoA反思已配置为自动执行，不再询问确认。*"""
        
        cmd = [
            '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
            'message', 'send',
            '--channel', 'feishu',
            '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
            '--message', message
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 发送通知失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 T01 MoA自动策略反思")
    print("=" * 60)
    print(f"📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查今天是否是周五
    today = datetime.now()
    if today.weekday() != 4:
        print(f"ℹ️ 今天不是周五(今天是星期{today.weekday() + 1})，跳过")
        return 0
    
    print("✅ 今天是周五，执行MoA策略反思")
    
    # 获取本周数据
    print("📊 获取本周数据...")
    data = get_weekly_data()
    print(f"✅ 本周选股天数: {data['days_with_selection']}")
    print(f"✅ 候选股总数: {data['selection_count']}")
    
    # 执行MoA分析
    print("🧠 执行MoA分析...")
    success, output = execute_moa_analysis(data)
    
    # 保存结果
    print("💾 保存分析结果...")
    result_file = save_moa_result(data, success, output)
    print(f"✅ 结果已保存: {result_file}")
    
    # 发送通知
    print("📱 发送飞书通知...")
    if send_feishu_notification(data, success, output, result_file):
        print("✅ 通知发送成功")
    else:
        print("❌ 通知发送失败")
    
    print("=" * 60)
    print("✅ MoA自动策略反思完成")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
