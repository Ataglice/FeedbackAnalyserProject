from django.shortcuts import render, get_object_or_404, redirect
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout

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