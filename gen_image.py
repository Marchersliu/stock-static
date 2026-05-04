import os
from PIL import Image, ImageDraw, ImageFont

# Canvas settings
WIDTH = 1080
BG_COLOR = (255, 255, 255)
HEADER_BG = (26, 82, 118)
DAY1_BG = (26, 82, 118)
DAY2_BG = (192, 57, 43)
DAY3_BG = (39, 174, 96)
ITEM_BG = (248, 249, 250)
TEXT_COLOR = (51, 51, 51)
LIGHT_TEXT = (136, 136, 136)
ACCENT_COLOR = (26, 82, 118)

def get_font(size, bold=False):
    """Try to get a nice font, fallback to default"""
    font_names = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
    ]
    for name in font_names:
        if os.path.exists(name):
            try:
                if "PingFang" in name or "STHeiti" in name:
                    # For .ttc files, try index 0 first, then 1 for bold
                    idx = 1 if bold else 0
                    return ImageFont.truetype(name, size, index=idx)
                return ImageFont.truetype(name, size)
            except:
                continue
    return ImageFont.load_default()

# Load fonts
try:
    font_title = get_font(44, bold=True)
    font_subtitle = get_font(24)
    font_day = get_font(30, bold=True)
    font_day_tag = get_font(20)
    font_time = get_font(24, bold=True)
    font_content = get_font(26)
    font_note = get_font(22)
    font_tips_title = get_font(26, bold=True)
    font_tips = get_font(22)
    font_footer = get_font(20)
except Exception as e:
    font_title = ImageFont.load_default()
    font_subtitle = ImageFont.load_default()
    font_day = ImageFont.load_default()
    font_day_tag = ImageFont.load_default()
    font_time = ImageFont.load_default()
    font_content = ImageFont.load_default()
    font_note = ImageFont.load_default()
    font_tips_title = ImageFont.load_default()
    font_tips = ImageFont.load_default()
    font_footer = ImageFont.load_default()

def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def wrap_text(text, font, max_width, draw):
    """Simple word wrapping for Chinese text"""
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        w, h = text_size(draw, test_line, font)
        if w > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines

# We need to pre-calculate height. Let's use a temporary draw object.
# First, create a large temporary image
img_temp = Image.new('RGB', (WIDTH, 5000), BG_COLOR)
draw_temp = ImageDraw.Draw(img_temp)

y = 0
positions = []

# ===== HEADER =====
y += 30
positions.append(('header_title', y))
y += 55
positions.append(('header_sub', y))
y += 35

# ===== DAY 1 =====
y += 20
positions.append(('day1_header', y))
y += 50
positions.append(('day1_body_start', y))

# Day 1 items
day1_items = [
    ("10:00-12:00", "抵达入住", "海航威斯汀，天河区林和中路6号"),
    ("12:00-14:00", "午餐：陶陶居", "正佳广场店，菠萝包、虾饺、凤爪、艇仔粥"),
    ("14:30-17:00", "广东省博物馆", "⚠️ 提前1天公众号预约！看恐龙化石、海洋馆"),
    ("17:00-18:00", "花城广场+海心桥", "免费，看广州塔全景"),
    ("18:00-19:30", "晚餐：点都德", "红米肠、流沙包、蛋挞、蒸排骨"),
    ("19:30-21:00", "广州塔夜景", "433米观光厅150元，18:30-19:30最佳"),
]

for time, title, note in day1_items:
    positions.append(('item', y, time, title, note))
    # estimate height
    title_lines = wrap_text(title, font_content, WIDTH - 180, draw_temp)
    note_lines = wrap_text(note, font_note, WIDTH - 180, draw_temp)
    h = max(30, len(title_lines) * 32 + len(note_lines) * 28 + 10)
    y += h + 12

y += 15  # padding

# ===== DAY 2 =====
y += 20
positions.append(('day2_header', y))
y += 50
positions.append(('day2_body_start', y))

day2_items = [
    ("08:00-09:00", "退房+换酒店", "威斯汀退房，打车去长隆酒店/熊猫酒店"),
    ("09:30-11:30", "欢乐世界南门进", "哈比王国：梦幻转马→奇妙车队→飞马家庭过山车"),
    ("11:30-12:00", "4D影院", "坐着看，歇脚避暑"),
    ("12:00-13:30", "园区内午餐", "欢乐小镇餐厅，有儿童套餐"),
    ("13:30-14:30", "急流勇进+飓风飞椅", "会湿身，自带雨衣！"),
    ("14:30-15:30", "机甲大巡游", "15:00必看！占第一排，演员会互动"),
    ("15:30-17:00", "欢乐摩天轮+二刷", "看日落，喜欢的项目再玩一遍"),
    ("18:30", "大马戏占座", "提前1小时占座！选CD区第一排靠栏杆"),
    ("19:30-21:00", "长隆国际大马戏", "必看招牌，10岁女孩全程惊叹"),
]

