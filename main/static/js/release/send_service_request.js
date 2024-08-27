document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы
    const sendRequestButton = document.getElementById('sendRequestButton');
    const releaseGroupSelect = document.getElementById('releaseGroup');
    const releaseNumberInput = document.getElementById('numberRelease');
    const spinner = document.getElementById('loading-spinner');

    // Обработчик клика на кнопку "Отправить запрос сервисного окна"
    sendRequestButton.addEventListener('click', function() {
        // Проверка на тип рассылки
        const groupValue = releaseGroupSelect.value;
        const releaseNumber = releaseNumberInput.value;

        // Проверка заполненности поля "Номер релиза"
        if (!releaseNumber) {
            infoShowToast('Пожалуйста, укажите номер релиза.');
            return;
        }

        let data = {
            release_version: releaseNumber
        };

        // Проверяем, соответствует ли выбранная группа условиям
        if (groupValue === 'releaseGP') {
            sendRequest('POST', '/apiv2/send_service_request/', data);
        } else {
            infoShowToast('Некорректный тип или группа рассылки для этого запроса.');
        }
    });

    // Функция для отправки запроса на сервер
    function sendRequest(method, url, data) {
        spinner.style.display = 'block'; // Показываем спиннер

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }).then(response => {
            spinner.style.display = 'none'; // Скрываем спиннер
            if (!response.ok) {
                throw new Error(`${response.statusText}`);
            }
            return response.json();
        }).then(data => {
            if (data.success) {
                successShowToast('Запрос на сервисное окно успешно отправлен!');
            } else {
                errorShowToast('Ошибка при отправке запроса на сервисное окно.');
            }
        }).catch((error) => {
            spinner.style.display = 'none';
            errorShowToast(`Произошла ошибка: ${error.message}`);
        });
    }
});
