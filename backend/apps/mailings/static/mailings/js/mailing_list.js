document.querySelectorAll('.start-mailing').forEach(btn => {
    btn.addEventListener('click', function() {
        fetch(`/mailings/start/${this.dataset.id}/`)
        .then(response => response.json())
        .then(data => {
            showBootstrapToast(data.message, data.status === "started" ? "success" : "danger");
        })
        .catch(error => console.error("Ошибка запроса:", error));
    });
});

// Функция для отображения Bootstrap Toast
function showBootstrapToast(message, type) {
    let toastContainer = document.querySelector(".toast-container");

    if (!toastContainer) {
        toastContainer = document.createElement("div");
        toastContainer.className = "toast-container position-fixed bottom-0 end-0 p-3";
        document.body.appendChild(toastContainer);
    }

    let toast = document.createElement("div");
    toast.className = `toast align-items-center text-bg-${type} border-0 show`;
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "assertive");
    toast.setAttribute("aria-atomic", "true");

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${type === "danger" ? "Ошибка:" : "Успех:"}</strong> ${message}
            </div>
            <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    new bootstrap.Toast(toast, { delay: 5000 }).show();

    // Удаление toasts после анимации исчезновения
    setTimeout(() => toast.remove(), 5500);
}

// Подключение WebSocket
const mailings = document.querySelectorAll('[id^="status-"]');
mailings.forEach(item => {
    let mailingId = item.id.replace("status-", "");

    // Определяем, использовать ws:// или wss://
    let ws_protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    let ws = new WebSocket(`${ws_protocol}${window.location.host}/ws/mailing/${mailingId}/`);

    ws.onmessage = function(event) {
        let data = JSON.parse(event.data);
        let statusElement = document.getElementById(`status-${mailingId}`);

        if (statusElement && data.status) {
            statusElement.innerText = data.status;

            // Обновляем кнопку
            let actionContainer = statusElement.closest("tr").querySelector(".d-flex");
            if (data.status !== "Черновик") {
                actionContainer.innerHTML = `<a href="/mailings/detail/${mailingId}/" class="styled-btn view-result">Результат</a>`;
            }

            console.log("data:", data.status)
            // Показываем алерт только если рассылка завершилась ошибкой
            if (data.status === "Ошибка") {
                showBootstrapToast(`Рассылка #${mailingId} завершилась с ошибкой!`, "danger");
            }
        }
    };

    ws.onerror = function(error) {
        console.error("⚠️ Ошибка WebSocket:", error);
    };
});
