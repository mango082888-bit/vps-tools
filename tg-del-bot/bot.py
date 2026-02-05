#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 消息删除 Bot
命令：
  /del today - 删除今天的消息
  /del yesterday - 删除昨天的消息
  /del 14:00-16:00 - 删除指定时间段的消息
  /del 1h - 删除最近1小时的消息
  /del 30m - 删除最近30分钟的消息
"""

import os
import re
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 配置
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_IDS = [int(x) for x in os.environ.get('ADMIN_IDS', '').split(',') if x]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 存储消息记录 {chat_id: [(msg_id, timestamp), ...]}
message_store = {}

async def record_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """记录所有消息"""
    if not update.message:
        return
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    timestamp = update.message.date
    
    if chat_id not in message_store:
        message_store[chat_id] = []
    message_store[chat_id].append((msg_id, timestamp))
    
    # 只保留最近7天的记录
    cutoff = datetime.now(timestamp.tzinfo) - timedelta(days=7)
    message_store[chat_id] = [(m, t) for m, t in message_store[chat_id] if t > cutoff]

def parse_time_range(arg, now):
    """解析时间参数"""
    tz = now.tzinfo
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if arg == 'today':
        return today_start, now
    elif arg == 'yesterday':
        yesterday_start = today_start - timedelta(days=1)
        return yesterday_start, today_start
    elif re.match(r'^\d+h$', arg):
        hours = int(arg[:-1])
        return now - timedelta(hours=hours), now
    elif re.match(r'^\d+m$', arg):
        minutes = int(arg[:-1])
        return now - timedelta(minutes=minutes), now
    elif re.match(r'^\d{1,2}:\d{2}-\d{1,2}:\d{2}$', arg):
        start_str, end_str = arg.split('-')
        sh, sm = map(int, start_str.split(':'))
        eh, em = map(int, end_str.split(':'))
        start = today_start.replace(hour=sh, minute=sm)
        end = today_start.replace(hour=eh, minute=em)
        return start, end
    return None, None

async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """删除消息命令"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ 无权限")
        return
    
    if not context.args:
        await update.message.reply_text(
            "用法:\n"
            "/del today - 删除今天的消息\n"
            "/del yesterday - 删除昨天的消息\n"
            "/del 1h - 删除最近1小时\n"
            "/del 30m - 删除最近30分钟\n"
            "/del 14:00-16:00 - 删除时间段"
        )
        return
    
    arg = context.args[0].lower()
    chat_id = update.effective_chat.id
    now = datetime.now(update.message.date.tzinfo)
    
    start_time, end_time = parse_time_range(arg, now)
    if not start_time:
        await update.message.reply_text("❌ 无效的时间格式")
        return
    
    # 获取要删除的消息
    messages = message_store.get(chat_id, [])
    to_delete = [m for m, t in messages if start_time <= t <= end_time]
    
    if not to_delete:
        await update.message.reply_text("📭 没有找到该时间段的消息")
        return
    
    # 删除消息
    deleted = 0
    for msg_id in to_delete:
        try:
            await context.bot.delete_message(chat_id, msg_id)
            deleted += 1
        except Exception as e:
            logger.warning(f"删除失败 {msg_id}: {e}")
    
    # 更新存储
    message_store[chat_id] = [(m, t) for m, t in messages if m not in to_delete]
    
    await update.message.reply_text(f"✅ 已删除 {deleted} 条消息")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动命令"""
    await update.message.reply_text(
        "🗑️ 消息删除 Bot\n\n"
        "命令:\n"
        "/del today - 删除今天的消息\n"
        "/del yesterday - 删除昨天的消息\n"
        "/del 1h - 删除最近1小时\n"
        "/del 30m - 删除最近30分钟\n"
        "/del 14:00-16:00 - 删除时间段"
    )

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN 未设置")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # 记录所有消息
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.ALL, record_message), group=-1)
    
    # 命令
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("del", del_command))
    
    logger.info("Bot 启动...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
