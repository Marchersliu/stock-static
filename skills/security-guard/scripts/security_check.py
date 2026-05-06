#!/usr/bin/env python3
"""
Security Self-Check Script — 安全自查脚本
运行方式: python3 scripts/security_check.py
功能: 扫描仓库敏感文件、检测token泄露、验证.gitignore规则
"""

import os
import re
import subprocess
import sys

# ========== 配置 ==========
# 自动检测workspace目录（脚本在 skills/security-guard/scripts/ 下）
def find_workspace():
    current = os.path.dirname(os.path.abspath(__file__))
    # 向上两级: scripts/ -> security-guard/ -> skills/ -> workspace/
    workspace = os.path.dirname(os.path.dirname(os.path.dirname(current)))
    if os.path.exists(os.path.join(workspace, 'AGENTS.md')) or os.path.exists(os.path.join(workspace, '.git')):
        return workspace
    # fallback: 尝试再上一级
    workspace = os.path.dirname(workspace)
    if os.path.exists(os.path.join(workspace, 'AGENTS.md')) or os.path.exists(os.path.join(workspace, '.git')):
        return workspace
    return current  # 最终fallback

WORKSPACE = find_workspace()
SENSITIVE_PATTERNS = [
    # Kimi/OpenAI API key
    (r'sk-[a-zA-Z0-9]{20,}', "Kimi/OpenAI API key"),
    # Tushare token (40位hex) — 排除git commit hash上下文
    (r'(?<!commit\s)(?<!index\s)[a-f0-9]{40}(?!\s\(from)', "Tushare token (40位hex)"),
    # 企业微信 Secret (纯字母数字20位+)
    (r'[A-Z][a-zA-Z0-9]{15,}[0-9]{2,}', "可能的Secret"),
    # Bearer token
    (r'Bearer\s+[a-zA-Z0-9\-_]+', "Bearer token"),
    # API key各种变体
    (r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{10,}', "API key"),
    # Secret各种变体
    (r'secret\s*[:=]\s*["\']?[a-zA-Z0-9]{10,}', "Secret"),
    # 密码
    (r'password\s*[:=]\s*["\']?[a-zA-Z0-9]+', "Password"),
]

SENSITIVE_FILES = [
    'TOOLS.md',
    'stock_service.py',
    'price_alert_state.json',
    'price_alert_queue.json',
    'update_html_news.py',
    'auto_push_github.sh',
    'start_service.sh',
    '.env',
    '.env.local',
    '.env.production',
]

ALLOWED_REPO_FILES = [
    '.github',
    '.gitignore',
    'index.html',
    'README.md',
    'vercel.json',
    'skills/',
    'skills/security-guard/',
    'skills/security-guard/SKILL.md',
    'skills/security-guard/scripts/',
    'skills/security-guard/scripts/security_check.py',
    'skills/security-guard/references/',
    'skills/security-guard/references/token_patterns.md',
    # vercel-deploy/ 目录下的文件
]

# ========== 颜色 ==========
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_ok(msg): print(f"{GREEN}✅{RESET} {msg}")
def print_warn(msg): print(f"{YELLOW}⚠️{RESET} {msg}")
def print_err(msg): print(f"{RED}❌{RESET} {msg}")
def print_info(msg): print(f"{BOLD}ℹ️{RESET} {msg}")

def check_staged_files():
    """检查暂存区是否有敏感文件"""
    print_info("检查1: 暂存区文件列表...")
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True, text=True, cwd=WORKSPACE
    )
    staged = [f for f in result.stdout.strip().split('\n') if f]
    violations = [f for f in staged if f in SENSITIVE_FILES]
    
    if violations:
        print_err(f"暂存区含敏感文件: {', '.join(violations)}")
        print(f"   请执行: git rm --cached {' '.join(violations)}")
        return False
    
    if staged:
        print_ok(f"暂存区 {len(staged)} 个文件，无敏感文件")
    else:
        print_ok("暂存区为空")
    return True

def check_staged_content():
    """检查暂存区内容是否含token"""
    print_info("检查2: 暂存区内容token扫描...")
    result = subprocess.run(
        ['git', 'diff', '--cached'],
        capture_output=True, text=True, cwd=WORKSPACE
    )
    content = result.stdout
    
    if not content:
        print_ok("暂存区无内容变更")
        return True
    
    found = False
    for pattern, name in SENSITIVE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # 排除常见误报（如git hash）
            if len(match) < 20 and not match.startswith('sk-'):
                continue
            print_err(f"发现 {name}: {match[:30]}...")
            found = True
    
    if found:
        print_err("发现token残留！请移除后再提交")
        return False
    
    print_ok("暂存区无token残留")
    return True

