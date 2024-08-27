document.addEventListener("DOMContentLoaded", function() {
    Vue.component('vue-good-table', window["vue-good-table"].VueGoodTable);

    try {
        new Vue({
            el: '#app',
            data: {
                columns: [
                    { label: 'Наименование клиента', field: 'client_name' },
                    { label: 'Версия сервера', field: 'server_version' },
                    { label: 'Дата обновления', field: 'update_date' },
                    { label: 'Менеджер', field: 'manager' },
                    { label: 'Тарифный план', field: 'service_pack' },
                    { label: 'Примечания', field: 'notes' },
                ],
                rows: window.searchResultsData || [],
            },
            template: `
                <div id="app">
                    <vue-good-table :columns="columns" :rows="rows"></vue-good-table>
                </div>
            `,
        });
    } catch (error) {
        console.error('Ошибка при инициализации Vue:', error);
    }

    $('#serverVersionCheckbox').change(function() {
        if ($(this).is(':checked')) {
            $('#serverVersionInputWrapper').show();
        } else {
            $('#serverVersionInputWrapper').hide();
        }
    });

    $('#showAllClients').click(function() {
        window.location.href = '/search_results?show_all=true';
    });
});
