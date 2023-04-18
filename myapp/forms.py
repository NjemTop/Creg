from django import forms
from .models import BMInfoOnClient, ContactsCard

class AddClientForm(forms.ModelForm):
    class Meta:
        model = BMInfoOnClient
        fields = ['client_name', 'notes', 'contact_status']

    def __init__(self, *args, **kwargs):
        super(AddClientForm, self).__init__(*args, **kwargs)
        self.fields['contact_status'].initial = True  # Установите значение по умолчанию для contact_status
        self.fields['contact_status'].widget = forms.HiddenInput()  # Сделайте поле скрытым

class ContactsCardForm(forms.ModelForm):
    class Meta:
        model = ContactsCard
        fields = ['contact_name', 'contact_position', 'contact_email', 'notification_update', 'contact_notes']
