import logging
import os
import json
from flask import Flask, request, jsonify
import requests
import random

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8206656364:AAExGzZ2Lgca_XYkzCsniJx4JpbakPaDB6M')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__)

def get_chat_administrators(chat_id):
    """Получить список администраторов чата"""
    url = f"https://api.telegram.org/bot{TOKEN}/getChatAdministrators"
    payload = {'chat_id': chat_id}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get('result', [])
        else:
            logger.error(f"Error getting admins: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error in get_chat_administrators: {e}")
        return []

def get_chat_member_count(chat_id):
    """Получить количество участников чата"""
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMembersCount"
    payload = {'chat_id': chat_id}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get('result', 0)
        else:
            logger.error(f"Error getting member count: {response.status_code}")
            return 0
    except Exception as e:
        logger.error(f"Error in get_chat_member_count: {e}")
        return 0

def get_chat_info(chat_id):
    """Получить информацию о чате"""
    url = f"https://api.telegram.org/bot{TOKEN}/getChat"
    payload = {'chat_id': chat_id}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get('result', {})
        else:
            logger.error(f"Error getting chat info: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error in get_chat_info: {e}")
        return {}

@app.route('/')
def home():
    return jsonify({"status": "Bot is running", "webhook_set": True})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook для Telegram"""
    try:
        raw_data = request.get_data(as_text=True)
        logger.info(f"📨 Received webhook: {raw_data[:500]}...")
        
        if raw_data:
            data = json.loads(raw_data)
            
            if 'message' in data:
                message = data['message']
                chat_id = message['chat']['id']
                chat_type = message['chat']['type']
                text = message.get('text', '')
                user = message.get('from', {})
                user_name = user.get('first_name', 'User')
                
                logger.info(f"💬 Message from {user_name} in {chat_type}: {text}")
                
                # Обрабатываем команды
                if text == '/start':
                    response_text = (
                        "👋 Привет! Я бот для упоминаний\n\n"
                        "📢 Команды:\n"
                        "/all - упомянуть всех\n" 
                        "/random - случайный участник\n"
                        "/help - справка"
                    )
                    send_telegram_message(chat_id, response_text)
                    
                elif text == '/help':
                    response_text = (
                        "🎯 Бот для упоминаний\n\n"
                        "📢 Команды:\n"
                        "/all - Упоминание всех\n"
                        "/random - Случайный участник\n\n"
                        "💡 Примеры:\n"
                        "/all Всем читать!\n"
                        "/all Собрание в 18:00"
                    )
                    send_telegram_message(chat_id, response_text)
                    
                elif text.startswith('/all'):
                    handle_all_command(chat_id, chat_type, text, user_name)
                    
                elif text == '/random':
                    handle_random_command(chat_id, chat_type, user_name)
                    
                elif text.startswith('/'):
                    response_text = f"❌ Неизвестная команда: {text}\nИспользуй /help для списка команд"
                    send_telegram_message(chat_id, response_text)
                    
        return 'ok'
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return 'error', 500

def handle_all_command(chat_id, chat_type, text, user_name):
    """Обработка команды /all"""
    if chat_type not in ["group", "supergroup"]:
        send_telegram_message(chat_id, "❌ Эта команда работает только в группах!")
        return
    
    try:
        custom_text = text[5:].strip() if len(text) > 5 else "Внимание всем!"
        
        # Получаем информацию о чате
        total_members = get_chat_member_count(chat_id)
        admins = get_chat_administrators(chat_id)
        
        # Формируем упоминания администраторов
        admin_mentions = []
        for admin in admins:
            admin_user = admin.get('user', {})
            if not admin_user.get('is_bot', False) and admin_user.get('username'):
                admin_mentions.append(f"@{admin_user['username']}")
        
        # Собираем сообщение
        message_parts = [f"📢 {custom_text}", ""]
        
        if admin_mentions:
            message_parts.extend([
                "👑 Администраторы:",
                " ".join(admin_mentions),
                ""
            ])
        
        message_parts.extend([
            f"👥 Участников: {total_members}",
            f"💬 От: {user_name}"
        ])
        
        response_text = "\n".join(message_parts)
        send_telegram_message(chat_id, response_text)
            
    except Exception as e:
        logger.error(f"❌ Error in /all: {e}")
        send_telegram_message(chat_id, "📢 Внимание всем!")

def handle_random_command(chat_id, chat_type, user_name):
    """Обработка команды /random"""
    if chat_type not in ["group", "supergroup"]:
        send_telegram_message(chat_id, "❌ Эта команда работает только в группах!")
        return
    
    try:
        admins = get_chat_administrators(chat_id)
        
        # Фильтруем ботов и оставляем только людей
        human_admins = []
        for admin in admins:
            admin_user = admin.get('user', {})
            if not admin_user.get('is_bot', False):
                human_admins.append(admin_user)
        
        # Выбираем случайного участника
        if human_admins:
            random.shuffle(human_admins)
            selected_user = human_admins[0]
            
            # Формируем упоминание
            if selected_user.get('username'):
                mention = f"@{selected_user['username']}"
            else:
                mention = selected_user.get('first_name', '')
                if selected_user.get('last_name'):
                    mention += f" {selected_user['last_name']}"
            
            response_text = (
                f"🎲 Внимание случайному участнику!\n\n"
                f"🎯 Выбран: {mention}\n\n"
                f"💬 От: {user_name}"
            )
        else:
            response_text = "🎲 Не найдено участников для упоминания"
        
        send_telegram_message(chat_id, response_text)
        
    except Exception as e:
        logger.error(f"❌ Error in /random: {e}")
        send_telegram_message(chat_id, "🎲 Ошибка при выборе случайного участника")

def send_telegram_message(chat_id, text):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        logger.info(f"📤 Sent message to {chat_id}, status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Send message error: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"🚀 Starting bot on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)