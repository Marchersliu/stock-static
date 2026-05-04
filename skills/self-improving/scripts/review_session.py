#!/usr/bin/env python3
"""
自动复盘脚本 - 分析session日志，识别问题模式，提出改进建议

用法:
    python3 review_session.py --date 2026-05-04
    python3 review_session.py --latest          # 分析最新日志
    python3 review_session.py --stats           # 统计今日操作
"""
import argparse
import os
import re
from datetime import datetime

MEMORY_DIR = '/Users/hf/.kimi_openclaw/workspace/memory'
AGENTS_MD = '/Users/hf/.kimi_openclaw/workspace/AGENTS.md'

ERROR_KEYWORDS = ['error', 'err', 'fail', 'bug', 'fix', '修复', '失败', 'warn', 'warning']
EFFICIENCY_PATTERNS = {
    'sed_abuse': {'pattern': r'sed\s', 'desc': 'sed命令使用', 'threshold': 2},
    'manual_copy': {'pattern': r'cp\s', 'desc': '手动复制文件', 'threshold': 5},
    'syntax_error': {'pattern': r'SyntaxError|语法错误', 'desc': '语法错误', 'threshold': 1},
    'cache_issue': {'pattern': r'缓存|cache', 'desc': '缓存相关问题', 'threshold': 2},
}


def find_latest_memory():
    """找到最新的memory文件"""
    files = []
    for f in os.listdir(MEMORY_DIR):
        if f.startswith('2026-') and f.endswith('.md'):
            files.append(os.path.join(MEMORY_DIR, f))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def analyze_file(filepath):
    """分析日志文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    total_lines = len(lines)
    
    # 统计错误关键词
    error_count = sum(1 for line in lines if any(kw in line.lower() for kw in ERROR_KEYWORDS))
    
    # 统计效率模式
    efficiency_issues = []
    for name, cfg in EFFICIENCY_PATTERNS.items():
        matches = len(re.findall(cfg['pattern'], content, re.IGNORECASE))
        if matches >= cfg['threshold']:
            efficiency_issues.append({
                'name': name,
                'desc': cfg['desc'],
                'count': matches,
                'threshold': cfg['threshold']
            })
    
    # 检查敏感信息
    sensitive_patterns = [
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub token
        r'[a-f0-9]{40}',  # Tushare token pattern
    ]
    sensitive_found = []
    for pattern in sensitive_patterns:
        matches = re.findall(pattern, content)
        if matches:
            sensitive_found.extend(matches)
    
    return {
        'file': filepath,
        'total_lines': total_lines,
        'error_count': error_count,
        'efficiency_issues': efficiency_issues,
        'sensitive_found': len(sensitive_found),
        'sensitive_samples': sensitive_found[:3]
    }


def generate_report(analysis):
    """生成复盘报告"""
    print(f"\n{'='*60}")
    print(f"  Session复盘报告")
    print(f"  文件: {os.path.basename(analysis['file'])}")
    print(f"{'='*60}")
    
    print(f"\n📊 基础统计")
    print(f"  总行数: {analysis['total_lines']}")
    print(f"  错误/警告出现: {analysis['error_count']}次")
    
    if analysis['efficiency_issues']:
        print(f"\n⚠️ 效率问题（{len(analysis['efficiency_issues'])}项）")
        for issue in analysis['efficiency_issues']:
            print(f"  • {issue['desc']}: {issue['count']}次 (阈值: {issue['threshold']})")
            print(f"    建议: {get_suggestion(issue['name'])}")
    else:
        print(f"\n✅ 无效率问题")
    
    if analysis['sensitive_found'] > 0:
        print(f"\n🚨 敏感信息泄露警告: {analysis['sensitive_found']}处")
        for sample in analysis['sensitive_samples']:
            print(f"  • {sample[:20]}...")
    else:
        print(f"\n✅ 无敏感信息泄露")
    
    print(f"\n{'='*60}")
    print(generate_suggestions(analysis))


def get_suggestion(issue_name):
    """根据问题类型给出建议"""
    suggestions = {
        'sed_abuse': '使用edit工具或Python脚本替代sed处理HTML/JS',
        'manual_copy': '写脚本自动化文件复制和同步流程',
        'syntax_error': '修改后必须执行 node --check / python3 -m py_compile',
        'cache_issue': '服务端加Cache-Control头，URL加?v=N参数',
    }
    return suggestions.get(issue_name, '需要人工分析')


def generate_suggestions(analysis):
    """生成整体改进建议"""
    lines = ["\n📝 改进建议:\n"]
    
    if analysis['error_count'] > 10:
        lines.append("  • 错误/警告出现较频繁，建议排查根因")
    
    if any(i['name'] == 'sed_abuse' for i in analysis['efficiency_issues']):
        lines.append("  • AGENTS.md应新增：sed禁令规则")
    
    if analysis['sensitive_found'] > 0:
        lines.append("  • 立即检查敏感信息是否已泄露到GitHub等公开仓库")
        lines.append("  • 建议revoke并重置相关token")
    
    if not lines[-1].startswith('  •'):
        lines.append("  • 整体表现良好，继续保持")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Session Review Tool')
    parser.add_argument('--date', help='Review specific date (YYYY-MM-DD)')
    parser.add_argument('--latest', action='store_true', help='Review latest session')
    parser.add_argument('--stats', action='store_true', help='Show operation statistics')
    
    args = parser.parse_args()
    
    if args.date:
        filepath = os.path.join(MEMORY_DIR, f"{args.date}.md")
        if not os.path.exists(filepath):
            print(f"[ERR] File not found: {filepath}")
            return
    elif args.latest:
        filepath = find_latest_memory()
        if not filepath:
            print("[ERR] No memory files found")
            return
    else:
        filepath = find_latest_memory()
        if not filepath:
            print("[ERR] No memory files found")
            return
    
    analysis = analyze_file(filepath)
    generate_report(analysis)


if __name__ == '__main__':
    main()
