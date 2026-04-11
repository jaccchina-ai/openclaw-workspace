#!/usr/bin/env python3
"""
验证T01配置文件YAML语法正确性
"""
import yaml
import sys

def validate_config():
    config_path = '/root/.openclaw/workspace/tasks/T01/config.yaml'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("✅ YAML语法验证通过")
        
        # 检查关键配置项是否存在
        if 'sentiment_monitor' in config:
            print("✅ sentiment_monitor配置存在")
            
            if 'thresholds' in config['sentiment_monitor']:
                print("✅ thresholds配置存在")
            
            if 'notification' in config['sentiment_monitor']:
                print("✅ notification配置存在")
            
            if 'schedule' in config['sentiment_monitor']:
                print(f"ℹ️ schedule配置: {config['sentiment_monitor']['schedule']}")
            else:
                print("ℹ️ schedule配置已被注释或移除")
        else:
            print("⚠️ sentiment_monitor配置不存在")
        
        print("\n✅ 所有验证通过！")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == '__main__':
    success = validate_config()
    sys.exit(0 if success else 1)
