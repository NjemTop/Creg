$(function() {
    const spinnerTarget = document.getElementById('spinner');
    const spinner = new Spinner().spin(spinnerTarget); // Создаем спиннер один раз и используем его повторно

    const releaseSelect2x = $('#release-number-select-2x');
    const releaseSelect3x = $('#release-number-select-3x');
    const dataTable = $('#release-info-table-body');

    function fetchToken() {
        return new Promise((resolve, reject) => {
            $.ajax({
                url: '/api/token',
                method: 'POST',
                data: {
                    username: 'admin', // Логин для получения токена
                    password: 'ekSkaaiWnK' // Пароль для получения токена
                },
                success: function(data) {
                    resolve(data.access);
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    reject(new Error(`Ошибка при получении токена: ${textStatus}`));
                }
            });
        });
    }

    // Функция для отображения данных при выборе релиза
    function showReleaseData(releaseNumber) {
        // Отправляем запрос на сервер
        fetchToken().then(accessToken => {
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
                    console.error('Ошибка отображения данных при выборе релиза:', textStatus, errorThrown);
                    errorShowToast(`Ошибка отображения данных при выборе релиза: ${errorThrown}`);
                }
            });
        }).catch(error => {
            console.error('Ошибка при получении токена:', error);
            errorShowToast('Ошибка при получении токена:', error);
        });
    }

    // Функция для отправки запроса на получение данных релиза
    function fetchReleaseData(releaseNumber) {
        if (!releaseNumber) return; // Не делаем запрос, если номер релиза не задан

        fetchToken().then(accessToken => {
            $.ajax({
                url: `/api/data_release/${releaseNumber}/version_info`,
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                },
                dataType: 'json',
                success: displayData,
                error: function(jqXHR, textStatus, errorThrown) {
                    console.error('Ошибка отправки запроса на получение данных релиза:', textStatus, errorThrown);
                    errorShowToast(`Ошибка отправки запроса на получение данных релиза: ${errorThrown}`);
                }
            });
        }).catch(error => {
            console.error('Ошибка при получении токена:', error);
            errorShowToast('Ошибка при получении токена:', error);
        });
    }

    // Функция для отображения данных в таблице
    function displayData(dataJson) {
        // Очищаем только таблицу
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

    // Установка плейсхолдера для выпадающего списка
    function setPlaceholder(selectElement, showPlaceholder) {
        // Удаляем существующий плейсхолдер, если есть
        selectElement.find('option[value=""]').remove();

        if (showPlaceholder) {
            // Добавляем плейсхолдер, если он должен быть показан
            selectElement.prepend(`<option value="" disabled selected>Выберите необходимый релиз</option>`);
        }
    }

    function handleReleaseSelection() {
        const releaseNumber = $(this).val();
        const is2xSelected = $(this).is(releaseSelect2x);
        
        setPlaceholder(releaseSelect2x, !is2xSelected);
        setPlaceholder(releaseSelect3x, is2xSelected);
        fetchReleaseData(releaseNumber);
    }

    // Функция для заполнения выпадающих списков релизами
    function populateReleaseSelects(data) {
        // Очищаем списки релизов
        releaseSelect2x.empty();
        releaseSelect3x.empty();

        let lastRelease2x = null;
        let lastRelease3x = null;

        // Установка плейсхолдера для обоих списков
        setPlaceholder(releaseSelect2x, true);
        setPlaceholder(releaseSelect3x, true);

        // Сортируем данные по дате в обратном порядке
        data.sort((a, b) => new Date(b.Data) - new Date(a.Data));

        data.forEach(release => {
            if (release.Number.startsWith('2')) {
                releaseSelect2x.append(new Option(release.Number, release.Number));
                lastRelease2x = release.Number;
            } else if (release.Number.startsWith('3')) {
                releaseSelect3x.append(new Option(release.Number, release.Number));
                lastRelease3x = release.Number;
            }
        });

        // Автоматически выбираем последний релиз в каждом списке
        if (lastRelease2x) {
            releaseSelect2x.val(lastRelease2x);
            showReleaseData(lastRelease2x);
        }

        if (lastRelease3x) {
            releaseSelect3x.val(lastRelease3x);
            showReleaseData(lastRelease3x);
        }
    }

    // Функция для определения и установки последнего релиза и установки плейсхолдеров
    function setLastReleaseAndPlaceholders(data) {
        // Переменные для хранения последнего номера релиза и самой поздней даты для каждой версии
        let lastRelease2x = null;
        let lastRelease3x = null;
        let latestDate2x = new Date(0); // Начальная дата для сравнения (очень старая дата)
        let latestDate3x = new Date(0); // Начальная дата для сравнения (очень старая дата)
    
        // Перебор всех релизов для нахождения самого свежего релиза для каждой версии
        data.forEach(release => {
            const releaseDate = new Date(release.Data); // Преобразование строки в объект Date
            if (release.Number.startsWith('2') && releaseDate > latestDate2x) {
                latestDate2x = releaseDate;
                lastRelease2x = release.Number;
            } else if (release.Number.startsWith('3') && releaseDate > latestDate3x) {
                latestDate3x = releaseDate;
                lastRelease3x = release.Number;
            }
        });
    
        // Сравнение дат последних релизов и установка значения выпадающего списка для самого свежего релиза
        if (latestDate2x > latestDate3x) {
            releaseSelect2x.val(lastRelease2x); // Установка последнего релиза 2.x
            showReleaseData(lastRelease2x);
        } else {
            releaseSelect3x.val(lastRelease3x); // Установка последнего релиза 3.x
            showReleaseData(lastRelease3x);
        }

        // Установка плейсхолдера для неактивного выпадающего списка
        setPlaceholder(releaseSelect2x, releaseSelect3x.val());
        setPlaceholder(releaseSelect3x, releaseSelect2x.val());
    }

    // Получение и установка токена доступа и данных релиза
    fetchToken().then(accessToken => {
        $.ajax({
            url: '/api/data_release',
            headers: { 'Authorization': `Bearer ${accessToken}` },
            dataType: 'json',
            success: function(data) {
                data.sort((a, b) => new Date(b.Data) - new Date(a.Data)); // Сортировка данных по убыванию дат
                populateReleaseSelects(data); // Заполнение выпадающих списков
                setLastReleaseAndPlaceholders(data); // Установка последнего релиза и плейсхолдеров
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Ошибка:', textStatus, errorThrown);
                errorShowToast(`Ошибка при загрузке данных о релизах: ${errorThrown}`);
            },
            complete: function() {
                spinner.stop();
            }
        });
    }).catch(error => {
        console.error('Ошибка при получении токена:', error);
        errorShowToast('Ошибка при получении токена:', error);
    });

    // Установка обработчиков событий для выпадающих списков
    releaseSelect2x.change(handleReleaseSelection);
    releaseSelect3x.change(handleReleaseSelection);
});
