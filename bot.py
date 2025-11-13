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
        logger.info(f"📨 Received webhook: {raw_data}")
        
        if raw_data:
            data = json.loads(raw_data)
            logger.info(f"📊 Parsed data: {json.dumps(data, indent=2)}")
            
            # Проверяем есть ли сообщение
            if 'message' in data:
                message = data['message']
                chat_id = message['chat']['id']
                text = message.get('text', '')
                user = message.get('from', {})
                
                logger.info(f"💬 Message from {user.get('first_name')}: {text}")
                
                # Отвечаем на команды
                if text.startswith('/'):
                    response_text = f"✅ Получил команду: {text}\nЧат ID: {chat_id}"
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