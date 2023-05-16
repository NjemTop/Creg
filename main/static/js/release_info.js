$(document).ready(function () {
    const releaseSelect = $('#release-number-select');
    const dataTable = $('#data-table tbody');

    function displayData(dataJson) {
        dataTable.empty();
        dataJson.forEach(item => {
            dataTable.append(`
                <tr>
                    <td>${item['Дата_рассылки']}</td>
                    <td>${item['Номер_релиза']}</td>
                    <td>${item['Наименование_клиента']}</td>
                    <td>${item['Основной_контакт']}</td>
                    <td>${item['Копия']}</td>
                </tr>
            `);
        });
    }

    releaseSelect.on('change', function () {
        const releaseNumber = this.value;

        $.ajax({
            url: 'http://194.37.1.214:3030/api/data_release/?release_number=' + releaseNumber,
            headers: {
                'Authorization': 'Basic ' + btoa('admin:ekSkaaiWnK'),
            },
            dataType: 'json',
            success: function (data) {
                displayData(data);
            },
            error: function(jqXHR, textStatus, errorThrown) {
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
            data.sort((a, b) => new Date(b.date) - new Date(a.date));
            const latestRelease = data[0].release_number;
            releaseSelect.val(latestRelease);
            releaseSelect.trigger('change');
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error(textStatus, errorThrown);
        }
    });
});
