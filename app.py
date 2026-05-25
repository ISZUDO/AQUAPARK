import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8333512746:AAG9kBpDW0disV1SookpPkXQX8nRYmIjAPw"
ADMIN_ID = 123456789  # O'z Telegram ID ingizni qo'ying

# ===================== NARXLAR =====================
PRICES = {
    "adult":  {"name": "Kattalar (18+)",     "price": 50000,  "emoji": "👨"},
    "child":  {"name": "Bolalar (5-17)",      "price": 30000,  "emoji": "👶"},
    "vip":    {"name": "VIP zona",            "price": 100000, "emoji": "⭐"},
    "family": {"name": "Oilaviy paket (2+2)", "price": 150000, "emoji": "👨‍👩‍👧‍👦"},
}

# ===================== ISH VAQTI =====================
OPEN_HOUR  = 9
CLOSE_HOUR = 20

def is_open_now():
    now = datetime.now()
    return OPEN_HOUR <= now.hour < CLOSE_HOUR

# ===================== FAQ =====================
FAQ = [
    ("🧴 Sochiq va shippak kerakmi?",       "Ha, o'z sochiq va shippagingizni olib keling. Ijaraga ham beramiz — sochiq 5 000 so'm, shippak 3 000 so'm."),
    ("🍔 Ovqat olib kirsa bo'ladimi?",       "Tashqaridan ovqat olib kirish taqiqlangan. Bizda kafe va snack-bar mavjud."),
    ("🅿️ Avtoturargoh bormi?",              "Ha, bepul avtoturargoh mavjud."),
    ("🌊 Necha ta hovuz bor?",               "3 ta hovuz: kattalar uchun, bolalar uchun va to'lqinli hovuz."),
    ("📍 Manzil qayer?",                     "Qo'qon shahri, Mustaqqillik ko'chasi 45."),
    ("📞 Telefon raqam?",                    "+998 73 123 45 67"),
    ("🎟 Oldindan band qilsa bo'ladimi?",    "Ha, bu bot orqali band qilishingiz mumkin!"),
    ("👙 Kiyim almashtirish xonasi bormi?",  "Ha, alohida ayollar va erkaklar uchun kiyinish xonalari mavjud."),
]

# ===================== STATES =====================
(SELECTING_TICKET, SELECTING_COUNT, SELECTING_DATE,
 ENTERING_NAME, ENTERING_PHONE, CONFIRMING,
 ASKING_QUESTION) = range(7)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== YORDAMCHI =====================
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Band qilish",              callback_data="book")],
        [InlineKeyboardButton("💰 Narxlar",                  callback_data="prices")],
        [InlineKeyboardButton("🕐 Ish vaqti",                callback_data="hours")],
        [InlineKeyboardButton("❓ Tez-tez so'raladigan savollar", callback_data="faq")],
        [InlineKeyboardButton("📞 Bog'lanish",               callback_data="contact")],
    ])

async def go_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"🌊 Salom, {user.first_name}!\n\n"
        f"*Qo'qon AquaPark*ga xush kelibsiz! 🏖\n\n"
        f"Quyidagi bo'limlardan birini tanlang:"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")

# ===================== /start =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await go_main(update, context)

# ===================== NARXLAR =====================
async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "💰 *Narxlar ro'yxati:*\n\n"
    for val in PRICES.values():
        text += f"{val['emoji']} {val['name']}: *{val['price']:,} so'm*\n"
    text += "\n📌 Narxlar 1 kunlik kirish uchun."
    kb = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ===================== ISH VAQTI =====================
async def show_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    now = datetime.now()
    if is_open_now():
        status = f"🟢 Hozir *ochiq* (soat {now.strftime('%H:%M')})"
    else:
        status = f"🔴 Hozir *yopiq* (soat {now.strftime('%H:%M')})"
    text = (
        f"🕐 *Ish vaqti:*\n\n"
        f"📅 Har kuni (Dushanba — Yakshanba)\n"
        f"🌅 Ochilish: *09:00*\n"
        f"🌇 Yopilish: *20:00*\n\n"
        f"{status}"
    )
    kb = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ===================== FAQ =====================
