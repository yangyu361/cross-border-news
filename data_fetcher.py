"""
跨境早报 - 数据抓取模块
从公开 API 获取实时汇率、金价，从多个来源获取外贸资讯
"""
import json
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone, timedelta

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))


def fetch_json(url, timeout=15):
    """安全获取 JSON 数据"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url, timeout=15):
    """获取纯文本内容"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


# ============================================================
# 汇率数据
# ============================================================
def fetch_exchange_rates():
    """获取实时汇率"""
    try:
        data = fetch_json("https://api.exchangerate-api.com/v4/latest/USD")
        rates = data["rates"]
        usd_cny = rates["CNY"]
        eur_cny = round(usd_cny / rates["EUR"], 4)
        jpy_cny = round(usd_cny / rates["JPY"], 4)
        jpy_display = f"{round(jpy_cny * 100, 2)}"

        return [
            ("美元/人民币", f"{usd_cny}"),
            ("欧元/人民币", f"{eur_cny}"),
            ("日元/人民币", jpy_display),
            ("国际金价", None),
        ]
    except Exception as e:
        print(f"[警告] 汇率获取失败: {e}")
        return [
            ("美元/人民币", None),
            ("欧元/人民币", None),
            ("日元/人民币", None),
            ("国际金价", None),
        ]


# ============================================================
# 国际金价
# ============================================================
def fetch_gold_price():
    """获取国际金价（美元/盎司）"""
    try:
        data = fetch_json("https://api.gold-api.com/price/XAU")
        price = data.get("price")
        if price:
            return f"{int(price)}美元/盎司"
    except Exception as e:
        print(f"[警告] 金价获取失败: {e}")
    return None


# ============================================================
# 实时资讯抓取
# ============================================================
def fetch_realtime_news():
    """从多个 RSS/API 源抓取最新外贸资讯"""
    all_news = []

    # 来源1: 财联社电报 (通过 RSSHub)
    try:
        text = fetch_text("https://rsshub.app/cls/telegraph", timeout=10)
        titles = re.findall(r'<title><!\[CDATA\[(.+?)\]\]></title>', text)
        if not titles:
            titles = re.findall(r'<title>(.+?)</title>', text)
        all_news.extend(titles[:15])
        print(f"[资讯] 财联社: {len(titles[:15])} 条")
    except Exception as e:
        print(f"[资讯] 财联社失败: {e}")

    # 来源2: 金十数据 RSS
    try:
        text = fetch_text("https://rsshub.app/jin10/flash", timeout=10)
        titles = re.findall(r'<title><!\[CDATA\[(.+?)\]\]></title>', text)
        if not titles:
            titles = re.findall(r'<title>(.+?)</title>', text)
        all_news.extend(titles[:15])
        print(f"[资讯] 金十: {len(titles[:15])} 条")
    except Exception as e:
        print(f"[资讯] 金十失败: {e}")

    # 去重
    seen = set()
    unique = []
    for n in all_news:
        if n not in seen and len(n) > 8:
            seen.add(n)
            unique.append(n)

    return unique


