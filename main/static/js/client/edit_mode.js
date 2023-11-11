$(document).ready(function() {
    // Переключение на режим редактирования
    $('.edit-button').click(function() {
        enterEditMode();
    });

    // Сохранение изменений
    $('.save-button').click(function() {
        saveChanges();
        exitEditMode();
    });

    // Отмена редактирования
    $('.cancel-button').click(function() {
        cancelEdit();
        exitEditMode();
    });

    // Добавление новой строки
    $('.add-row-button').click(function() {
        var tableType = $(this).data('table-type');
        var tbodyId = tableType + '-tbody'; // Создаем идентификатор на основе типа таблицы
        addNewRow(tableType, tbodyId); // Передаем tbodyId в функцию
    });

    // Удаление конкретной строки
    $('body').on('click', '.delete-row-button', function() {
        if ($('tbody tr').length > 1) { 
            $(this).closest('tr').remove();
        } else {
            alert("Необходимо оставить хотя бы одну строку");
        }
    });
});

function addNewRow(tableType, tbodyId) {
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
}

// Функция для перехода в режим редактирования страницы
function enterEditMode() {
    $('.editable, .editable-select, .password-hidden').each(function() {
        $(this).attr('data-original-content', $(this).html());
        $('tbody').attr('data-original-table', $('tbody').html());
    });

    $('.edit-button').hide();
    $('.save-button, .cancel-button').show();
    $('.add-row-button, .delete-row-button').show();
    $('.delete-column').show();

    // Включение режима редактирования для текстовых полей
    $('.editable').each(function() {
        var content = $(this).html();
        $(this).html('<input type="text" class="editField" value="' + content + '" />');
    });

    // Включение режима редактирования для выпадающих списков
    $('.editable-select').each(function() {
        let currentValue = $(this).text();
        let options = $(this).data('options').split(',');
        let select = $('<select class="editSelect"></select>');
        
        options.forEach(function(option) {
            let optionElement = $('<option></option>').val(option).text(option);
            if (option === currentValue) {
                optionElement.prop('selected', true);
            }
            select.append(optionElement);
        });

        $(this).html(select);
    });

    // Устанавливаем атрибут data-edited для строки, которая редактируется
    $('.editable').on('input', function() {
        $(this).closest('tr').attr('data-edited', 'true');
    });

    // Показываем поля ввода для редактирования паролей
    $('.password-hidden').each(function() {
        var currentPassword = $(this).data('password');
        var input = $('<input>', {
            type: 'text',
            class: 'editField password-input',
            value: currentPassword
        });
        $(this).html(input);
        $(this).siblings('.show-password-button, .copy-password-button').hide();
    });

    // Добавляем обработчик событий для новых полей ввода пароля
    $('.password-input').on('input', function() {
        // Также обновляем data-password для .password-hidden
        $(this).closest('.password-hidden').data('password', $(this).val());
    });
}

function saveChanges() {
    // Сохранение изменений для текстовых полей
    $('.editField').each(function() {
        var content = $(this).val();
        $(this).parent().html(content);
    });

    // Сохранение изменений для выпадающих списков
    $('.editSelect').each(function() {
        var content = $(this).find(':selected').text();
        $(this).parent().html(content);
    });

    // Обработка полей ввода пароля
    $('.password-hidden').each(function() {
        var newPassword = $(this).data('password');
        // Убедимся, что newPassword является строкой
        if (typeof newPassword === 'string') {
            var maskedPassword = newPassword.replace(/./g, '*');
            $(this).text(maskedPassword);
            console.log("Новый пароль установлен: ", newPassword);
        } else {
            console.log(newPassword)
            console.log("Ошибка: Новый пароль не является строкой.");
        }
    });

    // Обработка изменений в таблицах
    processTableChanges('contact', '#contact-tbody', ['name', 'position', 'email', 'number', 'notification_update']);
    processTableChanges('connect_info', '#connect_info-tbody', ['name', 'account', 'password']);
    processTableChanges('tech_account', '#tech_account-tbody', ['description', 'account', 'password']);
}

// Функция для обработки добавления/изменений в таблицах
function processTableChanges(EndPoint, tbodySelector, fieldNames) {
    $(tbodySelector + ' tr').each(function() {
        var row = $(this);
        var rowId = row.data('row-id');
        var isNew = row.data('new');
        var isEdited = row.data('edited');
        var clientId = $('.section-title').data('client-id');
        var content = {};

        fieldNames.forEach(function(fieldName, index) {
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
            sendPostRequest(EndPoint, clientId, content);
        } else if (isEdited) {
            // Отправляем PATCH-запрос
            console.log("Отправляем PATCH-запрос с данными: ", content);
            sendPatchRequest(EndPoint, rowId, content);
        }
    });
}

function cancelEdit() {
    // Возвращение всех полей к их первоначальному состоянию
    $('.editable, .editable-select, .password-hidden').each(function() {
        var originalContent = $(this).attr('data-original-content');
        $(this).html(originalContent);
        $(this).siblings('.show-password-button, .copy-password-button').show();
        // Возвращаем таблицу к её первоначальному состоянию
        $('tbody').html($('tbody').attr('data-original-table'));
    });
}

function exitEditMode() {
    $('.save-button, .cancel-button').hide();
    $('.add-row-button, .delete-row-button').hide();
    $('.delete-column').hide();
    $('.edit-button').show();
}

function sendPostRequest(EndPoint, clientId, content) {
    // Отправка POST-запроса для добавления новых данных на сервер
    fetch(`/apiv2/${EndPoint}/add/${clientId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(content)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Запрос ошибка! Статус: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log(data);
    
    })
    .catch((error) => {
        console.error('Ошибка:', error);
        errorShowToast(`Ошибка при добавлении данных: ${error.message}`);
    });
}

function sendPatchRequest(EndPoint, rowId, content) {
    // Отправка PATCH-запроса для обновления существующей новых данных на сервер
    fetch(`/apiv2/${EndPoint}/update/${rowId}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(content)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Запрос ошибка! Статус: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log(data);
    
    })
    .catch((error) => {
        console.error('Ошибка:', error);
        errorShowToast(`Ошибка при обновлении данных: ${error.message}`);
    });
}
