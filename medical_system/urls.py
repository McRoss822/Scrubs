from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Імпортуємо вбудовані view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- URL-адреси Автентифікації ---
    
    # 1. Сторінка входу (Login)
    # Використовує вбудований LoginView, але з нашим кастомним шаблоном
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='login.html'
    ), name='login'),
    
    # 2. Сторінка виходу (Logout)
    # Використовує вбудований LogoutView. 
    # (Після виходу він перенаправить на LOGOUT_REDIRECT_URL з settings.py)
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # --- URL-адреси нашого додатку ---
    
    # Підключаємо всі URL з файлу clinic/urls.py
    path('', include('clinic.urls')),
]
