// Получаем кнопку
var buttonScrollUp = document.getElementById("back-to-top");

// Когда пользователь прокручивает вниз на 20 пикселей от верхней части документа, показать кнопку
window.onscroll = function() {
  scrollFunction();
};

function scrollFunction() {
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    buttonScrollUp.style.display = "block";
  } else {
    buttonScrollUp.style.display = "none";
  }
}

// Когда пользователь кликает на кнопку, прокрутить вверх до начала документа
buttonScrollUp.addEventListener('click', function(){
  document.body.scrollTop = 0; // Для Safari
  document.documentElement.scrollTop = 0; // Для Chrome, Firefox, IE и Opera
});
