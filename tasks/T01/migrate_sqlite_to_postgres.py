#!/usr/bin/env python3
"""
T01 SQLite 到 PostgreSQL 数据迁移脚本
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from postgres_storage import T01PostgresStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self, sqlite_path: str, postgres_config: str):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        self.pg_storage = None
        self.sqlite_conn = None
        
    def connect(self):
        """连接数据库"""
        logger.info(f"连接 SQLite: {self.sqlite_path}")
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        logger.info(f"连接 PostgreSQL: {self.postgres_config}")
        self.pg_storage = T01PostgresStorage(self.postgres_config)
        
    def migrate_recommendations(self) -> int:
        """迁移推荐记录"""
        logger.info("开始迁移推荐记录...")
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM t01_recommendations ORDER BY trade_date")
        rows = cursor.fetchall()
        
        migrated = 0
        errors = 0
        
        for row in rows:
            try:
                # 解析JSON数据
                raw_data = {}
                if row['recommendation_json']:
                    try:
                        raw_data = json.loads(row['recommendation_json'])
                    except:
                        pass
                
                # 构建完整数据
                data = {
                    'trade_date': row['trade_date'],
                    't1_date': row['t1_date'],
                    'ts_code': row['ts_code'],
                    'name': row['name'],
                    'total_score': row['total_score'] or 0,
                    't_day_score': row['t_day_score'] or row['total_score'] or 0,
                    'auction_score': row['auction_score'] or 0,
                    'open_change_pct': row['open_change_pct'] or 0,
                }
                data.update(raw_data)
                
                # 保存到 PostgreSQL
                self.pg_storage.save_t_day_recommendation(data)
                migrated += 1
                
                if migrated % 10 == 0:
                    logger.info(f"已迁移 {migrated}/{len(rows)} 条推荐记录")
                    
            except Exception as e:
                logger.warning(f"迁移记录失败 {row.get('ts_code', 'unknown')} @ {row.get('trade_date', 'unknown')}: {e}")
                errors += 1
                continue
        
        logger.info(f"推荐记录迁移完成: {migrated} 成功, {errors} 失败")
        return migrated
    
    def migrate_trades(self) -> int:
        """迁移交易记录"""
        logger.info("开始迁移交易记录...")
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM t01_trades ORDER BY trade_date")
        rows = cursor.fetchall()
        
        migrated = 0
        for row in rows:
            try:
                trade_data = {
                    'recommendation_id': row['recommendation_id'],
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'trade_date': row['trade_date'],
                    'trade_type': row['trade_type'],
                    'trade_time': row.get('trade_time', ''),
                    'price': row['price'],
                    'quantity': row.get('quantity', 0),
                    'amount': row.get('amount', 0),
                    'commission': row.get('commission', 0),
                    'status': row.get('status', 'completed'),
                    'notes': row.get('notes', ''),
                    'entry_score': row.get('entry_score', 0),
                }
                
                self.pg_storage.record_trade(trade_data)
                migrated += 1
                
            except Exception as e:
                logger.warning(f"迁移交易记录失败: {e}")
                continue
        
        logger.info(f"交易记录迁移完成: {migrated} 条")
        return migrated
    
    def migrate_performance(self) -> int:
        """迁移表现统计"""
        logger.info("开始迁移表现统计...")
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM t01_performance ORDER BY buy_date")
        rows = cursor.fetchall()
        
        migrated = 0
        for row in rows:
            try:
                perf_data = {
                    'recommendation_id': row['recommendation_id'],
                    'ts_code': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'buy_date': row['buy_date'],
                    'buy_price': row['buy_price'],
                    'buy_time': row.get('buy_time', ''),
                    'sell_date': row.get('sell_date'),
                    'sell_price': row.get('sell_price'),
                    'sell_time': row.get('sell_time', ''),
                    'holding_days': row.get('holding_days', 0),
                    'return_pct': row.get('return_pct', 0),
                    'win_loss': row.get('win_loss', -1),
                    'max_drawdown': row.get('max_drawdown', 0),
                    't1_open_price': row.get('t1_open_price'),
                    't2_close_price': row.get('t2_close_price'),
                }
                
                self.pg_storage.record_performance(perf_data)
                migrated += 1
                
            except Exception as e:
                logger.warning(f"迁移表现记录失败: {e}")
                continue
        
        logger.info(f"表现统计迁移完成: {migrated} 条")
        return migrated
    
    def verify_migration(self) -> dict:
        """验证迁移结果"""
        logger.info("验证迁移结果...")
        
        cursor = self.sqlite_conn.cursor()
        
        # SQLite 记录数
        cursor.execute("SELECT COUNT(*) FROM t01_recommendations")
        sqlite_recs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM t01_trades")
        sqlite_trades = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM t01_performance")
        sqlite_perf = cursor.fetchone()[0]
        
        # PostgreSQL 记录数
        pg_recs = 0
        pg_trades = 0
        pg_perf = 0
        
        try:
            with self.pg_storage.get_cursor(commit=False) as cursor:
                cursor.execute("SELECT COUNT(*) FROM stock_recommendations")
                pg_recs = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM trade_records")
                pg_trades = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM performance_stats")
                pg_perf = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"查询 PostgreSQL 失败: {e}")
        
        result = {
            'recommendations': {'sqlite': sqlite_recs, 'postgres': pg_recs, 'match': sqlite_recs == pg_recs},
            'trades': {'sqlite': sqlite_trades, 'postgres': pg_trades, 'match': sqlite_trades == pg_trades},
            'performance': {'sqlite': sqlite_perf, 'postgres': pg_perf, 'match': sqlite_perf == pg_perf},
        }
        
        return result
    
    def close(self):
        """关闭连接"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_storage:
            self.pg_storage.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01 数据迁移工具')
    parser.add_argument('--sqlite', default='./data/t01_database.db', help='SQLite 数据库路径')
    parser.add_argument('--config', default='./config_postgres.yaml', help='PostgreSQL 配置文件')
    parser.add_argument('--verify-only', action='store_true', help='仅验证，不迁移')
    
    args = parser.parse_args()
    
    # 检查 SQLite 文件是否存在
    if not os.path.exists(args.sqlite):
        logger.error(f"SQLite 数据库不存在: {args.sqlite}")
        sys.exit(1)
    
    migrator = DataMigrator(args.sqlite, args.config)
    
    try:
        migrator.connect()
        
        if args.verify_only:
            result = migrator.verify_migration()
            print("\n验证结果:")
            print(json.dumps(result, indent=2))
        else:
            # 执行迁移
            print("开始数据迁移...")
            print("=" * 50)
            
            rec_count = migrator.migrate_recommendations()
            trade_count = migrator.migrate_trades()
            perf_count = migrator.migrate_performance()
            
            print("=" * 50)
            print(f"迁移完成:")
            print(f"  推荐记录: {rec_count} 条")
            print(f"  交易记录: {trade_count} 条")
            print(f"  表现统计: {perf_count} 条")
            
            # 验证
            result = migrator.verify_migration()
            print("\n验证结果:")
            for table, stats in result.items():
                status = "✅" if stats['match'] else "⚠️"
                print(f"  {status} {table}: SQLite={stats['sqlite']}, PostgreSQL={stats['postgres']}")
            
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        migrator.close()


if __name__ == "__main__":
    main()
