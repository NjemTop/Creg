var deletedRows = []; // Глобальный массив для хранения ID удаленных строк

$(document).ready(function() {
    var $editButton = $('.edit-button');
    var $saveButton = $('.save-button');
    var $cancelButton = $('.cancel-button');
    var $addRowButton = $('.add-row-button');

    // Переключение на режим редактирования
    $editButton.click(() => {
        enterEditMode();
    });

    // Сохранение изменений
    $saveButton.click(() => {
        saveChanges();
        exitEditMode();
    });

    // Отмена редактирования
    $cancelButton.click(() => {
        cancelEdit();
        exitEditMode();
    });

    // Добавление новой строки
    $addRowButton.click(function() {
        var tableType = $(this).data('table-type');
        var tbodyId = tableType + '-tbody'; // Создаем идентификатор на основе типа таблицы
        addNewRow(tableType, tbodyId); // Передаем tbodyId в функцию
    });

    // Удаление конкретной строки
    $('body').on('click', '.delete-row-button', function() {
        var $row = $(this).closest('tr');
        var tableType = $row.closest('tbody').attr('id'); // Получаем ID родительского элемента tbody
        if ($('tbody tr').length > 1) {
            // Если у строки есть data-row-id, сохраняем его в массив
            var rowId = $row.data('row-id');
            if (rowId) {
                deletedRows.push({ id: rowId, type: tableType }); // Сохраняем ID и тип таблицы
            }
            $row.remove();
        } else {
            alert("Необходимо оставить хотя бы одну строку");
        }
    });
});

// Функция для перехода в режим редактирования страницы
function enterEditMode() {
    try {
        var $editableFields = $('.editable, .editable-select, .password-hidden');
        var $editableDates = $('.editable-date, .techinfo-toggle');
        var $tbody = $('tbody');

        // При входе в режим редактирования сохраняем исходные значения полей
        $editableFields.each(function() {
            var $this = $(this);
            $this.attr('data-original-content', $this.html());
            $tbody.attr('data-original-table', $tbody.html());
        });

        $editableDates.each(function() {
            var $this = $(this);
            $this.attr('data-original-content', $this.is('input[type="checkbox"]') ? $this.is(':checked').toString() : $this.text());
        });

        // Скрываем кнопки копирования и показываем кнопки в редакторе (сохранения и отмены изменений)
        $('.edit-button, .copy-account-button').hide();
        $('.save-button, .cancel-button').show();
        $('.add-row-button, .delete-row-button, .delete-column').show();

        initializeCalendar();
        initializeTextFields();
        initializeSelectFields();
        

        // Устанавливаем атрибут data-edited для строки, которая редактируется
        $('.editable').on('input', function() {
            $(this).closest('tr').attr('data-edited', 'true');
        });

        // Показываем поля ввода для редактирования паролей
        $('.password-hidden').each(function() {
            var $this = $(this);
            var currentPassword = $this.data('password');
            var input = $('<input>', {
                type: 'text',
                class: 'editField password-input',
                value: currentPassword
            });
            $this.html(input);
            $this.siblings('.show-password-button, .copy-password-button').hide();
        });

        setupEventHandlers();
    } catch (error) {
        console.error('Ошибка при заходе в редактор:', error);
        errorShowToast('Ошибка при заходе в редактор:', error);
    }
}

// Функция для сохранения изменений на странице
function saveChanges() {
    try {
        saveTextFields();
        saveSelectFields();
        savePasswordFields();

        // Обработка изменений в таблицах
        saveChangesForTable('contact', '#contact-tbody', ['name', 'position', 'email', 'number', 'notification_update']);
        saveChangesForTable('connect_info', '#connect_info-tbody', ['name', 'account', 'password']);
        saveChangesForTable('tech_account', '#tech_account-tbody', ['description', 'account', 'password']);
        saveChangesForTable('bm_server', '#bm_server-tbody', ['circuit', 'servers_name', 'servers_adress', 'operation_system', 'url', 'role']);

        // Обработка изменений в разделах (не таблицах)
        saveChangesForSection('service-section', 'service_card');
        saveChangesForSection('techinfo-section', 'tech_info');
        saveChangesForSection('vpn_info-section', 'connection_info');
        saveChangesForSection('technote-section', 'tech_note');

        // Отправка запросов на удаление для удаленных строк
        if (deletedRows.length > 0) {
            deletedRows.forEach(function(row) {
                var endpoint;
                switch (row.type) {
                    case 'connect_info-tbody':
                        endpoint = `/apiv2/connect_info/delete/${row.id}/`;
                        break;
                    case 'tech_account-tbody':
                        endpoint = `/apiv2/tech_account/delete/${row.id}/`;
                        break;
                    default:
                        endpoint = `/apiv2/contact/delete/${row.id}/`;
                }
                sendRequest('DELETE', endpoint, {}, function(data) {
                    console.log('Строка удалена:', data);
                });
            });

            // Очистка массива удаленных строк после отправки запросов
            deletedRows = [];
        }

        successShowToast("Данные успешно обновлены!");

        // Задержка перед перезагрузкой страницы
        setTimeout(function() {
            location.reload();
        }, 2000); // 2000 миллисекунд (2 секунды) задержки

    } catch (error) {
        console.error('Ошибка при сохранении данных:', error);
        errorShowToast('Ошибка при сохранении данных:', error);
    }
}

