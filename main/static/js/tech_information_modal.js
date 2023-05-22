// Функция, выполняющаяся при загрузке страницы
(function() {
    // Получение всех модальных окон на странице
    const modals = document.querySelectorAll('[id^="tech_informationModal_"]');

    // Имя пользователя и пароль для авторизации на сервере
    const username = 'admin';
    const password = 'ekSkaaiWnK';

    // Создание заголовков для отправки с запросом
    const headers = new Headers();
    headers.set('Authorization', 'Basic ' + btoa(username + ":" + password));

    // Проход по всем модальным окнам
    modals.forEach((modal) => {
        // Обработчик события при открытии модального окна
        modal.addEventListener('show.bs.modal', function (event) {
            // Получение кнопки, которая вызвала модальное окно
            const button = event.relatedTarget;
            // Получение идентификатора клиента из атрибута кнопки
            const clientId = button.getAttribute('data-client-id');

            // Отправка запроса на сервер с авторизационными заголовками
            fetch(`/api/tech_information/client/${clientId}`, { headers })
                .then(response => {
                    // Проверка успешности ответа
                    if (!response.ok) {
                        throw new Error('Ошибка сети при получении данных');
                    }
                    return response.json();
                })
                .then(data => {
                    // Получение всех нужных элементов страницы
                    const elements = [
                        'server_version',
                        'update_date',
                        'api',
                        'ipad',
                        'android',
                        'mdm',
                        'localizable_web',
                        'localizable_ios',
                        'skins_web',
                        'skins_ios'
                    ].reduce((acc, curr) => {
                        acc[curr] = document.getElementById(`${curr}_${clientId}`);
                        return acc;
                    }, {});

                    // Заполнение элементов страницы данными
                    if (data[0].tech_information !== null) {
                        elements.server_version.value = data[0].tech_information.server_version;

                        // Обработка и форматирование даты
                        let date = new Date(data[0].tech_information.update_date);
                        let day = date.getDate();
                        let month = date.getMonth();
                        let year = date.getFullYear();

                        // Инициализация календаря с новым форматом даты
                        const monthNames = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'];
                        day = day < 10 ? '0' + day : day;
                        elements.update_date.value = `${day} ${monthNames[month]} ${year} года`;

                        // Заполнение полей 'ipad', 'android', 'mdm' данными
                        ['ipad', 'android', 'mdm'].forEach(item => {
                            elements[item].value = data[0].tech_information[item];
                        });

                        // Инициализация календаря с использованием jQuery UI datepicker
                        $('#update_date_' + clientId).datepicker({
                            dateFormat: 'dd MM yy',
                            monthNames: monthNames,
                            onSelect: function(dateText, inst) {
                                var date = $(this).datepicker('getDate'),
                                    day  = date.getDate(),
                                    month = date.getMonth(),
                                    year =  date.getFullYear();
                                $(this).val(day + ' ' + inst.settings.monthNames[month] + ' ' + year + ' года');
                            }
                        });

                        // Обработчик для установки корректного z-index для datepicker
                        $('#update_date_' + clientId).on("focus", function() { 
                            var dp = $(this).data("datepicker");
                            dp.dpDiv.css("z-index", 2000);
                        });

                        // Функция для вывода информационного сообщения о формате версии
                        function showVersionFormatInfo() {
                            Toastify({
                                text: 'Пример формата версии: 2.45.35301.26201',
                                backgroundColor: '#869a9c',
                                className: 'info-toast',
                            }).showToast();
                        }

                        // Функция для вывода информационного сообщения о формате версии
                        function showMDMFormatInfo() {
                            Toastify({
                                text: 'Например Mobileiron, AirWatch и др.',
                                backgroundColor: '#869a9c',
                                className: 'info-toast',
                            }).showToast();
                        }

                        // Добавляем обработчик для события фокуса на поле "Версия сервера"
                        elements.server_version.addEventListener('focus', showVersionFormatInfo);

                        // Добавляем обработчик для события фокуса на поле "MDM"
                        elements.mdm.addEventListener('focus', showMDMFormatInfo);
                        
                        // Функция для отправки запроса и обновления UI
                        function sendRequestAndUpdateUI(value, item, techInfoId) {
                            return sendPatchRequest(value, item, techInfoId)
                                .then(response => {
                                    if (response.ok) {
                                        // Если запрос выполнен успешно, показываем уведомление об успешном выполнении
                                        Toastify({
                                            text: 'Запрос успешно выполнен',
                                            backgroundColor: 'linear-gradient(to right, #00b09b, #96c93d)',
                                            className: 'success-toast',
                                        }).showToast();
                                        // ... другие действия после успешного запроса ...
                                    } else {
                                        throw new Error('Ошибка при отправке запроса');
                                    }
                                })
                                .catch(error => {
                                    console.error(`Произошла ошибка при обновлении ${item}:`, error);
                                    // Выводим сообщение об ошибке в консоль
                                    console.error(error);
                                    // Показываем уведомление об ошибке
                                    Toastify({
                                        text: `Ошибка при обновлении ${item}: ${error.message}`,
                                        backgroundColor: '#ff6347',
                                        className: 'error-toast',
                                    }).showToast();
                                });
                        }

                        // Обработчик событий для всех элементов тех. информации со свичами
                        ['api', 'localizable_web', 'localizable_ios', 'skins_web', 'skins_ios'].forEach(item => {
                            // Проверяем, существует ли элемент перед обработкой
                            if (elements[item]) {
                                // Получаем родительский элемент старого checkbox (div с классом 'form-check form-switch')
                                let parentElement = elements[item].parentNode;
                                let clientId = parentElement.id.split('_')[1]; // Извлекаем id клиента из id элемента
                            
                                // Удаляем старый элемент checkbox
                                elements[item].remove();
                            
                                // Создаем новый элемент checkbox
                                let newCheckbox = document.createElement('input');
                                newCheckbox.type = 'checkbox';
                                newCheckbox.id = `${item}_${clientId}`; // Добавляем новый id
                                newCheckbox.classList.add('form-check-input');
                                newCheckbox.classList.add('tech-information-switch'); // Добавление класса для свитчера
                            
                                // Создаем новую метку и связываем ее с новым чекбоксом
                                let newLabel = document.createElement('label');
                                newLabel.setAttribute('for', newCheckbox.id);
                                newLabel.classList.add('form-check-label');

                            
                                // Добавляем новый checkbox и метку в родительский элемент
                                parentElement.appendChild(newCheckbox);
                                parentElement.appendChild(newLabel);
                            
                                // Заменяем старый checkbox новым в списке элементов
                                elements[item] = newCheckbox;
                            
                                // Добавляем проверку на существование значения в данных
                                if(data[0].tech_information && data[0].tech_information[item] !== undefined) {
                                    elements[item].checked = data[0].tech_information[item];
                                } else {
                                    elements[item].checked = false;
                                }
                            
                                elements[item].addEventListener('change', function(event) {
                                    event.stopPropagation();
                                    // Проверяем, существует ли tech_information в данных
                                    if(data[0].tech_information) {
                                        sendRequestAndUpdateUI(this.checked, item, data[0].tech_information.id);
                                    } else {
                                        console.error('Не удалось обновить данные, т.к. отсутствуют tech_information');
                                    }
                                });
                            
                                // Инициализация Switchery после установки обработчика событий
                                let switchery = new Switchery(elements[item], {
                                    size: 'small', // Размер свича ('small', 'default', 'large')
                                    color: '#64bd63', // Цвет активного свича
                                    secondaryColor: '#f44336', // Цвет не активного свеча
                                    jackColor: '#fff',
                                    jackSecondaryColor: '#c8ff77'
                                });
                            }
                        });
                    } else {
                        console.error('Отсутствуют данные tech_information');
                        // Действия, если данных нет:

                        // Отправка POST-запроса для создания новых данных
                        const postData = {
                            android: "Не указано",
                            api: false,
                            ipad: "Не указано",
                            localizable_ios: false,
                            localizable_web: false,
                            mdm: "Не указано",
                            server_version: "Не указано",
                            skins_ios: false,
                            skins_web: false,
                            update_date: formatNewDateForServer(new Date()) // текущая дата
                        };
                        sendPostRequest(clientId, postData)
                        .then(response => {
                            if (response.ok) {
                                // Если запрос выполнен успешно, показываем уведомление об успешном выполнении
                                Toastify({
                                    text: 'Запрос на создание данных успешно выполнен',
                                    backgroundColor: 'linear-gradient(to right, #00b09b, #96c93d)',
                                    className: 'success-toast',
                                }).showToast();
                                // ... здесь потом добавлю другие действия после успешного запроса ...
                            } else {
                                throw new Error('Ошибка при отправке запроса на создание данных');
                            }
                        })
                        .catch(error => {
                            console.error('Произошла ошибка при создании данных:', error);
                            // Выводим сообщение об ошибке в консоль
                            console.error(error);
                            // Показываем уведомление об ошибке
                            Toastify({
                                text: 'Ошибка при создании данных: ' + error.message,
                                backgroundColor: '#ff6347',
                                className: 'error-toast',
                            }).showToast();
                        });
                    }

                    // Обработчик для поля сервера (нажатие клавиши Enter)
                    elements.server_version.addEventListener('keydown', function(event) {
                        if (event.key === 'Enter') {
                            event.preventDefault();
                            sendRequestAndUpdateUI(this.value, 'server_version', data[0].tech_information.id);
                        }
                    });

                    // Обработчики событий для текстовых полей
                    ['ipad', 'android', 'mdm'].forEach(item => {
                        elements[item].addEventListener('keydown', function(event) {
                            if (event.key === 'Enter') {
                                event.preventDefault();
                                sendRequestAndUpdateUI(this.value, item, data[0].tech_information.id);
                            }
                        });
                    });

                    // Обработчик для кнопки "Применить"
                    document.getElementById(`apply_${clientId}`).addEventListener('click', function() {
                        const serverValue = elements.server_version.value;
                        const dateValue = elements.update_date.value;

                        // Отправка запроса для сервера
                        const serverPromise = sendPatchRequest(serverValue, 'server_version', data[0].tech_information.id);

                        // Отправка запроса для даты
                        console.log(dateValue);
                        const datePromise = sendPatchRequest(dateValue, 'update_date', data[0].tech_information.id);

                        // Отправка запросов для 'ipad', 'android', 'mdm'
                        const patchPromises = ['ipad', 'android', 'mdm'].map(item => {
                            return sendPatchRequest(elements[item].value, item, data[0].tech_information.id);
                        });

                        Promise.all([serverPromise, datePromise, ...patchPromises])
                            .then(responses => {
                                const allSuccessful = responses.every(response => response.ok);
                                if (allSuccessful) {
                                    // Если все запросы выполнены успешно, показываем уведомление об успешном выполнении
                                    Toastify({
                                        text: 'Все запросы успешно выполнены',
                                        backgroundColor: 'linear-gradient(to right, #00b09b, #96c93d)',
                                        className: 'success-toast',
                                    }).showToast();
                                    // ... потом добавлю другие действия после успешных запросов ...
                                } else {
                                    Toastify({
                                        text: 'Произошла ошибка при выполнении запросов',
                                        backgroundColor: '#ff6347',
                                        className: 'error-toast',
                                    }).showToast();
                                    throw new Error('Произошла ошибка при выполнении запросов');
                                }
                            })
                            .catch(error => {
                                console.error('Произошла ошибка при выполнении запросов:', error);
                                // Выводим сообщение об ошибке в консоль
                                console.error(error);
                                // Показываем уведомление об ошибке
                                Toastify({
                                    text: 'Ошибка: ' + error.message,
                                    backgroundColor: '#ff6347',
                                    className: 'error-toast',
                                }).showToast();
                            });
                    });

                    function sendPatchRequest(value, item, techInfoId) {
                        // Получение токена для аутентификации
                        return fetch('/api/token', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                username: 'admin',
                                password: 'ekSkaaiWnK',
                            }),
                        })
                        .then(response => response.json())
                        .then(tokenData => {
                            const accessToken = tokenData.access;
                            const headers = new Headers();
                            headers.set('Authorization', 'Bearer ' + accessToken);
                            headers.set('Content-Type', 'application/json');

                            // Форматирование даты, если необходимо
                            if (item === 'update_date') {
                                value = formatDateForServer(value);
                            }

                            // Отправка запроса на обновление информации
                            return fetch(`/api/tech_information/detail/${techInfoId}`, {
                                method: 'PATCH',
                                headers: headers,
                                body: JSON.stringify({
                                    [item]: value || null
                                }),
                                credentials: 'include',
                            });
                        })
                        .catch((error) => {
                            console.error('Ошибка при получении токена:', error);
                            // Выводим сообщение об ошибке в консоль
                            console.error(error);
                            throw error;
                        });
                      }

                    // Функция для отправки POST-запроса и создания новых данных tech_information
                    function sendPostRequest(clientId, postData) {
                        // Получение токена для аутентификации
                        return fetch('/api/token', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                username: 'admin',
                                password: 'ekSkaaiWnK',
                            }),
                        })
                        .then(response => response.json())
                        .then(tokenData => {
                            const accessToken = tokenData.access;
                            const headers = new Headers();
                            headers.set('Authorization', 'Bearer ' + accessToken);
                            headers.set('Content-Type', 'application/json');

                            // Отправка запроса на создание новых данных tech_information
                            return fetch(`/api/tech_information/client/${clientId}`, {
                                method: 'POST',
                                headers: headers,
                                body: JSON.stringify(postData),
                                credentials: 'include',
                            });
                        })
                        .catch((error) => {
                            console.error('Ошибка при получении токена:', error);
                            // Выводим сообщение об ошибке в консоль
                            console.error(error);
                            throw error;
                        });
                    }

                    // Функция для форматирования даты в формат "YYYY-MM-DD"
                    function formatDateForServer(dateString) {
                        console.log('dateString:', dateString); // Вывод значения в консоль
                        const [day, month, year] = dateString.split(' ');
                        const monthIndex = monthNames.findIndex(name => name === month) + 1;
                        const formattedMonth = monthIndex < 10 ? '0' + monthIndex : monthIndex;
                        const formattedDay = day < 10 ? '0' + day : day;
                        return `${year}-${formattedMonth}-${formattedDay}`;
                    }

                    function formatNewDateForServer(dateString) {
                        const date = new Date(dateString);
                        const year = date.getFullYear();
                        const month = (date.getMonth() + 1).toString().padStart(2, '0');
                        const day = date.getDate().toString().padStart(2, '0');
                        return `${year}-${month}-${day}`;
                    }
                })
                .catch(error => {
                    // Обработка ошибок, возникающих при запросе к серверу или при работе с полученными данными
                    console.error('Произошла ошибка при обработке данных:', error);
                });
        });
    });
})();
