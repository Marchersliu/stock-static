---
name: image-analysis
description: 图像分析技能。分析截图、图表、K线图、流程图、文档截图等，提取文字（OCR）、识别图表类型、读取数据点、描述内容。适用于股票截图分析、报表截图识别、流程图理解。
---

# Image Analysis 图像分析

## 核心功能

| 功能 | 说明 | 适用场景 |
|------|------|----------|
| **OCR文字识别** | 提取图片中的文字 | 截图、文档照片 |
| **图表识别** | 识别K线图/柱状图/折线图/饼图 | 股票截图、报表 |
| **数据读取** | 读取图表中的具体数值 | 提取K线数据点 |
| **内容描述** | 生成图片内容描述 | 流程图、架构图 |
| **对比分析** | 对比两张图片的差异 | 前后对比、版本对比 |

## 支持的图表类型

- K线图（蜡烛图）
- 折线图/面积图
- 柱状图/条形图
- 饼图/环形图
- 散点图
- 热力图
- 流程图/架构图

## 用法

```bash
# OCR识别
python3 image_analysis.py /path/to/screenshot.png --ocr

# 图表分析
python3 image_analysis.py chart.png --chart --output data.json

# 股票K线截图分析
python3 image_analysis.py kline_screenshot.png --kline --stock 688485.SH

# 描述图片内容
python3 image_analysis.py diagram.png --describe

# 对比两张图
python3 image_analysis.py before.png after.png --diff
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/image-analysis/scripts
python3 image_analysis.py /path/to/image.png --describe
```

## 依赖安装

```bash
pip3 install pillow pytesseract
# macOS: brew install tesseract
```
