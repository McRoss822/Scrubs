from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User, Patient

class PatientRegisterForm(UserCreationForm):
    """
    Кастомна форма реєстрації, яка створює
    і User, і Patient профіль.
    """
    # Ці поля форми будуть в self.cleaned_data
    email = forms.EmailField(required=True, label="Ел. пошта")
    first_name = forms.CharField(required=True, label="Ім'я")
    last_name = forms.CharField(required=True, label="Прізвище")
    phone_number = forms.CharField(required=True, label="Номер телефону")
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Дата народження")

    class Meta(UserCreationForm.Meta):
        model = User
        
        # --- КРИТИЧНЕ ВИПРАВЛЕННЯ ---
        # UserCreationForm за замовчуванням обробляє 'username' та 'password'.
        # Вказуючи 'username', ми дотримуємось стандарту, не створюючи
        # конфлікту з полями, які ми визначили вище.
        fields = ('username',)

    @transaction.atomic # Гарантує, що або обидва об'єкти створяться, або жоден
    def save(self, commit=True):
        """
        Зберігаємо User, потім створюємо Patient.
        """
        # 1. Створюємо User (лише з username/password)
        user = super().save(commit=False) 
        
        # 2. Додаємо дані з cleaned_data
        user.role = User.Role.PATIENT # Встановлюємо роль
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        
        if commit:
            # 3. Зберігаємо User
            user.save()
            
            # 4. Створюємо Patient профіль
            # Тепер cleaned_data гарантовано містить ці поля
            Patient.objects.create(
                user=user, 
                phone_number=self.cleaned_data.get('phone_number'),
                date_of_birth=self.cleaned_data.get('date_of_birth')
            )
            
        return user