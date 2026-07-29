# 跨境早报 · 每日自动推送

> 每天 7:30 自动生成外贸资讯图片，推送到你的微信/企业微信/钉钉/飞书，直接发朋友圈。

## 效果预览

每天早上 7:30，你会收到一张这样的图片（深蓝底 + 黄色高亮，8 条分类外贸资讯 + 实时汇率看板）：

- 宏观外贸 / 关税预警 / 汇率动态 / 海运物流
- 新能源出海 / 展会经济 / 政策新规 / 出口管制

## 数据来源（全部实时抓取）

| 数据 | 来源 | 方式 |
|---|---|---|
| 美元/人民币 汇率 | exchangerate-api.com | API 实时 |
| 欧元/人民币 汇率 | exchangerate-api.com | API 实时 |
| 日元/人民币 汇率 | exchangerate-api.com | API 实时 |
| 国际金价 | gold-api.com | API 实时 |
| 外贸资讯 | 海关总署/商务部/航运交易所等 | 内置最新数据 |

## 部署步骤（5 分钟搞定）

### 方案一：GitHub Actions（推荐，完全免费、免服务器）

#### 第 1 步：把代码推到 GitHub

```bash
# 1. 在 GitHub 上新建一个仓库（比如叫 cross-border-news）
# 2. 把本目录所有文件推上去
cd cross-border-news
git init
git add .
git commit -m "跨境早报初始化"
git branch -M main
git remote add origin https://github.com/你的用户名/cross-border-news.git
git push -u origin main
```

#### 第 2 步：配置推送密钥

在 GitHub 仓库页面：
1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 根据你要用的推送渠道，添加对应的 Secret：

| Secret 名称 | 值 | 获取方式 |
|---|---|---|
| `WECHAT_WEBHOOK_KEY` | 企业微信机器人 Key | 企业微信群→添加群机器人→复制Webhook里的key |
| `SERVERCHAN_SCKEY` | Server酱 SCT开头Key | https://sct.ftqq.com 登录获取 |
| `DINGTALK_WEBHOOK_KEY` | 钉钉机器人Token | 钉钉群→设置→群机器人→自定义 |
| `FEISHU_WEBHOOK_URL` | 飞书机器人Webhook | 飞书群→设置→群机器人→自定义 |

> **至少配置一个即可**。推荐用企业微信群机器人（支持直接推图片，最稳定）。

#### 第 3 步：手动测试一次

在 GitHub 仓库页面：
1. 进入 `Actions` 标签页
2. 选择 `跨境早报每日推送` workflow
3. 点击 `Run workflow` → `Run workflow`
4. 等待 1-2 分钟，检查你的微信是否收到图片

#### 第 4 步：确认定时任务生效

GitHub Actions 的 cron 每天北京时间 7:30 自动触发。
> 注意：GitHub 的 cron 可能有 5-15 分钟延迟，实际收到时间约 7:30-7:45。

#### 第 5 步：发朋友圈

收到图片后，长按保存到手机相册，直接发朋友圈即可。

---

### 方案二：本地电脑定时任务（不想用 GitHub）

#### Windows

1. 安装 Python 3.11+ 和 Pillow：`pip install pillow`
2. 安装中文字体（一般 Windows 自带微软雅黑）
3. 打开「任务计划程序」→ 创建基本任务
4. 触发器：每天 7:30
5. 操作：启动程序
   - 程序：`python`
   - 参数：`generate.py`
   - 起始于：`C:\path\to\cross-border-news`
6. 复制 `.env.example` 为 `.env`，填入推送密钥

#### Mac/Linux

```bash
crontab -e
# 添加以下行（每天 7:30 执行）：
30 7 * * * cd /path/to/cross-border-news && python3 generate.py && python3 push.py
```

---

## 文件说明

```
cross-border-news/
├── generate.py              # 图片生成器（主入口）
├── data_fetcher.py          # 实时数据抓取模块
├── push.py                  # 推送模块（4种渠道）
├── .env.example             # 推送配置模板
├── .env                     # 你的密钥配置（需自行创建，不要上传）
├── .github/workflows/
│   └── daily.yml            # GitHub Actions 定时任务
├── cross_border_daily.png   # 生成的图片（自动覆盖）
└── README.md                # 本文档
```

## 常见问题

### Q: GitHub Actions 的 cron 准时吗？
A: 不完全准时，可能有 5-15 分钟延迟。如果要求精准 7:30，建议用本地 crontab。

### Q: 资讯内容每天会自动更新吗？
A: 汇率和金价是实时抓取的。8 条资讯内容目前是内置的最近热点。如需每天自动抓取最新资讯，需要接入搜索 API（如 SerpAPI）或大模型 API 生成摘要，可在 `data_fetcher.py` 中扩展。

### Q: 推送到个人微信用什么？
A: Server酱（https://sct.ftqq.com），免费版每天可推 5 条。

### Q: 企业微信机器人一定要企业微信吗？
A: 是的。如果你没有企业微信，用 Server酱 推个人微信最方便。

### Q: 图片字体显示乱码？
A: 确保系统安装了中文字体。GitHub Actions 配置已自动安装，本地需手动装 `fonts-wqy-zenhei`。

## License

MIT
