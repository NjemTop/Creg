$(document).ready(function() {
    // Инициализация Switchery
    var elems = Array.prototype.slice.call(document.querySelectorAll('.js-switch'));
    elems.forEach(function(html) {
        var switchery = new Switchery(html, { size: 'small' });
    });

    // Открытие модального окна и заполнение формы
    $('.edit-btn').on('click', function() {
        var clientId = $(this).data('client-id');
        $('#updateIntegrationModal_' + clientId).modal('show');
    });
});
