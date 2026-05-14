#!/usr/bin/env python3
"""
清理images_宝玉AI目录中不属于宝玉AI公众号的图片
"""

import os
import re
import json
from pathlib import Path

def extract_image_hashes_from_file(file_path):
    """从宝玉AI.txt文件中提取所有图片文件名"""
    valid_hashes = set()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # 尝试解析JSON
            try:
                data = json.loads(line)
                cover_path = data.get('cover', '')
                
                # 匹配宝玉AI图片路径
                match = re.search(r'images_宝玉AI/([a-f0-9]+)\.jpg', cover_path)
                if match:
                    hash_value = match.group(1)
                    valid_hashes.add(hash_value)
            except json.JSONDecodeError:
                continue
    
    return valid_hashes

def clean_orphan_images(images_dir, valid_hashes):
    """清理孤儿图片"""
    deleted_count = 0
    total_count = 0
    
    if not os.path.exists(images_dir):
        print(f"错误：目录不存在 {images_dir}")
        return
    
    print(f"开始清理目录: {images_dir}")
    print(f"有效的图片数量: {len(valid_hashes)}")
    
    # 遍历目录中的所有图片文件
    for filename in os.listdir(images_dir):
        if filename.endswith('.jpg'):
            total_count += 1
            hash_name = filename.replace('.jpg', '')
            
            # 检查是否为有效的图片
            if hash_name not in valid_hashes:
                file_path = os.path.join(images_dir, filename)
                
                try:
                    # 删除孤儿图片
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"❌ 删除: {filename}")
                except Exception as e:
                    print(f"⚠️  删除失败 {filename}: {e}")
    
    print(f"\n清理完成:")
    print(f"总图片数量: {total_count}")
    print(f"有效图片数量: {len(valid_hashes)}")
    print(f"删除的孤儿图片: {deleted_count}")
    print(f"保留的有效图片: {total_count - deleted_count}")

def main():
    # 定义路径
    base_dir = Path("/Users/wanglijie/PycharmProjects/claude_code_project/PaperHub")
    data_file = base_dir / "data" / "papers" / "wechat_subscriptions" / "宝玉AI.txt"
    images_dir = base_dir / "data" / "papers" / "wechat_subscriptions" / "images_宝玉AI"
    
    print(f"数据文件: {data_file}")
    print(f"图片目录: {images_dir}")
    print("-" * 60)
    
    # 提取有效图片哈希值
    valid_hashes = extract_image_hashes_from_file(data_file)
    
    if not valid_hashes:
        print("❌ 没有找到有效的图片哈希值，请检查数据文件格式")
        return
    
    print(f"✅ 成功提取 {len(valid_hashes)} 个有效图片哈希值")
    
    # 显示前10个哈希值作为示例
    print(f"示例哈希值: {list(valid_hashes)[:10]}")
    
    # 确认清理操作
    print("\n" + "=" * 60)
    input("按 Enter 键开始清理孤儿图片 (按 Ctrl+C 取消)...")
    
    # 执行清理
    clean_orphan_images(images_dir, valid_hashes)

if __name__ == "__main__":
    main()