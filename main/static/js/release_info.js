$(window).on('load', function () {
    const username = 'admin'; // Переменная для имени пользователя
    const password = 'ekSkaaiWnK'; // Переменная для пароля

    const target = document.getElementById('spinner');
    const spinner = new Spinner().spin(target); // Создаем экземпляр спиннера и запускаем его

    // Получение токена доступа
    $.ajax({
        url: '/api/token',
        method: 'POST',
        data: {
            username: username,
            password: password
        },
        success: function(data) {
            const accessToken = data.access;

            // Получаем ссылку на элементы select и tbody
            const releaseSelect = $('#release-number-select');
            const dataTable = $('#release-info-table-body');

            // Функция для отображения данных в таблице
            function displayData(dataJson) {
                // Очищаем таблицу
                dataTable.empty();
                
                // Если нет данных, отображаем сообщение
                if (dataJson.length === 0) {
                    dataTable.append(`
                        <tr>
                            <td colspan="5">Нет данных</td>
                        </tr>
                    `);
                } else {
                    // Иначе, для каждого элемента в данных
                    dataJson.forEach(item => {
                        // Преобразуем дату из формата ISO в формат "день месяц год"
                        const date = new Date(item['date']);
                        const formattedDate = `${date.getDate()} ${date.toLocaleString('ru', { month: 'long' })} ${date.getFullYear()} года`;

                        // Добавляем строку в таблицу
                        dataTable.append(`
                            <tr>
                                <td>${formattedDate}</td>
                                <td>${item['release_number']}</td>
                                <td>${item['client_name']}</td>
                                <td>${item['main_contact']}</td>
                                <td>${item['copy_contact']}</td>
                            </tr>
                        `);
                    });
                }
                // Скрываем спиннер
                spinner.stop();
            }

            // Функция для отображения данных при выборе релиза
            function showReleaseData(releaseNumber) {
                // Отправляем запрос на сервер
                $.ajax({
                    url: `/api/data_release/${releaseNumber}/version_info`,
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                    },
                    dataType: 'json',
                    success: function (data) {
                        // Если успешно, отображаем новые данные
                        displayData(data);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        // Если ошибка, выводим информацию об ошибке в консоль
                        console.error(textStatus, errorThrown);
                    }
                });
            }

            // Обработчик события изменения выбранного релиза
            releaseSelect.on('change', function () {
                const releaseNumber = this.value;
                showReleaseData(releaseNumber);
            });

            // Получаем список релизов и выбираем последний
            $.ajax({
                url: '/api/data_release',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                },
                dataType: 'json',
                success: function (data) {
                    // Сортируем данные по дате
                    data.sort((a, b) => new Date(b.Data) - new Date(a.Data));
                    
                    // Очищаем список релизов
                    releaseSelect.empty();
                    
                    // Добавляем все релизы в список
                    data.forEach(release => {
                        releaseSelect.append(new Option(release.Number, release.Number));
                    });

                    // Выбираем последний релиз
                    const latestRelease = data[0].Number;
                    releaseSelect.val(latestRelease);
                    
                    // Отображаем данные для последнего релиза
                    showReleaseData(latestRelease);
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    // Если ошибка, выводим информацию об ошибке в консоль
                    console.error(textStatus, errorThrown);
                }
            });
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // Если ошибка, выводим информацию об ошибке в консоль
            console.error(textStatus, errorThrown);
        }
    });
});
