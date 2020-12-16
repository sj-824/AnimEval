from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (LoginView, LogoutView)
from .forms import LoginForm, UserCreateForm
from .models import User
from bs4 import BeautifulSoup as bs4
import requests
# Create your views here.

class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'login.html'

class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'homepage.html'
    # model = ProfileModel

class UserCreate(generic.CreateView):
    form_class = UserCreateForm
    success_url = reverse_lazy('create_profile')
    template_name = 'signup.html'

    def form_valid(self,form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username = username, password = password)
        login(self.request,user)
        return response

class UserDelete(LoginRequiredMixin, generic.View):
    def get(self, *args, **kwargs):
        user = User.objects.get(username = self.request.user.username)
        user.is_active = False
        user.save()
        logout(self.request)
        return render(self.request,'user_delete.html')

def homepage(request):
    return render(request,'homepage.html')

def create_profile(request):
    if request.method == 'POST':
        form = CreateProfile(request.POST)
        if form.is_valid():
            object = form.save(commit = False)
            object.username = request.user
            object.save()
            return redirect('home')
    else:
        form = CreateProfile
    return render(request,'create_profile.html',{'form' : form})

def home(request):
    return render(request,'home.html')

def create_question(request):
    if request.method == 'POST':
        form = CreateQuestion(request.POST)
        nickname = ProfileModel.objects.filter(username = request.user)
        if form.is_valid():
            object = form.save()
            object.username = request.user
            object.nickname = nickname
            object.save()
            return redirect('home')
    else:
        form = CreateQuestion
    return render(request,'create_question.html',{'form' : form})

def profile(request,pk):
    profile_list = ProfileModel.objects.get(pk = pk)
    print(profile_list)
    article_list = ArticleModel.objects.filter(username = profile_list.username)
    question_list = QuestionModel.objects.filter(username = profile_list.username)
    return render(request, 'profile.html', {'profile_list' : profile_list, 'article_list' : article_list, 'question_list' : question_list})


