# Internship Tracker（每日自动扫描 + 写入 Google Sheet）

这套脚本每天自动检查 [SimplifyJobs/Summer2027-Internships](https://github.com/SimplifyJobs/Summer2027-Internships)，
按关键词筛选出匹配的岗位，去重后追加写入你的 Google Sheet。全程跑在 GitHub Actions 里，不需要你电脑开机。

**这套东西只负责“发现 + 记录”，不会帮你注册账号、过验证码或提交申请** —— 那几步始终需要你本人操作。

---

## 目录结构

把这几个文件放进一个新的 GitHub 仓库（结构必须保持一致，`.github/workflows/` 必须在仓库根目录下）：

```
your-repo/
├── fetch_internships.py
├── requirements.txt
└── .github/
    └── workflows/
        └── daily-scan.yml
```

---

## 配置步骤

### 1. 创建 Google Cloud 服务账号（Service Account）

1. 打开 [Google Cloud Console](https://console.cloud.google.com/)，新建一个项目（或用已有的）。
2. 左侧菜单找到 **APIs & Services → Library**，搜索 **Google Sheets API**，点击启用。
3. 左侧菜单 **APIs & Services → Credentials → Create Credentials → Service Account**，
   随便起个名字（比如 `internship-bot`），一路下一步创建完成。
4. 创建完成后点进这个服务账号，进入 **Keys** 标签页 → **Add Key → Create new key → JSON**，
   会下载一个 `.json` 文件，**这个文件后面要整个复制进 GitHub Secrets，先保存好**。
5. 记下服务账号的邮箱地址（形如 `internship-bot@你的项目.iam.gserviceaccount.com`），
   在服务账号详情页顶部能看到。

### 2. 把 Google Sheet 分享给这个服务账号

打开你的 Google Sheet →右上角 **共享（Share）** → 粘贴上一步的服务账号邮箱 → 权限选
**编辑者（Editor）** → 发送。这一步不做，脚本会因为没有写入权限而报错。

### 3. 在 GitHub 仓库里配置 Secrets

新建一个 GitHub 仓库，把上面三个文件放进去，然后：
**Settings → Secrets and variables → Actions → New repository secret**，依次添加：

| Secret 名称 | 值 |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | 把第 1 步下载的 `.json` 文件**全部内容**粘贴进来 |
| `SHEET_ID` | 你的表格 ID，即表格链接中 `/d/` 和 `/edit` 之间的那一串，例如 `1UiNZXJDNL-mZybGwLSwhMAtTCkgqrtkFp6w_zsdrlwI` |
| `SHEET_TAB`（可选） | 要写入的工作表（tab）名称，不填默认是 `Sheet1` |

### 4. 手动跑一次测试

去仓库的 **Actions** 标签页 → 左侧选择 **Daily Internship Scan** → 右侧 **Run workflow** 按钮手动触发一次，
跑完看看日志有没有报错，再去 Google Sheet 里确认有没有写入新行。

### 5. 确认没问题后，就交给每天的定时任务了

`daily-scan.yml` 里默认设置的是每天 UTC 13:00（约北京时间 21:00）自动跑一次，
想改时间就改这一行里的 cron 表达式（cron 时间永远是 UTC，不是你本地时区）：

```yaml
- cron: "0 13 * * *"
```

---

## 想调整筛选逻辑？

打开 `fetch_internships.py` 顶部的配置区：

- **`KEYWORDS`**：关键词列表，决定哪些岗位算匹配，按你的方向随便加减
  （比如想收窄到纯机器人方向，可以去掉 `"ai"` `"machine learning"` 这些太宽泛的词）。
- **`EXCLUDE_PHD_ONLY`**：默认 `True`，丢掉标题里只要 PhD 的岗位；`MS/PhD` 这类仍然会保留。改成 `False` 就不过滤。
- **`EXCLUDE_ROLE_KEYWORDS`**：标题里出现这些词就丢掉，默认排除嵌入式（`embedded`）。
- **`EXCLUDE_COOP`**：默认 `True`，丢掉 co-op / Intern/Co-op。改成 `False` 就不过滤。
- **`EXCLUDE_US_CITIZEN`**：默认 `True`，丢掉 README 里标了 🇺🇸（Requires U.S. Citizenship）的岗位。
- **`MAX_AGE_DAYS`**：只保留发布在多少天以内的岗位，默认 14 天，改成 `None` 就是不限制。
- **`SHEET_HEADERS`**：写入表格的列名，如果你的表格已经有自己的表头，把这行改成一致的顺序即可。
- **`REPO_README_URL`**：想换成扫描 `Summer2026-Internships`、`New-Grad-Positions` 等其他
  SimplifyJobs 仓库，把这个链接换成对应仓库的 raw README 地址即可，脚本逻辑不用改。

---

## 排查问题

- **Action 跑失败，提示 `Missing GOOGLE_SERVICE_ACCOUNT_JSON`**：Secret 没配对，检查名字拼写和是否粘贴了完整 JSON。
- **提示权限不足 / 403**：Google Sheet 没有分享给服务账号邮箱，回到第 2 步检查。
- **表格里一行没写进去，但日志显示 `Found N postings`**：可能是 `SHEET_TAB` 名字和你表格里实际的 tab 名对不上。
- **README 结构变了导致找不到分区（`Sections found` 是空的）**：SimplifyJobs 偶尔会调整标题文字或 emoji，
  去 [仓库页面](https://github.com/SimplifyJobs/Summer2027-Internships) 对照 `SECTION_HEADERS` 里的文字更新一下即可。
