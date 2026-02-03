#!/bin/bash
# 安装脚本

mkdir -p /root/.openclaw/workspace/rfc-monitor
chmod +x /root/.openclaw/workspace/rfc-monitor/monitor.sh

# 创建 systemd 服务
cat > /etc/systemd/system/rfc-monitor.service << 'EOF'
[Unit]
Description=RFCHost Stock Monitor
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash /root/.openclaw/workspace/rfc-monitor/monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rfc-monitor
systemctl start rfc-monitor

echo "✅ 安装完成！"
echo "查看状态: systemctl status rfc-monitor"
echo "查看日志: tail -f /root/.openclaw/workspace/rfc-monitor/monitor.log"
