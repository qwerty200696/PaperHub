#!/usr/bin/env python3
"""
测试数据导出API
"""
import requests
import json

BASE_URL = "http://localhost:5799"

def test_export_json():
    """测试JSON导出"""
    print("测试 JSON 导出...")
    response = requests.post(
        f"{BASE_URL}/api/export/json",
        json={
            "types": ["papers", "articles", "notes"],
            "include_tags": True,
            "include_content": True
        }
    )
    
    if response.status_code == 200:
        print(f"✅ JSON 导出成功")
        print(f"   文件大小: {len(response.content)} bytes")
        # 尝试解析JSON
        try:
            data = json.loads(response.content)
            print(f"   论文数量: {len(data.get('papers', []))}")
            print(f"   文章数量: {len(data.get('articles', []))}")
            print(f"   笔记数量: {len(data.get('notes', []))}")
        except Exception as e:
            print(f"   ⚠️  JSON解析失败: {e}")
    else:
        print(f"❌ JSON 导出失败: {response.status_code}")
        print(f"   错误信息: {response.text}")


def test_export_csv():
    """测试CSV导出"""
    print("\n测试 CSV 导出...")
    response = requests.post(
        f"{BASE_URL}/api/export/csv",
        json={"type": "papers"}
    )
    
    if response.status_code == 200:
        print(f"✅ CSV 导出成功")
        print(f"   文件大小: {len(response.content)} bytes")
        # 显示前几行
        lines = response.content.decode('utf-8').split('\n')[:5]
        print(f"   预览:")
        for line in lines:
            print(f"     {line[:100]}")
    else:
        print(f"❌ CSV 导出失败: {response.status_code}")
        print(f"   错误信息: {response.text}")


def test_export_markdown():
    """测试Markdown导出"""
    print("\n测试 Markdown 导出...")
    response = requests.post(
        f"{BASE_URL}/api/export/markdown",
        json={
            "types": ["papers", "articles", "notes"],
            "separate_files": False
        }
    )
    
    if response.status_code == 200:
        print(f"✅ Markdown 导出成功")
        print(f"   文件大小: {len(response.content)} bytes")
        # 显示前几行
        content = response.content.decode('utf-8')
        lines = content.split('\n')[:10]
        print(f"   预览:")
        for line in lines:
            print(f"     {line}")
    else:
        print(f"❌ Markdown 导出失败: {response.status_code}")
        print(f"   错误信息: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("PaperHub 数据导出 API 测试")
    print("=" * 60)
    
    try:
        test_export_json()
        test_export_csv()
        test_export_markdown()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
