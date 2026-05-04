#!/usr/bin/env python3
"""
认知记忆管理器 - 人脑式记忆系统的核心引擎

功能:
    编码(encode): 5W1H情境编码新记忆
    存储(store):   分层存储（情境/语义/程序/联想）
    检索(recall):  多模式检索（精确/联想/情境/情感/程序）
    遗忘(forget):  Ebbinghaus遗忘曲线自动衰减
    巩固(consolidate): 从短期记忆转入长期记忆

用法:
    # 编码新记忆
    python3 memory_manager.py --encode --what "修复恒指bug" --where "stock_dashboard" \
        --why "字段映射错误" --how "统一用parts[32]" --tags "恒指,腾讯接口"

    # 联想回忆
    python3 memory_manager.py --associate "腾讯接口"

    # 情境查询
    python3 memory_manager.py --context --who HF --when "2026-05"

    # 情感标记查询
    python3 memory_manager.py --emotional critical

    # 程序回忆
    python3 memory_manager.py --procedure "修复HTML"

    # 记忆健康度
    python3 memory_manager.py --health

    # 搜索（多模式）
    python3 memory_manager.py --search "恒指bug"
"""
import argparse
import json
import os
import re
import math
from datetime import datetime, timedelta
from collections import defaultdict

# 数据库文件
DB_PATH = '/Users/hf/.kimi_openclaw/workspace/memory/cognitive_memory.json'


