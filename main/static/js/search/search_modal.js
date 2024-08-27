document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('serverVersionCheckbox').addEventListener('change', function() {
        document.getElementById('serverVersionInputWrapper').style.display = this.checked ? 'block' : 'none';
    });
    document.getElementById('filterByVersion').addEventListener('change', function() {
        document.getElementById('versionSelectWrapper').style.display = this.checked ? 'block' : 'none';
    });
    document.getElementById('filterByManager').addEventListener('change', function() {
        document.getElementById('managerSelectWrapper').style.display = this.checked ? 'block' : 'none';
    });
    document.getElementById('filterByTariffPlan').addEventListener('change', function() {
        document.getElementById('tariffPlanSelectWrapper').style.display = this.checked ? 'block' : 'none';
    });

    // Удаление неактивных полей перед отправкой формы
    document.getElementById('advancedSearchForm').addEventListener('submit', function(event) {
        if (!document.getElementById('serverVersionCheckbox').checked) {
            document.getElementById('serverVersionInput').disabled = true;
        }
        if (!document.getElementById('filterByVersion').checked) {
            document.getElementById('versionSelect').disabled = true;
        }
        if (!document.getElementById('filterByManager').checked) {
            document.getElementById('managerSelect').disabled = true;
        }
        if (!document.getElementById('filterByTariffPlan').checked) {
            document.getElementById('tariffPlanSelect').disabled = true;
        }
    });

    // Инициализация автозаполнения для версии сервера
    var url = $('#serverVersionInput').data('url');
    $('#serverVersionInput').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: url,
                data: {
                    q: request.term
                },
                success: function(data) {
                    response(data);
                },
                error: function() {
                    response([]);
                }
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $('#serverVersionInput').val(ui.item.value);
            return false;
        }
    });
});
