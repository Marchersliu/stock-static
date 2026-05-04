#!/usr/bin/env python3
"""新闻自动摘要 - 抽取式摘要，提取5W1H"""
import argparse, json, re

def summarize_text(text, mode='standard', max_sentences=5):
    """简单抽取式摘要"""
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if not sentences:
        return {'summary': text[:200], 'sentences': 0}
    
    # 评分：关键词密度、位置、长度
    scores = []
    for i, sent in enumerate(sentences):
        score = 0
        # 位置权重（开头和结尾）
        if i == 0: score += 3
        if i == len(sentences) - 1: score += 2
        # 数字/数据
        if re.search(r'\d+', sent): score += 2
        # 关键词
        keywords = ['营收', '净利润', '增长', '下跌', '涨幅', '政策', '数据', '报告', '宣布', '发布']
        score += sum(1 for kw in keywords if kw in sent)
        # 长度适中
        if 20 <= len(sent) <= 100: score += 1
        scores.append((score, sent))
    
    scores.sort(reverse=True)
    top = scores[:max_sentences]
    top.sort(key=lambda x: sentences.index(x[1]))  # 保持原文顺序
    
    summary = '。'.join(t[1] for t in top) + '。'
    
    # 5W1H提取
    five_w = {}
    for sent in sentences:
        if re.search(r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}', sent):
            five_w['when'] = re.search(r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}', sent).group()
        if any(w in sent for w in ['公司', '企业', '集团', '银行']):
            five_w['who'] = sent[:30]
        if any(w in sent for w in ['宣布', '发布', '推出', '完成']):
            five_w['what'] = sent[:50]
        if any(w in sent for w in ['在', '位于', '地区']):
            five_w['where'] = sent[:30]
        if any(w in sent for w in ['因为', '由于', '旨在', '为了']):
            five_w['why'] = sent[:50]
        if any(w in sent for w in ['通过', '利用', '采用']):
            five_w['how'] = sent[:50]
    
    return {
        'summary': summary,
        'sentences': len(top),
        '5w1h': five_w,
        'keywords': extract_keywords(text)
    }

def extract_keywords(text, topk=10):
    """简单关键词提取"""
    words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    freq = {}
    for w in words:
        if len(w) >= 2 and w not in ['的','了','在','是','和','与','及','等','有','为']:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:topk]

def main():
    parser = argparse.ArgumentParser(description='News Summarizer')
    parser.add_argument('--text', help='Text to summarize')
    parser.add_argument('--file', help='File to summarize')
    parser.add_argument('--url', help='URL to fetch and summarize')
    parser.add_argument('--mode', default='standard', choices=['headline', 'brief', 'standard', 'detailed'])
    parser.add_argument('--output', help='Output file')
    args = parser.parse_args()
    
    modes = {'headline': 1, 'brief': 3, 'standard': 5, 'detailed': 10}
    n = modes.get(args.mode, 5)
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    elif args.url:
        import requests
        text = requests.get(args.url, timeout=10).text[:5000]
    else:
        print('[ERR] Provide --text, --file, or --url')
        return
    
    result = summarize_text(text, args.mode, n)
    
    print(f'\n{"="*60}')
    print(f'  摘要 ({args.mode}, {result["sentences"]}句)')
    print(f'{"="*60}')
    print(f'\n{result["summary"]}\n')
    
    if result['5w1h']:
        print('  5W1H:')
        for k, v in result['5w1h'].items():
            print(f'    {k}: {v[:50]}')
    
    if result['keywords']:
        print(f'\n  关键词: {", ".join(f"{k}({v})" for k,v in result["keywords"])}')
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'\n[OK] Saved: {args.output}')

if __name__ == '__main__':
    main()
