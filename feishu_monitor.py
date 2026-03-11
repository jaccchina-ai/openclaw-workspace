#!/usr/bin/env python3
"""
飞书消息发送监控器
监控消息发送状态，提供健康度报告和告警
"""

import json
import os
import sys
from datetime import datetime, timedelta
import logging

# 配置
LOG_DIR = "/root/.openclaw/workspace/logs"
FEISHU_STATS_FILE = os.path.join(LOG_DIR, "feishu_stats.json")
FEISHU_FALLBACK_LOG = os.path.join(LOG_DIR, "feishu_fallback.log")
MONITOR_LOG = os.path.join(LOG_DIR, "feishu_monitor.log")

# 创建日志目录
os.makedirs(LOG_DIR, exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(MONITOR_LOG, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_stats():
    """加载统计数据"""
    if os.path.exists(FEISHU_STATS_FILE):
        try:
            with open(FEISHU_STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")
            return None
    else:
        logger.warning(f"统计文件不存在: {FEISHU_STATS_FILE}")
        return None

def analyze_fallback_log():
    """分析fallback日志"""
    if not os.path.exists(FEISHU_FALLBACK_LOG):
        return {
            "exists": False,
            "count": 0,
            "recent_entries": [],
            "has_fallback": False
        }
    
    try:
        with open(FEISHU_FALLBACK_LOG, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析日志条目
        entries = []
        current_entry = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('['):
                # 新的日志条目开始
                if current_entry:
                    entries.append(current_entry)
                timestamp_start = line.find('[') + 1
                timestamp_end = line.find(']')
                timestamp = line[timestamp_start:timestamp_end] if timestamp_end > timestamp_start else "unknown"
                
                current_entry = {
                    "timestamp": timestamp,
                    "reason": line.split("FALLBACK - ")[1] if "FALLBACK - " in line else line,
                    "message": ""
                }
            elif line and current_entry:
                if not current_entry.get("message"):
                    current_entry["message"] = line
                elif line != '-'*40:
                    current_entry["message"] += f"\n{line}"
        
        if current_entry:
            entries.append(current_entry)
        
        # 获取最近24小时的条目
        recent_entries = []
        now = datetime.now()
        
        for entry in entries[-10:]:  # 只取最近10条
            try:
                entry_time = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
                if (now - entry_time).days <= 1:
                    recent_entries.append(entry)
            except:
                recent_entries.append(entry)  # 包含无法解析时间戳的条目
        
        return {
            "exists": True,
            "count": len(entries),
            "recent_count": len(recent_entries),
            "recent_entries": recent_entries[:3],  # 只显示最近3条
            "has_fallback": len(recent_entries) > 0
        }
        
    except Exception as e:
        logger.error(f"分析fallback日志失败: {e}")
        return {
            "exists": True,
            "count": 0,
            "recent_entries": [],
            "has_fallback": False
        }

def calculate_health_score(stats, fallback_analysis):
    """计算健康度评分 (0-100)"""
    score = 100
    
    # 基础分数调整
    if stats:
        total_sent = stats.get("total_sent", 0)
        total_failed = stats.get("total_failed", 0)
        
        if total_sent > 0:
            success_rate = (total_sent - total_failed) / total_sent
            # 成功率权重: 50%
            score *= success_rate * 0.5
        
        # 连续失败惩罚: 30%
        consecutive_failures = stats.get("consecutive_failures", 0)
        if consecutive_failures > 0:
            score *= max(0.7, 1.0 - (consecutive_failures * 0.1))
    
    # Fallback日志惩罚: 20%
    if fallback_analysis.get("has_fallback"):
        recent_count = fallback_analysis.get("recent_count", 0)
        if recent_count > 0:
            score *= max(0.8, 1.0 - (recent_count * 0.05))
    
    return round(score, 1)

def generate_report(stats, fallback_analysis, health_score):
    """生成监控报告"""
    report_lines = [
        "📊 飞书消息发送监控报告",
        "=" * 40,
        f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"健康度评分: {health_score}/100",
        ""
    ]
    
    # 统计数据
    report_lines.append("## 📈 发送统计")
    if stats:
        total_sent = stats.get("total_sent", 0)
        total_failed = stats.get("total_failed", 0)
        total_retries = stats.get("total_retries", 0)
        consecutive_failures = stats.get("consecutive_failures", 0)
        
        if total_sent > 0:
            success_rate = ((total_sent - total_failed) / total_sent) * 100
            report_lines.append(f"总发送: {total_sent} 次")
            report_lines.append(f"总失败: {total_failed} 次")
            report_lines.append(f"成功率: {success_rate:.1f}%")
            report_lines.append(f"总重试: {total_retries} 次")
        else:
            report_lines.append("暂无发送记录")
        
        report_lines.append(f"连续失败: {consecutive_failures} 次")
        
        if stats.get("last_success"):
            report_lines.append(f"最后成功: {stats['last_success']}")
        if stats.get("last_failure"):
            report_lines.append(f"最后失败: {stats['last_failure']}")
    else:
        report_lines.append("无统计数据")
    
    report_lines.append("")
    
    # Fallback日志分析
    report_lines.append("## ⚠️  Fallback日志")
    if fallback_analysis.get("exists"):
        if fallback_analysis.get("has_fallback"):
            report_lines.append(f"📝 最近24小时有 {fallback_analysis['recent_count']} 条fallback记录")
            
            # 显示最近几条记录
            if fallback_analysis.get("recent_entries"):
                report_lines.append("最近记录:")
                for i, entry in enumerate(fallback_analysis["recent_entries"], 1):
                    truncated_msg = entry.get("message", "")[:100] + ("..." if len(entry.get("message", "")) > 100 else "")
                    report_lines.append(f"  {i}. [{entry.get('timestamp', 'unknown')}] {entry.get('reason', 'unknown')[:50]}")
                    report_lines.append(f"     消息: {truncated_msg}")
        else:
            report_lines.append("✅ 最近24小时无fallback记录")
    else:
        report_lines.append("📁 Fallback日志文件不存在")
    
    report_lines.append("")
    
    # 健康度评估
    report_lines.append("## 🏥 健康度评估")
    if health_score >= 90:
        report_lines.append("✅ 状态优秀 - 消息发送系统健康")
        report_lines.append("建议: 继续保持当前配置")
    elif health_score >= 70:
        report_lines.append("🟡 状态良好 - 系统基本正常")
        report_lines.append("建议: 监控fallback日志，检查偶尔失败")
    elif health_score >= 50:
        report_lines.append("🟠 状态一般 - 需要注意")
        report_lines.append("建议: 检查网络连接和飞书配置")
    else:
        report_lines.append("🔴 状态不佳 - 需要立即修复")
        report_lines.append("建议: 运行诊断工具: `python3 feishu_connectivity_test.py --full`")
    
    report_lines.append("")
    
    # 行动建议
    report_lines.append("## 🔧 行动建议")
    if fallback_analysis.get("has_fallback"):
        report_lines.append("1. 检查fallback日志中的失败原因")
        report_lines.append("2. 运行完整连接性测试: `python3 feishu_connectivity_test.py --full`")
        report_lines.append("3. 验证Node.js和openclaw配置")
    else:
        report_lines.append("✅ 系统状态正常，无需立即行动")
        report_lines.append("建议: 定期运行此监控脚本")
    
    return "\n".join(report_lines)

def check_cron_health():
    """检查cron任务健康状态"""
    try:
        import subprocess
        
        # 检查crontab中T100任务
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            cron_content = result.stdout
            t100_count = cron_content.count("T100")
            t99_count = cron_content.count("T99")
            t01_count = cron_content.count("T01")
            
            return {
                "has_t100": "T100:" in cron_content,
                "has_t99": "T99:" in cron_content,
                "has_t01": "T01:" in cron_content,
                "t100_count": t100_count,
                "t99_count": t99_count,
                "t01_count": t01_count
            }
        else:
            return {"error": "读取crontab失败"}
            
    except Exception as e:
        return {"error": str(e)}

def main():
    """主函数"""
    print("🔍 开始飞书消息发送监控...")
    
    # 加载数据
    stats = load_stats()
    fallback_analysis = analyze_fallback_log()
    
    # 计算健康度
    health_score = calculate_health_score(stats, fallback_analysis)
    
    # 生成报告
    report = generate_report(stats, fallback_analysis, health_score)
    
    print(report)
    
    # 检查cron健康
    cron_health = check_cron_health()
    print("\n## ⏰ Cron任务状态")
    if "error" in cron_health:
        print(f"❌ Cron检查失败: {cron_health['error']}")
    else:
        print(f"T01任务: {'✅ 存在' if cron_health['has_t01'] else '❌ 缺失'} (共{cron_health['t01_count']}个)")
        print(f"T99任务: {'✅ 存在' if cron_health['has_t99'] else '❌ 缺失'} (共{cron_health['t99_count']}个)")
        print(f"T100任务: {'✅ 存在' if cron_health['has_t100'] else '❌ 缺失'} (共{cron_health['t100_count']}个)")
    
    # 记录到监控日志
    logger.info(f"飞书监控报告生成，健康度: {health_score}/100")
    
    return 0 if health_score >= 70 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  监控被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"监控异常: {e}")
        sys.exit(1)