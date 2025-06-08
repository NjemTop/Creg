document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector("form");
    const contactList = document.getElementById("contact_list");
    const addContactBtn = document.getElementById("add_contact");
    const phoneInputs = {};

    // Универсальная функция валидации поля с выводом текста ошибки
    function setupFieldValidation(selector, regex, errorMessage) {
        const field = document.querySelector(selector);
        if (!field) return;

        let errorDiv = field.nextElementSibling;
        if (!errorDiv || !errorDiv.classList.contains("invalid-feedback")) {
            errorDiv = document.createElement("div");
            errorDiv.classList.add("invalid-feedback");
            field.after(errorDiv);
        }

        // Проверка только при потере фокуса
        field.addEventListener("blur", function () {
            if (!regex.test(field.value) && field.value.trim() !== "") {
                field.classList.add("is-invalid");
                errorDiv.textContent = errorMessage;
            }
        });

        // Если пользователь снова вводит данные — убираем ошибку
        field.addEventListener("input", function () {
            field.classList.remove("is-invalid");
            errorDiv.textContent = "";
        });
    }

    // Подключение intlTelInput и IMask
    function setupPhoneInput(selector) {
        const input = document.querySelector(selector);
        if (!input) return;

        const iti = window.intlTelInput(input, {
            initialCountry: "ru",
            preferredCountries: ["ru", "kz", "rs"],
            separateDialCode: false,
            nationalMode: false,
            autoPlaceholder: "off",
            formatOnDisplay: false,
            loadUtils: () => import("/static/js/utils.js"),
        });

        phoneInputs[input.id] = iti;

        let mask;
        function updateMask() {
            if (mask) mask.destroy();

            const country = iti.getSelectedCountryData().iso2;
            const dialCode = iti.getSelectedCountryData().dialCode;

            const masks = {
                "ru": "+7 (000) 000-00-00",
                "kz": "+7 (000) 000-00-00",
                "rs": "+381 00 000 0000",
                "us": "+1 (000) 000-0000",
                "gb": "+44 0000 000000",
                "fr": "+33 0 00 00 00 00",
                "de": "+49 000 0000000",
                "ua": "+380 (00) 000-00-00",
                "pl": "+48 000 000 000",
            };

            mask = IMask(input, { mask: masks[country] || `+${dialCode} 000 000 0000` });
        }

        // Функция обновления скрытого поля
        function updateHiddenInput() {
            setTimeout(() => {
                if (iti.isValidNumber()) {
                    const formattedNumber = iti.getNumber();
                    let hiddenInput = document.querySelector(`input[name="${input.id}"]`);
                    if (!hiddenInput) {
                        hiddenInput = document.createElement("input");
                        hiddenInput.type = "hidden";
                        hiddenInput.name = input.id;
                        form.appendChild(hiddenInput);
                    }
                    hiddenInput.value = formattedNumber;
                }
            }, 200);
        }

        input.addEventListener("input", updateHiddenInput);
        input.addEventListener("countrychange", () => {
            updateMask();
            updateHiddenInput();
        });

        updateMask();
    }

    // Инициализация валидации при загрузке
    setupFieldValidation("#id_account_name", /^[a-z]+$/, "Допустимы только латинские буквы (a-z), без пробелов и заглавных букв.");

    // Добавление контакта
    if (!addContactBtn.dataset.listenerAdded) {
        addContactBtn.dataset.listenerAdded = "true";
        addContactBtn.addEventListener("click", function () {
            const contactNumber = document.querySelectorAll(".contact-card").length;

            const contactCard = document.createElement("div");
            contactCard.className = "card contact-card p-3 shadow-sm";
            contactCard.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0 contact-title">Контакт ${contactNumber + 1}</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-contact">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
                <hr>
                <div class="row g-2">
                    <div class="col-md-6">
                        <label for="id_contacts-${contactNumber}-first_name" class="form-label">Имя <span class="text-danger">*</span></label>
                        <input type="text" name="contacts-${contactNumber}-first_name" id="id_contacts-${contactNumber}-first_name" class="form-control" required>
                    </div>
                    <div class="col-md-6">
                        <label for="id_contacts-${contactNumber}-last_name" class="form-label">Фамилия <span class="text-danger">*</span></label>
                        <input type="text" name="contacts-${contactNumber}-last_name" id="id_contacts-${contactNumber}-last_name" class="form-control" required>
                    </div>
                </div>
                <div class="row g-2 mt-2">
                    <div class="col-md-6">
                        <label for="id_contacts-${contactNumber}-email" class="form-label">Почта <span class="text-danger">*</span></label>
                        <input type="email" name="contacts-${contactNumber}-email" id="id_contacts-${contactNumber}-email" class="form-control email-input" required>
                    </div>
                    <div class="col-md-6">
                        <label for="id_contacts-${contactNumber}-phone_number" class="form-label">Телефон</label>
                        <input type="tel" name="contacts-${contactNumber}-phone_number" id="id_contacts-${contactNumber}-phone_number" class="form-control phone-input">
                    </div>
                </div>
                <div class="mt-2">
                    <label for="id_contacts-${contactNumber}-notes" class="form-label">Примечание</label>
                    <textarea name="contacts-${contactNumber}-notes" id="id_contacts-${contactNumber}-notes" class="form-control"></textarea>
                </div>
            `;

            contactList.appendChild(contactCard);
            setupPhoneInput(`#id_contacts-${contactNumber}-phone_number`);
            setupFieldValidation(`#id_contacts-${contactNumber}-email`, /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/, "Введите корректный email (например, example@mail.com).");
        });
    }

    // Удаление контакта (делегирование события)
    contactList.addEventListener("click", function (event) {
        if (event.target.closest(".remove-contact")) {
            event.target.closest(".contact-card").remove();
        }
    });

    // Валидация перед отправкой формы
    form.addEventListener("submit", function (event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            form.classList.add("was-validated");
        }
    });
});
