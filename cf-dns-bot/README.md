# Cloudflare DNS Bot

Telegram Bot 管理 Cloudflare DNS 记录。

## 一键安装

```bash
bash <(curl -sL https://raw.githubusercontent.com/mango082888-bit/vps-tools/main/cf-dns-bot/install.sh)
```

## 功能

- `/add domain sub ip` - 添加 A 记录
- `/del domain sub` - 删除记录
- `/proxy on|off domain sub` - 开关小黄云
- `/list domain` - 列出记录
- `/help` - 显示帮助

## 管理

```bash
systemctl status cf-dns-bot   # 状态
systemctl restart cf-dns-bot  # 重启
systemctl stop cf-dns-bot     # 停止
```
