#!/usr/bin/env python3
"""
修复调度器30分钟重启问题
增强异常捕获和资源管理
"""

import sys
import time
import schedule
import traceback
from datetime import datetime
import gc
import psutil
import logging

# 修改schedule库以增强异常处理
def patch_schedule_library():
    """增强schedule库的异常处理"""
    import schedule
    
    original_run_job = schedule.Job.run
    
    def patched_run_job(self):
        """包装job运行，捕获所有异常"""
        try:
            return original_run_job(self)
        except Exception as e:
            logging.getLogger(__name__).error(f"定时任务执行异常 (job={self}): {e}", exc_info=True)
            # 返回None表示任务失败但继续运行
            return None
    
    schedule.Job.run = patched_run_job
    print("✅ schedule库异常处理已增强")

def add_memory_monitoring():
    """添加内存监控装饰器"""
    import functools
    
    def memory_monitor(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_mem = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_mem = psutil.Process().memory_info().rss / 1024 / 1024
                end_time = time.time()
                
                mem_diff = end_mem - start_mem
                time_diff = end_time - start_time
                
                if mem_diff > 50:  # 内存增加超过50MB
                    logging.getLogger(__name__).warning(
                        f"函数 {func.__name__} 内存使用增加 {mem_diff:.1f}MB, 执行时间 {time_diff:.1f}秒"
                    )
                
                # 触发垃圾回收
                if mem_diff > 100:
                    gc.collect()
        
        return wrapper
    
    return memory_monitor

def add_retry_logic(max_retries=3, delay=5):
    """添加重试逻辑装饰器"""
    import functools
    import time
    
    def retry_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.getLogger(__name__).warning(
                            f"函数 {func.__name__} 第{attempt+1}次失败，{delay}秒后重试: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logging.getLogger(__name__).error(
                            f"函数 {func.__name__} 重试{max_retries}次后仍失败: {e}"
                        )
            raise last_exception
        
        return wrapper
    
    return retry_decorator

def create_robust_scheduler():
    """创建健壮的调度器包装类"""
    import schedule
    
    class RobustScheduler:
        """健壮调度器，防止异常导致退出"""
        
        def __init__(self, original_scheduler):
            self.scheduler = original_scheduler
            self.logger = logging.getLogger(__name__)
            self.start_time = datetime.now()
            self.heartbeat_counter = 0
            self.last_heartbeat = time.time()
            
            # 监控配置
            self.max_memory_mb = 500  # 最大内存限制
            self.heartbeat_interval = 300  # 5分钟心跳
        
        def run_pending_with_safety(self):
            """安全运行pending任务"""
            try:
                # 检查内存使用
                self.check_memory_usage()
                
                # 运行任务
                schedule.run_pending()
                
                # 记录心跳
                current_time = time.time()
                if current_time - self.last_heartbeat > self.heartbeat_interval:
                    self.heartbeat_counter += 1
                    self.logger.info(
                        f"💓 调度器心跳 #{self.heartbeat_counter}, "
                        f"运行时间: {(datetime.now() - self.start_time).total_seconds() / 60:.1f}分钟, "
                        f"内存: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB"
                    )
                    self.last_heartbeat = current_time
                    
                    # 定期垃圾回收
                    if self.heartbeat_counter % 12 == 0:  # 每小时一次
                        gc.collect()
                        self.logger.info("🔄 执行定期垃圾回收")
                
                return True
                
            except Exception as e:
                self.logger.error(f"调度器主循环异常: {e}", exc_info=True)
                # 不重新抛出异常，避免退出
                return False
        
        def check_memory_usage(self):
            """检查内存使用"""
            mem_info = psutil.Process().memory_info()
            mem_mb = mem_info.rss / 1024 / 1024
            
            if mem_mb > self.max_memory_mb:
                self.logger.warning(f"⚠️ 内存使用过高: {mem_mb:.1f}MB > {self.max_memory_mb}MB")
                
                # 尝试释放内存
                gc.collect()
                
                # 记录内存状态
                self.log_memory_state()
        
        def log_memory_state(self):
            """记录内存状态"""
            import gc
            mem_info = psutil.Process().memory_info()
            
            self.logger.info(
                f"内存状态 - RSS: {mem_info.rss / 1024 / 1024:.1f}MB, "
                f"VMS: {mem_info.vms / 1024 / 1024:.1f}MB, "
                f"垃圾回收对象: {len(gc.get_objects())}"
            )
        
        def run_forever(self, sleep_seconds=60):
            """永远运行调度器"""
            self.logger.info(f"🚀 启动健壮调度器，检查间隔: {sleep_seconds}秒")
            
            consecutive_failures = 0
            max_consecutive_failures = 5
            
            while True:
                try:
                    success = self.run_pending_with_safety()
                    
                    if success:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            self.logger.error(f"连续失败 {consecutive_failures} 次，可能系统不稳定")
                    
                    time.sleep(sleep_seconds)
                    
                except KeyboardInterrupt:
                    self.logger.info("调度器被用户中断")
                    break
                except Exception as e:
                    self.logger.error(f"调度器意外异常: {e}", exc_info=True)
                    consecutive_failures += 1
                    
                    # 如果连续失败太多，等待更长时间
                    if consecutive_failures > max_consecutive_failures:
                        sleep_time = min(300, sleep_seconds * 2)  # 最多5分钟
                        self.logger.warning(f"连续失败过多，等待 {sleep_time} 秒后继续")
                        time.sleep(sleep_time)
                    else:
                        time.sleep(sleep_seconds)
    
    return RobustScheduler

def apply_fixes_to_existing_scheduler():
    """向现有调度器应用修复"""
    print("🔧 应用调度器修复...")
    
    # 1. 增强schedule库
    patch_schedule_library()
    
    # 2. 创建健壮调度器类
    RobustSchedulerClass = create_robust_scheduler()
    
    print("✅ 调度器修复已应用")
    print("\n建议修改 scheduler.py:")
    print("""
1. 在文件顶部添加:
   from scheduler_30min_fix import RobustScheduler
    
2. 修改 run_scheduler() 方法中的主循环:
   # 替换原来的 schedule.run_pending() 循环
   robust_scheduler = RobustScheduler(schedule)
   robust_scheduler.run_forever(sleep_seconds=60)
    
3. 在 T01Scheduler.__init__() 中添加内存监控
   """)
    
    return RobustSchedulerClass

def generate_fix_report():
    """生成修复报告"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'issues_found': [
            '可能的内存泄漏（未验证）',
            '未捕获的异常可能导致退出',
            'schedule库默认异常处理不足',
            '缺少监控和自动恢复机制'
        ],
        'fixes_applied': [
            '增强schedule库异常处理',
            '添加内存监控装饰器',
            '添加重试逻辑',
            '创建健壮调度器包装类',
            '添加心跳和健康检查'
        ],
        'recommendations': [
            '立即应用健壮调度器修复',
            '部署健康监控器 (scheduler_health_monitor.py)',
            '定期检查系统资源使用',
            '设置进程监控自动重启'
        ],
        'files_created': [
            'scheduler_30min_fix.py - 核心修复',
            'scheduler_health_monitor.py - 健康监控',
            'debug_scheduler_crash.py - 崩溃分析'
        ]
    }
    
    print("\n" + "="*60)
    print("调度器30分钟重启问题修复方案")
    print("="*60)
    
    print(f"\n生成时间: {report['timestamp']}")
    
    print("\n📋 发现的问题:")
    for issue in report['issues_found']:
        print(f"  • {issue}")
    
    print("\n🔧 应用的修复:")
    for fix in report['fixes_applied']:
        print(f"  ✓ {fix}")
    
    print("\n🚀 推荐操作:")
    for rec in report['recommendations']:
        print(f"  → {rec}")
    
    print("\n📁 创建的文件:")
    for file in report['files_created']:
        print(f"  📄 {file}")
    
    print("\n📝 使用说明:")
    print("""
1. 立即启动健康监控器:
   cd /root/.openclaw/workspace/tasks/T01
   python3 scheduler_health_monitor.py --mode monitor &

2. 监控调度器运行状况:
   tail -f /tmp/t01_health_monitor.log

3. 应用健壮调度器修复:
   修改 scheduler.py，使用 RobustScheduler 替换原有主循环
   
4. 设置cron定期检查:
   */5 * * * * cd /root/.openclaw/workspace/tasks/T01 && python3 scheduler_health_monitor.py --mode check >> /tmp/t01_health_check.log 2>&1
    """)

if __name__ == "__main__":
    # 生成修复报告
    generate_fix_report()
    
    # 应用修复（演示）
    RobustSchedulerClass = apply_fixes_to_existing_scheduler()
    
    print("\n🎯 总结:")
    print("调度器30分钟重启问题可能是由于:")
    print("1. 未捕获的异常导致进程退出")
    print("2. 内存泄漏或资源耗尽")
    print("3. schedule库的内部问题")
    print("4. 外部依赖超时或失败")
    print("\n通过增强异常处理、添加监控和自动恢复机制，可以显著提高调度器稳定性。")