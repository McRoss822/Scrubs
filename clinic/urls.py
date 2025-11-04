from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка
    path('', views.home_view, name='home'),
    
    # Сторінка реєстрації
    path('register/', views.register_view, name='register'),
]
