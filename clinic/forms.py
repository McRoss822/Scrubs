from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User, Patient

class PatientRegisterForm(UserCreationForm):
    """
    Кастомна форма реєстрації для Пацієнта.
    Створює User і пов'язаний з ним Patient.
    """
    # Додаємо поля, яких немає в UserCreationForm за замовчуванням
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    
    # Додаємо поля з моделі Patient
    phone_number = forms.CharField(max_length=20, required=True, label="Номер телефону")
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Дата народження")

    class Meta(UserCreationForm.Meta):
        model = User
        # Вказуємо, які поля User показувати у формі
        fields = ('username', 'first_name', 'last_name', 'email')

    @transaction.atomic # Гарантує, що обидві моделі створяться успішно
    def save(self, commit=True):
        # 1. Зберігаємо User
        user = super().save(commit=False)
        user.role = User.Role.PATIENT # Встановлюємо роль
        
        # Додаємо поля, які ми визначили вище
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        
        if commit:
            user.save()

        # 2. Зберігаємо пов'язаний Patient
        patient = Patient.objects.create(
            user=user,
            phone_number=self.cleaned_data.get('phone_number'),
            date_of_birth=self.cleaned_data.get('date_of_birth')
        )
        
        return user
