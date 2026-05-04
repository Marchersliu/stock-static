#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格提醒iMessage发送器
- 读取 price_alert_queue.json
- 通过 AppleScript 发送 iMessage
- 标记已发送的提醒

配置：在 ~/.kimi_openclaw/workspace/.imessage_config.json 中设置收件人
{
    "recipient": "+86xxxxxxxxxxx"
}
"""

import json
import os
import subprocess
import sys

WORKSPACE = "/Users/hf/.kimi_openclaw/workspace"
QUEUE_FILE = os.path.join(WORKSPACE, "price_alert_queue.json")
STATE_FILE = os.path.join(WORKSPACE, "price_alert_state.json")
CONFIG_FILE = os.path.join(WORKSPACE, ".imessage_config.json")

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def load_queue():
    try:
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False)

def send_imessage(recipient, message):
    """通过 AppleScript 发送 iMessage"""
    script = f'''
tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy "{recipient}" of targetService
    send "{message}" to targetBuddy
end tell
'''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[ERR] iMessage发送失败: {e}")
        return False

def send_alert(alert, recipient):
    """发送单条提醒"""
    code = alert['code']
    name = alert['name']
    price = alert['price']
    label = alert['label']
    msg = alert['msg']
    key = alert['key']
    
    # 构建完整消息
    full_msg = f"""{msg}

📊 九州一轨 {code}
💰 当前价: {price:.2f}元
⏰ 时间: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}

—— 股票实时监控"""
    
    print(f"[SEND] 发送提醒: {name} {label} ({price})")
    success = send_imessage(recipient, full_msg)
    
    if success:
        # 标记为已发送
        state = load_state()
        state[key] = True
        save_state(state)
        print(f"[OK] 提醒已发送并标记: {key}")
        return True
    else:
        print(f"[ERR] 提醒发送失败: {key}")
        return False

def main():
    config = load_config()
    recipient = config.get('recipient', '').strip()
    
    if not recipient:
        print("[ERR] 未配置iMessage收件人。请在 .imessage_config.json 中设置:")
        print('  {"recipient": "+86xxxxxxxxxxx"}')
        sys.exit(1)
    
    queue = load_queue()
    if not queue:
        print("[OK] 没有待发送的提醒")
        return
    
    print(f"[INFO] 发现 {len(queue)} 条待发送提醒")
    
    sent_count = 0
    for alert in queue:
        if send_alert(alert, recipient):
            sent_count += 1
    
    # 清空队列（已发送的已标记，未发送的保留）
    remaining = [a for a in queue if not load_state().get(a['key'])]
    with open(QUEUE_FILE, 'w') as f:
        json.dump(remaining, f, ensure_ascii=False)
    
    print(f"[OK] 发送完成: {sent_count}/{len(queue)} 条成功")

if __name__ == '__main__':
    main()
