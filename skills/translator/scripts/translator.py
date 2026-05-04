#!/usr/bin/env python3
"""
多语言翻译 - 支持中英/中日/中韩/中法/中德等主流语言

用法:
    python3 translator.py "Hello world" --to zh
    python3 translator.py --file report_en.md --to zh --output report_zh.md
"""
import argparse
import json
import os

# 术语表路径
TERMS_PATH = '/Users/hf/.kimi_openclaw/workspace/memory/translation_terms.json'

DEFAULT_TERMS = {
    "碳酸锂": "Lithium Carbonate",
    "氢氧化锂": "Lithium Hydroxide",
    "固态电池": "Solid-state Battery",
    "人形机器人": "Humanoid Robot",
    "钙钛矿": "Perovskite",
    "电解液": "Electrolyte",
    "正极材料": "Cathode Material",
    "负极材料": "Anode Material",
    "动力电池": "Power Battery",
    "储能电池": "Energy Storage Battery",
    "光伏": "Photovoltaic",
    "风电": "Wind Power",
    "核电": "Nuclear Power",
    "充电桩": "Charging Pile",
    "换电站": "Battery Swap Station",
    "续航里程": "Driving Range",
    "能量密度": "Energy Density",
    "功率密度": "Power Density",
    "充电倍率": "Charge Rate",
    "循环寿命": "Cycle Life",
    "安全性能": "Safety Performance",
    "A股": "A-shares",
    "港股": "Hong Kong Stocks",
    "美股": "US Stocks",
    "涨停": "Limit Up",
    "跌停": "Limit Down",
    "主力资金": "Main Force Capital",
    "北向资金": "Northbound Capital",
    "成交量": "Trading Volume",
    "换手率": "Turnover Rate",
    "市盈率": "P/E Ratio",
    "市净率": "P/B Ratio",
    "市值": "Market Cap",
    "财报": "Financial Report",
    "营收": "Revenue",
    "净利润": "Net Profit",
    "毛利率": "Gross Margin",
    "净利率": "Net Margin",
    "ROE": "Return on Equity",
    "资产负债率": "Debt-to-Asset Ratio",
    "现金流": "Cash Flow",
    "自由现金流": "Free Cash Flow",
}


def load_terms():
    """加载术语表"""
    if os.path.exists(TERMS_PATH):
        with open(TERMS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_TERMS


def save_terms(terms):
    """保存术语表"""
    os.makedirs(os.path.dirname(TERMS_PATH), exist_ok=True)
    with open(TERMS_PATH, 'w', encoding='utf-8') as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)


def translate_text(text, source, target, mode='standard', terms=None):
    """
    翻译文本（框架函数，实际翻译由OpenClaw agent的LLM完成）
    
    此脚本主要用于：
    1. 预处理文本（术语替换）
    2. 格式化输出
    3. 文件批量处理
    """
    if terms is None:
        terms = load_terms()
    
    # 术语替换标记
    marked_text = text
    term_map = {}
    
    if source == 'zh' and target == 'en':
        # 中文→英文：替换中文术语为标记
        for zh, en in terms.items():
            if zh in marked_text:
                marker = f"__TERM_{len(term_map)}__"
                term_map[marker] = en
                marked_text = marked_text.replace(zh, marker)
    elif source == 'en' and target == 'zh':
        # 英文→中文
        for zh, en in terms.items():
            if en in marked_text:
                marker = f"__TERM_{len(term_map)}__"
                term_map[marker] = zh
                marked_text = marked_text.replace(en, marker)
    
    # 返回标记后的文本（供LLM翻译后还原术语）
    return {
        'marked_text': marked_text,
        'term_map': term_map,
        'source': source,
        'target': target,
        'mode': mode,
    }


def detect_language(text):
    """简单语言检测"""
    # 如果有中文字符，认为是中文
    if any('\u4e00' <= c <= '\u9fff' for c in text[:100]):
        return 'zh'
    # 如果有日文假名
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text[:100]):
        return 'ja'
    # 如果有韩文
    if any('\uac00' <= c <= '\ud7af' for c in text[:100]):
        return 'ko'
    # 默认英文
    return 'en'


def main():
    parser = argparse.ArgumentParser(description='Translator')
    parser.add_argument('text', nargs='?', help='Text to translate')
    parser.add_argument('--file', help='File to translate')
    parser.add_argument('--to', required=True, choices=['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru'], help='Target language')
    parser.add_argument('--from', dest='source', choices=['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru'], help='Source language (auto-detect if not specified)')
    parser.add_argument('--mode', default='standard', choices=['standard', 'professional', 'concise', 'literal'], help='Translation mode')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--terms', help='Custom terms JSON file')
    
    args = parser.parse_args()
    
    # 加载自定义术语表
    terms = DEFAULT_TERMS
    if args.terms and os.path.exists(args.terms):
        with open(args.terms, 'r', encoding='utf-8') as f:
            terms = json.load(f)
    
    # 获取输入文本
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("[ERR] Provide text or --file")
        return
    
    # 检测源语言
    source = args.source or detect_language(text)
    
    print(f"[Translator] {source} → {args.to} | Mode: {args.mode}")
    print(f"[Translator] Length: {len(text)} chars")
    
    # 预处理
    result = translate_text(text, source, args.to, args.mode, terms)
    
    print()
    print("="*60)
    print("  预处理完成（术语已标记）")
    print("="*60)
    print()
    print("  标记后文本（前200字符）:")
    print(f"  {result['marked_text'][:200]}...")
    print()
    print("  术语映射:")
    for marker, term in list(result['term_map'].items())[:5]:
        print(f"    {marker} → {term}")
    if len(result['term_map']) > 5:
        print(f"    ... 共 {len(result['term_map'])} 个术语")
    print()
    print("="*60)
    print("  提示：实际翻译由OpenClaw agent的LLM完成")
    print("  使用方法：告诉agent '翻译这段文本成英文'")
    print("="*60)
    
    # 保存预处理结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result['marked_text'])
        print(f"\n[OK] Preprocessed text saved: {args.output}")


if __name__ == '__main__':
    main()
