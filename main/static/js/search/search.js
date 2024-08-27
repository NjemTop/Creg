// Функция для получения результатов поиска с сервера.
function getSearchResults(searchText, callback) {

    // URL для запроса на сервер.
    var url = "/api/client_search?q=" + searchText;

    // Учетные данные для Basic Auth.
    var username = "admin";
    var password = "ekSkaaiWnK";

    // Отправка запроса на сервер.
    fetch(url, {
        headers: {
            'Authorization': 'Basic ' + btoa(username + ":" + password)
        }
    })
    .then(response => {
        // Проверка статуса ответа.
        if (!response.ok) {
            throw new Error("HTTP status " + response.status);
        }
        return response.json();
    })
    .then(data => {
        callback(data);  // Вызов callback-функции с полученными данными.
    })
    .catch(error => console.error('Error:', error));  // Обработка возможных ошибок.
}

// Инициализация автозаполнения при загрузке документа.
$(document).ready(function() {
    $( "#regularSearch" ).autocomplete({
        minLength: 2,  // Минимальное количество символов, необходимых для начала поиска.
        source: function(request, response) {

            // Получение результатов поиска с сервера и передача их в функцию response для отображения в интерфейсе.
            getSearchResults(request.term, function(data) {
                response($.map(data, function(item) {
                    return {
                        label: item.client_name + " (Version: " + (item.clients_card__tech_information__server_version || 'N/A') + ")",
                        value: item.client_name,
                        id: item.id  // Добавление идентификатора клиента
                    };
                }));
            });
        },
        select: function(event, ui) {
            // Получение идентификатора клиента из выбранного элемента.
            var clientId = ui.item.id;
        
            // Формирование URL на основе идентификатора клиента.
            var clientUrl = "/client/" + clientId + "/";
        
            // Перенаправление на страницу клиента.
            window.location.href = clientUrl;
        }
    });
});
