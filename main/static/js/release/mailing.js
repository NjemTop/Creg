document.addEventListener('DOMContentLoaded', function() {
    // Определения переменных и получение элементов страницы
    const applyButton = document.getElementById('applyButton');
    const applyButtonProd = document.getElementById('applyButtonProd');
    const sendRequestButton = document.getElementById('sendRequestButton');
    const applyButtonHotfix = document.getElementById('applyButtonHotfix');
    const releaseTypeSelect = document.getElementById('releaseTypeGroup');
    const releaseGroupSelect = document.getElementById('releaseGroup');
    const languageSelect = document.getElementById('languageSelect');
    const emailRow = document.getElementById('emailRow');
    const numberReleaseRow = document.getElementById('numberReleaseRow');
    const iPadVersionRow = document.getElementById('iPadVersionRow');
    const AndroidVersionRow = document.getElementById('AndroidVersionRow');
    const releaseVersionInput = document.getElementById('numberRelease');
    const iPadVersionInput = document.getElementById('iPadVersion');
    const AndroidVersionInput = document.getElementById('AndroidVersion');
    const downloadButton = document.getElementById('downloadButton');
    const uploadButton = document.getElementById('uploadButton');
    const uploadInput = document.getElementById('uploadInput');
    const previewIframe = document.getElementById('previewIframe');
    const testMailingCheckbox = document.getElementById('testMailingCheckbox');
    const testMailingRow = document.getElementById('testMailingRow');
    
    // Переменная для хранения выбранного файла
    let selectedFile = null;

    // Конфигурация видимости
    const visibilityConfig = {
        'standard_mailing': {
            'release2x': { 'numberRelease': true, 'iPadVersion': true, 'AndroidVersion': true },
            'release3x': { 'numberRelease': true, 'iPadVersion': true, 'AndroidVersion': true },
            'default': { 'numberRelease': true }
        },
        'request': {
            'releaseGP': { 'numberRelease': true },
            'releaseSaaS': { 'numberRelease': true },
            'default': { 'numberRelease': true }
        },
        'hotfix': {
            'release2x': { 'numberRelease': true, 'iPadVersion': false, 'AndroidVersion': false },
            'release3x': { 'numberRelease': true, 'iPadVersion': false, 'AndroidVersion': false },
            'releaseiPad2x': { 'numberRelease': false, 'iPadVersion': true },
            'releaseiPad3x': { 'numberRelease': false, 'iPadVersion': true },
            'releaseAndroid2x': { 'numberRelease': false, 'AndroidVersion': true },
            'releaseAndroid3x': { 'numberRelease': false, 'AndroidVersion': true },
            'default': { 'numberRelease': true }
        },
        'default': { 'numberRelease': false, 'iPadVersion': false, 'AndroidVersion': false, 'email': false }
    };

    function updateReleaseGroupOptions() {
        const typeValue = releaseTypeSelect.value;

        // Сначала очищаем текущие опции
        releaseGroupSelect.innerHTML = '';

        // Добавляем опции в зависимости от типа рассылки
        if (typeValue === 'standard_mailing') {
            releaseGroupSelect.add(new Option('2.x', 'release2x'));
            releaseGroupSelect.add(new Option('3.x', 'release3x'));
        } else if (typeValue === 'hotfix') {
            releaseGroupSelect.add(new Option('2.x', 'release2x'));
            releaseGroupSelect.add(new Option('3.x', 'release3x'));
            releaseGroupSelect.add(new Option('iPad/iPhone 2.0', 'releaseiPad2x'));
            releaseGroupSelect.add(new Option('iPad/iPhone 3.0', 'releaseiPad3x'));
            releaseGroupSelect.add(new Option('Android 2.0', 'releaseAndroid2x'));
            releaseGroupSelect.add(new Option('Android 3.0', 'releaseAndroid3x'));
            releaseGroupSelect.add(new Option('По модулям', 'releaseModule'));
            releaseGroupSelect.add(new Option('По интеграциям', 'releaseIntegration'));
        } else if (typeValue === 'request') {
            releaseGroupSelect.add(new Option('Gold/Platinum', 'releaseGP'));
            releaseGroupSelect.add(new Option('SaaS', 'releaseSaaS'));
        }
    }

    function toggleVisibility(element, condition) {
        if (element) {
            element.style.display = condition ? '' : 'none';
        }
    }

    function updateVisibility() {
        const typeValue = releaseTypeSelect.value;
        const groupValue = releaseGroupSelect.value;
        const isTestMailing = testMailingCheckbox.checked;

        // Получаем конфигурацию для выбранного типа и группы рассылки
        let configForType = visibilityConfig[typeValue] || visibilityConfig['default'];
        let config = configForType[groupValue] || configForType['default'];

        // Управляем видимостью элементов
        toggleVisibility(numberReleaseRow, config.numberRelease);
        toggleVisibility(iPadVersionRow, config.iPadVersion);
        toggleVisibility(AndroidVersionRow, config.AndroidVersion);
        toggleVisibility(emailRow, isTestMailing);
        toggleVisibility(languageSelect.closest('.row'), isTestMailing);
        
        // Кнопки
        toggleVisibility(applyButton, isTestMailing);
        toggleVisibility(applyButtonProd, !isTestMailing && typeValue === 'standard_mailing');
        toggleVisibility(sendRequestButton, !isTestMailing && typeValue === 'request');
        toggleVisibility(applyButtonHotfix, !isTestMailing && typeValue === 'hotfix');

        // "Выберите рассылку:" должно всегда отображаться
        toggleVisibility(testMailingRow, true);
    }

    function clearFields() {
        releaseVersionInput.value = '';
        iPadVersionInput.value = '';
        AndroidVersionInput.value = '';
    }

    // Установка обработчиков событий
    releaseTypeSelect.addEventListener('change', function() {
        clearFields();  // Очистка полей при смене типа рассылки
        updateReleaseGroupOptions();
        updateVisibility();
    });

    testMailingCheckbox.addEventListener('change', updateVisibility);
    releaseGroupSelect.addEventListener('change', updateVisibility);

    // Инициализация опций и видимости при загрузке страницы
    updateReleaseGroupOptions();
    updateVisibility();

    // Обработчик выбора файла
    uploadInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            selectedFile = this.files[0];
            const reader = new FileReader();
            reader.onload = function(e) {
                previewIframe.contentWindow.document.open();
                previewIframe.contentWindow.document.write(e.target.result);
                previewIframe.contentWindow.document.close();
            };
            reader.readAsText(selectedFile);
        }
    });

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

    /// Функции для предпросмотра шаблона в iframe
    function getSelectedTemplateName() {
        const releaseType = releaseTypeSelect.value;
        const releaseGroup = releaseGroupSelect.value;
        const language = languageSelect.value;

        // Определяем язык суффикса
        const languageSuffix = language === 'ru' ? '_ru' : '_en';

        // Логика для выбора имени шаблона на основе выбранных параметров
        if (releaseType === 'standard_mailing') {
            if (releaseGroup === 'release2x') {
                return `index_2x${languageSuffix}.html`;
            } else if (releaseGroup === 'release3x') {
                return `index_3x${languageSuffix}.html`;
            }
        } else if (releaseType === 'hotfix') {
            if (releaseGroup === 'release2x') {
                return `index_2x_hotfix_server${languageSuffix}.html`;
            } else if (releaseGroup === 'release3x') {
                return `index_3x_hotfix_server${languageSuffix}.html`;
            } else if (releaseGroup === 'releaseAndroid2x') {
                return `index_2x_hotfix_android${languageSuffix}.html`;
            } else if (releaseGroup === 'releaseAndroid3x') {
                return `index_3x_hotfix_android${languageSuffix}.html`;
            } else if (releaseGroup === 'releaseiPad2x') {
                return `index_2x_hotfix_ipad${languageSuffix}.html`;
            } else if (releaseGroup === 'releaseiPad3x') {
                return `index_3x_hotfix_ipad${languageSuffix}.html`;
            } else if (releaseGroup === 'releaseModule') {
                return `index_module_hotfix${languageSuffix}.html`;
            } else if (releaseGroup === 'releaseIntegration') {
                return `index_integration_hotfix${languageSuffix}.html`;
            }
        }

        // Если не найден подходящий шаблон
        return null;
    }

    // Функция загрузки предпросмотра шаблона рассылки
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
                const iframe = document.getElementById('previewIframe');
                iframe.contentWindow.document.open();
                iframe.contentWindow.document.write('<div style="font-size: 16px; color: red; text-align: center; padding: 20px;">Не удалось загрузить предпросмотр.</div>');
                iframe.contentWindow.document.close();
                infoShowToast(error.message);
            });
    }

    // Функция для обновления предпросмотра шаблона
    function updateTemplatePreview() {
        const selectedTemplateName = getSelectedTemplateName();
        if (selectedTemplateName) {
            loadTemplatePreview(selectedTemplateName);
        }
    }

    // Функция для загрузки файла шаблона на сервер
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

    // Инициализация предпросмотра шаблона
    updateTemplatePreview();

    // Обработчик событий при изменении параметров шаблона
    releaseTypeSelect.addEventListener('change', updateTemplatePreview);
    releaseGroupSelect.addEventListener('change', updateTemplatePreview);
    languageSelect.addEventListener('change', updateTemplatePreview);
});
