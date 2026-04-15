from celery import shared_task
from .models import Feedback, SentimanetAnalyze


@shared_task
def analyze_feedback_task(feedback_id):
    from .views import get_analyzer
    
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

    #send_sentiment_alert(feedback_instance, overall_value)