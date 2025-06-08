document.addEventListener("DOMContentLoaded", function () {
    const logContainer = document.getElementById("log-container");
    const mailingStatus = document.getElementById("mailing-status");
    const mailingId = document.getElementById("mailing-container").dataset.mailingId;

    const searchInput = document.getElementById("search-input");
    const rows = document.querySelectorAll(".recipient-row");

    let ws_protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    let socket = new WebSocket(`${ws_protocol}${window.location.host}/ws/mailing/${mailingId}/`);

    socket.onmessage = function (event) {
        let data = JSON.parse(event.data);

        if (data.status) {
            mailingStatus.innerText = data.status;
        }

        if (data.log) {
            let logItem = document.createElement("li");
            logItem.className = `log-entry log-${data.log.level} new-log`;
            logItem.innerHTML = `
                <span class="log-time">[${new Date(data.log.timestamp).toLocaleString()}]</span>
                <span class="log-level">(${data.log.level.toUpperCase()})</span>
                <span class="log-message">${data.log.message}</span>
            `;
        
            logContainer.appendChild(logItem);
        
            // Снимаем "новое" через 1.5 секунды
            setTimeout(() => logItem.classList.remove("new-log"), 1500);
        
            // Скроллим вниз, только если пользователь не листает вверх
            const isScrolledToBottom = logContainer.scrollHeight - logContainer.scrollTop <= logContainer.clientHeight + 10;
            if (isScrolledToBottom) {
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        }
    };

    socket.onerror = function (error) {
        let logItem = document.createElement("li");
        logItem.className = "log-entry log-error";
        logItem.innerHTML = `<span class="log-time">[${new Date().toLocaleString()}]</span> <span class="log-level">(ERROR)</span> <span class="log-message">Ошибка WebSocket: ${error}</span>`;
        logContainer.appendChild(logItem);
        console.error("⚠️ Ошибка WebSocket:", error);
    };

    searchInput.addEventListener("input", function () {
        const filter = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll(".recipient-row");
        
        const clientGroups = {};
    
        rows.forEach(row => {
            const clientId = row.dataset.clientId;
            const email = row.dataset.email.toLowerCase();
            const clientName = row.dataset.clientName.toLowerCase();
    
            if (!clientGroups[clientId]) {
                clientGroups[clientId] = {
                    clientName: row.dataset.clientName,
                    rows: [],
                    visibleRows: []
                };
            }
            
            clientGroups[clientId].rows.push(row);
    
            const match = email.includes(filter) || clientName.includes(filter);
            row.style.display = match ? "" : "none";
            if (match) clientGroups[clientId].visibleRows.push(row);
    
            // Удаляем старую ячейку с именем клиента в каждой строке (чтобы сбросить)
            const oldClientCell = row.querySelector('.client-name-cell');
            if (oldClientCell) {
                oldClientCell.remove();
            }
        });
    
        Object.values(clientGroups).forEach(group => {
            const visibleRows = group.visibleRows;
    
            if (visibleRows.length > 0) {
                // Создаём ячейку клиента для первой видимой строки
                const firstRow = visibleRows[0];
                const clientCell = document.createElement('td');
                clientCell.className = 'client-name-cell';
                clientCell.rowSpan = visibleRows.length;
                clientCell.innerText = group.clientName;
    
                // Вставляем новую ячейку на первое место в первой видимой строке
                firstRow.prepend(clientCell);
            }
        });
    });

    // Фильтрация по уровню
    document.querySelectorAll(".log-filter-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            document.querySelectorAll(".log-filter-btn").forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            const level = this.dataset.level;
            document.querySelectorAll(".log-entry").forEach(entry => {
                const matches = level === "" || entry.classList.contains(`log-${level}`);
                entry.style.display = matches ? "" : "none";
            });
        });
    });

    // Поиск по сообщению
    const logSearch = document.getElementById("log-search");
    logSearch?.addEventListener("input", function () {
        const keyword = this.value.toLowerCase();
        document.querySelectorAll(".log-entry").forEach(entry => {
            const msg = entry.querySelector(".log-message")?.innerText.toLowerCase() || "";
            entry.style.display = msg.includes(keyword) ? "" : "none";
        });
    });

    const stopBtn = document.getElementById("stop-mailing-btn");
    const repeatBtn = document.getElementById("repeat-mailing-btn");

    if (stopBtn) {
        stopBtn.addEventListener("click", function () {
            if (confirm("Вы уверены, что хотите остановить рассылку?")) {
                fetch(`/mailings/stop/${mailingId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                    }
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    location.reload();
                });
            }
        });
    }

    if (repeatBtn) {
        repeatBtn.addEventListener("click", function () {
            if (confirm("Повторить рассылку с теми же параметрами?")) {
                fetch(`/mailings/repeat/${mailingId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                    }
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    }
                });
            }
        });
    }

    function getCSRFToken() {
        return document.cookie.split('; ').find(row => row.startsWith('csrftoken')).split('=')[1];
    }
});
