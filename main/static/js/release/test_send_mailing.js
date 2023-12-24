document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы страницы
    const applyButton = document.getElementById('applyButton');
    const releaseGroupSelect = document.getElementById('releaseGroup');
    const releaseTypeSelect = document.getElementById('releaseTypeGroup');
    const releaseViewSelect = document.getElementById('releaseViewGroup');
    const releaseVersionInput = document.getElementById('numberRelease');
    const mobileVersionInput = document.getElementById('mobileVersion');
    const emailInput = document.getElementById('email');
    const spinner = document.getElementById('loading-spinner');

    // Создаём константы
    const HOTFIX = 'hotfix';
    const STANDARD_MAILING = 'standard_mailing';
    const IPAD = 'ipad';
    const ANDROID = 'android';
    const RELEASE_3X = 'release3x';

    // Обработчик клика на кнопку "Применить"
    applyButton.addEventListener('click', function() {
        // Проверка на тип рассылки (test_mailing)
        if (releaseTypeSelect.value !== 'test_mailing') {
            return;
        }

        // Определение типа рассылки и дополнительного типа (например, iPad или Android)
        const mailingType = releaseViewSelect.value;
        let additionalType = null;
        if (mailingType === HOTFIX) {
            additionalType = releaseGroupSelect.value === 'releaseiPad' ? IPAD : 
                             releaseGroupSelect.value === 'releaseAndroid' ? ANDROID : null;
        }

        // Формирование объекта данных для отправки
        let data = {
            version: releaseVersionInput.value,
            email: emailInput.value,
            mailing_type: mailingType,
            additional_type: additionalType
        };

        // Добавляем мобильную версию для 3.x, если выбрана стандартная рассылка
        if (mailingType === STANDARD_MAILING && releaseGroupSelect.value === 'release3x') {
            data.mobile_version = mobileVersionInput.value;
        }

        // Проверка заполнения обязательных полей
        if (data.version && data.email && 
            ((mailingType === STANDARD_MAILING && releaseGroupSelect.value === RELEASE_3X && data.mobile_version) || 
             (mailingType === STANDARD_MAILING && releaseGroupSelect.value !== RELEASE_3X) || 
             mailingType === HOTFIX)) {
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
