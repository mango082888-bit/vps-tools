# VPS Tools

VPS 管理工具集，包含续费提醒和补货监控功能。

## 项目结构

```
├── vps-reminder/    # VPS 续费提醒 Bot
└── rfc-monitor/     # 库存监控脚本
```

## vps-reminder

Telegram Bot，用于管理 VPS 续费提醒和补货监控。

### 功能
- 📋 VPS 列表管理
- ⏰ 到期提醒（7天、3天、1天）
- 🔍 补货监控
- 📡 Ping 检测

### 安装

```bash
cd vps-reminder
pip install python-telegram-bot aiohttp
export BOT_TOKEN="your_bot_token"
export ADMIN_ID="your_telegram_id"
python bot.py
```

## rfc-monitor

简单的库存监控脚本，检测到有货时发送 Telegram 通知。

### 使用

```bash
cd rfc-monitor
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
./monitor.sh
```

## 环境变量

| 变量 | 说明 |
|------|------|
| BOT_TOKEN | Telegram Bot Token |
| ADMIN_ID | 管理员 Telegram ID |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token (monitor.sh) |
| TELEGRAM_CHAT_ID | 通知接收者 ID |

## License

MIT
