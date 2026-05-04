#!/usr/bin/env python3
"""
自我批评引擎 - 识别错误和可改进点

功能:
    - 分析任务输出，识别明显错误
    - 对比最佳实践，找出偏差
    - 从用户纠正中学习规则
    - 生成批评报告

批评类型:
    1. 事实错误 (FactError): 数据/代码/逻辑错误
    2. 安全违规 (SecurityBreach): 敏感信息泄露、危险操作
    3. 效率低下 (Inefficient): 冗余步骤、token浪费
    4. 风格偏差 (StyleIssue): 不符合用户偏好
    5. 遗漏疏忽 (Omission): 遗漏关键步骤/信息

用法:
    # 批评单个输出
    python3 critique.py --text "输出内容" --task "任务描述"
    
    # 从日志批评
    python3 critique.py --file memory/2026-05-04.md
    
    # 查看批评统计
    python3 critique.py --stats
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_manager import encode_episode, encode_concept

CRITIQUE_LOG = '/Users/hf/.kimi_openclaw/workspace/memory/critiques.json'

# 批评规则库
CRITIQUE_RULES = {
    'FactError': {
        'patterns': [
            {'regex': r'错误[:：]|不对|错了|incorrect|wrong|error', 'desc': '包含错误关键词', 'severity': 'high'},
            {'regex': r'修复[:：]|fix|bug|修正', 'desc': '提到修复某问题', 'severity': 'medium'},
            {'regex': r'应该是|应该是|正确的是', 'desc': '纠正之前的输出', 'severity': 'high'},
        ],
        'examples': [
            '输出"恒指+2026%"（实际是+1.62%）',
            '用了parts[30]而非parts[32]',
            'token写入了对话而非存本地',
        ]
    },
    'SecurityBreach': {
        'patterns': [
            {'regex': r'ghp_[a-zA-Z0-9]{36}', 'desc': 'GitHub Token泄露', 'severity': 'critical'},
            {'regex': r'[a-f0-9]{40}', 'desc': '疑似API Token', 'severity': 'critical'},
            {'regex': r'rm -rf /|mkfs |chmod 777', 'desc': '危险命令', 'severity': 'critical'},
            {'regex': r'docker prune.*-[fa]', 'desc': '强制清理Docker', 'severity': 'high'},
        ],
        'examples': [
            'token出现在对话回复中',
            '建议用户执行rm -rf',
            'GitHub PAT暴露在日志',
        ]
    },
    'Inefficient': {
        'patterns': [
            {'regex': r'手动|逐个|一步一步|反复', 'desc': '手动操作过多', 'severity': 'medium'},
            {'regex': r'可以简化为|有更简单的|一步就能', 'desc': '自我意识到冗余', 'severity': 'medium'},
            {'regex': r'尝试.*然后.*再|试了.*又', 'desc': '反复尝试', 'severity': 'low'},
        ],
        'examples': [
            '用10次edit工具完成本该1次完成的事',
            '先cp再edit再验证而非一步到位',
            '重复搜索同一信息',
        ]
    },
    'StyleIssue': {
        'patterns': [
            {'regex': r'很高兴|我很乐意|让我来帮您', 'desc': '废话/客套话', 'severity': 'low'},
            {'regex': r'当然啦|当然的|没问题', 'desc': '填充词', 'severity': 'low'},
            {'regex': r'感谢您的耐心|希望对您有帮助', 'desc': '结尾客套', 'severity': 'low'},
        ],
        'examples': [
            '用户偏好简洁但输出包含3段客套话',
            '用了表格而非用户偏好的列表',
            'emoji过多不符合严肃场合',
        ]
    },
    'Omission': {
        'patterns': [
            {'regex': r'TODO|遗留|待解决|待处理|未完成|稍后', 'desc': '未完成事项', 'severity': 'medium'},
            {'regex': r'忘记|忘了|漏了|遗漏', 'desc': '承认遗漏', 'severity': 'high'},
            {'regex': r'还需要|还要|还有一步', 'desc': '未完成', 'severity': 'medium'},
        ],
        'examples': [
            '修改了文件但忘记验证语法',
            '说了部署但没提如何持久化',
            '给了方案但遗漏关键参数',
        ]
    }
}


def init_critique_log():
    """初始化批评日志"""
    os.makedirs(os.path.dirname(CRITIQUE_LOG), exist_ok=True)
    if not os.path.exists(CRITIQUE_LOG):
        with open(CRITIQUE_LOG, 'w', encoding='utf-8') as f:
            json.dump({
                "version": "1.0",
                "critiques": [],
                "rule_violations": {},
                "learned_rules": []
            }, f, ensure_ascii=False, indent=2)
    return load_critique_log()


def load_critique_log():
    with open(CRITIQUE_LOG, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_critique_log(data):
    with open(CRITIQUE_LOG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def critique_text(text, task_desc="", context=""):
    """批评分析文本"""
    critiques = []
    
    for category, rules in CRITIQUE_RULES.items():
        for pattern in rules['patterns']:
            matches = re.findall(pattern['regex'], text, re.IGNORECASE)
            if matches:
                critiques.append({
                    'category': category,
                    'severity': pattern['severity'],
                    'pattern': pattern['desc'],
                    'matches': len(matches),
                    'examples': matches[:3]
                })
    
    # 用户偏好检查
    try:
        with open('/Users/hf/.kimi_openclaw/workspace/memory/preferences.json', 'r') as f:
            prefs = json.load(f)
        
        for pref in prefs.get('preferences', []):
            pref_text = pref.get('preference', '')
            # 检查是否违反偏好
            if '简洁' in pref_text and len(text) > 2000:
                critiques.append({
                    'category': 'StyleIssue',
                    'severity': 'medium',
                    'pattern': f"违反偏好: {pref_text}",
                    'matches': 1,
                    'examples': [f"输出{len(text)}字符，违反简洁偏好"]
                })
    except:
        pass
    
    return critiques


def critique_session_log(filepath):
    """批评整个session日志"""
    if not os.path.exists(filepath):
        print(f"[ERR] File not found: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    log = init_critique_log()
    all_critiques = []
    
    # 分段批评
    sections = re.split(r'###\s+', content)
    for section in sections[1:]:  # 跳过第一个空段
        title_match = re.match(r'(.+?)\n', section)
        title = title_match.group(1) if title_match else "Unknown"
        
        section_critiques = critique_text(section, title)
        if section_critiques:
            all_critiques.append({
                'section': title[:80],
                'critiques': section_critiques
            })
            
            # 记录到日志
            for c in section_critiques:
                entry = {
                    'id': f"crit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(log['critiques'])}",
                    'timestamp': datetime.now().isoformat(),
                    'task': title[:100],
                    'category': c['category'],
                    'severity': c['severity'],
                    'issue': c['pattern'],
                    'source_file': os.path.basename(filepath)
                }
                log['critiques'].append(entry)
                
                # 统计违规
                cat = c['category']
                if cat not in log['rule_violations']:
                    log['rule_violations'][cat] = {'count': 0, 'last': None}
                log['rule_violations'][cat]['count'] += 1
                log['rule_violations'][cat]['last'] = datetime.now().isoformat()
    
    save_critique_log(log)
    
    # 输出报告
    if all_critiques:
        print(f"\n{'='*60}")
        print(f"  🔍 批评报告: {os.path.basename(filepath)}")
        print(f"{'='*60}")
        
        for item in all_critiques:
            print(f"\n  📌 {item['section'][:60]}")
            for c in item['critiques']:
                severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                icon = severity_icon.get(c['severity'], '⚪')
                print(f"    {icon} [{c['category']}] {c['pattern']} ({c['severity']})")
                if c['examples']:
                    print(f"       例: {str(c['examples'][0])[:80]}")
    else:
        print(f"[Critique] {os.path.basename(filepath)}: No issues found ✅")
    
    return all_critiques


def generate_learned_rules():
    """从批评历史生成学习规则"""
    log = init_critique_log()
    
    rules = []
    
    # 高频违规 → 规则
    for cat, data in log['rule_violations'].items():
        if data['count'] >= 2:
            rule = {
                'from_critique': True,
                'category': cat,
                'trigger_count': data['count'],
                'rule': f"避免{cat}: {CRITIQUE_RULES.get(cat, {}).get('examples', [''])[0]}",
                'confidence': min(0.5 + data['count'] * 0.1, 0.95),
                'date': data['last']
            }
            rules.append(rule)
    
    # 保存
    log['learned_rules'] = rules
    save_critique_log(log)
    
    return rules


def show_stats():
    """显示批评统计"""
    log = init_critique_log()
    
    print(f"\n{'='*60}")
    print(f"  📊 批评统计")
    print(f"{'='*60}")
    
    print(f"\n  总批评次数: {len(log['critiques'])}")
    
    # 按类别统计
    from collections import Counter
    cats = Counter(c['category'] for c in log['critiques'])
    print(f"\n  按类别:")
    for cat, count in cats.most_common():
        print(f"    • {cat}: {count}次")
    
    # 按严重程度
    sevs = Counter(c['severity'] for c in log['critiques'])
    print(f"\n  按严重程度:")
    sev_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
    for sev, count in sevs.most_common():
        print(f"    {sev_icon.get(sev, '⚪')} {sev}: {count}次")
    
    # 已学规则
    rules = generate_learned_rules()
    if rules:
        print(f"\n  💡 已生成{len(rules)}条学习规则:")
        for r in rules[:5]:
            print(f"    • [{r['category']}] {r['rule'][:60]}")


def main():
    parser = argparse.ArgumentParser(description='Self-Critique Engine')
    parser.add_argument('--text', help='Text to critique')
    parser.add_argument('--task', help='Task description')
    parser.add_argument('--file', help='Session log file to critique')
    parser.add_argument('--stats', action='store_true', help='Show critique statistics')
    parser.add_argument('--learn', action='store_true', help='Generate learned rules')
    
    args = parser.parse_args()
    
    if args.text:
        critiques = critique_text(args.text, args.task or "")
        if critiques:
            print(f"\n  Found {len(critiques)} issues:")
            for c in critiques:
                print(f"    [{c['category']}] {c['pattern']} ({c['severity']})")
        else:
            print("  ✅ No issues found")
    
    elif args.file:
        critique_session_log(args.file)
    
    elif args.stats:
        show_stats()
    
    elif args.learn:
        rules = generate_learned_rules()
        print(f"[Learn] Generated {len(rules)} learned rules")
        for r in rules:
            print(f"  • {r['rule'][:60]}")
    
    else:
        # 默认批评最新日志
        import glob
        files = sorted(glob.glob('/Users/hf/.kimi_openclaw/workspace/memory/2026-*.md'),
                      key=os.path.getmtime, reverse=True)
        if files:
            critique_session_log(files[0])
        else:
            print("[ERR] No log files found")


if __name__ == '__main__':
    main()
