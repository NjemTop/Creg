document.addEventListener('DOMContentLoaded', function() {
    var clientCardModal = new bootstrap.Modal(document.getElementById('clientCardModal'), {
        keyboard: false
    });

    // Обработчик клика по кнопке "Карточка клиента"
    var clientCardButtons = document.querySelectorAll('[data-bs-target="#clientCardModal"]');
    clientCardButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            clientCardModal.show();
        });
    });
});
