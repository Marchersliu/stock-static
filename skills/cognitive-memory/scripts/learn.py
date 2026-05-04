#!/usr/bin/env python3
"""
自我学习引擎 - 将改进经验写入记忆，下次自动应用

流程:
    1. 收集反思结果 (reflect.py)
    2. 收集批评结果 (critique.py)
    3. 提取改进规则
    4. 写入认知记忆 + 偏好数据库
    5. 生成学习摘要

学习规则类型:
    - 修正规则: 旧做法 → 新做法
    - 偏好规则: 用户喜欢/不喜欢
    - 效率规则: 更优的工作方式
    - 安全规则: 禁止/必须遵守
    - 领域规则: 特定领域的知识

用法:
    # 从反思和批评中学习
    python3 learn.py --from-reflection --from-critique
    
    # 手动添加学习规则
    python3 learn.py --add-rule "不要用sed改HTML" "用edit工具" --type correction
    
    # 查看学习成果
    python3 learn.py --summary
    
    # 应用到USER.md
    python3 learn.py --apply
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_manager import encode_episode, encode_concept

LEARN_LOG = '/Users/hf/.kimi_openclaw/workspace/memory/learning.json'
RULES_DB = '/Users/hf/.kimi_openclaw/workspace/memory/learned_rules.json'


def init_learning_db():
    """初始化学习数据库"""
    os.makedirs(os.path.dirname(LEARN_LOG), exist_ok=True)
    for path in [LEARN_LOG, RULES_DB]:
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": "1.0",
                    "rules": [],
                    "improvements": [],
                    "applied_count": 0
                }, f, ensure_ascii=False, indent=2)


def load_learning_db():
    with open(LEARN_LOG, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_learning_db(data):
    with open(LEARN_LOG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_rules_db():
    if not os.path.exists(RULES_DB):
        init_learning_db()
    with open(RULES_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_rules_db(data):
    with open(RULES_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def learn_from_reflection():
    """从反思日志学习"""
    reflect_path = '/Users/hf/.kimi_openclaw/workspace/memory/reflections.json'
    if not os.path.exists(reflect_path):
        print("[Learn] No reflections found")
        return []
    
    with open(reflect_path, 'r', encoding='utf-8') as f:
        reflect_log = json.load(f)
    
    rules = []
    
    # 从低分反思中提取规则
    for ref in reflect_log.get('reflections', []):
        if ref['total_score'] < 7:
            for issue in ref.get('issues', []):
                # 将问题转化为规则
                rule = {
                    'id': f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(rules)}",
                    'source': 'reflection',
                    'trigger': issue,
                    'rule': f"避免: {issue}",
                    'context': ref['task'][:100],
                    'confidence': min(0.5 + (7 - ref['total_score']) * 0.1, 0.9),
                    'date': ref['timestamp'],
                    'applied_count': 0,
                    'type': 'avoidance'
                }
                rules.append(rule)
    
    return rules


def learn_from_critique():
    """从批评日志学习"""
    critique_path = '/Users/hf/.kimi_openclaw/workspace/memory/critiques.json'
    if not os.path.exists(critique_path):
        print("[Learn] No critiques found")
        return []
    
    with open(critique_path, 'r', encoding='utf-8') as f:
        critique_log = json.load(f)
    
    rules = []
    
    # 从批评历史生成规则
    for cat, data in critique_log.get('rule_violations', {}).items():
        if data['count'] >= 2:
            rule = {
                'id': f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(rules)}",
                'source': 'critique',
                'trigger': cat,
                'rule': f"严格遵守: {cat}规则",
                'context': f"已违反{data['count']}次",
                'confidence': min(0.5 + data['count'] * 0.1, 0.95),
                'date': data['last'],
                'applied_count': 0,
                'type': 'compliance'
            }
            rules.append(rule)
    
    return rules


def learn_from_user_corrections():
    """从用户纠正中学习"""
    pref_path = '/Users/hf/.kimi_openclaw/workspace/memory/preferences.json'
    if not os.path.exists(pref_path):
        return []
    
    with open(pref_path, 'r', encoding='utf-8') as f:
        prefs = json.load(f)
    
    rules = []
    
    # 从纠正记录提取规则
    for corr in prefs.get('corrections', []):
        rule = {
            'id': f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(rules)}",
            'source': 'user_correction',
            'trigger': corr.get('old_behavior', '')[:100],
            'rule': f"用'{corr.get('new_behavior', '')[:50]}'替代'{corr.get('old_behavior', '')[:50]}'",
            'context': corr.get('context', '')[:100],
            'confidence': 0.9,
            'date': corr.get('date', datetime.now().isoformat()),
            'applied_count': corr.get('applied_count', 0),
            'type': 'correction'
        }
        rules.append(rule)
    
    # 从偏好提取规则
    for pref in prefs.get('preferences', []):
        rule = {
            'id': f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(rules)}",
            'source': 'user_preference',
            'trigger': pref.get('category', 'general'),
            'rule': pref.get('preference', '')[:100],
            'context': pref.get('context', '')[:100],
            'confidence': 0.8 if pref.get('confidence') == 'high' else 0.6,
            'date': pref.get('date', datetime.now().isoformat()),
            'applied_count': 0,
            'type': 'preference'
        }
        rules.append(rule)
    
    return rules


def add_rule(trigger, action, rule_type='correction', context=""):
    """手动添加规则"""
    rules_db = load_rules_db()
    
    rule = {
        'id': f"rule_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'source': 'manual',
        'trigger': trigger,
        'rule': action,
        'context': context,
        'confidence': 0.9,
        'date': datetime.now().isoformat(),
        'applied_count': 0,
        'type': rule_type
    }
    
    rules_db['rules'].append(rule)
    save_rules_db(rules_db)
    
    # 同时编码到认知记忆
    encode_episode(
        what=f"学习规则: {trigger[:80]} → {action[:80]}",
        why="手动添加的学习规则",
        how=f"类型: {rule_type}",
        tags=['学习规则', rule_type],
        emotional_weight=0.7
    )
    
    print(f"[Learn] Rule added: {trigger[:50]} → {action[:50]}")
    return rule


def generate_summary():
    """生成学习摘要"""
    rules_db = load_rules_db()
    learn_db = load_learning_db()
    
    rules = rules_db.get('rules', [])
    
    if not rules:
        print("[Learn] No learned rules yet")
        return
    
    print(f"\n{'='*60}")
    print(f"  📚 学习成果摘要")
    print(f"{'='*60}")
    
    # 按类型分组
    from collections import defaultdict
    by_type = defaultdict(list)
    for r in rules:
        by_type[r['type']].append(r)
    
    for rule_type, type_rules in by_type.items():
        print(f"\n  【{rule_type}】({len(type_rules)}条)")
        for r in type_rules[-5:]:
            conf_bar = "█" * int(r['confidence'] * 10)
            print(f"    • {r['rule'][:60]}")
            print(f"      置信度: {r['confidence']:.2f} {conf_bar}")
            print(f"      来源: {r['source']} | 应用: {r['applied_count']}次")
    
    # 统计
    total = len(rules)
    high_conf = sum(1 for r in rules if r['confidence'] >= 0.8)
    applied = sum(r['applied_count'] for r in rules)
    
    print(f"\n  📊 统计: {total}条规则 | 高置信度: {high_conf} | 已应用: {applied}次")
    print(f"{'='*60}")


def apply_rules_to_user_md():
    """将学习到的规则应用到 USER.md"""
    rules_db = load_rules_db()
    user_md = '/Users/hf/.kimi_openclaw/workspace/USER.md'
    
    if not os.path.exists(user_md):
        print(f"[Learn] {user_md} not found")
        return
    
    with open(user_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    added = 0
    
    for rule in rules_db.get('rules', []):
        if rule['confidence'] >= 0.8 and rule['applied_count'] >= 2:
            rule_text = f"- **{rule['type']}**: {rule['rule'][:80]}"
            if rule_text not in content:
                # 追加到文件末尾或特定部分
                if '## 学习规则' not in content and '## Learned Rules' not in content:
                    content += "\n\n## 学习规则\n\n"
                content += f"\n{rule_text}\n"
                added += 1
                rule['applied_count'] += 1
    
    if added > 0:
        with open(user_md, 'w', encoding='utf-8') as f:
            f.write(content)
        save_rules_db(rules_db)
        print(f"[Learn] Applied {added} rules to USER.md")
    else:
        print("[Learn] No new high-confidence rules to apply")


def main():
    parser = argparse.ArgumentParser(description='Self-Learning Engine')
    parser.add_argument('--from-reflection', action='store_true', help='Learn from reflections')
    parser.add_argument('--from-critique', action='store_true', help='Learn from critiques')
    parser.add_argument('--from-corrections', action='store_true', help='Learn from user corrections')
    parser.add_argument('--add-rule', nargs=2, metavar=('TRIGGER', 'ACTION'), help='Add manual rule')
    parser.add_argument('--type', default='correction', help='Rule type')
    parser.add_argument('--context', default='', help='Rule context')
    parser.add_argument('--summary', action='store_true', help='Show learning summary')
    parser.add_argument('--apply', action='store_true', help='Apply rules to USER.md')
    parser.add_argument('--all', action='store_true', help='Learn from all sources')
    
    args = parser.parse_args()
    
    init_learning_db()
    
    new_rules = []
    
    if args.from_reflection or args.all:
        new_rules.extend(learn_from_reflection())
    
    if args.from_critique or args.all:
        new_rules.extend(learn_from_critique())
    
    if args.from_corrections or args.all:
        new_rules.extend(learn_from_user_corrections())
    
    if new_rules:
        rules_db = load_rules_db()
        existing_triggers = {r['trigger'] for r in rules_db['rules']}
        
        added = 0
        for rule in new_rules:
            if rule['trigger'] not in existing_triggers:
                rules_db['rules'].append(rule)
                added += 1
        
        save_rules_db(rules_db)
        print(f"[Learn] Learned {added} new rules from {len(new_rules)} candidates")
    
    if args.add_rule:
        add_rule(args.add_rule[0], args.add_rule[1], args.type, args.context)
    
    if args.summary:
        generate_summary()
    
    if args.apply:
        apply_rules_to_user_md()
    
    if not any([args.from_reflection, args.from_critique, args.from_corrections,
                args.add_rule, args.summary, args.apply, args.all]):
        generate_summary()


if __name__ == '__main__':
    main()
