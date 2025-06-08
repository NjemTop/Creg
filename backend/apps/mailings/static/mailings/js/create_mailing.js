document.addEventListener("DOMContentLoaded", function () {
    let modeField = document.getElementById("id_mode");
    let testEmailWrapper = document.getElementById("test_email_wrapper");
    let testEmailField = document.getElementById("id_test_email");

    let languageWrapper = document.getElementById("language_wrapper");
    let serverVersionField = document.getElementById("id_server_version");

    let serviceWindowWrapper = document.querySelector(".custom-switch label[for='id_service_window']").parentElement;
    let saasNotificationWrapper = document.querySelector(".custom-switch label[for='id_saas_notification']").parentElement;

    let serviceWindowCheckbox = document.getElementById("id_service_window");
    let saasNotificationCheckbox = document.getElementById("id_saas_notification");

    let saasUpdateWrapper = document.getElementById("saas_update_time_wrapper");

    const form = document.querySelector("form");

    function toggleTestModeFields() {
        let isTestMode = modeField.value === "test";

        testEmailWrapper.style.display = isTestMode ? "block" : "none";
        testEmailField.required = isTestMode;
        testEmailField.disabled = !isTestMode;

        languageWrapper.style.display = isTestMode ? "block" : "none";
        const languageField = document.getElementById("id_language");
        languageField.disabled = !isTestMode;

        if (!isTestMode) {
            testEmailField.value = "";
            languageField.value = "";
        }
    }

    function toggleSaaSUpdateTime() {
        saasUpdateWrapper.style.display = saasNotificationCheckbox.checked ? "block" : "none";
    }

    function toggleSwitches() {
        let isServerVersionFilled = serverVersionField.value.trim().length > 0;

        serviceWindowCheckbox.disabled = !isServerVersionFilled;
        saasNotificationCheckbox.disabled = !isServerVersionFilled;

        // Если отключаем чекбоксы, то сбрасываем их состояние
        if (!isServerVersionFilled) {
            serviceWindowCheckbox.checked = false;
            saasNotificationCheckbox.checked = false;
            toggleSaaSUpdateTime();
            
            // Добавляем серый стиль для отключённых свичей
            serviceWindowWrapper.classList.add("disabled-switch");
            saasNotificationWrapper.classList.add("disabled-switch");
        } else {
            // Убираем серый стиль, если поле заполнено
            serviceWindowWrapper.classList.remove("disabled-switch");
            saasNotificationWrapper.classList.remove("disabled-switch");
        }
    }

    // Универсальная функция валидации поля с выводом текста ошибки
    function setupFieldValidation(selector, regex, errorMessage) {
        const field = document.querySelector(selector);
        if (!field) return;

        let errorDiv = field.nextElementSibling;
        if (!errorDiv || !errorDiv.classList.contains("invalid-feedback")) {
            errorDiv = document.createElement("div");
            errorDiv.classList.add("invalid-feedback");
            field.after(errorDiv);
        }

        // Проверка только при потере фокуса
        field.addEventListener("blur", function () {
            if (!regex.test(field.value) && field.value.trim() !== "") {
                field.classList.add("is-invalid");
                errorDiv.textContent = errorMessage;
            }
        });

        // Если пользователь снова вводит данные — убираем ошибку
        field.addEventListener("input", function () {
            field.classList.remove("is-invalid");
            errorDiv.textContent = "";
        });
    }

    // Добавляем валидацию email (теперь с проверкой при blur)
    setupFieldValidation(
        "#id_test_email",
        /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
        "Введите корректный email (например, example@mail.com)."
    );

    // Слушаем изменения
    modeField.addEventListener("change", toggleTestModeFields);
    saasNotificationCheckbox.addEventListener("change", toggleSaaSUpdateTime);
    serverVersionField.addEventListener("input", toggleSwitches);

    // Первоначальная настройка
    toggleTestModeFields();
    toggleSaaSUpdateTime();
    toggleSwitches();
});
