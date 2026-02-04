#!/usr/bin/env python3
"""Cloudflare DNS 管理 Telegram Bot"""

import os
import logging
import requests
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "YOUR_CF_TOKEN")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "0").split(",")]

updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(level=logging.INFO)

ZONE_CACHE = {}

def get_zone_id(domain):
    root = ".".join(domain.split(".")[-2:])
    if root in ZONE_CACHE:
        return ZONE_CACHE[root]
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    zones = requests.get("https://api.cloudflare.com/client/v4/zones", headers=headers).json()
    for z in zones.get("result", []):
        if z["name"] == root:
            ZONE_CACHE[root] = z["id"]
            return z["id"]
    return None

def is_authorized(uid):
    return uid in ALLOWED_USERS

def help_cmd(update, context):
    if not is_authorized(update.effective_user.id):
        return
    msg = """🛠️ *Cloudflare DNS 控制机器人*

`/add domain sub ip` - 添加 A 记录
`/del domain sub` - 删除记录
`/proxy on|off domain sub` - 设置小黄云
`/list domain` - 列出记录
`/help` - 显示帮助"""
    update.message.reply_text(msg, parse_mode="Markdown")

def start_cmd(update, context):
    help_cmd(update, context)

def list_cmd(update, context):
    if not is_authorized(update.effective_user.id):
        return
    if len(context.args) != 1:
        return update.message.reply_text("用法: /list domain.com")
    domain = context.args[0]
    zid = get_zone_id(domain)
    if not zid:
        return update.message.reply_text("❌ 无法获取 Zone ID")
    url = f"https://api.cloudflare.com/client/v4/zones/{zid}/dns_records"
    r = requests.get(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}).json()
    msg = f"📄 *{domain} 记录：*\n\n"
    for i in r.get("result", []):
        status = "🟡代理" if i["proxied"] else "⚪直连"
        msg += f"• `{i['name']}` → {i['content']} [{i['type']}] {status}\n"
    update.message.reply_text(msg, parse_mode="Markdown")

def add_cmd(update, context):
    if not is_authorized(update.effective_user.id):
        return
    if len(context.args) != 3:
        return update.message.reply_text("用法: /add domain sub ip")
    domain, sub, ip = context.args
    zid = get_zone_id(domain)
    if not zid:
        return update.message.reply_text("❌ 无法获取 Zone ID")
    full = f"{sub}.{domain}"
    payload = {"type": "A", "name": full, "content": ip, "ttl": 1, "proxied": False}
    url = f"https://api.cloudflare.com/client/v4/zones/{zid}/dns_records"
    r = requests.post(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}, json=payload).json()
    update.message.reply_text(f"✅ 添加成功：{full}" if r.get("success") else "❌ 添加失败")

def del_cmd(update, context):
    if not is_authorized(update.effective_user.id):
        return
    if len(context.args) != 2:
        return update.message.reply_text("用法: /del domain sub")
    domain, sub = context.args
    zid = get_zone_id(domain)
    full = f"{sub}.{domain}"
    url = f"https://api.cloudflare.com/client/v4/zones/{zid}/dns_records"
    records = requests.get(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}).json().get("result", [])
    for r in records:
        if r["name"] == full:
            del_url = f"{url}/{r['id']}"
            d = requests.delete(del_url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}).json()
            return update.message.reply_text("✅ 删除成功" if d.get("success") else "❌ 删除失败")
    update.message.reply_text("❌ 未找到该记录")

def proxy_cmd(update, context):
    if not is_authorized(update.effective_user.id):
        return
    if len(context.args) != 3:
        return update.message.reply_text("用法: /proxy on|off domain sub")
    action, domain, sub = context.args
    zid = get_zone_id(domain)
    full = f"{sub}.{domain}"
    url = f"https://api.cloudflare.com/client/v4/zones/{zid}/dns_records"
    records = requests.get(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}).json().get("result", [])
    for r in records:
        if r["name"] == full:
            r["proxied"] = (action == "on")
            put_url = f"{url}/{r['id']}"
            u = requests.put(put_url, headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}, json=r).json()
            return update.message.reply_text("✅ 设置成功" if u.get("success") else "❌ 设置失败")
    update.message.reply_text("❌ 未找到该记录")

# 注册命令
dispatcher.add_handler(CommandHandler("start", start_cmd))
dispatcher.add_handler(CommandHandler("help", help_cmd))
dispatcher.add_handler(CommandHandler("list", list_cmd))
dispatcher.add_handler(CommandHandler("add", add_cmd))
dispatcher.add_handler(CommandHandler("del", del_cmd))
dispatcher.add_handler(CommandHandler("proxy", proxy_cmd))

if __name__ == "__main__":
    print("Bot started!")
    updater.start_polling()
    updater.idle()
