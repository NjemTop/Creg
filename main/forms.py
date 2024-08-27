from django.core.exceptions import ValidationError
from .models import ClientsList, ContactsCard, ServiseCard, TechInformationCard, Integration, ModuleCard, UsersBoardMaps
from django.forms import ModelForm, TextInput, Textarea, formset_factory, Select, CheckboxInput
from django import forms
from django.utils.safestring import mark_safe


class ClientForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                label = self.fields[field_name].label
                if label:
                    self.fields[field_name].label = mark_safe(label + '<span class="required-star">*</span>')

    class Meta:
        model = ClientsList
        fields = ['client_name', 'short_name', 'notes']
        widgets = {
            "client_name": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите наименование клиента",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Название клиента обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            "short_name": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Вписать название для УЗ jFrog/NextCloud (по-английски, без пробелов и заглавных букв. Например, 'gpnserbia')",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Сокращенное наименование клиента обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,  # Размера высоты поля
                'cols': 10,  # Размер ширины поля
                'class': 'form-control resizable',
                "placeholder": "Здесь могут быть заметки для данного клиента"
            }),
        }

    def clean_client_name(self):
        client_name = self.cleaned_data.get("client_name")
        # Проверяем, существует ли уже клиент с таким наименованием
        if ClientsList.objects.filter(client_name__iexact=client_name).exists():
            raise ValidationError("Клиент с таким наименованием уже существует.")
        return client_name

class ContactForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                label = self.fields[field_name].label
                if label:
                    self.fields[field_name].label = mark_safe(label + '<span class="required-star">*</span>')

    class Meta:
        model = ContactsCard
        fields = ['firstname', 'lastname', 'contact_position', 'contact_email', 'notification_update', 'contact_notes']
        widgets = {
            "firstname": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите имя контакта",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Имя обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            "lastname": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите фамилию контакта",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Фамилия обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            "contact_email": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите почту контакта",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Почта обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
            "contact_position": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите должность контакта"
            }),
            'contact_notes': forms.Textarea(attrs={
                'rows': 2,  # Размера высоты поля
                'cols': 10,  # Размер ширины поля
                'class': 'form-control resizable',
                "placeholder": "Здесь могут быть комментарии для данного контакта"
            }),
            'notification_update': forms.CheckboxInput(attrs={
                'class': 'notification_update-toggle'
                }),
        }


class TechInformationCardForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TechInformationCardForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                label = self.fields[field_name].label
                if label:
                    self.fields[field_name].label = mark_safe(label + '<span class="required-star">*</span>')

    class Meta:
        model = TechInformationCard
        fields = ['server_version']
        widgets = {
            "server_version": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите версию сервера при внедрении клиента",
                "required": 'required',
                "oninvalid": "this.setCustomValidity('Поле Версия сервера обязательно для заполнения.')",
                "oninput": "this.setCustomValidity('')"
            }),
        }

class ModuleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModuleForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                self.fields[field_name].widget = forms.CheckboxInput(attrs={'class': 'module-toggle'})

    class Meta:
        model = ModuleCard
        fields = '__all__'
        exclude = ['client_card']

class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = '__all__'
        exclude = ['client_card'] # Исключаем поле client_card, так как оно будет автоматически привязано при сохранении

class ServiseCardForm(ModelForm):
    class Meta:
        model = ServiseCard
        fields = ['manager']

class CommandForm(forms.Form):
    command = forms.CharField(label='Введите команду', max_length=100)


VERSION_CHOICES = [
    ('2', '2.x'),
    ('3', '3.x'),
]

class AdvancedSearchForm(forms.Form):
    integration = forms.BooleanField(required=False, label='Интеграции')
    module = forms.BooleanField(required=False, label='Модули')
    plan_status = forms.BooleanField(required=False, label='Статус плана', initial=True)
    server_version_checkbox = forms.BooleanField(required=False, label='Версия сервера')
    server_version_input = forms.CharField(required=False, label='Введите версию сервера')
    filter_by_version = forms.BooleanField(required=False, label='Фильтр по версии')
    version = forms.ChoiceField(choices=VERSION_CHOICES, required=False, label='Выберите версию')
    filter_by_manager = forms.BooleanField(required=False, label='Фильтр по менеджеру')
    manager = forms.ModelChoiceField(queryset=UsersBoardMaps.objects.filter(position='Менеджер'), required=False, label='Менеджеры')

    filter_by_tariff_plan = forms.BooleanField(required=False, label='Фильтр по тарифному плану')
    tariff_plan = forms.ChoiceField(required=False, choices=[], label='Тарифный план')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tariff_plan'].choices = [
            (plan, plan) for plan in ServiseCard.objects.values_list('service_pack', flat=True).distinct()
        ]


class URLInputForm(forms.Form):
    service_url = forms.URLField(label='URL адрес стенда', required=True)

class ServerInputForm(forms.Form):
    service_url = forms.CharField(label='Адрес сервера, где развёрнут стенд', required=True)
