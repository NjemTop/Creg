function initializeSwitchery(selector, options = {}) {
    let defaults = {
        size: 'small',
        color: '#fcd0c0', // Цвет активного переключателя
        secondaryColor: '#e8e0dc', // Цвет неактивного переключателя
        jackColor: '#f77343', // Цвет элемента, который переключается (переключатель)
        jackSecondaryColor: '#fafafa' // Цвет элемента, который переключается в неактивном состоянии
    };

    let switches = Array.prototype.slice.call(document.querySelectorAll(selector));
    switches.forEach(function (element) {
        new Switchery(element, {...defaults, ...options});
    });
}

$(document).ready(function () {
    // Выбор элементов с названиями классамов и затем инициализируем их с помощью фреимворка Switchery
    var techinfoToggles = Array.prototype.slice.call(document.querySelectorAll('.techinfo-toggle'));
    var integrationToggles = Array.prototype.slice.call(document.querySelectorAll('.integration-toggle'));
    var moduleToggles = Array.prototype.slice.call(document.querySelectorAll('.module-toggle'));

    techinfoToggles.forEach(function (toggle) {
        new Switchery(toggle, {
            size: 'small',
            color: '#fcd0c0', // Цвет активного переключателя
            secondaryColor: '#e8e0dc', // Цвет неактивного переключателя
            jackColor: '#f77343', // Цвет элемента, который переключается (переключатель)
            jackSecondaryColor: '#fafafa' // Цвет элемента, который переключается в неактивном состоянии
        });
    });

    integrationToggles.forEach(function (toggle) {
        new Switchery(toggle, {
            size: 'small',
            color: '#fcd0c0', // Цвет активного переключателя
            secondaryColor: '#e8e0dc', // Цвет неактивного переключателя
            jackColor: '#f77343', // Цвет элемента, который переключается (переключатель)
            jackSecondaryColor: '#fafafa' // Цвет элемента, который переключается в неактивном состоянии
        });
    });

    moduleToggles.forEach(function (toggle) {
        new Switchery(toggle, {
            size: 'small',
            color: '#fcd0c0', // Цвет активного переключателя
            secondaryColor: '#e8e0dc', // Цвет неактивного переключателя
            jackColor: '#f77343', // Цвет элемента, который переключается (переключатель)
            jackSecondaryColor: '#fafafa' // Цвет элемента, который переключается в неактивном состоянии
        });
    });
});