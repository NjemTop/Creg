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

        let checkboxes = document.querySelectorAll('input[type="checkbox"].client-active-checkbox');

        checkboxes.forEach(checkbox => {
            let switchery = new Switchery(checkbox, {
                size: 'small', // Размер свича ('small', 'default', 'large')
                color: '#ff9e4c', // Цвет активного свича
                secondaryColor: '#808080', // Цвет не активного свеча
                jackColor: '#fff',
                jackSecondaryColor: '#fff'
            });

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
                    console.log('Success:', data);
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
            });
        });
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});
