from django import forms
import re
import phonenumbers
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.forms import TextInput, Textarea, CheckboxInput, inlineformset_factory
from apps.company.models import Employee

from apps.clients.models import (
    Language, Client, Contact, TechnicalInfo, ServiceInfo, Integration, ClientIntegration
)


class ClientForm(forms.ModelForm):
    """Форма создания клиента с кастомными плейсхолдерами и валидацией"""

    manager = forms.ModelChoiceField(
        queryset=Employee.objects.filter(role="Менеджер"),
        empty_label="Выберите менеджера",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    language = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        empty_label="Выберите язык клиента",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                label = self.fields[field_name].label
                if label:
                    self.fields[field_name].label = mark_safe(label + '<span class="required-star">*</span>')

    def clean_account_name(self):
        """📌 Проверка: только латинские буквы (a-z), без пробелов и заглавных букв"""
        account_name = self.cleaned_data.get("account_name")

        if not re.fullmatch(r"^[a-z]+$", account_name):
            raise ValidationError("Учётная запись должна содержать только латинские буквы (a-z), без пробелов и заглавных букв.")

        if Client.objects.filter(account_name__iexact=account_name).exists():
            raise ValidationError(f"Клиент с учётной записью '{account_name}' уже существует.")

        return account_name

    def clean_client_name(self):
        """Проверка, что клиент с таким именем не существует"""
        client_name = self.cleaned_data.get("client_name")
        if Client.objects.filter(client_name__iexact=client_name).exists():
            raise ValidationError("Клиент с таким наименованием уже существует.")
        return client_name

    class Meta:
        model = Client
        fields = ['client_name', 'short_name', 'account_name', 'notes', 'saas', 'language', 'manager']
        widgets = {
            "client_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Юридическое наименование клиента",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Название клиента обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            "short_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Аббревиатура/псевдоним/краткое имя клиента",
                "oninvalid": "this.setCustomValidity('Поле Сокращенное наименование клиента обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            "account_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Учётная запись клиента",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Учётная запись клиента обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'cols': 10,
                'class': 'form-control resizable',
                "placeholder": "Здесь могут быть заметки о данном клиенте"
            }),
            'saas': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'language': forms.Select(attrs={
                'class': 'form-select'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class ContactForm(forms.ModelForm):
    """Форма для контактов клиента"""

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if not phone:
            return phone

        try:
            parsed_phone = phonenumbers.parse(phone, None)  # Определяем страну по номеру
            if not phonenumbers.is_valid_number(parsed_phone):
                raise ValidationError("Некорректный номер телефона")

            return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValidationError("Некорректный номер телефона")

    def clean_email(self):
        """📌 Валидация: проверяем, существует ли такой email"""
        email = self.cleaned_data.get("email")

        if Contact.objects.filter(email=email).exists():
            raise ValidationError(f"Контакт с почтой '{email}' уже существует.")

        return email

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                label = self.fields[field_name].label
                if label:
                    self.fields[field_name].label = mark_safe(label + ' <span class="required-star">*</span>')

    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'notes']
        widgets = {
            "first_name": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите имя контакта",
                "required": 'required'
            }),
            "last_name": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите фамилию контакта",
                "required": 'required'
            }),
            "email": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите почту контакта",
                "required": 'required'
            }),
            'notes': Textarea(attrs={
                'rows': 2,
                'cols': 10,
                'class': 'form-control resizable',
                "placeholder": "Примечания к контакту"
            }),
        }


class TechnicalInfoForm(forms.ModelForm):
    """Форма для технической информации о клиенте"""
    def __init__(self, *args, **kwargs):
        super(TechnicalInfoForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                label = self.fields[field_name].label
                if label:
                    self.fields[field_name].label = mark_safe(label + ' <span class="required-star">*</span>')

    class Meta:
        model = TechnicalInfo
        fields = ['server_version']
        widgets = {
            "server_version": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Версия при внедрении",
                "required": 'required'
            }),
        }


class ServiceInfoForm(forms.ModelForm):
    """Форма для сервисной информации клиента"""
    class Meta:
        model = ServiceInfo
        fields = ['manager']
        widgets = {
            "manager": forms.Select(attrs={"class": "form-select"}),
        }

# Формсеты (группы форм внутри формы клиента)
ContactFormSet = inlineformset_factory(Client, Contact, form=ContactForm, extra=1, can_delete=True)
