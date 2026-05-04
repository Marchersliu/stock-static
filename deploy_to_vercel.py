#!/usr/bin/env python3
"""
Vercel 自动部署脚本：每30分钟注入最新数据 → 部署到 Vercel

前置条件（只需执行一次）：
    1. 去 https://vercel.com 注册账号（建议用 GitHub 登录）
    2. 安装 Vercel CLI: npm i -g vercel
    3. 登录: vercel login
    4. 首次部署（手动引导）: cd vercel-deploy && vercel --prod
       这一步会生成 .vercel/project.json，以后自动部署就用它

使用方法:
    # 单次执行（注入数据 + 部署）
    python3 /Users/hf/.kimi_openclaw/workspace/deploy_to_vercel.py

    # 后台定时执行（每30分钟）
    nohup python3 /Users/hf/.kimi_openclaw/workspace/deploy_to_vercel.py --daemon > /tmp/vercel_deploy.log 2>&1 &

手机访问地址: https://你的项目名.vercel.app
"""
import os
import sys
import time
import subprocess

# 路径
WORKSPACE = '/Users/hf/.kimi_openclaw/workspace'
DEPLOY_DIR = os.path.join(WORKSPACE, 'vercel-deploy')
HTML_PATH = os.path.join(WORKSPACE, 'stock_dashboard.html')
INJECT_SCRIPT = os.path.join(WORKSPACE, 'inject_live_data.py')


def run_inject():
    """运行数据注入脚本"""
    print('[Deploy] Running inject_live_data.py...')
    result = subprocess.run(
        [sys.executable, INJECT_SCRIPT],
        capture_output=True, text=True, timeout=60, cwd=WORKSPACE
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f'[WARN] inject failed: {result.stderr[:200]}')
        return False
    return True


def copy_to_deploy():
    """复制最新 HTML 到部署目录"""
    import shutil
    if not os.path.exists(HTML_PATH):
        print(f'[ERR] HTML not found: {HTML_PATH}')
        return False
    shutil.copy2(HTML_PATH, os.path.join(DEPLOY_DIR, 'index.html'))
    print(f'[OK] Copied to {DEPLOY_DIR}/index.html')
    return True


def deploy_to_github():
    """推送到 GitHub，Vercel 自动部署"""
    print('[Deploy] Pushing to GitHub...')
    # 先配置 git 用户信息（如果还没配）
    subprocess.run(['git', 'config', 'user.email', 'deploy@openclaw.ai'], cwd=DEPLOY_DIR, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Deploy Bot'], cwd=DEPLOY_DIR, capture_output=True)
    
    # add + commit
    subprocess.run(['git', 'add', '.'], cwd=DEPLOY_DIR, capture_output=True)
    result = subprocess.run(
        ['git', 'commit', '-m', f'Auto update {time.strftime("%Y-%m-%d %H:%M")}'],
        cwd=DEPLOY_DIR, capture_output=True, text=True
    )
    # 如果没有变更，commit 会失败，这不算是错误
    
    # push
    result = subprocess.run(
        ['git', 'push', 'origin', 'main'],
        capture_output=True, text=True, timeout=60, cwd=DEPLOY_DIR
    )
    print(result.stdout)
    if result.returncode != 0:
        err = result.stderr
        if 'fatal: Authentication failed' in err or '403' in err:
            print('[ERR] GitHub 认证失败，需要配置 Personal Access Token')
            print('      请去 https://github.com/settings/tokens 生成一个 token')
            print('      然后运行: git remote set-url origin https://TOKEN@github.com/Marchersliu/stock-dashboard.git')
        else:
            print(f'[ERR] push failed: {err[:200]}')
        return False
    print('[OK] Pushed to GitHub, Vercel will auto-deploy in ~30s')
    return True


def deploy_once():
    print(f'\n=== {time.strftime("%Y-%m-%d %H:%M:%S")} ===')

    # 1. 注入最新数据
    if not run_inject():
        # 注入失败也用现有 HTML 继续部署
        pass

    # 2. 复制到部署目录
    if not copy_to_deploy():
        return False

    # 3. 推送到 GitHub（Vercel 自动部署）
    return deploy_to_github()


def run_daemon():
    print('[Daemon] Vercel deploy started, interval=30min')
    while True:
        try:
            deploy_once()
        except Exception as e:
            print(f'[ERR] deploy_once: {e}')
        print('[Daemon] Sleeping 15min...\n')
        time.sleep(900)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        run_daemon()
    else:
        success = deploy_once()
        sys.exit(0 if success else 1)
