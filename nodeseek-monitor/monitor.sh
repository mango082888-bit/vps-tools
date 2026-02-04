#!/bin/bash
# RFCHost 库存监控脚本

# 配置 - 请修改为你自己的值
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-YOUR_BOT_TOKEN}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-YOUR_CHAT_ID}"
LOG_FILE="${LOG_FILE:-./monitor.log}"

# 监控产品配置
PRODUCT1_NAME="JP2-T1ION-Balance"
PRODUCT1_URL="https://my.rfchost.com/cart.php?a=add&pid=78"
PRODUCT1_PRICE="\$29.90/年"

PRODUCT2_NAME="JP2-CO-Micro-Lite"
PRODUCT2_URL="https://my.rfchost.com/cart.php?a=add&pid=80"
PRODUCT2_PRICE="\$7.49"
PRODUCT2_COUPON="我是高手我不需要发工单"

send_telegram() {
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="$1" \
        -d parse_mode="HTML" > /dev/null
}

check_stock() {
    local url="$1"
    local response=$(curl -s -L --max-time 15 "$url" 2>/dev/null)
    
    if [ -z "$response" ]; then
        return 1
    fi
    
    if echo "$response" | grep -qi "out of stock"; then
        return 1
    fi
    
    if echo "$response" | grep -qi "configure\|order\|checkout"; then
        return 0
    fi
    
    return 1
}

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "监控启动"

while true; do
    if check_stock "$PRODUCT1_URL"; then
        log "$PRODUCT1_NAME 有货！"
        send_telegram "🎉 $PRODUCT1_NAME 有货！
💰 $PRODUCT1_PRICE
🔗 $PRODUCT1_URL"
        sleep 300
    else
        log "$PRODUCT1_NAME 无货"
    fi

    if check_stock "$PRODUCT2_URL"; then
        log "$PRODUCT2_NAME 有货！"
        send_telegram "🎉 $PRODUCT2_NAME 有货！
💰 $PRODUCT2_PRICE
🎫 优惠码: $PRODUCT2_COUPON
🔗 $PRODUCT2_URL"
        sleep 300
    else
        log "$PRODUCT2_NAME 无货"
    fi

    sleep 60
done
