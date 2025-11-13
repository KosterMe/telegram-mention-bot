import logging
import os
import json
from flask import Flask, request, jsonify
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8206656364:AAExGzZ2Lgca_XYkzCsniJx4JpbakPaDB6M')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__)

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
        # Логируем все входящие данные
        raw_data = request.get_data(as_text=True)
        logger.info(f"📨 Received webhook: {raw_data[:500]}...")  # Ограничиваем длину
        
        if raw_data:
            data = json.loads(raw_data)
            
            # Проверяем есть ли сообщение
            if 'message' in data:
                message = data['message']
                chat_id = message['chat']['id']
                text = message.get('text', '')
                user = message.get('from', {})
                
                logger.info(f"💬 Message from {user.get('first_name')}: {text}")
                
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
                    # Простая версия команды /all
                    custom_text = text[5:] if len(text) > 5 else "Внимание всем!"
                    response_text = f"📢 {custom_text}\n\n@all @everyone"
                    send_telegram_message(chat_id, response_text)
                    
                elif text == '/random':
                    response_text = "🎲 Внимание случайному участнику!"
                    send_telegram_message(chat_id, response_text)
                    
                else:
                    # Ответ на неизвестные команды
                    response_text = f"❌ Неизвестная команда: {text}\nИспользуй /help для списка команд"
                    send_telegram_message(chat_id, response_text)
                    
        return 'ok'
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return 'error', 500

def send_telegram_message(chat_id, text):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
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