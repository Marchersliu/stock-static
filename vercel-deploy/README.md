# Vercel 免费部署指南

## 目标
把股票监控面板部署到 Vercel（免费 CDN + HTTPS），手机随时随地访问，不用家里 Mac 一直开着。

## 费用
**0 元** — Vercel 个人免费版，每月 100GB 流量，完全够用。

## 前置条件（5分钟搞定）

### 1. 注册 Vercel 账号
- 打开 https://vercel.com
- 点击 **Sign Up** → 用 **GitHub** 账号登录（最方便）
- 验证邮箱

### 2. 安装 Vercel CLI（命令行工具）
```bash
# 需要 Node.js，Mac 自带，如果没有去 https://nodejs.org 下载
npm install -g vercel
```

### 3. 登录 Vercel CLI
```bash
vercel login
# 会弹浏览器让你授权，点 Continue 即可
```

### 4. 首次手动部署（建立项目关联）
```bash
cd /Users/hf/.kimi_openclaw/workspace/vercel-deploy
vercel --prod
```
- 第一次会问几个问题：
  - **Set up and deploy?** → 输入 `Y`
  - **Which scope?** → 选你的用户名（回车默认）
  - **Link to existing project?** → 输入 `N`（新建项目）
  - **What's your project name?** → 输入 `stock-dashboard`（或你喜欢的名字）
- 部署完成后会显示 URL，例如：`https://stock-dashboard-xxx.vercel.app`
- **把这个 URL 记下来，手机访问就是它**

### 5. 测试手机访问
- 手机浏览器打开 `https://stock-dashboard-xxx.vercel.app`
- 应该能看到跟 Mac 上一样的页面

## 自动定时更新（每30分钟）

首次部署后，以后每30分钟自动更新数据并重新部署：

```bash
# 后台启动自动部署守护进程
nohup python3 /Users/hf/.kimi_openclaw/workspace/deploy_to_vercel.py --daemon > /tmp/vercel_deploy.log 2>&1 &
```

或者设置 Mac 开机自启：
```bash
# 添加到 launchctl 定时任务
cat > ~/Library/LaunchAgents/com.hf.verceldeploy.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hf.verceldeploy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Library/Developer/CommandLineTools/usr/bin/python3</string>
        <string>/Users/hf/.kimi_openclaw/workspace/deploy_to_vercel.py</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/vercel_deploy.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/vercel_deploy.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.hf.verceldeploy.plist
```

## 查看日志
```bash
tail -f /tmp/vercel_deploy.log
```

## 故障排查

| 问题 | 解决 |
|------|------|
| `vercel: command not found` | `npm install -g vercel` |
| `not logged in` | `vercel login` |
| 部署后页面没变 | 等30秒 CDN 刷新，或地址加 `?v=1` |
| 手机打不开 | 确认 URL 是 `https://` 开头 |
| 想换项目名 | `vercel --prod` 重新部署，Vercel 后台改名字 |

## 文件结构
```
vercel-deploy/
├── index.html          # 股票监控面板（自动注入最新数据）
├── vercel.json         # Vercel 配置文件
└── .vercel/
    └── project.json    # 首次部署后自动生成，记录项目ID
```

## 提示
- Vercel 是**静态托管**，每次部署会全球 CDN 刷新（30秒内生效）
- 页面里的数据是注入时的快照，不是实时 websocket
- 每30分钟更新一次，对新闻/原料价格/恒指来说够用了
- 如果需要**实时盘中刷新**，还是得用阿里云 ECS（方案A）
