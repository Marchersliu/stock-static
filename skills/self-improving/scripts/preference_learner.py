#!/usr/bin/env python3
"""
偏好学习脚本 - 记住用户的纠正和偏好，让助手越用越聪明

用法:
    python3 preference_learner.py --scan memory/2026-05-04.md     # 扫描session日志提取偏好
    python3 preference_learner.py --list                           # 列出所有偏好
    python3 preference_learner.py --apply                          # 应用偏好到USER.md
    python3 preference_learner.py --health                       # 检查偏好健康度
    python3 preference_learner.py --learn "我喜欢简洁的输出"        # 手动添加偏好
    python3 preference_learner.py --correct "不要用sed" "用edit工具" # 手动添加纠正

自动触发关键词:
    纠正: 不对, 错了, 应该是, 不是, 改回
    偏好: 我喜欢, 我希望, prefer, 最好, 尽量
    禁止: 不要, 别, 禁止, never, 不准
    规则: 以后, always, 默认, 每次都要
    数值: 改成X, 太慢, 太快, 缩短, 延长
"""
import argparse
import json
import os
import re
from datetime import datetime, timedelta

PREF_FILE = '/Users/hf/.kimi_openclaw/workspace/memory/preferences.json'
MEMORY_DIR = '/Users/hf/.kimi_openclaw/workspace/memory'
USER_MD = '/Users/hf/.kimi_openclaw/workspace/USER.md'

# 触发关键词映射
TRIGGER_PATTERNS = {
    'correction': [
        r'不[对是]|错了|错[了啦]|应该是|应该是|要改成|不对[，,]|[不没]是\s*这个|[重请]新|改回|退回',
    ],
    'preference': [
        r'我喜欢|我希望|prefer|最好|尽量|我习惯|我通常|我倾向于|我爱|我想要',
    ],
    'ban': [
        r'不要|别\s|禁止|never|不准|不许|别用|不要[再又]|杜绝',
    ],
    'rule': [
        r'以后|always|默认|每次都要|每次都|任何情况下|一律|必须|应该[要]',
    ],
    'setting': [
        r'改成\s*(\d+)|缩短|延长|调[整快]|太慢|太快|[加减]少|[增减]加',
    ]
}


def load_preferences():
    """加载偏好数据库"""
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'corrections': [], 'preferences': [], 'banned_patterns': [], 'settings': []}


