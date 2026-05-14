#!/usr/bin/env python3
"""
生成 PaperHub Clipper 插件占位图标
使用 PIL/Pillow 创建简单的渐变图标
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    def create_icon(size, output_path):
        """创建指定尺寸的图标"""
        # 创建图像
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制渐变背景（紫色到蓝色）
        for y in range(size):
            # 计算渐变色
            ratio = y / size
            r = int(102 + (102 - 102) * ratio)
            g = int(126 + (90 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        
        # 绘制圆角矩形背景
        margin = size // 8
        radius = size // 4
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=radius,
            fill=(102, 126, 234, 255)
        )
        
        # 绘制字母 "P"
        font_size = size // 2
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default()
        
        # 计算文字位置（居中）
        text = "P"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - bbox[1]
        
        # 绘制白色文字
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        # 保存
        img.save(output_path, 'PNG')
        print(f"✓ 已生成: {output_path} ({size}x{size})")
    
    # 创建三个尺寸的图标
    icons_dir = os.path.dirname(os.path.abspath(__file__))
    create_icon(16, os.path.join(icons_dir, 'icon-16.png'))
    create_icon(48, os.path.join(icons_dir, 'icon-48.png'))
    create_icon(128, os.path.join(icons_dir, 'icon-128.png'))
    
    print("\n✅ 所有图标生成成功！")
    
except ImportError:
    print("❌ 需要安装 Pillow 库")
    print("运行: pip install Pillow")
    print("\n或者手动准备 PNG 图标文件放在 icons/ 目录下")
