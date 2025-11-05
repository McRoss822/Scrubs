from rest_framework.routers import DefaultRouter
from . import api_viewsets

# Створюємо роутер
router = DefaultRouter()

# Реєструємо наші ViewSets
# Роутер автоматично згенерує URL'и:
# /specialties/
# /specialties/<id>/
# /doctors/
# /doctors/<id>/
# /appointments/
# /appointments/<id>/

router.register(r'specialties', api_viewsets.SpecialtyViewSet, basename='specialty')
router.register(r'doctors', api_viewsets.DoctorViewSet, basename='doctor')
router.register(r'appointments', api_viewsets.AppointmentViewSet, basename='appointment')

# urlpatterns - це те, що ми імпортуємо в головний urls.py
urlpatterns = router.urls