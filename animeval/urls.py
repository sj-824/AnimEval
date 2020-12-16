from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name = 'homepage'),
    path('login',views.Login.as_view(),name = 'login'),
    path('signup',views.UserCreate.as_view(),name = 'signup'),
    path('create_profile',views.create_profile,name = 'create_profile'),
    path('logout',views.Logout.as_view(),name = 'logout'),
    path('home',views.home,name = 'home'),
    path('profile/<int:pk>',views.profile, name = 'profile'),
    path('create_question', views.create_question, name = 'create_question'),
    path('create_article', views.create_article, name = 'create_article'),
]