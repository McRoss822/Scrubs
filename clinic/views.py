from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models # Потрібно для Q
import datetime # --- ПОТРІБНО ДЛЯ СТВОРЕННЯ СЛОТІВ ---

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
        
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
             messages.error(request, 'Лише пацієнти можуть бронювати прийоми.')
             return redirect('doctor_detail', doctor_id=doctor.pk)
        
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
    """
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Ця сторінка доступна лише для пацієнтів.')
        return redirect('home')

    now = timezone.now()
    
    appointments = Appointment.objects.filter(patient=patient).select_related(
        'doctor__user', 'time_slot'
    ).order_by('time_slot__start_time')
    
    future_appointments = appointments.filter(time_slot__start_time__gte=now)
    past_appointments = appointments.filter(time_slot__start_time__lt=now)
    
    context = {
        'future_appointments': future_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'patient_dashboard.html', context)

# --- ОНОВЛЕНИЙ VIEW ---
@login_required
def doctor_dashboard_view(request):
    """
    Особистий кабінет лікаря.
    Дозволяє керувати розкладом та переглядати записи.
    Шлях: doctor_dashboard.html
    """
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Ця сторінка доступна лише для лікарів.')
        return redirect('home')

    # --- ЛОГІКА СТВОРЕННЯ СЛОТІВ (POST) ---
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')
            interval_min = int(request.POST.get('interval', 30))

            # 1. Парсимо дату і час
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time_obj = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            end_time_obj = datetime.datetime.strptime(end_time_str, '%H:%M').time()
            
            # 2. Перетворюємо на timezone-aware datetime
            current_dt = timezone.make_aware(datetime.datetime.combine(date_obj, start_time_obj))
            end_dt = timezone.make_aware(datetime.datetime.combine(date_obj, end_time_obj))
            interval = datetime.timedelta(minutes=interval_min)
            
            # 3. Перевірки
            if current_dt < timezone.now():
                raise ValueError("Неможливо створити слоти у минулому.")
            if end_dt <= current_dt:
                raise ValueError("Час закінчення має бути пізніше часу початку.")

            # 4. Цикл генерації слотів
            slots_created_count = 0
            while current_dt < end_dt:
                slot_end_time = current_dt + interval
                if slot_end_time > end_dt:
                    break # Не створюємо "обрізаний" слот
                
                # Перевірка на конфлікт (чи такий слот вже існує)
                exists = TimeSlot.objects.filter(
                    doctor=doctor,
                    start_time=current_dt
                ).exists()
                
                if not exists:
                    TimeSlot.objects.create(
                        doctor=doctor,
                        start_time=current_dt,
                        end_time=slot_end_time,
                        is_available=True
                    )
                    slots_created_count += 1
                
                current_dt = slot_end_time # Переходимо до наступного слоту
            
            if slots_created_count > 0:
                messages.success(request, f'Успішно додано {slots_created_count} нових слотів.')
            else:
                messages.info(request, 'Не було створено нових слотів (можливо, вони вже існують).')
                
        except Exception as e:
            messages.error(request, f'Помилка при створенні слотів: {e}')
        
        return redirect('doctor_dashboard')
    
    # --- ЛОГІКА ВІДОБРАЖЕННЯ (GET) ---
    now = timezone.now()
    
    appointments = Appointment.objects.filter(doctor=doctor).select_related(
        'patient__user', 'time_slot'
    ).order_by('time_slot__start_time')
    
    future_appointments = appointments.filter(time_slot__start_time__gte=now)
    past_appointments = appointments.filter(time_slot__start_time__lt=now)
    
    # Потрібно для 'min' атрибуту в формі
    today = timezone.localdate().strftime('%Y-%m-%d')
    
    context = {
        'doctor': doctor,
        'future_appointments': future_appointments,
        'past_appointments': past_appointments,
        'today': today, # Передаємо сьогоднішню дату в шаблон
    }
    return render(request, 'doctor_dashboard.html', context)