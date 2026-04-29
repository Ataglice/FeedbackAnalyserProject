from celery import shared_task
from .models import Feedback, SentimanetAnalyze
from .utils import send_telegram_notification, send_email_alert, notify_company_users
from users.utils import get_analyzer
import html


@shared_task
def analyze_feedback_task(feedback_id):
    
    try:
        feedback = Feedback.objects.get(id=feedback_id)
    except Feedback.DoesNotExist:
        return "Отзыв не найден"

    analyzer = get_analyzer()
    result = analyzer.smart_analyze(feedback.text)

    type_data = result.get('type', {})
    overall_value = result.get('value', 0.0)

    for model_name, model_metrics in type_data.items():
        pos_val = 0.0
        neg_val = 0.0
        neu_val = 0.0
        
        # По умолчанию записываем общий итог 
        model_specific_value = overall_value 

        #? ВЕТВЬ А: Если модель вернула словарь (Embed, VADER)
        if isinstance(model_metrics, dict):
            # Универсальное извлечение: ищет ключи Embed, если их нет — ищет ключи VADER
            pos_val = model_metrics.get('POSITIVE', model_metrics.get('pos', 0.0))
            neg_val = model_metrics.get('NEGATIVE', model_metrics.get('neg', 0.0))
            neu_val = model_metrics.get('NEUTRAL', model_metrics.get('neu', 0.0))

            if neg_val > 0:
                neg_val = -neg_val
            
            # Если это VADER, извлекаем его конкретный итоговый коэффициент
            if model_name == "VADER":
                model_specific_value = model_metrics.get('compound', overall_value)

        #? ВЕТВЬ Б: Если модель вернула число (RuBERT, DistilBERT)
        elif isinstance(model_metrics, (float, int)):
            model_specific_value = float(model_metrics)
            
            # Конвертация числа в метрики (от -1.0 до 1.0)
            if model_metrics > 0:
                pos_val = float(model_metrics)
            elif model_metrics < 0:
                neg_val = float(model_metrics)
            else:
                neu_val = 1.0


        SentimanetAnalyze.objects.create(
            feedback=feedback,
            type=model_name,
            positive_val=pos_val,
            negative_val=neg_val,
            neutral_val=neu_val,
            value=model_specific_value
        )

    SentimanetAnalyze.objects.create(
        feedback=feedback,
        type='FINAL',
        value=overall_value,
        positive_val=0.0,
        negative_val=0.0,
        neutral_val=0.0
    )

    
    try:
        settings = feedback.company.notification_settings
    except Exception:
        settings = None

    threshold = settings.critical_threshold if settings else -0.5
    
    if overall_value <= threshold:
        # Базовые переменные для шаблона
        platform_name = feedback.platform.name if feedback.platform else 'Неизвестно'
        feedback_link = f"http://127.0.0.1:8000/feedback_feed/?search_query={feedback.external_id}"
        safe_text = html.escape(feedback.text)
        
        # Генерация сообщения на основе шаблона (или дефолтного)
        if settings and settings.alert_template:
            # Если клиент написал свой шаблон, заменяем теги на реальные данные
            base_message = settings.alert_template \
                .replace('{company}', feedback.company.name) \
                .replace('{platform}', platform_name) \
                .replace('{score}', str(overall_value)) \
                .replace('{text}', safe_text) \
                .replace('{link}', feedback_link)
        else:
            # Стандартное сообщение, если клиент не задал свой шаблон
            base_message = (
                f"🚨 <b>АЛЕРТ: НЕГАТИВНЫЙ ОТЗЫВ</b>\n\n"
                f"<b>Платформа:</b> {platform_name}\n"
                f"<b>Оценка ИИ:</b> {overall_value}\n\n"
                f"<b>Текст:</b> <i>{safe_text}</i>\n\n"
                f"<b>Ссылка:</b> {feedback_link}"
            )

        # 1. Колокольчик
        if settings and settings.is_in_app_enabled:
            notify_company_users(
                company=feedback.company,
                title="⚠️ Негативный отзыв!",
                message=f"Оценка {overall_value}. Платформа: {platform_name}.",
                notification_type="CRITICAL",
                link=feedback_link 
            )

        # 2. Email
        if settings and settings.is_email_enabled:
            clean_email_body = base_message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
            send_email_alert(
                company=feedback.company, 
                subject=f"Негативный отзыв ({overall_value}) - {feedback.company.name}", 
                message=clean_email_body,
                custom_emails_str=settings.custom_emails 
            )

        # 3. Telegram
        if settings and settings.is_telegram_enabled:
            send_telegram_notification(
                message=base_message,
                token=settings.telegram_bot_token,  
                chat_id=settings.telegram_chat_id  
            )