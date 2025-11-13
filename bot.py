import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import os
# Настройка красивого логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8206656364:AAExGzZ2Lgca_XYkzCsniJx4JpbakPaDB6M')

# Эмодзи для красивого оформления
EMOJI = {
    "wave": "👋",
    "megaphone": "📢",
    "target": "🎯",
    "dice": "🎲",
    "crown": "👑",
    "busts": "👥",
    "speech": "💬",
    "bell": "🔔",
    "info": "ℹ️",
    "sparkles": "✨"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    if update.effective_chat.type in ["group", "supergroup"]:
        message = (
            f"{EMOJI['wave']} <b>Привет! Я бот для упоминаний</b>\n\n"
            f"{EMOJI['megaphone']} <b>Доступные команды:</b>\n"
            "• /all - Упомянуть всех участников\n"
            "• /all [текст] - Упоминание с вашим текстом\n" 
            "• /random - Упомянуть случайного участника\n"
            "• /help - Полная справка\n\n"
            f"{EMOJI['sparkles']} <i>Просто введи команду в чате!</i>"
        )
        await update.message.reply_text(message, parse_mode='HTML')
    else:
        await update.message.reply_text(
            f"{EMOJI['wave']} Добавь меня в группу, чтобы начать работу! 👥"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        f"{EMOJI['target']} <b>Бот для упоминаний - Помощь</b>\n\n"
        f"{EMOJI['megaphone']} <b>Команды:</b>\n"
        "• <code>/all</code> - Общее упоминание\n"
        "• <code>/all [текст]</code> - Упоминание с вашим текстом\n"
        "• <code>/random</code> - Случайный участник\n\n"
        f"{EMOJI['info']} <b>Примеры использования:</b>\n"
        "• <code>/all Всем читать сообщение!</code>\n"
        "• <code>/all Собрание в 18:00</code>\n"
        "• <code>/random</code>\n\n"
        f"{EMOJI['sparkles']} Бот упоминает администраторов группы"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')

async def mention_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Упоминание всех участников"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Эта команда работает только в группах!")
        return
    
    try:
        bot = context.bot
        custom_text = " ".join(context.args) if context.args else "Внимание всем!"
        
        # Получаем данные о чате
        total_members = await bot.get_chat_member_count(chat.id)
        admins = await bot.get_chat_administrators(chat.id)
        
        # Собираем упоминания администраторов
        admin_mentions = []
        for admin in admins:
            admin_user = admin.user
            if not admin_user.is_bot and admin_user.username:
                admin_mentions.append(f"@{admin_user.username}")
        
        # Формируем красивое сообщение
        message_parts = [
            f"{EMOJI['megaphone']} <b>{custom_text}</b>",
            ""
        ]
        
        if admin_mentions:
            message_parts.extend([
                f"{EMOJI['crown']} <b>Администраторы:</b>",
                " ".join(admin_mentions),
                ""
            ])
        
        message_parts.extend([
            f"{EMOJI['busts']} Участников в чате: <b>{total_members}</b>",
            f"{EMOJI['speech']} От: <b>{user.first_name}</b>"
        ])
        
        await update.message.reply_text("\n".join(message_parts), parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в mention_all: {e}")
        error_message = (
            f"{EMOJI['megaphone']} <b>Внимание всем!</b>\n\n"
            "❌ <i>Не удалось получить список участников</i>"
        )
        await update.message.reply_text(error_message, parse_mode='HTML')

async def mention_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Упоминание случайного участника"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Эта команда работает только в группах!")
        return
    
    try:
        bot = context.bot
        custom_text = " ".join(context.args) if context.args else "Внимание случайному участнику!"
        
        admins = await bot.get_chat_administrators(chat.id)
        
        # Фильтруем ботов и перемешиваем
        human_admins = [admin for admin in admins if not admin.user.is_bot]
        random.shuffle(human_admins)
        
        # Выбираем одного случайного участника
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
                mentions.append(f"<b>{name}</b>")
        
        if mentions:
            message = (
                f"{EMOJI['dice']} <b>{custom_text}</b>\n\n"
                f"🎯 Выбран: {mentions[0]}\n\n"
                f"{EMOJI['speech']} От: <b>{user.first_name}</b>"
            )
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text(
                f"{EMOJI['dice']} ❌ Не найдено участников для упоминания",
                parse_mode='HTML'
            )
        
    except Exception as e:
        logger.error(f"Ошибка в mention_random: {e}")
        await update.message.reply_text(
            f"{EMOJI['dice']} ❌ Ошибка при выборе случайного участника",
            parse_mode='HTML'
        )

def main():
    """Основная функция запуска бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("all", mention_all))
        application.add_handler(CommandHandler("random", mention_random))
        
        # Запускаем бота
        logger.info("🚀 Бот для упоминаний успешно запущен...")
        print("=" * 50)
        print("🤖 Бот запущен и работает")
        print("⚡ Ожидаем сообщения...")
        print("=" * 50)
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()