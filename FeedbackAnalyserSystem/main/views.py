from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Avg, Q

from users.models import Feedback, SentimanetAnalyze

@login_required(login_url='/users/login/')
def dashboard_view(request):

    today = timezone.now().date()
    
    # Всего отзывов за текущий день
    total_reviews_today = Feedback.objects.filter(created_at__date=today).count()
    
    # Средний индекс тональности (конвертация float в шкалу 0-100)
    avg_sentiment = SentimanetAnalyze.objects.aggregate(avg_val=Avg('value'))['avg_val']
    avg_index = int(avg_sentiment * 100) if avg_sentiment is not None else 0
        
    # Количество критических отзывов (сильный негатив или сарказм)
    critical_count = SentimanetAnalyze.objects.filter(
        Q(value__lt=-0.5) | Q(meta_data__status__icontains="SARCASM")
    ).count()

    trend_data = {
        'labels': ['01 Mar', '03 Mar', '05 Mar', '07 Mar', '09 Mar', '11 Mar', '14 Mar'],
        'positive': [15, 22, 18, 30, 25, 35, 28],
        'negative': [10, 5, 12, 8, 15, 10, 5]
    }

    # Данные для кольцевой диаграммы (Распределение)
    distribution_data = {
        'labels': ['Нейтральные', 'Позитивные', 'Негативные'],
        'values': [42, 36, 15]
    }

    context = {
        'page_title': 'Дашборд',
        'total_reviews': total_reviews_today,
        'avg_index': avg_index,
        'critical_count': critical_count,
        # Передача данных для графиков
        'trend_data': trend_data,
        'distribution_data': distribution_data,
    }

    return render(request, 'main/dashboard.html', context)