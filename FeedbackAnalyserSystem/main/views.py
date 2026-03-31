from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Q, Count
from django.db.models.functions import TruncDate # Добавлен импорт для работы с датами
from django.core.paginator import Paginator
from django.contrib.auth.models import User

from users.models import Feedback, SentimanetAnalyze

@login_required(login_url='/users/login/')
def dashboard_view(request):
    today = timezone.now().date()
    fourteen_days_ago = today - timedelta(days=14) # Ограничиваем выборку последними 14 днями
    
    # ==========================================
    # 1. КЛЮЧЕВЫЕ МЕТРИКИ (KPI)
    # ==========================================
    total_reviews_today = Feedback.objects.filter(created_at__date=today).count()
    
    avg_sentiment = SentimanetAnalyze.objects.aggregate(avg_val=Avg('value'))['avg_val']
    avg_index = int(avg_sentiment * 100) if avg_sentiment is not None else 0
        
    critical_count = SentimanetAnalyze.objects.filter(
        Q(value__lt=-0.5) | Q(meta_data__status__icontains="SARCASM")
    ).count()

    # ==========================================
    # 2. ПОДГОТОВКА ДАННЫХ ДЛЯ ГРАФИКОВ
    # ==========================================
    

    base_qs = SentimanetAnalyze.objects.filter(
        type='Embed', 
        feedback__created_at__gte=fourteen_days_ago
    )

    # --- Кольцевая диаграмма (Распределение) ---
    pos_count = base_qs.filter(value__gt=0.2).count()
    neg_count = base_qs.filter(value__lt=-0.2).count()
    neu_count = base_qs.filter(value__gte=-0.2, value__lte=0.2).count()

    distribution_data = {
        'labels': ['Нейтральные', 'Позитивные', 'Негативные'],
        'values': [neu_count, pos_count, neg_count]
    }

    # --- Линейный график (Тренд тональности) ---
    # Группируем записи по дате создания и считаем количество позитива/негатива в каждый день
    daily_stats = base_qs.annotate(date=TruncDate('feedback__created_at')) \
        .values('date') \
        .annotate(
            pos_count=Count('id', filter=Q(value__gt=0.2)),
            neg_count=Count('id', filter=Q(value__lt=-0.2))
        ).order_by('date')

    # Распаковка сгруппированных данных в списки для Chart.js
    trend_labels = []
    trend_positive = []
    trend_negative = []

    for stat in daily_stats:
        if stat['date']:
            # Преобразуем объект даты в строку формата "05 Mar"
            formatted_date = stat['date'].strftime('%d %b')
            trend_labels.append(formatted_date)
            trend_positive.append(stat['pos_count'])
            trend_negative.append(stat['neg_count'])

    trend_data = {
        'labels': trend_labels,
        'positive': trend_positive,
        'negative': trend_negative
    }

    # ==========================================
    # 3. ПЕРЕДАЧА В ШАБЛОН
    # ==========================================
    context = {
        'page_title': 'Дашборд',
        'total_reviews': total_reviews_today,
        'avg_index': avg_index,
        'critical_count': critical_count,
        'trend_data': trend_data,
        'distribution_data': distribution_data,
    }

    return render(request, 'main/dashboard.html', context)

@login_required(login_url='/users/login/')
def feedback_view(request):
    all_feedbacks = Feedback.objects.all().order_by('-created_at')

    paginator = Paginator(all_feedbacks, 10)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj 
    }

    context_1 = {
        'all_feedbacks': all_feedbacks
    }
    return render(request, 'main/feed.html', context)

@login_required(login_url='/users/login/')
def config(request):
    all_users = User.objects.all().order_by('-date_joined')
    context = {
        "users": all_users
    }
    return render(request, 'main/config.html', context)