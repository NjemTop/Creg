document.addEventListener('DOMContentLoaded', function () {
    // Получаем токен доступа
    fetch('/api/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: 'admin',
            password: 'ekSkaaiWnK',
        }),
    })
    .then(response => response.json())
    .then(data => {
        const accessToken = data.access;

        // Вызываем функцию initializeSwitchery из файла switchery_setup.js
        initializeSwitchery('.client-active-checkbox');

        let checkboxes = document.querySelectorAll('input[type="checkbox"].client-active-checkbox');

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function (event) {
                let clientId = this.id.split('_')[1];
                let isActive = this.checked;

                fetch(`/api/clients/${clientId}/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${accessToken}`,
                    },
                    body: JSON.stringify({
                        "contact_status": isActive
                    }),
                })
                .then(response => response.json())
                .then(data => {
                    successShowToast('Запрос успешно выполнен');
                })
                .catch((error) => {
                    console.error('Ошибка:', error);
                    errorShowToast(`Ошибка при обновлении данных: ${error.message}`);
                });
            });
        });
    })
    .catch((error) => {
        console.error('Ошибка:', error);
        errorShowToast(`Ошибка при обновлении данных: ${error.message}`);
    });
});
