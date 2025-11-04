from django.apps import AppConfig

class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic'

    def ready(self):
        """
        Цей метод викликається, коли додаток готовий.
        Ми імпортуємо сигнали тут, щоб "підключити" їх.
        """
        # Це повідомляє Django про існування файлу signals.py
        import clinic.signals