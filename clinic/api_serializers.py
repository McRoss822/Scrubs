from rest_framework import serializers
from .models import User, Doctor, Patient, Specialty, Appointment, TimeSlot

# --- Serializers for User Profiles ---

class UserSerializer(serializers.ModelSerializer):
    """Серіалізатор для базової моделі User (для відображення в профілях)"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class PatientSerializer(serializers.ModelSerializer):
    """Серіалізатор для профілю Пацієнта"""
    user = UserSerializer(read_only=True) # Вкладений серіалізатор
    
    class Meta:
        model = Patient
        fields = ['user', 'phone_number', 'date_of_birth']

class SpecialtySerializer(serializers.ModelSerializer):
    """Серіалізатор для Спеціалізацій"""
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

class DoctorSerializer(serializers.ModelSerializer):
    """Серіалізатор для профілю Лікаря"""
    user = UserSerializer(read_only=True)
    # Використовуємо StringRelatedField для читабельного відображення
    specialty = serializers.StringRelatedField() 
    
    class Meta:
        model = Doctor
        # Використовуємо 'pk' замість 'id'
        fields = ['pk', 'user', 'specialty', 'bio']

# --- Serializers for Appointments ---

class TimeSlotSerializer(serializers.ModelSerializer):
    """Серіалізатор для слотів часу"""
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'is_available']

class AppointmentSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для Записів на прийом.
    Використовується для відображення існуючих записів.
    """
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'time_slot', 'status', 'created_at']

class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Спрощений серіалізатор ТІЛЬКИ для СТВОРЕННЯ запису.
    Пацієнт буде автоматично взятий з request.user.
    """
    time_slot = serializers.PrimaryKeyRelatedField(
        queryset=TimeSlot.objects.filter(is_available=True, start_time__gte=serializers.timezone.now())
    )
    
    class Meta:
        model = Appointment
        fields = ['time_slot'] # Пацієнт надасть лише ID слоту

    def create(self, validated_data):
        # Отримуємо пацієнта з контексту, який ми передамо у ViewSet
        patient = self.context['request'].user.patient
        
        # Використовуємо наш надійний BookingService для створення запису
        # Це гарантує, що ми дотримуємося патерну Фасад!
        from .services import BookingService
        
        try:
            appointment = BookingService.create_appointment(
                patient=patient,
                time_slot_id=validated_data['time_slot'].id
            )
            return appointment
        except BookingService.BookingError as e:
            # Перетворюємо помилку сервісу на помилку валідації DRF
            raise serializers.ValidationError(str(e))