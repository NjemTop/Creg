from django import forms
from django.core.exceptions import ValidationError
from .models import Mailing, MailingTestRecipient, MailingMode
from apps.clients.models import Language


class MailingForm(forms.ModelForm):

    test_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com',
            'type': 'email',
            'required': 'required'
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загружаем языки из модели Language
        self.fields['language'].queryset = Language.objects.all()
        self.fields['language'].empty_label = "Выберите язык"

        # Режим по умолчанию — тест
        self.fields['mode'].initial = 'test'

        ### Форматируем формат даты и времени для отображения на фронте
        self.fields['saas_update_time'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_test_email(self):
        """Валидация и очистка тестового email."""
        mode = self.cleaned_data.get('mode')
        test_email = self.cleaned_data.get('test_email')

        if mode == MailingMode.TEST and not test_email:
            raise ValidationError("В тестовом режиме необходимо указать email.")

        if mode != MailingMode.TEST:
            return None

        return test_email

    def clean_language(self):
        """Валидация и очистка поля языка."""
        mode = self.cleaned_data.get('mode')
        language = self.cleaned_data.get('language')

        if mode == MailingMode.TEST and not language:
            raise ValidationError("В тестовом режиме необходимо указать язык ")

        # При продакшн-режиме язык не должен передаваться
        if mode != MailingMode.TEST:
            return None

        return language

    def clean(self):
        """ Проверка, что указана хотя бы одна версия (Server, iPad, Android). """
        cleaned_data = super().clean()
        server_version = cleaned_data.get('server_version')
        ipad_version = cleaned_data.get('ipad_version')
        android_version = cleaned_data.get('android_version')

        if not (server_version or ipad_version or android_version):
            raise ValidationError("Необходимо указать хотя бы одну версию (Server, iPad или Android).")

        if cleaned_data.get("saas_notification") and not cleaned_data.get("saas_update_time"):
            raise ValidationError("Укажите дату и время обновления для SaaS-клиентов.")

        return cleaned_data

    class Meta:
        model = Mailing
        fields = [
            'mode', 'language', 'release_type',
            'server_version', 'ipad_version', 'android_version',
            'service_window', 'saas_notification', 'saas_update_time'
        ]
        widgets = {
            'mode': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'release_type': forms.Select(attrs={'class': 'form-select'}),
            'server_version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Версия Server'
            }),
            'ipad_version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Версия iPad'
            }),
            'android_version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Версия Android'
            }),
            'service_window': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'saas_notification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'saas_update_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
