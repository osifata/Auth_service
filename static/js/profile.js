const message = document.getElementById("message");
const logoutButton = document.getElementById("logoutButton");

function showMessage(text, type = "error") {
    message.textContent = text;
    message.className = `message ${type}`;
}

async function loadProfile() {
    try {
        const response = await fetch("/api/profile");

        if (response.status === 401) {
            window.location.href = "/login.html";
            return;
        }

        const data = await response.json();

        if (!data.success) {
            window.location.href = "/login.html";
            return;
        }

        const user = data.user;

        document.getElementById("profileUsername").textContent = user.username;
        document.getElementById("username").textContent = user.username;
        document.getElementById("email").textContent = user.email;
        // Показываем только дату регистрации, без времени.
        const date = new Date(user.created_at.replace(" ", "T") + "Z");
        const formattedDate = new Intl.DateTimeFormat("ru-RU", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric"
        }).format(date);

        document.getElementById("createdAt").textContent = formattedDate;
        document.getElementById("role").textContent = user.role;
    } catch (error) {
        showMessage("Не удалось загрузить данные профиля.");
    }
}

logoutButton.addEventListener("click", async () => {
    try {
        await fetch("/api/logout", {method: "POST"});
        window.location.href = "/login.html";
    } catch (error) {
        showMessage("Не удалось выполнить выход.");
    }
});

loadProfile();
