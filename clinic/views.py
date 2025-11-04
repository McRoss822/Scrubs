from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import PatientRegisterForm

# (Ваші старі імпорти, якщо вони там були)
# ...

def home_view(request):
    """
    Рендерить головну сторінку.
    """
    return render(request, 'home.html')

def register_view(request):
    """
    Рендерить сторінку реєстрації пацієнта.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save() # Наша кастомна форма створює User + Patient
            login(request, user) # Автоматично логінимо користувача
            return redirect('home') # Перенаправляємо на головну
    else:
        form = PatientRegisterForm()
        
    return render(request, 'register.html', {'form': form})

# ----------
# Примітка:
# Логіку для LoginView та LogoutView ми пропишемо прямо в urls.py,
# оскільки вони вбудовані в Django і не вимагають коду у views.py.
# ----------
