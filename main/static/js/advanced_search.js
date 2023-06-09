// Загружаем контент документа
document.addEventListener("DOMContentLoaded", function() {
    // Регестрируем компонент vue-good-table
    Vue.component('vue-good-table', window["vue-good-table"].VueGoodTable);
  
    try {
      // Создаём новый экземпляр Vue
      new Vue({
        el: '#app',
        data: {
          columns: [
            // Определяем колонки для таблицы
            { label: 'Наименование клиента', field: 'client_name' },
            { label: 'Версия сервера', field: 'server_version' },
            { label: 'Дата обновления', field: 'update_date' },
            // Потом другие колонки
          ],
          // Используем данные из шаблона, если они есть; в противном случае используем пустой массив
          rows: window.searchResultsData || [],
        },
        // Отрисовываем таблицу с заданными столбцами и строками
        template: `
          <div id="app">
            <vue-good-table :columns="columns" :rows="rows"></vue-good-table>
          </div>
        `,
      });
    } catch (error) {
      // В случае ошибки выводим ее в консоль
      console.error('Ошибка при инициализации Vue:', error);
    }
  });
  