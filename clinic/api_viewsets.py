from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Doctor, Specialty, Appointment
from .api_serializers import (
    DoctorSerializer, 
    SpecialtySerializer, 
    AppointmentSerializer,
    AppointmentCreateSerializer
)

# --- Дозволи (Permissions) ---

class IsPatientReadOnlyOrAuthenticatedCreate(permissions.BasePermission):
    """
    Дозвіл:
    - Читати (GET) може будь-хто.
    - Створювати (POST) може лише автентифікований Пацієнт.
    """
    def has_permission(self, request, view):
        # Дозволити GET, HEAD, OPTIONS запити (читання)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Дозволити POST, якщо користувач - Пацієнт
        return request.user.is_authenticated and request.user.is_patient

# --- ViewSets ---

class SpecialtyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для перегляду спеціалізацій.
    Лише читання (GET).
    """
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer

class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint для перегляду лікарів.
    Лише читання (GET).
    Дозволяє фільтрацію за ?specialty=ID
    """
    queryset = Doctor.objects.select_related('user', 'specialty').all()
    serializer_class = DoctorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['specialty'] # Дозволяє /api/v1/doctors/?specialty=1

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint для керування записами на прийом.
    - Пацієнти: можуть створювати (POST) та бачити СВОЇ записи (GET).
    - Інші: нічого не бачать.
    """
    permission_classes = [permissions.IsAuthenticated] # Тільки для залогінених

    def get_queryset(self):
        """
        Цей метод гарантує, що користувачі бачать лише те, що їм належить.
        """
        user = self.request.user
        if user.is_patient:
            # Пацієнти бачать лише свої записи
            return Appointment.objects.filter(patient__user=user)
        elif user.is_doctor:
            # Лікарі бачать лише свої записи
            return Appointment.objects.filter(doctor__user=user)
        elif user.is_staff:
            # Адміни бачать всі
            return Appointment.objects.all()
        return Appointment.objects.none() # Інші нічого не бачать

    def get_serializer_class(self):
        """
        Використовуємо різні серіалізатори для різних дій.
        - `AppointmentCreateSerializer` (простий) для 'create'.
        - `AppointmentSerializer` (детальний) для 'list', 'retrieve'.
        """
        if self.action == 'create':
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def get_serializer_context(self):
        """Передаємо об'єкт request у серіалізатор (для 'create')"""
        return {'request': self.request}