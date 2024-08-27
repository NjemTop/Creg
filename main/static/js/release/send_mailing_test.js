document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы страницы
    const applyButton = document.getElementById('applyButton');
    const releaseGroupSelect = document.getElementById('releaseGroup');
    const releaseTypeSelect = document.getElementById('releaseTypeGroup');
    const releaseVersionInput = document.getElementById('numberRelease');
    const iPadVersionInput = document.getElementById('iPadVersion');
    const AndroidVersionInput = document.getElementById('AndroidVersion');
    const emailInput = document.getElementById('email');
    const languageSelect = document.getElementById('languageSelect');
    const spinner = document.getElementById('loading-spinner');

    // Создаём константы
    const HOTFIX = 'hotfix';
    const STANDARD_MAILING = 'standard_mailing';
    const IPAD = 'ipad';
    const ANDROID = 'android';

    // Обработчик клика на кнопку "Отправить тестовую рассылку"
    applyButton.addEventListener('click', function() {
        // Проверка на тип рассылки (test_mailing)
        if (!document.getElementById('testMailingCheckbox').checked) {
            return;
        }

        // Определение типа рассылки и дополнительного типа (например, iPad или Android)
        const mailingType = releaseTypeSelect.value;
        let additionalType = null;
        if (mailingType === HOTFIX) {
            additionalType = releaseGroupSelect.value === 'releaseiPad' ? IPAD : 
                             releaseGroupSelect.value === 'releaseAndroid' ? ANDROID : null;
        }

        // Формирование объекта данных для отправки
        let data = {
            email: emailInput.value,
            mailing_type: mailingType,
            release_type: releaseGroupSelect.value,
            server_version: releaseVersionInput.value,
            ipad_version: iPadVersionInput.value,
            android_version: AndroidVersionInput.value,
            language: languageSelect.value
        };

        // Проверка заполнения обязательных полей
        if (data.email && 
            ((mailingType === STANDARD_MAILING && data.server_version) ||
            (mailingType === HOTFIX && (data.server_version || data.android_version || data.ipad_version)))) {
            sendRequest('POST', '/apiv2/send_test_mailing/', data);
        } else {
            infoShowToast("Пожалуйста, заполните все необходимые поля.");
        }
    });

    // Функция для отправки запроса на сервер
    function sendRequest(method, url, data) {
        // Показываем спиннер
        spinner.style.display = 'block';

        fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(response => {
            // Скрываем спиннер
            spinner.style.display = 'none';
            if (!response.ok) {
                throw new Error(`${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            successShowToast("Тестовое письмо было отправлено.");
        })
        .catch((error) => {
            spinner.style.display = 'none';
            errorShowToast(`Произошла ошибка при отправке тестового письма: ${error.message}`);
        });
    }
});