// Функция отмены всех изменений из режима редактирования
function cancelEdit() {
    try {
        // Возвращение всех полей к их первоначальному состоянию
        $('.editable, .editable-select, .password-hidden').each(function() {
            var $this = $(this);
            var originalContent = $this.attr('data-original-content');
            $this.html(originalContent);
            $this.siblings('.show-password-button, .copy-password-button').show();
            // Возвращаем таблицу к её первоначальному состоянию
            $('tbody').html($('tbody').attr('data-original-table'));
        });
    } catch (error) {
        console.error('Ошибка при отмене изменений в редакторе:', error);
        errorShowToast('Ошибка при отмене изменений в редакторе:', error);
    }
}

// Функция выхода из режима редактирования
function exitEditMode() {
    try {
        $('.save-button, .cancel-button').hide();
        $('.add-row-button, .delete-row-button').hide();
        $('.delete-column').hide();
        $('.edit-button').show();
    } catch (error) {
        console.error('Ошибка при выходе из редакторе:', error);
        errorShowToast('Ошибка при выходе из редакторе:', error);
    }
}

// Функция для инициализации текстовых полей в режиме редактирования
function initializeTextFields() {
    $('.editable').each(function() {
        var content;
        var $this = $(this);
        // Проверяем, является ли элемент блоком <pre>
        if ($this.is('pre')) {
            // Для блоков <pre> используем <textarea>, получаем HTML-содержимое
            content = $this.html().replace(/<br\s*[\/]?>/gi, "\n").replace(/<a.*?>(.*?)<\/a>/gi, "$1");
            $this.html('<textarea class="editField" style="width: 30%; height: 150px;">' + content + '</textarea>');
        } else if ($this.find('a').length > 0) {
            // Для URL-адресов извлекаем URL из атрибута href
            content = $this.find('a').attr('href');
            $this.html('<input type="text" class="editField" value="' + content + '" />');
        } else {
            content = $this.html();
            $this.html('<input type="text" class="editField" value="' + content + '" />');
        }
    });
}

// Функция инициализации "daterangepicker" для поля ввода даты и времени
function initializeCalendar(){
    $('.editable-date').daterangepicker({
        singleDatePicker: true,
        showDropdowns: true,
        locale: {
            format: 'DD MMMM YYYY', // Формат, который вы хотите использовать для отображения
            daysOfWeek: ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
            monthNames: [
                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
                "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
            ]
        }
    });

    $('.editable-date').on('apply.daterangepicker', function(ev, picker) {
        var $this = $(this);
        // Преобразование выбранной даты в нужный формат (YYYY-MM-DD)
        var formattedDate = picker.startDate.format('YYYY-MM-DD');
        // Установка отформатированной даты в атрибут data-date у элемента
        $this.attr('data-date', formattedDate);
        // Обновляем текстовое содержимое элемента
        $this.text(formattedDate);
    });
}

// Функция для инициализации выпадающих списков
function initializeSelectFields() {
    $('.editable-select').each(function() {
        var $this = $(this);
        let currentValue = $this.text();
        let options = $this.data('options').split(',').filter(option => option.trim() !== ''); // Фильтрация пустых элементов
        let select = $('<select class="editSelect"></select>');
        
        options.forEach((option) => {
            let optionElement = $('<option></option>').val(option).text(option);
            if (option === currentValue) {
                optionElement.prop('selected', true);
            }
            select.append(optionElement);
        });

        $this.html(select);
    });
}

// Функция для установки обработчиков событий
function setupEventHandlers() {
    $('.password-input').on('input', function() {
        var $this = $(this);
        // Также обновляем data-password для .password-hidden
        $this.closest('.password-hidden').data('password', $this.val());
    });
}

// Функция сохранений изменений для текстовых полей
function saveTextFields() {
    $('.editField').each(function() {
        var $this = $(this);
        var content = $this.val();
        $this.parent().html(content);
    });
}

// Функция сохранений изменений для выпадающих списков
function saveSelectFields() {
    $('.editSelect').each(function() {
        var $this = $(this);
        var content = $this.find(':selected').text();
        $this.parent().html(content);
    });
}

// Функция обработки полей ввода пароля
function savePasswordFields() {
    $('.password-hidden').each(function() {
        var $this = $(this);
        var newPassword = $this.data('password');
        // Убедимся, что newPassword является строкой
        if (typeof newPassword === 'string') {
            var maskedPassword = newPassword.replace(/./g, '*');
            $this.text(maskedPassword);
        } else {
            console.log(newPassword)
        }
    });
}

