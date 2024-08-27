document.addEventListener('DOMContentLoaded', function() {
    // Кеширование элементов DOM
    const reportGroupSelect = document.getElementById('reportGroup');
    const reportTypeRow = document.getElementById('reportTypeRow');
    const reportTypeSelect = document.getElementById('reportType');
    const dateRangeRow = document.getElementById('dateRange').parentNode.parentNode; // получаем родительский div для dateRange
    const applyButton = document.querySelector('#applyButton');
    const elementsToRemove = document.querySelectorAll('.tickets-info, .lists');

    // Функция парсинга JSON данных, которые получаем при запуске страницы
    function parseTickets() {
        try {
            return JSON.parse(document.getElementById('report_tickets').textContent);
        } catch (error) {
            console.error("Ошибка при парсинге JSON: ", error);
            throw new Error("Ошибка при парсинге JSON.");
        }
    }

    // Функция для скрытия и изменения элементов на странице
    function hideOrModifyElements() {
        // Скрыть элементы с классами .tickets-info и .lists
        document.querySelector('.tickets-info').style.display = 'none';
        document.querySelector('.lists').style.display = 'none';

        // Изменить стиль диаграммы, чтобы она занимала всю ширину страницы
        document.querySelector('.chart-container').style.width = '100%';
    }

    reportGroupSelect.addEventListener('change', function() {
        if (this.value === 'tickets') {
            reportTypeRow.style.visibility = 'visible';
            reportTypeRow.style.height = 'auto'; // вернуть высоту элемента
        } else {
            reportTypeRow.style.visibility = 'hidden';
            reportTypeRow.style.height = '0'; // установить высоту элемента в 0, чтобы он не занимал места
        }
    });

    reportTypeSelect.addEventListener('change', function() {
        if (this.value === 'create_close') {
            // Показать блоки "Отборы" и "Фильтры"
            document.getElementById('selectionsRow').style.visibility = 'visible';
            document.getElementById('selectionsRow').style.height = 'auto';
            document.getElementById('filtersRow').style.visibility = 'visible';
            document.getElementById('filtersRow').style.height = 'auto';
    
            // Показать диапазон дат, если он был скрыт
            dateRangeRow.style.visibility = 'visible';
            dateRangeRow.style.height = 'auto';
        } else {
            // Скрыть блоки "Отборы" и "Фильтры"
            document.getElementById('selectionsRow').style.visibility = 'hidden';
            document.getElementById('selectionsRow').style.height = '0';
            document.getElementById('filtersRow').style.visibility = 'hidden';
            document.getElementById('filtersRow').style.height = '0';
    
            // Для других типов отчетов обрабатывать видимость диапазона дат
            if (this.value === 'open') {
                dateRangeRow.style.visibility = 'hidden';
                dateRangeRow.style.height = '0';
            } else {
                dateRangeRow.style.visibility = 'visible';
                dateRangeRow.style.height = 'auto';
            }
        }
    });

    // Функция для обновления доступных опций фильтра
    function updateFilterOptions() {
        const selectionType = document.getElementById('selectionType').value;
        const filterTypeSelect = document.getElementById('filterType');
        const filterOptions = filterTypeSelect.options;

        for (let i = 0; i < filterOptions.length; i++) {
            const option = filterOptions[i];
            if (['support', 'modules', 'reasons'].includes(option.value)) {
                option.disabled = selectionType === 'open_only';
            }
        }

        // Если выбран "Только открытые", устанавливаем значение фильтра в "Не учитывать"
        if (selectionType === 'open_only') {
            filterTypeSelect.value = 'default';
        }
    }

    // Функция для обновления значения "Отборы:"
    function updateSelectionType() {
        const filterType = document.getElementById('filterType').value;
        const selectionTypeSelect = document.getElementById('selectionType');

        if (['support', 'modules', 'reasons'].includes(filterType)) {
            selectionTypeSelect.value = 'closed_only';
            updateFilterOptions(); // Обновляем доступные опции фильтра
        }
    }

    // Обработчик событий для "Отборы:"
    document.getElementById('selectionType').addEventListener('change', function() {
        updateFilterOptions();
    });

    // Обработчик событий для "Фильтры:"
    document.getElementById('filterType').addEventListener('change', function() {
        updateSelectionType();
    });

    // Вызов функции для инициализации доступных опций фильтра
    updateFilterOptions();

    // Функция генерации линейной диаграммы
    function generateLineChart(dates, createdData = null, closedData = null, supportData = null) {
        const ctx = document.getElementById('ticketsChart').getContext('2d');
    
        // Перед созданием новой диаграммы уничтожьте существующую, если она есть
        if (window.myChart) {
            window.myChart.destroy();
        }

        // Определение наборов данных для графика
        const datasets = [];
    
        // Добавляем данные об открытых тикетах, если они доступны
        if (createdData) {
            datasets.push({
                label: 'Открыто тикетов',
                data: createdData,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            });
        }
    
        // Добавляем данные о закрытых тикетах, если они доступны
        if (closedData) {
            datasets.push({
                label: 'Закрыто тикетов',
                data: closedData,
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            });
        }

        // Добавляем данные по саппортам, если они доступны
        if (supportData) {
            Object.keys(supportData).forEach((supportName, index) => {
                datasets.push({
                    label: `Закрыто тикетов - ${supportName}`,
                    data: supportData[supportName],
                    backgroundColor: getRandomColor(),
                    borderColor: getRandomColor(),
                    borderWidth: 1
                });
            });
        }
    
        window.myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Это позволит графику растягиваться по высоте контейнера
                scales: {
                    x: {
                        beginAtZero: true,
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Функция генерации круговой диаграммы
    function generatePieChart(data) {
        const clientsData = {};
    
        // Собираем данные о клиентах из полученных данных
        data.forEach(ticket => {
            const clientName = ticket.client_name;
            clientsData[clientName] = (clientsData[clientName] || 0) + 1;
        });
    
        // Сортируем данные о клиентах от большего к меньшему
        const sortedClientsData = Object.entries(clientsData)
            .sort((a, b) => b[1] - a[1]);
    
        // Получаем метки и данные из отсортированных данных
        const labels = sortedClientsData.map(([clientName]) => clientName);
        const dataValues = sortedClientsData.map(([_, count]) => count);
    
        // Создаём круговую диаграмму и отображаем её в указанном контейнере
        const pieChartContainer = document.querySelector('.pie-chart');
        pieChartContainer.innerHTML = ''; // Очищаем контейнер
    
        const pieChartCanvas = document.createElement('canvas');
        pieChartContainer.appendChild(pieChartCanvas);
    
        const pieChartContext = pieChartCanvas.getContext('2d');
    
        // Создаём массив разнообразных цветов
        const colors = [
            'rgba(255, 99, 132, 0.5)',
            'rgba(54, 162, 235, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(75, 192, 192, 0.5)',
            'rgba(153, 102, 255, 0.5)',
            'rgba(74, 50, 122, 0.5)',
            'rgba(59, 138, 211, 0.5)',
            'rgba(32, 54, 175, 0.5)',
            'rgba(22, 138, 74, 0.5)',
            'rgba(95, 224, 138, 0.5)',
            'rgba(131, 189, 55, 0.5)'
        ];
    
        // Подготовка цвета для данных
        const backgroundColor = [];
        const borderColor = [];
        for (let i = 0; i < dataValues.length; i++) {
            const colorIndex = i % colors.length;
            backgroundColor.push(colors[colorIndex]);
            borderColor.push(colors[colorIndex].replace('0.5', '1'));
        }
    
        new Chart(pieChartContext, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: dataValues,
                    backgroundColor: backgroundColor,
                    borderColor: borderColor,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right', // положение легенды: 'top', 'right', 'bottom' или 'left'
                        labels: {
                            boxWidth: 20, // ширина блока метки
                            padding: 10, // отступ между метками
                        }
                    }
                },
                layout: {
                    padding: {
                        left: 0,
                        right: 0,
                        top: 0,
                        bottom: 0
                    }
                }
            }
        });
    }

    // Вспомогательная функция для генерации случайного цвета
    function getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Определяем пустой аргумент для того, чтобы потом обновлять таблицу в режиме онлайн
    let vueInstance = null;

    // Функция для создания и обновления таблицы списков тикетов (vue-good-table)
    function initializeVueTable(data) {
        Vue.component('vue-good-table', window["vue-good-table"].VueGoodTable);
        
        // Проверяем, существует ли экземпляр Vue
        if (vueInstance) {
            vueInstance.rows = data;
        } else {
            vueInstance = new Vue({
                el: '#app',
                data: {
                    columns: [
                        { 
                            label: 'Тикет ID', 
                            field: 'ticket_id',
                            html: true,
                            slot: 'ticketLink' // определение слота
                        },
                        { label: 'Создан', field: 'creation_date' },
                        { label: 'Тема тикета', field: 'subject' },
                        { label: 'Статус', field: 'status' },
                        { label: 'Клиент', field: 'client_name' },
                        { label: 'Приоритет', field: 'priority' },
                        { label: 'Исполнитель', field: 'assignee_name' },
                        { label: 'Дата обновления', field: 'updated_at' },
                        { label: 'Дата ответа', field: 'last_reply_at' },
                        { label: 'Первое время ответа', field: 'first_response_time' },
                        { label: 'Время SLA', field: 'sla_time' },
                        { label: 'SLA', field: 'sla' },
                        { label: 'Причина возникновения', field: 'cause' },
                        { label: 'Модуль BoardMaps', field: 'module_boardmaps' },
                        { label: 'Сообщений от саппорта', field: 'staff_message' },
                    ],
                    rows: data, // передаем данные непосредственно из таблицы
                },
                methods: {
                    // ... методы для получения данных в таблицу...
                },
            });
        }
    }

    // Функция для выстраивания (агрегации) графика с шагами, колторые передаются
    function aggregateData(dates, createdData, closedData, step, onlyOpen = false) {
        const aggregatedData = {};
    
        dates.forEach((date, index) => {
            const [day, month, year] = date.split('.').map(Number);
            let stepKey;
    
            // Агрегация данных в зависимости от выбранного шага
            if (step === 'day') {
                stepKey = `${String(day).padStart(2, '0')}.${String(month).padStart(2, '0')}.${String(year).slice(2)}`;
            } else if (step === 'week') {
                const dateObj = new Date(year, month - 1, day);
                const mondayDate = new Date(dateObj);
                mondayDate.setDate(dateObj.getDate() - dateObj.getDay() + (dateObj.getDay() === 0 ? -6 : 1));
                stepKey = `${String(mondayDate.getDate()).padStart(2, '0')}.${String(mondayDate.getMonth() + 1).padStart(2, '0')}.${String(mondayDate.getFullYear()).slice(2)}`;
            } else if (step === 'month') {
                stepKey = `${String(month).padStart(2, '0')}.${String(year).slice(2)}`;
            } else if (step === 'year') {
                stepKey = String(year);
            }
    
            if (!aggregatedData[stepKey]) {
                aggregatedData[stepKey] = {
                    created: 0,
                    closed: onlyOpen ? undefined : 0
                };
            }
    
            aggregatedData[stepKey].created += createdData[index];
            if (!onlyOpen) {
                aggregatedData[stepKey].closed += closedData[index];
            }
        });
    
        const aggregatedDates = Object.keys(aggregatedData);
        const aggregatedCreated = aggregatedDates.map(date => aggregatedData[date].created);
        const aggregatedClosed = !onlyOpen ? aggregatedDates.map(date => aggregatedData[date].closed) : null;
    
        return onlyOpen ? { dates: aggregatedDates, createdData: aggregatedCreated } : { dates: aggregatedDates, createdData: aggregatedCreated, closedData: aggregatedClosed };
    }
    
    // Функция обработки данных (фильтрация по дате)
    function processTickets(tickets, onlyOpen = false) {
        const datesMap = new Map();
    
        tickets.forEach(ticket => {
            const creationDate = new Date(ticket.creation_date).toLocaleDateString();
            const closingDate = !onlyOpen && (ticket.status === "Выполнено" || ticket.status === "Closed") ? new Date(ticket.closed_date).toLocaleDateString() : null;
    
            datesMap.set(creationDate, (datesMap.get(creationDate) || { created: 0, closed: 0 }));
            datesMap.get(creationDate).created++;
    
            if (closingDate) {
                datesMap.set(closingDate, (datesMap.get(closingDate) || { created: 0, closed: 0 }));
                datesMap.get(closingDate).closed++;
            }
        });
    
        const sortedDates = Array.from(datesMap.keys()).sort();
        const createdData = sortedDates.map(date => datesMap.get(date).created);
        const closedData = !onlyOpen ? sortedDates.map(date => datesMap.get(date).closed) : null;
    
        return onlyOpen ? { dates: sortedDates, createdData } : { dates: sortedDates, createdData, closedData };
    }

    // Функция создания списка топ модулей
    function getTopEntities(tickets, entity) {
        let entities = {};

        tickets.filter(ticket => ticket.status === "Выполнено" || ticket.status === "Closed")
            .forEach(ticket => {
                entities[ticket[entity]] = (entities[ticket[entity]] || 0) + 1;
       });

        return Object.entries(entities)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(entry => entry[0]);
    }

    // Функция создания списка топ причин возникновений
    function populateList(selector, entities) {
        const list = document.querySelector(selector);
        list.innerHTML = '';  // очистка списка
        entities.forEach(entity => {
            let listItem = document.createElement('li');
            listItem.textContent = entity;
            list.appendChild(listItem);
        });
    }

    // Функция сортировки данных по дате
    function sortByDate(dates) {
        return dates.sort((a, b) => {
            const [dayA, monthA, yearA] = a.split('.').map(Number);
            const [dayB, monthB, yearB] = b.split('.').map(Number);
            
            if(yearA !== yearB) return yearA - yearB;
            if(monthA !== monthB) return monthA - monthB;
            return dayA - dayB;
        });
    }

    // Функция для удаления и изменения элементов на странице
    function mergeAndRemoveTables() {
        const reportResults = document.getElementById('reportResults');

        // Находим блок по идентификатору
        if (reportResults) {
            const col9 = reportResults.querySelector('.col-lg-9');
            const col3 = reportResults.querySelector('.col-lg-3');
    
            if (col9 && col3) {
                // Создаём новый элемент, который объединяет содержимое col9 и col3
                const mergedElement = document.createElement('div');
                mergedElement.className = 'col-lg-6'; // Добавляем элемент с 50% шириной страницы
    
                // Перемещаем содержимое col9 и col3 в объединенный элемент
                while (col9.firstChild) {
                    mergedElement.appendChild(col9.firstChild);
                }

                // Удаляем col9
                col9.remove();

                // Заменяем содержимое блока "reportResults" на объединенный элемент
                reportResults.innerHTML = ''; // Очищаем содержимое
                reportResults.appendChild(mergedElement); // Добавляем объединенный элемент вместо row

                // Создаем второй контейнер col-lg-6 для круговой диаграммы
                const col6ForPieChart = document.createElement('div');
                col6ForPieChart.className = 'col-lg-6';

                // Создаем контейнер для круговой диаграммы и добавляем его в col6ForPieChart
                const pieChartContainer = document.createElement('div');
                pieChartContainer.id = 'pieChartContainer'; // Присваиваем id для контейнера
                pieChartContainer.className = 'pie-chart';
                col6ForPieChart.appendChild(pieChartContainer);

                // Добавляем col6ForPieChart внутрь родительского контейнера row
                reportResults.appendChild(col6ForPieChart);

                // Создание контейнера для таблицы
                const tableContainer = document.createElement('div');
                tableContainer.id = 'app'; // Присваиваем id для контейнера (чтобы в дальнейшем с ним работать)

                // Добавляем тэг <vue-good-table> внутрь контейнера
                tableContainer.innerHTML = `
                    <vue-good-table
                        :columns="columns"
                        :rows="rows"
                        :line-numbers="true"
                        :search-options="{ enabled: true, placeholder: 'Поиск по таблице' }"
                        :pagination-options="{ enabled: true, mode: 'pages' }"
                    >
                        <template slot="table-row" slot-scope="props">
                            <span v-if="props.column.label === 'Тикет ID'">
                                <a :href="'https://cs.boardmaps.ru/ru/ticket/list/filter/id/11/ticket/' + props.row.ticket_id">{{ props.row.ticket_id }}</a>
                            </span>
                            <span v-else>
                                {{ props.formattedRow[props.column.field] }}
                            </span>
                        </template>
                    </vue-good-table>
                `;

                reportResults.appendChild(tableContainer); // Добавляем контейнер для таблицы после диаграммы
            }
        } else {
            console.error("Элемент 'reportResults' не найден в DOM.");
            return;
        }
        // Удаляем из страницы счётчик и списки модулей и причин возникновений
        elementsToRemove.forEach(element => {
            // Проверяем, существует ли элемент перед его удалением
            if (element) {
                element.remove();
            }
        });
    }

    // Функция для создания календаря
    function setupDateRangePicker() {
        $(function() {
            // Используем moment.js для создания объектов дат
            const today = moment();
            const thisYear = today.year(); // Получаем год из объекта moment
            const startOfYear = moment().startOf('year'); // Устанавливаем начало текущего года
            
            // Конвертируем объекты moment в объекты Date для использования в 'daterangepicker'
            const startOfMonth = new Date(thisYear, today.month(), 1);
            const endOfMonth = new Date(thisYear, today.month() + 1, 0);
            const startOfLastMonth = new Date(thisYear, today.month() - 1, 1);
            const endOfLastMonth = new Date(thisYear, today.month(), 0);
            const endOfYear = new Date(thisYear, 11, 31);
            const startOfLastYear = new Date(thisYear - 1, 0, 1);
            const endOfLastYear = new Date(thisYear - 1, 11, 31);
    
            $('#dateRange').daterangepicker({
                startDate: startOfYear,
                endDate: today,
                autoUpdateInput: true,
                ranges: {
                    'Эта неделя': [moment().startOf('week'), moment().endOf('week')],
                    'Этот месяц': [moment(startOfMonth), moment(endOfMonth)],
                    'Предыдущий месяц': [moment(startOfLastMonth), moment(endOfLastMonth)],
                    'Текущий год': [moment(startOfYear), moment(endOfYear)],
                    'Предыдущий год': [moment(startOfLastYear), moment(endOfLastYear)]
                },
                locale: {
                    format: 'YYYY-MM-DD',
                    cancelLabel: 'Очистить',
                    applyLabel: 'Применить',
                    fromLabel: 'От',
                    toLabel: 'До',
                    customRangeLabel: 'Выбрать даты',
                    daysOfWeek: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
                    monthNames: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
                }
            });
    
            // Устанавливаем начальное значение элемента диапазона дат в нужном формате
            $('#dateRange').val(startOfYear.format('YYYY-MM-DD') + ' - ' + today.format('YYYY-MM-DD'));

            // Обработчики событий для применения и отмены выбора диапазона
            $('#dateRange').on('apply.daterangepicker', function(ev, picker) {
                $(this).val(picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD'));
            });

            $('#dateRange').on('cancel.daterangepicker', function(ev, picker) {
                $(this).val('');
            });
        });
    }

    try {
        const tickets = parseTickets();

        const { dates, createdData, closedData } = processTickets(tickets);
        console.log('Текущие тикеты:', tickets);

        // Вызываем функцию сортировки
        sortByDate(dates);

        const aggregatedResultsByMonth = aggregateData(dates, createdData, closedData, 'month');
        generateLineChart(aggregatedResultsByMonth.dates, aggregatedResultsByMonth.createdData, aggregatedResultsByMonth.closedData);
        populateList('.modules-list ol', getTopEntities(tickets, 'module_boardmaps'));
        populateList('.reasons-list ol', getTopEntities(tickets, 'cause'));

        setupDateRangePicker();

    } catch (error) {
        console.error("Произошла ошибка при обработке данных:", error.message);
        errorShowToast("Произошла ошибка при загрузке страницы. Пожалуйста, обновите страницу или попробуйте позже.");
    }

    // Находите кнопку "Применить" по её id или классу и добавьте обработчик события click
    applyButton.addEventListener('click', function () {
        // Получаем значения выбранного диапазона дат из элемента с id "dateRange"
        const dateRangeValue = document.querySelector('#dateRange').value;

        // Разберите значение диапазона дат на начальную и конечную даты
        const [startDate, endDate] = dateRangeValue.split(' - ');
        
        // Получаем выбранный отчет из элемента с id "reportType"
        const selectedReport = document.querySelector('#reportType').value;

        // Получаем выбранный шаг из элемента с id "dataStep"
        const selectedStep = document.querySelector('#dataStep').value;

        // Получаем выбранные фильтры отчёта с id "selectionType" и "filterType"
        const selectionType = document.querySelector('#selectionType').value;
        const filterType = document.querySelector('#filterType').value;

        // Вызываем функцию для удаления и изменения элементов
        mergeAndRemoveTables();

        // Если выбран отчет "Создание/закрытие тикетов", выполните следующее:
        if (selectedReport === 'create_close') {
            // Определяем, нужно ли генерировать диаграмму по саппортам
            if (selectionType === 'closed_only' && filterType === 'support') {
                // Отправляем AJAX-запрос на сервер за агрегированными данными по закрытым тикетам саппортов
                fetch(`/apiv2/closed_tickets_by_support/?start_date=${startDate}&end_date=${endDate}&step=${selectedStep}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Нет ответа от сервера');
                    }
                    return response.json();
                })
                .then(data => {
                    // Построение графика с полученными данными
                    generateLineChart(data.dates, null, null, data.supportData);
                })
                .catch(error => {
                    console.error("Произошла ошибка при запросе данных:", error);
                    errorShowToast(`Произошла ошибка при запросе данных: ${error.message}`);
                });
                // Отправляем запрос для получения списка закрытых тикетов
                fetch(`/apiv2/closed_tickets/?start_date=${startDate}&end_date=${endDate}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Нет ответа от сервера');
                    }
                    return response.json();
                })
                .then(closedTicketsData => {
                    // Построение отчёта и диаграммы с полученными данными
                    initializeVueTable(closedTicketsData);
                    generatePieChart(closedTicketsData);
                })
                .catch(error => {
                    console.error("Ошибка при получении списка закрытых тикетов:", error);
                    errorShowToast(`Ошибка при получении списка закрытых тикетов: ${error.message}`);
                });
            }
            else if (selectionType === 'closed_only') {
                fetch(`/apiv2/closed_tickets/?start_date=${startDate}&end_date=${endDate}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Нет ответа от сервера');
                    }
                    return response.json();
                })
                .then(closedTicketsData => {
                    // Построение отчёта и диаграммы с полученными данными
                    initializeVueTable(closedTicketsData);
                    generatePieChart(closedTicketsData);
                })
                .catch(error => {
                    console.error("Ошибка при получении списка закрытых тикетов:", error);
                    errorShowToast(`Ошибка при получении списка закрытых тикетов: ${error.message}`);
                });
            } 
            else {
                // Отправляем AJAX-запрос на сервер с выбранными фильтрами
                fetch(`/apiv2/get_tickets/?start_date=${startDate}&end_date=${endDate}&step=${selectedStep}`)
                .then(response => {
                    if (!response.ok) {
                    throw new Error('Нет ответа от сервера');
                    }
                    return response.json(); // Преобразуем ответ в JSON
                })
                .then(data => {
                    // Строим график
                    generateLineChart(data.dates, data.created_counts, data.closed_counts);

                    // Генерируйте круговую диаграмму с данными клиентов
                    generatePieChart(data.data);

                    // Инициализируем Vue и таблицу с полученными данными
                    initializeVueTable(data.data);
                })
                .catch(error => {
                    console.error("Произошла ошибка при запросе данных:", error);
                    console.error('Ошибка:', error.responseText);
                    errorShowToast(`Произошла ошибка при запросе данных: ${error.message}`);
                });
            }
        }
        else if (selectedReport === 'open'){
            // Отправляем AJAX-запрос на сервер с выбранными фильтрами
            fetch(`/apiv2/opened_tickets/`)
            .then(response => {
                if (!response.ok) {
                throw new Error('Нет ответа от сервера');
                }
                return response.json(); // Преобразуем ответ в JSON
            })
            .then(data => {
                // Обновите данные на странице с использованием полученных данных
                const { dates, createdData } = processTickets(data.tickets, true);
                console.log(data)

                // Вызываем функцию сортировки
                sortByDate(dates);

                // Проверяем что выбрано в графе "Сводные данные в разрезе / шаг в:" и стоим график от этого выбора
                if (selectedStep === 'day') {
                    const aggregatedResultsByDay = aggregateData(dates, createdData, 'day', true);
                    generateLineChart(aggregatedResultsByDay.dates, aggregatedResultsByDay.createdData);
                }
                else if (selectedStep === 'week') {
                    const aggregatedResultsByWeek = aggregateData(dates, createdData, 'week', true);
                    generateLineChart(aggregatedResultsByWeek.dates, aggregatedResultsByWeek.createdData);
                }
                else if (selectedStep === 'month') {
                    const aggregatedResultsByMonth = aggregateData(dates, createdData, 'month', true);
                    generateLineChart(aggregatedResultsByMonth.dates, aggregatedResultsByMonth.createdData);
                }
                else if (selectedStep === 'year') {
                    const aggregatedResultsByYear = aggregateData(dates, createdData, 'year', true);
                    generateLineChart(aggregatedResultsByYear.dates, aggregatedResultsByYear.createdData);
                }
                else {
                    // Сюда потом обработку, когда нефига нет !!!!!!!!!!!!!
                }

                // Генерируйте круговую диаграмму с данными клиентов
                generatePieChart(data.tickets);

                // Инициализируем Vue и таблицу с полученными данными
                initializeVueTable(data.tickets);
            })
            .catch(error => {
                console.error("Произошла ошибка при запросе данных:", error);
                console.error('Ошибка:', error.responseText);
                errorShowToast(`Произошла ошибка при запросе данных: ${error.message}`);
            });
        }
        else if (selectedReport === 'ci'){

        }
        else if (selectedReport === 'movement'){
            
        }
        else {
            // Тут остальные обработки, которых пока нет...
            
        }
    });
});
