from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка
    path('', views.home_view, name='home'),
    
    # Сторінка реєстрації
    path('register/', views.register_view, name='register'),

     # Cторінка списку лікарів
    path('doctors/', views.doctor_list_view, name='doctor_list'),

    path('doctor/<int:doctor_id>/', views.doctor_detail_view, name='doctor_detail'),

    # Особистий кабінет
    path('my-appointments/', views.patient_dashboard_view, name='patient_dashboard'),

    # --- НОВИЙ URL ---
    path('my-schedule/', views.doctor_dashboard_view, name='doctor_dashboard'),
]