for time, title, note in day2_items:
    positions.append(('item', y, time, title, note))
    title_lines = wrap_text(title, font_content, WIDTH - 180, draw_temp)
    note_lines = wrap_text(note, font_note, WIDTH - 180, draw_temp)
    h = max(30, len(title_lines) * 32 + len(note_lines) * 28 + 10)
    y += h + 12

# Tips box for day2
tips_title = "🎢 她能玩 vs 不能玩"
tips_lines = [
    "✅ 能玩：梦幻转马、飞马家庭过山车、急流勇进、",
    "   飓风飞椅、摩天轮、4D影院",
    "❌ 别排：垂直/十环/火箭过山车、U型滑板、",
    "   超级大摆锤、跳楼机",
]
y += 10
positions.append(('tips', y, tips_title, tips_lines))
for line in tips_lines:
    y += 28
y += 20

# ===== DAY 3 =====
y += 20
positions.append(('day3_header', y))
y += 50
positions.append(('day3_body_start', y))

day3_items = [
    ("09:00-11:00", "自然醒+酒店早餐", "Lazy morning，回血"),
    ("11:00-13:00", "飞鸟乐园 / 休息", "二选一：百鸟飞歌(11:30)、喂火烈鸟，或游泳"),
    ("13:00-14:00", "午餐：滋粥楼/大鸽饭", "顺德菜清淡，孩子吃得惯"),
    ("14:30", "出发去白云机场", "长隆→机场约50-60分钟，五一预留充分"),
]

for time, title, note in day3_items:
    positions.append(('item', y, time, title, note))
    title_lines = wrap_text(title, font_content, WIDTH - 180, draw_temp)
    note_lines = wrap_text(note, font_note, WIDTH - 180, draw_temp)
    h = max(30, len(title_lines) * 32 + len(note_lines) * 28 + 10)
    y += h + 12

# Pack box
pack_title = "🎒 带女儿必带装备"
pack_lines = [
    "✓ 加厚雨衣+鞋套×2（急流勇进用）",
    "✓ 小风扇/便携扇子（排队救命）",
    "✓ 防晒霜（广州5月已经很热）",
    "✓ 小零食+水（园区饮料30元/瓶）",
    "✓ 舒适运动鞋（全天走路）",
    "✓ 防丢绳（人多防走散）",
]
y += 15
positions.append(('pack', y, pack_title, pack_lines))
for line in pack_lines:
    y += 28
y += 25

# Footer
positions.append(('footer', y))
y += 40

TOTAL_HEIGHT = y + 30

