%% Системна межа (прямокутник)
rectangle "Система запису до лікаря" {
    
    %% --- Публічні прецеденти ---
    useCase "Реєстрація" as UC_REG
    useCase "Автентифікація" as UC_AUTH
    useCase "Перегляд списку лікарів" as UC_VIEW_DOCS
    useCase "Перегляд спеціалізацій" as UC_VIEW_SPECS

    %% --- Прецеденти Пацієнта ---
    useCase "Запис на прийом" as UC_BOOK
    useCase "Скасування прийому" as UC_CANCEL
    useCase "Перегляд історії прийомів" as UC_HISTORY_PATIENT

    %% --- Прецеденти Лікаря ---
    useCase "Керування розкладом" as UC_MANAGE_SCHEDULE
    useCase "Перегляд свого розкладу" as UC_VIEW_SCHEDULE

    %% --- Прецеденти Адміністратора ---
    useCase "Керування Лікарями" as UC_ADMIN_DOCS
    useCase "Керування Пацієнтами" as UC_ADMIN_PATIENTS
    useCase "Перегляд Звітів" as UC_ADMIN_REPORTS
    
    %% --- Службовий прецедент ---
    useCase "Відправка нагадувань" as UC_NOTIFY
}

%% Зв'язки акторів з прецедентами

' Гість може виконувати публічні дії
Гість -- UC_REG
Гість -- UC_AUTH
Гість -- UC_VIEW_DOCS
Гість -- UC_VIEW_SPECS

' Пацієнт виконує дії, пов'язані з записами
Пацієнт -- UC_BOOK
Пацієнт -- UC_CANCEL
Пацієнт -- UC_HISTORY_PATIENT

' Лікар керує своїм розкладом
Лікар -- UC_MANAGE_SCHEDULE
Лікар -- UC_VIEW_SCHEDULE

' Адміністратор керує системою
Адміністратор -- UC_ADMIN_DOCS
Адміністратор -- UC_ADMIN_PATIENTS
Адміністратор -- UC_ADMIN_REPORTS

%% Зв'язки між прецедентами

' Усі дії, окрім публічних, вимагають автентифікації
' <<include>> означає обов'язкову дію
UC_BOOK ..> UC_AUTH : <<include>>
UC_CANCEL ..> UC_AUTH : <<include>>
UC_HISTORY_PATIENT ..> UC_AUTH : <<include>>
UC_MANAGE_SCHEDULE ..> UC_AUTH : <<include>>
UC_VIEW_SCHEDULE ..> UC_AUTH : <<include>>
UC_ADMIN_DOCS ..> UC_AUTH : <<include>>
UC_ADMIN_PATIENTS ..> UC_AUTH : <<include>>
UC_ADMIN_REPORTS ..> UC_AUTH : <<include>>

' Нагадування є опціональним розширенням для запису
' <<extend>> означає опціональну дію
UC_BOOK ..> UC_NOTIFY : <<extend>>

