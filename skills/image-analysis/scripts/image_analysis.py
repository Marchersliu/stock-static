#!/usr/bin/env python3
"""
图像分析 - OCR、图表识别、内容描述

用法:
    python3 image_analysis.py /path/to/image.png --describe
    python3 image_analysis.py chart.png --chart --output data.json
    python3 image_analysis.py before.png after.png --diff
"""
import argparse
import json
import os
from PIL import Image


def describe_image(image_path):
    """生成图像描述（框架函数，实际分析由OpenClaw agent的LLM完成）"""
    try:
        img = Image.open(image_path)
        info = {
            'path': image_path,
            'format': img.format,
            'size': img.size,
            'mode': img.mode,
            'width': img.width,
            'height': img.height,
        }
        return info
    except Exception as e:
        return {'error': str(e)}


def ocr_image(image_path):
    """OCR识别"""
    try:
        import pytesseract
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return text
    except ImportError:
        return "[ERR] pytesseract not installed. Run: pip3 install pytesseract && brew install tesseract"
    except Exception as e:
        return f"[ERR] {e}"


def analyze_chart(image_path):
    """图表分析（框架函数）"""
    info = describe_image(image_path)
    
    # 简单的图表类型判断
    chart_types = []
    
    # 这里需要实际的图像处理来识别图表类型
    # 当前版本返回框架信息
    
    return {
        'image_info': info,
        'chart_types': chart_types,
        'note': '实际图表识别需要LLM vision能力或专门的CV模型'
    }


def compare_images(path1, path2):
    """对比两张图片"""
    try:
        img1 = Image.open(path1)
        img2 = Image.open(path2)
        
        info1 = describe_image(path1)
        info2 = describe_image(path2)
        
        diff = {
            'size_same': img1.size == img2.size,
            'format_same': img1.format == img2.format,
            'mode_same': img1.mode == img2.mode,
            'image1': info1,
            'image2': info2,
        }
        
        # 简单的像素差异（如果尺寸相同）
        if img1.size == img2.size:
            # 转换为相同模式
            img1_rgb = img1.convert('RGB')
            img2_rgb = img2.convert('RGB')
            
            # 计算差异
            diff_pixels = 0
            total_pixels = img1.width * img1.height
            
            for x in range(0, img1.width, 10):  # 采样
                for y in range(0, img1.height, 10):
                    p1 = img1_rgb.getpixel((x, y))
                    p2 = img2_rgb.getpixel((x, y))
                    if abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) + abs(p1[2]-p2[2]) > 30:
                        diff_pixels += 1
            
            sample_size = ((img1.width // 10) + 1) * ((img1.height // 10) + 1)
            diff['pixel_diff_ratio'] = diff_pixels / sample_size if sample_size > 0 else 0
            diff['significant_diff'] = diff['pixel_diff_ratio'] > 0.1
        
        return diff
    except Exception as e:
        return {'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Image Analysis')
    parser.add_argument('images', nargs='+', help='Image file path(s)')
    parser.add_argument('--describe', action='store_true', help='Describe image content')
    parser.add_argument('--ocr', action='store_true', help='OCR text extraction')
    parser.add_argument('--chart', action='store_true', help='Analyze chart')
    parser.add_argument('--kline', action='store_true', help='Analyze K-line chart')
    parser.add_argument('--stock', help='Stock code for K-line context')
    parser.add_argument('--diff', action='store_true', help='Compare two images')
    parser.add_argument('--output', help='Save result to file')
    
    args = parser.parse_args()
    
    if args.diff and len(args.images) >= 2:
        result = compare_images(args.images[0], args.images[1])
        print(f"[Compare] {args.images[0]} vs {args.images[1]}")
        print(f"  Size same: {result.get('size_same', 'N/A')}")
        print(f"  Format same: {result.get('format_same', 'N/A')}")
        print(f"  Mode same: {result.get('mode_same', 'N/A')}")
        if 'pixel_diff_ratio' in result:
            print(f"  Pixel diff: {result['pixel_diff_ratio']:.1%}")
            print(f"  Significant: {'Yes' if result.get('significant_diff') else 'No'}")
    
    elif args.ocr:
        for img_path in args.images:
            print(f"[OCR] {img_path}")
            text = ocr_image(img_path)
            print(text[:1000])
            if len(text) > 1000:
                print(f"... ({len(text)} chars total)")
    
    elif args.chart or args.kline:
        for img_path in args.images:
            print(f"[Chart] {img_path}")
            result = analyze_chart(img_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        # 默认描述
        for img_path in args.images:
            print(f"[Image] {img_path}")
            info = describe_image(img_path)
            print(f"  Format: {info.get('format')}")
            print(f"  Size: {info.get('width')}x{info.get('height')}")
            print(f"  Mode: {info.get('mode')}")
            print()
            print("="*60)
            print("  提示：实际图像分析由OpenClaw agent的LLM完成")
            if args.kline or (args.stock and 'kline' in img_path.lower()):
                print(f"  股票上下文: {args.stock}")
            print("  使用方法：上传图片并告诉agent '分析这张截图'")
            print("="*60)
    
    if args.output:
        # 简化：保存基本信息
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({'images': args.images, 'args': vars(args)}, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved: {args.output}")


if __name__ == '__main__':
    main()
