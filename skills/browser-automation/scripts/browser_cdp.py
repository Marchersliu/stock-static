#!/usr/bin/env python3
"""
浏览器自动化（CDP协议）- 通过Chrome DevTools Protocol控制浏览器

用法:
    # 启动Chrome CDP模式
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=9222 --headless

    # 截图
    python3 browser_cdp.py --screenshot "https://example.com" --output /tmp/page.png

    # 提取内容
    python3 browser_cdp.py --extract "https://example.com" --selector "h1"

    # 执行JS
    python3 browser_cdp.py --evaluate "document.title" --url "https://example.com"
"""
import argparse
import json
import requests
import base64
import time
from urllib.parse import urljoin


class BrowserCDP:
    """Chrome DevTools Protocol 客户端"""
    
    def __init__(self, host='localhost', port=9222):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws_url = None
        self.session = requests.Session()
    
    def get_version(self):
        """获取浏览器版本信息"""
        try:
            resp = self.session.get(f"{self.base_url}/json/version", timeout=5)
            return resp.json()
        except Exception as e:
            print(f"[ERR] Cannot connect to Chrome CDP: {e}")
            return None
    
    def get_pages(self):
        """获取所有页面"""
        try:
            resp = self.session.get(f"{self.base_url}/json/list", timeout=5)
            return resp.json()
        except:
            return []
    
    def new_page(self, url='about:blank'):
        """创建新页面"""
        try:
            resp = self.session.put(
                f"{self.base_url}/json/new?{url}",
                timeout=10
            )
            page_info = resp.json()
            self.ws_url = page_info.get('webSocketDebuggerUrl')
            return page_info
        except Exception as e:
            print(f"[ERR] Failed to create page: {e}")
            return None
    
    def close_page(self, page_id):
        """关闭页面"""
        try:
            self.session.get(f"{self.base_url}/json/close/{page_id}", timeout=5)
            return True
        except:
            return False
    
    def screenshot(self, url, output_path, width=1920, height=1080, full_page=False):
        """截图"""
        page = self.new_page(url)
        if not page:
            return False
        
        page_id = page['id']
        ws_url = page.get('webSocketDebuggerUrl')
        
        try:
            import websocket
            ws = websocket.create_connection(ws_url)
            
            # 设置视口
            ws.send(json.dumps({
                "id": 1,
                "method": "Emulation.setDeviceMetricsOverride",
                "params": {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": False
                }
            }))
            
            # 导航
            ws.send(json.dumps({
                "id": 2,
                "method": "Page.navigate",
                "params": {"url": url}
            }))
            
            # 等待加载
            time.sleep(3)
            
            # 截图
            ws.send(json.dumps({
                "id": 3,
                "method": "Page.captureScreenshot",
                "params": {"format": "png", "fullSize": full_page}
            }))
            
            # 接收响应
            result = None
            for _ in range(10):
                msg = json.loads(ws.recv())
                if msg.get('id') == 3 and 'result' in msg:
                    result = msg['result']
                    break
            
            ws.close()
            self.close_page(page_id)
            
            if result and 'data' in result:
                img_data = base64.b64decode(result['data'])
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                print(f"[OK] Screenshot saved: {output_path} ({len(img_data)} bytes)")
                return True
            
        except ImportError:
            print("[ERR] websocket-client not installed. Run: pip3 install websocket-client")
            return False
        except Exception as e:
            print(f"[ERR] Screenshot failed: {e}")
            return False
        
        return False
    
    def evaluate(self, url, expression):
        """在页面执行JS表达式"""
        page = self.new_page(url)
        if not page:
            return None
        
        page_id = page['id']
        ws_url = page.get('webSocketDebuggerUrl')
        
        try:
            import websocket
            ws = websocket.create_connection(ws_url)
            
            # 导航
            ws.send(json.dumps({
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": url}
            }))
            time.sleep(3)
            
            # 执行JS
            ws.send(json.dumps({
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expression,
                    "returnByValue": True
                }
            }))
            
            result = None
            for _ in range(10):
                msg = json.loads(ws.recv())
                if msg.get('id') == 2 and 'result' in msg:
                    result = msg['result']
                    break
            
            ws.close()
            self.close_page(page_id)
            
            if result and 'result' in result:
                value = result['result'].get('value')
                return value
            
        except ImportError:
            print("[ERR] websocket-client not installed")
            return None
        except Exception as e:
            print(f"[ERR] Evaluate failed: {e}")
            return None
        
        return None
    
    def extract_content(self, url, selector):
        """提取页面元素内容"""
        js = f"""
        (function() {{
            var elements = document.querySelectorAll('{selector}');
            var results = [];
            for (var i = 0; i < elements.length; i++) {{
                results.push({{
                    text: elements[i].innerText,
                    html: elements[i].innerHTML.substring(0, 200)
                }});
            }}
            return results;
        }})()
        """
        return self.evaluate(url, js)


def check_chrome_running():
    """检查Chrome CDP是否运行"""
    try:
        resp = requests.get('http://localhost:9222/json/version', timeout=2)
        return resp.status_code == 200
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description='Browser Automation (CDP)')
    parser.add_argument('--screenshot', help='URL to screenshot')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--extract', help='URL to extract content from')
    parser.add_argument('--selector', default='h1', help='CSS selector')
    parser.add_argument('--evaluate', help='JavaScript expression to evaluate')
    parser.add_argument('--url', help='Target URL')
    parser.add_argument('--port', type=int, default=9222, help='CDP port')
    
    args = parser.parse_args()
    
    # 检查Chrome
    if not check_chrome_running():
        print("[WARN] Chrome CDP not running on port 9222")
        print("  Start with:")
        print('  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome')
        print('    --remote-debugging-port=9222 --headless')
        return
    
    browser = BrowserCDP(port=args.port)
    
    # 显示版本
    version = browser.get_version()
    if version:
        print(f"[CDP] Chrome: {version.get('Browser', 'Unknown')}")
    
    if args.screenshot:
        url = args.screenshot
        output = args.output or '/tmp/screenshot.png'
        browser.screenshot(url, output)
    
    elif args.evaluate and args.url:
        result = browser.evaluate(args.url, args.evaluate)
        print(f"[Result] {result}")
    
    elif args.extract:
        url = args.extract
        selector = args.selector
        results = browser.extract_content(url, selector)
        print(f"[Extract] {len(results) if results else 0} elements")
        if results:
            for i, r in enumerate(results[:5], 1):
                print(f"  {i}. {r.get('text', '')[:100]}")
    
    else:
        # 列出页面
        pages = browser.get_pages()
        print(f"\n[Pages] {len(pages)} open:")
        for p in pages:
            print(f"  • {p.get('title', 'Untitled')[:50]} - {p.get('url', '')[:60]}")


if __name__ == '__main__':
    main()
