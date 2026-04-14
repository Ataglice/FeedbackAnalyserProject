from django.db import models
from django.contrib.auth.models import User 
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework_api_key.models import AbstractAPIKey

class Platform(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название платформы")
    code = models.SlugField(max_length=50, unique=True, verbose_name="Системный код")
    base_url = models.URLField(max_length=255, null=True, blank=True, verbose_name="Базовый URL")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Платформа"
        verbose_name_plural = "Платформы"

    def __str__(self):
        return f"{self.name} ({self.code})"

class Company(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    ]

    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=150)
    registr_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.name
    
class CompanyAPIKey(AbstractAPIKey):
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    
    class Meta(AbstractAPIKey.Meta):
        verbose_name = "API ключ компании"
        verbose_name_plural = "API ключи компаний"

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    phone = models.CharField(max_length=20, null=True, blank=True)
    slug = models.SlugField(default="", null=False)

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"

class Feedback(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='feedbacks')
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, related_name='feedbacks', null=True)
    external_id = models.CharField(max_length=100)
    text = models.TextField()
    category = models.CharField(max_length=100, null=True, blank=True)
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    send_time = models.DateTimeField(null=True, blank=True)
    meta_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        platform_name = self.platform.name if self.platform else "Нет платформы"
        return f"{platform_name} - {self.external_id}"
    
class SentimanetAnalyze(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='analyses')
    type = models.CharField(max_length=50)
    positive_val = models.FloatField()
    negative_val = models.FloatField()
    neutral_val = models.FloatField()
    value = models.FloatField()
    meta_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Analysis ({self.type}) for Feedback ID: {self.feedback_id}"
 
class SentimentAnchor(models.Model):
    SENTIMENT_CHOICES = [
        ('POSITIVE', 'Позитивный'),
        ('NEGATIVE', 'Негативный')
    ]
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'Английский'),
    ]

    text = models.CharField(max_length=255, verbose_name="Якорь (фраза/слово)")
    sentiment = models.CharField(max_length=15, choices=SENTIMENT_CHOICES, verbose_name="Тональность")
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='ru', verbose_name="Язык")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Словарный якорь"
        verbose_name_plural = "Словарные якоря"
        unique_together = ('text', 'language')
    
    def __str__(self):
        return f"[{self.sentiment}] {self.text} ({self.language})"
    
    @classmethod
    def get_anchors_as_dict(cls, target_language='ru'):
        anchors_dict = {'POSITIVE': [], 'NEGATIVE': [], 'NEUTRAL': []}
        
        active_anchors = cls.objects.filter(is_active=True, language=target_language)
        
        for anchor in active_anchors:
            if anchor.sentiment in anchors_dict:
                anchors_dict[anchor.sentiment].append(anchor.text)
                
        return {k: v for k, v in anchors_dict.items() if v}