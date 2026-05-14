"""
AI 配置功能测试脚本
用于验证前端配置加载逻辑是否正确
"""

def test_ai_config_flow():
    """测试 AI 配置流程"""
    print("=" * 60)
    print("AI 配置功能测试")
    print("=" * 60)
    
    # 1. 检查 .env 文件
    print("\n1. 检查 .env 文件...")
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'LLM_API_KEY=your-api-key-here' in content:
                print("   ❌ .env 文件中 API Key 仍是占位符")
                print("   建议：编辑 .env 文件，填入真实的 API Key")
            elif 'LLM_API_KEY=' in content and len(content.split('LLM_API_KEY=')[1].split('\n')[0]) > 10:
                print("   ✅ .env 文件中已配置 API Key")
            else:
                print("   ⚠️  .env 文件中未找到 API Key 配置")
    except FileNotFoundError:
        print("   ❌ .env 文件不存在")
    
    # 2. 检查后端 API
    print("\n2. 检查后端 AI 配置 API...")
    try:
        import sys
        sys.path.insert(0, 'backend')
        from api.ai import get_ai_config
        from services.llm_client import get_llm_client
        
        client = get_llm_client()
        print(f"   Provider: {client.provider}")
        print(f"   Has API Key: {bool(client.api_key)}")
        print(f"   Base URL: {client.base_url or '(默认)'}")
        print(f"   Model ID: {getattr(client, 'model_id', '') or '(默认)'}")
        
        if client.api_key:
            print("   ✅ 后端已配置 API Key")
        else:
            print("   ❌ 后端未配置 API Key")
            print("   建议：通过前端界面配置或编辑 .env 文件")
    except Exception as e:
        print(f"   ⚠️  无法检查后端配置: {e}")
    
    # 3. 检查前端代码
    print("\n3. 检查前端配置加载逻辑...")
    try:
        with open('frontend/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查是否有 loadAIConfig 函数
            if 'function loadAIConfig()' in content:
                print("   ✅ loadAIConfig 函数存在")
            else:
                print("   ❌ loadAIConfig 函数不存在")
            
            # 检查是否有异步加载逻辑
            if "axios.get('/api/ai/config')" in content:
                print("   ✅ 包含从后端异步加载配置的逻辑")
            else:
                print("   ❌ 缺少从后端异步加载配置的逻辑")
            
            # 检查是否有 localStorage 读取
            if "localStorage.getItem('aiConfigs')" in content:
                print("   ✅ 包含从 localStorage 读取配置的逻辑")
            else:
                print("   ❌ 缺少从 localStorage 读取配置的逻辑")
            
            # 检查是否有 watch 监听器
            if 'watch(aiConfigDialogVisible' in content:
                print("   ✅ 包含弹窗打开的 watch 监听器")
            else:
                print("   ❌ 缺少弹窗打开的 watch 监听器")
                
    except FileNotFoundError:
        print("   ❌ frontend/index.html 文件不存在")
    
    # 4. 给出建议
    print("\n" + "=" * 60)
    print("建议操作：")
    print("=" * 60)
    print("1. 如果之前配置过但现在看不到：")
    print("   - 刷新浏览器页面（Ctrl+F5 / Cmd+Shift+R）")
    print("   - 检查浏览器控制台是否有错误信息")
    print("   - 打开浏览器开发者工具 -> Application -> Local Storage")
    print("     查看是否有 'aiConfigs' 键")
    print()
    print("2. 如果从未配置过：")
    print("   - 方案A：编辑 .env 文件，填入真实 API Key，重启后端")
    print("   - 方案B：点击前端「配置」按钮，输入 API Key 并保存")
    print()
    print("3. 验证配置是否生效：")
    print("   - 点击「生成 AI 解读」按钮")
    print("   - 成功：显示 AI 生成的摘要")
    print("   - 失败：检查错误提示")
    print("=" * 60)


if __name__ == '__main__':
    test_ai_config_flow()
