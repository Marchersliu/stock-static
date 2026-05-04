#!/bin/bash
# GitHub Push Helper - 避免shell特殊字符问题

if [ -z "$1" ]; then
    echo "Usage: bash push_github.sh '<YOUR_TOKEN>'"
    echo "注意：token用单引号包裹，防止特殊字符被shell解释"
    exit 1
fi

TOKEN="$1"
cd /Users/hf/.kimi_openclaw/workspace

echo "[1/3] 配置remote URL..."
git remote set-url origin "https://${TOKEN}@github.com/Marchersliu/stock-dashboard.git"

echo "[2/3] 推送中..."
git push origin main

echo "[3/3] 清除remote中的token（安全）..."
git remote set-url origin https://github.com/Marchersliu/stock-dashboard.git

echo "[OK] Push完成，token已从remote URL清除"
