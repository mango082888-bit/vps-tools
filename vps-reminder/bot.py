#!/usr/bin/env python3
"""VPS 管理 + 补货监控 Telegram Bot"""

import json, os, aiohttp, subprocess
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATA_FILE = os.getenv("DATA_FILE", "./data.json")

ADD_NAME, ADD_PROVIDER, ADD_IP, ADD_DATE, ADD_PRICE = range(5)
MON_NAME, MON_URL, MON_KEYWORD = 10, 11, 12

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return {"vps": [], "remind_days": [7, 3, 1], "monitors": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def days_left(d):
    return (datetime.strptime(d, "%Y-%m-%d") - datetime.now()).days

def ping_host(ip):
    try:
        return subprocess.run(["ping", "-c", "1", "-W", "3", ip], 
            capture_output=True, timeout=5).returncode == 0
    except:
        return False

async def check_url(url, keyword):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"User-Agent": "Mozilla/5.0"}, 
                timeout=aiohttp.ClientTimeout(total=10)) as r:
                return keyword.lower() in (await r.text()).lower()
    except:
        return None

# 主菜单
async def start(update: Update, ctx):
    if update.effective_user.id != ADMIN_ID: return
    kb = [[InlineKeyboardButton("📋 VPS列表", callback_data="list")],
          [InlineKeyboardButton("🔍 补货监控", callback_data="monitors")],
          [InlineKeyboardButton("⚙️ 设置", callback_data="settings")]]
    await update.message.reply_text("🖥️ *管理面板*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def help_cmd(update: Update, ctx):
    if update.effective_user.id != ADMIN_ID: return
    text = """📖 *命令列表*

*VPS管理*
/start - 主菜单
/list - VPS列表
/add - 添加VPS
/ping - Ping检测

*补货监控*
/monitors - 监控列表
/addmon - 添加监控
/check - 立即检测"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def back_main(u, c):
    await u.callback_query.answer()
    kb = [[InlineKeyboardButton("📋 VPS列表", callback_data="list")],
          [InlineKeyboardButton("🔍 补货监控", callback_data="monitors")],
          [InlineKeyboardButton("⚙️ 设置", callback_data="settings")]]
    await u.callback_query.edit_message_text("🖥️ *管理面板*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# 设置菜单
async def settings_menu(u, c):
    await u.callback_query.answer()
    data = load_data()
    days = data.get("remind_days", [7, 3, 1])
    msg = f"⚙️ *设置*\n\n📅 提醒天数: {', '.join(map(str, sorted(days, reverse=True)))}天"
    kb = [[InlineKeyboardButton("📅 修改提醒天数", callback_data="set_days")],
          [InlineKeyboardButton("« 返回", callback_data="back_main")]]
    await u.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# 设置提醒天数
async def set_days_menu(u, c):
    await u.callback_query.answer()
    data = load_data()
    days = data.get("remind_days", [7, 3, 1])
    msg = f"📅 *提醒天数设置*\n\n当前: {', '.join(map(str, sorted(days, reverse=True)))}天\n\n点击切换开关:"
    kb = []
    for d in [30, 14, 7, 3, 1]:
        status = "✅" if d in days else "⬜"
        kb.append([InlineKeyboardButton(f"{status} {d}天", callback_data=f"toggle_day_{d}")])
    kb.append([InlineKeyboardButton("« 返回", callback_data="settings")])
    await u.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# 切换提醒天数
async def toggle_day(u, c):
    await u.callback_query.answer()
    day = int(u.callback_query.data.split("_")[2])
    data = load_data()
    days = data.get("remind_days", [7, 3, 1])
    if day in days:
        days.remove(day)
    else:
        days.append(day)
    data["remind_days"] = sorted(days, reverse=True)
    save_data(data)
    # 刷新菜单
    msg = f"📅 *提醒天数设置*\n\n当前: {', '.join(map(str, data['remind_days']))}天\n\n点击切换开关:"
    kb = []
    for d in [30, 14, 7, 3, 1]:
        status = "✅" if d in data["remind_days"] else "⬜"
        kb.append([InlineKeyboardButton(f"{status} {d}天", callback_data=f"toggle_day_{d}")])
    kb.append([InlineKeyboardButton("« 返回", callback_data="settings")])
    await u.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# VPS列表
async def show_list(u, c):
    q = u.callback_query
    if q: await q.answer()
    data = load_data()
    if not data["vps"]:
        msg = "📭 暂无VPS"
    else:
        msg = "📋 *VPS列表*\n\n"
        for i, v in enumerate(data["vps"]):
            d = days_left(v['date'])
            s = "🟢" if d > 7 else "🟡" if d > 3 else "🔴"
            msg += f"{i+1}. {s} *{v['name']}*\n"
            msg += f"   {v['provider']} | {d}天\n"
    kb = [[InlineKeyboardButton("➕ 添加", callback_data="add"),
           InlineKeyboardButton("🔄 Ping", callback_data="ping_all")],
          [InlineKeyboardButton("🗑️ 删除", callback_data="vps_del"),
           InlineKeyboardButton("« 返回", callback_data="back_main")]]
    if q:
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else:
        await u.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# VPS添加
async def add_start(u, c):
    q = u.callback_query
    if q: await q.answer(); await q.edit_message_text("请输入VPS名称：")
    else: await u.message.reply_text("请输入VPS名称：")
    return ADD_NAME

async def add_name(u, c):
    c.user_data['name'] = u.message.text
    await u.message.reply_text("商家名称：")
    return ADD_PROVIDER

async def add_provider(u, c):
    c.user_data['provider'] = u.message.text
    await u.message.reply_text("IP地址 (- 跳过)：")
    return ADD_IP

async def add_ip(u, c):
    c.user_data['ip'] = "" if u.message.text == "-" else u.message.text
    await u.message.reply_text("到期日期 (2026-12-31)：")
    return ADD_DATE

async def add_date(u, c):
    c.user_data['date'] = u.message.text
    await u.message.reply_text("价格 (- 跳过)：")
    return ADD_PRICE

async def add_price(u, c):
    data = load_data()
    data["vps"].append({
        "name": c.user_data['name'],
        "provider": c.user_data['provider'],
        "ip": c.user_data.get('ip', ''),
        "date": c.user_data['date'],
        "price": "" if u.message.text == "-" else u.message.text
    })
    save_data(data)
    await u.message.reply_text("✅ 已添加")
    return ConversationHandler.END

# VPS删除
async def vps_del_start(u, c):
    await u.callback_query.answer()
    data = load_data()
    if not data["vps"]:
        await u.callback_query.edit_message_text("📭 暂无VPS")
        return
    kb = [[InlineKeyboardButton(v['name'], callback_data=f"vdel_{i}")] 
          for i, v in enumerate(data["vps"])]
    kb.append([InlineKeyboardButton("« 返回", callback_data="list")])
    await u.callback_query.edit_message_text("选择删除：", reply_markup=InlineKeyboardMarkup(kb))

async def vps_del_confirm(u, c):
    await u.callback_query.answer()
    data = load_data()
    idx = int(u.callback_query.data.split("_")[1])
    name = data["vps"][idx]["name"]
    del data["vps"][idx]
    save_data(data)
    await u.callback_query.edit_message_text(f"✅ 已删除 {name}")

# Ping检测
async def ping_all(u, c):
    q = u.callback_query
    if q:
        await q.answer()
        msg = await q.edit_message_text("🔄 检测中...")
    else:
        msg = await u.message.reply_text("🔄 检测中...")
    data = load_data()
    results = []
    for v in data["vps"]:
        ip = v.get("ip", "")
        if ip:
            online = ping_host(ip)
            s = "🟢" if online else "🔴"
        else:
            s = "⚪"
        results.append(f"{v['name']}: {s}")
    await msg.edit_text("📡 *Ping结果*\n" + "\n".join(results), parse_mode="Markdown")

# 补货监控菜单
async def monitors_menu(u, c):
    q = u.callback_query
    if q: await q.answer()
    data = load_data()
    mons = data.get("monitors", [])
    if not mons:
        msg = "🔍 *补货监控*\n\n📭 暂无"
    else:
        msg = "🔍 *补货监控*\n\n"
        for i, m in enumerate(mons):
            s = "🟢" if m.get('in_stock') else "🔴"
            msg += f"{i+1}. {s} {m['name']}\n"
    kb = [[InlineKeyboardButton("➕ 添加", callback_data="mon_add"),
           InlineKeyboardButton("🔄 检测", callback_data="mon_check")],
          [InlineKeyboardButton("🗑️ 删除", callback_data="mon_del"),
           InlineKeyboardButton("« 返回", callback_data="back_main")]]
    if q:
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else:
        await u.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# 添加监控
async def mon_add_start(u, c):
    q = u.callback_query
    if q: await q.answer(); await q.edit_message_text("监控名称：")
    else: await u.message.reply_text("监控名称：")
    return MON_NAME

async def mon_name(u, c):
    c.user_data['mon_name'] = u.message.text
    await u.message.reply_text("监控URL：")
    return MON_URL

async def mon_url(u, c):
    c.user_data['mon_url'] = u.message.text
    await u.message.reply_text("有货关键词：")
    return MON_KEYWORD

async def mon_keyword(u, c):
    data = load_data()
    if "monitors" not in data:
        data["monitors"] = []
    data["monitors"].append({
        "name": c.user_data['mon_name'],
        "url": c.user_data['mon_url'],
        "keyword": u.message.text,
        "in_stock": False
    })
    save_data(data)
    await u.message.reply_text("✅ 已添加")
    return ConversationHandler.END

# 删除监控
async def mon_del_start(u, c):
    await u.callback_query.answer()
    data = load_data()
    mons = data.get("monitors", [])
    if not mons:
        await u.callback_query.edit_message_text("📭 暂无")
        return
    kb = [[InlineKeyboardButton(m['name'], callback_data=f"mdel_{i}")] 
          for i, m in enumerate(mons)]
    kb.append([InlineKeyboardButton("« 返回", callback_data="monitors")])
    await u.callback_query.edit_message_text("选择删除：", reply_markup=InlineKeyboardMarkup(kb))

async def mon_del_confirm(u, c):
    await u.callback_query.answer()
    data = load_data()
    idx = int(u.callback_query.data.split("_")[1])
    del data["monitors"][idx]
    save_data(data)
    await u.callback_query.edit_message_text("✅ 已删除")

# 检测补货
async def mon_check(u, c):
    q = u.callback_query
    if q:
        await q.answer()
        msg = await q.edit_message_text("🔄 检测中...")
    else:
        msg = await u.message.reply_text("🔄 检测中...")
    data = load_data()
    mons = data.get("monitors", [])
    if not mons:
        await msg.edit_text("📭 暂无监控")
        return
    results = []
    for m in mons:
        r = await check_url(m['url'], m['keyword'])
        if r is None:
            results.append(f"⚠️ {m['name']}: 检测失败")
        elif r:
            m['in_stock'] = True
            results.append(f"🟢 {m['name']}: 有货")
        else:
            m['in_stock'] = False
            results.append(f"🔴 {m['name']}: 无货")
    save_data(data)
    await msg.edit_text("🔍 *检测结果*\n\n" + "\n".join(results), parse_mode="Markdown")

# 定时任务
async def check_expire(ctx):
    data = load_data()
    for v in data["vps"]:
        d = days_left(v["date"])
        if d in data["remind_days"]:
            await ctx.bot.send_message(ADMIN_ID, 
                f"⏰ VPS到期提醒: {v['name']} 还有{d}天")

async def check_monitors_job(ctx):
    data = load_data()
    for m in data.get("monitors", []):
        was = m.get("in_stock", False)
        r = await check_url(m['url'], m['keyword'])
        if r and not was:
            m['in_stock'] = True
            await ctx.bot.send_message(ADMIN_ID, 
                f"🎉 补货通知: {m['name']}\n{m['url']}")
        elif r is not None:
            m['in_stock'] = r
    save_data(data)

async def cancel(u, c):
    await u.message.reply_text("已取消")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # VPS添加会话
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_start, pattern="^add$"),
                      CommandHandler("add", add_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_PROVIDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_provider)],
            ADD_IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ip)],
            ADD_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_date)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # 监控添加会话
    mon_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(mon_add_start, pattern="^mon_add$"),
                      CommandHandler("addmon", mon_add_start)],
        states={
            MON_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, mon_name)],
            MON_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, mon_url)],
            MON_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, mon_keyword)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # 命令处理
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", show_list))
    app.add_handler(CommandHandler("ping", ping_all))
    app.add_handler(CommandHandler("monitors", monitors_menu))
    app.add_handler(CommandHandler("check", mon_check))
    
    app.add_handler(add_conv)
    app.add_handler(mon_conv)
    
    # 按钮回调
    app.add_handler(CallbackQueryHandler(show_list, pattern="^list$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(vps_del_start, pattern="^vps_del$"))
    app.add_handler(CallbackQueryHandler(vps_del_confirm, pattern="^vdel_"))
    app.add_handler(CallbackQueryHandler(ping_all, pattern="^ping_all$"))
    app.add_handler(CallbackQueryHandler(monitors_menu, pattern="^monitors$"))
    app.add_handler(CallbackQueryHandler(mon_del_start, pattern="^mon_del$"))
    app.add_handler(CallbackQueryHandler(mon_del_confirm, pattern="^mdel_"))
    app.add_handler(CallbackQueryHandler(mon_check, pattern="^mon_check$"))
    app.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(set_days_menu, pattern="^set_days$"))
    app.add_handler(CallbackQueryHandler(toggle_day, pattern="^toggle_day_"))
    
    # 定时任务
    app.job_queue.run_daily(check_expire, time=time(9, 0))
    app.job_queue.run_repeating(check_monitors_job, interval=300, first=60)
    
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
