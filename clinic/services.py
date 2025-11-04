from django.utils import timezone
from .models import Appointment, TimeSlot, Doctor, Patient, User
from django.db.models import Count
import datetime

# --- 1. Патерн "Фасад" (Facade) ---
# Ми створюємо єдиний клас, який ховає за собою всю
# складну логіку процесу бронювання.

class BookingService:
    """
    Фасад для керування логікою бронювання.
    Ховає складність перевірок та створення запису.
    """
    
    class BookingError(Exception):
        """Спеціальний клас винятків для помилок бронювання."""
        pass

    @staticmethod
    def create_appointment(patient: Patient, time_slot_id: int) -> Appointment:
        """
        Головний метод для створення запису на прийом.
        
        Викликає помилку BookingError, якщо бронювання неможливе.
        """
        
        try:
            # 1. Знайти слот
            time_slot = TimeSlot.objects.select_related('doctor').get(id=time_slot_id)
        except TimeSlot.DoesNotExist:
            raise BookingService.BookingError("Обраний час недоступний.")

        # 2. Перевірити доступність слоту
        if not time_slot.is_available:
            raise BookingService.BookingError("Цей слот вже зайнято.")

        # 3. Перевірити, чи не минув час
        if time_slot.start_time < timezone.now():
            raise BookingService.BookingError("Неможливо забронювати час у минулому.")
            
        # 4. (Додаткова логіка) Перевірити, чи пацієнт не має іншого запису в цей час
        # ... (можна додати) ...

        # 5. Створення запису
        # Ми не змінюємо time_slot.is_available = False тут.
        # Це автоматично зробить метод .save() моделі Appointment,
        # який ми написали раніше!
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=time_slot.doctor,
            time_slot=time_slot
        )
        
        # 6. Відправка email
        # Ми НЕ робимо цього тут. Патерн "Спостерігач" (signals.py)
        # автоматично "почує", що цей запис створено, і відправить email.
        # Це зберігає наш сервіс чистим (Single Responsibility).
        
        return appointment
    
class ReportStrategy:
    """Абстрактний базовий клас для всіх стратегій звітів."""
    
    def generate(self, *args, **kwargs):
        """Метод, який запускає генерацію звіту."""
        raise NotImplementedError("Subclasses must implement this method.")

class DailyAppointmentsStrategy(ReportStrategy):
    """Стратегія 1: Кількість прийомів за день."""
    
    def generate(self, date: datetime.date):
        count = Appointment.objects.filter(
            time_slot__start_time__date=date,
            status=Appointment.Status.COMPLETED
        ).count()
        return {"report_type": "Daily Appointments", "date": date, "count": count}

class DoctorLoadStrategy(ReportStrategy):
    """Стратегія 2: Статистика завантаженості лікарів."""
    
    def generate(self, start_date: datetime.date, end_date: datetime.date):
        load = Doctor.objects.annotate(
            completed_appointments=Count('appointments', filter=models.Q(
                appointments__time_slot__start_time__date__range=(start_date, end_date),
                appointments__status=Appointment.Status.COMPLETED
            ))
        ).values('user__first_name', 'user__last_name', 'completed_appointments')
        
        return {"report_type": "Doctor Load", "period": (start_date, end_date), "load": list(load)}

class NewPatientsStrategy(ReportStrategy):
    """Стратегія 3: Динаміка нових пацієнтів."""
    
    def generate(self, start_date: datetime.date, end_date: datetime.date):
        count = Patient.objects.filter(
            user__date_joined__date__range=(start_date, end_date)
        ).count()
        return {"report_type": "New Patients", "period": (start_date, end_date), "new_patients_count": count}


class ReportGenerator:
    """
    Клас "Контекст", який використовує обрану стратегію.
    """
    def __init__(self, strategy: ReportStrategy):
        self._strategy = strategy
        
    def set_strategy(self, strategy: ReportStrategy):
        self._strategy = strategy
        
    def run(self, *args, **kwargs):
        """Запускає генерацію звіту за допомогою обраної стратегії."""
        return self._strategy.generate(*args, **kwargs)
