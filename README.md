# 深大羽毛球场馆预约工具

> **中文** · [English](#english)

## 功能特性

- **到点自动开抢**：固定**在预约日前一天 12:30** 自动开抢，倒计时越接近越频繁（可跨多天等待）
- **指定场地**：可指定粤海/丽湖校区及具体羽毛球场地，不指定则随机
- **多场次连续预约**：一次可预约多个场次，优先同场次连续时间段
- **多运动类型**：羽毛球、足球、排球、网球、篮球、壁球、健身、乒乓球

## 环境要求

- Python 3.9+
- 依赖：`requests`（安装：`pip install requests`）

## 快速开始

1. **复制并填写配置**

   ```bash
   cp config.example.py config.py
   ```

   在 `config.py` 中填写姓名、学号以及预约参数（日期、时间、运动类型等）。

2. **获取 Cookie（手动粘贴）**

   本项目**不做自动登录**，需要手动提供 cookie：

   1. 用浏览器登录 [深大统一身份认证](https://authserver.szu.edu.cn/authserver/login)，并进入[场馆预约系统](https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do)
   2. 按 `F12` 打开开发者工具 → `Network` 面板
   3. 刷新页面，任选一个请求（如 `getTimeList.do`），复制其请求头中的整段 `Cookie`
   4. 打开项目根目录的 `cookie.txt`，把整段 Cookie 粘贴进去（覆盖原内容）并保存

   > ⚠️ **Cookie 当天有效，过了当天 0 点自动失效。** 请务必在**开抢当天（预约日前一天）0 点后**重新获取 Cookie 并启动脚本，等脚本倒计时到 12:30 自动开抢。提前数天启动，Cookie 跨天会失效。

3. **运行**

   ```bash
   python main.py
   ```

## 配置说明

| 配置项 | 说明 |
| --- | --- |
| `YOU_NAME` / `YOU_ID` | 姓名、学号 |
| `YYLX` | 预约类型：羽毛球/排球/网球/壁球/乒乓球=`1.0`，健身房/足球/篮球=`2.0` |
| `typeOfSport` | 运动类型编码：`001`羽毛球 `002`足球 `003`排球 `004`网球 `005`篮球 `006`壁球 `007`一楼重量型健身 `008`二楼有氧型健身 `013`乒乓球 |
| `appointment_day` | 预约日期，格式 `YYYY-MM-DD`，示例 `"2026-08-24"` |
| `appointment_time_start` | 预约开始时间，格式 `HH:MM`，示例 `"20:00"` |
| `cnt` | 预约场次数目（1 或 2；一个时间段只能约一场，单人最多约两场） |
| `campus` | 校区：`"1"`=粤海，`"2"`=丽湖 |
| `target_room` | 指定场地：粤海 `A3`-`A8`/`B3`-`B8`/`C3`-`C8`/`D3`-`D8`，丽湖 `至畅羽毛球1-10号场`/`至快羽毛球1-12号场`；留空则随机 |

> **开抢规则**：固定为**预约日前一天 12:30**。例如预约 `2026-08-24`，脚本会在 `2026-08-23 12:30` 自动开抢。由于 Cookie 当天有效，需在**开抢当天 0 点后**获取 Cookie 并启动脚本。

## 常见问题

- **提示 "Cookies 失效"**：cookie 会话约 30 分钟失效，且**当天 0 点后自动失效**。运行时脚本会通过响应自动刷新 `_WEU`，并**定期自动检测 cookie 是否失效——一旦失效立即提示**，此时把新 Cookie 粘贴进 `cookie.txt`，程序检测到后会自动继续，无需重启；跨天或彻底失效时同样提示更新。
- **提示 "未配置 Cookie"**：`cookie.txt` 不存在或为空，按上面第 2 步粘贴获取。
- **预约日期填错**：脚本会校验日期，过去日期会停止；已移除"仅限次日/后日"的限制，可预约更远日期。

---

# <span id="english"></span>SZU Badminton Booking

> [中文](#深大羽毛球场馆预约工具) · **English**

## Features

- **Auto-grab at opening time**: fixed at **12:30 the day before the booking date**, with countdown that becomes more frequent as the moment approaches (waits across days)
- **Specify court**: choose campus (Yuehai/Lihu) and exact badminton court, or random
- **Multiple courts**: book several courts in one run, preferring consecutive slots
- **Multiple sports**: badminton, football, volleyball, tennis, basketball, squash, fitness, table tennis

## Requirements

- Python 3.9+
- Dependency: `requests` (`pip install requests`)

## Quick Start

1. **Copy and fill the config**

   ```bash
   cp config.example.py config.py
   ```

   Fill in your name, student ID and booking params in `config.py`.

2. **Get Cookie (manual)**

   This project does **not** auto-login; you must provide a cookie manually:

   1. Log in to [SZU unified auth](https://authserver.szu.edu.cn/authserver/login) and open the [venue booking system](https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do)
   2. Press `F12` → `Network` tab
   3. Refresh, pick any request (e.g. `getTimeList.do`), copy the full `Cookie` header
   4. Open `cookie.txt` in the project root, paste the whole cookie (overwrite), and save

   > ⚠️ **The cookie is only valid for the day it is obtained and expires at midnight.** Get a fresh cookie and start the script **after 00:00 on the opening day** (the day before the booking date); it will wait until 12:30 to grab automatically. Starting days in advance will leave the cookie expired.

3. **Run**

   ```bash
   python main.py
   ```

## Config Reference

| Key | Description |
| --- | --- |
| `YOU_NAME` / `YOU_ID` | Your name / student ID |
| `YYLX` | Booking type: badminton/volleyball/tennis/squash/table-tennis=`1.0`, gym/football/basketball=`2.0` |
| `typeOfSport` | Sport code: `001` badminton, `002` football, `003` volleyball, `004` tennis, `005` basketball, `006` squash, `007` weight room, `008` aerobic room, `013` table tennis |
| `appointment_day` | Booking date, `YYYY-MM-DD`, e.g. `"2026-08-24"` |
| `appointment_time_start` | Start time, `HH:MM`, e.g. `"20:00"` |
| `cnt` | Number of courts to book (1 or 2; max 2 per person) |
| `campus` | Campus: `"1"`=Yuehai, `"2"`=Lihu |
| `target_room` | Specific court: Yuehai `A3`-`A8`/`B3`-`B8`/`C3`-`C8`/`D3`-`D8`, Lihu `至畅羽毛球1-10号场`/`至快羽毛球1-12号场`; empty = random |

> **Opening rule**: fixed at **12:30 the day before the booking date**. E.g. booking `2026-08-24` grabs automatically at `2026-08-23 12:30`. Since the cookie expires at midnight, get a fresh cookie and start the script **after 00:00 on the opening day**.

## Troubleshooting

- **"Cookies invalid"**: the session lasts ~30 min and **expires at midnight**. The script auto-refreshes `_WEU` from responses and **periodically re-checks the cookie during the wait — if it dies it prompts immediately**; paste a fresh cookie into `cookie.txt` and the script detects it and continues automatically (no restart needed).
- **"Please set Cookie"**: `cookie.txt` is missing or empty — paste a fresh cookie (step 2 above).
- **Wrong date**: past dates stop the script; the old "next-day only" limit has been removed, so booking farther ahead is allowed.

---

## 文件结构 / Project Layout

```
config.example.py  # 示例配置（提交） / example config (committed)
config.py          # 你的真实配置（gitignored）
cookie.txt         # 手动粘贴的 Cookie（gitignored，程序自动读取）
main.py            # 运行入口 / entry point
CStack_utils/      # 核心逻辑 / core logic
  └─ sportGet.py
static/            # 羽毛球场馆/时段缓存 / cached venues & time slots
```