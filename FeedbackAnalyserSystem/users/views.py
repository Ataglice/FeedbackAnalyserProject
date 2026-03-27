from django.shortcuts import render, get_object_or_404, redirect
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout

from rest_framework import generics
from .models import Feedback, SentimanetAnalyze
from api.serializers import DataRecordSerializer
from analyser.AnalyzerPipeline import SentimentAnalyzer
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def user(request):
    myusers = User.objects.all().values()
    context = {
        'myusers': myusers
    }
    return render(request, 'users/all_users.html', context)

def details(request, slug):
    myuser = get_object_or_404(User, slug=slug) 
    context = {
        'myuser': myuser 
    }
    return render(request, 'users/details.html', context)
  
def main(request):
    return render(request, 'users/main.html')

def testing(request):
    myusers = User.objects.all().values()
    context = {
        'myusers': myusers,
    }
    return render(request, 'users/template.html', context)

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect("users")
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("users")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {"form": form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect("users")

nlp_analyzer = SentimentAnalyzer()


class DataRecordCreateView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = DataRecordSerializer

    def perform_create(self, serializer):
        feedback_instance = serializer.save()
        text_to_analyze = feedback_instance.text

        result = nlp_analyzer.smart_analyze(text_to_analyze)

        type_data = result.get('type', {})
        overall_value = result.get('value', 0.0)

        for model_name, model_metrics in type_data.items():
            pos_val = 0.0
            neg_val = 0.0
            neu_val = 0.0
            
            # По умолчанию записываем общий итог (для Embed, так как он не выдает единый индекс в словаре)
            model_specific_value = overall_value 

            # ВЕТВЬ А: Если модель вернула словарь (Embed, VADER)
            if isinstance(model_metrics, dict):
                # Универсальное извлечение: ищет ключи Embed, если их нет — ищет ключи VADER
                pos_val = model_metrics.get('POSITIVE', model_metrics.get('pos', 0.0))
                neg_val = model_metrics.get('NEGATIVE', model_metrics.get('neg', 0.0))
                neu_val = model_metrics.get('NEUTRAL', model_metrics.get('neu', 0.0))
                
                # Если это VADER, извлекаем его конкретный итоговый коэффициент
                if model_name == "VADER":
                    model_specific_value = model_metrics.get('compound', overall_value)

            # ВЕТВЬ Б: Если модель вернула число (RuBERT, DistilBERT)
            elif isinstance(model_metrics, (float, int)):
                model_specific_value = float(model_metrics)
                
                # Конвертация числа в метрики (от -1.0 до 1.0)
                if model_metrics > 0:
                    pos_val = float(model_metrics)
                elif model_metrics < 0:
                    neg_val = abs(float(model_metrics))
                else:
                    neu_val = 1.0


            SentimanetAnalyze.objects.create(
                feedback=feedback_instance,
                type=model_name,
                positive_val=pos_val,
                negative_val=neg_val,
                neutral_val=neu_val,
                value=model_specific_value
            )