async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [[InlineKeyboardButton(q, callback_data=f"faq_{i}")] for i, (q, _) in enumerate(FAQ)]
    kb.append([InlineKeyboardButton("✏️ O'z savolimni yuborish", callback_data="ask_question")])
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")])
    await query.edit_message_text(
        "❓ *Tez-tez so'raladigan savollar:*\n\nSavol tanlang yoki o'z savolingizni yuboring:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def show_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[1])
    question, answer = FAQ[idx]
    kb = [
        [InlineKeyboardButton("🔙 Savollarga qaytish", callback_data="faq")],
        [InlineKeyboardButton("🏠 Bosh menyu",         callback_data="back_main")],
    ]
    await query.edit_message_text(
        f"*{question}*\n\n{answer}",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

# ===================== O'Z SAVOL =====================
async def ask_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Savolingizni yozing, administratorga yuboriladi:\n\n"
        "_(Bekor qilish uchun /cancel)_",
        parse_mode="Markdown"
    )
    return ASKING_QUESTION

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    question_text = update.message.text

    # Foydalanuvchiga javob
    await update.message.reply_text(
        "✅ Savolingiz adminga yuborildi! Tez orada javob beramiz 🙏",
        reply_markup=main_keyboard()
    )

    # Adminga xabar
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📩 *Yangi savol keldi!*\n\n"
                f"👤 Foydalanuvchi: {user.full_name}\n"
                f"🆔 ID: `{user.id}`\n"
                f"📱 Username: @{user.username or 'yoq'}\n\n"
                f"❓ *Savol:*\n{question_text}"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Admin ga yuborishda xato: {e}")

    return ConversationHandler.END

# ===================== BOG'LANISH =====================
async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "📞 *Bog'lanish:*\n\n"
        "📍 *Manzil:* Qo'qon shahri, Mustaqqillik ko'chasi 45\n"
        "📱 *Telefon:* +998 73 123 45 67\n"
        "💬 *WhatsApp:* +998 90 123 45 67\n"
        "📧 *Email:* aquapark@qoqon.uz\n"
        "📸 *Instagram:* @qoqon\\_aquapark\n\n"
        "🕐 Qo'ng'iroq vaqti: 09:00 — 20:00"
    )
    kb = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ===================== BAND QILISH =====================
