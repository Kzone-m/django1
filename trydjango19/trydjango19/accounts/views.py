from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, get_user_model, login, logout
from .forms import UserLoginForm, UserRegisterForm


def login_view(request):
    # print(request.user.is_authenticated())

    next = request.GET.get('next')
    title = 'Login'
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(request, user)
        print(request.user.is_authenticated())
        # redirect
        if next:
            return redirect(next)
        return redirect('/')
    d = {
        'form': form,
        'title': title
    }
    return render(request, 'form.html', d)


def register_view(request):
    # このページがリクエストされた瞬間に読み込まれる
    # print(request.user.is_authenticated())

    next = request.GET.get('next')
    title = 'Register'
    form = UserRegisterForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        user.set_password(password)
        user.save()

        new_user = authenticate(username=user.username, password=password)
        login(request, new_user)
        # redirect
        if next:
            return redirect(next)
        return redirect('/')

    d = {
        'form': form,
        'title': title
    }
    return render(request, 'form.html', d)


def logout_view(request):
    logout(request)
    return render(request, 'form.html', {})

