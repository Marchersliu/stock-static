#!/usr/bin/env python3
"""
分层记忆管理器 - HOT → WARM → COLD 自动晋升/降级

分层架构:
    HOT (热层):   频繁使用，随时提取，驻留内存
    WARM (温层):  项目/领域相关，按需加载
    COLD (冷层):  归档记忆，长期存储，偶尔激活

晋升/降级规则:
    3次使用    → 从WARM晋升HOT
    7天不用   → 从HOT降级WARM
    30天不用  → 从WARM降级COLD
    90天不用  → 从COLD归档（压缩存储）
    强关联激活 → COLD可晋升WARM

用法:
    # 检查记忆层级
    python3 tiered_memory.py --status
    
    # 访问记忆（自动更新层级）
    python3 tiered_memory.py --access "股票监控"
    
    # 运行晋升/降级
    python3 tiered_memory.py --rebalance
    
    # 压缩归档
    python3 tiered_memory.py --archive
"""
import argparse
import json
import os
import sys
import math
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_manager import load_db, save_db, compute_memory_strength

TIER_CONFIG = {
    'HOT': {
        'description': '热层 - 高频使用，随时提取',
        'max_items': 20,
        'decay_days': 7,       # 7天不用降级
        'access_threshold': 3,  # 3次使用晋升
    },
    'WARM': {
        'description': '温层 - 项目/领域相关',
        'max_items': 50,
        'decay_days': 30,      # 30天不用降级
        'access_threshold': 3,  # 3次使用晋升HOT
    },
    'COLD': {
        'description': '冷层 - 归档记忆',
        'max_items': 200,
        'decay_days': 90,      # 90天不用归档
        'access_threshold': 1,  # 1次强关联激活可晋升WARM
    },
    'ARCHIVED': {
        'description': '归档 - 压缩存储',
        'max_items': float('inf'),
        'decay_days': float('inf'),
        'access_threshold': float('inf'),
    }
}


def get_tier_data():
    """获取分层数据"""
    db = load_db()
    if 'tiers' not in db:
        db['tiers'] = {'HOT': [], 'WARM': [], 'COLD': [], 'ARCHIVED': []}
        save_db(db)
    return db['tiers']


def assign_tier(item_id, item_type='episode'):
    """为新记忆分配层级"""
    db = load_db()
    tiers = get_tier_data()
    
    # 新记忆默认WARM（如果是重要事件则为HOT）
    db_item = None
    if item_type == 'episode':
        db_item = next((e for e in db['episodes'] if e['id'] == item_id), None)
    elif item_type == 'concept':
        db_item = db['concepts'].get(item_id)
    
    default_tier = 'WARM'
    if db_item and db_item.get('emotional_weight', 0) >= 0.8:
        default_tier = 'HOT'
    
    # 检查是否已在某层
    for tier_name, items in tiers.items():
        if item_id in [i['id'] for i in items]:
            return tier_name
    
    # 分配到默认层
    tiers[default_tier].append({
        'id': item_id,
        'type': item_type,
        'assigned_at': datetime.now().isoformat(),
        'access_count': 0,
        'last_access': datetime.now().isoformat(),
        'promotion_history': []
    })
    
    db['tiers'] = tiers
    save_db(db)
    
    return default_tier


def rebalance_tiers():
    """运行晋升/降级"""
    db = load_db()
    tiers = get_tier_data()
    now = datetime.now()
    
    changes = []
    
    # 检查HOT层降级
    for item in list(tiers['HOT']):
        last_access = datetime.fromisoformat(item['last_access'])
        days_inactive = (now - last_access).days
        
        if days_inactive >= TIER_CONFIG['HOT']['decay_days']:
            # 降级到WARM
            tiers['HOT'].remove(item)
            item['promotion_history'].append({
                'from': 'HOT',
                'to': 'WARM',
                'reason': f'{days_inactive}天未访问',
                'date': now.isoformat()
            })
            tiers['WARM'].append(item)
            changes.append(f"{item['id'][:20]}... HOT→WARM ({days_inactive}天未用)")
    
    # 检查WARM层（晋升或降级）
    for item in list(tiers['WARM']):
        last_access = datetime.fromisoformat(item['last_access'])
        days_inactive = (now - last_access).days
        
        if item['access_count'] >= TIER_CONFIG['WARM']['access_threshold']:
            # 晋升到HOT
            tiers['WARM'].remove(item)
            item['promotion_history'].append({
                'from': 'WARM',
                'to': 'HOT',
                'reason': f'{item["access_count"]}次使用',
                'date': now.isoformat()
            })
            tiers['HOT'].append(item)
            changes.append(f"{item['id'][:20]}... WARM→HOT ({item['access_count']}次使用)")
        
        elif days_inactive >= TIER_CONFIG['WARM']['decay_days']:
            # 降级到COLD
            tiers['WARM'].remove(item)
            item['promotion_history'].append({
                'from': 'WARM',
                'to': 'COLD',
                'reason': f'{days_inactive}天未访问',
                'date': now.isoformat()
            })
            tiers['COLD'].append(item)
            changes.append(f"{item['id'][:20]}... WARM→COLD ({days_inactive}天未用)")
    
    # 检查COLD层（归档）
    for item in list(tiers['COLD']):
        last_access = datetime.fromisoformat(item['last_access'])
        days_inactive = (now - last_access).days
        
        if days_inactive >= TIER_CONFIG['COLD']['decay_days']:
            # 归档
            tiers['COLD'].remove(item)
            item['promotion_history'].append({
                'from': 'COLD',
                'to': 'ARCHIVED',
                'reason': f'{days_inactive}天未访问',
                'date': now.isoformat()
            })
            tiers['ARCHIVED'].append(item)
            changes.append(f"{item['id'][:20]}... COLD→ARCHIVED ({days_inactive}天未用)")
    
    # HOT层超限处理（保留最近访问的）
    if len(tiers['HOT']) > TIER_CONFIG['HOT']['max_items']:
        excess = len(tiers['HOT']) - TIER_CONFIG['HOT']['max_items']
        # 按最后访问排序，移除最旧的
        sorted_hot = sorted(tiers['HOT'], key=lambda x: x['last_access'])
        for item in sorted_hot[:excess]:
            tiers['HOT'].remove(item)
            item['promotion_history'].append({
                'from': 'HOT',
                'to': 'WARM',
                'reason': 'HOT层超限',
                'date': now.isoformat()
            })
            tiers['WARM'].insert(0, item)
            changes.append(f"{item['id'][:20]}... HOT→WARM (层超限)")
    
    db['tiers'] = tiers
    save_db(db)
    
    return changes


