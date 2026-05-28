#!/usr/bin/env python3
"""
飞书消息功能快速测试脚本
用于验证API接口是否正常工作
"""
import sys
import os

# 添加backend到路径
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_path)

from api.feishu import OFFLINE_MESSAGES_DIR

def test_offline_dir():
    """测试离线消息目录是否创建成功"""
    print("📁 检查离线消息存储目录...")
    print(f"   路径: {OFFLINE_MESSAGES_DIR}")
    
    if OFFLINE_MESSAGES_DIR.exists():
        print("   ✅ 目录已创建")
        return True
    else:
        print("   ❌ 目录不存在")
        return False

def test_api_imports():
    """测试API模块导入"""
    print("\n📦 检查API模块导入...")
    try:
        from api.feishu import (
            run_lark_cli,
            get_groups,
            get_messages,
            save_offline_messages,
            list_offline_messages,
            load_offline_messages,
            delete_offline_messages
        )
        print("   ✅ 所有API函数导入成功")
        return True
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        return False

def test_blueprint_registration():
    """测试蓝图注册"""
    print("\n🔗 检查蓝图注册...")
    try:
        from app import create_app
        app = create_app('default')
        
        # 检查飞书蓝图是否注册
        feishu_rules = [rule for rule in app.url_map.iter_rules() 
                       if 'feishu' in str(rule)]
        
        if feishu_rules:
            print(f"   ✅ 飞书蓝图已注册，共 {len(feishu_rules)} 个路由:")
            for rule in sorted(feishu_rules, key=lambda x: str(x)):
                print(f"      - {rule}")
            return True
        else:
            print("   ❌ 未找到飞书路由")
            return False
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 飞书消息功能测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("离线目录", test_offline_dir()))
    results.append(("API导入", test_api_imports()))
    results.append(("蓝图注册", test_blueprint_registration()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:12s}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有测试通过！飞书消息功能已就绪。")
        print("\n下一步：")
        print("1. 安装 lark-cli: npm install -g @larksuite/lark-cli")
        print("2. 授权（使用user身份）: lark-cli auth login --scope \"im:chat:read,im:message:readonly\"")
        print("3. 启动服务并访问: http://localhost:5000/toolbox/feishu")
    else:
        print("⚠️  部分测试失败，请检查上述错误信息。")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
