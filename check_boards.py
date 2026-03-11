#!/usr/bin/env python3
import akshare as ak
import time
import signal

def timeout_func(func, timeout=3):
    def handler(signum, frame):
        raise TimeoutError()
    
    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        result = func()
        signal.alarm(0)
        return result, None
    except TimeoutError:
        return None, "timeout"
    except Exception as e:
        return None, str(e)
    finally:
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)

print("测试板块列表接口...")

# 测试获取行业板块列表
print("\n1. 测试stock_board_industry_name_em:")
try:
    start = time.time()
    df = ak.stock_board_industry_name_em()
    elapsed = time.time() - start
    print(f"   成功，耗时 {elapsed:.2f}秒")
    print(f"   板块数量: {len(df)}")
    if not df.empty:
        print("   前5个板块:")
        for i, row in df.head(5).iterrows():
            print(f"     {row['板块名称']} - 代码: {row['板块代码']}")
except Exception as e:
    print(f"   失败: {e}")

# 测试获取概念板块列表
print("\n2. 测试stock_board_concept_name_em:")
try:
    start = time.time()
    df = ak.stock_board_concept_name_em()
    elapsed = time.time() - start
    print(f"   成功，耗时 {elapsed:.2f}秒")
    print(f"   板块数量: {len(df)}")
except Exception as e:
    print(f"   失败: {e}")

print("\n3. 尝试获取一个板块的成分股（使用板块代码）:")
try:
    # 先获取一个板块代码
    industry_df = ak.stock_board_industry_name_em()
    if not industry_df.empty:
        sector_code = industry_df.iloc[0]['板块代码']
        sector_name = industry_df.iloc[0]['板块名称']
        print(f"   测试板块: {sector_name} (代码: {sector_code})")
        
        # 尝试用代码获取成分股
        def get_cons():
            return ak.stock_board_industry_cons_em(symbol=sector_code)
        
        result, error = timeout_func(get_cons, timeout=5)
        if error:
            print(f"   获取成分股失败: {error}")
        elif result is not None:
            print(f"   成功获取成分股: {len(result)}只")
    else:
        print("   无法获取板块列表")
except Exception as e:
    print(f"   整体流程失败: {e}")

print("\n测试完成")