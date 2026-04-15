from django.contrib import admin
from .models import Feedback, SentimanetAnalyze
from .models import Company, EmployeeProfile, Feedback, SentimanetAnalyze, Platform, SentimentAnchor
from rest_framework_api_key.admin import APIKeyModelAdmin
from .models import CompanyAPIKey
from users.models import CompanyMember



class MemberAdmin(admin.ModelAdmin):
  list_display = ("firstname", "lastname", "phone")
  prepopulated_fields = {"slug": ("firstname", "lastname")}
  
  
admin.site.register(Feedback)
admin.site.register(SentimanetAnalyze)
admin.site.register(Company)
admin.site.register(EmployeeProfile)
admin.site.register(Platform)
admin.site.register(SentimentAnchor)
admin.site.register(CompanyMember)

@admin.register(CompanyAPIKey)
class CompanyAPIKeyAdmin(APIKeyModelAdmin):
    pass