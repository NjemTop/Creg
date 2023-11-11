// Функция для настройки информативных алертов
function infoShowToast(message) {
    // Используем Toastify для алертов
    Toastify({
        text: message,
        duration: 3000, // Время, в течение которого алерт будет видимым (в миллисекундах)
        newWindow: true,
        close: true,
        gravity: 'bottom', // Положение алерта (вверху или внизу)
        positionLeft: false, // Расположение алерта (слева или справа)
        className: 'info-toast', // Тип алерта
        style: {
            background: 'linear-gradient(to right, #D2691E,  #de861b)' // Цвет фона алерта
        },
    }).showToast();
}

// Функция для настройки успешных алертов
function successShowToast(message) {
    // Используем Toastify для алертов
    Toastify({
        text: message,
        duration: 3000, // Время, в течение которого алерт будет видимым (в миллисекундах)
        newWindow: true,
        close: true,
        gravity: 'bottom', // Положение алерта (вверху или внизу)
        positionLeft: false, // Расположение алерта (слева или справа)
        className: 'success-toast', // Тип алерта
        style: {
            background: 'linear-gradient(to right, #198754, #37a36d)' // Цвет фона алерта
        },
    }).showToast();
}

// Функция для настройки ошибок алертов
function errorShowToast(message) {
    // Используем Toastify для алертов
    Toastify({
        text: message,
        duration: 3000, // Время, в течение которого алерт будет видимым (в миллисекундах)
        newWindow: true,
        close: true,
        gravity: 'bottom', // Положение алерта (вверху или внизу)
        positionLeft: false, // Расположение алерта (слева или справа)
        className: 'error-toast', // Тип алерта
        style: {
            background: 'linear-gradient(to right, #800000, #ab2020)' // Цвет фона алерта
        },
    }).showToast();
}
