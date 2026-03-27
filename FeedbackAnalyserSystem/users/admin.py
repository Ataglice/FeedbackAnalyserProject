from django.contrib import admin
from .models import User, Feedback, SentimanetAnalyze



class MemberAdmin(admin.ModelAdmin):
  list_display = ("firstname", "lastname", "phone")
  prepopulated_fields = {"slug": ("firstname", "lastname")}
  
  
admin.site.register(User, MemberAdmin)
admin.site.register(Feedback)
admin.site.register(SentimanetAnalyze)