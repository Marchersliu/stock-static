from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册字体
try:
    pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
    font_name = 'PingFang'
except:
    font_name = 'Helvetica'

pdf_path = '/Users/hf/.kimi_openclaw/workspace/协作总结_喷涂厂时间轴.pdf'
c = canvas.Canvas(pdf_path, pagesize=A4)
width, height = A4

# 标题
c.setFont(font_name, 16)
c.drawString(20*mm, height - 20*mm, "喷涂厂项目时间轴（XDR & Darfon Substrates）")
c.drawString(20*mm, height - 28*mm, "—— 与 AI 协作完成")

# 插入图片
img_path = '/Users/hf/.kimi_openclaw/workspace/协作总结_喷涂厂时间轴.png'
c.drawImage(img_path, 15*mm, height - 270*mm, width=180*mm, preserveAspectRatio=True, anchor='n')

# 总结文字
c.setFont(font_name, 10)
y = height - 280*mm

summary_lines = [
    "📋 协作总结",
    "",
    "用户：把喷涂厂两个substrates（XDR + Darfon）的项目按时间轴做成Excel，",
    "要求：XDR和Darfon上下并排，时间从左到右，假期和空白段合并成等宽单元格。",
    "",
    "我：用Python + openpyxl生成时间轴Excel，反复调整3版：",
    "  → 第1版：31天逐列，太宽",
    "  → 第2版：假期合并但宽度不一致",
    "  → 第3版：假期+空白段都合并，所有列等宽，一屏看完",
    "",
    "用户：可以了，你帮忙把咱们的对话，总结一下，你的回复太多内容，挑简要的，",
    "然后再把你做的excel文件截屏，总结成一张照片，我分享给我同事看看，",
    "如何和你一起工作。把我这句话也放入总结中。总结成pdf也行。",
    "",
    "我：生成这张总结图片（包含Excel截图+协作过程简述）。",
    "",
    "💡 协作特点：自然语言描述需求 → 快速迭代 → 精确交付"
]

for line in summary_lines:
    c.drawString(20*mm, y, line)
    y -= 6*mm
    if y < 20*mm:
        c.showPage()
        y = height - 20*mm
        c.setFont(font_name, 10)

c.save()
print(f"✅ 总结PDF已保存: {pdf_path}")

# 同步到iCloud
import shutil
shutil.copy(pdf_path, '/Users/hf/Library/Mobile Documents/com~apple~CloudDocs/下载文件/HF/协作总结_喷涂厂时间轴.pdf')
print("✅ PDF已同步到 iCloud")