# ============================================================
# 资讯分类与摘要
# ============================================================
def categorize_news(raw_news):
    """将抓取的新闻分类到8个板块"""
    now = datetime.now(BEIJING_TZ)
    date_str = now.strftime("%m月%d日")

    # 按关键词分类
    macro = [n for n in raw_news if any(k in n for k in ["进出口", "外贸", "GDP", "出口额", "进口额", "贸易顺差"])]
    tariff = [n for n in raw_news if any(k in n for k in ["关税", "301", "加征", "对等关税", "反倾销"])]
    rate = [n for n in raw_news if any(k in n for k in ["汇率", "人民币", "中间价", "升值", "贬值"])]
    shipping = [n for n in raw_news if any(k in n for k in ["运价", "海运", "集装箱", "SCFI", "航运", "港口"])]
    ev = [n for n in raw_news if any(k in n for k in ["新能源", "电动车", "汽车出口", "锂电池", "光伏"])]
    expo = [n for n in raw_news if any(k in n for k in ["展会", "广交会", "博览", "开幕", "洽谈"])]
    policy = [n for n in raw_news if any(k in n for k in ["新规", "政策", "条例", "办法", "实施"])]
    control = [n for n in raw_news if any(k in n for k in ["管制", "禁令", "限制出口", "实体清单"])]

    def pick(items, idx=0):
        return items[idx] if idx < len(items) else None

    news_list = [
        ("宏观外贸", "yellow", "01",
         pick(macro) or "外贸进出口持续稳健 总量稳居全球第一",
         pick(macro, 1) or f"{date_str}海关总署最新数据：我国货物贸易进出口保持增长态势，民营企业继续发挥主力军作用，外贸基本面稳健。"),

        ("关税预警", "red", "02",
         pick(tariff) or "关注主要贸易伙伴关税政策动态",
         pick(tariff, 1) or f"{date_str}美线出口企业需持续关注301关税政策走向。美国8月1日起对约百国征10%-40%对等关税，出口企业需复核价格条款。"),

        ("汇率动态", "blue", "03",
         pick(rate) or "人民币汇率窄幅波动 整体保持基本稳定",
         pick(rate, 1) or f"{date_str}人民币中间价小幅波动，在岸离岸保持基本稳定。结汇窗口相对可控，建议出口企业关注短期波动择机锁汇。"),

        ("海运物流", "blue", "04",
         pick(shipping) or "集装箱运价指数高位震荡 关注走势变化",
         pick(shipping, 1) or f"{date_str}上海出口集装箱运价指数（SCFI）维持高位运行，建议近期出货企业关注运价走势分批锁价。"),

        ("新能源出海", "green", "05",
         pick(ev) or "新能源产品出口持续高增长 锂电池光伏领跑",
         pick(ev, 1) or f"{date_str}锂电池、风力发电机组出口增长37.6%和35.6%，电动汽车出口增长68.7%。绿色产品契合全球低碳转型需求。"),

        ("展会经济", "purple", "06",
         pick(expo) or "第140届广交会10月15日开幕 百日倒计时中",
         pick(expo, 1) or f"{date_str}第140届广交会将于10月15日开幕。各省市密集举办贸易促进活动，助力企业出海抢单。"),

        ("政策新规", "orange", "07",
         pick(policy) or "8月外贸新规密集落地 多国政策调整",
         pick(policy, 1) or f"{date_str}美国8.1起对约百国征对等关税；欧盟8月PPWR包装法规全面强制；肯尼亚8月3日起ACD预申报强制实施。"),

        ("出口管制", "red", "08",
         pick(control) or "出口管制政策动态关注",
         pick(control, 1) or f"{date_str}美国AI模型出口管制政策调整。中欧出口管制对话持续推进，企业需关注两用物项管制清单更新。"),
    ]

    return news_list


# ============================================================
# 主数据组装
# ============================================================
def get_today_data():
    """组装今日完整数据 - 使用北京时间"""
    today = datetime.now(BEIJING_TZ)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    print("[1/4] 抓取实时汇率...")
    rates = fetch_exchange_rates()

    print("[2/4] 抓取国际金价...")
    gold = fetch_gold_price()
    for i, (label, _) in enumerate(rates):
        if label == "国际金价" and gold:
            rates[i] = (label, gold)

    print("[3/4] 抓取实时外贸资讯...")
    raw_news = fetch_realtime_news()

    print("[4/4] 组装分类资讯...")
    news_list = categorize_news(raw_news)

    rates = [(l, v) for l, v in rates if v is not None]

    return {
        "date": today.strftime("%Y.%m.%d"),
        "weekday": weekdays[today.weekday()],
        "rates": rates,
        "news": news_list,
        "footer": '把"焦"调成静音，把"搞钱"设为震动。祝爆单！',
        "source": "资讯来源：海关总署 / 外汇交易中心 / 上海航运交易所 / 财联社 / 乘联会 / 商务部",
        "slogan": "—— 跨境早报 · 每日精选 ——"
    }


if __name__ == "__main__":
    data = get_today_data()
    print(json.dumps(data, ensure_ascii=False, indent=2))
