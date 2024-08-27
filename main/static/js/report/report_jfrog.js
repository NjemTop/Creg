const reportDateRange = document.getElementById('report-date-range');

// Инициализация Select2
$(document).ready(function() {
    $('#account-select').select2();
    $('#version-select').select2();
});

const fetchData = (start, end, accounts, versions) => {
    const accountParams = accounts.map(a => `account=${a}`).join('&');
    const versionParams = versions.map(v => `version=${v}`).join('&');
    fetch(`/api2/get_report_jfrog/?start=${start}&end=${end}&${accountParams}&${versionParams}`)
        .then(response => response.json())
        .then(data => {
            // Обновите данные таблицы
            app.rows = data;
        });
};

// Получение данных для фильтров при загрузке страницы
fetch('/api2/get_unique_accounts/')
    .then(response => response.json())
    .then(data => {
        app.allAccounts = data;
        $('#account-select').empty();
        data.forEach(account => {
            var newOption = new Option(account, account, false, false);
            $('#account-select').append(newOption).trigger('change');
        });
    });

fetch('/api2/get_unique_versions/')
    .then(response => response.json())
    .then(data => {
        app.allVersions = data;
        $('#version-select').empty();
        data.forEach(version => {
            var newOption = new Option(version, version, false, false);
            $('#version-select').append(newOption).trigger('change');
        });
    });

const endDate = moment();
const startDate = moment().subtract(1, 'days');

$(reportDateRange).daterangepicker({
    locale: {
        format: 'YYYY-MM-DD'
    },
    opens: 'right',
    startDate: startDate,
    endDate: endDate
}, function(start, end, label) {
    fetchData(start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'), app.selectedAccounts, app.selectedVersions);
});

// Применение фильтров
document.getElementById('apply-filters').addEventListener('click', () => {
    const selectedAccounts = Array.from(document.getElementById('account-select').selectedOptions).map(o => o.value);
    const selectedVersions = Array.from(document.getElementById('version-select').selectedOptions).map(o => o.value);
    fetchData(startDate.format('YYYY-MM-DD'), endDate.format('YYYY-MM-DD'), selectedAccounts, selectedVersions);
});

const app = new Vue({
    el: '#app',
    data: {
        columns: [
            { label: 'Дата', field: 'date' },
            { label: 'Учётная запись', field: 'account_name' },
            { label: 'Образ', field: 'image_name' },
            { label: 'Версия', field: 'version_download' },
            { label: 'IP-адрес', field: 'ip_address' },
        ],
        rows: [],
        selectedAccounts: [],
        selectedVersions: [],
        allAccounts: [],
        allVersions: [],
    },
    mounted() {
        this.$nextTick(() => {
            const accountSelect = document.getElementById('account-select');
            const versionSelect = document.getElementById('version-select');

            this.allAccounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account;
                option.text = account;
                accountSelect.add(option);
            });

            this.allVersions.forEach(version => {
                const option = document.createElement('option');
                option.value = version;
                option.text = version;
                versionSelect.add(option);
            });
        });
    },
});

// Загрузите данные за последние два дня при загрузке страницы
fetchData(startDate.format('YYYY-MM-DD'), endDate.format('YYYY-MM-DD'), [], []);