def init_db():
    """初始化认知记忆数据库"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        db = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "episodes": [],      # 情境记忆
            "concepts": {},      # 语义记忆
            "procedures": {},    # 程序性记忆
            "associations": [],  # 联想网络
            "emotional_tags": {}, # 情感标记
            "last_access": {},   # 最后访问时间
            "consolidation_log": [] # 巩固历史
        }
        save_db(db)
        return db
    return load_db()


def load_db():
    """加载数据库"""
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_db(db):
    """保存数据库"""
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def compute_memory_strength(base, last_access_str, emotional_weight=0.5):
    """计算记忆强度（Ebbinghaus遗忘曲线）
    
    strength = base * exp(-decay_rate * days)
    decay_rate = 0.1 (routine) * (1 - emotional_weight * 0.5)
    """
    last_access = datetime.fromisoformat(last_access_str)
    days = (datetime.now() - last_access).total_seconds() / 86400
    decay_rate = 0.1 * (1 - emotional_weight * 0.5)
    strength = base * math.exp(-decay_rate * days)
    return min(strength, 3.0)


def generate_id(prefix):
    """生成记忆ID"""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{ts}_{len(load_db().get('episodes', [])):04d}"


def encode_episode(what, where=None, who=None, why=None, how=None, 
                   tags=None, emotional_weight=0.5, source=None):
    """5W1H情境编码"""
    db = load_db()
    
    episode = {
        "id": generate_id("ep"),
        "type": "episode",
        "encoding": {
            "when": datetime.now().isoformat(),
            "where": where or "unknown",
            "who": who or ["user"],
            "what": what,
            "why": why or "",
            "how": how or ""
        },
        "tags": tags or [],
        "emotional_weight": emotional_weight,
        "base_strength": 1.0,
        "access_count": 0,
        "last_access": datetime.now().isoformat()
    }
    
    db['episodes'].append(episode)
    
    # 自动提取概念到语义网络
    for tag in (tags or []):
        if tag not in db['concepts']:
            db['concepts'][tag] = {
                "definition": f"与'{what}'相关的概念",
                "first_seen": datetime.now().isoformat(),
                "associations": [],
                "emotional_tag": "neutral",
                "occurrence_count": 1
            }
        else:
            db['concepts'][tag]['occurrence_count'] += 1
    
    # 如果有how，尝试提取程序性记忆
    if how and len(how) > 20:
        proc_key = what[:30]
        if proc_key not in db['procedures']:
            db['procedures'][proc_key] = {
                "steps": [how],
                "context": where or "",
                "success_count": 1,
                "first_seen": datetime.now().isoformat()
            }
    
    save_db(db)
    print(f"[Encode] Episode recorded: {episode['id']}")
    print(f"  What: {what[:80]}")
    print(f"  Tags: {', '.join(tags or [])}")
    print(f"  Emotional: {emotional_weight}")
    return episode['id']


def encode_concept(name, definition, associations=None, emotional_tag="neutral"):
    """编码语义概念"""
    db = load_db()
    
    if name not in db['concepts']:
        db['concepts'][name] = {
            "definition": definition,
            "first_seen": datetime.now().isoformat(),
            "associations": associations or [],
            "emotional_tag": emotional_tag,
            "occurrence_count": 1
        }
    else:
        db['concepts'][name]['occurrence_count'] += 1
        # 合并新关联
        if associations:
            existing = {a['to'] for a in db['concepts'][name]['associations']}
            for a in associations:
                if a['to'] not in existing:
                    db['concepts'][name]['associations'].append(a)
                else:
                    # 增强现有关联
                    for ea in db['concepts'][name]['associations']:
                        if ea['to'] == a['to']:
                            ea['strength'] = min(ea['strength'] + 0.1, 1.0)
    
    save_db(db)
    print(f"[Encode] Concept recorded: {name}")
    return name


def encode_procedure(name, steps, context=""):
    """编码程序性记忆"""
    db = load_db()
    
    if name not in db['procedures']:
        db['procedures'][name] = {
            "steps": steps if isinstance(steps, list) else [steps],
            "context": context,
            "success_count": 1,
            "first_seen": datetime.now().isoformat()
        }
    else:
        db['procedures'][name]['steps'].extend(
            steps if isinstance(steps, list) else [steps]
        )
        db['procedures'][name]['success_count'] += 1
    
    save_db(db)
    print(f"[Encode] Procedure recorded: {name}")
    return name


def exact_recall(query, top_n=5):
    """精确回忆 - 关键词匹配"""
    db = load_db()
    query_lower = query.lower()
    matches = []
    
    for ep in db['episodes']:
        score = 0
        text = f"{ep['encoding']['what']} {ep['encoding']['why']} {ep['encoding']['how']}"
        text_lower = text.lower()
        
        # 精确匹配加分
        if query_lower in text_lower:
            score += 10
        
        # 标签匹配
        for tag in ep['tags']:
            if query_lower in tag.lower():
                score += 5
        
        # 情感权重加成
        score *= (0.5 + ep['emotional_weight'])
        
        # 记忆强度衰减
        strength = compute_memory_strength(
            ep['base_strength'], 
            ep['last_access'],
            ep['emotional_weight']
        )
        score *= strength
        
        if score > 0:
            matches.append({
                'episode': ep,
                'score': score,
                'strength': strength
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:top_n]


def associative_recall(seed_concept, depth=2, top_n=10):
    """联想回忆 - 从种子概念扩散激活关联网络"""
    db = load_db()
    
    activated = set()
    queue = [(seed_concept, 1.0, 0)]  # (concept, activation_strength, depth)
    results = []
    
    while queue and len(results) < top_n:
        concept, strength, d = queue.pop(0)
        
        if concept in activated or d > depth:
            continue
        activated.add(concept)
        
        # 查找相关的情境记忆
        for ep in db['episodes']:
            if concept in ep['tags'] or concept.lower() in ep['encoding']['what'].lower():
                mem_strength = compute_memory_strength(
                    ep['base_strength'],
                    ep['last_access'],
                    ep['emotional_weight']
                )
                final_score = strength * mem_strength * (0.5 + ep['emotional_weight'])
                results.append({
                    'episode': ep,
                    'score': final_score,
                    'activation_path': f"{seed_concept} → {concept} (depth={d})",
                    'strength': mem_strength
                })
        
        # 沿着概念网络扩散
        if concept in db['concepts']:
            for assoc in db['concepts'][concept].get('associations', []):
                next_concept = assoc['to']
                next_strength = strength * assoc.get('strength', 0.5)
                if next_strength > 0.2:  # 阈值过滤
                    queue.append((next_concept, next_strength, d + 1))
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]


def contextual_recall(who=None, where=None, when=None, what=None):
    """情境回忆 - 5W1H多维度查询"""
    db = load_db()
    matches = []
    
    for ep in db['episodes']:
        score = 0
        enc = ep['encoding']
        
        if who and any(who.lower() in str(w).lower() for w in (enc['who'] or [])):
            score += 5
        if where and where.lower() in enc['where'].lower():
            score += 5
        if when and when in enc['when']:
            score += 5
        if what and what.lower() in enc['what'].lower():
            score += 10
        
        if score > 0:
            strength = compute_memory_strength(
                ep['base_strength'],
                ep['last_access'],
                ep['emotional_weight']
            )
            matches.append({
                'episode': ep,
                'score': score * strength,
                'strength': strength
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches


def emotional_recall(tag="critical", top_n=10):
    """情感回忆 - 按重要性标记查询"""
    db = load_db()
    matches = []
    
    # 情感权重映射
    tag_weights = {
        "critical": 0.9,
        "important": 0.7,
        "routine": 0.3,
        "neutral": 0.5
    }
    threshold = tag_weights.get(tag, 0.5)
    
    for ep in db['episodes']:
        if ep['emotional_weight'] >= threshold:
            strength = compute_memory_strength(
                ep['base_strength'],
                ep['last_access'],
                ep['emotional_weight']
            )
            matches.append({
                'episode': ep,
                'score': ep['emotional_weight'] * strength,
                'strength': strength
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:top_n]


def procedure_recall(name=None, context=None):
    """程序回忆 - 检索如何做"""
    db = load_db()
    
    if name and name in db['procedures']:
        proc = db['procedures'][name]
        return {
            'name': name,
            'steps': proc['steps'],
            'context': proc['context'],
            'success_count': proc['success_count']
        }
    
    # 模糊匹配
    if context:
        matches = []
        for pname, proc in db['procedures'].items():
            if context.lower() in pname.lower() or context.lower() in proc['context'].lower():
                matches.append({
                    'name': pname,
                    'steps': proc['steps'],
                    'context': proc['context'],
                    'score': proc['success_count']
                })
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:5]
    
    return None


def access_memory(episode_id):
    """访问记忆 - 刷新遗忘曲线"""
    db = load_db()
    
    for ep in db['episodes']:
        if ep['id'] == episode_id:
            ep['access_count'] += 1
            ep['base_strength'] = min(ep['base_strength'] + 0.1, 3.0)
            ep['last_access'] = datetime.now().isoformat()
            save_db(db)
            return True
    return False


def display_results(results, mode="episode"):
    """格式化显示检索结果"""
    if not results:
        print("  (无记忆)")
        return
    
    print(f"\n  找到 {len(results)} 条记忆:\n")
    
    for i, r in enumerate(results, 1):
        if mode == "episode":
            ep = r['episode']
            enc = ep['encoding']
            strength = r.get('strength', 0)
            score = r.get('score', 0)
            
            # 记忆清晰度标记
            if strength > 0.7:
                clarity = "🟢"
            elif strength > 0.3:
                clarity = "🟡"
            else:
                clarity = "🔴"
            
            # 情感标记
            ew = ep['emotional_weight']
            if ew >= 0.9:
                emo = "🔴"
            elif ew >= 0.7:
                emo = "🟠"
            elif ew >= 0.5:
                emo = "🟡"
            else:
                emo = "⚪"
            
            print(f"  {i}. {clarity}{emo} [{ep['id']}]")
            print(f"     When: {enc['when'][:16]}")
            print(f"     What: {enc['what'][:80]}")
            if enc['why']:
                print(f"     Why:  {enc['why'][:80]}")
            if enc['how']:
                print(f"     How:  {enc['how'][:80]}")
            print(f"     Tags: {', '.join(ep['tags'])}")
            print(f"     Strength: {strength:.2f} | Score: {score:.1f} | Access: {ep['access_count']}")
            
            if 'activation_path' in r:
                print(f"     Path: {r['activation_path']}")
            print()
        
        elif mode == "procedure":
            print(f"  {i}. 📋 {r.get('name', 'Unknown')}")
            for j, step in enumerate(r.get('steps', [])[:3], 1):
                print(f"     {j}. {step[:100]}")
            print()


def health_check():
    """记忆健康度检查"""
    db = load_db()
    
    print(f"\n{'='*60}")
    print(f"  🧠 认知记忆健康报告")
    print(f"{'='*60}")
    
    total_episodes = len(db['episodes'])
    total_concepts = len(db['concepts'])
    total_procedures = len(db['procedures'])
    
    print(f"\n📊 记忆总量")
    print(f"  情境记忆: {total_episodes} 条")
    print(f"  语义概念: {total_concepts} 个")
    print(f"  程序记忆: {total_procedures} 条")
    
    # 记忆强度分布
    strength_dist = {"🟢清晰(>0.7)": 0, "🟡模糊(0.3-0.7)": 0, "🔴遗忘(<0.3)": 0}
    for ep in db['episodes']:
        s = compute_memory_strength(ep['base_strength'], ep['last_access'], ep['emotional_weight'])
        if s > 0.7:
            strength_dist["🟢清晰(>0.7)"] += 1
        elif s > 0.3:
            strength_dist["🟡模糊(0.3-0.7)"] += 1
        else:
            strength_dist["🔴遗忘(<0.3)"] += 1
    
    print(f"\n💪 记忆强度分布")
    for label, count in strength_dist.items():
        pct = count / max(total_episodes, 1) * 100
        bar = "█" * int(pct / 5)
        print(f"  {label}: {count:3d} ({pct:4.1f}%) {bar}")
    
    # 高频概念
    if db['concepts']:
        top_concepts = sorted(
            db['concepts'].items(),
            key=lambda x: x[1].get('occurrence_count', 0),
            reverse=True
        )[:5]
        print(f"\n🏷️ 高频概念")
        for name, data in top_concepts:
            print(f"  • {name}: {data.get('occurrence_count', 0)}次")
    
    # 最近记忆
    recent = sorted(
        db['episodes'],
        key=lambda x: x['last_access'],
        reverse=True
    )[:3]
    if recent:
        print(f"\n🕐 最近访问")
        for ep in recent:
            print(f"  • {ep['encoding']['what'][:60]}")
    
    # 建议
    print(f"\n💡 建议")
    if strength_dist["🔴遗忘(<0.3)"] > total_episodes * 0.3:
        print("  • 遗忘记忆较多，建议运行 --consolidate 巩固")
    if total_episodes < 10:
        print("  • 记忆库较空，多使用 --encode 积累")
    if not total_concepts:
        print("  • 概念网络为空，建议先用 --encode-concept 建立")
    
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='Cognitive Memory Manager')
    
    # 编码
    parser.add_argument('--encode', action='store_true', help='Encode new episode')
    parser.add_argument('--encode-concept', help='Encode new concept')
    parser.add_argument('--encode-procedure', help='Encode new procedure')
    
    parser.add_argument('--what', help='What happened')
    parser.add_argument('--where', help='Where')
    parser.add_argument('--who', help='Who involved (comma-separated)')
    parser.add_argument('--why', help='Why')
    parser.add_argument('--how', help='How')
    parser.add_argument('--tags', help='Tags (comma-separated)')
    parser.add_argument('--emotional', type=float, default=0.5, help='Emotional weight 0-1')
    parser.add_argument('--definition', help='Concept definition')
    parser.add_argument('--steps', help='Procedure steps (semicolon-separated)')
    
    # 检索
    parser.add_argument('--search', help='Search/query')
    parser.add_argument('--associate', help='Associative recall from concept')
    parser.add_argument('--context', action='store_true', help='Contextual recall')
    parser.add_argument('--procedure', help='Procedure recall')
    
    # 其他
    parser.add_argument('--health', action='store_true', help='Health check')
    parser.add_argument('--depth', type=int, default=2, help='Association depth')
    parser.add_argument('--top', type=int, default=5, help='Top N results')
    
    args = parser.parse_args()
    
    # 确保数据库存在
    init_db()
    
    if args.encode:
        who = args.who.split(',') if args.who else None
        tags = args.tags.split(',') if args.tags else None
        encode_episode(
            what=args.what,
            where=args.where,
            who=who,
            why=args.why,
            how=args.how,
            tags=tags,
            emotional_weight=args.emotional
        )
    
    elif args.encode_concept:
        encode_concept(
            name=args.encode_concept,
            definition=args.definition or f"Concept: {args.encode_concept}",
            emotional_tag="neutral"
        )
    
    elif args.encode_procedure:
        steps = args.steps.split(';') if args.steps else [args.how or "No steps"]
        encode_procedure(
            name=args.encode_procedure,
            steps=steps,
            context=args.where or ""
        )
    
    elif args.search:
        print(f"\n🔍 搜索: '{args.search}'")
        results = exact_recall(args.search, args.top)
        display_results(results)
    
    elif args.associate:
        print(f"\n🌐 联想回忆: '{args.associate}' (depth={args.depth})")
        results = associative_recall(args.associate, args.depth, args.top)
        display_results(results)
    
    elif args.context:
        print(f"\n📍 情境回忆")
        results = contextual_recall(
            who=args.who,
            where=args.where,
            when=args.search,
            what=args.what
        )
        display_results(results)
    
    elif args.procedure:
        print(f"\n📋 程序回忆: '{args.procedure}'")
        result = procedure_recall(name=args.procedure)
        if result:
            print(f"  名称: {result['name']}")
            print(f"  成功次数: {result['success_count']}")
            print(f"  步骤:")
            for i, step in enumerate(result['steps'], 1):
                print(f"    {i}. {step[:100]}")
        else:
            print("  未找到")
    
    elif args.health:
        health_check()
    
    else:
        health_check()


if __name__ == '__main__':
    main()
