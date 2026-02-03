
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    if not data["vps"]:
        await query.edit_message_text("📭 暂无VPS")
        return
    kb = [[InlineKeyboardButton(v['name'], callback_data=f"del_{i}")] 
          for i, v in enumerate(data["vps"])]
    await query.edit_message_text("选择要删除的VPS：", 
        reply_markup=InlineKeyboardMarkup(kb))

async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    data = load_data()
    name = data["vps"][idx]["name"]
    del data["vps"][idx]
    save_data(data)
    await query.edit_message_text(f"✅ 已删除 {name}")