async def book_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    kb = []
    for key, val in PRICES.items():
        kb.append([InlineKeyboardButton(
            f"{val['emoji']} {val['name']} — {val['price']:,} so'm",
            callback_data=f"ticket_{key}"
        )])
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")])
    await query.edit_message_text(
        "📅 *Band qilish*\n\nChipta turini tanlang:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )
    return SELECTING_TICKET

async def select_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("ticket_", "")
    context.user_data["ticket_key"] = key
    context.user_data["ticket"]     = PRICES[key]
    kb = [[InlineKeyboardButton(str(i), callback_data=f"count_{i}") for i in range(1, 6)]]
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="book")])
    await query.edit_message_text(
        f"✅ Tanlangan: *{PRICES[key]['name']}*\n\n👥 Nechta chipta kerak?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )
    return SELECTING_COUNT

async def select_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    count = int(query.data.replace("count_", ""))
    context.user_data["count"] = count
    ticket = context.user_data["ticket"]
    context.user_data["total"] = ticket["price"] * count

    # Sana tanlash — bugundan boshlab 7 kun
    today = datetime.now()
    kb = []
    row = []
    for i in range(7):
        from datetime import timedelta
        d = today + timedelta(days=i)
        label = d.strftime("%d.%m") + (" (bugun)" if i == 0 else "")
        row.append(InlineKeyboardButton(label, callback_data=f"date_{d.strftime('%d.%m.%Y')}"))
        if len(row) == 3:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="book")])
    await query.edit_message_text(
        f"📅 Tashrif sanasini tanlang:\n\n"
        f"🎟 {ticket['name']} × {count} ta\n"
        f"💰 Jami: *{context.user_data['total']:,} so'm*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )
    return SELECTING_DATE

async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["date"] = query.data.replace("date_", "")
    await query.edit_message_text(
        f"📅 Sana: *{context.user_data['date']}*\n\n"
        f"👤 Ismingizni kiriting:",
        parse_mode="Markdown"
    )
    return ENTERING_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        f"✅ Ism: *{update.message.text}*\n\n"
        f"📱 Telefon raqamingizni kiriting:\n_(Masalan: +998901234567)_",
        parse_mode="Markdown"
    )
    return ENTERING_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    d = context.user_data
    ticket = d["ticket"]
    text = (
        f"📋 *Bandlovni tasdiqlang:*\n\n"
        f"👤 Ism: {d['name']}\n"
        f"📱 Telefon: {d['phone']}\n"
        f"📅 Sana: {d['date']}\n"
        f"🎟 Chipta: {ticket['name']}\n"
        f"👥 Soni: {d['count']} ta\n"
        f"💰 Jami: *{d['total']:,} so'm*\n\n"
        f"_To'lov kassada amalga oshiriladi._"
    )
    kb = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="confirm_no")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    return CONFIRMING

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_yes":
        d = context.user_data
        order_id = f"AQ{datetime.now().strftime('%d%m%H%M%S')}"
        ticket = d["ticket"]

        # Foydalanuvchiga
        await query.edit_message_text(
            f"🎉 *Band qilish tasdiqlandi!*\n\n"
            f"🆔 Raqam: `{order_id}`\n"
            f"👤 {d['name']}\n"
            f"📅 Sana: {d['date']}\n"
            f"🎟 {ticket['name']} × {d['count']} ta\n"
            f"💰 {d['total']:,} so'm\n\n"
            f"📍 Kassaga kelganda ushbu raqamni ko'rsating.\n"
            f"📞 Savollar: +998 73 123 45 67\n\n"
            f"Xush kelibsiz! 🌊",
            parse_mode="Markdown"
        )

        # Adminga
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📅 *Yangi band qilish!*\n\n"
                    f"🆔 {order_id}\n"
                    f"👤 {d['name']}\n"
                    f"📱 {d['phone']}\n"
                    f"📅 Sana: {d['date']}\n"
                    f"🎟 {ticket['name']} × {d['count']} ta\n"
                    f"💰 {d['total']:,} so'm"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Admin ga yuborishda xato: {e}")
    else:
        await query.edit_message_text(
            "❌ Band qilish bekor qilindi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_main")]])
        )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_keyboard())
    return ConversationHandler.END

async def back_main_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await go_main(update, context)
    return ConversationHandler.END

# ===================== MAIN =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    book_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_start, pattern="^book$")],
        states={
            SELECTING_TICKET: [
                CallbackQueryHandler(select_ticket,  pattern="^ticket_"),
                CallbackQueryHandler(back_main_cb,   pattern="^back_main$"),
            ],
            SELECTING_COUNT: [
                CallbackQueryHandler(select_count,   pattern="^count_"),
                CallbackQueryHandler(book_start,     pattern="^book$"),
            ],
            SELECTING_DATE: [
                CallbackQueryHandler(select_date,    pattern="^date_"),
                CallbackQueryHandler(book_start,     pattern="^book$"),
            ],
            ENTERING_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            CONFIRMING:     [CallbackQueryHandler(confirm_order, pattern="^confirm_")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(back_main_cb, pattern="^back_main$"),
        ],
    )

    ask_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_question_start, pattern="^ask_question$")],
        states={
            ASKING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(book_conv)
    app.add_handler(ask_conv)
    app.add_handler(CallbackQueryHandler(show_prices,     pattern="^prices$"))
    app.add_handler(CallbackQueryHandler(show_hours,      pattern="^hours$"))
    app.add_handler(CallbackQueryHandler(show_faq,        pattern="^faq$"))
    app.add_handler(CallbackQueryHandler(show_faq_answer, pattern="^faq_\\d+$"))
    app.add_handler(CallbackQueryHandler(show_contact,    pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(back_main_cb,    pattern="^back_main$"))

    print("🌊 Qo'qon AquaPark boti ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()