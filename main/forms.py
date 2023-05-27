from .models import ClientsList, ContactsCard, ServiseCard
from django.forms import ModelForm, TextInput, Textarea, formset_factory


class ClientListForm(ModelForm):
    class Meta:
        model = ClientsList
        fields = ["client_name"]
        widgets = {
            "client_name": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите наименование клиента"
            }),
        }


class ContactForm(ModelForm):
    class Meta:
        model = ContactsCard
        fields = ['contact_name', 'contact_position', 'contact_email', 'notification_update', 'contact_notes']
        widgets = {
            'contact_name': TextInput(attrs={'class': 'form-control'}),
            'contact_position': TextInput(attrs={'class': 'form-control'}),
            'contact_email': TextInput(attrs={'class': 'form-control'}),
            'notification_update': TextInput(attrs={'class': 'form-control'}),
            'contact_notes': Textarea(attrs={'class': 'form-control'}),
        }


ContactFormSet = formset_factory(ContactForm, extra=1)


class ServiseCardForm(ModelForm):
    class Meta:
        model = ServiseCard
        fields = ['service_pack', 'manager', 'loyal']
        widgets = {
            'service_pack': TextInput(attrs={'class': 'form-control'}),
            'manager': TextInput(attrs={'class': 'form-control'}),
            'loyal': TextInput(attrs={'class': 'form-control'}),
        }
