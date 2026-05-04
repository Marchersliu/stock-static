#!/usr/bin/env python3
"""每日情报简报生成"""
import sys, json, argparse, subprocess
from pathlib import Path
from datetime import datetime

def generate_report(date_str, output_path):
    today = datetime.strptime(date_str, "%Y-%m-%d")
    
    # 读取股票数据（从 stock_service.py 缓存）
    stock_data = {}
    cache_file = Path("/tmp/stock_data.json")
    if cache_file.exists():
        stock_data = json.loads(cache_file.read_text())
    
    lines = [
        f"# 每日情报简报 · {date_str}",
        f"\n生成时间：{datetime.now().strftime('%H:%M')}",
        "\n---\n",
        "\n## 📊 持仓概览",
        "\n（数据来自Tushare Pro，交易时段自动刷新）",
        "\n---\n",
        "\n## 📰 重大新闻",
        "\n（自动抓取持仓股关联新闻）",
        "\n---\n",
        "\n## 🏭 原材料价格",
        "\n（来源：SMM/百川/卓创）",
        "\n---\n",
        "\n## 🌤️ 天气",
        "\n（来源：wttr.in）",
        "\n---\n",
        "\n## 📅 今日日程",
        "\n（来源：Apple Calendar）",
        "\n---\n",
        "\n## ⚡ 风险提示",
        "\n- 持仓股涨跌停监控",
        "- 原材料价格异动",
        "- 汇率/地缘风险",
        "\n---\n",
        "\n*本简报由AI自动生成，数据仅供参考，不构成投资建议。*",
    ]
    
    md_path = output_path.replace(".pdf", ".md")
    Path(md_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown报告已生成：{md_path}")
    
    # 尝试转PDF
    pdf_script = Path(__file__).parent.parent / "md-to-pdf" / "scripts" / "md_to_pdf.py"
    if pdf_script.exists():
        subprocess.run([sys.executable, str(pdf_script), md_path, "--output", output_path], check=False)
    else:
        print("md-to-pdf技能未安装，仅生成Markdown版本")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--output", default="~/Desktop/日报.pdf")
    args = parser.parse_args()
    generate_report(args.date, args.output)
