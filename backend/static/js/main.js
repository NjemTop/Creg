document.addEventListener("DOMContentLoaded", function () {
    // Включаем Bootstrap tooltips
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));

});

// Определяем тему до загрузки страницы -->
(function() {
const isDark = localStorage.getItem("darkMode") === "true";
if (isDark) {
    document.documentElement.classList.add("dark-mode"); 
}
// Показываем страницу после проставления нужной темы
document.documentElement.style.visibility = "visible";
})();

// Переключение темы
document.addEventListener("DOMContentLoaded", function () {
    const themeToggle = document.getElementById("themeToggle");

    // Проверяем, есть ли 'dark-mode' на <html>
    const isDarkMode = document.documentElement.classList.contains("dark-mode");
    themeToggle.innerHTML = isDarkMode
        ? '<i class="bi bi-brightness-high"></i>'
        : '<i class="bi bi-moon"></i>';

    themeToggle.addEventListener("click", function () {
        // Переключаем класс на <html>
        document.documentElement.classList.toggle("dark-mode");
        const darkModeEnabled = document.documentElement.classList.contains("dark-mode");

        // Запоминаем состояние
        localStorage.setItem("darkMode", darkModeEnabled);

        // Меняем иконку
        themeToggle.innerHTML = darkModeEnabled
            ? '<i class="bi bi-brightness-high"></i>'
            : '<i class="bi bi-moon"></i>';
    });
});
