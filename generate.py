"""
跨境早报 - 每日外贸资讯图片生成器 (实时数据版)
风格：深蓝底 + 黄色高亮，符合朋友圈传播
"""
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# 同目录导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_fetcher import get_today_data

# ============ 配色 ============
BG_DARK = (10, 25, 47)
BG_CARD = (20, 35, 60)
ACCENT_YELLOW = (255, 200, 0)
ACCENT_RED = (220, 60, 60)
ACCENT_BLUE = (60, 130, 200)
ACCENT_GREEN = (50, 170, 100)
ACCENT_PURPLE = (150, 90, 180)
ACCENT_ORANGE = (230, 130, 50)
TEXT_WHITE = (240, 240, 240)
TEXT_GRAY = (170, 180, 200)
TEXT_DIM = (120, 130, 150)

COLOR_MAP = {
    "yellow": ACCENT_YELLOW,
    "red": ACCENT_RED,
    "blue": ACCENT_BLUE,
    "green": ACCENT_GREEN,
    "purple": ACCENT_PURPLE,
    "orange": ACCENT_ORANGE,
}


def get_font(size):
    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except:
                pass
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """按像素宽度自动换行"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def measure(text, font, draw):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def generate_image(TODAY, output_path):
    """生成图片主函数"""
    W, H = 1200, 3000
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # 字体
    f_title = get_font(80)
    f_subtitle = get_font(30)
    f_date = get_font(52)
    f_weekday = get_font(28)
    f_section = get_font(24)
    f_number = get_font(32)
    f_rate_label = get_font(26)
    f_rate_value = get_font(44)
    f_news_title = get_font(34)
    f_news_body = get_font(24)
    f_footer = get_font(30)
    f_source = get_font(22)
    f_slogan = get_font(24)

    LEFT = 70
    RIGHT = W - 70
    CONTENT_W = RIGHT - LEFT

    y = 70
    # 主标题
    draw.text((LEFT, y), "跨境早报", fill=ACCENT_YELLOW, font=f_title)
    y += 95
    draw.text((LEFT, y), "CROSS-BORDER DAILY NEWS", fill=TEXT_GRAY, font=f_subtitle)

    # 右上日期
    w, _ = measure(TODAY["date"], f_date, draw)
    draw.text((RIGHT - w, 80), TODAY["date"], fill=TEXT_WHITE, font=f_date)
    w, _ = measure(TODAY["weekday"], f_weekday, draw)
    draw.text((RIGHT - w, 140), TODAY["weekday"], fill=TEXT_GRAY, font=f_weekday)

    # 分隔线
    y = 200
    draw.line([(LEFT, y), (RIGHT, y)], fill=ACCENT_YELLOW, width=2)
    y += 35

    # 汇率看板
    board_h = 140
    draw.rounded_rectangle([(LEFT, y), (RIGHT, y + board_h)], radius=14, fill=BG_CARD, outline=ACCENT_YELLOW, width=1)
    rate_count = len(TODAY["rates"])
    rate_w = CONTENT_W // max(rate_count, 1)
    for i, (label, val) in enumerate(TODAY["rates"]):
        cx = LEFT + i * rate_w + rate_w // 2
        lw, _ = measure(label, f_rate_label, draw)
        draw.text((cx - lw // 2, y + 28), label, fill=TEXT_GRAY, font=f_rate_label)
        vw, _ = measure(val, f_rate_value, draw)
        if vw > rate_w - 20:
            f_small = get_font(36)
            vw, _ = measure(val, f_small, draw)
            draw.text((cx - vw // 2, y + 72), val, fill=ACCENT_YELLOW, font=f_small)
        else:
            draw.text((cx - vw // 2, y + 72), val, fill=ACCENT_YELLOW, font=f_rate_value)
    y += board_h + 50

    # 新闻卡片
    for tag, color_key, num, title, body in TODAY["news"]:
        color = COLOR_MAP.get(color_key, ACCENT_YELLOW)

        title_lines = wrap_text(title, f_news_title, CONTENT_W - 40, draw)
        title_h = len(title_lines) * 44

        body_lines = wrap_text(body, f_news_body, CONTENT_W - 40, draw)
        body_h = len(body_lines) * 34

        card_h = 35 + 44 + 15 + title_h + 15 + body_h + 35

        draw.rounded_rectangle([(LEFT, y), (RIGHT, y + card_h)], radius=10, fill=BG_CARD)
        draw.rectangle([(LEFT, y), (LEFT + 8, y + card_h)], fill=ACCENT_YELLOW)

        tw, th = measure(tag, f_section, draw)
        tag_w = tw + 24
        tag_h = 38
        draw.rounded_rectangle([(LEFT + 25, y + 22), (LEFT + 25 + tag_w, y + 22 + tag_h)], radius=4, fill=color)
        draw.text((LEFT + 25 + (tag_w - tw) // 2, y + 22 + 5), tag, fill=TEXT_WHITE, font=f_section)
        draw.text((LEFT + 25 + tag_w + 15, y + 24), num, fill=TEXT_DIM, font=f_number)

        cy = y + 35 + 44
        for line in title_lines:
            draw.text((LEFT + 25, cy), line, fill=TEXT_WHITE, font=f_news_title)
            cy += 44
        cy += 12
        for line in body_lines:
            draw.text((LEFT + 25, cy), line, fill=TEXT_GRAY, font=f_news_body)
            cy += 34

        y += card_h + 22

    # 底部
    y += 25
    draw.line([(LEFT, y), (RIGHT, y)], fill=(50, 70, 100), width=1)
    y += 30
    fw, _ = measure(TODAY["footer"], f_footer, draw)
    draw.text(((W - fw) // 2, y), TODAY["footer"], fill=ACCENT_YELLOW, font=f_footer)
    y += 55
    sw, _ = measure(TODAY["source"], f_source, draw)
    draw.text(((W - sw) // 2, y), TODAY["source"], fill=TEXT_DIM, font=f_source)
    y += 38
    slw, _ = measure(TODAY["slogan"], f_slogan, draw)
    draw.text(((W - slw) // 2, y), TODAY["slogan"], fill=TEXT_DIM, font=f_slogan)

    final = img.crop((0, 0, W, y + 100))
    final.save(output_path, "PNG", quality=95)
    print(f"图片生成成功: {final.size} → {output_path}")
    return output_path


if __name__ == "__main__":
    print("=" * 50)
    print("跨境早报 - 开始生成")
    print("=" * 50)

    # 获取实时数据
    TODAY = get_today_data()

    # 生成图片
    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cross_border_daily.png")
    generate_image(TODAY, output)

    print("=" * 50)
    print("完成！")
    print("=" * 50)
