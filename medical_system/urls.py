from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- URL'и Веб-додатку (з clinic/urls.py) ---
    path('', include('clinic.urls')), 
    
    # --- URL'и Автентифікації (вбудовані в Django) ---
    # Використовує 'login.html' та 'logout.html' з вашої папки /templates
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- URL'и API (з clinic/api_urls.py) ---
    # Всі API-адреси будуть починатися з /api/v1/
    path('api/v1/', include('clinic.api_urls')),
]