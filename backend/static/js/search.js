document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const searchResults = document.getElementById("searchResults");
    const searchResultsContainer = document.getElementById("searchResultsContainer");

    searchInput.addEventListener("input", function () {
        const query = searchInput.value.trim();

        // Показываем результаты, если 2+ символа
        if (query.length > 1) {
            fetch(`/api/search-clients/?q=${query}`)
                .then(response => response.json())
                .then(data => {
                    if (data.results.length) {
                        searchResults.innerHTML = data.results.map(client => 
                            `<a href="/clients/${client.id}" class="dropdown-item">
                                <i class="bi bi-person"></i> ${client.name}
                            </a>`
                        ).join("");
                        searchResults.style.display = "block";
                        searchResultsContainer.style.display = "flex";
                        searchResults.classList.remove("hidden");
                    } else {
                        closeSearchResults();
                    }
                })
                .catch(error => console.error("Ошибка поиска:", error));
        } else {
            closeSearchResults();
        }
    });

    // Закрываем список при клике вне него
    document.addEventListener("click", function (event) {
        if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
            closeSearchResults();
        }
    });

    function closeSearchResults() {
        searchResults.classList.add("hidden"); // Добавляем анимацию скрытия
        setTimeout(() => {
            searchResults.style.display = "none";
            searchResultsContainer.style.display = "none";
            searchResults.classList.remove("hidden"); // Убираем класс после скрытия
        }, 200); // 200ms совпадает с анимацией fadeOut
    }
});
