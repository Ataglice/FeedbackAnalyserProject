from django.shortcuts import render, get_object_or_404, redirect
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from .permissions import HasCompanyAPIKey
from .models import CompanyAPIKey
from rest_framework import generics
from .models import Feedback, SentimanetAnalyze
from api.serializers import DataRecordSerializer
from analyser.AnalyzerPipeline import SentimentAnalyzer
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from users.utils import send_sentiment_alert
from .tasks import analyze_feedback_task

'''
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
'''

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {"form": form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect("login")

nlp_analyzer = None

def get_analyzer():
    global nlp_analyzer
    if nlp_analyzer is None:
        print(">>> Загрузка AI-моделей в память... <<<")
        nlp_analyzer = SentimentAnalyzer()
    return nlp_analyzer


class DataRecordCreateView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = DataRecordSerializer
    permission_classes = [HasCompanyAPIKey]

    def perform_create(self, serializer):

        key = self.request.META.get("HTTP_AUTHORIZATION", "").split()[-1]
        
        try:
            # 3. ИДЕНТИФИКАЦИЯ: Находим компанию по этому ключу
            api_key_obj = CompanyAPIKey.objects.get_from_key(key)
            company = api_key_obj.company
        except CompanyAPIKey.DoesNotExist:
            raise PermissionDenied("Недействительный API ключ")
        
        feedback_instance = serializer.save(company=company)

        analyze_feedback_task.delay(feedback_instance.id)





