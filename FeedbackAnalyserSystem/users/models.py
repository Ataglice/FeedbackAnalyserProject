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

    users = models.ManyToManyField(
        User, 
        through='CompanyMember', 
        related_name='companies'
    )

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
    phone = models.CharField(max_length=20, null=True, blank=True)
    slug = models.SlugField(default="", null=False)

    def __str__(self):
        return f"Профиль: {self.user.username}"
    
class CompanyMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='manager')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'company')
        verbose_name = "Сотрудник компании"
        verbose_name_plural = "Сотрудники компаний"

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
    source_url = models.URLField(max_length=500, null=True, blank=True, verbose_name="Ссылка на источник")
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

    is_manual = models.BooleanField(default=False, verbose_name="Ручная правка")
    
    edited_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='edited_sentiments'
    )

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
    

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('INFO', 'Информация'),
        ('SUCCESS', 'Успех'),
        ('WARNING', 'Внимание'),
        ('CRITICAL', 'Критическое'),
    )

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name='Пользователь'
    )
    

    company = models.ForeignKey(
        'Company', 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True, 
        blank=True,
        verbose_name='Компания'
    )
    

    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='INFO', verbose_name='Тип')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ссылка для перехода')
    
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at'] 
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self):
        return f"[{self.get_type_display()}] {self.user.username} - {self.title}"
    

class NotificationSetting(models.Model):
    company = models.OneToOneField(
        'Company', 
        on_delete=models.CASCADE, 
        related_name='notification_settings'
    )
    
    is_in_app_enabled = models.BooleanField(default=True, verbose_name="Внутренние уведомления (Колокольчик)")
    is_telegram_enabled = models.BooleanField(default=False, verbose_name="Уведомления в Telegram")
    is_email_enabled = models.BooleanField(default=False, verbose_name="Уведомления в Email")
    
    critical_threshold = models.FloatField(default=-0.5, verbose_name="Порог критического негатива")
    

    telegram_bot_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Токен Telegram бота клиента")
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID Telegram чата")
    
    custom_emails = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Дополнительные Email",
        help_text="Укажите email-адреса через запятую (например: boss@mail.ru, qc@mail.ru)"
    )

    alert_template = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Шаблон уведомления",
        help_text="Доступные переменные: {company}, {platform}, {score}, {text}, {link}"
    )

    class Meta:
        verbose_name = "Настройки уведомлений"
        verbose_name_plural = "Настройки уведомлений"

    def __str__(self):
        return f"Настройки: {self.company.name}"