import os
from PIL import Image, ImageDraw, ImageFont

# Canvas settings - wider for better readability
WIDTH = 1200
MARGIN = 50
CONTENT_W = WIDTH - MARGIN * 2
BG_COLOR = (255, 255, 255)
HEADER_BG = (26, 82, 118)
DAY1_BG = (26, 82, 118)
DAY2_BG = (192, 57, 43)
DAY3_BG = (39, 174, 96)
ITEM_BG = (248, 249, 250)
TEXT_COLOR = (51, 51, 51)
LIGHT_TEXT = (100, 100, 100)
WHITE = (255, 255, 255)

def get_font(size, bold=False):
    font_names = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
    ]
    for name in font_names:
        if os.path.exists(name):
            try:
                if ".ttc" in name:
                    idx = 1 if bold else 0
                    return ImageFont.truetype(name, size, index=idx)
                return ImageFont.truetype(name, size)
            except:
                continue
    return ImageFont.load_default()

# Load fonts
font_title = get_font(48, bold=True)
font_subtitle = get_font(28)
font_day = get_font(32, bold=True)
font_day_tag = get_font(22)
font_time = get_font(26, bold=True)
font_content = get_font(28)
font_note = get_font(24)
font_tips_title = get_font(28, bold=True)
font_tips = get_font(24)
font_footer = get_font(24)

def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_text_wrapped(draw, text, font, max_width, x, y, fill, line_height):
    """Draw wrapped text, return total height used"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        w, _ = text_size(draw, test, font)
        if w > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_height), line, font=font, fill=fill)
    
    return len(lines) * line_height

def measure_wrapped_height(draw, text, font, max_width, line_height):
    """Measure height of wrapped text without drawing"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        w, _ = text_size(draw, test, font)
        if w > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return len(lines) * line_height

# First pass: calculate total height needed
img_calc = Image.new('RGB', (WIDTH, 1), BG_COLOR)
draw_calc = ImageDraw.Draw(img_calc)

y = 0

# Header
y += 40
y += 60  # title
y += 40  # subtitle
y += 30  # gap

# Day 1
y += 25
y += 55  # day header
y += 20  # padding

day1_items = [
    ("10:00-12:00", "抵达入住", "海航威斯汀，天河区林和中路6号"),
    ("12:00-14:00", "午餐：陶陶居", "正佳广场店，菠萝包、虾饺、凤爪、艇仔粥"),
    ("14:30-17:00", "广东省博物馆", "⚠️ 提前1天公众号预约！看恐龙化石、海洋馆、科威特展"),
    ("17:00-18:00", "花城广场 + 海心桥", "免费，看广州塔全景，拍照"),
    ("18:00-19:30", "晚餐：点都德", "红米肠、流沙包、蛋挞、蒸排骨，孩子爱吃"),
    ("19:30-21:00", "广州塔夜景", "433米观光厅150元，18:30-19:30最佳时段"),
]

for time, title, note in day1_items:
    y += 15  # gap before item
    inner_y = 0
    inner_y += 15  # top padding
    inner_y += draw_text_wrapped(draw_calc, time, font_time, CONTENT_W - 40, 0, 0, TEXT_COLOR, 36)
    inner_y += 8   # gap between time and title
    inner_y += draw_text_wrapped(draw_calc, title, font_content, CONTENT_W - 40, 0, 0, TEXT_COLOR, 38)
    inner_y += 6   # gap between title and note
    inner_y += draw_text_wrapped(draw_calc, note, font_note, CONTENT_W - 40, 0, 0, LIGHT_TEXT, 32)
    inner_y += 15  # bottom padding
    y += max(inner_y, 80)

y += 20

# Day 2
y += 25
y += 55
y += 20