def check_gitignore():
    """检查.gitignore是否屏蔽了敏感文件"""
    print_info("检查3: .gitignore规则完整性...")
    gitignore_path = os.path.join(WORKSPACE, '.gitignore')
    
    if not os.path.exists(gitignore_path):
        print_err(".gitignore 不存在！")
        return False
    
    with open(gitignore_path) as f:
        content = f.read()
    
    missing = [f for f in SENSITIVE_FILES if f not in content]
    
    if missing:
        print_warn(f".gitignore 缺少以下规则:")
        for f in missing:
            print(f"   - {f}")
        print(f"   请添加到 .gitignore")
        return False
    
    print_ok(".gitignore 规则完整")
    return True

def check_repo_files():
    """检查仓库当前文件是否合规"""
    print_info("检查4: 仓库文件合规性...")
    result = subprocess.run(
        ['git', 'ls-tree', '-r', 'HEAD', '--name-only'],
        capture_output=True, text=True, cwd=WORKSPACE
    )
    repo_files = [f for f in result.stdout.strip().split('\n') if f]
    
    # 过滤允许的文件
    violations = []
    for f in repo_files:
        allowed = False
        for allowed_pattern in ALLOWED_REPO_FILES:
            if f.startswith(allowed_pattern) or f == allowed_pattern:
                allowed = True
                break
        if not allowed:
            violations.append(f)
    
    if violations:
        print_err(f"仓库含多余文件: {', '.join(violations)}")
        print(f"   请执行: git rm --cached {' '.join(violations)}")
        return False
    
    print_ok(f"仓库文件合规 ({len(repo_files)} 个文件)")
    return True

def check_local_sensitive_files():
    """检查本地是否存在敏感文件（应在.gitignore中）"""
    print_info("检查5: 本地敏感文件隔离...")
    missing_files = []
    for f in SENSITIVE_FILES:
        filepath = os.path.join(WORKSPACE, f)
        if not os.path.exists(filepath):
            missing_files.append(f)
    
    if missing_files:
        print_warn(f"本地缺少敏感文件（可能已丢失）: {', '.join(missing_files)}")
    else:
        print_ok("本地敏感文件存在（.gitignore保护）")
    
    # 检查.env是否存在
    env_path = os.path.join(WORKSPACE, '.env')
    if os.path.exists(env_path):
        print_ok(".env 文件存在")
    else:
        print_warn(".env 文件不存在 — 请创建并写入token")
    
    return True  # 这个检查不阻断

def check_git_history():
    """检查Git历史是否仍含敏感文件"""
    print_info("检查6: Git历史敏感文件扫描...")
    
    for filename in SENSITIVE_FILES[:5]:  # 只检查最关键的5个
        result = subprocess.run(
            ['git', 'log', '--all', '--full-history', '--', filename],
            capture_output=True, text=True, cwd=WORKSPACE
        )
        if result.stdout.strip():
            print_err(f"Git历史仍含 {filename} — 需用 git-filter-repo 清除")
            return False
    
    print_ok("Git历史无敏感文件残留")
    return True

def check_token_in_history():
    """扫描git历史中的token残留"""
    print_info("检查7: Git历史token残留扫描...")
    
    # 检查最近10次提交的diff
    result = subprocess.run(
        ['git', 'log', '-p', '-10'],
        capture_output=True, text=True, cwd=WORKSPACE
    )
    history = result.stdout
    
    found = False
    for pattern, name in SENSITIVE_PATTERNS[:2]:  # 只检查最关键的
        matches = re.findall(pattern, history, re.IGNORECASE)
        for match in set(matches):
            if len(match) >= 20 or match.startswith('sk-'):
                print_warn(f"历史提交中发现 {name}: {match[:25]}...")
                found = True
    
    if found:
        print_warn("历史提交含token — 如已更换token则风险可控")
    else:
        print_ok("近期提交无token残留")
    
    return True  # 这个检查不阻断，仅提醒

def main():
    print(f"{BOLD}{'='*50}{RESET}")
    print(f"{BOLD}🛡️  安全自查报告{RESET}")
    print(f"{BOLD}{'='*50}{RESET}")
    print(f"工作目录: {WORKSPACE}")
    print()
    
    results = []
    results.append(("暂存区文件", check_staged_files()))
    results.append(("暂存区内容", check_staged_content()))
    results.append((".gitignore规则", check_gitignore()))
    results.append(("仓库文件合规", check_repo_files()))
    results.append(("本地文件隔离", check_local_sensitive_files()))
    results.append(("Git历史文件", check_git_history()))
    results.append(("Git历史token", check_token_in_history()))
    
    print()
    print(f"{BOLD}{'='*50}{RESET}")
    
    # 统计
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}{BOLD}🛡️  全部通过 ({passed}/{total}) — 可以安全提交{RESET}")
        return 0
    else:
        print(f"{RED}{BOLD}🚨 未通过 ({passed}/{total}) — 请修复后再提交{RESET}")
        for name, ok in results:
            if not ok:
                print(f"   {RED}✗{RESET} {name}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
