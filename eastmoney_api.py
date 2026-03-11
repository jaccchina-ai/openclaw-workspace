#!/usr/bin/env python3
"""
东方财富实时数据API封装
接口地址: https://push2.eastmoney.com/api/qt/clist/get
支持：板块排行、个股列表、资金流向等实时数据
"""

import requests
import json
import time
import pandas as pd
from typing import Dict, List, Any, Optional
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class EastMoneyAPI:
    """东方财富API封装类"""
    
    BASE_URL = "https://push2.eastmoney.com/api/qt/clist/get"
    
    # 字段映射表（根据东方财富API文档）
    FIELD_MAPPING = {
        # 基础字段
        'f1': 'unknown1',      # 未知
        'f2': 'latest_price',  # 最新价
        'f3': 'change_pct',    # 涨跌幅
        'f4': 'change_amt',    # 涨跌额
        'f5': 'volume',        # 成交量(手)
        'f6': 'turnover',      # 成交额
        'f7': 'amplitude',     # 振幅
        'f8': 'turnover_rate', # 换手率
        'f9': 'pe',            # 市盈率
        'f10': 'unknown10',    # 未知
        'f11': 'unknown11',    # 未知
        'f12': 'code',         # 代码
        'f13': 'market',       # 市场 (0:深圳, 1:上海, 90:板块)
        'f14': 'name',         # 名称
        'f15': 'high',         # 最高
        'f16': 'low',          # 最低
        'f17': 'open',         # 开盘
        'f18': 'close',        # 昨收
        'f20': 'total_mv',     # 总市值
        'f21': 'circ_mv',      # 流通市值
        'f22': 'unknown22',    # 未知
        'f23': 'pb',           # 市净率
        'f24': 'unknown24',    # 未知
        'f25': 'unknown25',    # 未知
        'f26': 'unknown26',    # 未知
        # 资金流向相关
        'f62': 'main_net_inflow',  # 主力净流入
        'f128': 'unknown128',      # 未知
        'f136': 'unknown136',      # 未知
        'f115': 'pe_ttm',          # 市盈率(TTM)
        'f152': 'unknown152',      # 未知
    }
    
    # 市场类型映射
    MARKET_TYPE = {
        'industry': 'm:90 t:2',      # 行业板块
        'concept': 'm:90 t:3',       # 概念板块
        'ashare': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',  # A股
        'sh': 'm:1 t:2,m:1 t:23',    # 上海
        'sz': 'm:0 t:6,m:0 t:80',    # 深圳
    }
    
    def __init__(self, timeout=15, max_retries=3):
        """初始化API客户端"""
        self.timeout = timeout
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://quote.eastmoney.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """发送API请求"""
        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"东方财富API请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"东方财富API响应解析失败: {e}")
            return None
    
    def _parse_response(self, data: Dict, board_type: str = "industry") -> List[Dict]:
        """解析API响应数据"""
        if not data or 'data' not in data or 'diff' not in data['data']:
            return []
        
        diff = data['data']['diff']
        results = []
        
        # diff可能是字典（键值对）或列表
        items = diff.values() if isinstance(diff, dict) else diff
        
        for item in items:
            parsed_item = {'board_type': board_type}
            
            # 转换字段
            for field_key, value in item.items():
                field_name = self.FIELD_MAPPING.get(field_key, field_key)
                try:
                    # 尝试转换为数值
                    if isinstance(value, (int, float)):
                        parsed_item[field_name] = value
                    elif value is None or value == '':
                        parsed_item[field_name] = None
                    else:
                        # 尝试转换为浮点数
                        try:
                            parsed_item[field_name] = float(value)
                        except (ValueError, TypeError):
                            parsed_item[field_name] = value
                except Exception as e:
                    parsed_item[field_name] = value
            
            # 确保关键字段存在
            if 'change_pct' in parsed_item and parsed_item['change_pct'] is not None:
                results.append(parsed_item)
        
        return results
    
    def get_board_ranking(self, board_type: str = "industry", 
                          sort_by: str = "change_pct",
                          ascending: bool = False,
                          limit: int = 20) -> List[Dict]:
        """
        获取板块排行
        
        Args:
            board_type: 板块类型 industry(行业) / concept(概念)
            sort_by: 排序字段 change_pct(涨跌幅) / turnover(成交额) / main_net_inflow(主力净流入)
            ascending: 是否升序
            limit: 返回数量限制
        
        Returns:
            板块数据列表
        """
        if board_type not in ['industry', 'concept']:
            board_type = 'industry'
        
        fs = self.MARKET_TYPE.get(board_type, 'm:90 t:2')
        
        # 字段选择
        fields = "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f22,f23,f24,f25,f26,f62,f128,f136,f115,f152"
        
        params = {
            "pn": 1,        # 页码
            "pz": limit * 2, # 多取一些用于过滤
            "po": 1,        # 排序
            "np": 1,        # 
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",  # 固定token
            "fltt": 2,      # 
            "invt": 2,      # 
            "fid": "f3",    # 排序字段 f3:涨跌幅
            "fs": fs,
            "fields": fields
        }
        
        data = self._make_request(params)
        if not data:
            return []
        
        results = self._parse_response(data, board_type)
        
        # 排序
        if results and sort_by in results[0]:
            try:
                results.sort(key=lambda x: x.get(sort_by, 0), reverse=not ascending)
            except (TypeError, KeyError):
                pass
        
        return results[:limit]
    
    def get_stock_list(self, market: str = "ashare",
                       sort_by: str = "change_pct",
                       ascending: bool = False,
                       limit: int = 100) -> List[Dict]:
        """
        获取股票列表
        
        Args:
            market: 市场类型 ashare(A股) / sh(上海) / sz(深圳)
            sort_by: 排序字段
            ascending: 是否升序
            limit: 返回数量限制
        
        Returns:
            股票数据列表
        """
        fs = self.MARKET_TYPE.get(market, 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23')
        
        fields = "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f22,f23,f24,f25,f26,f62,f128,f136,f115,f152"
        
        params = {
            "pn": 1,
            "pz": limit * 2,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": fs,
            "fields": fields
        }
        
        data = self._make_request(params)
        if not data:
            return []
        
        results = self._parse_response(data, "stock")
        
        # 排序
        if results and sort_by in results[0]:
            try:
                results.sort(key=lambda x: x.get(sort_by, 0), reverse=not ascending)
            except (TypeError, KeyError):
                pass
        
        return results[:limit]
    
    def get_board_constituents(self, board_code: str, board_type: str = "industry") -> List[Dict]:
        """
        获取板块成分股（需要单独接口，这里暂时返回空列表）
        注：东方财富成分股接口需要另一个API，这里先预留接口
        """
        # TODO: 实现成分股接口
        # 接口示例: https://push2.eastmoney.com/api/qt/clist/get?fs=b:{board_code} f1,f2,f3...
        return []
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            # 尝试获取少量数据测试连接
            params = {
                "pn": 1,
                "pz": 1,
                "fs": "m:90 t:2",
                "fields": "f12,f14,f3",
                "ut": "bd1d9ddb04089700cf9c27f6f7426281"
            }
            response = self.session.get(self.BASE_URL, params=params, timeout=5)
            return response.status_code == 200
        except:
            return False


# 全局实例
api_client = EastMoneyAPI()


def get_top_boards(board_type="industry", top_n=10, min_change=0.0) -> List[Dict]:
    """
    获取强势板块（简化接口）
    
    Args:
        board_type: 板块类型
        top_n: 返回数量
        min_change: 最小涨跌幅过滤
    
    Returns:
        强势板块列表
    """
    try:
        boards = api_client.get_board_ranking(
            board_type=board_type,
            sort_by="change_pct",
            ascending=False,
            limit=top_n * 2
        )
        
        # 过滤
        filtered = []
        for board in boards:
            change_pct = board.get('change_pct', 0)
            if change_pct is not None and change_pct >= min_change:
                filtered.append({
                    'code': board.get('code', ''),
                    'name': board.get('name', '未知'),
                    'change_pct': change_pct,
                    'turnover': board.get('turnover', 0),
                    'main_net_inflow': board.get('main_net_inflow', 0),
                    'turnover_rate': board.get('turnover_rate', 0),
                })
        
        return filtered[:top_n]
    except Exception as e:
        print(f"获取强势板块失败: {e}")
        return []


def get_stocks_by_sector(sector_name: str, limit: int = 50) -> List[Dict]:
    """
    根据板块名称获取股票（简化版，实际需要成分股接口）
    暂时通过名称过滤全市场股票
    
    Args:
        sector_name: 板块名称
        limit: 返回数量
    
    Returns:
        股票列表
    """
    try:
        # TODO: 实现真正的成分股查询
        # 暂时返回空列表，需要实际实现
        return []
    except Exception as e:
        print(f"获取板块成分股失败: {e}")
        return []


if __name__ == "__main__":
    # 测试代码
    print("测试东方财富API连接...")
    
    client = EastMoneyAPI(timeout=10)
    
    # 测试连接
    if client.test_connection():
        print("✅ API连接测试成功")
    else:
        print("❌ API连接测试失败")
    
    # 测试获取行业板块
    print("\n获取行业板块排行...")
    industry_boards = client.get_board_ranking("industry", limit=5)
    if industry_boards:
        print(f"获取到 {len(industry_boards)} 个行业板块:")
        for i, board in enumerate(industry_boards[:3]):
            print(f"  {i+1}. {board.get('name')}: {board.get('change_pct')}%")
    else:
        print("获取行业板块失败")
    
    # 测试获取概念板块
    print("\n获取概念板块排行...")
    concept_boards = client.get_board_ranking("concept", limit=5)
    if concept_boards:
        print(f"获取到 {len(concept_boards)} 个概念板块:")
        for i, board in enumerate(concept_boards[:3]):
            print(f"  {i+1}. {board.get('name')}: {board.get('change_pct')}%")
    else:
        print("获取概念板块失败")
    
    print("\n测试完成")