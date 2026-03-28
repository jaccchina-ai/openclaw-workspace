#!/usr/bin/env python3
"""
T01 MoA自动调用机制 - 简化版
每周五自动调用MoA进行策略深度反思
"""

import os
import sys
import json
from datetime import datetime, timedelta
import subprocess

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

def save_moa_request(data):
    """保存MoA分析请求，供后续处理"""
    request_dir = os.path.join(current_dir, "moa_requests")
    os.makedirs(request_dir, exist_ok=True)
    
    request_file = os.path.join(request_dir, f"moa_request_{datetime.now().strftime('%Y%m%d')}.json")
    
    request_data = {
        "timestamp": datetime.now().isoformat(),
        "type": "weekly_strategy_review",
        "status": "pending",
        "week_data": data,
        "prompt_template": "t01_weekly_review"
    }
    
    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)
    
    return request_file

def send_notification(data, request_file):
    """发送飞书通知"""
    try:
        env = os.environ.copy()
        node_path = "/root/.nvm/versions/node/v22.22.0/bin"
        if node_path not in env.get('PATH', ''):
            env['PATH'] = node_path + ':' + env.get('PATH', '')
        
        today_str = datetime.now().strftime("%Y年%m月%d日")
        
        message = f"""🧠 **T01策略MoA反思请求已生成**

**分析时间**: {today_str}
**数据周期**: {data['week_start']} 至 {data['week_end']}

**本周数据摘要**:
• 选股天数: {data['days_with_selection']}天
• 候选股总数: {data['selection_count']}只
• 平均每日候选: {data['selection_count'] / max(data['days_with_selection'], 1):.1f}只

**MoA分析请求**:
• 状态: ⏳ 待执行
• 请求文件: `{request_file}`

**建议行动**:
1. 手动执行MoA分析，或
2. 等待系统自动处理

**执行MoA分析命令**:
```bash
cd /root/.openclaw/workspace/skills/moa
node scripts/moa.js "T01策略本周表现分析..."
```

**查看请求详情**:
```bash
cat {request_file}
```"""
        
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
    print("🚀 启动T01 MoA自动策略反思...")
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
    
    # 保存MoA请求
    print("💾 保存MoA分析请求...")
    request_file = save_moa_request(data)
    print(f"✅ 请求已保存: {request_file}")
    
    # 发送通知
    print("📱 发送飞书通知...")
    if send_notification(data, request_file):
        print("✅ 通知发送成功")
    else:
        print("❌ 通知发送失败")
    
    print("✅ MoA自动策略反思完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
