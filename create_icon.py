"""
创建一个高质量的图标文件用于系统托盘显示
"""

from PIL import Image, ImageDraw
import os
import sys

def create_icon(filename="icon.ico", size=64):
    """创建一个高质量的图标文件，专门针对Windows系统托盘优化
    
    参数:
        filename: 输出文件名
        size: 图标大小（像素）
    """
    print(f"创建高质量图标 {filename}...")
    
    # Windows系统托盘通常使用16x16和32x32的图标
    tray_sizes = [16, 24, 32, 48, 64]
    images = []
    
    # 为每个尺寸创建图标
    for icon_size in tray_sizes:
        # 创建更美观的默认图标
        width = icon_size
        height = icon_size
        
        # 背景颜色 - 使用渐变色
        bg_color = (240, 248, 255, 0)  # 透明背景
        icon_color = (30, 144, 255, 255)  # 深蓝色主色调，完全不透明
        accent_color = (70, 130, 180, 255)  # 钢蓝色作为强调色，完全不透明
        
        # 创建带透明背景的图像
        image = Image.new('RGBA', (width, height), bg_color)
        dc = ImageDraw.Draw(image)
        
        # 绘制一个圆形作为主体
        padding = max(1, int(width * 0.05))
        dc.ellipse([(padding, padding), (width-padding, height-padding)], fill=icon_color)
        
        # 绘制内部图形
        inner_padding = max(2, int(width * 0.2))
        # 绘制内部的小时计时器样式
        dc.pieslice([(inner_padding, inner_padding), (width-inner_padding, height-inner_padding)], 
                   start=45, end=315, fill=accent_color)
        
        # 计算合适的中心点和指针大小
        center_size = max(1, int(width * 0.1))
        center_x = width // 2
        center_y = height // 2
        
        # 绘制中心点
        dc.ellipse([(center_x-center_size//2, center_y-center_size//2), 
                   (center_x+center_size//2, center_y+center_size//2)], 
                   fill=(240, 248, 255, 255))  # 使用不透明的浅蓝色
        
        # 添加"指针"效果，确保尺寸适合小图标
        pointer_length = max(2, int(width * 0.25))
        pointer_width = max(1, int(width * 0.03))
        
        # 小时指针
        dc.line([(center_x, center_y), (center_x, center_y - pointer_length)], 
               fill=(240, 248, 255, 255), width=pointer_width)
        # 分钟指针
        dc.line([(center_x, center_y), (center_x + pointer_length, center_y)], 
               fill=(240, 248, 255, 255), width=pointer_width)
        
        # 保存这个尺寸的图像
        images.append(image)
    
    # 保存为PNG格式（透明背景）
    png_filename = filename.replace(".ico", ".png")
    images[4].save(png_filename)  # 使用最大尺寸的图标为PNG
    print(f"已保存PNG图标: {png_filename}")
    
    # 保存所有尺寸的ICO图标
    try:
        # 使用所有尺寸创建ICO文件
        if os.path.exists(filename):
            os.remove(filename)
            
        # 保存为ICO格式
        images[4].save(filename, format='ICO', sizes=[(s, s) for s in tray_sizes])
        print(f"已保存多尺寸ICO图标: {filename}")
    except Exception as e:
        print(f"保存多尺寸ICO失败: {e}")
        
        # 尝试保存单尺寸图标
        try:
            # 使用最小尺寸保存，确保系统托盘兼容性
            images[0].save(filename, format='ICO')
            print(f"已保存单尺寸ICO图标: {filename}")
        except Exception as e2:
            print(f"保存单尺寸ICO也失败: {e2}")
    
    return filename

if __name__ == "__main__":
    # 如果有命令行参数，使用它作为输出文件名
    output_file = "icon.ico"
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        
    # 创建图标文件
    icon_path = create_icon(output_file)
    print(f"图标创建完成，路径: {os.path.abspath(icon_path)}") 