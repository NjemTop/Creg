document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы страницы
    const releaseTypeSelect = document.getElementById('releaseTypeGroup');
    const releaseViewSelect = document.getElementById('releaseViewGroup');
    const releaseGroupSelect = document.getElementById('releaseGroup');
    const filterGroupSelect = document.getElementById('filterGroup');
    const filterGroupRow = document.getElementById('filterGroupRow');
    const emailRow = document.getElementById('emailRow');
    const releaseGroupRow = document.getElementById('releaseGroup').parentNode.parentNode; // Получаем строку для скрытия
    const mobileVersionRow = document.getElementById('mobileVersionRow');
    const downloadButton = document.getElementById('downloadButton');
    const uploadButton = document.getElementById('uploadButton');
    const uploadInput = document.getElementById('uploadInput');

    // Шаблоны опций для "Выберите рассылку"
    const releaseOptionTemplates = {
        'standard_mailing': `<option value="release2x">2.х</option>
                             <option value="release3x">3.х</option>`,
        'hotfix': `<option value="release2x">2.х</option>
                   <option value="release3x">3.х</option>
                   <option value="releaseiPad">iPad/iPhone</option>
                   <option value="releaseAndroid">Android</option>
                   <option value="releaseModule">По модулям</option>
                   <option value="releaseIntegration">По интеграциям</option>`,
        'request': `<option value="releaseGP">Gold/Platinum</option>
                    <option value="releaseSaaS">SaaS</option>`,
        'default': `<option value="release2x">Пока ничего нет</option>`
    };

    // Шаблоны опций для "Фильтры"
    const filterOptionTemplates = {
        'test_mailing': `<option value="email">Кому отправлять</option>
                         <option value="release_process">release_process</option>`,
        'hotfix': `<option value="all_clients">Все клиенты</option>
                   <option value="select_list">Выбор из списка</option>`,
        'default': ''
    };

    // Функция обновления опций в выпадающем списке "Выберите рассылку"
    function updateReleaseGroupOptions() {
        const typeValue = releaseTypeSelect.value;
        const viewValue = releaseViewSelect.value;
        // Определяем ключ для выбора нужных опций
        const key = typeValue === 'test_mailing' ? viewValue : typeValue;
        // Обновляем опции в соответствии с выбранным ключом
        releaseGroupSelect.innerHTML = releaseOptionTemplates[key] || releaseOptionTemplates['default'];
    }

    // Функция отображение блока ввода почты
    function toggleEmailInput() {
        emailRow.style.display = filterGroupSelect.value === 'email' ? 'block' : 'none';
    }

    // Функция обновления опций и видимости фильтров
    function updateFilterGroupOptions() {
        const typeValue = releaseTypeSelect.value;
        const template = filterOptionTemplates[typeValue] || filterOptionTemplates['default'];
        filterGroupSelect.innerHTML = template;
        // Обновляем display для всей строки, чтобы скрыть и метку, и select
        filterGroupRow.style.display = template ? 'flex' : 'none'; // Используйте 'flex', если ваш .row использует flexbox
        emailRow.style.display = 'none'; // Скрываем поле email, если filterGroup не активен
        // Сразу вызываем toggleEmailInput, чтобы обновить видимость поля email
        toggleEmailInput();
    }

    // Функция обновления видимости разделов "Выберите рассылку" и "Фильтры"
    function updateVisibility() {
        const viewValue = releaseViewSelect.value;
        // Скрываем или показываем раздел "Выберите рассылку"
        releaseGroupRow.style.display = viewValue === 'custom_mailing' ? 'none' : '';
        // Показываем раздел "Фильтры" только для кастомной рассылки
        filterGroupRow.style.display = viewValue === 'custom_mailing' ? '' : 'none';
    }

    // Обработчик событий при изменении "Выберите вид рассылки"
    releaseViewSelect.addEventListener('change', function() {
        updateVisibility();
        // Также необходимо обновить предпросмотр, если это реализовано
    });

    // Обработчик выбора файла
    uploadInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            // Предполагается, что файл сразу загружается и отображается в iframe для предпросмотра
            const file = this.files[0];
            const reader = new FileReader();
            reader.onload = function(e) {
                previewIframe.contentWindow.document.open();
                previewIframe.contentWindow.document.write(e.target.result);
                previewIframe.contentWindow.document.close();
            };
            reader.readAsText(file);
        }
    });

    releaseTypeSelect.addEventListener('change', updateFilterGroupOptions);

    // Обработчик событий при изменении "Выберите тип рассылки"
    releaseTypeSelect.addEventListener('change', function() {
        updateReleaseGroupOptions();
        updateFilterGroupOptions();
        // Показываем или скрываем дополнительные опции на основе выбранного типа рассылки
        testMailingRow.style.visibility = this.value === 'test_mailing' ? 'visible' : 'hidden';
        testMailingRow.style.height = this.value === 'test_mailing' ? 'auto' : '0';
        // Дополнительно вызываем toggleEmailInput для обновления поля email
        toggleEmailInput();
    });

    filterGroupSelect.addEventListener('change', toggleEmailInput);

    // Обработчик событий при изменении "Выберите вид рассылки"
    releaseViewSelect.addEventListener('change', function() {
        updateReleaseGroupOptions();
        toggleMobileVersionInput();
    });

    // Обработчик событий при изменении "Выберите рассылку"
    releaseGroupSelect.addEventListener('change', function() {
        toggleMobileVersionInput();
    });

    // Функция для показа/скрытия поля мобильной версии
    function toggleMobileVersionInput() {
        const releaseViewValue = releaseViewSelect.value;
        const releaseGroupValue = releaseGroupSelect.value;

        // Показываем поле для мобильной версии только для версии 3.x и если не выбран "hotfix"
        mobileVersionRow.style.display = (releaseViewValue !== 'hotfix' && releaseGroupValue === 'release3x') ? 'block' : 'none';
    }

    // Функция для определения имени шаблона
    function getSelectedTemplateName() {
        const releaseType = releaseTypeSelect.value;
        const releaseView = releaseViewSelect.value;
        const releaseGroup = releaseGroupSelect.value;

        // Определите логику для выбора имени шаблона на основе выбранных параметров
        if (releaseType === 'test_mailing' && releaseView === 'standard_mailing') {
            if (releaseGroup === 'release2x') {
                return 'index_2x.html';
            } else if (releaseGroup === 'release3x') {
                return 'index_3x.html';
            }
        } else if (releaseType === 'test_mailing' && releaseView === 'hotfix') {
            if (releaseGroup === 'release2x') {
                return 'index_2x_hotfix_server.html';
            } else if (releaseGroup === 'release3x') {
                return 'index_3x_hotfix_server.html';
            } else if (releaseGroup === 'releaseiPad') {
                return 'index_iPad.html';
            } else if (releaseGroup === 'releaseAndroid') {
                return 'index_Android.html';
            } else if (releaseGroup === 'releaseModule') {
                return 'index_Module.html';
            }
            // Остальные условие для шаблонов
        }
        // Возвращаем пустую строку или null, если шаблон не найден
        return null;
    }

    // Обработчик клика на кнопку скачивания
    downloadButton.addEventListener('click', function() {
        const selectedTemplateName = getSelectedTemplateName();
        if (selectedTemplateName) {
            // Если имя шаблона определено, формируем URL для скачивания
            window.location.href = `/apiv2/download_template/${selectedTemplateName}`;
        } else {
            // Если имя шаблона не найдено, выводим сообщение об ошибке
            infoShowToast("Шаблон не выбран или отсутствует.");
        }
    });

    // Переменная для хранения выбранного файла
    let selectedFile = null;

    // Обработчик выбора файла
    uploadInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            selectedFile = this.files[0]; // Сохраняем выбранный файл
        } else {
            selectedFile = null;
        }
    });

    // Обработчик клика на кнопку загрузки
    uploadButton.addEventListener('click', function() {
        if (selectedFile) {
            const selectedTemplateName = getSelectedTemplateName();
            if (selectedTemplateName) {
                // Проверяем, соответствует ли имя файла ожидаемому шаблону
                if (selectedFile.name === selectedTemplateName) {
                    uploadFile(selectedFile, selectedTemplateName);
                } else {
                    infoShowToast(`Имя файла должно быть '${selectedTemplateName}'.`);
                }
            } else {
                infoShowToast("Название шаблона не определено.");
            }
        } else {
            infoShowToast("Файл не выбран.");
        }
    });

    function loadTemplatePreview(templateName) {
        fetch(`/apiv2/get_template_content/${templateName}`)
            .then(response => {
                if (response.ok) {
                    return response.text();
                } else {
                    throw new Error('Не удалось загрузить предпросмотр.');
                }
            })
            .then(htmlContent => {
                const iframe = document.getElementById('previewIframe');
                iframe.contentWindow.document.open();
                iframe.contentWindow.document.write(htmlContent);
                iframe.contentWindow.document.close();
            })
            .catch(error => {
                infoShowToast(error.message);
            });
    }
    
    // Обработчик событий при изменении параметров шаблона
    releaseTypeSelect.addEventListener('change', updateTemplatePreview);
    releaseViewSelect.addEventListener('change', updateTemplatePreview);
    releaseGroupSelect.addEventListener('change', updateTemplatePreview);
    
    function updateTemplatePreview() {
        const selectedTemplateName = getSelectedTemplateName();
        if (selectedTemplateName) {
            loadTemplatePreview(selectedTemplateName);
        }
    }

    // Инициализация при загрузке страницы
    updateReleaseGroupOptions();
    updateFilterGroupOptions();
    toggleEmailInput();
    updateVisibility();
    toggleMobileVersionInput(); // Вызываем при загрузке, чтобы установить правильное состояние
    const selectedTemplateName = getSelectedTemplateName();
    loadTemplatePreview(selectedTemplateName);
});

// Функция загрузки шаблона на сервер
function uploadFile(file, templateName) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('templateName', templateName);

    fetch('/apiv2/upload_template/', {
        method: 'POST',
        body: formData
    }).then(response => {
        if (response.ok) {
            successShowToast("Шаблон успешно загружен.");
        } else {
            errorShowToast(`Ошибка при загрузке шаблона.`);
        }
    }).catch(error => {
        errorShowToast(`Ошибка: ${error.message}`);
    });
}
