# Auth_service
## Практическое задание №2

### Сервис аутентификации с защитой от ботов

Веб-сервис регистрации и авторизации пользователей с математической CAPTCHA.
## Ссылка на сервис: https://auth-service-vrqr.onrender.com

### Дизайн
![Image](https://github.com/user-attachments/assets/f630615a-6ec5-430b-945d-330a4edd32d3)
![Image](https://github.com/user-attachments/assets/c032be52-f12d-4a94-9afb-0adb3dd2896d)
![Image](https://github.com/user-attachments/assets/0cb4bd54-1333-498e-94e8-d9f0425bfb4b)

### Структура проекта

```text
auth_service/
│
├── app.py
├── requirements.txt
├── README.md
├── users.db                  # создаётся автоматически
│
├── templates/
│   ├── login.html            # страница входа
│   ├── register.html         # страница регистрации
│   └── profile.html          # личный кабинет
│
└── static/
    │
    ├── css/
    │   └── style.css         # единый CSS для всех страниц
    │
    └── js/
        ├── login.js          # логика входа и CAPTCHA
        ├── register.js       # логика регистрации и валидации
        └── profile.js        # загрузка профиля и выход
