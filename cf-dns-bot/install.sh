#!/bin/bash
# Cloudflare DNS Bot 一键安装脚本

set -e

echo "=========================================="
echo "   Cloudflare DNS Bot 一键安装"
echo "=========================================="
echo ""

# 获取用户输入
read -p "请输入 Telegram Bot Token: " BOT_TOKEN
read -p "请输入 Cloudflare API Token: " CF_TOKEN
read -p "请输入你的 Telegram ID: " USER_ID

echo ""
echo "[*] 安装依赖..."
apt update -qq
apt install -y python3 python3-venv python3-pip git curl -qq

echo "[*] 下载程序..."
rm -rf /opt/cf-dns-bot
git clone https://github.com/mango082888-bit/vps-tools.git /tmp/vps-tools
mv /tmp/vps-tools/cf-dns-bot /opt/cf-dns-bot
rm -rf /tmp/vps-tools

echo "[*] 创建虚拟环境..."
python3 -m venv /opt/cf-dns-bot/venv
/opt/cf-dns-bot/venv/bin/pip install -q python-telegram-bot==13.15 requests

echo "[*] 写入配置..."
cat > /opt/cf-dns-bot/.env << EOF
BOT_TOKEN=${BOT_TOKEN}
CF_API_TOKEN=${CF_TOKEN}
ALLOWED_USERS=${USER_ID}
EOF

echo "[*] 创建服务..."
cat > /etc/systemd/system/cf-dns-bot.service << EOF
[Unit]
Description=Cloudflare DNS Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/cf-dns-bot
EnvironmentFile=/opt/cf-dns-bot/.env
ExecStart=/opt/cf-dns-bot/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "[*] 启动服务..."
systemctl daemon-reload
systemctl enable cf-dns-bot
systemctl start cf-dns-bot

echo ""
echo "=========================================="
echo "   ✅ 安装完成！"
echo "=========================================="
echo ""
echo "Bot 已启动，发送 /help 查看命令"
echo ""
echo "管理命令："
echo "  systemctl status cf-dns-bot  # 查看状态"
echo "  systemctl restart cf-dns-bot # 重启"
echo "  systemctl stop cf-dns-bot    # 停止"
echo ""
