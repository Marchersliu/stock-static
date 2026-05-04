#!/usr/bin/env python3
"""
知识本体管理 - 概念分类体系、实体关系网络、知识图谱

用法:
    python3 ontology.py add-concept "股票" --parent "金融资产"
    python3 ontology.py add-relation "股票" "has_sector" "轨交设备"
    python3 ontology.py add-instance "九州一轨" --concept "股票"
    python3 ontology.py find-path "九州一轨" "制造业"
    python3 ontology.py query "股票" --relations
    python3 ontology.py export --output ontology.json
"""
import argparse
import json
import os
from collections import defaultdict, deque

DB_PATH = '/Users/hf/.kimi_openclaw/workspace/memory/ontology.json'


def init_db():
    """初始化本体数据库"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        db = {
            "concepts": {},      # 概念 {name: {parent, properties}}
            "relations": [],     # 关系 [{from, type, to, properties}]
            "instances": {},     # 实例 {name: {concept, properties}}
        }
        save_db(db)
        return db
    return load_db()


def load_db():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_db(db):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def add_concept(name, parent=None, properties=None):
    """添加概念"""
    db = load_db()
    db['concepts'][name] = {
        'parent': parent,
        'properties': properties or {},
        'children': []
    }
    # 更新父概念的children
    if parent and parent in db['concepts']:
        if name not in db['concepts'][parent]['children']:
            db['concepts'][parent]['children'].append(name)
    save_db(db)
    print(f"[Ontology] Concept added: {name} (parent: {parent})")


def add_relation(from_concept, rel_type, to_concept, properties=None):
    """添加关系"""
    db = load_db()
    relation = {
        'from': from_concept,
        'type': rel_type,
        'to': to_concept,
        'properties': properties or {}
    }
    db['relations'].append(relation)
    save_db(db)
    print(f"[Ontology] Relation: {from_concept} --{rel_type}-- {to_concept}")


def add_instance(name, concept, properties=None):
    """添加实例"""
    db = load_db()
    db['instances'][name] = {
        'concept': concept,
        'properties': properties or {}
    }
    save_db(db)
    print(f"[Ontology] Instance: {name} (isa {concept})")


def get_concept(name):
    """查询概念"""
    db = load_db()
    return db['concepts'].get(name)


def get_instances(concept_name):
    """获取某概念的所有实例"""
    db = load_db()
    return {k: v for k, v in db['instances'].items() if v['concept'] == concept_name}


def find_path(start, end, max_depth=5):
    """查找两个概念/实例之间的路径"""
    db = load_db()
    
    # 构建图
    graph = defaultdict(list)
    for r in db['relations']:
        graph[r['from']].append((r['to'], r['type']))
        # 双向
        if r['type'] in ['isa', 'part_of', 'has_sector']:
            graph[r['to']].append((r['from'], f"_{r['type']}"))
    
    # BFS
    queue = deque([(start, [(start, 'start')])])
    visited = {start}
    
    while queue:
        node, path = queue.popleft()
        if node == end:
            return path
        if len(path) > max_depth:
            continue
        
        for neighbor, rel_type in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [(neighbor, rel_type)]))
    
    return None


def infer(start_concept, rel_type, max_depth=3):
    """推理：从概念出发，沿关系类型推断"""
    db = load_db()
    graph = defaultdict(list)
    for r in db['relations']:
        if r['type'] == rel_type or rel_type == 'all':
            graph[r['from']].append(r['to'])
    
    results = set()
    queue = deque([(start_concept, 0)])
    visited = {start_concept}
    
    while queue:
        node, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                results.add(neighbor)
                queue.append((neighbor, depth + 1))
    
    return list(results)


def query(name, show_relations=False, show_instances=False):
    """综合查询"""
    db = load_db()
    
    print(f"\n{'='*60}")
    print(f"  🔍 查询: {name}")
    print(f"{'='*60}")
    
    # 概念信息
    concept = db['concepts'].get(name)
    if concept:
        print(f"\n  📦 概念: {name}")
        print(f"     父概念: {concept.get('parent', '无')}")
        print(f"     子概念: {', '.join(concept.get('children', [])) or '无'}")
        if concept.get('properties'):
            print(f"     属性: {json.dumps(concept['properties'], ensure_ascii=False)}")
    
    # 实例信息
    instance = db['instances'].get(name)
    if instance:
        print(f"\n  🎯 实例: {name}")
        print(f"     类型: {instance['concept']}")
        if instance.get('properties'):
            print(f"     属性: {json.dumps(instance['properties'], ensure_ascii=False)}")
    
    # 关系
    if show_relations:
        related = [r for r in db['relations'] if r['from'] == name or r['to'] == name]
        if related:
            print(f"\n  🔗 关系 ({len(related)}条):")
            for r in related:
                direction = "→" if r['from'] == name else "←"
                other = r['to'] if r['from'] == name else r['from']
                print(f"     {name} {direction}{r['type']}→ {other}")
    
    # 实例列表
    if show_instances and concept:
        instances = get_instances(name)
        if instances:
            print(f"\n  📋 实例列表 ({len(instances)}个):")
            for iname, idata in instances.items():
                print(f"     • {iname}")


def export_db(output_path, fmt='json'):
    """导出数据库"""
    db = load_db()
    with open(output_path, 'w', encoding='utf-8') as f:
        if fmt == 'json':
            json.dump(db, f, ensure_ascii=False, indent=2)
        else:
            # 简单文本格式
            f.write("# Ontology Export\n\n")
            f.write("## Concepts\n")
            for name, data in db['concepts'].items():
                f.write(f"- {name} (parent: {data.get('parent', 'None')})\n")
            f.write("\n## Relations\n")
            for r in db['relations']:
                f.write(f"- {r['from']} --{r['type']}-- {r['to']}\n")
            f.write("\n## Instances\n")
            for name, data in db['instances'].items():
                f.write(f"- {name} isa {data['concept']}\n")
    print(f"[Ontology] Exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Ontology Manager')
    subparsers = parser.add_subparsers(dest='command')
    
    # add-concept
    p = subparsers.add_parser('add-concept')
    p.add_argument('name')
    p.add_argument('--parent')
    p.add_argument('--property', nargs='*')
    
    # add-relation
    p = subparsers.add_parser('add-relation')
    p.add_argument('from_concept')
    p.add_argument('rel_type')
    p.add_argument('to_concept')
    
    # add-instance
    p = subparsers.add_parser('add-instance')
    p.add_argument('name')
    p.add_argument('--concept', required=True)
    
    # query
    p = subparsers.add_parser('query')
    p.add_argument('name')
    p.add_argument('--relations', action='store_true')
    p.add_argument('--instances', action='store_true')
    
    # find-path
    p = subparsers.add_parser('find-path')
    p.add_argument('start')
    p.add_argument('end')
    
    # infer
    p = subparsers.add_parser('infer')
    p.add_argument('concept')
    p.add_argument('--relation', default='all')
    
    # export
    p = subparsers.add_parser('export')
    p.add_argument('--output', required=True)
    p.add_argument('--format', default='json', choices=['json', 'text'])
    
    args = parser.parse_args()
    
    init_db()
    
    if args.command == 'add-concept':
        props = {}
        if args.property:
            for p in args.property:
                if '=' in p:
                    k, v = p.split('=', 1)
                    props[k] = v
        add_concept(args.name, args.parent, props)
    
    elif args.command == 'add-relation':
        add_relation(args.from_concept, args.rel_type, args.to_concept)
    
    elif args.command == 'add-instance':
        add_instance(args.name, args.concept)
    
    elif args.command == 'query':
        query(args.name, args.relations, args.instances)
    
    elif args.command == 'find-path':
        path = find_path(args.start, args.end)
        if path:
            print(f"\n  路径: {' → '.join(f'{n}({r})' for n, r in path)}")
        else:
            print(f"\n  未找到路径")
    
    elif args.command == 'infer':
        results = infer(args.concept, args.relation)
        print(f"\n  从'{args.concept}'推断 ({args.relation}):")
        for r in results:
            print(f"    • {r}")
    
    elif args.command == 'export':
        export_db(args.output, args.format)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
