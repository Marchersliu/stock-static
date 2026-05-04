#!/usr/bin/env python3
"""Linter - 多语言代码检查封装"""
import argparse, subprocess, os, glob

def run_command(cmd, description):
    """运行命令并返回结果"""
    print(f'\n[{description}]')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def lint_python(path, fix=False):
    """Python lint"""
    ok = True
    
    # ruff
    fix_flag = '--fix' if fix else ''
    ok = run_command(f'ruff check {fix_flag} {path}', 'ruff check') and ok
    
    # black (format check)
    if fix:
        run_command(f'black {path}', 'black format')
    else:
        ok = run_command(f'black --check {path}', 'black check') and ok
    
    return ok

def lint_shell(path, fix=False):
    """Shell lint"""
    return run_command(f'shellcheck {path}', 'shellcheck')

def lint_markdown(path, fix=False):
    """Markdown lint"""
    # 简单检查：标题层级、空行
    issues = []
    for filepath in glob.glob(os.path.join(path, '**/*.md'), recursive=True):
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            if line.startswith('#') and not line.startswith('# '):
                issues.append(f'{filepath}:{i}: Header format issue')
            if line.rstrip() == '  ':
                issues.append(f'{filepath}:{i}: Trailing spaces')
    
    if issues:
        print('\n[markdownlint]')
        for issue in issues[:20]:
            print(f'  {issue}')
        return False
    print('\n[markdownlint] ✅ No issues')
    return True

def lint_json(path):
    """JSON validation"""
    import json
    issues = []
    for filepath in glob.glob(os.path.join(path, '**/*.json'), recursive=True):
        try:
            with open(filepath, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues.append(f'{filepath}: {e}')
    
    if issues:
        print('\n[JSON check]')
        for issue in issues:
            print(f'  {issue}')
        return False
    print('\n[JSON check] ✅ All valid')
    return True

def lint_all(path, fix=False):
    """检查所有语言"""
    results = {}
    
    # Python
    py_files = glob.glob(os.path.join(path, '**/*.py'), recursive=True)
    if py_files:
        results['python'] = lint_python(path, fix)
    
    # Shell
    sh_files = glob.glob(os.path.join(path, '**/*.sh'), recursive=True)
    if sh_files:
        results['shell'] = all(lint_shell(f) for f in sh_files)
    
    # Markdown
    md_files = glob.glob(os.path.join(path, '**/*.md'), recursive=True)
    if md_files:
        results['markdown'] = lint_markdown(path, fix)
    
    # JSON
    json_files = glob.glob(os.path.join(path, '**/*.json'), recursive=True)
    if json_files:
        results['json'] = lint_json(path)
    
    print(f'\n{"="*60}')
    print('  Lint Summary')
    print(f'{"="*60}')
    for lang, ok in results.items():
        status = '✅' if ok else '❌'
        print(f'  {status} {lang}')
    
    return all(results.values())

def main():
    parser = argparse.ArgumentParser(description='Linter')
    parser.add_argument('--lang', choices=['python', 'shell', 'markdown', 'json', 'all'], default='all')
    parser.add_argument('--dir', default='.', help='Directory to lint')
    parser.add_argument('--file', help='Single file to lint')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues')
    
    args = parser.parse_args()
    
    path = args.file or args.dir
    
    if args.lang == 'python' or (args.lang == 'all' and args.file and args.file.endswith('.py')):
        ok = lint_python(path, args.fix)
    elif args.lang == 'shell' or (args.lang == 'all' and args.file and args.file.endswith('.sh')):
        ok = lint_shell(path, args.fix)
    elif args.lang == 'all':
        ok = lint_all(path, args.fix)
    else:
        print(f'[ERR] Language {args.lang} not supported for {path}')
        ok = False
    
    exit(0 if ok else 1)

if __name__ == '__main__':
    main()
