document.addEventListener('DOMContentLoaded', function() {
    // Обработчик клика по кнопке "Карточка клиента"
    var clientCardButtons = document.querySelectorAll('[data-bs-target^="#clientCardModal"]');
    clientCardButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            var clientId = button.getAttribute('data-client-id');
            var clientCardModal = new bootstrap.Modal(document.getElementById('clientCardModal_' + clientId));
            
            // Перед показом модального окна карточки клиента
            clientCardModal._element.addEventListener('show.bs.modal', function() {
                var modalBackdrop = document.querySelector('.modal-backdrop');
                if (modalBackdrop) {
                    modalBackdrop.parentNode.removeChild(modalBackdrop); // Удаляем фон, если есть
                }
            });

            clientCardModal.show();
        });
    });
});
