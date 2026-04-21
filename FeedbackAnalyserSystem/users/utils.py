from django.core.mail import send_mail
from django.conf import settings
import requests
import os
from analyser.AnalyzerPipeline import SentimentAnalyzer
from django.conf import settings
from .models import CompanyMember, Notification

def send_email_alert(company, subject, message, custom_emails_str=None):
    if not company:
        return
    
    recipients = CompanyMember.objects.filter(
        company=company, 
        role__in=['owner', 'admin']
    ).select_related('user').values_list('user__email', flat=True)
    
    recipient_list = [email for email in recipients if email]

  
    if custom_emails_str:
        extra_emails = [e.strip() for e in custom_emails_str.split(',') if '@' in e.strip()]
        recipient_list.extend(extra_emails)

    recipient_list = list(set(recipient_list))

    if not recipient_list:
        print(f"Email Alert: Нет получателей для компании {company.name}")
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL, 
            recipient_list=recipient_list,
            fail_silently=False, 
        )
        print(f"✅ Email успешно отправлен {len(recipient_list)} получателям!")
    except Exception as e:
        print(f"❌ Ошибка при отправке Email: {e}")
        


def send_telegram_notification(message, token=None, chat_id=None):
    final_token = token if token else os.getenv("TELEGRAM_BOT_TOKEN")
    final_chat_id = chat_id if chat_id else os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    
    if not final_token or not final_chat_id:
        print("Ошибка: Токен или Chat ID для Telegram отсутствуют.")
        return 
    
    url = f"https://api.telegram.org/bot{final_token}/sendMessage"
    data = {
        "chat_id": final_chat_id,
        "text": message,
        "parse_mode": "HTML" 
    }
    
    try:
        response = requests.post(url, data=data, timeout=5)
        if response.status_code != 200:
            print(f"Ошибка Telegram API: {response.text}")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")


def notify_company_users(company, title, message, notification_type='INFO', link=None):

    if not company:
        return
    
    members = CompanyMember.objects.filter(company=company).select_related('user')

    notifications_to_create = []

    for member in members:
        notifications_to_create.append(
            Notification(
                user=member.user,
                company=company,
                type=notification_type,
                title=title,
                message=message,
                link=link
            )
        )

    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)


nlp_analyzer = None

def get_analyzer():
    global nlp_analyzer
    if nlp_analyzer is None:
        print(">>> Загрузка AI-моделей в память... <<<")
        nlp_analyzer = SentimentAnalyzer()
    return nlp_analyzer