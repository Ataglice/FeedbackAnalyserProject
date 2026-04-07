from django import forms
from django.contrib.auth.models import User
from .models import EmployeeProfile

class EmployeeCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'mock-input w-100', 'placeholder': 'Пароль'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'mock-input w-100', 'placeholder': 'Email'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'mock-input w-100', 'placeholder': 'Телефон (необязательно)'}))
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('manager', 'Менеджер')
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'mock-input w-100'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'mock-input w-100', 'placeholder': 'Логин (Имя пользователя)'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Хешируем пароль 
        user.set_password(self.cleaned_data['password'])
        
        # Раздаем права
        if self.cleaned_data['role'] == 'manager':
            user.is_staff = True
            
        if commit:
            user.save()
        return user