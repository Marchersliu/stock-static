---
name: security-guard
description: 安全守护技能 - Token/密钥防泄露、GitHub仓库安全检查、敏感文件隔离、数据外泄防护。每次涉及Git提交、API调用、文件上传时自动触发安全检查。包含：token泄露检测、仓库敏感文件扫描、.gitignore规则验证、启动脚本安全封装、环境变量隔离。
---

# Security Guard 安全守护技能

## 安全铁律（最高优先级）

1. **Token/密钥绝不写入可提交文件** — 只存 `.env` 或环境变量
2. **敏感文件绝不 push 到 GitHub** — 用 `.gitignore` 永久屏蔽
3. **提交前强制安全检查** — 运行自查脚本确认无敏感内容
4. **最小权限原则** — 仓库只保留必要文件（index.html + workflow）
5. **历史泄露立即清除** — 用 git-filter-repo 从所有提交中删除敏感文件

## 模块概览

| 模块 | 功能 | 触发时机 |
|------|------|---------|
| Token泄露检测 | 扫描文本中的API key、token、secret | 每次编辑/生成文件后 |
| 仓库安全扫描 | 检查GitHub仓库是否含敏感文件 | 每次push前 |
| .gitignore验证 | 确认敏感文件在屏蔽列表中 | 每次修改.gitignore后 |
| 启动脚本封装 | 将token封装在本地脚本，不暴露 | 创建/修改启动脚本时 |
| 历史清除 | git-filter-repo删除敏感文件历史 | 发现泄露后 |

## 安全检查清单

### 提交前必查（Pre-commit Checklist）

```bash
# 1. 检查暂存区是否有敏感文件
git diff --cached --name-only | grep -E "TOOLS|stock_service|price_alert|update_|auto_push|start_service|\.env" && echo "❌ 敏感文件在暂存区！" || echo "✅ 无敏感文件"

# 2. 检查暂存区内容是否含token
git diff --cached | grep -E "sk-[a-zA-Z0-9]{20,}|e53f440|6e00a3|44a9OW|km_b_prod" && echo "❌ 发现token残留！" || echo "✅ 无token残留"

# 3. 检查.gitignore是否有效
cat .gitignore | grep -E "TOOLS|stock_service|price_alert|update_|auto_push|start_service|\.env" | wc -l
# 结果应为 >= 8

# 4. 验证仓库文件列表（应只有index.html + workflow）
git ls-tree -r HEAD --name-only | grep -vE "index\.html|\.github|\.gitignore" && echo "❌ 有多余文件！" || echo "✅ 干净"
```

### 敏感文件清单

| 文件名 | 泄露风险 | 屏蔽方式 |
|--------|---------|---------|
| `TOOLS.md` | 🔴 极高 — 含Tushare/Kimi/企业微信token | `.gitignore` |
| `stock_service.py` | 🔴 极高 — 含业务逻辑、token、股票列表 | `.gitignore` |
| `price_alert_state.json` | 🟡 中 — 提醒状态、价格阈值 | `.gitignore` |
| `price_alert_queue.json` | 🟡 中 — 待发送队列 | `.gitignore` |
| `update_html_news.py` | 🟡 中 — 新闻更新脚本 | `.gitignore` |
| `auto_push_github.sh` | 🟡 中 — 自动化脚本 | `.gitignore` |
| `start_service.sh` | 🟡 中 — 启动脚本（含token加载） | `.gitignore` |
| `.env` | 🔴 极高 — 环境变量文件 | `.gitignore` |
| `*.pyc` | 🟢 低 — Python缓存 | `.gitignore` |
| `__pycache__/` | 🟢 低 — Python缓存目录 | `.gitignore` |

### Token特征识别

```bash
# 高风险模式（grep正则）
"sk-[a-zA-Z0-9]{30,}"        # Kimi/OpenAI API key
"[a-f0-9]{40}"                # Tushare token (hex40)
"[A-Za-z0-9]{20,}"            # 企业微信 Secret
"Bearer\s+[a-zA-Z0-9\-_]+"   # Bearer token
"api[_-]?key\s*[:=]\s*"      # 各种API key
"password\s*[:=]\s*"         # 密码
"secret\s*[:=]\s*"            # Secret
```

## 安全操作流程

### 1. 创建/修改文件时的安全检查

```
每次 write/edit 操作后 → 自动运行 scan_content()
  ↓
检查内容是否含 token 模式
  ↓
是 → 阻断操作，提示移入 .env
否 → 允许继续
```

### 2. Git 提交前的安全检查

```
git add 之后 → 自动运行 pre_commit_check()
  ↓
检查暂存区文件列表
  ↓
发现敏感文件 → 阻断，提示 git rm --cached
  ↓
检查暂存区内容是否含 token
  ↓
发现 token → 阻断，提示清理
  ↓
全部通过 → 允许 git commit
```

### 3. 仓库定期安全扫描

```bash
# 每周运行一次
security_audit()
  ↓
1. 拉取GitHub仓库文件列表
2. 与敏感文件清单比对
3. 检查 .gitignore 规则是否完整
4. 检查本地 .env 是否存在
5. 输出安全报告
```

## 环境变量隔离方案

### 推荐架构

```
workspace/
├── .env                        ← 敏感配置（.gitignore保护）
│   ├── TUSHARE_TOKEN=xxx
│   ├── KIMI_API_KEY=xxx
│   └── 其他密钥...
├── start_service.sh            ← 加载.env并启动（.gitignore保护）
├── .gitignore                  ← 屏蔽规则（提交）
├── stock_dashboard.html         ← 看板前端（提交到vercel-deploy/）
├── vercel-deploy/
│   ├── index.html              ← GitHub Pages部署文件（提交）
│   └── .github/workflows/
│       └── pages.yml           ← Actions配置（提交）
└── [其他本地脚本...]           ← .gitignore保护
```

