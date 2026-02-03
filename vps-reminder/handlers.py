
async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    
    if not data["vps"]:
        await query.edit_message_text("📭 暂无VPS，点 /start 添加")
        return
    
    text = "📋 *VPS列表*\n\n"
    for v in data["vps"]:
        d = days_left(v["date"])
        s = "🟢" if d > 7 else "🟡" if d > 3 else "🔴"
        text += f"{s} *{v['name']}* ({v['provider']})\n"
        text += f"   到期: {v['date']} ({d}天)\n"
        if v.get('price'): text += f"   价格: {v['price']}\n"
        text += "\n"
    await query.edit_message_text(text, parse_mode="Markdown")

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("请输入VPS名称：")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("请输入商家名称：")
    return ADD_PROVIDER

async def add_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['provider'] = update.message.text
    await update.message.reply_text("请输入到期日期 (格式: 2026-12-31)：")
    return ADD_DATE

async def add_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("请输入价格 (可选，输入 - 跳过)：")
    return ADD_PRICE

async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = update.message.text
    if price == "-": price = ""
    data = load_data()
    data["vps"].append({
        "name": context.user_data['name'],
        "provider": context.user_data['provider'],
        "date": context.user_data['date'],
        "price": price
    })
    save_data(data)
    await update.message.reply_text("✅ 添加成功！/start 返回")
    return ConversationHandler.END
