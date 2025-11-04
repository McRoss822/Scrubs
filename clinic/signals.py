from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Appointment

# --- Патерн "Спостерігач" (Observer) ---
# Ми використовуємо вбудовані "Сигнали" Django.
# Модель Appointment - це "Суб'єкт" (Subject).
# Функція нижче - це "Спостерігач" (Observer).

@receiver(post_save, sender=Appointment)
def send_appointment_confirmation(sender, instance: Appointment, created: bool, **kwargs):
    """
    Ця функція автоматично викликається, коли об'єкт Appointment
    зберігається в базі даних.
    """
    
    # Ми реагуємо ТІЛЬКИ на перше створення запису
    if created:
        print(f"SIGNAL: Створено новий запис {instance.id}, відправка email...")
        
        patient = instance.patient
        doctor = instance.doctor
        
        # Готуємо email
        subject = f"Підтвердження запису до лікаря {doctor}"
        message = (
            f"Шановний(а) {patient.user.first_name},\n\n"
            f"Ви успішно записані на прийом до лікаря {doctor} "
            f"на {instance.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}.\n\n"
            "Дякуємо, що обрали нашу клініку!"
        )
        
        # Щоб це спрацювало, вам потрібно налаштувати email-бекэнд 
        # у вашому settings.py (наприклад, Gmail або SendGrid).
        # Для тестування можна використовувати ConsoleEmailBackend.
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL, # Ваш email (з settings.py)
                [patient.user.email],       # Email пацієнта
                fail_silently=False,
            )
            print(f"SIGNAL: Email успішно відправлено на {patient.user.email}")
        except Exception as e:
            # У реальному проекті тут має бути логування помилок
            print(f"SIGNAL ERROR: Не вдалося відправити email. Помилка: {e}")

# --- Налаштування email для тестування ---
# Щоб бачити email у вашій консолі (терміналі) без реальної відправки,
# додайте цей рядок у ваш medical_system/settings.py:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# DEFAULT_FROM_EMAIL = 'admin@myclinic.com'