def access_item(item_id):
    """访问记忆（更新计数和层级）"""
    db = load_db()
    tiers = get_tier_data()
    
    # 找到记忆所在层
    found = False
    for tier_name, items in tiers.items():
        for item in items:
            if item['id'] == item_id:
                item['access_count'] += 1
                item['last_access'] = datetime.now().isoformat()
                found = True
                
                # 检查是否触发晋升
                if tier_name == 'WARM' and item['access_count'] >= TIER_CONFIG['WARM']['access_threshold']:
                    # 晋升到HOT
                    tiers['WARM'].remove(item)
                    item['promotion_history'].append({
                        'from': 'WARM',
                        'to': 'HOT',
                        'reason': f'访问触发晋升（{item["access_count"]}次）',
                        'date': datetime.now().isoformat()
                    })
                    tiers['HOT'].append(item)
                    print(f"  ⬆️ 晋升: {item_id[:30]}... WARM→HOT")
                
                elif tier_name == 'COLD':
                    # 激活到WARM
                    tiers['COLD'].remove(item)
                    item['promotion_history'].append({
                        'from': 'COLD',
                        'to': 'WARM',
                        'reason': '强关联激活',
                        'date': datetime.now().isoformat()
                    })
                    tiers['WARM'].append(item)
                    print(f"  ⬆️ 激活: {item_id[:30]}... COLD→WARM")
                
                break
        if found:
            break
    
    if not found:
        # 新记忆，分配层级
        tier = assign_tier(item_id)
        print(f"  📌 分配: {item_id[:30]}... → {tier}")
    
    db['tiers'] = tiers
    save_db(db)


def show_status():
    """显示分层状态"""
    db = load_db()
    tiers = get_tier_data()
    
    print(f"\n{'='*60}")
    print(f"  🏗️ 分层记忆状态")
    print(f"{'='*60}")
    
    total = sum(len(items) for items in tiers.values())
    
    for tier_name, items in tiers.items():
        config = TIER_CONFIG[tier_name]
        pct = len(items) / max(total, 1) * 100
        bar = "█" * int(pct / 2)
        status = ""
        if len(items) > config['max_items']:
            status = " ⚠️超限"
        
        print(f"\n  {tier_name}: {len(items)}项 ({pct:.1f}%){status}")
        print(f"    {config['description']}")
        print(f"    限制: {config['max_items']} | 衰减: {config['decay_days']}天")
        print(f"    {bar}")
        
        # 显示最近访问的
        if items:
            recent = sorted(items, key=lambda x: x['last_access'], reverse=True)[:3]
            for item in recent:
                last = datetime.fromisoformat(item['last_access'])
                days = (datetime.now() - last).days
                print(f"      • {item['id'][:40]}... (访问{item['access_count']}次, {days}天前)")
    
    print(f"\n  总计: {total}条记忆")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='Tiered Memory Manager')
    parser.add_argument('--status', action='store_true', help='Show tier status')
    parser.add_argument('--rebalance', action='store_true', help='Run promotion/demotion')
    parser.add_argument('--access', help='Record access to an item')
    parser.add_argument('--archive', action='store_true', help='Compress archived memories')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    
    elif args.rebalance:
        print("[Tier] Running rebalance...")
        changes = rebalance_tiers()
        if changes:
            print(f"\n  变更记录:")
            for c in changes:
                print(f"    • {c}")
        else:
            print("  ✅ 无变更，层级稳定")
        show_status()
    
    elif args.access:
        access_item(args.access)
    
    elif args.archive:
        # 压缩归档记忆（简化实现）
        db = load_db()
        tiers = get_tier_data()
        archived_count = len(tiers['ARCHIVED'])
        print(f"[Tier] {archived_count} memories archived")
        print("  (压缩功能待实现)")
    
    else:
        show_status()


if __name__ == '__main__':
    main()
