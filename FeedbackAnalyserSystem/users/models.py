from django.db import models
from django.contrib.auth.models import User 
from django.core.validators import MinValueValidator, MaxValueValidator

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
        return f"{self.source_id} - {self.external_id}"
    
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
 
