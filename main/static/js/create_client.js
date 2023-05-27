// Получение значений contactFormCount и contactFormMaxCount из атрибутов кнопки
var contactFormCount = parseInt(document.getElementById('add_contact').getAttribute('data-contact-formset-total-form-count'));
var contactFormMaxCount = parseInt(document.getElementById('add_contact').getAttribute('data-contact-formset-max-num'));

// Обработчик события клика на кнопке "Добавить контакт"
document.getElementById('add_contact').addEventListener('click', function () {
    // Проверка, что количество форм не превышает максимальное значение
    if (contactFormCount < contactFormMaxCount) {
        var formSet = document.getElementById('contact_form_set');
        var newForm = document.createElement('div');
        newForm.className = 'contact-form mb-3';
        newForm.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <label for="id_contacts-${contactFormCount}-contact_name">ФИО <span class="text-danger">*</span></label>
                    <input type="text" name="contacts-${contactFormCount}-contact_name" id="id_contacts-${contactFormCount}-contact_name" required class="form-control">
                </div>
                <div class="col-md-4">
                    <label for="id_contacts-${contactFormCount}-contact_position">Должность <span class="text-danger">*</span></label>
                    <input type="text" name="contacts-${contactFormCount}-contact_position" id="id_contacts-${contactFormCount}-contact_position" required class="form-control">
                </div>
                <div class="col-md-4">
                    <label for="id_contacts-${contactFormCount}-contact_email">Почта <span class="text-danger">*</span></label>
                    <input type="email" name="contacts-${contactFormCount}-contact_email" id="id_contacts-${contactFormCount}-contact_email" required class="form-control">
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <label for="id_contacts-${contactFormCount}-notification_update">Отправка рассылки</label>
                    <select name="contacts-${contactFormCount}-notification_update" id="id_contacts-${contactFormCount}-notification_update" class="form-select">
                        <option value="">Выберите тип рассылки</option>
                        <option value="Основной контакт рассылки">Основной контакт рассылки</option>
                        <option value="Копия рассылки">Копия рассылки</option>
                        <option value="Рассылка не нужна">Рассылка не нужна</option>
                    </select>
                </div>
                <div class="col-md-6">
                    <label for="id_contacts-${contactFormCount}-contact_notes">Заметки</label>
                    <textarea name="contacts-${contactFormCount}-contact_notes" id="id_contacts-${contactFormCount}-contact_notes" class="form-control"></textarea>
                </div>
            </div>
        `;
        formSet.appendChild(newForm);
        contactFormCount++;
    }
});

// Обработчик события изменения значения поля "Менеджер"
document.getElementById('manager').addEventListener('change', function () {
    var managerCustomInput = document.getElementById('manager_custom');
    if (this.value === 'Другое') {
        managerCustomInput.style.display = 'block';
        managerCustomInput.required = true;
    } else {
        managerCustomInput.style.display = 'none';
        managerCustomInput.required = false;
    }
});