day2_items = [
    ("08:00-09:00", "退房 + 换酒店", "威斯汀退房，打车去长隆酒店/熊猫酒店，存行李"),
    ("09:30-11:30", "欢乐世界 南门进", "哈比王国：梦幻转马 → 奇妙车队 → 飞马家庭过山车"),
    ("11:30-12:00", "4D影院", "坐着看，歇脚避暑"),
    ("12:00-13:30", "园区内午餐", "欢乐小镇餐厅，有儿童套餐"),
    ("13:30-14:30", "急流勇进 + 飓风飞椅", "会湿身，自带雨衣！园区卖50元/套"),
    ("14:30-15:30", "机甲大巡游", "15:00 必看！占第一排，演员会互动"),
    ("15:30-17:00", "欢乐摩天轮 + 二刷", "看日落拍照。喜欢的项目再玩一遍"),
    ("18:30", "大马戏占座", "提前1小时占座！选CD区第一排靠栏杆"),
    ("19:30-21:00", "长隆国际大马戏", "必看招牌，10岁女孩全程惊叹"),
]

for time, title, note in day2_items:
    y += 15
    inner_y = 0
    inner_y += 15
    inner_y += draw_text_wrapped(draw_calc, time, font_time, CONTENT_W - 40, 0, 0, TEXT_COLOR, 36)
    inner_y += 8
    inner_y += draw_text_wrapped(draw_calc, title, font_content, CONTENT_W - 40, 0, 0, TEXT_COLOR, 38)
    inner_y += 6
    inner_y += draw_text_wrapped(draw_calc, note, font_note, CONTENT_W - 40, 0, 0, LIGHT_TEXT, 32)
    inner_y += 15
    y += max(inner_y, 80)

# Tips box
y += 15
tips_title = "她能玩 vs 不能玩"
tips_lines = [
    "✅ 能玩：梦幻转马、飞马家庭过山车、急流勇进、飓风飞椅、摩天轮、4D影院",
    "❌ 别排：垂直过山车、十环过山车、火箭过山车、U型滑板、超级大摆锤、跳楼机",
]
y += 20  # title
for line in tips_lines:
    y += 34
y += 20  # bottom padding

y += 20

# Day 3
y += 25
y += 55
y += 20

day3_items = [
    ("09:00-11:00", "自然醒 + 酒店早餐", "Lazy morning，回血"),
    ("11:00-13:00", "飞鸟乐园 / 休息", "二选一：百鸟飞歌(11:30)、喂火烈鸟，或酒店游泳"),
    ("13:00-14:00", "午餐：滋粥楼 / 大鸽饭", "顺德菜清淡，孩子吃得惯"),
    ("14:30", "出发去白云机场", "长隆→机场约50-60分钟，五一预留充分"),
]

for time, title, note in day3_items:
    y += 15
    inner_y = 0
    inner_y += 15
    inner_y += draw_text_wrapped(draw_calc, time, font_time, CONTENT_W - 40, 0, 0, TEXT_COLOR, 36)
    inner_y += 8
    inner_y += draw_text_wrapped(draw_calc, title, font_content, CONTENT_W - 40, 0, 0, TEXT_COLOR, 38)
    inner_y += 6
    inner_y += draw_text_wrapped(draw_calc, note, font_note, CONTENT_W - 40, 0, 0, LIGHT_TEXT, 32)
    inner_y += 15
    y += max(inner_y, 80)

# Pack box
y += 15
pack_title = "带女儿必带装备"
pack_lines = [
    "✓ 加厚雨衣 + 鞋套 ×2（急流勇进用，园区卖50元/套）",
    "✓ 小风扇 / 便携扇子（排队救命）",
    "✓ 防晒霜（广州5月已经很热）",
    "✓ 小零食 + 水（园区饮料30元/瓶）",
    "✓ 舒适运动鞋（全天走路）",
    "✓ 防丢绳（人多防走散）",
]
y += 20  # title
for line in pack_lines:
    y += 34
y += 20

# Footer
y += 30
y += 40

TOTAL_HEIGHT = y + 40

