#!/usr/bin/env bash
# dashboard_auto_sync.sh — 自动抓取股票数据并同步GitHub
# 定时：每天 10:00 / 15:30 / 19:30
# crontab: 0 10,15,19 * * * ~/.kimi_openclaw/workspace/scripts/dashboard_auto_sync.sh

set -e

WORKSPACE="/Users/hf/.kimi_openclaw/workspace"
LOGFILE="$WORKSPACE/logs/dashboard_sync.log"
PIDFILE="$WORKSPACE/stock_service.pid"

mkdir -p "$WORKSPACE/logs"

echo "========================================" >> "$LOGFILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始自动同步" >> "$LOGFILE"

# 1. 确保 stock_service.py 在运行
cd "$WORKSPACE"
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] stock_service 未运行，重新启动..." >> "$LOGFILE"
        nohup python3 "$WORKSPACE/stock_service.py" > "$WORKSPACE/logs/stock_service.log" 2>&1 &
        echo $! > "$PIDFILE"
        sleep 3
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] stock_service 未运行，启动..." >> "$LOGFILE"
    nohup python3 "$WORKSPACE/stock_service.py" > "$WORKSPACE/logs/stock_service.log" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 3
fi

# 2. 触发数据抓取（调用API触发后台刷新）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 触发数据抓取..." >> "$LOGFILE"
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8888/api/data?t=$(date +%s)" >> "$LOGFILE" 2>&1 || true
echo "" >> "$LOGFILE"

# 等待数据抓取完成
sleep 5

# 3. 触发新闻抓取
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8888/api/premarket?t=$(date +%s)" >> "$LOGFILE" 2>&1 || true
echo "" >> "$LOGFILE"

sleep 3

# 4. 生成静态页面（服务端渲染，用于 GitHub Pages）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 生成静态页面..." >> "$LOGFILE"
python3 "$WORKSPACE/scripts/generate_static.py" >> "$LOGFILE" 2>&1 || echo "[$(date '+%Y-%m-%d %H:%M:%S')] 静态生成失败" >> "$LOGFILE"

sleep 1

# 5. GitHub 同步
cd "$WORKSPACE"

# 检查是否有变更（排除日志文件）
if git status --short -- ':!logs/*' ':!*.log' | grep -q .; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 检测到变更，提交同步..." >> "$LOGFILE"
    git add -A -- ':!logs/*' ':!*.log'
    git commit -m "auto-sync: $(date '+%Y-%m-%d %H:%M:%S') 数据更新" >> "$LOGFILE" 2>&1 || true
    git push origin main >> "$LOGFILE" 2>&1 || echo "[$(date '+%Y-%m-%d %H:%M:%S')] 推送失败，可能无网络或无变更" >> "$LOGFILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 无变更需要同步" >> "$LOGFILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 同步完成" >> "$LOGFILE"
