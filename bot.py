import logging
import os
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8206656364:AAExGzZ2Lgca_XYkzCsniJx4JpbakPaDB6M')
PORT = int(os.environ.get('PORT', 5000))
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', '') + f"/webhook/{TOKEN}"

# Flask приложение
app = Flask(__name__)

# Глобальные переменные для бота
application = None

# Твои функции (не изменились) 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для упоминаний\n\n"
        "📢 Команды:\n"
        "/all - упомянуть всех\n" 
        "/random - случайный участник\n"
        "/help - справка"
    )

async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Эта команда работает только в группах!")
        return
    
    try:
        bot = context.bot
        custom_text = " ".join(context.args) if context.args else "Внимание всем!"
        
        total_members = await bot.get_chat_member_count(chat.id)
        admins = await bot.get_chat_administrators(chat.id)
        
        admin_mentions = []
        for admin in admins:
            admin_user = admin.user
            if not admin_user.is_bot and admin_user.username:
                admin_mentions.append(f"@{admin_user.username}")
        
        message_parts = [f"📢 {custom_text}", ""]
        
        if admin_mentions:
            message_parts.extend([
                "👑 Администраторы:",
                " ".join(admin_mentions),
                ""
            ])
        
        message_parts.extend([
            f"👥 Участников: {total_members}",
            f"💬 От: {user.first_name}"
        ])
        
        await update.message.reply_text("\n".join(message_parts))
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("📢 Внимание всем!")

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Эта команда работает только в группах!")
        return
    
    try:
        bot = context.bot
        admins = await bot.get_chat_administrators(chat.id)
        
        human_admins = [admin for admin in admins if not admin.user.is_bot]
        random.shuffle(human_admins)
        
        selected = human_admins[:1] if human_admins else []
        
        mentions = []
        for admin in selected:
            admin_user = admin.user
            if admin_user.username:
                mentions.append(f"@{admin_user.username}")
            else:
                name = admin_user.first_name
                if admin_user.last_name:
                    name += f" {admin_user.last_name}"
                mentions.append(name)
        
        if mentions:
            message = f"🎲 Внимание случайному участнику!\n\n🎯 Выбран: {mentions[0]}\n\n💬 От: {user.first_name}"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("🎲 Не найдено участников для упоминания")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("🎲 Ошибка при выборе случайного участника")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 Бот для упоминаний\n\n"
        "📢 Команды:\n"
        "/all - Упоминание всех\n"
        "/random - Случайный участник\n\n"
        "💡 Примеры:\n"
        "/all Всем читать!\n"
        "/all Собрание в 18:00"
    )

# Flask endpoints
@app.route('/')
def home():
    return jsonify({
        "status": "Bot is running", 
        "service": "Web Service",
        "commands": ["/start", "/all", "/random", "/help"]
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Обработчик webhook от Telegram"""
    try:
        if application is None:
            return 'Bot not initialized', 503
            
        json_str = request.get_data().decode('UTF-8')
        update = Update.de_json(json_str, application.bot)
        application.update_queue.put_nowait(update)
        return 'ok'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'error', 500

def setup_bot():
    """Настройка и запуск бота в том же потоке"""
    global application
    
    # Создаем application в основном потоке
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("all", all_command))
    application.add_handler(CommandHandler("random", random_command))
    
    # Настраиваем webhook если URL доступен
    if WEBHOOK_URL and 'onrender.com' in WEBHOOK_URL:
        logger.info(f"Setting webhook to: {WEBHOOK_URL}")
        
        # Запускаем webhook в отдельном потоке с правильным event loop
        def start_webhook():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                secret_token='webhook',
                webhook_url=WEBHOOK_URL
            )
        
        import threading
        webhook_thread = threading.Thread(target=start_webhook)
        webhook_thread.daemon = True
        webhook_thread.start()
        
    else:
        # Локальная разработка - polling
        logger.info("Running in polling mode")
        def start_polling():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            application.run_polling()
        
        import threading
        polling_thread = threading.Thread(target=start_polling)
        polling_thread.daemon = True
        polling_thread.start()

if __name__ == "__main__":
    # Настраиваем бота
    setup_bot()
    
    # Запускаем Flask server в основном потоке
    logger.info(f"Starting Flask server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)