(function() {
    // Получаем все модальные окна
    const modals = document.querySelectorAll('[id^="serviceModal_"]');
    // Параметры авторизации
    const username = 'admin';
    const password = 'ekSkaaiWnK';

    // Для каждого модального окна
    modals.forEach((modal) => {
        // Создаем экземпляр Bootstrap модального окна
        const bsModal = new bootstrap.Modal(modal);
        
        // Добавляем обработчик события "show.bs.modal", который запускается, когда модальное окно открывается
        modal.addEventListener('show.bs.modal', function (event) {
            // Получаем кнопку, которая вызвала модальное окно
            const button = event.relatedTarget;
            // Получаем client ID из атрибутов кнопки
            const clientId = button.getAttribute('data-client-id');
            // Находим элементы в модальном окне
            const manager = document.getElementById(`manager_${clientId}`);
            const service_pack  = document.getElementById(`service_pack_${clientId}`);
            const loyalty = document.getElementById(`loyalty_${clientId}`);
            const managerOtherInput = document.querySelector(`#manager_other_${clientId}`);
            const applyButton = modal.querySelector('.apply-changes');

            // Добавляем обработчик изменения менеджера
            manager.addEventListener('change', (e) => {
                if (e.target.value === 'Другое') {
                    managerOtherInput.style.display = 'block';
                } else {
                    managerOtherInput.style.display = 'none';
                }
            });

            // Отправляем GET-запрос к API для получения данных
            fetch(`/api/servise/client/${clientId}`, { headers: {'Authorization': 'Basic ' + btoa(username + ":" + password)} })
                .then(response => response.json())
                .then(data => {
                    // Если данные успешно получены, обновляем значения в модальном окне
                    if(manager && service_pack && loyalty) {
                        // Проверяем, есть ли у нас данные
                        if (data[0].servise_card !== null) {
                            manager.value = data[0].servise_card.manager;
                            service_pack.value = data[0].servise_card.service_pack;
                            loyalty.value = data[0].servise_card.loyal;
                        } else {
                            // Если данных нет, то выводим сообщение "Данных нет."
                            manager.value = "Данных нет.";
                            service_pack.value = "Данных нет.";
                            loyalty.value = "Данных нет.";
                        }
                    } else {
                        console.error(`Не найдены один или несколько элементов: manager = ${manager}, service_pack = ${service_pack}, loyalty = ${loyalty}`);
                    }

                    // Добавляем обработчик клика на кнопку "Применить"
                    applyButton.addEventListener('click', () => {
                        const servise_card_id = data[0].servise_card.id;
                        const updatedData = {
                            "service_pack": service_pack.value,
                            "manager": manager.value === 'Другое' ? managerOtherInput.value : manager.value,
                            "loyal": loyalty.value
                        };
                        
                        // Отправляем PATCH-запрос к API с обновленными данными
                        fetch(`/api/servise/detail/${servise_card_id}`, {
                            method: 'PATCH',
                            headers: {
                                'Authorization': 'Basic ' + btoa(username + ":" + password),
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(updatedData)
                        })
                        .then(response => {
                            if (response.ok) {
                                return response.json();
                            } else {
                                throw new Error(`Ошибка при отправке запроса: ${response.statusText}`);
                            }
                        })
                        .then(updated => {
                            console.log('Data successfully updated', updated);
                            // Если данные успешно обновлены, выводим уведомление
                            Toastify({
                                text: 'Данные успешно обновлены',
                                backgroundColor: 'linear-gradient(to right, #00b09b, #96c93d)',
                                className: 'success-toast',
                            }).showToast();
                        })
                        .catch(err => {
                            console.error('Error updating data', err);
                            // Если при обновлении данных произошла ошибка, выводим уведомление об ошибке
                            Toastify({
                                text: `Ошибка при обновлении данных: ${err.message}`,
                                backgroundColor: '#ff6347',
                                className: 'error-toast',
                            }).showToast();
                        });
                    });
                })
                .catch(err => {
                    // Если при получении данных произошла ошибка, выводим уведомление об ошибке
                    console.error('Error fetching data', err);
                    Toastify({
                        text: `Ошибка при получении данных: ${err.message}`,
                        backgroundColor: '#ff6347',
                        className: 'error-toast',
                    }).showToast();
                });
        });
    });
})();