// Функция для обработки добавления/изменений в таблицах
function saveChangesForTable(EndPoint, tbodySelector, fieldNames) {
    try {
        $(tbodySelector + ' tr').each(function() {
            var row = $(this);
            var rowId = row.data('row-id');
            var isNew = row.data('new');
            var isEdited = row.data('edited');
            var clientId = $('.section-title').data('client-id');
            var content = {};

            fieldNames.forEach((fieldName, index) => {
                if (fieldName === 'password') {
                    // Получаем исходный пароль из поля ввода для новой записи или из данных элемента для существующей записи
                    content[fieldName] = isNew ? row.find('.editable').eq(index).text() : row.find('.password-hidden').data('password');
                } else {
                    content[fieldName] = row.find('.editable').eq(index).text();
                }
            });

            if (isNew) {
                // Отправляем POST-запрос
                console.log("Отправляем POST-запрос с данными: ", content);
                sendRequest('POST', `/apiv2/${EndPoint}/add/${clientId}/`, content, (data) => {
                    console.log(data);
                });
            } else if (isEdited) {
                // Отправляем PATCH-запрос
                console.log("Отправляем PATCH-запрос с данными: ", content);
                sendRequest('PATCH', `/apiv2/${EndPoint}/update/${rowId}/`, content, (data) => {
                    console.log(data);
                });
            }
        });
    } catch (error) {
        console.error('Ошибка при обработке таблицы:', error);
        errorShowToast('Ошибка при обработке таблицы:', error);
    }
}

// Функция для обработки изменений не разделах (не таблицах)
function saveChangesForSection(sectionId, endpoint) {
    try {
        var id = $(`#${sectionId} h3[data-id]`).data('id');
        var clientId = $('.section-title').data('client-id');
        var data = {};
        var isChanged = false;

        // Собираем изменения данных в разделе
        $(`#${sectionId} [data-field]`).each(function() {
            var $this = $(this);
            var fieldName = $this.data('field');
            var fieldValue = $this.is('input[type="checkbox"]') ? $this.is(':checked') : $this.text();
            var originalValue = $this.attr('data-original-content');

            console.log(`Поле: ${fieldName}, Текущее значение: ${fieldValue}, Оригинальное значение: ${originalValue}`);

            // Преобразование boolean значений в строки с большой буквы
            if (typeof fieldValue === 'boolean') {
                fieldValue = fieldValue ? 'True' : 'False';
                originalValue = originalValue === 'true' ? 'True' : 'False';
            }

            if (fieldValue !== originalValue) {
                data[fieldName] = fieldValue;
                isChanged = true;
            }
        });

        // Проверяем были ли изменения в разделах
        if (isChanged) {
            var method = id === 'new' ? 'POST' : 'PATCH';
            var url = id === 'new' ? `/apiv2/${endpoint}/add/${clientId}/` : `/apiv2/${endpoint}/update/${id}/`;
    
            sendRequest(method, url, data, (data) => {
                console.log(data);
            });
        }
    } catch (error) {
        console.error('Ошибка при обработке строк:', error);
        errorShowToast('Ошибка при обработке строк:', error);
    }
}

// Функция отправки новых данных на сервер
function sendRequest(method, url, data, callback) {
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Ошибка запроса! Статус: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (callback) {
            callback(data);
        }
    })
    .catch((error) => {
        console.error('Ошибка:', error);
        errorShowToast(`Ошибка при отправке данных: ${error.message}`);
    });
}

// Функция создания новых строк таблиц
function addNewRow(tableType, tbodyId) {
    try {
        var newRowHtml = '';
        switch (tableType) {
            case "contact":
                newRowHtml = `<tr>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td data-bs-toggle="tooltip" data-bs-placement="left" title="Удалить контакт"><button class="delete-row-button"><i class="fa fa-trash" aria-hidden="true"></i></button></td>
                </tr>`;
                break;
            case "connect_info":
                newRowHtml = `<tr>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td data-bs-toggle="tooltip" data-bs-placement="left" title="Удалить контакт"><button class="delete-row-button"><i class="fa fa-trash" aria-hidden="true"></i></button></td>
                </tr>`;
                break;
            case "tech_account":
                newRowHtml = `<tr>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td data-bs-toggle="tooltip" data-bs-placement="left" title="Удалить контакт"><button class="delete-row-button"><i class="fa fa-trash" aria-hidden="true"></i></button></td>
                </tr>`;
                break;
            case "bm_server":
                newRowHtml = `<tr>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td class="editable"><input type="text" class="editField" value="" /></td>
                    <td data-bs-toggle="tooltip" data-bs-placement="left" title="Удалить контакт"><button class="delete-row-button"><i class="fa fa-trash" aria-hidden="true"></i></button></td>
                </tr>`;
                break;
            default:
                console.error('Неизвестный тип таблицы:', tableType);
                return; // Если тип таблицы неизвестен, не добавляем строку
        }

        // Создаем новую строку с атрибутом data-new
        var newRow = $(newRowHtml).attr('data-new', 'true');
        // Добавляем новую строку в соответствующее тело таблицы
        $('#' + tbodyId).append(newRow);
        // Инициализируем всплывающие подсказки
        $('[data-bs-toggle="tooltip"]').tooltip();
    } catch (error) {
        console.error('Ошибка при добавлении строки в таблицу:', error);
        errorShowToast('Ошибка при добавлении строки в таблицу:', error);
    }
}