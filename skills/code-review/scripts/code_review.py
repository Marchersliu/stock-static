#!/usr/bin/env python3
"""代码审查 - 检查bug、安全、性能、风格问题"""
import argparse, ast, re, os

def analyze_file(filepath):
    """分析Python文件"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [{'severity': 'ERR', 'line': 0, 'msg': f'Cannot read file: {e}'}]
    
    # 语法检查
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return [{'severity': 'ERR', 'line': e.lineno, 'msg': f'Syntax error: {e.msg}'}]
    
    # 安全检查
    security_patterns = [
        (r'eval\s*\(', 'Dangerous eval() usage'),
        (r'exec\s*\(', 'Dangerous exec() usage'),
        (r'subprocess\.call\s*\(.*shell\s*=\s*True', 'Shell=True is dangerous'),
        (r'os\.system\s*\(', 'os.system() is dangerous'),
        (r'input\s*\(.*\)', 'Unsanitized input()'),
        (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern, msg in security_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({'severity': '🔴', 'line': i, 'msg': f'Security: {msg}', 'code': line.strip()})
    
    # 常见bug模式
    bug_patterns = [
        (r'==\s*None', 'Use "is None" instead of "== None"'),
        (r'!=\s*None', 'Use "is not None" instead of "!= None"'),
        (r'except\s*:', 'Bare except clause - too broad'),
        (r'\.has_key\s*\(', 'Deprecated .has_key()'),
        (r'print\s+[^(]', 'Python 2 print statement'),
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern, msg in bug_patterns:
            if re.search(pattern, line):
                issues.append({'severity': '🟡', 'line': i, 'msg': f'Bug: {msg}', 'code': line.strip()})
    
    # AST分析
    for node in ast.walk(tree):
        # 超长函数
        if isinstance(node, ast.FunctionDef):
            func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
            if func_lines > 50:
                issues.append({'severity': '🟡', 'line': node.lineno, 'msg': f'Function "{node.name}" is {func_lines} lines (too long)', 'code': ''})
        
        # 未使用的变量（简单检查）
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            var_name = node.id
            if var_name.startswith('_'):
                continue
            # 简单检查：变量名是否在其他地方Load
            used = any(isinstance(n, ast.Name) and n.id == var_name and isinstance(n.ctx, ast.Load) for n in ast.walk(tree))
            if not used:
                issues.append({'severity': '⚪', 'line': node.lineno, 'msg': f'Unused variable: {var_name}', 'code': ''})
    
    return issues

def review_code(filepath):
    """审查代码并输出报告"""
    issues = analyze_file(filepath)
    
    print(f'\n{"="*60}')
    print(f'  Code Review: {filepath}')
    print(f'{"="*60}')
    
    if not issues:
        print('\n  ✅ No issues found')
        return
    
    severity_counts = {'🔴': 0, '🟡': 0, '⚪': 0}
    for issue in issues:
        severity_counts[issue['severity']] = severity_counts.get(issue['severity'], 0) + 1
    
    print(f'\n  Issues: 🔴 {severity_counts.get("🔴", 0)} | 🟡 {severity_counts.get("🟡", 0)} | ⚪ {severity_counts.get("⚪", 0)}')
    print()
    
    for issue in issues:
        print(f'  {issue["severity"]} L{issue["line"]}: {issue["msg"]}')
        if issue.get('code'):
            print(f'     {issue["code"][:80]}')
    
    return issues

def diff_review(file1, file2):
    """对比两个文件"""
    try:
        import difflib
        with open(file1, 'r') as f:
            lines1 = f.readlines()
        with open(file2, 'r') as f:
            lines2 = f.readlines()
        
        diff = list(difflib.unified_diff(lines1, lines2, fromfile=file1, tofile=file2))
        
        print(f'\n[Diff] {file1} → {file2}')
        print(f'  Added: {sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))}')
        print(f'  Removed: {sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))}')
        
        # 审查修改后的文件
        print()
        review_code(file2)
    except Exception as e:
        print(f'[ERR] Diff failed: {e}')

def main():
    parser = argparse.ArgumentParser(description='Code Review')
    parser.add_argument('--file', help='File to review')
    parser.add_argument('--diff', nargs=2, help='Diff two files')
    parser.add_argument('--dir', help='Review all Python files in directory')
    parser.add_argument('--output', help='Save report to file')
    
    args = parser.parse_args()
    
    all_issues = []
    
    if args.file:
        all_issues = review_code(args.file)
    elif args.diff:
        diff_review(args.diff[0], args.diff[1])
    elif args.dir:
        for root, dirs, files in os.walk(args.dir):
            for f in files:
                if f.endswith('.py'):
                    filepath = os.path.join(root, f)
                    issues = review_code(filepath)
                    all_issues.extend(issues)
    else:
        parser.print_help()
    
    if args.output and all_issues:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(all_issues, f, ensure_ascii=False, indent=2)
        print(f'\n[OK] Report saved: {args.output}')

if __name__ == '__main__':
    main()
