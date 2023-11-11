$(document).ready(function () {

    // Обработчик события для копирования пароля
    var clipboard = new ClipboardJS('.copy-account-button', {
        text: function (trigger) {
            return trigger.getAttribute('data-account');
        }
    });

    clipboard.on('success', function (e) {
        e.clearSelection();

        // Используем Toastify для алертов
        successShowToast('УЗ скопирован в буфер обмена');
    });
});
