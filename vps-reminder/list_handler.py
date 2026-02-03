async def list_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    if not data["vps_list"]:
        await query.edit_message_text("📭 暂无VPS记录\n\n使用 /add 添加")
        return
    
    text = "📋 *VPS 列表*\n\n"
    for i, vps in enumerate(data["vps_list"]):
        days = get_days_left(vps["expire_date"])
        status = "🟢" if days > 7 else "🟡" if days > 3 else "🔴"
        text += f"{status} *{vps['name']}*\n"
        text += f"   商家: {vps['provider']}\n"
        text += f"   到期: {vps['expire_date']} ({days}天)\n"
        if vps.get('price'):
            text += f"   价格: {vps['price']}\n"
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("🔙 返回", callback_data="back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
