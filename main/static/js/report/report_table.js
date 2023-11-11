Vue.component('vue-good-table', window["vue-good-table"].VueGoodTable);

const dataTag = document.getElementById('report-data-tag');
const tableData = JSON.parse(dataTag.textContent);

export const app = new Vue({
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
            { label: 'Среднее время ответа', field: 'response_time' },
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
                console.error('Error fetching data:', error);
            });
        },
        getSLADescription(row) {
            return row.sla
              ? 'True - просроченный тикет'
              : 'False - нет просрочки по тикету';
          },
    },
});
