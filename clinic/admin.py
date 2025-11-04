from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Patient, Doctor, Specialty, TimeSlot, Appointment

# --- 1. Inline-конфігурації ---
# Це дозволяє редагувати профілі Patient/Doctor прямо на сторінці User

class PatientInline(admin.StackedInline):
    """
    Дозволяє редагувати профіль Пацієнта (Patient) 
    всередині сторінки Користувача (User).
    """
    model = Patient
    can_delete = False # Не можна видалити профіль, не видаляючи User
    verbose_name_plural = 'Профіль Пацієнта'
    fk_name = 'user'

class DoctorInline(admin.StackedInline):
    """
    Дозволяє редагувати профіль Лікаря (Doctor) 
    всередині сторінки Користувача (User).
    """
    model = Doctor
    can_delete = False
    verbose_name_plural = 'Профіль Лікаря'
    fk_name = 'user'

# --- 2. Кастомна Адмін-панель для User ---
# Ми розширюємо стандартну UserAdmin, щоб додати наші inlines

class CustomUserAdmin(UserAdmin):
    """
    Кастомна адмін-панель для User, яка відображає
    профіль Patient або Doctor в залежності від ролі.
    """
    # Додаємо 'role' до полів, що відображаються у списку
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    # Додаємо 'role' до полів, які можна редагувати на сторінці User
    # (потрібно розширити fieldsets)
    fieldsets = UserAdmin.fieldsets + (
        ('Додаткова Інформація', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Додаткова Інформація', {'fields': ('role',)}),
    )

    def get_inlines(self, request, obj=None):
        """
        Динамічно показує потрібний inline (Patient або Doctor)
        в залежності від ролі обраного користувача.
        """
        if not obj: # При створенні нового користувача
            return []
        if obj.role == User.Role.PATIENT:
            return (PatientInline,)
        if obj.role == User.Role.DOCTOR:
            return (DoctorInline,)
        return []

# --- 3. Адмін-панелі для інших моделей ---

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_time', 'end_time', 'is_available')
    list_filter = ('doctor', 'is_available', 'start_time')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'time_slot_display', 'status')
    list_filter = ('status', 'doctor', 'patient')
    search_fields = ('patient__user__first_name', 'doctor__user__first_name')
    
    # Допоміжний метод для красивого відображення time_slot
    def time_slot_display(self, obj):
        return str(obj.time_slot)
    time_slot_display.short_description = 'Час прийому'


# --- 4. Реєстрація моделей ---
# Спочатку "від'єднуємо" стандартний User (якщо він був зареєстрований)
# admin.site.unregister(User) # Це може бути не потрібно, якщо AbstractUser
# Реєструємо нашу кастомну модель User з кастомною адмін-панеллю
admin.site.register(User, CustomUserAdmin)

# Нам більше не потрібні окремі адмінки для Patient і Doctor,
# оскільки вони тепер редагуються всередині User.
# admin.site.register(Patient) # Коментуємо або видаляємо
# admin.site.register(Doctor) # Коментуємо або видаляємо