def save_preferences(data):
    """保存偏好数据库"""
    os.makedirs(os.path.dirname(PREF_FILE), exist_ok=True)
    with open(PREF_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Preferences saved to {PREF_FILE}")


def scan_file(filepath):
    """扫描日志文件提取偏好"""
    if not os.path.exists(filepath):
        print(f"[ERR] File not found: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    found = []
    date_str = os.path.basename(filepath).replace('.md', '')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('>'):
            continue
        
        # 检查每种触发类型
        for ptype, patterns in TRIGGER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # 提取上下文（前后2行）
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = '\n'.join(lines[context_start:context_end]).strip()
                    
                    # 提取偏好内容
                    pref = extract_preference(line, context, ptype)
                    if pref:
                        pref['date'] = date_str
                        pref['source_line'] = line[:200]
                        found.append(pref)
    
    # 去重
    seen = set()
    unique = []
    for f in found:
        key = f.get('key', '')
        if key and key not in seen:
            seen.add(key)
            unique.append(f)
    
    return unique


def extract_preference(line, context, ptype):
    """从单行文本中提取偏好内容"""
    line = line.strip()
    
    if ptype == 'correction':
        # "不对，应该是XXX" → 提取XXX
        m = re.search(r'应该是\s*["""]?(.*?)["""]?\s*[,，。]', line)
        if m:
            return {
                'type': 'correction',
                'key': f"correct:{m.group(1)[:50]}",
                'old_behavior': extract_old_behavior(context),
                'new_behavior': m.group(1).strip(),
                'confidence': 'medium',
                'context': context[:300]
            }
    
    elif ptype == 'preference':
        # "我喜欢简洁的" → 提取偏好
        m = re.search(r'我(?:喜欢|希望|习惯|倾向于|想要)\s*["""]?(.*?)["""]?[,，。]', line)
        if m:
            return {
                'type': 'preference',
                'key': f"pref:{m.group(1)[:50]}",
                'category': guess_category(context),
                'preference': m.group(1).strip(),
                'confidence': 'high',
                'context': context[:300]
            }
    
    elif ptype == 'ban':
        # "不要用sed" → 提取禁止模式
        m = re.search(r'(?:不要|别|禁止|不准)\s*(用|做|用|选|搞)?\s*["""]?(.*?)["""]?[,，。]', line)
        if m:
            banned = m.group(2).strip() if m.group(2) else m.group(0)
            return {
                'type': 'banned_pattern',
                'key': f"ban:{banned[:50]}",
                'pattern': banned,
                'reason': '用户禁止',
                'severity': 'high',
                'context': context[:300]
            }
    
    elif ptype == 'rule':
        # "以后都这样做" → 提取规则
        m = re.search(r'(?:以后|每次|默认|任何情况)\s*[,，]?\s*(.*?)[,，。]', line)
        if m:
            return {
                'type': 'rule',
                'key': f"rule:{m.group(1)[:50]}",
                'rule': m.group(1).strip(),
                'scope': 'global',
                'confidence': 'high',
                'context': context[:300]
            }
    
    elif ptype == 'setting':
        # "改成15分钟" → 提取数值
        m = re.search(r'改成\s*(\d+)\s*(分钟|小时|秒|天|次)', line)
        if m:
            return {
                'type': 'setting',
                'key': f"setting:{m.group(2)}:{m.group(1)}",
                'parameter': m.group(2),
                'value': int(m.group(1)),
                'unit': m.group(2),
                'confidence': 'high',
                'context': context[:300]
            }
    
    return None


def extract_old_behavior(context):
    """从上下文中提取旧行为"""
    # 简单启发：找"原来"、"之前"、"旧的"等词
    m = re.search(r'(?:原来|之前|旧[的版]|上[个次]版)[:：]\s*(.*?)[。\n]', context)
    if m:
        return m.group(1).strip()[:200]
    return "未知"


def guess_category(context):
    """根据上下文猜测偏好类别"""
    categories = {
        '沟通': ['简洁', '啰嗦', '废话', '直接', '详细', 'verbose', 'brief'],
        '股票': ['股票', '行情', '监控', '价格', '新闻', '持仓'],
        '文件': ['文件', '同步', 'iCloud', '备份', '路径'],
        '安全': ['token', '密码', '安全', '泄露', '隐藏'],
        '时间': ['时间', '频率', '间隔', '分钟', '小时', '每天'],
        '格式': ['格式', '表格', '列表', 'HTML', 'Markdown', 'PDF'],
    }
    context_lower = context.lower()
    for cat, keywords in categories.items():
        if any(kw in context_lower for kw in keywords):
            return cat
    return '其他'


def apply_to_user_md():
    """将高置信度偏好应用到 USER.md"""
    prefs = load_preferences()
    if not os.path.exists(USER_MD):
        print(f"[WARN] {USER_MD} not found, skipping")
        return
    
    with open(USER_MD, 'r', encoding='utf-8') as f:
        content = f.read()
    
    added = []
    
    # 添加偏好到 USER.md
    for p in prefs.get('preferences', []):
        if p.get('confidence') == 'high' and p.get('preference', '') not in content:
            # 在 Preferences 部分追加
            if '## Preferences' not in content and '## 偏好' not in content:
                content += "\n\n## Preferences\n"
            pref_line = f"- **{p['category']}**: {p['preference']}"
            if pref_line not in content:
                content += f"\n{pref_line}"
                added.append(pref_line)
    
    # 添加禁止事项
    for b in prefs.get('banned_patterns', []):
        if b.get('severity') == 'high' and b.get('pattern', '') not in content:
            if '## Red Lines' not in content and '## 红线' not in content:
                content += "\n\n## Red Lines\n"
            ban_line = f"- 禁止: {b['pattern']}"
            if ban_line not in content:
                content += f"\n{ban_line}"
                added.append(ban_line)
    
    if added:
        with open(USER_MD, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Applied {len(added)} preferences to USER.md")
    else:
        print("[INFO] No new high-confidence preferences to apply")


def health_check():
    """检查偏好数据库健康度"""
    prefs = load_preferences()
    issues = []
    
    today = datetime.now().date()
    
    # 检查过时偏好
    for p in prefs.get('preferences', []):
        pdate = datetime.strptime(p.get('date', today.isoformat()), '%Y-%m-%d').date()
        days_old = (today - pdate).days
        if days_old > 90 and p.get('confidence') == 'medium':
            issues.append(f"[OLD] Preference '{p['key'][:40]}' is {days_old} days old, consider downgrading")
    
    # 检查重复
    keys = [p.get('key', '') for p in prefs.get('preferences', [])]
    from collections import Counter
    dupes = {k: v for k, v in Counter(keys).items() if v > 1}
    for k, v in dupes.items():
        issues.append(f"[DUPE] Key '{k[:40]}' appears {v} times")
    
    # 检查冲突
    bans = [b.get('pattern', '') for b in prefs.get('banned_patterns', [])]
    for p in prefs.get('preferences', []):
        pref_text = p.get('preference', '')
        for ban in bans:
            if ban in pref_text:
                issues.append(f"[CONFLICT] Preference '{pref_text[:40]}' conflicts with ban '{ban[:40]}'")
    
    if issues:
        print("⚠️ 健康检查发现问题：")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ 偏好数据库健康")
    
    # 统计
    total = sum(len(prefs.get(k, [])) for k in ['corrections', 'preferences', 'banned_patterns', 'settings'])
    print(f"\n📊 统计: {total}条记录 (纠正{prefs['corrections'].__len__()}/偏好{prefs['preferences'].__len__()}/禁止{prefs['banned_patterns'].__len__()}/设置{prefs['settings'].__len__()})")


def list_preferences():
    """列出所有偏好"""
    prefs = load_preferences()
    print(f"\n{'='*60}")
    print(f"  偏好数据库 ({PREF_FILE})")
    print(f"{'='*60}")
    
    for ptype, label in [
        ('corrections', '纠正记录'),
        ('preferences', '用户偏好'),
        ('banned_patterns', '禁止事项'),
        ('settings', '参数设置')
    ]:
        items = prefs.get(ptype, [])
        if items:
            print(f"\n📌 {label} ({len(items)}条)")
            for i, item in enumerate(items[-5:], 1):
                print(f"  {i}. {item.get('key', 'N/A')[:60]}")
                if 'preference' in item:
                    print(f"     → {item['preference'][:80]}")
                if 'confidence' in item:
                    print(f"     [置信度: {item['confidence']}]")


def main():
    parser = argparse.ArgumentParser(description='Preference Learning System')
    parser.add_argument('--scan', help='Scan a memory file for preferences')
    parser.add_argument('--list', action='store_true', help='List all preferences')
    parser.add_argument('--apply', action='store_true', help='Apply high-confidence prefs to USER.md')
    parser.add_argument('--health', action='store_true', help='Check preference health')
    parser.add_argument('--learn', help='Manually add a preference')
    parser.add_argument('--correct', nargs=2, metavar=('OLD', 'NEW'), help='Manually add a correction')
    
    args = parser.parse_args()
    
    if args.scan:
        print(f"[Scan] Reading {args.scan}...")
        found = scan_file(args.scan)
        if found:
            prefs = load_preferences()
            # 合并新发现的偏好
            for f in found:
                ptype_map = {
                    'correction': 'corrections',
                    'preference': 'preferences',
                    'banned_pattern': 'banned_patterns',
                    'rule': 'preferences',
                    'setting': 'settings'
                }
                target = ptype_map.get(f['type'])
                if target and f not in prefs[target]:
                    prefs[target].append(f)
            save_preferences(prefs)
            print(f"[OK] Found and recorded {len(found)} new preferences")
        else:
            print("[INFO] No preferences found in this file")
    
    elif args.learn:
        prefs = load_preferences()
        prefs['preferences'].append({
            'type': 'preference',
            'key': f"pref:{args.learn[:50]}",
            'date': datetime.now().strftime('%Y-%m-%d'),
            'category': guess_category(args.learn),
            'preference': args.learn,
            'confidence': 'high',
            'source': 'manual'
        })
        save_preferences(prefs)
        print(f"[OK] Recorded preference: {args.learn}")
    
    elif args.correct:
        old, new = args.correct
        prefs = load_preferences()
        prefs['corrections'].append({
            'type': 'correction',
            'key': f"correct:{new[:50]}",
            'date': datetime.now().strftime('%Y-%m-%d'),
            'old_behavior': old,
            'new_behavior': new,
            'confidence': 'high',
            'source': 'manual'
        })
        save_preferences(prefs)
        print(f"[OK] Recorded correction: {old} → {new}")
    
    elif args.apply:
        apply_to_user_md()
    
    elif args.health:
        health_check()
    
    elif args.list:
        list_preferences()
    
    else:
        # 默认行为：扫描最新日志
        import glob
        files = sorted(glob.glob(f"{MEMORY_DIR}/2026-*.md"), key=os.path.getmtime, reverse=True)
        if files:
            print(f"[Auto] Scanning latest: {files[0]}...")
            found = scan_file(files[0])
            if found:
                prefs = load_preferences()
                for f in found:
                    ptype_map = {'correction': 'corrections', 'preference': 'preferences', 
                                'banned_pattern': 'banned_patterns', 'setting': 'settings'}
                    target = ptype_map.get(f['type'])
                    if target:
                        # 检查是否已存在
                        exists = any(p.get('key') == f['key'] for p in prefs[target])
                        if not exists:
                            prefs[target].append(f)
                save_preferences(prefs)
                print(f"[OK] Auto-scanned {len(found)} preferences from {os.path.basename(files[0])}")
            else:
                print("[INFO] No new preferences in latest log")
        else:
            print("[ERR] No memory files found")


if __name__ == '__main__':
    main()
