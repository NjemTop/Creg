document.addEventListener('DOMContentLoaded', function() {
    // Добавляем обработчик для закрытия всех модальных окон при клике на пустую область
    var modalBackdrops = document.querySelectorAll('.modal-backdrop');
    modalBackdrops.forEach(function(backdrop) {
        backdrop.addEventListener('click', function() {
            var openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                var modalInstance = bootstrap.Modal.getInstance(modal);
                modalInstance.hide();
            });
            // Дополнительно: перенаправить на страницу списка клиентов
            window.location.href = '/clients/';
        });
    });

    var contactButtons = document.querySelectorAll('[data-bs-target^="#contactModal_"]');

    // Обработчик клика по кнопке "Контакты"
    contactButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            var clientId = button.getAttribute('data-client-id');
            var contactModal = new bootstrap.Modal(document.getElementById('contactModal_' + clientId));
            
            // Перед показом модального окна контактов
            contactModal._element.addEventListener('show.bs.modal', function() {
                var modalBackdrop = document.querySelector('.modal-backdrop');
                if (modalBackdrop) {
                    modalBackdrop.parentNode.removeChild(modalBackdrop); // Удаляем фон, если есть
                }
            });

            // После закрытия модального окна контактов
            contactModal._element.addEventListener('hidden.bs.modal', function() {
                var clientCardModal = new bootstrap.Modal(document.getElementById('clientCardModal_' + clientId));
                clientCardModal.show(); // Показываем модальное окно карточки клиента после закрытия списка контактов
            });

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
