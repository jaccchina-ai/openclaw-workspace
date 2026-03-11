#!/usr/bin/env python3
"""
竞价分析准备状态检查脚本
检查明早09:25竞价分析所需的所有系统条件，确保100%可靠执行

功能：
1. 定时任务状态验证 (schedule库作业)
2. 数据源健康检查 (Tushare API、候选股文件)
3. 系统状态检查 (时区、内存、进程)
4. 飞书消息推送测试
5. 准备状态评分和报告生成

使用方式：
1. 手动运行: python3 auction_preparation_check.py
2. 跳过飞书测试: python3 auction_preparation_check.py --skip-feishu
3. 强制发送报告: python3 auction_preparation_check.py --always-send
4. 测试模式: python3 auction_preparation_check.py --test
5. 定时运行: 建议明早08:30自动运行
"""

import sys
import os
import json
import yaml
import logging
import psutil
import tushare as ts
import schedule
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, time as dt_time
import pandas as pd
import time
from typing import Dict, List, Tuple, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/auction_preparation_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuctionPreparationChecker:
    """竞价分析准备状态检查器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.config = None
        self.pro = None
        self.results = {}  # 存储所有检查结果
        self.score = 0
        self.total_points = 0
        self.beijing_time = self._get_beijing_time()
        
    def _get_beijing_time(self) -> datetime:
        """获取北京时间 (系统时区已经是Asia/Beijing)"""
        # 系统时区已经是Asia/Beijing (CST, +0800)
        # 直接使用datetime.now()获取本地时间
        return datetime.now()
    
    def load_config(self) -> Tuple[bool, str]:
        """加载配置文件"""
        try:
            if not Path(self.config_path).exists():
                return False, f"配置文件不存在: {self.config_path}"
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 设置Tushare token
            if 'api' in self.config and 'api_key' in self.config['api']:
                ts.set_token(self.config['api']['api_key'])
                self.pro = ts.pro_api()
            
            return True, "配置文件加载成功"
        except Exception as e:
            return False, f"配置文件加载失败: {e}"
    
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有检查"""
        logger.info("=" * 70)
        logger.info("🚀 开始竞价分析准备状态检查")
        logger.info(f"📅 检查时间: {self.beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        logger.info("=" * 70)
        
        # 初始化结果存储
        self.results = {}
        self.score = 0
        self.total_points = 0
        
        # 定义所有检查项（名称，函数，权重）
        checks = [
            ("配置文件", self.check_config, 5),
            ("系统时区", self.check_timezone, 10),
            ("Tushare API连接", self.check_tushare_connection, 15),
            ("候选股文件", self.check_candidate_file, 20),
            ("调度器进程", self.check_scheduler_process, 15),
            ("定时任务注册", self.check_schedule_jobs, 10),
            ("实时竞价接口", self.check_realtime_auction_interface, 10),
            ("系统内存", self.check_system_memory, 5),
            ("飞书推送测试", self.check_feishu_push, 5),
            ("时间窗口", self.check_time_window, 5),
        ]
        
        # 运行所有检查
        for check_name, check_func, weight in checks:
            logger.info(f"🔍 正在检查: {check_name}")
            try:
                passed, message, details = check_func()
                status = "✅" if passed else "❌"
                self.results[check_name] = {
                    "status": status,
                    "passed": passed,
                    "message": message,
                    "details": details,
                    "weight": weight
                }
                
                if passed:
                    self.score += weight
                self.total_points += weight
                
                logger.info(f"   {status} {message}")
                
            except Exception as e:
                logger.error(f"   ⚠️ 检查异常: {e}")
                self.results[check_name] = {
                    "status": "⚠️",
                    "passed": False,
                    "message": f"检查异常: {e}",
                    "details": {},
                    "weight": weight
                }
                self.total_points += weight
        
        # 计算得分百分比
        score_percent = int((self.score / self.total_points) * 100) if self.total_points > 0 else 0
        
        logger.info("=" * 70)
        logger.info(f"📊 检查完成! 总得分: {self.score}/{self.total_points} ({score_percent}%)")
        
        return {
            "timestamp": self.beijing_time.isoformat(),
            "score": self.score,
            "total_points": self.total_points,
            "score_percent": score_percent,
            "results": self.results,
            "next_auction_window": self._get_next_auction_window(),
            "recommendations": self._generate_recommendations()
        }
    
    # ==================== 检查函数 ====================
    
    def check_config(self) -> Tuple[bool, str, Dict]:
        """检查配置文件"""
        passed, message = self.load_config()
        details = {"config_path": self.config_path}
        if passed:
            details["api_key_configured"] = 'api' in self.config and 'api_key' in self.config['api']
        return passed, message, details
    
    def check_timezone(self) -> Tuple[bool, str, Dict]:
        """检查系统时区"""
        try:
            # 检查时区是否为中国时区
            result = subprocess.run(
                ['timedatectl', 'show', '--property=Timezone', '--value'],
                capture_output=True, text=True, timeout=5
            )
            timezone = result.stdout.strip()
            
            # 检查时钟同步
            sync_result = subprocess.run(
                ['timedatectl', 'show', '--property=NTPSynchronized', '--value'],
                capture_output=True, text=True, timeout=5
            )
            synced = sync_result.stdout.strip() == 'yes'
            
            is_china_tz = any(tz in timezone.lower() for tz in ['beijing', 'shanghai', 'asia/shanghai', 'asia/beijing'])
            
            if is_china_tz and synced:
                return True, f"时区正确 ({timezone})，时钟已同步", {
                    "timezone": timezone,
                    "synchronized": synced
                }
            elif is_china_tz and not synced:
                return False, f"时区正确 ({timezone})，但时钟未同步", {
                    "timezone": timezone,
                    "synchronized": synced
                }
            else:
                return False, f"时区不正确: {timezone} (应为中国时区)", {
                    "timezone": timezone,
                    "synchronized": synced
                }
                
        except Exception as e:
            return False, f"时区检查失败: {e}", {"error": str(e)}
    
    def check_tushare_connection(self) -> Tuple[bool, str, Dict]:
        """检查Tushare连接"""
        if not self.pro:
            return False, "Tushare未初始化", {}
        
        try:
            # 测试简单的API调用
            cal = self.pro.trade_cal(
                exchange='SSE', 
                start_date=self.beijing_time.strftime('%Y%m%d'),
                end_date=self.beijing_time.strftime('%Y%m%d')
            )
            
            if not cal.empty:
                is_trading_day = cal.iloc[0]['is_open'] == 1
                return True, f"Tushare连接正常，今日是{'交易日' if is_trading_day else '非交易日'}", {
                    "is_trading_day": bool(is_trading_day),
                    "api_test": "success"
                }
            else:
                return True, "Tushare连接正常，但未查询到交易日历数据", {
                    "is_trading_day": None,
                    "api_test": "partial"
                }
                
        except Exception as e:
            return False, f"Tushare连接失败: {e}", {"error": str(e)}
    
    def check_candidate_file(self) -> Tuple[bool, str, Dict]:
        """检查候选股文件"""
        try:
            # 构建预期的候选股文件名
            # T日评分在昨天20:00运行，生成的是 candidates_{yesterday}_to_{today}.json
            # 用于今天09:25的竞价分析
            yesterday = (self.beijing_time - timedelta(days=1)).strftime('%Y%m%d')
            today = self.beijing_time.strftime('%Y%m%d')
            expected_file = f"state/candidates_{yesterday}_to_{today}.json"
            
            # 同时检查明天的文件（如果T日评分任务刚刚运行）
            tomorrow = (self.beijing_time + timedelta(days=1)).strftime('%Y%m%d')
            tomorrow_file = f"state/candidates_{today}_to_{tomorrow}.json"
            
            # 优先检查预期文件
            if os.path.exists(expected_file):
                candidate_file = expected_file
                file_type = "正常"
            elif os.path.exists(tomorrow_file):
                # 如果找到了明天的文件，说明T日评分任务刚刚运行
                candidate_file = tomorrow_file
                file_type = "提前生成"
                expected_file = tomorrow_file  # 更新预期文件
            else:
                # 尝试查找最近的候选股文件
                state_dir = Path("state")
                if state_dir.exists():
                    candidate_files = list(state_dir.glob("candidates_*_to_*.json"))
                    if candidate_files:
                        latest_file = max(candidate_files, key=os.path.getmtime)
                        candidate_file = str(latest_file)
                        file_type = "最近可用"
                        expected_file = candidate_file
                    else:
                        return False, f"候选股文件不存在: {expected_file} 或 {tomorrow_file}", {
                            "expected_yesterday_to_today": expected_file,
                            "expected_today_to_tomorrow": tomorrow_file,
                            "found": False
                        }
                else:
                    return False, f"state目录不存在且候选股文件不存在", {
                        "expected_yesterday_to_today": expected_file,
                        "expected_today_to_tomorrow": tomorrow_file,
                        "state_dir_exists": False
                    }
            
            # 检查文件内容
            with open(candidate_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            candidates = data.get('candidates', [])
            candidate_count = len(candidates)
            
            if candidate_count == 0:
                return False, f"候选股文件为空: {candidate_file}", {
                    "file": candidate_file,
                    "file_type": file_type,
                    "candidate_count": 0
                }
            
            # 检查文件生成时间
            file_mtime = datetime.fromtimestamp(os.path.getmtime(candidate_file))
            file_age_hours = (self.beijing_time - file_mtime).total_seconds() / 3600
            
            if file_age_hours > 48:
                return False, f"候选股文件过旧 ({file_age_hours:.1f}小时): {candidate_file}", {
                    "file": candidate_file,
                    "file_type": file_type,
                    "candidate_count": candidate_count,
                    "file_age_hours": file_age_hours,
                    "file_mtime": file_mtime.isoformat(),
                    "warning": "文件超过48小时，可能已失效"
                }
            
            return True, f"候选股文件正常 ({file_type})，包含 {candidate_count} 只股票 (生成于 {file_age_hours:.1f} 小时前)", {
                "file": candidate_file,
                "file_type": file_type,
                "candidate_count": candidate_count,
                "file_age_hours": file_age_hours,
                "file_mtime": file_mtime.isoformat(),
                "expected_yesterday_to_today": f"state/candidates_{yesterday}_to_{today}.json",
                "expected_today_to_tomorrow": f"state/candidates_{today}_to_{tomorrow}.json"
            }
            
        except Exception as e:
            return False, f"候选股文件检查失败: {e}", {"error": str(e)}
    
    def check_scheduler_process(self) -> Tuple[bool, str, Dict]:
        """检查调度器进程"""
        try:
            # 查找调度器进程
            scheduler_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'scheduler.py' in ' '.join(cmdline):
                        scheduler_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline,
                            'status': proc.status()
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not scheduler_processes:
                return False, "未找到调度器进程", {"processes_found": 0}
            
            if len(scheduler_processes) > 1:
                return False, f"找到多个调度器进程 ({len(scheduler_processes)}个)", {
                    "processes_found": len(scheduler_processes),
                    "pids": [p['pid'] for p in scheduler_processes]
                }
            
            # 检查是否为systemd服务
            proc = scheduler_processes[0]
            pid = proc['pid']
            
            # 尝试检查是否为systemd服务
            try:
                result = subprocess.run(
                    ['systemctl', 'status', 't01-scheduler.service'],
                    capture_output=True, text=True, timeout=5
                )
                is_systemd = 'Active: active (running)' in result.stdout
            except:
                is_systemd = False
            
            return True, f"调度器进程运行正常 (PID: {pid}, {'systemd' if is_systemd else '手动启动'})", {
                "pid": pid,
                "is_systemd": is_systemd,
                "status": proc['status']
            }
            
        except Exception as e:
            return False, f"调度器进程检查失败: {e}", {"error": str(e)}
    
    def check_schedule_jobs(self) -> Tuple[bool, str, Dict]:
        """检查schedule库定时任务注册状态"""
        try:
            # 检查调度器日志中是否有定时任务注册信息
            log_file = "scheduler_latest.log"
            if not os.path.exists(log_file):
                return False, "调度器日志文件不存在", {"log_file": log_file, "exists": False}
            
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # 查找任务注册信息
            job_count = 0
            job_details = []
            
            if "已注册定时任务数量: 2" in log_content:
                job_count = 2
                # 提取任务详情
                import re
                job_matches = re.findall(r'任务 #\d+: Job\([^)]+\)', log_content)
                for match in job_matches[:2]:
                    job_details.append(match)
            
            if job_count == 2:
                return True, f"已注册 {job_count} 个定时任务 (20:00评分, 09:25竞价分析)", {
                    "job_count": job_count,
                    "jobs": job_details,
                    "log_file": log_file
                }
            elif job_count > 0:
                return False, f"只注册了 {job_count} 个定时任务 (应为2个)", {
                    "job_count": job_count,
                    "jobs": job_details,
                    "log_file": log_file
                }
            else:
                return False, "未找到定时任务注册信息", {
                    "job_count": 0,
                    "log_file": log_file
                }
                
        except Exception as e:
            return False, f"定时任务检查失败: {e}", {"error": str(e)}
    
    def check_realtime_auction_interface(self) -> Tuple[bool, str, Dict]:
        """检查实时竞价接口"""
        if not self.pro:
            return False, "Tushare未初始化，无法检查接口", {}
        
        try:
            # 测试stk_auction接口（不指定trade_date）
            today_str = self.beijing_time.strftime('%Y%m%d')
            
            # 获取一个测试股票代码（使用候选股文件中的股票）
            test_stock = None
            candidate_file = f"state/candidates_{self.beijing_time.strftime('%Y%m%d')}_to_{(self.beijing_time + timedelta(days=1)).strftime('%Y%m%d')}.json"
            
            if os.path.exists(candidate_file):
                with open(candidate_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('candidates'):
                        test_stock = data['candidates'][0]['ts_code']
            
            if not test_stock:
                # 使用默认测试股票
                test_stock = "000001.SZ"
            
            # 尝试调用接口（不指定trade_date，这是修复后的正确方式）
            try:
                auction_data = self.pro.stk_auction(ts_code=test_stock)
                if auction_data is not None and not auction_data.empty:
                    return True, f"实时竞价接口正常 (测试股票: {test_stock})", {
                        "test_stock": test_stock,
                        "has_data": True,
                        "data_count": len(auction_data)
                    }
                else:
                    return True, f"实时竞价接口可调用，但返回空数据 (测试股票: {test_stock})", {
                        "test_stock": test_stock,
                        "has_data": False,
                        "note": "竞价窗口外返回空数据是正常的"
                    }
            except Exception as api_error:
                return False, f"实时竞价接口调用失败: {api_error}", {
                    "test_stock": test_stock,
                    "error": str(api_error)
                }
                
        except Exception as e:
            return False, f"实时竞价接口检查失败: {e}", {"error": str(e)}
    
    def check_system_memory(self) -> Tuple[bool, str, Dict]:
        """检查系统内存"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_gb = memory.total / (1024**3)
            
            if memory_percent < 80:
                return True, f"系统内存正常 ({memory_percent:.1f}% 使用率，总共 {memory_gb:.1f} GB)", {
                    "percent_used": memory_percent,
                    "total_gb": memory_gb,
                    "available_gb": memory.available / (1024**3)
                }
            elif memory_percent < 90:
                return False, f"系统内存使用较高 ({memory_percent:.1f}%)", {
                    "percent_used": memory_percent,
                    "total_gb": memory_gb,
                    "available_gb": memory.available / (1024**3),
                    "warning": "内存使用较高，可能影响性能"
                }
            else:
                return False, f"系统内存使用过高 ({memory_percent:.1f}%)", {
                    "percent_used": memory_percent,
                    "total_gb": memory_gb,
                    "available_gb": memory.available / (1024**3),
                    "critical": "内存使用过高，可能影响稳定性"
                }
                
        except Exception as e:
            return False, f"内存检查失败: {e}", {"error": str(e)}
    
    def check_feishu_push(self) -> Tuple[bool, str, Dict]:
        """测试飞书消息推送"""
        try:
            # 使用绝对路径调用openclaw命令
            openclaw_path = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
            
            # 构建测试命令
            test_message = f"✅ 竞价分析准备状态检查 - 飞书推送测试\n时间: {self.beijing_time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 尝试两种格式：
            # 1. 不带target（希望openclaw能自动推断上下文）
            # 2. 带target（使用用户open_id）
            
            # 用户open_id（从上下文中获取）
            user_open_id = "ou_b8a256a9cb526db6c196cb438d6893a6"
            
            # 尝试不带target
            cmd_without_target = [
                openclaw_path, "message", "send", "--channel", "feishu",
                "--message", test_message
            ]
            
            # 尝试带target
            cmd_with_target = [
                openclaw_path, "message", "send", "--channel", "feishu",
                "--target", f"user:{user_open_id}",
                "--message", test_message
            ]
            
            # 先尝试不带target的命令
            result = subprocess.run(cmd_without_target, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return True, "飞书消息推送测试成功（不带target）", {
                    "command": ' '.join(cmd_without_target),
                    "returncode": result.returncode,
                    "output": result.stdout[:200] if result.stdout else "无输出",
                    "target_used": "auto-inferred"
                }
            
            # 如果不带target失败，尝试带target
            logger.info("   ⚠️ 不带target的命令失败，尝试带target的命令...")
            result = subprocess.run(cmd_with_target, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return True, "飞书消息推送测试成功（带target）", {
                    "command": ' '.join(cmd_with_target),
                    "returncode": result.returncode,
                    "output": result.stdout[:200] if result.stdout else "无输出",
                    "target_used": f"user:{user_open_id}"
                }
            else:
                return False, f"飞书消息推送测试失败 (返回码: {result.returncode})", {
                    "command_without_target": ' '.join(cmd_without_target),
                    "command_with_target": ' '.join(cmd_with_target),
                    "returncode": result.returncode,
                    "stderr": result.stderr[:500] if result.stderr else "无错误信息",
                    "stdout": result.stdout[:200] if result.stdout else "无输出"
                }
                
        except subprocess.TimeoutExpired:
            return False, "飞书推送测试超时 (30秒)", {"timeout": True}
        except Exception as e:
            return False, f"飞书推送测试异常: {e}", {"error": str(e)}
    
    def check_time_window(self) -> Tuple[bool, str, Dict]:
        """检查距离竞价窗口的时间"""
        try:
            current_time = self.beijing_time.time()
            auction_start = dt_time(9, 25)  # 09:25
            auction_end = dt_time(9, 29)   # 09:29
            
            # 计算距离竞价窗口的时间
            now_dt = datetime.combine(self.beijing_time.date(), current_time)
            auction_start_dt = datetime.combine(self.beijing_time.date(), auction_start)
            
            if current_time < auction_start:
                # 还未到竞价窗口
                time_to_window = (auction_start_dt - now_dt).total_seconds() / 60  # 分钟
                return True, f"距离竞价窗口还有 {time_to_window:.1f} 分钟", {
                    "minutes_to_window": time_to_window,
                    "window_start": "09:25",
                    "window_end": "09:29",
                    "current_status": "等待窗口"
                }
            elif auction_start <= current_time <= auction_end:
                # 在竞价窗口内
                time_in_window = (now_dt - auction_start_dt).total_seconds() / 60
                return True, f"已在竞价窗口内 ({time_in_window:.1f} 分钟)", {
                    "minutes_in_window": time_in_window,
                    "window_start": "09:25",
                    "window_end": "09:29",
                    "current_status": "窗口内"
                }
            else:
                # 已过竞价窗口
                return True, "已过今日竞价窗口", {
                    "window_start": "09:25",
                    "window_end": "09:29",
                    "current_status": "已过窗口"
                }
                
        except Exception as e:
            return False, f"时间窗口检查失败: {e}", {"error": str(e)}
    
    # ==================== 辅助函数 ====================
    
    def _get_next_auction_window(self) -> Dict[str, Any]:
        """获取下一个竞价窗口信息"""
        current_time = self.beijing_time
        tomorrow = current_time + timedelta(days=1)
        
        # 明天的竞价窗口
        auction_start = datetime.combine(tomorrow.date(), dt_time(9, 25))
        auction_end = datetime.combine(tomorrow.date(), dt_time(9, 29))
        
        # 计算距离明天竞价窗口的时间
        time_to_window = (auction_start - current_time).total_seconds() / 3600  # 小时
        
        return {
            "date": tomorrow.strftime('%Y-%m-%d'),
            "start": "09:25",
            "end": "09:29",
            "hours_until_window": round(time_to_window, 1),
            "recommended_check_time": "08:30"
        }
    
    def _generate_recommendations(self) -> List[str]:
        """根据检查结果生成建议"""
        recommendations = []
        
        # 检查失败的项目
        failed_checks = [name for name, data in self.results.items() if not data['passed']]
        
        if failed_checks:
            recommendations.append(f"⚠️ 需要立即修复: {', '.join(failed_checks)}")
        
        # 特定建议
        for check_name, data in self.results.items():
            if not data['passed']:
                if check_name == "候选股文件":
                    recommendations.append("📄 候选股文件问题: 请检查昨晚20:00 T日评分任务是否成功运行")
                elif check_name == "调度器进程":
                    recommendations.append("🔄 调度器问题: 请检查systemd服务状态: systemctl status t01-scheduler.service")
                elif check_name == "定时任务注册":
                    recommendations.append("⏰ 定时任务问题: 请检查调度器日志，确保20:00和09:25任务已注册")
                elif check_name == "实时竞价接口":
                    recommendations.append("🔧 竞价接口问题: 确保已修复stk_auction接口调用方式（移除trade_date参数）")
        
        # 时间相关建议
        next_window = self._get_next_auction_window()
        hours_to_window = next_window['hours_until_window']
        
        if hours_to_window > 1:
            recommendations.append(f"⏰ 距离明天竞价窗口还有 {hours_to_window:.1f} 小时，有足够时间修复问题")
        elif hours_to_window > 0.5:
            recommendations.append(f"🚨 距离明天竞价窗口仅剩 {hours_to_window:.1f} 小时，建议立即修复问题")
        
        # 总体建议
        score_percent = int((self.score / self.total_points) * 100) if self.total_points > 0 else 0
        
        if score_percent >= 90:
            recommendations.append("🎉 系统准备状态优秀，明早09:25竞价分析应能正常执行")
        elif score_percent >= 70:
            recommendations.append("⚠️ 系统准备状态良好，但建议修复上述问题以确保可靠性")
        else:
            recommendations.append("🚨 系统准备状态不足，必须修复问题后才能进行竞价分析")
        
        return recommendations
    
    def generate_report(self, check_results: Dict[str, Any]) -> str:
        """生成检查报告"""
        report_lines = []
        
        # 标题
        report_lines.append("=" * 60)
        report_lines.append("📊 竞价分析准备状态检查报告")
        report_lines.append(f"📅 生成时间: {self.beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # 总体评分
        score_percent = check_results['score_percent']
        score_bar = "█" * (score_percent // 5) + "░" * (20 - score_percent // 5)
        
        report_lines.append(f"总体评分: {score_percent}%")
        report_lines.append(f"[{score_bar}]")
        report_lines.append(f"得分: {check_results['score']}/{check_results['total_points']}")
        report_lines.append("")
        
        # 详细检查结果
        report_lines.append("详细检查结果:")
        report_lines.append("-" * 60)
        
        for check_name, data in check_results['results'].items():
            status = data['status']
            message = data['message']
            report_lines.append(f"{status} {check_name}: {message}")
        
        report_lines.append("")
        
        # 下一个竞价窗口
        next_window = check_results['next_auction_window']
        report_lines.append(f"📅 下一个竞价窗口: {next_window['date']} {next_window['start']}-{next_window['end']}")
        report_lines.append(f"⏰ 距离窗口: {next_window['hours_until_window']} 小时")
        report_lines.append(f"🕗 建议检查时间: 明早 {next_window['recommended_check_time']}")
        report_lines.append("")
        
        # 建议
        recommendations = check_results['recommendations']
        if recommendations:
            report_lines.append("📋 建议:")
            for rec in recommendations:
                report_lines.append(f"• {rec}")
        
        return "\n".join(report_lines)
    
    def send_report_to_feishu(self, report_text: str) -> bool:
        """发送报告到飞书"""
        try:
            openclaw_path = "/root/.nvm/versions/node/v22.22.0/bin/openclaw"
            
            # 用户open_id
            user_open_id = "ou_b8a256a9cb526db6c196cb438d6893a6"
            
            # 先尝试不带target的命令
            cmd_without_target = [
                openclaw_path, "message", "send", "--channel", "feishu",
                "--message", report_text
            ]
            
            result = subprocess.run(cmd_without_target, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ 检查报告已发送到飞书（不带target）")
                return True
            
            # 如果不带target失败，尝试带target
            logger.info("   ⚠️ 不带target的命令失败，尝试带target的命令...")
            cmd_with_target = [
                openclaw_path, "message", "send", "--channel", "feishu",
                "--target", f"user:{user_open_id}",
                "--message", report_text
            ]
            
            result = subprocess.run(cmd_with_target, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ 检查报告已发送到飞书（带target: user:{user_open_id}）")
                return True
            else:
                logger.error(f"❌ 发送报告到飞书失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送报告异常: {e}")
            return False

def main():
    """主函数"""
    try:
        # 解析命令行参数
        skip_feishu = '--skip-feishu' in sys.argv
        always_send = '--always-send' in sys.argv
        test_mode = '--test' in sys.argv
        
        # 初始化检查器
        checker = AuctionPreparationChecker()
        
        # 如果跳过飞书测试，修改检查列表
        if skip_feishu:
            logger.info("⏭️  跳过飞书推送测试（命令行参数指定）")
            # 临时修改检查函数
            original_check_feishu = checker.check_feishu_push
            checker.check_feishu_push = lambda: (True, "飞书测试已跳过", {"skipped": True})
        
        # 运行所有检查
        check_results = checker.run_all_checks()
        
        # 生成报告
        report = checker.generate_report(check_results)
        
        # 打印报告
        print("\n" + report)
        
        # 保存报告到文件
        report_file = f"auction_preparation_report_{checker.beijing_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 检查报告已保存到: {report_file}")
        
        # 发送报告到飞书
        score_percent = check_results['score_percent']
        should_send = (score_percent < 90 and not skip_feishu) or always_send
        
        if should_send and not test_mode:
            logger.info("📱 正在发送报告到飞书...")
            if checker.send_report_to_feishu(report):
                logger.info("✅ 报告发送成功")
            else:
                logger.warning("⚠️  报告发送失败，请手动检查")
        elif test_mode:
            logger.info("🧪 测试模式，不发送报告")
        elif skip_feishu:
            logger.info("⏭️  跳过发送报告（命令行参数指定）")
        else:
            logger.info("✅ 得分≥90%，不自动发送报告（使用 --always-send 强制发送）")
        
        # 返回退出码
        if score_percent >= 70:
            logger.info("✅ 系统准备状态可接受")
            return 0
        elif score_percent >= 50:
            logger.warning("⚠️  系统准备状态一般，建议修复问题")
            return 1
        else:
            logger.error("❌ 系统准备状态不足，必须修复问题")
            return 2
            
    except Exception as e:
        logger.error(f"❌ 检查脚本执行失败: {e}")
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)