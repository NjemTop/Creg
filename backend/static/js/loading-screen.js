window.addEventListener("load", function() {
    let loadingScreen = document.getElementById("loading-screen");
    if (loadingScreen) {
        loadingScreen.style.opacity = "0"; // Плавное исчезновение
        setTimeout(() => {
            loadingScreen.style.display = "none";
        }, 500); // Через 0.5 сек скроем совсем
    }
});
