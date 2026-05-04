---
name: browser-automation
description: 浏览器自动化技能（CDP协议）。通过Chrome DevTools Protocol控制浏览器，实现无头浏览、页面操作、元素提取、性能监控。当用户需要：(1) 自动化网页操作，(2) 批量抓取动态内容，(3) 模拟用户行为，(4) 监控网页变化时使用。
---

# Browser-Automation 浏览器自动化

## 核心功能

| 功能 | CDP方法 | 说明 |
|------|---------|------|
| **无头浏览** | `Target.createTarget` | 创建无头页面 |
| **导航** | `Page.navigate` | 跳转到URL |
| **截图** | `Page.captureScreenshot` | 页面截图 |
| **元素提取** | `Runtime.evaluate` + `DOM.querySelector` | CSS选择器提取 |
| **点击/输入** | `Input.dispatchMouseEvent` / `Input.dispatchKeyEvent` | 模拟交互 |
| **性能监控** | `Performance.getMetrics` | 页面性能数据 |
| **网络监控** | `Network.enable` | 监听网络请求 |

## 连接方式

```python
from browser_cdp import BrowserCDP

# 连接本地Chrome
browser = BrowserCDP(port=9222)

# 打开页面
page = browser.new_page("https://example.com")

# 截图
page.screenshot("/tmp/page.png")

# 提取元素
text = page.query_selector("h1")

# 点击
page.click("button#submit")

# 输入
page.type("input#search", "关键词")

# 关闭
browser.close()
```

## 用法

```bash
# 启动Chrome（CDP模式）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 --headless

# 截图
python3 browser_cdp.py --screenshot "https://example.com" --output /tmp/page.png

# 提取内容
python3 browser_cdp.py --extract "https://example.com" --selector "article"

# 自动化操作
python3 browser_cdp.py --script automation_script.py
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/browser-automation/scripts
python3 browser_cdp.py --help
```
