#!/bin/bash
# Telegram 消息删除 Bot 一键安装脚本

set -e

echo "🗑️ Telegram 消息删除 Bot 安装"
echo "================================"

# 检查参数
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "用法: $0 <BOT_TOKEN> <ADMIN_ID>"
    echo "示例: $0 123456:ABC your_telegram_id"
    exit 1
fi

BOT_TOKEN=$1
ADMIN_ID=$2

# 安装目录
INSTALL_DIR="/opt/tg-del-bot"

# 安装依赖
echo "📦 安装依赖..."
apt update -qq
apt install -y python3-venv python3-pip -qq

# 创建目录
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# 下载脚本
echo "📥 下载脚本..."
curl -sL https://raw.githubusercontent.com/mango082888-bit/vps-tools/main/tg-del-bot/bot.py -o bot.py

# 创建虚拟环境
echo "🐍 创建虚拟环境..."
python3 -m venv venv
./venv/bin/pip install python-telegram-bot -q

# 创建服务
echo "⚙️ 创建服务..."
cat > /etc/systemd/system/tg-del-bot.service << EOF
[Unit]
Description=Telegram Delete Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
Environment=BOT_TOKEN=$BOT_TOKEN
Environment=ADMIN_IDS=$ADMIN_ID
ExecStart=$INSTALL_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable tg-del-bot
systemctl start tg-del-bot

echo ""
echo "✅ 安装完成！"
echo "Bot 已启动，把它拉进群并设为管理员"
echo ""
echo "命令:"
echo "  /del today - 删除今天的消息"
echo "  /del 1h - 删除最近1小时"
echo "  /del 14:00-16:00 - 删除时间段"
