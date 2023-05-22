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
                        value: item.client_name
                    };
                }));
            });
        },
        select: function(event, ui) {
            // Обработка выбранного элемента.
            console.log("Selected item:", ui.item);  // Вывод информации о выбранном элементе в консоль.
        }
    });
});
