"""
跨境早报 - 推送模块
支持：Server酱（个人微信）、企业微信群机器人、钉钉群机器人、飞书群机器人

图片推送策略：
- Server酱：先上传到 freeimage.host 图床，再推送 markdown 图片链接
- 企业微信：直接推 base64 图片
- 钉钉/飞书：推 markdown 消息 + 图床链接
"""
import json
import base64
import hashlib
import urllib.request
import urllib.parse
import os
import uuid
import mimetypes


def read_image_as_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_md5(image_path):
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ============================================================
# 免费图床上传（freeimage.host）
# ============================================================
def upload_to_image_host(image_path):
    """
    上传图片到 freeimage.host 免费图床
    返回图片直链 URL，失败返回 None
    """
    print("[图床] 上传图片到 freeimage.host...")
    img_b64 = read_image_as_base64(image_path)

    data = urllib.parse.urlencode({
        "type": "base64",
        "action": "upload",
        "key": "6d207e02198a847aa98d0a2a901485a5",
        "source": img_b64,
        "format": "json"
    }).encode()

    req = urllib.request.Request("https://freeimage.host/api/1/upload", data=data, method="POST")
    req.add_header("User-Agent", "Mozilla/5.0")

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                img_url = result["image"]["url"]
                display_url = result["image"].get("display_url", img_url)
                print(f"[图床] 上传成功: {img_url}")
                return img_url, display_url
        except Exception as e:
            print(f"[图床] 第 {attempt+1} 次上传失败: {e}")
            if attempt < 2:
                import time
                time.sleep(3)

    print("[图床] 上传失败，将仅推送文字消息")
    return None, None


# ============================================================
# 方案 A：Server酱（推送到个人微信）
# ============================================================
def push_serverchan(image_path, sckey, title="跨境早报"):
    """
    通过 Server酱 推送到个人微信
    图片先上传图床，再推送 markdown 图片链接
    """
    print("[推送] Server酱...")

    # 1. 上传图片到图床
    img_url, display_url = upload_to_image_host(image_path)

    # 2. 构造 markdown 消息
    date_str = os.popen("date '+%Y.%m.%d'").read().strip()
    if img_url:
        desp = f"""## {title} · {date_str}

![{title}]({img_url})

---
> 把"焦"调成静音，把"搞钱"设为震动。祝爆单！

[点击查看原图]({img_url})
"""
    else:
        desp = f"今日早报已生成，但图片上传失败，请手动查看。"

    # 3. 推送
    data = urllib.parse.urlencode({
        "title": f"{title} {date_str}",
        "desp": desp
    }).encode()

    try:
        req = urllib.request.Request(
            f"https://sctapi.ftqq.com/{sckey}.send",
            data=data,
            method="POST"
        )
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if result.get("code") == 0:
                print("[推送] Server酱推送成功！")
                return True
            else:
                print(f"[推送] Server酱推送失败: {result}")
                return False
    except Exception as e:
        print(f"[推送] Server酱异常: {e}")
        return False


# ============================================================
# 方案 B：企业微信群机器人（直接推图片）
# ============================================================
def push_wechat_work(image_path, webhook_key, title="跨境早报"):
    """
    通过企业微信群机器人推送图片到微信群
    """
    print("[推送] 企业微信群机器人...")
    webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}"

    img_b64 = read_image_as_base64(image_path)
    img_md5 = get_image_md5(image_path)

    payload = {
        "msgtype": "image",
        "image": {
            "base64": img_b64,
            "md5": img_md5
        }
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if result.get("errcode") == 0:
                print("[推送] 企业微信推送成功！")
                return True
            else:
                print(f"[推送] 企业微信推送失败: {result}")
                return False
    except Exception as e:
        print(f"[推送] 企业微信异常: {e}")
        return False


# ============================================================
# 方案 C：钉钉群机器人
# ============================================================
def push_dingtalk(image_path, webhook_key, title="跨境早报"):
    """
    通过钉钉群机器人推送（markdown + 图床链接）
    """
    print("[推送] 钉钉群机器人...")
    webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={webhook_key}"

    img_url, _ = upload_to_image_host(image_path)
    date_str = os.popen("date '+%Y.%m.%d'").read().strip()

    if img_url:
        text = f"## {title} · {date_str}\n\n![跨境早报]({img_url})\n\n[查看原图]({img_url})"
    else:
        text = f"## {title} · {date_str}\n\n今日早报已生成，图片上传失败。"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{title} {date_str}",
            "text": text
        }
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"[推送] 钉钉结果: {result}")
            return result.get("errcode") == 0
    except Exception as e:
        print(f"[推送] 钉钉异常: {e}")
        return False


# ============================================================
# 方案 D：飞书群机器人
# ============================================================
def push_feishu(image_path, webhook_url, title="跨境早报"):
    """
    通过飞书自定义机器人推送（interactive 图片消息）
    """
    print("[推送] 飞书群机器人...")

    img_url, _ = upload_to_image_host(image_path)
    date_str = os.popen("date '+%Y.%m.%d'").read().strip()

    if img_url:
        # 飞书 interactive 卡片支持图片
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"{title} {date_str}"},
                    "template": "blue"
                },
                "elements": [
                    {"tag": "img", "img_key": img_url, "alt": {"tag": "plain_text", "content": title}},
                    {"tag": "note", "elements": [{"tag": "plain_text", "content": "每日7:30自动推送"}]}
                ]
            }
        }
    else:
        payload = {
            "msg_type": "text",
            "content": {"text": f"{title} {date_str} - 今日早报已生成，图片上传失败"}
        }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"[推送] 飞书结果: {result}")
            return result.get("code") == 0 or result.get("StatusCode") == 0
    except Exception as e:
        print(f"[推送] 飞书异常: {e}")
        return False


# ============================================================
# 主推送入口
# ============================================================
def push(image_path, title="跨境早报"):
    """根据 .env 配置自动选择推送渠道"""
    def get_config(key):
        val = os.environ.get(key, "")
        if not val:
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and "=" in line and not line.startswith("#"):
                            k, v = line.split("=", 1)
                            if k.strip() == key:
                                return v.strip()
        return val

    success = False

    # 企业微信（推荐，直接推图片）
    wechat_key = get_config("WECHAT_WEBHOOK_KEY")
    if wechat_key:
        if push_wechat_work(image_path, wechat_key, title):
            success = True

    # Server酱
    sckey = get_config("SERVERCHAN_SCKEY")
    if sckey:
        if push_serverchan(image_path, sckey, title):
            success = True

    # 钉钉
    dingtalk_key = get_config("DINGTALK_WEBHOOK_KEY")
    if dingtalk_key:
        if push_dingtalk(image_path, dingtalk_key, title):
            success = True

    # 飞书
    feishu_url = get_config("FEISHU_WEBHOOK_URL")
    if feishu_url:
        if push_feishu(image_path, feishu_url, title):
            success = True

    if not success:
        print("[推送] 未配置推送渠道或全部失败")
        print(f"[推送] 图片路径: {image_path}")

    return success


if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cross_border_daily.png")
    push(image_path)
