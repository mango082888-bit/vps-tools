#!/bin/bash
# VPS 到期提醒 Bot 安装脚本

echo "📦 安装依赖..."
pip3 install python-telegram-bot -q

echo "🔧 创建 systemd 服务..."
cat > /etc/systemd/system/vps-reminder.service << 'EOF'
[Unit]
Description=VPS Reminder Bot
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/vps-reminder/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vps-reminder
systemctl start vps-reminder

echo "✅ 安装完成！"
echo "状态: systemctl status vps-reminder"
