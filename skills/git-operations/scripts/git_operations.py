#!/usr/bin/env python3
"""Git高级操作 - 智能提交、批量操作、分支管理"""
import argparse, subprocess, os, re
from datetime import datetime

def run(cmd, cwd=None):
    """运行git命令"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def smart_commit(message, cwd=None):
    """智能提交"""
    # 自动stage
    out, err, rc = run('git add -A', cwd)
    if rc != 0:
        print(f'[ERR] git add failed: {err}')
        return
    
    # 检查是否有改动
    out, _, _ = run('git diff --cached --name-only', cwd)
    if not out:
        print('[Info] No changes to commit')
        return
    
    # 生成规范message
    types = ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']
    if ':' not in message and not any(message.startswith(t) for t in types):
        # 尝试推断类型
        files = out.split('\n')
        if any(f.endswith('.md') for f in files):
            message = f'docs: {message}'
        elif any(f.endswith('.py') or f.endswith('.js') for f in files):
            message = f'feat: {message}'
        else:
            message = f'chore: {message}'
    
    out, err, rc = run(f'git commit -m "{message}"', cwd)
    if rc == 0:
        print(f'[OK] Committed: {message}')
        # 显示提交信息
        out, _, _ = run('git log -1 --oneline', cwd)
        print(f'  {out}')
    else:
        print(f'[ERR] {err}')

def safe_push(cwd=None):
    """安全推送（pull first）"""
    out, err, rc = run('git pull --rebase', cwd)
    if rc != 0:
        print(f'[ERR] Pull failed: {err}')
        return
    
    out, err, rc = run('git push', cwd)
    if rc == 0:
        print('[OK] Pushed successfully')
    else:
        print(f'[ERR] Push failed: {err}')

def undo_last(soft=True, cwd=None):
    """撤销上次提交"""
    flag = '--soft' if soft else '--hard'
    out, err, rc = run(f'git reset {flag} HEAD~1', cwd)
    if rc == 0:
        print(f'[OK] Undone last commit ({"soft" if soft else "hard"})')
        out, _, _ = run('git status --short', cwd)
        if out:
            print(f'  Changes:\n{out}')
    else:
        print(f'[ERR] {err}')

def cleanup_branches(cwd=None):
    """清理已合并分支"""
    run('git remote prune origin', cwd)
    out, err, rc = run('git branch --merged | grep -v "\\*" | grep -v main | grep -v master', cwd)
    if out:
        branches = [b.strip() for b in out.split('\n') if b.strip()]
        for b in branches:
            _, err, rc = run(f'git branch -d {b}', cwd)
            if rc == 0:
                print(f'[OK] Deleted: {b}')
            else:
                print(f'[WARN] {b}: {err}')
    else:
        print('[Info] No merged branches to clean')

def log_graph(cwd=None, since='1 week ago'):
    """可视化log"""
    cmd = f'git log --oneline --graph --decorate --all --since="{since}"'
    out, _, _ = run(cmd, cwd)
    print(out)

def main():
    parser = argparse.ArgumentParser(description='Git Operations')
    sub = parser.add_subparsers(dest='cmd')
    
    p = sub.add_parser('smart-commit')
    p.add_argument('message')
    p.add_argument('--dir', default='.')
    
    p = sub.add_parser('safe-push')
    p.add_argument('--dir', default='.')
    
    p = sub.add_parser('undo')
    p.add_argument('--hard', action='store_true')
    p.add_argument('--dir', default='.')
    
    p = sub.add_parser('cleanup')
    p.add_argument('--dir', default='.')
    
    p = sub.add_parser('log-graph')
    p.add_argument('--since', default='1 week ago')
    p.add_argument('--dir', default='.')
    
    args = parser.parse_args()
    
    if args.cmd == 'smart-commit':
        smart_commit(args.message, args.dir)
    elif args.cmd == 'safe-push':
        safe_push(args.dir)
    elif args.cmd == 'undo':
        undo_last(not args.hard, args.dir)
    elif args.cmd == 'cleanup':
        cleanup_branches(args.dir)
    elif args.cmd == 'log-graph':
        log_graph(args.dir, args.since)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