# ===== RENDER =====
img = Image.new('RGB', (WIDTH, TOTAL_HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

y_cursor = 0

# Header
y_cursor += 30
draw.text((WIDTH//2, y_cursor), "🗺️ 广州五一三日行程", font=font_title, fill=HEADER_BG, anchor="mt")
y_cursor += 55
draw.text((WIDTH//2, y_cursor), "5.2-5.4 | 威斯汀→长隆 | 带10岁女儿", font=font_subtitle, fill=LIGHT_TEXT, anchor="mt")
y_cursor += 35

# Separator line
draw.line([(40, y_cursor), (WIDTH-40, y_cursor)], fill=(230, 230, 230), width=2)
y_cursor += 20

# ===== DAY 1 =====
y_cursor += 20
draw.rounded_rectangle((30, y_cursor, WIDTH-30, y_cursor+50), radius=12, fill=DAY1_BG)
draw.text((50, y_cursor+25), "📅 5月2日（周六）天河CBD", font=font_day, fill=(255,255,255), anchor="lm")
draw.text((WIDTH-50, y_cursor+25), "入住威斯汀", font=font_day_tag, fill=(255,255,255), anchor="rm")
y_cursor += 65

for time, title, note in day1_items:
    # Item background
    draw.rounded_rectangle((35, y_cursor, WIDTH-35, y_cursor+80), radius=10, fill=ITEM_BG)
    
    # Time
    draw.text((55, y_cursor+15), time, font=font_time, fill=DAY1_BG)
    
    # Title
    tw, th = text_size(draw, time, font_time)
    draw.text((55, y_cursor+45), title, font=font_content, fill=TEXT_COLOR)
    
    # Note
    nw, nh = text_size(draw, title, font_content)
    note_y = y_cursor + 45 + nh + 2
    draw.text((55, note_y), note, font=font_note, fill=LIGHT_TEXT)
    
    y_cursor += 90

y_cursor += 10

# ===== DAY 2 =====
y_cursor += 20
draw.rounded_rectangle((30, y_cursor, WIDTH-30, y_cursor+50), radius=12, fill=DAY2_BG)
draw.text((50, y_cursor+25), "📅 5月3日（周日）长隆欢乐世界", font=font_day, fill=(255,255,255), anchor="lm")
draw.text((WIDTH-50, y_cursor+25), "换住长隆", font=font_day_tag, fill=(255,255,255), anchor="rm")
y_cursor += 65

for time, title, note in day2_items:
    # Calculate needed height
    title_lines = wrap_text(title, font_content, WIDTH - 180, draw)
    note_lines = wrap_text(note, font_note, WIDTH - 180, draw)
    h = max(60, len(title_lines) * 32 + len(note_lines) * 28 + 15)
    
    draw.rounded_rectangle((35, y_cursor, WIDTH-35, y_cursor+h), radius=10, fill=ITEM_BG)
    
    # Time (left column)
    draw.text((55, y_cursor+12), time, font=font_time, fill=DAY2_BG)
    
    # Title & note (right area)
    tx = 55
    ty = y_cursor + 12
    for line in title_lines:
        draw.text((tx, ty), line, font=font_content, fill=TEXT_COLOR)
        ty += 32
    for line in note_lines:
        draw.text((tx, ty), line, font=font_note, fill=LIGHT_TEXT)
        ty += 28
    
    y_cursor += h + 8

# Tips box
y_cursor += 10
tips_h = 40 + len(tips_lines) * 30 + 15
draw.rounded_rectangle((35, y_cursor, WIDTH-35, y_cursor+tips_h), radius=10, fill=(232, 244, 253))
draw.text((55, y_cursor+20), tips_title, font=font_tips_title, fill=DAY1_BG)
ty = y_cursor + 50
for line in tips_lines:
    draw.text((55, ty), line, font=font_tips, fill=TEXT_COLOR)
    ty += 30
y_cursor += tips_h + 10

# ===== DAY 3 =====
y_cursor += 20
draw.rounded_rectangle((30, y_cursor, WIDTH-30, y_cursor+50), radius=12, fill=DAY3_BG)
draw.text((50, y_cursor+25), "📅 5月4日（周一）轻松返程", font=font_day, fill=(255,255,255), anchor="lm")
draw.text((WIDTH-50, y_cursor+25), "下午飞机", font=font_day_tag, fill=(255,255,255), anchor="rm")
y_cursor += 65

for time, title, note in day3_items:
    title_lines = wrap_text(title, font_content, WIDTH - 180, draw)
    note_lines = wrap_text(note, font_note, WIDTH - 180, draw)
    h = max(60, len(title_lines) * 32 + len(note_lines) * 28 + 15)
    
    draw.rounded_rectangle((35, y_cursor, WIDTH-35, y_cursor+h), radius=10, fill=ITEM_BG)
    
    draw.text((55, y_cursor+12), time, font=font_time, fill=DAY3_BG)
    
    tx = 55
    ty = y_cursor + 12
    for line in title_lines:
        draw.text((tx, ty), line, font=font_content, fill=TEXT_COLOR)
        ty += 32
    for line in note_lines:
        draw.text((tx, ty), line, font=font_note, fill=LIGHT_TEXT)
        ty += 28
    
    y_cursor += h + 8

# Pack box
y_cursor += 15
pack_h = 40 + len(pack_lines) * 30 + 15
draw.rounded_rectangle((35, y_cursor, WIDTH-35, y_cursor+pack_h), radius=10, fill=(253, 242, 242))
draw.text((55, y_cursor+20), pack_title, font=font_tips_title, fill=DAY2_BG)
ty = y_cursor + 50
for line in pack_lines:
    draw.text((55, ty), line, font=font_tips, fill=TEXT_COLOR)
    ty += 30
y_cursor += pack_h + 15

# Footer
y_cursor += 10
draw.text((WIDTH//2, y_cursor), "祝你和女儿玩得开心！🎉", font=font_footer, fill=LIGHT_TEXT, anchor="mt")

# Save
output_path = "/Users/hf/.kimi_openclaw/workspace/广州五一行程.png"
img.save(output_path, "PNG", quality=95)
print(f"Saved to {output_path}, size: {img.size}")
