document.addEventListener('DOMContentLoaded', function() {
    var contactButtons = document.querySelectorAll('[data-bs-target^="#contactModal_"]');

    // Обработчик клика по кнопке "Контакты"
    contactButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            var clientId = button.getAttribute('data-client-id');
            var contactModal = new bootstrap.Modal(document.getElementById('contactModal_' + clientId));
            
            // Выполнение AJAX-запроса для получения контактов
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var contactsTable = contactModal._element.querySelector('table');
                    contactsTable.innerHTML = xhr.responseText;
                    contactModal.show();
                }
            };
            xhr.open('GET', '/get_contacts/' + clientId + '/');
            xhr.send();
        });
    });
});
