from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import UserLoginForm, UserRegisterForm


def login_view(request):
    title = 'Login Practice'
    form = UserLoginForm(request.POST or None)
    d = {
        'title': title,
        'form': form,
    }
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('practice1:success')
    return render(request, 'FormPractice/form_practice.html', d)


def register_view(request):
    title = 'Register Practice'
    form = UserRegisterForm(request.POST or None)
    d = {
        'title': title,
        'form': form,
    }
    if form.is_valid():
        user = form.save(commit=False)    # <class 'django.contrib.auth.models.User'>
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user.set_password(password)
        user.save()
        new_user = authenticate(username=username, password=password)
        login(request, new_user)
        return redirect('practice1:success')
    return render(request, 'FormPractice/form_practice.html', d)


def logout_view(request):
    logout(request)
    return redirect('practice1:login')


def success_view(request):
    return render(request, 'FormPractice/form_practice_success.html', {})