# ===== RENDER =====
img = Image.new('RGB', (WIDTH, TOTAL_HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

y_cursor = 0

# Header
y_cursor += 40
draw.text((WIDTH // 2, y_cursor), "🗺️ 广州五一三日行程", font=font_title, fill=HEADER_BG, anchor="mt")
y_cursor += 60
draw.text((WIDTH // 2, y_cursor), "5.2 - 5.4  |  威斯汀 → 长隆  |  带10岁女儿", font=font_subtitle, fill=LIGHT_TEXT, anchor="mt")
y_cursor += 40

# Separator
draw.line([(MARGIN, y_cursor), (WIDTH - MARGIN, y_cursor)], fill=(220, 220, 220), width=2)
y_cursor += 30

# ===== DAY 1 =====
y_cursor += 25
draw.rounded_rectangle((MARGIN, y_cursor, WIDTH - MARGIN, y_cursor + 55), radius=14, fill=DAY1_BG)
draw.text((MARGIN + 20, y_cursor + 27), "📅  5月2日（周六）  天河CBD", font=font_day, fill=WHITE, anchor="lm")
draw.text((WIDTH - MARGIN - 20, y_cursor + 27), "入住威斯汀", font=font_day_tag, fill=WHITE, anchor="rm")
y_cursor += 75

for time, title, note in day1_items:
    y_cursor += 15
    
    # Calculate height
    h_time = measure_wrapped_height(draw, time, font_time, CONTENT_W - 40, 36)
    h_title = measure_wrapped_height(draw, title, font_content, CONTENT_W - 40, 38)
    h_note = measure_wrapped_height(draw, note, font_note, CONTENT_W - 40, 32)
    item_h = 15 + h_time + 8 + h_title + 6 + h_note + 15
    item_h = max(item_h, 90)
    
    draw.rounded_rectangle((MARGIN + 5, y_cursor, WIDTH - MARGIN - 5, y_cursor + item_h), radius=12, fill=ITEM_BG)
    
    inner_y = y_cursor + 15
    inner_y += draw_text_wrapped(draw, time, font_time, CONTENT_W - 40, MARGIN + 20, inner_y, DAY1_BG, 36)
    inner_y += 8
    inner_y += draw_text_wrapped(draw, title, font_content, CONTENT_W - 40, MARGIN + 20, inner_y, TEXT_COLOR, 38)
    inner_y += 6
    inner_y += draw_text_wrapped(draw, note, font_note, CONTENT_W - 40, MARGIN + 20, inner_y, LIGHT_TEXT, 32)
    
    y_cursor += item_h

y_cursor += 25

# ===== DAY 2 =====
y_cursor += 25
draw.rounded_rectangle((MARGIN, y_cursor, WIDTH - MARGIN, y_cursor + 55), radius=14, fill=DAY2_BG)
draw.text((MARGIN + 20, y_cursor + 27), "📅  5月3日（周日）  长隆欢乐世界", font=font_day, fill=WHITE, anchor="lm")
draw.text((WIDTH - MARGIN - 20, y_cursor + 27), "换住长隆", font=font_day_tag, fill=WHITE, anchor="rm")
y_cursor += 75

for time, title, note in day2_items:
    y_cursor += 15
    
    h_time = measure_wrapped_height(draw, time, font_time, CONTENT_W - 40, 36)
    h_title = measure_wrapped_height(draw, title, font_content, CONTENT_W - 40, 38)
    h_note = measure_wrapped_height(draw, note, font_note, CONTENT_W - 40, 32)
    item_h = 15 + h_time + 8 + h_title + 6 + h_note + 15
    item_h = max(item_h, 90)
    
    draw.rounded_rectangle((MARGIN + 5, y_cursor, WIDTH - MARGIN - 5, y_cursor + item_h), radius=12, fill=ITEM_BG)
    
    inner_y = y_cursor + 15
    inner_y += draw_text_wrapped(draw, time, font_time, CONTENT_W - 40, MARGIN + 20, inner_y, DAY2_BG, 36)
    inner_y += 8
    inner_y += draw_text_wrapped(draw, title, font_content, CONTENT_W - 40, MARGIN + 20, inner_y, TEXT_COLOR, 38)
    inner_y += 6
    inner_y += draw_text_wrapped(draw, note, font_note, CONTENT_W - 40, MARGIN + 20, inner_y, LIGHT_TEXT, 32)
    
    y_cursor += item_h

# Tips box
y_cursor += 20
tips_h = 20 + 34 + len(tips_lines) * 34 + 20
draw.rounded_rectangle((MARGIN + 5, y_cursor, WIDTH - MARGIN - 5, y_cursor + tips_h), radius=12, fill=(232, 244, 253))
draw.text((MARGIN + 20, y_cursor + 20), "🎢  " + tips_title, font=font_tips_title, fill=DAY1_BG)
ty = y_cursor + 20 + 34
for line in tips_lines:
    draw.text((MARGIN + 20, ty), line, font=font_tips, fill=TEXT_COLOR)
    ty += 34
y_cursor += tips_h + 10

y_cursor += 20

# ===== DAY 3 =====
y_cursor += 25
draw.rounded_rectangle((MARGIN, y_cursor, WIDTH - MARGIN, y_cursor + 55), radius=14, fill=DAY3_BG)
draw.text((MARGIN + 20, y_cursor + 27), "📅  5月4日（周一）  轻松返程", font=font_day, fill=WHITE, anchor="lm")
draw.text((WIDTH - MARGIN - 20, y_cursor + 27), "下午飞机", font=font_day_tag, fill=WHITE, anchor="rm")
y_cursor += 75

for time, title, note in day3_items:
    y_cursor += 15
    
    h_time = measure_wrapped_height(draw, time, font_time, CONTENT_W - 40, 36)
    h_title = measure_wrapped_height(draw, title, font_content, CONTENT_W - 40, 38)
    h_note = measure_wrapped_height(draw, note, font_note, CONTENT_W - 40, 32)
    item_h = 15 + h_time + 8 + h_title + 6 + h_note + 15
    item_h = max(item_h, 90)
    
    draw.rounded_rectangle((MARGIN + 5, y_cursor, WIDTH - MARGIN - 5, y_cursor + item_h), radius=12, fill=ITEM_BG)
    
    inner_y = y_cursor + 15
    inner_y += draw_text_wrapped(draw, time, font_time, CONTENT_W - 40, MARGIN + 20, inner_y, DAY3_BG, 36)
    inner_y += 8
    inner_y += draw_text_wrapped(draw, title, font_content, CONTENT_W - 40, MARGIN + 20, inner_y, TEXT_COLOR, 38)
    inner_y += 6
    inner_y += draw_text_wrapped(draw, note, font_note, CONTENT_W - 40, MARGIN + 20, inner_y, LIGHT_TEXT, 32)
    
    y_cursor += item_h

# Pack box
y_cursor += 20
pack_h = 20 + 34 + len(pack_lines) * 34 + 20
draw.rounded_rectangle((MARGIN + 5, y_cursor, WIDTH - MARGIN - 5, y_cursor + pack_h), radius=12, fill=(253, 242, 242))
draw.text((MARGIN + 20, y_cursor + 20), "🎒  " + pack_title, font=font_tips_title, fill=DAY2_BG)
ty = y_cursor + 20 + 34
for line in pack_lines:
    draw.text((MARGIN + 20, ty), line, font=font_tips, fill=TEXT_COLOR)
    ty += 34
y_cursor += pack_h + 15

# Footer
y_cursor += 30
draw.text((WIDTH // 2, y_cursor), "祝你和女儿玩得开心！🎉", font=font_footer, fill=LIGHT_TEXT, anchor="mt")

# Save
output_path = "/Users/hf/.kimi_openclaw/workspace/广州五一行程_v2.png"
img.save(output_path, "PNG", quality=95)
print(f"Saved: {output_path}")
print(f"Size: {img.size[0]} x {img.size[1]} px")
