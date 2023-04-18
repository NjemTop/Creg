from django import forms
from .models import BMInfoOnClient

class AddClientForm(forms.ModelForm):
    class Meta:
        model = BMInfoOnClient
        fields = ['client_name', 'notes', 'contact_status']

    def __init__(self, *args, **kwargs):
        super(AddClientForm, self).__init__(*args, **kwargs)
        self.fields['contact_status'].initial = True  # Установите значение по умолчанию для contact_status
        self.fields['contact_status'].widget = forms.HiddenInput()  # Сделайте поле скрытым
