document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("local-login-form");
    const toggleButton = document.getElementById("toggle-local-login");

    if (toggleButton) {
        toggleButton.addEventListener("click", function () {
            loginForm.style.display = (loginForm.style.display === "none" || loginForm.style.display === "") ? "block" : "none";
        });
    }
});
