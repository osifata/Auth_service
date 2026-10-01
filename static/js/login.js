const form = document.getElementById("loginForm");
const message = document.getElementById("message");
const captchaQuestion = document.getElementById("captchaQuestion");

function showMessage(text, type = "error") {
    message.textContent = text;
    message.className = `message ${type}`;
}

function clearErrors() {
    document.querySelectorAll(".error").forEach(el => {
        el.textContent = "";
    });
}

function setError(id, text) {
    document.getElementById(id).textContent = text;
}

async function refreshCaptcha() {
    // Сервер генерирует новую CAPTCHA при следующем GET страницы.
    // Для API-ответов CAPTCHA уже заменяется в сессии.
    // Получаем новую страницу и извлекаем новый вопрос.
    const response = await fetch("/login.html", {
        headers: {"X-Requested-With": "XMLHttpRequest"}
    });
    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const question = doc.getElementById("captchaQuestion");
    if (question) {
        captchaQuestion.textContent = question.textContent.trim();
    }
}

if (registrationSuccess) {
    showMessage("Регистрация успешна! Войдите в систему.", "success");
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    message.className = "message hidden";

    const login = document.getElementById("login").value.trim();
    const password = document.getElementById("password").value;
    const captcha = document.getElementById("captcha").value.trim();

    let valid = true;

    if (!login) {
        setError("loginError", "Введите логин или email.");
        valid = false;
    }

    if (!password) {
        setError("passwordError", "Введите пароль.");
        valid = false;
    }

    // Важное требование задания:
    // если CAPTCHA не заполнена, запрос не отправляется.
    if (!captcha) {
        setError("captchaError", "Введите ответ капчи.");
        valid = false;
    }

    if (!valid) {
        return;
    }

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({login, password, captcha})
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = "/profile.html";
            return;
        }

        showMessage(data.message, "error");
        document.getElementById("captcha").value = "";
        await refreshCaptcha();
    } catch (error) {
        showMessage("Ошибка соединения с сервером.", "error");
        await refreshCaptcha();
    }
});
