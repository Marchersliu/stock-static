#!/usr/bin/env python3
"""
自我反思引擎 - 每次任务完成后自动评估输出质量

流程:
    1. 任务完成 → 自动触发反思
    2. 评估输出质量（5维度评分）
    3. 识别可改进点
    4. 写入反思记忆
    5. 更新用户偏好/规则

评估维度:
    - 准确性: 数据/事实是否正确
    - 简洁性: 是否废话过多
    - 完整性: 是否遗漏关键信息
    - 安全性: 是否有敏感信息泄露风险
    - 效率: token使用是否合理

用法:
    # 手动触发反思（传入任务描述和输出）
    python3 reflect.py --task "生成股票日报" --output "..." --score 8
    
    # 自动反思（扫描最新session日志）
    python3 reflect.py --auto --file memory/2026-05-04.md
    
    # 查看反思历史
    python3 reflect.py --history --top 10
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_manager import init_db, load_db, save_db, encode_episode

REFLECT_LOG = '/Users/hf/.kimi_openclaw/workspace/memory/reflections.json'

# 反思维度定义
DIMENSIONS = {
    'accuracy': {'name': '准确性', 'desc': '数据/事实/代码是否正确', 'weight': 0.25},
    'conciseness': {'name': '简洁性', 'desc': '是否废话过多/是否简洁直接', 'weight': 0.20},
    'completeness': {'name': '完整性', 'desc': '是否遗漏关键信息/步骤', 'weight': 0.20},
    'safety': {'name': '安全性', 'desc': '敏感信息/危险操作/安全违规', 'weight': 0.20},
    'efficiency': {'name': '效率', 'desc': 'token消耗/步骤冗余/工具使用', 'weight': 0.15},
}


def init_reflect_log():
    """初始化反思日志"""
    os.makedirs(os.path.dirname(REFLECT_LOG), exist_ok=True)
    if not os.path.exists(REFLECT_LOG):
        with open(REFLECT_LOG, 'w', encoding='utf-8') as f:
            json.dump({
                "version": "1.0",
                "reflections": [],
                "patterns": {},
                "improvements": []
            }, f, ensure_ascii=False, indent=2)
        return load_reflect_log()
    return load_reflect_log()


def load_reflect_log():
    """加载反思日志"""
    with open(REFLECT_LOG, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_reflect_log(data):
    """保存反思日志"""
    with open(REFLECT_LOG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def score_dimension(dimension, output_text, task_desc=""):
    """对单个维度评分（启发式规则）"""
    score = 7.0  # 默认7分
    issues = []
    
    if dimension == 'accuracy':
        # 检查常见错误信号
        error_signals = ['错误', 'err', 'fail', '不对', '错了', '修复', 'bug', '不对']
        for sig in error_signals:
            if sig in output_text.lower():
                score -= 1.5
                issues.append(f"包含错误信号词'{sig}'")
                break
        # 检查数据一致性
        if re.search(r'\d+\.\d+%?.*?\d+\.\d+%?', output_text):
            # 有多个数字，检查是否有矛盾
            pass  # 需要更复杂的逻辑
    
    elif dimension == 'conciseness':
        # 检查废话模式
        filler_patterns = [
            r'我很高兴|我很开心|我很乐意|我很荣幸',
            r'感谢您的提问|感谢您的耐心|感谢您的理解',
            r'当然|当然啦|当然的',
            r'让我来|让我为您|让我来帮您',
            r'希望对您有帮助|希望这个回答',
        ]
        filler_count = 0
        for pattern in filler_patterns:
            matches = re.findall(pattern, output_text)
            filler_count += len(matches)
        if filler_count >= 2:
            score -= 2.0
            issues.append(f"废话模式出现{filler_count}次")
        
        # 检查简洁偏好（用户已知偏好）
        if '简洁直接，不要废话' in open('/Users/hf/.kimi_openclaw/workspace/memory/preferences.json').read():
            if filler_count >= 1:
                score -= 1.5
                issues.append("违反用户'简洁直接'偏好")
    
    elif dimension == 'completeness':
        # 检查TODO/遗留问题
        todo_count = len(re.findall(r'TODO|遗留|待解决|待处理|未完成', output_text))
        if todo_count >= 3:
            score -= 2.0
            issues.append(f"遗留{todo_count}项未完成")
        
        # 检查是否回答了核心问题
        if task_desc and len(output_text) < 100:
            score -= 1.5
            issues.append("输出过短，可能不完整")
    
    elif dimension == 'safety':
        # 检查敏感信息泄露
        sensitive_patterns = [
            r'ghp_[a-zA-Z0-9]{36}',
            r'[a-f0-9]{40}',
            r'[A-Za-z0-9+/]{40,}={0,2}',  # base64-like
        ]
        for pattern in sensitive_patterns:
            if re.search(pattern, output_text):
                score -= 3.0
                issues.append("可能包含敏感信息/Token")
        
        # 检查危险操作
        dangerous_patterns = [
            r'rm -rf /',
            r'mkfs',
            r'chmod 777',
            r'docker prune.*-f',
            r'iptables -F',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, output_text):
                score -= 3.0
                issues.append("包含危险操作命令")
    
    elif dimension == 'efficiency':
        # 检查冗余步骤
        tool_count = len(re.findall(r'(?:exec|read|edit|write|browser)\s*\(', output_text))
        if tool_count >= 10:
            score -= 1.5
            issues.append(f"工具调用{tool_count}次，可能冗余")
        
        # 检查是否有更简单的方法
        if '可以通过一步' in output_text or '更简单的' in output_text:
            score -= 1.0
            issues.append("自我意识到有更简单方法但未用")
    
    score = max(1.0, min(10.0, score))
    return round(score, 1), issues


def reflect_task(task_desc, output_text, user_feedback=None):
    """对单个任务进行完整反思"""
    log = init_reflect_log()
    
    scores = {}
    all_issues = []
    
    for dim_key, dim_info in DIMENSIONS.items():
        score, issues = score_dimension(dim_key, output_text, task_desc)
        scores[dim_key] = score
        all_issues.extend(issues)
    
    # 综合评分
    total_score = sum(scores[d] * DIMENSIONS[d]['weight'] for d in DIMENSIONS)
    
    # 用户反馈修正
    if user_feedback:
        if user_feedback.lower() in ['好', '很好', '完美', 'ok', 'good']:
            total_score += 0.5
        elif user_feedback.lower() in ['不好', '差', '错了', '不对', 'no']:
            total_score -= 2.0
            all_issues.append(f"用户反馈负面: {user_feedback}")
    
    total_score = max(1.0, min(10.0, total_score))
    
    reflection = {
        "id": f"ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "task": task_desc[:200],
        "scores": scores,
        "total_score": round(total_score, 1),
        "issues": list(set(all_issues)),
        "feedback": user_feedback,
        "grade": score_to_grade(total_score)
    }
    
    log['reflections'].append(reflection)
    
    # 提取改进模式
    for issue in all_issues:
        if issue not in log['patterns']:
            log['patterns'][issue] = {'count': 0, 'last_seen': None, 'severity': 'medium'}
        log['patterns'][issue]['count'] += 1
        log['patterns'][issue]['last_seen'] = datetime.now().isoformat()
    
    save_reflect_log(log)
    
    # 同时写入认知记忆
    if total_score < 7 or all_issues:
        encode_episode(
            what=f"反思: {task_desc[:100]}",
            why=f"评分{total_score:.1f}，问题: {', '.join(all_issues[:3])}",
            how="已记录改进点",
            tags=["反思", reflection['grade']] + [k for k, v in scores.items() if v < 6],
            emotional_weight=min(0.9, (10 - total_score) / 10)
        )
    
    return reflection


def score_to_grade(score):
    """分数转等级"""
    if score >= 9: return "A+"
    if score >= 8: return "A"
    if score >= 7: return "B"
    if score >= 6: return "C"
    if score >= 5: return "D"
    return "F"


def reflect_from_log(filepath):
    """从session日志自动提取任务并反思"""
    if not os.path.exists(filepath):
        print(f"[ERR] File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取任务块（用 ### 分隔）
    task_blocks = re.findall(r'###\s*(.+?)\n(.*?)(?=###|\Z)', content, re.DOTALL)
    
    print(f"[Reflect] Found {len(task_blocks)} task blocks in {os.path.basename(filepath)}")
    
    reflections = []
    for task_title, task_content in task_blocks:
        # 只反思有明确结果的任务
        if len(task_content) > 200:
            ref = reflect_task(task_title, task_content)
            reflections.append(ref)
    
    return reflections


def show_history(top_n=10):
    """显示反思历史"""
    log = init_reflect_log()
    refs = log['reflections'][-top_n:]
    
    if not refs:
        print("[Reflect] No reflections yet")
        return
    
    print(f"\n{'='*70}")
    print(f"  📊 反思历史 (最近{len(refs)}条)")
    print(f"{'='*70}")
    
    for ref in refs:
        grade_color = {"A+": "🟢", "A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "🔴"}
        color = grade_color.get(ref['grade'], "⚪")
        
        print(f"\n{color} [{ref['grade']}] {ref['task'][:60]}")
        print(f"   总分: {ref['total_score']:.1f}/10 | 时间: {ref['timestamp'][:16]}")
        
        # 显示各维度
        dim_str = " | ".join([f"{DIMENSIONS[k]['name'][:2]}:{v:.1f}" for k, v in ref['scores'].items()])
        print(f"   {dim_str}")
        
        if ref['issues']:
            print(f"   ⚠️ {', '.join(ref['issues'][:3])}")
    
    # 统计
    avg_score = sum(r['total_score'] for r in log['reflections']) / len(log['reflections'])
    print(f"\n{'='*70}")
    print(f"  总计: {len(log['reflections'])}次反思 | 平均分: {avg_score:.1f}")
    
    # 高频问题
    patterns = log.get('patterns', {})
    if patterns:
        top_patterns = sorted(patterns.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        print(f"\n  🔁 高频问题:")
        for p, data in top_patterns:
            print(f"    • {p}: {data['count']}次")


def main():
    parser = argparse.ArgumentParser(description='Self-Reflection Engine')
    parser.add_argument('--task', help='Task description')
    parser.add_argument('--output', help='Task output text')
    parser.add_argument('--score', type=float, help='Self-assessed score (1-10)')
    parser.add_argument('--feedback', help='User feedback')
    parser.add_argument('--auto', action='store_true', help='Auto-reflect from latest log')
    parser.add_argument('--file', help='Specific log file to reflect on')
    parser.add_argument('--history', action='store_true', help='Show reflection history')
    parser.add_argument('--top', type=int, default=10, help='Show top N reflections')
    
    args = parser.parse_args()
    
    if args.task and args.output:
        ref = reflect_task(args.task, args.output, args.feedback)
        print(f"\n[Reflect] Task reflected: {ref['grade']} ({ref['total_score']:.1f}/10)")
        if ref['issues']:
            print(f"  Issues: {', '.join(ref['issues'][:3])}")
    
    elif args.auto or args.file:
        filepath = args.file
        if not filepath and args.auto:
            import glob
            files = sorted(glob.glob('/Users/hf/.kimi_openclaw/workspace/memory/2026-*.md'),
                          key=os.path.getmtime, reverse=True)
            if files:
                filepath = files[0]
        
        if filepath:
            reflect_from_log(filepath)
        else:
            print("[ERR] No log files found")
    
    elif args.history:
        show_history(args.top)
    
    else:
        # 默认显示历史
        show_history(5)


if __name__ == '__main__':
    main()
