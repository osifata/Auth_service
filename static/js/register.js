const form = document.getElementById("registerForm");
const message = document.getElementById("message");
const captchaQuestion = document.getElementById("captchaQuestion");

function clearErrors() {
    document.querySelectorAll(".error").forEach(el => {
        el.textContent = "";
    });
}

function setError(id, text) {
    document.getElementById(id).textContent = text;
}

function showMessage(text, type = "error") {
    message.textContent = text;
    message.className = `message ${type}`;
}

async function refreshCaptcha() {
    const response = await fetch("/register.html", {
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

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    message.className = "message hidden";

    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const passwordConfirm = document.getElementById("password_confirm").value;
    const captcha = document.getElementById("captcha").value.trim();

    let valid = true;

    // Клиентская валидация имени.
    if (!/^[A-Za-z0-9]{3,20}$/.test(username)) {
        setError(
            "usernameError",
            "Только латиница и цифры, от 3 до 20 символов."
        );
        valid = false;
    }

    // Клиентская проверка email на @ и домен.
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        setError("emailError", "Введите корректный email.");
        valid = false;
    }

    // Пароль: минимум 6, буквы + цифры.
    if (!/^(?=.*[A-Za-z])(?=.*\d).{6,}$/.test(password)) {
        setError(
            "passwordError",
            "Минимум 6 символов, должны быть буквы и цифры."
        );
        valid = false;
    }

    if (password !== passwordConfirm) {
        setError("passwordConfirmError", "Пароли не совпадают.");
        valid = false;
    }

    // CAPTCHA не должна отправляться, если поле пустое.
    if (!captcha) {
        setError("captchaError", "Введите ответ капчи.");
        valid = false;
    }

    if (!valid) {
        return;
    }

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                username,
                email,
                password,
                password_confirm: passwordConfirm,
                captcha
            })
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = "/login.html?success=1";
            return;
        }

        showMessage(data.message, "error");
        document.getElementById("captcha").value = "";

        // Сервер уже обновил CAPTCHA после проверки.
        // Получаем ее отображение.
        await refreshCaptcha();
    } catch (error) {
        showMessage("Ошибка соединения с сервером.", "error");
    }
});
