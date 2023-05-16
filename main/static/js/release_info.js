$(document).ready(function () {
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
    }    

    // Когда выбран другой номер релиза
    releaseSelect.on('change', function () {
        const releaseNumber = this.value;

        // Отправляем запрос на сервер
        $.ajax({
            url: 'http://194.37.1.214:3030/api/data_release/?release_number=' + releaseNumber,
            headers: {
                'Authorization': 'Basic ' + btoa('admin:ekSkaaiWnK'),
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
    });

    // Получаем список релизов и выбираем последний
    $.ajax({
        url: 'http://194.37.1.214:3030/api/data_release/versions',
        headers: {
            'Authorization': 'Basic ' + btoa('admin:ekSkaaiWnK'),
        },
        dataType: 'json',
        success: function (data) {
            // Сортируем данные по дате
            data.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            // Добавляем все релизы в список
            data.forEach(release => {
                releaseSelect.append(new Option(release.release_number, release.release_number));
            });

            // Выбираем последний релиз
            const latestRelease = data[0].release_number;
            releaseSelect.val(latestRelease);
            
            // Запускаем событие изменения, чтобы загрузить данные для последнего релиза
            releaseSelect.trigger('change');
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // Если ошибка, выводим информацию об ошибке в консоль
            console.error(textStatus, errorThrown);
        }
    });
});
