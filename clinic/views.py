from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models # Потрібно для Q

from .forms import PatientRegisterForm
from .models import Doctor, Specialty, TimeSlot, Patient, Appointment, User 
from .services import BookingService

def home_view(request):
    """
    Рендерить головну сторінку.
    Шлях: home.html
    """
    return render(request, 'home.html', {})

def register_view(request):
    """
    Рендерить сторінку реєстрації пацієнта.
    Шлях: register.html
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Ви успішно зареєструвалися!')
            return redirect('home')
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')
    else:
        form = PatientRegisterForm()
        
    return render(request, 'register.html', {'form': form})

def doctor_list_view(request):
    """
    Рендерить сторінку зі списком лікарів.
    Шлях: doctor_list.html
    """
    specialties = Specialty.objects.all()
    doctors_query = Doctor.objects.select_related('user', 'specialty').all()
    
    selected_specialty_id = request.GET.get('specialty')
    
    if selected_specialty_id:
        doctors_query = doctors_query.filter(specialty__id=selected_specialty_id)
    
    context = {
        'doctors': doctors_query,
        'specialties': specialties,
        'selected_specialty_id': selected_specialty_id,
    }
    
    return render(request, 'doctor_list.html', context)


def doctor_detail_view(request, doctor_id):
    """
    Показує детальний профіль лікаря та його доступні слоти.
    Шлях: doctor_detail.html
    """
    doctor = get_object_or_404(Doctor.objects.select_related('user', 'specialty'), pk=doctor_id)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Будь ласка, увійдіть, щоб забронювати прийом.')
            return redirect('login')
        
        # --- СТАНДАРТИЗОВАНА ПЕРЕВІРКА ---
        # Використовуємо той самий надійний метод, що і в patient_dashboard
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
             messages.error(request, 'Лише пацієнти можуть бронювати прийоми.')
             return redirect('doctor_detail', doctor_id=doctor.pk)
        
        # --- Кінець перевірки ---
        
        time_slot_id = request.POST.get('time_slot_id')
        
        try:
            BookingService.create_appointment(patient=patient, time_slot_id=time_slot_id)
            messages.success(request, 'Ви успішно записані на прийом!')
            
        except BookingService.BookingError as e:
            messages.error(request, f'Помилка бронювання: {e}')
        
        return redirect('doctor_detail', doctor_id=doctor.pk)

    available_slots = TimeSlot.objects.filter(
        doctor=doctor, 
        is_available=True,
        start_time__gte=timezone.now()
    ).order_by('start_time')
    
    context = {
        'doctor': doctor,
        'available_slots': available_slots
    }
    return render(request, 'doctor_detail.html', context)

@login_required
def patient_dashboard_view(request):
    """
    Особистий кабінет пацієнта.
    Шлях: patient_dashboard.html
    
    --- НАДІЙНА ПЕРЕВІРКА ---
    """
    try:
        # Намагаємося отримати профіль пацієнта, 
        # пов'язаний з поточним залогіненим користувачем
        patient = Patient.objects.get(user=request.user)
        
    except Patient.DoesNotExist:
        # Якщо профіль не знайдено (або це Адмін, або Лікар)
        messages.error(request, 'Ця сторінка доступна лише для пацієнтів.')
        return redirect('home')

    # --- Кінець перевірки ---

    now = timezone.now()
    
    appointments = Appointment.objects.filter(patient=patient).select_related(
        'doctor__user', 'time_slot'
    ).order_by('time_slot__start_time')
    
    future_appointments = appointments.filter(time_slot__start_time__gte=now)
    
    # --- ОСЬ ТУТ ВИПРАВЛЕНО ---
    # Додано знак '='
    past_appointments = appointments.filter(time_slot__start_time__lt=now)
    
    context = {
        'future_appointments': future_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'patient_dashboard.html', context)