from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Q, Count
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib import messages

from users.models import Platform, SentimentAnchor
from users.models import Feedback, SentimanetAnalyze, EmployeeProfile
from users.forms import EmployeeCreationForm, EmployeeEditForm

from users.forms import SentimentAnchorForm
from users.views import get_analyzer

from django.views.decorators.http import require_POST
import openpyxl

@login_required(login_url='/users/login/')
def dashboard_view(request):
    user_company = request.user.profile.company
    
    today = timezone.now().date()
    fourteen_days_ago = today - timedelta(days=14)
    
    # ==========================================
    # 1. КЛЮЧЕВЫЕ МЕТРИКИ (KPI)
    # ==========================================
    total_reviews_today = Feedback.objects.filter(
        company=user_company, 
        created_at__date=today
    ).count()
    
    avg_sentiment = SentimanetAnalyze.objects.filter(
        feedback__company=user_company, 
        type='FINAL'                    
    ).aggregate(avg_val=Avg('value'))['avg_val']
    
    avg_index = int(avg_sentiment * 100) if avg_sentiment is not None else 0
        
    critical_count = SentimanetAnalyze.objects.filter(
        Q(value__lt=-0.5) | Q(meta_data__status__icontains="SARCASM"),
        feedback__company=user_company,
        type='FINAL'
    ).count()

    # ==========================================
    # 2. ПОДГОТОВКА ДАННЫХ ДЛЯ ГРАФИКОВ
    # ==========================================
    base_qs = SentimanetAnalyze.objects.filter(
        type='FINAL',                   
        feedback__company=user_company, 
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
    daily_stats = base_qs.annotate(date=TruncDate('feedback__created_at')) \
        .values('date') \
        .annotate(
            pos_count=Count('id', filter=Q(value__gt=0.2)),
            neg_count=Count('id', filter=Q(value__lt=-0.2))
        ).order_by('date')

    trend_labels = []
    trend_positive = []
    trend_negative = []

    for stat in daily_stats:
        if stat['date']:
            formatted_date = stat['date'].strftime('%d %b')
            trend_labels.append(formatted_date)
            trend_positive.append(stat['pos_count'])
            trend_negative.append(stat['neg_count'])

    trend_data = {
        'labels': trend_labels,
        'positive': trend_positive,
        'negative': trend_negative
    }

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
    user_company = request.user.profile.company

    all_feedbacks = Feedback.objects.filter(company=user_company)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    selected_source = request.GET.get('source_filter')
    selected_tag = request.GET.get('tag_filter')
    selected_search = request.GET.get('search_query')
    selected_rating = request.GET.get('rating_filter')

    if date_from:
        all_feedbacks = all_feedbacks.filter(created_at__date__gte=date_from)
        
    if date_to:
        all_feedbacks = all_feedbacks.filter(created_at__date__lte=date_to)
        
    if selected_source:
        all_feedbacks = all_feedbacks.filter(platform__name=selected_source)
    if selected_tag:
        all_feedbacks = all_feedbacks.filter(category__icontains=selected_tag)
    if selected_search:
        all_feedbacks = all_feedbacks.filter(text__icontains=selected_search)
    if selected_rating and selected_rating.isdigit():
        all_feedbacks = all_feedbacks.filter(rating__gte=float(selected_rating))

    all_feedbacks = all_feedbacks.order_by('-created_at')

    paginator = Paginator(all_feedbacks, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    feedback_ids = [feedback.id for feedback in page_obj]

    sentiments = SentimanetAnalyze.objects.filter(
        feedback_id__in=feedback_ids, 
        type='FINAL'
    ).values('feedback_id', 'value')

    sentiment_map = {item['feedback_id']: item['value'] for item in sentiments}

    for feedback in page_obj:
        feedback.sentiment_value = sentiment_map.get(feedback.id, 0.0)

    context = {
        'page_obj': page_obj,
        'platforms': Platform.objects.filter(is_active=True)
    }

    return render(request, 'main/feed.html', context)

@login_required(login_url='/users/login/')
def config(request):
    if not hasattr(request.user, 'profile'):
        return render(request, 'main/config.html', {'page_obj': [], 'form': EmployeeCreationForm()})

    user_company = request.user.profile.company

    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                new_user = form.save()
                
                EmployeeProfile.objects.create(
                    user=new_user,
                    company=user_company, 
                    phone=form.cleaned_data.get('phone', ''),
                    slug=new_user.username 
                )
            return redirect('config') 
    else:
        form = EmployeeCreationForm()

    all_users = User.objects.filter(profile__company=user_company)

    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    sort_date = request.GET.get('sort_date', '-date_joined')

    if search_query:
        all_users = all_users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(profile__phone__icontains=search_query)
        )
    if role_filter == 'admin':
        all_users = all_users.filter(is_superuser=True)
    elif role_filter == 'manager':
        all_users = all_users.filter(is_staff=True, is_superuser=False)
    elif role_filter == 'user':
        all_users = all_users.filter(is_staff=False, is_superuser=False)

    if status_filter == 'active':
        all_users = all_users.filter(is_active=True)
    elif status_filter == 'inactive':
        all_users = all_users.filter(is_active=False)

    if sort_date in ['date_joined', '-date_joined']:
        all_users = all_users.order_by(sort_date)
    else:
        all_users = all_users.order_by('-date_joined')

    paginator = Paginator(all_users, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form 
    }
    return render(request, 'main/config.html', context)

@login_required(login_url='/users/login/')
def delete_employee(request, user_id):
    if request.method == 'POST':
        user_company = request.user.profile.company

        user_to_delete = get_object_or_404(User, id=user_id, profile__company=user_company)

        if user_to_delete.id == request.user.id:
            return redirect('config')

        user_to_delete.delete()

    return redirect('config')


@login_required(login_url='/users/login/')
def edit_employee(request, user_id):
    user_company = request.user.profile.company
    
    user_to_edit = get_object_or_404(User, id=user_id, profile__company=user_company)

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            return redirect('config')
    else:
        form = EmployeeEditForm(instance=user_to_edit)

    context = {
        'form': form,
        'user_to_edit': user_to_edit
    }
    return render(request, 'main/edit_user.html', context)

@login_required(login_url='/users/login/')
def dictionary_view(request):
    if request.method == 'POST':
        form = SentimentAnchorForm(request.POST)
        if form.is_valid():
            form.save()
            
            try:
                analyzer = get_analyzer()
                analyzer.reload_anchors()
            except NameError:
                print("Функция get_analyzer не импортирована. Перезапустите сервер вручную.")
                
            return redirect('dictionary')
    else:
        form = SentimentAnchorForm()

    anchors = SentimentAnchor.objects.all().order_by('-created_at')

    search_query = request.GET.get('search', '')
    sentiment_filter = request.GET.get('sentiment', '')
    language_filter = request.GET.get('language', '')  
    status_filter = request.GET.get('status', '')

    if search_query:
        anchors = anchors.filter(text__icontains=search_query)
    
    if sentiment_filter:
        anchors = anchors.filter(sentiment=sentiment_filter)

    if language_filter:
        anchors = anchors.filter(language=language_filter)
        
    if status_filter == 'active':
        anchors = anchors.filter(is_active=True)
    elif status_filter == 'inactive':
        anchors = anchors.filter(is_active=False)

    paginator = Paginator(anchors, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sentiment_filter': sentiment_filter,
        'language_filter': language_filter, 
        'status_filter': status_filter,
        'form': form, 
    }
    return render(request, 'main/dictionary.html', context)

@login_required(login_url='/users/login/')
@require_POST
def delete_anchor(request, pk):
    anchor = get_object_or_404(SentimentAnchor, pk=pk)
    anchor.delete()
    
    try:
        analyzer = get_analyzer()
        analyzer.reload_anchors()
    except Exception as e:
        print(f"Ошибка обновления словаря: {e}")
        
    return redirect('dictionary')

@login_required(login_url='/users/login/')
@require_POST
def edit_anchor(request, pk):
    anchor = get_object_or_404(SentimentAnchor, pk=pk)
    
    form = SentimentAnchorForm(request.POST, instance=anchor)
    
    if form.is_valid():
        form.save()
        
        try:
            analyzer = get_analyzer()
            analyzer.reload_anchors()
        except Exception as e:
            print(f"Ошибка обновления словаря: {e}")
            
    return redirect('dictionary')



@login_required(login_url='/users/login/')
@require_POST
def import_anchors(request):
    excel_file = request.FILES.get('excel_file')
    
    # Базовая валидация
    if not excel_file or not excel_file.name.endswith('.xlsx'):
        messages.error(request, "Ошибка: Пожалуйста, загрузите файл формата .xlsx")
        return redirect('dictionary')

    try:
        # Читаем Excel файл напрямую из оперативной памяти (без сохранения на диск)
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        sheet = wb.active
        
        new_anchors = []
        valid_sentiments = ['POSITIVE', 'NEGATIVE']
        
        # Начинаем со 2-й строки (min_row=2), так как в 1-й строке будут заголовки
        for row in sheet.iter_rows(min_row=2, values_only=True):
            text = row[0]
            sentiment = row[1]
            language = row[2] if len(row) > 2 and row[2] else 'ru' 
            
            # Если строка не пустая и тональность указана верно
            if text and sentiment in valid_sentiments:
                new_anchors.append(SentimentAnchor(
                    text=str(text).strip(),
                    sentiment=str(sentiment).strip().upper(),
                    language=str(language).strip().lower()
                ))

        # Массовое сохранение (ignore_conflicts=True пропустит слова, которые уже есть в базе)
        if new_anchors:
            SentimentAnchor.objects.bulk_create(new_anchors, ignore_conflicts=True)
            
            analyzer = get_analyzer()
            analyzer.reload_anchors()
            
            messages.success(request, f"Успешно обработано {len(new_anchors)} слов. Словарь ИИ обновлен.")
        else:
            messages.warning(request, "Файл пуст или данные не соответствуют формату.")
            
    except Exception as e:
        messages.error(request, f"Произошла ошибка при чтении файла: {e}")

    return redirect('dictionary')