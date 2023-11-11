$(document).ready(function () {
    // Переменная для хранения таймера показа пароля
    var passwordVisible = false;

    $('.show-password-button').mousedown(function () {
        var passwordField = $(this).prev('.password-hidden');
        var passwordSpinner = $(this).find('.password-spinner');
        // Указываем класс, который глазика (будет скрываться при нажатии)
        var eyeIcon = $(this).find('.fa-low-vision');

        var actualPassword = passwordField.data('password');

        if (!passwordVisible) {
            passwordSpinner.show(); // Показываем иконку вращающегося колесика
            eyeIcon.hide(); // Скрываем иконку глаза
            passwordField.text(actualPassword);
            passwordField.addClass('password-visible');
            passwordVisible = true;

            // Устанавливаем таймер на скрытие пароля через 5 секунд
            setTimeout(function () {
                passwordField.text('********');
                passwordField.removeClass('password-visible');
                passwordVisible = false;
                passwordSpinner.hide(); // Скрываем иконку вращающегося колесика
                eyeIcon.show(); // Показываем иконку глаза
            }, 5000);
        } else {
            // Если пароль уже виден, скрываем его
            passwordField.text('********');
            passwordField.removeClass('password-visible');
            passwordVisible = false;
            passwordSpinner.hide(); // Скрываем иконку вращающегося колесика
            eyeIcon.show(); // Показываем иконку глаза
        }
    });

    // Обработчик события для копирования пароля
    var clipboard = new ClipboardJS('.copy-password-button', {
        text: function (trigger) {
            return trigger.getAttribute('data-password');
        }
    });

    clipboard.on('success', function (e) {
        e.clearSelection();
        successShowToast('Пароль скопирован в буфер обмена');
    });
});