### .env 文件模板

```bash
# Tushare Pro Token
TUSHARE_TOKEN=6e00a3a46d148610fba8c49fdd6c44e8c3455a4d898f4f06b16de929

# Kimi/OpenAI API Key
KIMI_API_KEY=sk-9WNjMdFQtiDxuvDBQEYam3G5YFXSnu6PGezrJTbo1W6PPDp6

# 其他密钥...
# WECHAT_SECRET=xxx
```

### start_service.sh 模板

```bash
#!/bin/bash
set -a
source /Users/hf/.kimi_openclaw/workspace/.env
set +a
cd /Users/hf/.kimi_openclaw/workspace
nohup python3 stock_service.py > logs/stock_service.log 2>&1 &
echo "服务已启动，PID: $!"
```

## 历史泄露清除

### 发现泄露后的紧急处理

```bash
# 1. 更换所有泄露的token（立即）
#    - Tushare官网重新生成
#    - Kimi控制台重新生成
#    - 企业微信后台重置

# 2. 从GitHub仓库删除文件（当前提交）
git rm --cached TOOLS.md stock_service.py ...
git commit -m "security: remove sensitive files"
git push

# 3. 从历史中彻底删除（所有旧提交）
git-filter-repo --path TOOLS.md --invert-paths --force
git-filter-repo --path stock_service.py --invert-paths --force
# ... 对每个敏感文件重复

# 4. 强制推送（覆盖所有历史）
git remote add origin git@github.com:.../....git
git push --force

# 5. 验证
#    - 检查GitHub仓库文件列表
#    - 检查旧提交是否还能访问
#    - 确认 .gitignore 生效
```

## 安全自查脚本

创建 `scripts/security_check.py`：

```python
#!/usr/bin/env python3
"""安全自查脚本 — 每次提交前运行"""
import os, re, subprocess, sys

SENSITIVE_PATTERNS = [
    r'sk-[a-zA-Z0-9]{30,}',           # Kimi/OpenAI key
    r'[a-f0-9]{40}',                   # Tushare token
    r'Bearer\s+[a-zA-Z0-9\-_]+',       # Bearer token
    r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{10,}',
    r'secret\s*[:=]\s*["\']?[a-zA-Z0-9]{10,}',
    r'password\s*[:=]\s*["\']?[a-zA-Z0-9]+',
]

SENSITIVE_FILES = [
    'TOOLS.md', 'stock_service.py', 'price_alert_state.json',
    'price_alert_queue.json', 'update_html_news.py',
    'auto_push_github.sh', 'start_service.sh', '.env'
]

def check_staged_files():
    """检查暂存区是否有敏感文件"""
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                          capture_output=True, text=True)
    staged = result.stdout.strip().split('\n')
    violations = [f for f in staged if f in SENSITIVE_FILES]
    if violations:
        print(f"❌ 暂存区含敏感文件: {', '.join(violations)}")
        return False
    print("✅ 暂存区无敏感文件")
    return True

def check_staged_content():
    """检查暂存区内容是否含token"""
    result = subprocess.run(['git', 'diff', '--cached'],
                          capture_output=True, text=True)
    content = result.stdout
    for pattern in SENSITIVE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"❌ 发现token残留: {matches[0][:20]}...")
            return False
    print("✅ 暂存区无token残留")
    return True

def check_gitignore():
    """检查.gitignore是否屏蔽了敏感文件"""
    if not os.path.exists('.gitignore'):
        print("❌ .gitignore 不存在！")
        return False
    with open('.gitignore') as f:
        content = f.read()
    missing = [f for f in SENSITIVE_FILES if f not in content]
    if missing:
        print(f"⚠️ .gitignore 缺少: {', '.join(missing)}")
    else:
        print("✅ .gitignore 规则完整")
    return len(missing) == 0

def main():
    print("=== 安全自查 ===")
    ok1 = check_staged_files()
    ok2 = check_staged_content()
    ok3 = check_gitignore()
    if ok1 and ok2 and ok3:
        print("\n🛡️ 全部通过，可以安全提交")
        return 0
    else:
        print("\n🚨 安全检查未通过，请修复后再提交")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `git-filter-repo not found` | 未安装工具 | `pip install git-filter-repo` |
| `remote origin removed` | git-filter-repo默认删除remote | `git remote add origin ...` |
| `push rejected non-fast-forward` | 强制推送被阻止 | `git push --force` |
| `.gitignore不生效` | 文件已跟踪 | `git rm --cached <file>` |
| `env文件不存在` | 未创建.env | 创建并写入token |

## 安全最佳实践

1. **Never commit credentials** — 即使仓库是私有的
2. **Rotate tokens regularly** — 每3个月更换一次
3. **Use environment variables** — 生产环境绝不硬编码
4. **Audit dependencies** — 定期检查第三方包是否安全
5. **Least privilege** — GitHub仓库只保留最小必要文件
6. **Monitor for leaks** — 定期检查GitHub仓库文件列表
7. **Separate concerns** — 敏感配置、业务逻辑、前端文件分离

## 文件清单

```
security-guard/
├── SKILL.md                      # 本文件
├── scripts/
│   └── security_check.py         # 安全自查脚本
└── references/
    └── token_patterns.md          # Token识别模式文档
```
