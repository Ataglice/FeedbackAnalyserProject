from django.core.mail import send_mail
from django.conf import settings
import requests
import os

def send_sentiment_alert(feedback_obj, sentiment_value):
    
    if sentiment_value <= -0.7:
        subject = f"КРИТИЧЕСКИЙ НЕГАТИВ: Отзыв #{feedback_obj.id}"
        message = (
            f"Внимание! Получен отзыв с критическим уровнем негатива.\n\n"
            f"Текст отзыва: {feedback_obj.text}\n"
            f"Оценка ИИ: {sentiment_value}\n"
            f"Источник: {feedback_obj.platform.name}\n\n"
            f"Ссылка на отзыв: http://emosdk.tech/feed/" #ссылка
        )
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['admin@emosdk.tech'], # Почта, куда придут алерты
            fail_silently=True,
        )

        send_telegram_notification(f"{subject}\n\n{message}")


def send_telegram_notification(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    
    if not token or not chat_id:
        return 
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML" 
    }
    
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")