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
from .tasks import analyze_feedback_task
from .decorators import require_role



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





