from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # Використовується для посилання на кастомну модель User

# --- 1. Кастомна Модель Користувача (User) ---
# Наслідуємо AbstractUser, щоб зберегти всі поля Django (login, password)
# і додати наше власне поле 'role'.

class User(AbstractUser):
    """
    Кастомна модель User, що розширює стандартну.
    Додає поле 'role' для розрізнення типів користувачів.
    """
    
    # Визначаємо ролі за допомогою TextChoices для надійності
    class Role(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Doctor'
        ADMIN = 'ADMIN', 'Admin'

    # 'role' - це поле з діаграми класів
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.PATIENT
    )

    # Допоміжні властивості для перевірки ролі (як у діаграмі)
    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_admin(self):
        # В Django, 'is_staff' контролює доступ до адмін-панелі
        return self.role == self.Role.ADMIN or self.is_staff

# --- 2. Модель Спеціалізації (Specialty) ---
class Specialty(models.Model):
    """
    Довідник медичних спеціалізацій.
    (Кардіолог, Стоматолог, тощо)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# --- 3. Модель Профілю Пацієнта (Patient) ---
# Зв'язок 1-до-1 з User
class Patient(models.Model):
    """
    Профіль Пацієнта з додатковою інформацією.
    Має зв'язок One-to-One з моделлю User.
    """
    # Використовуємо settings.AUTH_USER_MODEL для посилання на нашу кастомну модель User
    # primary_key=True означає, що зв'язок 1-до-1 є також і ID моделі
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True
    )
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Patient: {self.user.first_name} {self.user.last_name}"

# --- 4. Модель Профілю Лікаря (Doctor) ---
# Зв'язок 1-до-1 з User та 1-до-багатьох зі Specialty
class Doctor(models.Model):
    """
    Профіль Лікаря з додатковою інформацією.
    Має зв'язок One-to-One з User та ForeignKey до Specialty.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True
    )
    # Зв'язок "1-до-багатьох" зі Specialty (одна спеціальність - багато лікарів)
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL, # Не видаляти лікаря, якщо видалено спеціальність
        null=True
    )
    bio = models.TextField(blank=True, help_text="Коротка біографія лікаря")

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} ({self.specialty})"

# --- 5. Модель Слоту в Розкладі (TimeSlot) ---
class TimeSlot(models.Model):
    """
    Представляє доступний час у розкладі лікаря.
    (напр. Dr. Smith, 2025-11-10 10:00 - 10:30)
    """
    # Зв'язок "1-до-багатьох" з Doctor (один лікар - багато слотів)
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='time_slots' # Дозволяє легко отримати слоти з об'єкта лікаря
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    # 'is_available' з нашої діаграми
    is_available = models.BooleanField(default=True)

    class Meta:
        # Запобігаємо створенню однакових слотів для одного лікаря
        unique_together = ('doctor', 'start_time')
        ordering = ['start_time']

    def __str__(self):
        return f"{self.doctor} | {self.start_time.strftime('%Y-%m-%d %H:%M')}"

# --- 6. Модель Запису на прийом (Appointment) ---
# Центральний клас, що все пов'язує
class Appointment(models.Model):
    """
    Запис на прийом, що пов'язує Пацієнта, Лікаря та Слот.
    """
    
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Заплановано'
        COMPLETED = 'COMPLETED', 'Завершено'
        CANCELLED = 'CANCELLED', 'Скасовано'

    # Зв'язок "1-до-багатьох" з Patient
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    # Зв'язок "1-до-багатьох" з Doctor
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    # Зв'язок "1-до-1" з TimeSlot
    # Коли запис створено, цей слот стає 'is_available = False'
    time_slot = models.OneToOneField(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='appointment'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Методи з діаграми класів
    def cancel(self):
        self.status = self.Status.CANCELLED
        # Звільняємо слот назад
        self.time_slot.is_available = True
        self.time_slot.save()
        self.save()

    def complete(self):
        self.status = self.Status.COMPLETED
        self.save()

    def __str__(self):
        return f"Запис: {self.patient} до {self.doctor} на {self.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # Переконуємося, що слот позначено як "зайнятий" при створенні запису
        if self.pk is None: # Тільки при створенні нового запису
            if self.time_slot.is_available:
                self.time_slot.is_available = False
                self.time_slot.save()
            else:
                raise ValueError("Цей слот вже зайнятий")
        super().save(*args, **kwargs)
