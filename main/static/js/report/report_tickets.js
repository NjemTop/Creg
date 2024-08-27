// Ожидаем полной загрузки страницы
document.addEventListener('DOMContentLoaded', function() {

    // "report_table.js"
    Vue.component('vue-good-table', window["vue-good-table"].VueGoodTable);

    const dataTag = document.getElementById('report-data-tag');
    const tableData = JSON.parse(dataTag.textContent);

    const app = new Vue({
        el: '#app',
        data: {
            columns: [
                { label: 'Тикет ID', field: 'ticket_id' },
                { label: 'Создан', field: 'creation_date' },
                { label: 'Тема тикета', field: 'subject' },
                { label: 'Статус', field: 'status' },
                { label: 'Клиент', field: 'client_name' },
                { label: 'Приоритет', field: 'priority' },
                { label: 'Исполнитель', field: 'assignee_name' },
                { label: 'Дата обновления', field: 'updated_at' },
                { label: 'Дата ответа', field: 'last_reply_at' },
                { label: 'SLA', field: 'sla' },
                { label: 'Время SLA', field: 'sla_time' },
                { label: 'Первое время ответа', field: 'first_response_time' },
                { label: 'Причина возникновения', field: 'cause' },
                { label: 'Модуль BoardMaps', field: 'module_boardmaps' },
                { label: 'Сообщений от саппорта', field: 'staff_message' },
            ],
            rows: tableData, // передаем данные непосредственно из таблицы
        },
        methods: {
            fetchData(start_date, end_date) {
                fetch(`/get_report_data/?start_date=${start_date}&end_date=${end_date}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then((response) => response.json())
                .then((data) => {
                    this.rows = data;
                    displayData(data);
                })
                .catch((error) => {
                    console.error('Ошибка получения данных:', error);
                });
            },
            getSLADescription(row) {
                return row.sla
                ? 'True - просроченный тикет'
                : 'False - нет просрочки по тикету';
            },
        },
    });

    // "report_chart.js"
    const chartDataTag = document.getElementById('report-data-tag');
    const chartData = JSON.parse(chartDataTag.textContent);

    let causeCount = {};
    chartData.forEach(entry => {
        const cause = entry.cause;
        causeCount[cause] = (causeCount[cause] || 0) + 1;
    });

    const ctx = document.getElementById('chart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(causeCount),
            datasets: [{
                data: Object.values(causeCount),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40',
                    '#808080',
                ],
                borderColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40',
                    '#808080',
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b);
                            const value = context.raw;
                            const percentage = ((value / total) * 100).toFixed(2);
                            return `${value} (${percentage}%)`;
                        }
                    }
                },
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 20,
                        padding: 10,
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
            },
        }
    });

    const moduleData = {};
    chartData.forEach(entry => {
        const module = entry.module_boardmaps;
        moduleData[module] = (moduleData[module] || 0) + 1;
    });

    const ctxModules = document.getElementById('chart-modules').getContext('2d');
    const chartModules = new Chart(ctxModules, {
        type: 'pie',
        data: {
            labels: Object.keys(moduleData),
            datasets: [{
                data: Object.values(moduleData),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40',
                    '#808080',
                ],
                borderColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40',
                    '#808080',
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b);
                            const value = context.raw;
                            const percentage = ((value / total) * 100).toFixed(2);
                            return `${value} (${percentage}%)`;
                        }
                    }
                },
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 20,
                        padding: 10,
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
            },
        }
    });

    function sortLegend() {
        const dataset = chart.data.datasets[0];
        const labels = chart.data.labels;
        const data = dataset.data;

        const dataArray = labels.map((label, index) => ({
            label: label,
            data: data[index],
            backgroundColor: dataset.backgroundColor[index],
            borderColor: dataset.borderColor[index]
        }));

        dataArray.sort((a, b) => b.data - a.data);

        labels.length = 0;
        data.length = 0;
        dataset.backgroundColor.length = 0;
        dataset.borderColor.length = 0;

        dataArray.forEach(item => {
            labels.push(item.label);
            data.push(item.data);
            dataset.backgroundColor.push(item.backgroundColor);
            dataset.borderColor.push(item.borderColor);
        });

        chart.update();
    }

    function sortModuleLegend() {
        const datasetModules = chartModules.data.datasets[0];
        const labelsModules = chartModules.data.labels;
        const dataModules = datasetModules.data;

        const dataArrayModules = labelsModules.map((label, index) => ({
            label: label,
            data: dataModules[index],
            backgroundColor: datasetModules.backgroundColor[index],
            borderColor: datasetModules.borderColor[index]
        }));

        dataArrayModules.sort((a, b) => b.data - a.data);

        labelsModules.length = 0;
        dataModules.length = 0;
        datasetModules.backgroundColor.length = 0;
        datasetModules.borderColor.length = 0;

        dataArrayModules.forEach(item => {
            labelsModules.push(item.label);
            dataModules.push(item.data);
            datasetModules.backgroundColor.push(item.backgroundColor);
            datasetModules.borderColor.push(item.borderColor);
        });

        chartModules.update();
    }

    // "report.js"

    // Устанавливаем daterangepicker
    const reportDateRange = document.getElementById('report-date-range');
    $(reportDateRange).daterangepicker({
        locale: {
            format: 'YYYY-MM-DD',
            cancelLabel: 'Очистить',
            applyLabel: 'Применить',
            fromLabel: 'От',
            toLabel: 'До',
            customRangeLabel: 'Выбрать даты',
            daysOfWeek: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
            monthNames: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        },
        opens: 'right'
    });

    function displayDataByDateRange(startDate, endDate) {
        // Запрашиваем данные с сервера с переданными параметрами даты
        app.fetchData(startDate.format('YYYY-MM-DD'), endDate.format('YYYY-MM-DD'));
    }

    $(reportDateRange).on('apply.daterangepicker', function (ev, picker) {
        displayDataByDateRange(picker.startDate, picker.endDate);
    });

    // Функция для отображения данных
    function displayData(data) {
        // Очищаем массив перед добавлением новых записей
        app.rows = [];

        data.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${entry.ticket_id}</td>
                <td>${entry.subject}</td>
                <td>${entry.creation_date}</td>
                <td>${entry.status}</td>
                <td>${entry.client_name}</td>
                <td>${entry.priority}</td>
                <td>${entry.assignee_name}</td>
                <td>${entry.updated_at}</td>
                <td>${entry.last_reply_at}</td>
                <td>${entry.sla}</td>
                <td>${entry.sla_time}</td>
                <td>${entry.first_response_time}</td>
                <td>${entry.cause}</td>
                <td>${entry.module_boardmaps}</td>
                <td>${entry.staff_message}</td>
            `;
            app.rows.push(entry);
        });

        // Очищаем графики перед обновлением данных
        clearChart(chart);
        clearChart(chartModules);

        // Обновляем графики после фильтрации
        updateCauseChartData(data);
        updateModuleChartData(data);
    }

    // Функция для очистки графика
    function clearChart(chart) {
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        chart.update();
    }

    // Функция для обновления данных графика "Причины возникновения"
    function updateCauseChartData(filteredData) {
        let causeCount = {};

        filteredData.forEach(entry => {
            const cause = entry.cause;
            causeCount[cause] = (causeCount[cause] || 0) + 1;
        });

        // Обновляем график
        chart.data.labels = Object.keys(causeCount);
        chart.data.datasets[0].data = Object.values(causeCount);
        chart.update();
    }

    // Функция для обновления данных графика "Модули"
    function updateModuleChartData(filteredData) {
        let moduleCount = {};

        filteredData.forEach(entry => {
            const module = entry.module_boardmaps;
            moduleCount[module] = (moduleCount[module] || 0) + 1;
        });

        // Обновляем график "Модули"
        chartModules.data.labels = Object.keys(moduleCount);
        chartModules.data.datasets[0].data = Object.values(moduleCount);
        chartModules.update();
    }

    // Изначально показываем данные за текущую неделю
    const thisMonday = moment().startOf('week').add(1, 'days'); // Начало текущей недели, понедельник
    const today = moment(); // Сегодняшний день

    $(reportDateRange).data('daterangepicker').setStartDate(thisMonday);
    $(reportDateRange).data('daterangepicker').setEndDate(today);
    displayDataByDateRange(thisMonday, today);

    // Вызывайте функции сортировки легенды после создания графиков
    sortLegend();
    sortModuleLegend();
});