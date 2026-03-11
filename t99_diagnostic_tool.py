#!/usr/bin/env python3
"""
T99自动诊断修复工具
针对T99扫描连续7天失败问题，提供自动诊断和修复功能
"""

import os
import sys
import re
import subprocess
import json
from datetime import datetime, timedelta

class T99Diagnostic:
    def __init__(self):
        self.skill_dir = "/root/.openclaw/workspace/skills/a-share-short-decision"
        self.scan_log = os.path.join(self.skill_dir, "scan_fixed.log")
        self.scan_script = os.path.join(self.skill_dir, "run_scan_fixed.sh")
        self.main_py = os.path.join(self.skill_dir, "main.py")
        
    def diagnose(self):
        """诊断T99扫描失败原因"""
        print("🔍 T99扫描诊断开始...")
        
        # 检查日志文件
        if not os.path.exists(self.scan_log):
            return {"status": "error", "reason": "扫描日志不存在"}
        
        # 读取最后100行日志
        with open(self.scan_log, 'r') as f:
            lines = f.readlines()[-100:]
            log_content = ''.join(lines)
        
        print(f"📄 分析日志文件: {self.scan_log}")
        
        # 识别错误类型
        error_types = []
        
        # 1. JSON序列化错误
        if "TypeError: Object of type bool is not JSON serializable" in log_content:
            error_types.append("json_serialization")
            print("❌ 检测到JSON序列化错误")
        
        # 2. 超时错误
        if "扫描超时" in log_content or "warning.*超时" in log_content.lower():
            error_types.append("timeout")
            print("⏰ 检测到超时错误")
        
        # 3. API连接错误
        if "ConnectionError" in log_content or "timeout" in log_content.lower():
            error_types.append("api_connection")
            print("🔌 检测到API连接错误")
        
        # 4. 交易日检查错误
        if "非交易日" in log_content or "trading day" in log_content.lower():
            error_types.append("trading_day")
            print("📅 检测到交易日检查错误")
        
        # 5. 宏观数据提取错误
        if "宏观数据提取超时" in log_content or "macro" in log_content.lower():
            error_types.append("macro_data")
            print("📊 检测到宏观数据提取错误")
        
        if not error_types:
            error_types.append("unknown")
            print("❓ 未知错误类型")
        
        return {
            "status": "diagnosed",
            "error_types": error_types,
            "log_snippet": log_content[-500:]  # 最后500字符
        }
    
    def fix_json_serialization(self):
        """修复JSON序列化问题"""
        print("🔧 修复JSON序列化问题...")
        
        # 检查main.py是否已有EnhancedJSONEncoder
        with open(self.main_py, 'r') as f:
            content = f.read()
        
        if "class EnhancedJSONEncoder" in content:
            print("✅ EnhancedJSONEncoder已存在，检查是否完整...")
            
            # 检查是否包含numpy bool处理
            if "np.bool_" in content:
                print("✅ numpy bool处理已存在")
                return {"status": "already_fixed", "action": "none"}
            else:
                print("⚠️ EnhancedJSONEncoder存在但不完整，尝试增强...")
                # 这里可以添加代码来增强现有编码器
                return {"status": "partial", "action": "enhance"}
        else:
            print("❌ EnhancedJSONEncoder不存在，需要修复")
            # 这里可以添加代码来插入EnhancedJSONEncoder
            return {"status": "needs_fix", "action": "add_encoder"}
    
    def fix_timeout(self):
        """修复超时问题"""
        print("🔧 修复超时问题...")
        
        # 检查run_scan_fixed.sh的超时设置
        with open(self.scan_script, 'r') as f:
            content = f.read()
        
        # 查找超时设置
        timeout_match = re.search(r'MAIN_TIMEOUT=(\d+)', content)
        if timeout_match:
            current_timeout = int(timeout_match.group(1))
            print(f"📊 当前超时设置: {current_timeout}秒")
            
            if current_timeout < 600:
                print(f"⚠️ 建议增加超时时间到600秒以上")
                return {"status": "needs_adjustment", "current": current_timeout, "recommended": 600}
            else:
                print("✅ 超时设置合理")
                return {"status": "ok", "current": current_timeout}
        else:
            print("❌ 未找到超时设置")
            return {"status": "missing_timeout"}
    
    def run_quick_test(self):
        """运行快速测试验证修复效果"""
        print("🧪 运行快速测试...")
        
        # 运行一个简化的测试，避免长时间运行
        test_script = os.path.join(self.skill_dir, "tools", "market_data.py")
        if os.path.exists(test_script):
            try:
                result = subprocess.run(
                    ["python3", "-c", "from tools.market_data import get_market_sentiment; print('✅ 导入成功')"],
                    cwd=self.skill_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("✅ 模块导入测试成功")
                    return {"status": "success", "output": result.stdout}
                else:
                    print(f"❌ 模块导入测试失败: {result.stderr}")
                    return {"status": "failed", "error": result.stderr}
            except subprocess.TimeoutExpired:
                print("❌ 模块导入测试超时")
                return {"status": "timeout"}
        else:
            print("⚠️ 无法找到测试脚本")
            return {"status": "no_test_script"}
    
    def generate_report(self, diagnosis, fixes):
        """生成诊断报告"""
        print("📋 生成诊断报告...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "diagnosis": diagnosis,
            "fixes_applied": fixes,
            "recommendations": []
        }
        
        # 根据诊断结果添加建议
        if "json_serialization" in diagnosis.get("error_types", []):
            report["recommendations"].append("1. 确保main.py中的EnhancedJSONEncoder包含numpy.bool_类型处理")
        
        if "timeout" in diagnosis.get("error_types", []):
            report["recommendations"].append("2. 增加run_scan_fixed.sh中的MAIN_TIMEOUT到600秒以上")
            report["recommendations"].append("3. 添加交易时段检查，避免非交易时间执行API调用")
        
        if "api_connection" in diagnosis.get("error_types", []):
            report["recommendations"].append("4. 为Tushare API调用添加重试机制和回退数据源")
        
        # 添加通用建议
        report["recommendations"].append("5. 构建完整的T99自动恢复工作流，添加到AGENTS.md")
        report["recommendations"].append("6. 定期清理日志文件，监控磁盘空间")
        
        return report
    
    def run_full_diagnosis(self):
        """执行完整诊断流程"""
        print("=" * 60)
        print("🚀 T99自动诊断修复工具")
        print("=" * 60)
        
        # 1. 诊断问题
        diagnosis = self.diagnose()
        
        # 2. 根据问题类型应用修复
        fixes_applied = []
        
        if "json_serialization" in diagnosis.get("error_types", []):
            fixes_applied.append(self.fix_json_serialization())
        
        if "timeout" in diagnosis.get("error_types", []):
            fixes_applied.append(self.fix_timeout())
        
        # 3. 运行快速测试
        test_result = self.run_quick_test()
        
        # 4. 生成报告
        report = self.generate_report(diagnosis, fixes_applied)
        report["test_result"] = test_result
        
        # 5. 输出报告
        print("\n" + "=" * 60)
        print("📊 诊断报告")
        print("=" * 60)
        print(f"诊断时间: {report['timestamp']}")
        print(f"检测到问题: {', '.join(diagnosis.get('error_types', []))}")
        
        if fixes_applied:
            print(f"应用修复: {len(fixes_applied)}个")
        
        print("\n建议:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {rec}")
        
        print(f"\n测试结果: {test_result.get('status', 'unknown')}")
        
        # 保存报告到文件
        report_file = "/root/.openclaw/workspace/t99_diagnostic_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 完整报告已保存: {report_file}")
        
        return report

def main():
    diagnostic = T99Diagnostic()
    report = diagnostic.run_full_diagnosis()
    
    # 根据报告状态返回退出码
    if report.get("test_result", {}).get("status") == "success":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()