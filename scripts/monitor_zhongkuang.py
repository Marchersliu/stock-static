#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中矿资源(002738) 每日信号扫描脚本
工作日09:55自动执行
监控：碳酸锂价格 + Q2业绩预期 + 技术面信号
"""

import json
import datetime
import os

# 信号阈值
SIGNALS = {
    "lithium_price_stable": {
        "target": 200000,  # 20万/吨
        "current": 192000,  # 当前约19.2万（需手动更新或API抓取）
        "source": "SMM电池级碳酸锂现货"
    },
    "q2_profit": {
        "q1_growth": 277,  # Q1净利+277%
        "need": "Q2延续高增长",
        "next_report": "2026-08-15"  # Q2财报预估
    },
    "technical": {
        "buy_zone": "65-68元",
        "current": None,  # 需抓取
        "rsi_threshold": 30,
        "volume_condition": "缩量止跌"
    }
}

def check_signals():
    """检查当前信号状态"""
    now = datetime.datetime.now()
    
    report = {
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "ticker": "002738.SZ",
        "name": "中矿资源",
        "status": "监控中",
        "signals": {}
    }
    
    # 信号1: 碳酸锂价格
    report["signals"]["lithium_price"] = {
        "name": "碳酸锂价格站稳20万",
        "status": "⏳ 等待",
        "note": "当前约19.2万，需每日查看SMM/上海有色网"
    }
    
    # 信号2: Q2业绩
    days_to_q2 = (datetime.datetime(2026, 8, 15) - now).days
    report["signals"]["q2_earnings"] = {
        "name": "Q2业绩延续高增长",
        "status": "⏳ 等待",
        "note": f"Q2财报预计8月15日发布，还有{days_to_q2}天"
    }
    
    # 信号3: 技术面
    report["signals"]["technical"] = {
        "name": "技术面止跌（70-72元区间）",
        "status": "⏳ 等待",
        "note": "需手动查看行情软件：RSI6<30+缩量3天+70元附近企稳（现价73.07已偏高，等回调）"
    }
    
    # 综合判断
    report["action"] = "不满足入场条件，继续等待"
    report["next_check"] = "下一个工作日09:55"
    
    return report

def save_report(report):
    """保存报告到日志文件"""
    log_dir = os.path.expanduser("~/.kimi_openclaw/workspace/data")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "中矿资源_每日扫描.jsonl")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")
    
    return log_file

def print_summary(report):
    """打印扫描摘要"""
    print(f"\n{'='*60}")
    print(f"📊 中矿资源(002738) 每日信号扫描")
    print(f"时间: {report['date']}")
    print(f"{'='*60}")
    
    for key, sig in report["signals"].items():
        print(f"\n{sig['status']} {sig['name']}")
        print(f"   → {sig['note']}")
    
    print(f"\n{'-'*60}")
    print(f"📋 操作: {report['action']}")
    print(f"⏰ 下次检查: {report['next_check']}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    report = check_signals()
    log_file = save_report(report)
    print_summary(report)
    print(f"📁 报告已保存: {log_file}")
