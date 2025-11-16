# bot.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler, CallbackQueryHandler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8271856122:AAEwJ4y-drW66Bwt4xJEeyiJAh7S8V9RuNw")

# -----------------------
# STATES
# -----------------------
(
    CAR_TYPE, FUEL, PRICE, AMORT, RENT_COST,
    RENT_HOURS, RENT_TIME, ORDER_COST, ORDER_DISTANCE
) = range(9)

# -----------------------
# Хранилище пользователей
# -----------------------
users = {}

# -----------------------
# Тексты
# -----------------------
WELCOME_TEXT = (
    "👋 Привет! Я бот RideCalc 🐱, который помогает курьерам рассчитать рентабельность заказов.\n\n"
    "⚠️ Все расчеты приблизительные.\n\n"
    "Выберите тип транспорта:"
)

AMORT_HINT = (
    "Укажите амортизацию автомобиля (₽/км).\n"
    "Примерные диапазоны:\n"
    "• Эконом-класс: 3–5 ₽/км\n"
    "• Средний класс: 5–7 ₽/км\n"
    "• Премиум: 7–10 ₽/км\n"
    "Введите число (например: 4)"
)

# -----------------------
# Команды
# -----------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 Помощь и обратная связь:\n"
        "Telegram: @kamimyli\n"
        "/start — начать\n"
        "/stats — статистика\n"
        "/reset_stats — сброс статистики\n"
        "/reset_profile — сброс профиля\n"
        "/reset — сброс всего\n"
        "/cancel — отмена ввода"
    )

# -----------------------
# Старт
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚗 Своя машина", callback_data="own"),
         InlineKeyboardButton("📦 Аренда", callback_data="rent")],
        [InlineKeyboardButton("🆘 Помощь", url="https://t.me/kamimyli")]
    ])
    if update.message:
        await update.message.reply_text(WELCOME_TEXT, reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(WELCOME_TEXT, reply_markup=keyboard)
    return CAR_TYPE

async def car_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data
    users[user_id] = {"orders": []}
    users[user_id]["car_type"] = "Своя машина" if choice == "own" else "Арендованная машина"
    await query.edit_message_text("Шаг 1: Укажите расход топлива (л/100 км):")
    return FUEL

# -----------------------
# Обработчики ввода
# -----------------------
def parse_float_or_none(text):
    try:
        return float(text.replace(",", "."))
    except Exception:
        return None

async def fuel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v <= 0:
        await update.message.reply_text("Неверный ввод. Введите расход топлива (например: 8):")
        return FUEL
    users[user_id]["fuel"] = v
    await update.message.reply_text("Шаг 2: Укажите цену бензина (₽/л):")
    return PRICE

async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v <= 0:
        await update.message.reply_text("Неверный ввод. Введите цену бензина (например: 65):")
        return PRICE
    users[user_id]["price"] = v
    if users[user_id]["car_type"] == "Своя машина":
        await update.message.reply_text(AMORT_HINT)
        return AMORT
    await update.message.reply_text("Шаг 3: Укажите стоимость аренды машины за сутки (₽):")
    return RENT_COST

async def amort_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v < 0:
        await update.message.reply_text("Неверный ввод. Введите амортизацию (например: 4):")
        return AMORT
    users[user_id]["amort"] = v
    await update.message.reply_text("✅ Профиль сохранён! Введите стоимость заказа (₽):")
    return ORDER_COST

async def rent_cost_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v < 0:
        await update.message.reply_text("Неверный ввод. Введите аренду за сутки (например: 2500):")
        return RENT_COST
    users[user_id]["rent_cost"] = v
    await update.message.reply_text("Сколько часов вы обычно работаете в сутки?")
    return RENT_HOURS

async def rent_hours_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v <= 0:
        await update.message.reply_text("Неверный ввод. Введите часы в сутки (например: 10):")
        return RENT_HOURS
    users[user_id]["rent_hours"] = v
    await update.message.reply_text("Сколько минут в среднем занимает один заказ?")
    return RENT_TIME

async def rent_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v <= 0:
        await update.message.reply_text("Неверный ввод. Введите минуты (например: 20):")
        return RENT_TIME
    users[user_id]["rent_time"] = v
    await update.message.reply_text("✅ Профиль сохранён! Введите стоимость заказа (₽):")
    return ORDER_COST

async def order_cost_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v < 0:
        await update.message.reply_text("Неверный ввод. Стоимость заказа в ₽ (например: 390):")
        return ORDER_COST
    users[user_id]["order_cost"] = v
    await update.message.reply_text("Укажите расстояние (км):")
    return ORDER_DISTANCE

async def order_distance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    v = parse_float_or_none(update.message.text)
    if v is None or v < 0:
        await update.message.reply_text("Неверный ввод. Укажите расстояние (например: 15):")
        return ORDER_DISTANCE

    distance = v
    u = users[user_id]
    cost = u.get("order_cost", 0.0)
    fuel_cost = distance * u["fuel"] * u["price"] / 100.0

    if u["car_type"] == "Своя машина":
        amort_cost = distance * u.get("amort", 0.0)
        amort_label = "Амортизация"
    else:
        rent_per_hour = u["rent_cost"] / u["rent_hours"]
        amort_cost = rent_per_hour * (u["rent_time"] / 60.0)
        amort_label = "Аренда за время заказа"

    profit = cost - fuel_cost - amort_cost
    rating = "ВЫГОДНО ✅" if profit > 200 else "НОРМАЛЬНО ⚖️" if profit > 100 else "НЕВЫГОДНО ⚠️"

    u.setdefault("orders", []).append({
        "order_cost": cost,
        "fuel_cost": fuel_cost,
        "amort_cost": amort_cost,
        "profit": profit,
        "distance": distance
    })

    await update.message.reply_text(
        f"📦 Стоимость заказа: {cost:.2f} ₽\n"
        f"⛽ Бензин: {fuel_cost:.2f} ₽\n"
        f"🛠 {amort_label}: {amort_cost:.2f} ₽\n"
        f"💸 Чистая прибыль: {profit:.2f} ₽\n\n"
        f"📊 Оценка: {rating}\n\n"
        "Введите стоимость следующего заказа (₽) и расстояние для расчёта."
    )
    return ORDER_COST

# -----------------------
# MAIN
# -----------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CAR_TYPE: [CallbackQueryHandler(car_type_handler)],
            FUEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuel_handler)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_handler)],
            AMORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amort_handler)],
            RENT_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_cost_handler)],
            RENT_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_hours_handler)],
            RENT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_time_handler)],
            ORDER_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_cost_handler)],
            ORDER_DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_distance_handler)],
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: None)]
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
