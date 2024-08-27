document.addEventListener('DOMContentLoaded', function() {
    var message = localStorage.getItem('toastMessage');
    if (message) {
        successShowToast(message);
        localStorage.removeItem('toastMessage');
    }
    var suspendButton = document.querySelector('.suspend-client-button');
    var activateButton = document.querySelector('.activate-client-button');

    if (suspendButton) {
        suspendButton.addEventListener('click', function() {
            updateClientStatus('suspend');
        });
    }

    if (activateButton) {
        activateButton.addEventListener('click', function() {
            updateClientStatus('activate');
        });
    }
});

function updateClientStatus(action) {
    var clientId = document.querySelector('.section-title').getAttribute('data-client-id');
    if (!clientId) {
        console.log('ID клиента не найден.');
        return;
    }

    var confirmText = action === 'suspend' ? 'Вы действительно хотите снять клиента с ТП?' : 'Вы действительно хотите перевести клиента на ТП?';
    var confirmAction = confirm(confirmText);
    if (!confirmAction) {
        console.log('Действие отменено пользователем.');
        return;
    }

    fetch(`/apiv2/client/${clientId}/${action}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            // Тело запроса
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Сетевая ошибка при попытке обновить статус клиента.');
    })
    .then(data => {
        console.log('Статус клиента успешно обновлен:', data);
        localStorage.setItem('toastMessage', "Данные успешно обновлены!");
        window.location.reload();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        errorShowToast(`Ошибка при отправке данных: ${error.message}`);
    });
}
