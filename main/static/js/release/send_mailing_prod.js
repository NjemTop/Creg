document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы страницы
    const applyButtonProd = document.getElementById('applyButtonProd');
    const releaseGroupSelect = document.getElementById('releaseGroup');
    const releaseTypeSelect = document.getElementById('releaseTypeGroup');
    const releaseVersionInput = document.getElementById('numberRelease');
    const iPadVersionInput = document.getElementById('iPadVersion');
    const AndroidVersionInput = document.getElementById('AndroidVersion');
    const spinner = document.getElementById('loading-spinner');

    // Создаём константы
    const HOTFIX = 'hotfix';
    const STANDARD_MAILING = 'standard_mailing';
    const IPAD = 'ipad';
    const ANDROID = 'android';

    // Обработчик клика на кнопку "Отправить рассылку клиентам"
    applyButtonProd.addEventListener('click', function() {
        // Проверка на тип рассылки (standard_mailing)
        if (releaseTypeSelect.value !== STANDARD_MAILING) {
            return;
        }
    
        const server_version = releaseVersionInput.value;
        const confirmationMessage = `Вы уверены, что хотите отправить рассылку с темой: Обновление BoardMaps ${server_version}?`;
    
        // Определение дополнительного типа (например, iPad или Android)
        let additionalType = null;
        if (releaseGroupSelect.value === 'releaseiPad') {
            additionalType = IPAD;
        } else if (releaseGroupSelect.value === 'releaseAndroid') {
            additionalType = ANDROID;
        }
    
        // Формирование объекта данных для отправки
        let data = {
            mailing_type: releaseTypeSelect.value,
            release_type: releaseGroupSelect.value,
            server_version: server_version,
            ipad_version: iPadVersionInput.value,
            android_version: AndroidVersionInput.value
        };
    
        // Проверка заполнения обязательных полей
        if (data.server_version && ((releaseTypeSelect.value === STANDARD_MAILING) ||
            releaseTypeSelect.value === HOTFIX)) {
            // Показываем уточняющий вопрос пользователю
            if (confirm(confirmationMessage)) {
                sendRequest('POST', '/apiv2/send_prod_mailing/', data);
            } else {
                // Пользователь отменил отправку
                infoShowToast("Вы отменили отправку рассылки.");
            }
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
            successShowToast("Рассылка клиентам была успешно отправлена.");
        })
        .catch((error) => {
            spinner.style.display = 'none';
            errorShowToast(`Произошла ошибка при отправке рассылки клиентам: ${error.message}`);
        });
    }
});
