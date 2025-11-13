import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8206656364:AAExGzZ2Lgca_XYkzCsniJx4JpbakPaDB6M')

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

def main():
    try:
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("all", all_command))
        application.add_handler(CommandHandler("random", random_command))
        
        logger.info("🚀 Бот запущен на Render!")
        print("🤖 Бот работает...")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")

if __name__ == "__main__":
    main()