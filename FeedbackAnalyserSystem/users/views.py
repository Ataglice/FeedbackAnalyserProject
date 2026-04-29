from django.shortcuts import render, get_object_or_404, redirect
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from .permissions import HasCompanyAPIKey
from .models import CompanyAPIKey
from rest_framework import generics
from .models import Feedback, SentimanetAnalyze, Platform
from api.serializers import DataRecordSerializer
from analyser.AnalyzerPipeline import SentimentAnalyzer
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .tasks import analyze_feedback_task
from .decorators import require_role
from rest_framework.views import APIView
from users.models import Company
from rest_framework.response import Response
from rest_framework import status



def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect("select_company")
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("select_company")
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



class ExternalIntegrationView(APIView):
    permission_classes = [] 

    def post(self, request):
        # 1. Проверка API ключа
        api_key = request.headers.get('X-API-Key') or request.data.get('api_key')
        
        if not api_key:
            return Response({"error": "Missing API Key. Provide 'X-API-Key' in headers."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            key_record = CompanyAPIKey.objects.get_from_key(api_key)
            target_company = key_record.company
        except (CompanyAPIKey.DoesNotExist, Exception):
            return Response({"error": "Invalid API Key"}, status=status.HTTP_403_FORBIDDEN)

        # 2. Получение данных из тела запроса
        text = request.data.get('text')
        author = request.data.get('author_name', 'Аноним')
        external_id = request.data.get('external_id')
        platform_name = request.data.get('platform', 'WordPress Site')
        rating = request.data.get('rating')
        review_link = request.data.get('link')
        category = request.data.get('category')

        if not text:
            return Response({"error": "Field 'text' is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            platform_obj = Platform.objects.get(name=platform_name)
        except Platform.DoesNotExist:
            return Response(
                {"error": f"Platform '{platform_name}' does not exist. Please create it in the database first."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        new_feedback = Feedback.objects.create(
            company=target_company,
            text=text,
            external_id=external_id,
            platform=platform_obj,
            rating=rating,
            category=category,
            source_url=review_link, 
            meta_data={"author_name": author} 
        )

        analyze_feedback_task.delay(new_feedback.id)

        return Response({
            "status": "success", 
            "message": "Feedback accepted",
            "feedback_id": new_feedback.id
        }, status=status.HTTP_201_CREATED)

