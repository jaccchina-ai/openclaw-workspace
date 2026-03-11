def get_market_sentiment(analysis_date: str | None = None, debug: bool = False) -> dict[str, Any]:
    """获取市场情绪数据，使用进程级超时防止AKShare API永久阻塞"""
    debug = resolve_debug(debug)
    screener_cfg = get_screener_config()
    fallback_ok = is_fallback_enabled(default=False)
    target_ymd, target_date = _parse_analysis_date(analysis_date)
    
    # 内部函数，用于在子进程中执行
    def _fetch_data() -> dict[str, Any]:
        dbg: dict[str, Any] = {
            "module": "get_market_sentiment",
            "analysis_date": target_ymd,
            "akshare_available": ak is not None,
            "pandas_available": pd is not None,
            "fallback_enabled": fallback_ok,
        }
        
        if ak is None or pd is None:
            dbg["fallback_reason"] = "akshare_or_pandas_missing"
            return {
                "result": _fallback_market_sentiment(debug=debug, debug_info=dbg) if fallback_ok else with_debug(
                    {
                        "date": target_date.strftime("%Y-%m-%d"),
                        "limit_up": 0,
                        "limit_down": 0,
                        "max_height": 0,
                        "break_rate": 0.0,
                        "turnover": 0,
                        "market_sentiment_score": 0.0,
                        "data_source": "unavailable",
                        "error": "real_data_required",
                    },
                    debug,
                    dbg,
                ),
                "debug": dbg
            }
        
        chosen_date = ""
        zt_records: list[dict[str, Any]] = []
        dt_records: list[dict[str, Any]] = []
        zb_records: list[dict[str, Any]] = []
        
        date_candidates = [target_ymd] if analysis_date else _recent_trade_dates(anchor=target_date)
        dbg["date_candidates"] = date_candidates
        dbg["api_calls"] = []
        
        # 优先尝试使用Tushare获取涨停股数据
        tushare_success = False
        for date_text in date_candidates:
            try:
                import tushare as ts
                TUSHARE_TOKEN = "870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab"
                pro = ts.pro_api(TUSHARE_TOKEN)
                
                # 设置超时（5秒）
                import signal
                class TimeoutError(Exception):
                    pass
                def timeout_handler(signum, frame):
                    raise TimeoutError("Tushare API timeout")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)
                try:
                    limit_df = pro.limit_list_d(trade_date=date_text, limit_type='U')
                finally:
                    signal.alarm(0)
                
                if limit_df is not None and not limit_df.empty:
                    # 转换为与akshare兼容的格式
                    records = []
                    for _, row in limit_df.iterrows():
                        records.append({
                            "代码": row['ts_code'].replace('.SH', '').replace('.SZ', ''),
                            "名称": row['name'],
                            "连板数": int(row.get('limit_times', 1)),
                            "状态": "封板",
                            "所属行业": row.get('industry', '')
                        })
                    dbg["api_calls"].append({"api": "tushare_limit_list_d", "date": date_text, "ok": True, "rows": len(records)})
                    chosen_date = date_text
                    zt_records = records
                    tushare_success = True
                    break
            except Exception as e:
                if debug:
                    dbg["tushare_error"] = str(e)
                pass
        
        # 如果Tushare失败，尝试AKShare（带超时）
        if not tushare_success:
            for date_text in date_candidates:
                try:
                    import signal
                    class TimeoutError(Exception):
                        pass
                    def timeout_handler(signum, frame):
                        raise TimeoutError("AKShare API timeout")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(5)
                    try:
                        zt_df = ak.stock_zt_pool_em(date=date_text)
                    finally:
                        signal.alarm(0)
                    
                    records = _to_records(zt_df)
                    dbg["api_calls"].append({"api": "stock_zt_pool_em", "date": date_text, "ok": True, "rows": len(records)})
                    if records:
                        chosen_date = date_text
                        zt_records = records
                        break
                except Exception:
                    dbg["api_calls"].append({"api": "stock_zt_pool_em", "date": date_text, "ok": False})
        
        if not zt_records:
            dbg["fallback_reason"] = "empty_limit_up_pool"
            return {
                "result": _fallback_market_sentiment(debug=debug, debug_info=dbg) if fallback_ok else with_debug(
                    {
                        "date": target_date.strftime("%Y-%m-%d"),
                        "limit_up": 0,
                        "limit_down": 0,
                        "max_height": 0,
                        "break_rate": 0.0,
                        "turnover": 0,
                        "market_sentiment_score": 0.0,
                        "data_source": "unavailable",
                        "error": "real_data_required",
                    },
                    debug,
                    dbg,
                ),
                "debug": dbg
            }
        
        # 跌停股数据（带超时）
        try:
            import signal
            class TimeoutError(Exception):
                pass
            def timeout_handler(signum, frame):
                raise TimeoutError("AKShare API timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            try:
                dt_df = ak.stock_zt_pool_dtgc_em(date=chosen_date)
            finally:
                signal.alarm(0)
            
            dt_records = _to_records(dt_df)
            dbg["api_calls"].append({"api": "stock_zt_pool_dtgc_em", "date": chosen_date, "ok": True, "rows": len(dt_records)})
        except Exception:
            dbg["api_calls"].append({"api": "stock_zt_pool_dtgc_em", "date": chosen_date, "ok": False})
        
        # 炸板股数据（带超时）
        try:
            if hasattr(ak, "stock_zt_pool_zbgc_em"):
                import signal
                class TimeoutError(Exception):
                    pass
                def timeout_handler(signum, frame):
                    raise TimeoutError("AKShare API timeout")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)
                try:
                    zb_df = ak.stock_zt_pool_zbgc_em(date=chosen_date)
                finally:
                    signal.alarm(0)
                
                zb_records = _to_records(zb_df)
                dbg["api_calls"].append({"api": "stock_zt_pool_zbgc_em", "date": chosen_date, "ok": True, "rows": len(zb_records)})
        except Exception:
            dbg["api_calls"].append({"api": "stock_zt_pool_zbgc_em", "date": chosen_date, "ok": False})
        
        limit_up = len(zt_records)
        limit_down = len(dt_records)
        max_height = 0
        for row in zt_records:
            max_height = max(max_height, _parse_board_height(_str(row, ["连板数", "连板", "连板高度", "几天几板"], "1")))
        
        break_count = len(zb_records)
        if break_count == 0:
            for row in zt_records:
                state = _str(row, ["状态", "涨停状态", "封板状态"], "")
                if state and state not in ("封板", "涨停"):
                    break_count += 1
        
        total_lu_events = limit_up + break_count
        break_rate = break_count / total_lu_events if total_lu_events else 0.0
        
        turnover = 0.0
        try:
            import signal
            class TimeoutError(Exception):
                pass
            def timeout_handler(signum, frame):
                raise TimeoutError("AKShare API timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            try:
                spot_records = _to_records(ak.stock_zh_a_spot_em())
            finally:
                signal.alarm(0)
            
            dbg["api_calls"].append({"api": "stock_zh_a_spot_em", "ok": True, "rows": len(spot_records)})
            for row in spot_records:
                turnover += _num_unit(row, ["成交额", "成交额(元)", "amount"], 0.0)
        except Exception:
            dbg["api_calls"].append({"api": "stock_zh_a_spot_em", "ok": False})
        
        score = (
            clamp(limit_up / 70 * 45, 0, 45)
            + clamp((12 - limit_down) / 12 * 20, 0, 20)
            + clamp(max_height / 6 * 20, 0, 20)
            + clamp((0.35 - break_rate) / 0.35 * 15, 0, 15)
        )
        
        payload = {
            "date": f"{chosen_date[:4]}-{chosen_date[4:6]}-{chosen_date[6:8]}",
            "analysis_date": target_date.strftime("%Y-%m-%d"),
            "limit_up": limit_up,
            "limit_down": limit_down,
            "max_height": max_height,
            "break_rate": round(break_rate, 4),
            "turnover": int(turnover),
            "market_sentiment_score": round(score, 2),
            "data_source": "akshare-live",
        }
        dbg["derived"] = {"break_count": break_count, "total_lu_events": total_lu_events}
        return {"result": with_debug(payload, debug, dbg), "debug": dbg}
    
    # 主逻辑：使用multiprocessing进行进程级超时控制
    try:
        import multiprocessing
        import queue
        
        # 创建队列用于接收结果
        result_queue = multiprocessing.Queue()
        
        # 包装函数以便放入队列
        def worker(q):
            try:
                result = _fetch_data()
                q.put(("success", result))
            except Exception as e:
                q.put(("error", str(e)))
        
        # 启动进程
        p = multiprocessing.Process(target=worker, args=(result_queue,))
        p.start()
        
        # 等待10秒
        p.join(timeout=10)
        
        if p.is_alive():
            # 进程超时，强制终止
            p.terminate()
            p.join()
            if debug:
                print("[DEBUG] get_market_sentiment 进程超时（10秒），返回fallback数据")
            
            dbg_timeout: dict[str, Any] = {
                "module": "get_market_sentiment",
                "analysis_date": target_ymd,
                "timeout": True,
                "fallback_enabled": fallback_ok,
            }
            return _fallback_market_sentiment(debug=debug, debug_info=dbg_timeout) if fallback_ok else with_debug(
                {
                    "date": target_date.strftime("%Y-%m-%d"),
                    "limit_up": 0,
                    "limit_down": 0,
                    "max_height": 0,
                    "break_rate": 0.0,
                    "turnover": 0,
                    "market_sentiment_score": 0.0,
                    "data_source": "timeout",
                    "error": "process_timeout",
                },
                debug,
                dbg_timeout,
            )
        
        # 进程正常结束，获取结果
        try:
            status, data = result_queue.get_nowait()
            if status == "success":
                return data["result"]
            else:
                # 进程内部错误
                if debug:
                    print(f"[DEBUG] get_market_sentiment 进程内部错误: {data}")
                
                dbg_error: dict[str, Any] = {
                    "module": "get_market_sentiment",
                    "analysis_date": target_ymd,
                    "process_error": data,
                    "fallback_enabled": fallback_ok,
                }
                return _fallback_market_sentiment(debug=debug, debug_info=dbg_error) if fallback_ok else with_debug(
                    {
                        "date": target_date.strftime("%Y-%m-%d"),
                        "limit_up": 0,
                        "limit_down": 0,
                        "max_height": 0,
                        "break_rate": 0.0,
                        "turnover": 0,
                        "market_sentiment_score": 0.0,
                        "data_source": "process_error",
                        "error": data,
                    },
                    debug,
                    dbg_error,
                )
        except queue.Empty:
            # 队列为空
            if debug:
                print("[DEBUG] get_market_sentiment 队列为空，返回fallback数据")
            
            dbg_empty: dict[str, Any] = {
                "module": "get_market_sentiment",
                "analysis_date": target_ymd,
                "queue_empty": True,
                "fallback_enabled": fallback_ok,
            }
            return _fallback_market_sentiment(debug=debug, debug_info=dbg_empty) if fallback_ok else with_debug(
                {
                    "date": target_date.strftime("%Y-%m-%d"),
                    "limit_up": 0,
                    "limit_down": 0,
                    "max_height": 0,
                    "break_rate": 0.0,
                    "turnover": 0,
                    "market_sentiment_score": 0.0,
                    "data_source": "queue_empty",
                    "error": "queue_empty",
                },
                debug,
                dbg_empty,
            )
            
    except Exception as e:
        # multiprocessing失败，回退到原逻辑（不带进程保护）
        if debug:
            print(f"[DEBUG] multiprocessing失败，回退到原逻辑: {e}")
        
        try:
            # 直接调用内部函数
            result = _fetch_data()
            return result["result"]
        except Exception as inner_e:
            if debug:
                print(f"[DEBUG] 回退逻辑也失败: {inner_e}")
            
            dbg_fallback: dict[str, Any] = {
                "module": "get_market_sentiment",
                "analysis_date": target_ymd,
                "fallback_reason": f"multiprocessing_and_fallback_failed: {e}, {inner_e}",
                "fallback_enabled": fallback_ok,
            }
            return _fallback_market_sentiment(debug=debug, debug_info=dbg_fallback) if fallback_ok else with_debug(
                {
                    "date": target_date.strftime("%Y-%m-%d"),
                    "limit_up": 0,
                    "limit_down": 0,
                    "max_height": 0,
                    "break_rate": 0.0,
                    "turnover": 0,
                    "market_sentiment_score": 0.0,
                    "data_source": "complete_failure",
                    "error": f"multiprocessing_failed: {e}, fallback_failed: {inner_e}",
                },
                debug,
                dbg_fallback,
            )